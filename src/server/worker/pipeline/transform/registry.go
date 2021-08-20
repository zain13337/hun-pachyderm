package transform

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/gogo/protobuf/types"
	"github.com/jmoiron/sqlx"
	"golang.org/x/sync/errgroup"

	"github.com/pachyderm/pachyderm/v2/src/client"
	"github.com/pachyderm/pachyderm/v2/src/client/limit"
	"github.com/pachyderm/pachyderm/v2/src/internal/backoff"
	col "github.com/pachyderm/pachyderm/v2/src/internal/collection"
	"github.com/pachyderm/pachyderm/v2/src/internal/errors"
	"github.com/pachyderm/pachyderm/v2/src/internal/errutil"
	"github.com/pachyderm/pachyderm/v2/src/internal/grpcutil"
	"github.com/pachyderm/pachyderm/v2/src/internal/ppsdb"
	"github.com/pachyderm/pachyderm/v2/src/internal/ppsutil"
	"github.com/pachyderm/pachyderm/v2/src/internal/storage/renew"
	"github.com/pachyderm/pachyderm/v2/src/internal/uuid"
	"github.com/pachyderm/pachyderm/v2/src/internal/work"
	"github.com/pachyderm/pachyderm/v2/src/pfs"
	"github.com/pachyderm/pachyderm/v2/src/pps"
	pfsserver "github.com/pachyderm/pachyderm/v2/src/server/pfs"
	"github.com/pachyderm/pachyderm/v2/src/server/worker/common"
	"github.com/pachyderm/pachyderm/v2/src/server/worker/datum"
	"github.com/pachyderm/pachyderm/v2/src/server/worker/driver"
	"github.com/pachyderm/pachyderm/v2/src/server/worker/logs"
)

const (
	defaultDatumSetsPerWorker int64 = 4
)

type hasher struct {
	salt string
}

func (h *hasher) Hash(inputs []*common.Input) string {
	return common.HashDatum(h.salt, inputs)
}

type registry struct {
	driver      driver.Driver
	logger      logs.TaggedLogger
	taskQueue   *work.TaskQueue
	concurrency int64
	limiter     limit.ConcurrencyLimiter
}

// TODO:
// Prometheus stats? (previously in the driver, which included testing we should reuse if possible)
// capture logs (reuse driver tests and reintroduce tagged logger).
func newRegistry(driver driver.Driver, logger logs.TaggedLogger) (*registry, error) {
	// Determine the maximum number of concurrent tasks we will allow
	concurrency, err := driver.ExpectedNumWorkers()
	if err != nil {
		return nil, err
	}
	taskQueue, err := driver.NewTaskQueue()
	if err != nil {
		return nil, err
	}
	return &registry{
		driver:      driver,
		logger:      logger,
		taskQueue:   taskQueue,
		concurrency: concurrency,
		limiter:     limit.New(int(concurrency)),
	}, nil
}

func (reg *registry) succeedJob(pj *pendingJob) error {
	pj.logger.Logf("job successful, closing commits")
	// Use the registry's driver so that the job's supervision goroutine cannot cancel us
	return ppsutil.FinishJob(reg.driver.PachClient(), pj.ji, pps.JobState_JOB_FINISHING, "")
}

func (reg *registry) failJob(pj *pendingJob, reason string) error {
	pj.logger.Logf("failing job with reason: %s", reason)
	// Use the registry's driver so that the job's supervision goroutine cannot cancel us
	return ppsutil.FinishJob(reg.driver.PachClient(), pj.ji, pps.JobState_JOB_FAILURE, reason)
}

func (reg *registry) killJob(pj *pendingJob, reason string) error {
	pj.logger.Logf("killing job with reason: %s", reason)
	// Use the registry's driver so that the job's supervision goroutine cannot cancel us
	_, err := reg.driver.PachClient().PpsAPIClient.StopJob(
		reg.driver.PachClient().Ctx(),
		&pps.StopJobRequest{
			Job:    pj.ji.Job,
			Reason: reason,
		},
	)
	return err
}

