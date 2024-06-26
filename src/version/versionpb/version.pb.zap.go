// Code generated by protoc-gen-zap (etc/proto/protoc-gen-zap). DO NOT EDIT.
//
// source: version/versionpb/version.proto

package versionpb

import (
	zapcore "go.uber.org/zap/zapcore"
)

func (x *Version) MarshalLogObject(enc zapcore.ObjectEncoder) error {
	if x == nil {
		return nil
	}
	enc.AddUint32("major", x.Major)
	enc.AddUint32("minor", x.Minor)
	enc.AddUint32("micro", x.Micro)
	enc.AddString("additional", x.Additional)
	enc.AddString("git_commit", x.GitCommit)
	enc.AddString("git_tree_modified", x.GitTreeModified)
	enc.AddString("build_date", x.BuildDate)
	enc.AddString("go_version", x.GoVersion)
	enc.AddString("platform", x.Platform)
	return nil
}
