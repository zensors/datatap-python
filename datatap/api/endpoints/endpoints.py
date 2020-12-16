from datatap.api.endpoints.repository_endpoints import Repository
from typing import Optional

from .request import Request
from .user_endpoints import User
from .database_endpoints import Database
from .dataset_endpoints import Dataset

class ApiEndpoints:
    """
    Class for performing raw API requests.
    """

    user: User
    """
    User endpoints.
    """

    database: Database
    """
    Database endpoints.
    """

    repository: Repository
    """
    Repository endpoints.
    """

    dataset: Dataset
    """
    Dataset endpoints.
    """

    _request: Request

    def __init__(self, api_key: Optional[str] = None, uri: Optional[str] = None):
        self._request = Request(api_key, uri)

        self.user = User(self._request)
        self.database = Database(self._request)
        self.repository = Repository(self._request)
        self.dataset = Dataset(self._request)