func (reg *registry) startJob(jobInfo *pps.JobInfo) (retErr error) {
	reg.limiter.Acquire()
	defer func() {
		// TODO(2.0 optional): The error handling during job setup needs more work.
		// For a commit that is squashed, we would want to exit.
		// For transient errors, we would want to retry, not just give up on the job.
		if retErr != nil {
			reg.limiter.Release()
		}
	}()
	pi := reg.driver.PipelineInfo()
	pj := &pendingJob{
		driver: reg.driver,
		logger: reg.logger.WithJob(jobInfo.Job.ID),
		ji:     jobInfo,
		hasher: &hasher{
			salt: pi.Details.Salt,
		},
		noSkip: pi.Details.ReprocessSpec == client.ReprocessSpecEveryJob || pi.Details.S3Out,
	}
	if pj.ji.State == pps.JobState_JOB_CREATED {
		pj.ji.State = pps.JobState_JOB_STARTING
		if err := pj.writeJobInfo(); err != nil {
			return err
		}
	}
	// Inputs must be ready before we can construct a datum iterator.
	if err := pj.logger.LogStep("waiting for job inputs", func() error {
		return reg.processJobStarting(pj)
	}); err != nil {
		return err
	}
	if err := pj.load(); err != nil {
		return err
	}
	// TODO: This could probably be scoped to a callback.
	var afterTime time.Duration
	if pj.ji.Details.JobTimeout != nil {
		startTime, err := types.TimestampFromProto(pj.ji.Started)
		if err != nil {
			return err
		}
		timeout, err := types.DurationFromProto(pj.ji.Details.JobTimeout)
		if err != nil {
			return err
		}
		afterTime = time.Until(startTime.Add(timeout))
	}
	go func() {
		defer reg.limiter.Release()
		if pj.ji.Details.JobTimeout != nil {
			pj.logger.Logf("cancelling job at: %+v", afterTime)
			timer := time.AfterFunc(afterTime, func() {
				reg.killJob(pj, "job timed out")
			})
			defer timer.Stop()
		}
		if err := backoff.RetryUntilCancel(pj.driver.PachClient().Ctx(), func() error {
			ctx, cancel := context.WithCancel(reg.driver.PachClient().Ctx())
			defer cancel()
			eg, jobCtx := errgroup.WithContext(ctx)
			pj.driver = reg.driver.WithContext(jobCtx)
			pj.cancel = cancel
			eg.Go(func() error {
				return reg.superviseJob(pj)
			})
			eg.Go(func() error {
				var err error
				for err == nil {
					err = reg.processJob(pj)
				}
				if errors.Is(err, errutil.ErrBreak) || errors.Is(ctx.Err(), context.Canceled) {
					return nil
				}
				return err
			})
			return eg.Wait()
		}, backoff.NewInfiniteBackOff(), func(err error, d time.Duration) error {
			pj.logger.Logf("error processing job: %v, retrying in %v", err, d)
			for err != nil {
				if st, ok := err.(errors.StackTracer); ok {
					pj.logger.Logf("error stack: %+v", st.StackTrace())
				}
				err = errors.Unwrap(err)
			}
			// Reload the job's commits and info as they may have changed.
			if err := pj.load(); err != nil {
				return err
			}
			pj.ji.Restart++
			if err := pj.writeJobInfo(); err != nil {
				pj.logger.Logf("error incrementing restart count for job (%s): %v", pj.ji.Job.ID, err)
			}
			return nil
		}); err != nil {
			// TODO: We can hit this due to a transient failure of the pachd sidecar.
			pj.logger.Logf("fatal job error: %v", err)
		}
	}()
	return nil
}

func (reg *registry) superviseJob(pj *pendingJob) error {
	defer pj.cancel()
	_, err := pj.driver.PachClient().PfsAPIClient.InspectCommit(pj.driver.PachClient().Ctx(),
		&pfs.InspectCommitRequest{
			Commit: pj.ji.OutputCommit,
			Wait:   pfs.CommitState_FINISHED,
		})
	if err != nil {
		if pfsserver.IsCommitNotFoundErr(err) || pfsserver.IsCommitDeletedErr(err) {
			// Stop the job and clean up any job state in the registry
			if err := reg.killJob(pj, "output commit missing"); err != nil {
				return err
			}
			// Output commit was deleted. Delete job as well
			// TODO: This should be handled through a transaction defer when the commit is squashed.
			if err := pj.driver.NewSQLTx(func(sqlTx *sqlx.Tx) error {
				// Delete the job if no other worker has deleted it yet
				jobInfo := &pps.JobInfo{}
				if err := pj.driver.Jobs().ReadWrite(sqlTx).Get(ppsdb.JobKey(pj.ji.Job), jobInfo); err != nil {
					return err
				}
				return pj.driver.DeleteJob(sqlTx, jobInfo)
			}); err != nil && !col.IsErrNotFound(err) {
				return err
			}
			return nil
		}
		return err
	}
	return nil

}

