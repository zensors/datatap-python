from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Union, Mapping

from io import BufferedReader

from typing_extensions import Literal

class Experiment:
    id: str
    context: str

    def __init__(
        self,
        api_key: Optional[str] = ...,
        project_name: Optional[str] = ...,
        workspace: Optional[str] = ...,
        log_code: bool = ...,
        log_graph: bool = ...,
        auto_param_logging: bool = ...,
        auto_metric_logging: bool = ...,
        auto_weight_logging: bool = ...,
        auto_output_logging: bool = ...,
        auto_log_co2: bool = ...,
        parse_args: bool = ...,
        log_env_details: bool = ...,
        log_env_gpu: bool = ...,
        log_env_cpu: bool = ...,
        log_env_host: bool = ...,
        log_git_metadata: bool = ...,
        log_git_patch: bool = ...,
        display_summary_level: int = ...,
        disabled: bool = ...
    ) -> Experiment: ...

    def set_step(self, step: int) -> None: ...
    def log_asset(
        self,
        file_data: str | BufferedReader,
        file_name: Optional[str] = ...,
        overwrite: bool = ...,
        copy_to_tmp: bool = ...,
        step: Optional[int] = ...
    ) -> None: ...
    def log_asset_data(
        self,
        data: str | bytes,
        name: Optional[str] = ...,
        overwrite: bool = ...,
        step: Optional[int] = ...,
        metadata: Optional[Any] = ...,
        file_name: Optional[str] = ...
    ) -> None: ...
    def log_metric(
        self,
        name: str,
        value: str,
        step: Optional[int] = ...,
        epoch: Optional[int] = ...,
        include_context: bool = ...
    ) -> None: ...
    def log_metrics(
        self,
        dict: Dict[str, str],
        prefix: Optional[str] = ...,
        step: Optional[int] = ...,
        epoch: Optional[int] = ...
    ) -> None: ...
    def log_table(
        self,
        filename: str,
        tabular_data: Optional[Sequence[Sequence[Any]]] = ...,
        headers: Literal[False] | Sequence[str] = ...
    ) -> None: ...
    def log_model(
        self,
        name: str,
        file_or_folder: str,
        file_name: Optional[str] = ...,
        overwrite: bool = ...,
        metadata: Any = ...,
        copy_to_tmp: bool = ...
    ) -> None: ...
    def log_confusion_matrix(
        self,
        y_true: Optional[List[int]] = ...,
        y_predicted: Optional[Sequence[int]] = ...,
        matrix: Optional[List[List[Any]]] = ...,
        labels: Optional[List[str]] = ...,
        title: str = ...,
        row_label: str = ...,
        column_label: str = ...,
        max_examples_per_cell: int = ...,
        max_categories: int = ...,
        winner_function: Optional[Callable[[List[List[int]]], int]] = ...,
        index_to_example_function: Optional[Callable[[int], str | int | Dict[str, str]]] = ...,
        cache: bool = ...,
        file_name: str = ...,
        overwrite: bool = ...,
        step: Optional[int] = ...
    ) -> None: ...
    def log_parameter(
        self,
        name: str,
        value: Union[float, int, bool, str, List[Any]],
        step: Optional[int] = ...,
    ) -> None: ...
    def log_parameters(
        self,
        parameters: Mapping[str, Any],
        prefix: Optional[str] = ...,
        step: Optional[int] = ...,
    ) -> None: ...

    @contextmanager
    def context_manager(name: str) -> Iterator[Experiment]: ...