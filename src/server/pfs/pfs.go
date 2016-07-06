package pfs

import (
	"fmt"

	"github.com/pachyderm/pachyderm/src/client/pfs"
)

// ErrFileNotFound represents a file-not-found error.
type ErrFileNotFound struct {
	error
}

// ErrRepoNotFound represents a repo-not-found error.
type ErrRepoNotFound struct {
	error
}

// ErrCommitNotFound represents a commit-not-found error.
type ErrCommitNotFound struct {
	error
}

// ErrParentCommitNotFound represents a parent-commit-not-found error.
type ErrParentCommitNotFound struct {
	error
}

// NewErrFileNotFound creates a new ErrFileNotFound.
func NewErrFileNotFound(file string, repo string, commitID string) *ErrFileNotFound {
	return &ErrFileNotFound{
		error: fmt.Errorf("File %v not found in repo %v at commit %v", file, repo, commitID),
	}
}

// NewErrRepoNotFound creates a new ErrRepoNotFound.
func NewErrRepoNotFound(repo string) *ErrRepoNotFound {
	return &ErrRepoNotFound{
		error: fmt.Errorf("Repo %v not found", repo),
	}
}

// NewErrCommitNotFound creates a new ErrCommitNotFound.
func NewErrCommitNotFound(repo string, commitID string) *ErrCommitNotFound {
	return &ErrCommitNotFound{
		error: fmt.Errorf("Commit %v not found in repo %v", commitID, repo),
	}
}

// NewErrParentCommitNotFound creates a new ErrParentCommitNotFound.
func NewErrParentCommitNotFound(repo string, commitID string) *ErrParentCommitNotFound {
	return &ErrParentCommitNotFound{
		error: fmt.Errorf("Parent commit %v not found in repo %v", commitID, repo),
	}
}

// ByteRangeSize returns byteRange.Upper - byteRange.Lower.
func ByteRangeSize(byteRange *pfs.ByteRange) uint64 {
	return byteRange.Upper - byteRange.Lower
}