func (reg *registry) processJob(pj *pendingJob) error {
	state := pj.ji.State
	if pps.IsTerminal(state) || state == pps.JobState_JOB_FINISHING {
		return errutil.ErrBreak
	}
	switch state {
	case pps.JobState_JOB_STARTING:
		return errors.New("job should have been moved out of the STARTING state before processJob")
	case pps.JobState_JOB_RUNNING:
		return pj.logger.LogStep("processing job running", func() error {
			return reg.processJobRunning(pj)
		})
	case pps.JobState_JOB_EGRESSING:
		return pj.logger.LogStep("processing job egressing", func() error {
			return reg.processJobEgressing(pj)
		})
	}
	panic(fmt.Sprintf("unrecognized job state: %s", state))
}

func (reg *registry) processJobStarting(pj *pendingJob) error {
	// block until job inputs are ready
	failed, err := failedInputs(pj.driver.PachClient(), pj.ji)
	if err != nil {
		return err
	}
	if len(failed) > 0 {
		reason := fmt.Sprintf("inputs failed: %s", strings.Join(failed, ", "))
		return reg.failJob(pj, reason)
	}
	pj.ji.State = pps.JobState_JOB_RUNNING
	return pj.writeJobInfo()
}

func (reg *registry) processJobRunning(pj *pendingJob) error {
	pachClient := pj.driver.PachClient()
	// TODO: We need to delete the output for S3Out since we don't have a clear way to track the output in the stats commit (which means datums cannot be skipped with S3Out).
	// If we had a way to map the output added through the S3 gateway back to the datums, and stored this in the appropriate place in the stats commit, then we would be able
	// handle datums the same way we handle normal pipelines.
	if pj.driver.PipelineInfo().Details.S3Out {
		if err := pachClient.DeleteFile(pj.commitInfo.Commit, "/"); err != nil {
			return err
		}
	}
	if err := reg.taskQueue.RunTaskBlock(pachClient.Ctx(), func(master *work.Master) error {
		if err := pj.withParallelDatums(master.Ctx(), func(ctx context.Context, dit datum.Iterator) error {
			return reg.processDatums(ctx, pj, master, dit)
		}); err != nil {
			return err
		}
		return pj.withSerialDatums(master.Ctx(), func(ctx context.Context, dit datum.Iterator) error {
			return reg.processDatums(ctx, pj, master, dit)
		})
	}); err != nil {
		if errors.Is(err, errutil.ErrBreak) {
			return nil
		}
		return err
	}
	if pj.ji.Details.Egress != nil {
		pj.ji.State = pps.JobState_JOB_EGRESSING
		return pj.writeJobInfo()
	}
	return reg.succeedJob(pj)
}

func (reg *registry) processDatums(ctx context.Context, pj *pendingJob, master *work.Master, dit datum.Iterator) error {
	var numDatums int64
	if err := dit.Iterate(func(_ *datum.Meta) error {
		numDatums++
		return nil
	}); err != nil {
		return err
	}
	// Set up the datum set spec for the job.
	// When the datum set spec is not set, evenly distribute the datums.
	var setSpec *datum.SetSpec
	datumSetsPerWorker := defaultDatumSetsPerWorker
	if pj.driver.PipelineInfo().Details.DatumSetSpec != nil {
		setSpec = &datum.SetSpec{
			Number:    pj.driver.PipelineInfo().Details.DatumSetSpec.Number,
			SizeBytes: pj.driver.PipelineInfo().Details.DatumSetSpec.SizeBytes,
		}
		datumSetsPerWorker = pj.driver.PipelineInfo().Details.DatumSetSpec.PerWorker
	}
	if setSpec == nil || (setSpec.Number == 0 && setSpec.SizeBytes == 0) {
		setSpec = &datum.SetSpec{Number: numDatums / (int64(reg.concurrency) * datumSetsPerWorker)}
		if setSpec.Number == 0 {
			setSpec.Number = 1
		}
	}
	pachClient := pj.driver.PachClient().WithCtx(ctx)
	subtasks := make(chan *work.Task)
	stats := &datum.Stats{ProcessStats: &pps.ProcessStats{}}
	if err := pachClient.WithRenewer(func(ctx context.Context, renewer *renew.StringSet) error {
		eg, ctx := errgroup.WithContext(ctx)
		pachClient = pachClient.WithCtx(ctx)
		// Setup goroutine for creating datum set subtasks.
		eg.Go(func() error {
			defer close(subtasks)
			storageRoot := filepath.Join(pj.driver.InputDir(), client.PPSScratchSpace, uuid.NewWithoutDashes())
			// TODO: The dit needs to iterate with the inner context.
			return datum.CreateSets(dit, storageRoot, setSpec, func(upload func(client.ModifyFile) error) error {
				subtask, err := createDatumSetSubtask(pachClient, pj, upload, renewer)
				if err != nil {
					return err
				}
				select {
				case subtasks <- subtask:
				case <-ctx.Done():
					return ctx.Err()
				}
				return nil
			})
		})
		// Setup goroutine for running and collecting datum set subtasks.
		eg.Go(func() error {
			return pj.logger.LogStep("running and collecting datum set subtasks", func() error {
				return master.RunSubtasksChan(
					subtasks,
					func(ctx context.Context, taskInfo *work.TaskInfo) error {
						if taskInfo.State == work.State_FAILURE {
							return errors.Errorf("datum set subtask failed: %s", taskInfo.Reason)
						}
						data, err := deserializeDatumSet(taskInfo.Task.Data)
						if err != nil {
							return err
						}
						renewer.Remove(data.FileSetId)
						if _, err := pachClient.PfsAPIClient.AddFileSet(
							pachClient.Ctx(),
							&pfs.AddFileSetRequest{
								Commit:    pj.commitInfo.Commit,
								FileSetId: data.OutputFileSetId,
							},
						); err != nil {
							return grpcutil.ScrubGRPC(err)
						}
						if _, err := pachClient.PfsAPIClient.AddFileSet(
							pachClient.Ctx(),
							&pfs.AddFileSetRequest{
								Commit:    pj.metaCommitInfo.Commit,
								FileSetId: data.MetaFileSetId,
							},
						); err != nil {
							return grpcutil.ScrubGRPC(err)
						}
						if err := datum.MergeStats(stats, data.Stats); err != nil {
							return err
						}
						pj.saveJobStats(data.Stats)
						return pj.writeJobInfo()
					},
				)
			})
		})
		return eg.Wait()
	}); err != nil {
		return err
	}
	if stats.FailedID != "" {
		if err := reg.failJob(pj, fmt.Sprintf("datum %v failed", stats.FailedID)); err != nil {
			return err
		}
		return errutil.ErrBreak
	}
	return nil
}

