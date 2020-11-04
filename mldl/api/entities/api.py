from typing import Optional

from .user import User
from .database import Database
from ..endpoints import ApiEndpoints

class Api:
    def __init__(self, api_key: Optional[str] = None, uri: Optional[str] = None):
        self.endpoints = ApiEndpoints(api_key, uri)

    def get_current_user(self):
        return User.from_json(self.endpoints, self.endpoints.user.current())

    def get_database_list(self):
        return [
            Database.from_json(self.endpoints, json_db)
            for json_db in self.endpoints.database.list()
        ]

    def get_database_by_uid(self, uid: str):
        return Database.from_json(self.endpoints, self.endpoints.database.query(uid))
