# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: api/debug/debug.proto
# plugin: python-betterproto
# This file has been @generated
from dataclasses import dataclass
from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
)

import betterproto
import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf
import grpc

from .. import (
    pfs as _pfs__,
    pps as _pps__,
)


if TYPE_CHECKING:
    import grpc


class SetLogLevelRequestLogLevel(betterproto.Enum):
    UNKNOWN = 0
    DEBUG = 1
    INFO = 2
    ERROR = 3
    OFF = 4


@dataclass(eq=False, repr=False)
class ProfileRequest(betterproto.Message):
    profile: "Profile" = betterproto.message_field(1)
    filter: "Filter" = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class Profile(betterproto.Message):
    name: str = betterproto.string_field(1)
    duration: timedelta = betterproto.message_field(2)


@dataclass(eq=False, repr=False)
class Filter(betterproto.Message):
    pachd: bool = betterproto.bool_field(1, group="filter")
    pipeline: "_pps__.Pipeline" = betterproto.message_field(2, group="filter")
    worker: "Worker" = betterproto.message_field(3, group="filter")
    database: bool = betterproto.bool_field(4, group="filter")


@dataclass(eq=False, repr=False)
class Worker(betterproto.Message):
    pod: str = betterproto.string_field(1)
    redirected: bool = betterproto.bool_field(2)


@dataclass(eq=False, repr=False)
class BinaryRequest(betterproto.Message):
    filter: "Filter" = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class DumpRequest(betterproto.Message):
    filter: "Filter" = betterproto.message_field(1)
    limit: int = betterproto.int64_field(2)
    """
    Limit sets the limit for the number of commits / jobs that are returned for
    each repo / pipeline in the dump.
    """


@dataclass(eq=False, repr=False)
class SetLogLevelRequest(betterproto.Message):
    pachyderm: "SetLogLevelRequestLogLevel" = betterproto.enum_field(1, group="level")
    grpc: "SetLogLevelRequestLogLevel" = betterproto.enum_field(2, group="level")
    duration: timedelta = betterproto.message_field(3)
    recurse: bool = betterproto.bool_field(4)


@dataclass(eq=False, repr=False)
class SetLogLevelResponse(betterproto.Message):
    affected_pods: List[str] = betterproto.string_field(1)
    errored_pods: List[str] = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class GetDumpV2TemplateRequest(betterproto.Message):
    filters: List[str] = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetDumpV2TemplateResponse(betterproto.Message):
    request: "DumpV2Request" = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class Pipeline(betterproto.Message):
    project: str = betterproto.string_field(1)
    name: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class Pod(betterproto.Message):
    name: str = betterproto.string_field(1)
    ip: str = betterproto.string_field(2)
    containers: List[str] = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class App(betterproto.Message):
    name: str = betterproto.string_field(1)
    pods: List["Pod"] = betterproto.message_field(2)
    timeout: timedelta = betterproto.message_field(3)
    pipeline: "Pipeline" = betterproto.message_field(4)


@dataclass(eq=False, repr=False)
class System(betterproto.Message):
    helm: bool = betterproto.bool_field(1)
    database: bool = betterproto.bool_field(2)
    version: bool = betterproto.bool_field(3)
    describes: List["App"] = betterproto.message_field(4)
    logs: List["App"] = betterproto.message_field(5)
    loki_logs: List["App"] = betterproto.message_field(6)
    binaries: List["App"] = betterproto.message_field(7)
    profiles: List["App"] = betterproto.message_field(8)


@dataclass(eq=False, repr=False)
class StarlarkLiteral(betterproto.Message):
    """StarlarkLiteral is a custom Starlark script."""

    name: str = betterproto.string_field(1)
    """
    The name of the script; used for debug messages and to control where the
    output goes.
    """

    program_text: str = betterproto.string_field(2)
    """The text of the "debugdump" personality Starlark program."""


@dataclass(eq=False, repr=False)
class Starlark(betterproto.Message):
    """Starlark controls the running of a Starlark script."""

    builtin: str = betterproto.string_field(1, group="source")
    """One built into the pachd binary."""

    literal: "StarlarkLiteral" = betterproto.message_field(2, group="source")
    """Or a script supplied in this request."""

    timeout: timedelta = betterproto.message_field(3)
    """
    How long to allow the script to run for.  If unset, defaults to 1 minute.
    """


@dataclass(eq=False, repr=False)
class DumpV2Request(betterproto.Message):
    system: "System" = betterproto.message_field(1)
    """Which system-level information to include in the debug dump."""

    pipelines: List["Pipeline"] = betterproto.message_field(2)
    """
    Which pipelines to fetch information about and include in the debug dump.
    """

    input_repos: bool = betterproto.bool_field(3)
    """If true, fetch information about non-output repos."""

    timeout: timedelta = betterproto.message_field(4)
    """How long to run the dump for."""

    defaults: "DumpV2RequestDefaults" = betterproto.message_field(5)
    """Which defaults to include in the debug dump."""

    starlark_scripts: List["Starlark"] = betterproto.message_field(6)
    """A list of Starlark scripts to run."""


