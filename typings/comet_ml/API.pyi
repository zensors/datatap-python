from typing import List, Optional, overload

from typing_extensions import TypedDict

from .APIExperiment import APIAsset, APIExperiment
from .query import QueryExpression

class APIProject(TypedDict):
    projectId: str
    projectName: str
    ownerUserName: str
    projectDescription: str
    workspaceName: str
    numberOfExperiments: int
    lastUpdated: int
    public: bool

class APIRegistryExperimentModel(TypedDict):
    experimentModelId: str
    experimentModelName: str
    experimentKey: str

class APIRegistryVersion(TypedDict):
    registryModelItemId: str
    experimentModel: APIRegistryExperimentModel
    version: str
    comment: str
    stages: List[str]
    userName: str
    createdAt: int
    lastUpdated: int
    assets: List[APIAsset]
    restApiUrl: str

class APIRegistryModel(TypedDict):
    registryModelId: str
    modelName: str
    description: str
    isPublic: bool
    createdAt: int
    lastUpdate: int
    userName: str
    versions: List[APIRegistryVersion]

class API:
    def __init__(self, api_key: Optional[str] = ...) -> API: ...

    def query(
        self,
        workspace: str,
        project_name: str,
        query: QueryExpression,
        archived: bool = ...
    ) -> List[APIExperiment]: ...

    # From a type perspective, these could be collapsed into two overloads
    # but each one is doing something different, so i preferred to make it
    # explicit
    @overload
    def get(self) -> List[str]: ...
    @overload
    def get(self, workspace: str = ...) -> List[str]: ...
    @overload
    def get(self, workspace: str = ..., project_name: str = ...) -> List[str]: ...
    @overload
    def get(self, workspace: str = ..., project_name: str = ..., experiment: str = ...) -> APIExperiment: ...

    def get_experiment(self, workspace: str = ..., project_name: str = ..., experiment: str = ...) -> APIExperiment: ...
    def get_project(self, workspace: str, project_name: str) -> APIProject: ...
    def get_projects(self, workspace: str) -> List[APIProject]: ...

    def update_registry_model_version(
        self,
        workspace: str,
        registry_name: str,
        version: str,
        comment: Optional[str] = ...,
        stages: Optional[List[str]] = ...
    ) -> None: ...
    def get_registry_model_details(
        self,
        workspace: str,
        registry_name: str,
        version: Optional[str] = ...
    ) -> APIRegistryModel: ...
    def get_registry_model_names(self, workspace: str) -> List[str]: ...