from typing import Optional

from .Experiment import Experiment


class ExistingExperiment(Experiment):

    def __init__(
        self,
        api_key: Optional[str] = ...,
        previous_experiment: Optional[str] = ...,
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
    ) -> ExistingExperiment: ...