@dataclass(eq=False, repr=False)
class DumpV2RequestDefaults(betterproto.Message):
    cluster_defaults: bool = betterproto.bool_field(1)
    """If true, include the cluster defaults."""


@dataclass(eq=False, repr=False)
class DumpContent(betterproto.Message):
    content: bytes = betterproto.bytes_field(1)


@dataclass(eq=False, repr=False)
class DumpProgress(betterproto.Message):
    task: str = betterproto.string_field(1)
    total: int = betterproto.int64_field(2)
    progress: int = betterproto.int64_field(3)


@dataclass(eq=False, repr=False)
class DumpChunk(betterproto.Message):
    content: "DumpContent" = betterproto.message_field(1, group="chunk")
    progress: "DumpProgress" = betterproto.message_field(2, group="chunk")


@dataclass(eq=False, repr=False)
class RunPfsLoadTestRequest(betterproto.Message):
    spec: str = betterproto.string_field(1)
    branch: "_pfs__.Branch" = betterproto.message_field(2)
    seed: int = betterproto.int64_field(3)
    state_id: str = betterproto.string_field(4)


@dataclass(eq=False, repr=False)
class RunPfsLoadTestResponse(betterproto.Message):
    spec: str = betterproto.string_field(1)
    branch: "_pfs__.Branch" = betterproto.message_field(2)
    seed: int = betterproto.int64_field(3)
    error: str = betterproto.string_field(4)
    duration: timedelta = betterproto.message_field(5)
    state_id: str = betterproto.string_field(6)


