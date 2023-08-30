// Code generated by protoc-gen-zap (etc/proto/protoc-gen-zap). DO NOT EDIT.
//
// source: admin/admin.proto

package admin

import (
	zapcore "go.uber.org/zap/zapcore"
)

func (x *ClusterInfo) MarshalLogObject(enc zapcore.ObjectEncoder) error {
	if x == nil {
		return nil
	}
	enc.AddString("id", x.Id)
	enc.AddString("deployment_id", x.DeploymentId)
	enc.AddBool("warnings_ok", x.WarningsOk)
	warningsArrMarshaller := func(enc zapcore.ArrayEncoder) error {
		for _, v := range x.Warnings {
			enc.AppendString(v)
		}
		return nil
	}
	enc.AddArray("warnings", zapcore.ArrayMarshalerFunc(warningsArrMarshaller))
	enc.AddString("proxy_host", x.ProxyHost)
	enc.AddBool("proxy_tls", x.ProxyTls)
	enc.AddBool("paused", x.Paused)
	return nil
}

func (x *InspectClusterRequest) MarshalLogObject(enc zapcore.ObjectEncoder) error {
	if x == nil {
		return nil
	}
	enc.AddObject("client_version", x.ClientVersion)
	enc.AddObject("current_project", x.CurrentProject)
	return nil
}
