from typing import Any, List, Optional, overload

from typing_extensions import Literal, TypedDict

class APIAsset(TypedDict):
    fileName: str
    fileSize: int
    runContext: Optional[str]
    step: Optional[int]
    link: str
    createdAt: int
    dir: str
    canView: bool
    audio: bool
    video: bool
    histogram: bool
    image: bool
    type: str
    metadata: Any
    assetId: str

class APIMetrics(TypedDict):
    metricName: str
    metricValue: str
    timestamp: int
    step: int
    epoch: Optional[int]
    runContext: Optional[str]

class APIMetricsSummary(TypedDict):
    name: str
    valueMax: str
    valueMin: str
    timestampMax: int
    timestampMin: int
    timestampCurrent: int
    stepMax: int
    stepMin: int
    stepCurrent: int
    valueCurrent: str

class APIMetadata(TypedDict):
    archived: bool
    durationMillis: int
    endTimeMillis: int
    experimentKey: str
    experimentName: Optional[str]
    fileName: Optional[str]
    filePatah: Optional[str]
    projectId: str
    projectName: str
    running: bool
    startTimeMillis: int
    throttle: bool
    workspaceName: str


class APIExperiment:
    id: str
    url: str
    name: str
    start_server_timestamp: int

    def __init__(self, *args: Any, **kwargs: Any) -> APIExperiment: ...

    def add_tags(self, tags: List[str]) -> None: ...
    @overload
    def get_asset(self, asset_id: str, return_type: Literal["binary"] = ...) -> bytes: ...
    @overload
    def get_asset(self, asset_id: str, return_type: Literal["text"]) -> str: ...
    @overload
    def get_asset(self, asset_id: str, return_type: str) -> str | bytes: ...
    def get_asset_list(self, asset_type: str = ...) -> List[APIAsset]: ...
    def get_model_asset_list(self, model_name: str) -> List[APIAsset]: ...
    def download_model(self, name: str, output_path: str = ..., expand: bool = ...) -> None: ...
    def register_model(
        self,
        model_name: str,
        version: str = ...,
        workspace: Optional[str] = ...,
        registry_name: Optional[str] = ...,
        description: Optional[str] = ...,
        comment: Optional[str] = ...,
        stages: Optional[List[str]] = ...
    ) -> None: ...
    def get_metrics(self, metric: Optional[str] = ...) -> List[APIMetrics]: ...
    def log_other(self, key: str, value: Any, timestamp: Optional[int] = ...) -> None: ...
    def get_tags(self) -> List[str]: ...
    def get_metadata(self) -> APIMetadata: ...
    @overload
    def get_metrics_summary(self) -> List[APIMetricsSummary]: ...
    @overload
    def get_metrics_summary(self, metric: str) -> APIMetricsSummary: ...
    @overload
    def get_others_summary(self) -> List[APIMetricsSummary]: ...
    @overload
    def get_others_summary(self, other: str) -> List[str]: ...