class DebugStub:

    def __init__(self, channel: "grpc.Channel"):
        self.__rpc_profile = channel.unary_stream(
            "/debug_v2.Debug/Profile",
            request_serializer=ProfileRequest.SerializeToString,
            response_deserializer=betterproto_lib_google_protobuf.BytesValue.FromString,
        )
        self.__rpc_binary = channel.unary_stream(
            "/debug_v2.Debug/Binary",
            request_serializer=BinaryRequest.SerializeToString,
            response_deserializer=betterproto_lib_google_protobuf.BytesValue.FromString,
        )
        self.__rpc_dump = channel.unary_stream(
            "/debug_v2.Debug/Dump",
            request_serializer=DumpRequest.SerializeToString,
            response_deserializer=betterproto_lib_google_protobuf.BytesValue.FromString,
        )
        self.__rpc_set_log_level = channel.unary_unary(
            "/debug_v2.Debug/SetLogLevel",
            request_serializer=SetLogLevelRequest.SerializeToString,
            response_deserializer=SetLogLevelResponse.FromString,
        )
        self.__rpc_get_dump_v2_template = channel.unary_unary(
            "/debug_v2.Debug/GetDumpV2Template",
            request_serializer=GetDumpV2TemplateRequest.SerializeToString,
            response_deserializer=GetDumpV2TemplateResponse.FromString,
        )
        self.__rpc_dump_v2 = channel.unary_stream(
            "/debug_v2.Debug/DumpV2",
            request_serializer=DumpV2Request.SerializeToString,
            response_deserializer=DumpChunk.FromString,
        )
        self.__rpc_run_pfs_load_test = channel.unary_unary(
            "/debug_v2.Debug/RunPFSLoadTest",
            request_serializer=RunPfsLoadTestRequest.SerializeToString,
            response_deserializer=RunPfsLoadTestResponse.FromString,
        )
        self.__rpc_run_pfs_load_test_default = channel.unary_unary(
            "/debug_v2.Debug/RunPFSLoadTestDefault",
            request_serializer=betterproto_lib_google_protobuf.Empty.SerializeToString,
            response_deserializer=RunPfsLoadTestResponse.FromString,
        )

    def profile(
        self, *, profile: "Profile" = None, filter: "Filter" = None
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:

        request = ProfileRequest()
        if profile is not None:
            request.profile = profile
        if filter is not None:
            request.filter = filter

        for response in self.__rpc_profile(request):
            yield response

    def binary(
        self, *, filter: "Filter" = None
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:

        request = BinaryRequest()
        if filter is not None:
            request.filter = filter

        for response in self.__rpc_binary(request):
            yield response

    def dump(
        self, *, filter: "Filter" = None, limit: int = 0
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:

        request = DumpRequest()
        if filter is not None:
            request.filter = filter
        request.limit = limit

        for response in self.__rpc_dump(request):
            yield response

    def set_log_level(
        self,
        *,
        pachyderm: "SetLogLevelRequestLogLevel" = None,
        grpc: "SetLogLevelRequestLogLevel" = None,
        duration: timedelta = None,
        recurse: bool = False
    ) -> "SetLogLevelResponse":

        request = SetLogLevelRequest()
        request.pachyderm = pachyderm
        request.grpc = grpc
        if duration is not None:
            request.duration = duration
        request.recurse = recurse

        return self.__rpc_set_log_level(request)

    def get_dump_v2_template(
        self, *, filters: Optional[List[str]] = None
    ) -> "GetDumpV2TemplateResponse":
        filters = filters or []

        request = GetDumpV2TemplateRequest()
        request.filters = filters

        return self.__rpc_get_dump_v2_template(request)

    def dump_v2(
        self,
        *,
        system: "System" = None,
        pipelines: Optional[List["Pipeline"]] = None,
        input_repos: bool = False,
        timeout: timedelta = None,
        defaults: "DumpV2RequestDefaults" = None,
        starlark_scripts: Optional[List["Starlark"]] = None
    ) -> Iterator["DumpChunk"]:
        pipelines = pipelines or []
        starlark_scripts = starlark_scripts or []

        request = DumpV2Request()
        if system is not None:
            request.system = system
        if pipelines is not None:
            request.pipelines = pipelines
        request.input_repos = input_repos
        if timeout is not None:
            request.timeout = timeout
        if defaults is not None:
            request.defaults = defaults
        if starlark_scripts is not None:
            request.starlark_scripts = starlark_scripts

        for response in self.__rpc_dump_v2(request):
            yield response

    def run_pfs_load_test(
        self,
        *,
        spec: str = "",
        branch: "_pfs__.Branch" = None,
        seed: int = 0,
        state_id: str = ""
    ) -> "RunPfsLoadTestResponse":

        request = RunPfsLoadTestRequest()
        request.spec = spec
        if branch is not None:
            request.branch = branch
        request.seed = seed
        request.state_id = state_id

        return self.__rpc_run_pfs_load_test(request)

    def run_pfs_load_test_default(self) -> "RunPfsLoadTestResponse":

        request = betterproto_lib_google_protobuf.Empty()

        return self.__rpc_run_pfs_load_test_default(request)


class DebugBase:

    def profile(
        self, profile: "Profile", filter: "Filter", context: "grpc.ServicerContext"
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def binary(
        self, filter: "Filter", context: "grpc.ServicerContext"
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def dump(
        self, filter: "Filter", limit: int, context: "grpc.ServicerContext"
    ) -> Iterator["betterproto_lib_google_protobuf.BytesValue"]:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def set_log_level(
        self,
        pachyderm: "SetLogLevelRequestLogLevel",
        grpc: "SetLogLevelRequestLogLevel",
        duration: timedelta,
        recurse: bool,
        context: "grpc.ServicerContext",
    ) -> "SetLogLevelResponse":
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def get_dump_v2_template(
        self, filters: Optional[List[str]], context: "grpc.ServicerContext"
    ) -> "GetDumpV2TemplateResponse":
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def dump_v2(
        self,
        system: "System",
        pipelines: Optional[List["Pipeline"]],
        input_repos: bool,
        timeout: timedelta,
        defaults: "DumpV2RequestDefaults",
        starlark_scripts: Optional[List["Starlark"]],
        context: "grpc.ServicerContext",
    ) -> Iterator["DumpChunk"]:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def run_pfs_load_test(
        self,
        spec: str,
        branch: "_pfs__.Branch",
        seed: int,
        state_id: str,
        context: "grpc.ServicerContext",
    ) -> "RunPfsLoadTestResponse":
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def run_pfs_load_test_default(
        self, context: "grpc.ServicerContext"
    ) -> "RunPfsLoadTestResponse":
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    __proto_path__ = "debug_v2.Debug"

    @property
    def __rpc_methods__(self):
        return {
            "Profile": grpc.unary_stream_rpc_method_handler(
                self.profile,
                request_deserializer=ProfileRequest.FromString,
                response_serializer=ProfileRequest.SerializeToString,
            ),
            "Binary": grpc.unary_stream_rpc_method_handler(
                self.binary,
                request_deserializer=BinaryRequest.FromString,
                response_serializer=BinaryRequest.SerializeToString,
            ),
            "Dump": grpc.unary_stream_rpc_method_handler(
                self.dump,
                request_deserializer=DumpRequest.FromString,
                response_serializer=DumpRequest.SerializeToString,
            ),
            "SetLogLevel": grpc.unary_unary_rpc_method_handler(
                self.set_log_level,
                request_deserializer=SetLogLevelRequest.FromString,
                response_serializer=SetLogLevelRequest.SerializeToString,
            ),
            "GetDumpV2Template": grpc.unary_unary_rpc_method_handler(
                self.get_dump_v2_template,
                request_deserializer=GetDumpV2TemplateRequest.FromString,
                response_serializer=GetDumpV2TemplateRequest.SerializeToString,
            ),
            "DumpV2": grpc.unary_stream_rpc_method_handler(
                self.dump_v2,
                request_deserializer=DumpV2Request.FromString,
                response_serializer=DumpV2Request.SerializeToString,
            ),
            "RunPFSLoadTest": grpc.unary_unary_rpc_method_handler(
                self.run_pfs_load_test,
                request_deserializer=RunPfsLoadTestRequest.FromString,
                response_serializer=RunPfsLoadTestRequest.SerializeToString,
            ),
            "RunPFSLoadTestDefault": grpc.unary_unary_rpc_method_handler(
                self.run_pfs_load_test_default,
                request_deserializer=betterproto_lib_google_protobuf.Empty.FromString,
                response_serializer=betterproto_lib_google_protobuf.Empty.SerializeToString,
            ),
        }