func createDatumSetSubtask(pachClient *client.APIClient, pj *pendingJob, upload func(client.ModifyFile) error, renewer *renew.StringSet) (*work.Task, error) {
	resp, err := pachClient.WithCreateFileSetClient(func(mf client.ModifyFile) error {
		return upload(mf)
	})
	if err != nil {
		return nil, err
	}
	renewer.Add(resp.FileSetId)
	data, err := serializeDatumSet(&DatumSet{
		JobID:        pj.ji.Job.ID,
		OutputCommit: pj.commitInfo.Commit,
		// TODO: It might make sense for this to be a hash of the constituent datums?
		// That could make it possible to recover from a master restart.
		FileSetId: resp.FileSetId,
	})
	if err != nil {
		return nil, err
	}
	return &work.Task{
		// TODO: Should this just be a uuid?
		ID:   uuid.NewWithoutDashes(),
		Data: data,
	}, nil
}

func serializeDatumSet(data *DatumSet) (*types.Any, error) {
	serialized, err := types.MarshalAny(data)
	if err != nil {
		return nil, err
	}
	return serialized, nil
}

func deserializeDatumSet(any *types.Any) (*DatumSet, error) {
	data := &DatumSet{}
	if err := types.UnmarshalAny(any, data); err != nil {
		return nil, err
	}
	return data, nil
}

func (reg *registry) processJobEgressing(pj *pendingJob) error {
	url := pj.ji.Details.Egress.URL
	err := pj.driver.PachClient().GetFileURL(pj.commitInfo.Commit, "/", url)
	// file not found means the commit is empty, nothing to egress
	if err != nil && !pfsserver.IsFileNotFoundErr(err) {
		return err
	}
	return reg.succeedJob(pj)
}

func failedInputs(pachClient *client.APIClient, jobInfo *pps.JobInfo) ([]string, error) {
	var failed []string
	waitCommit := func(name string, commit *pfs.Commit) error {
		ci, err := pachClient.WaitCommit(commit.Branch.Repo.Name, commit.Branch.Name, commit.ID)
		if err != nil {
			return errors.Wrapf(err, "error blocking on commit %s", commit)
		}
		if ci.Error != "" {
			failed = append(failed, name)
		}
		return nil
	}
	visitErr := pps.VisitInput(jobInfo.Details.Input, func(input *pps.Input) error {
		if input.Pfs != nil && input.Pfs.Commit != "" {
			if err := waitCommit(input.Pfs.Name, client.NewCommit(input.Pfs.Repo, input.Pfs.Branch, input.Pfs.Commit)); err != nil {
				return err
			}
		}
		return nil
	})
	if visitErr != nil {
		return nil, visitErr
	}
	return failed, nil
}
