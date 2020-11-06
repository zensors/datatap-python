from typing import Optional

from .request import Request
from .user_endpoints import User
from .database_endpoints import Database
from .dataset_endpoints import Dataset

class API:
    def __init__(self, api_key: Optional[str] = None, uri: Optional[str] = None):
        self.request = Request(api_key, uri)

        self.user = User(self.request)
        self.database = Database(self.request)
        self.dataset = Dataset(self.request)