from __future__ import annotations
from typing import Optional

from datatap.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonUser

class User:
    """
    Represents a user account in the dataTap platform.
    """

    _endpoints: ApiEndpoints

    uid: str
    """
    The user's UID.
    """

    username: str
    """
    The user's username.
    """

    email: str
    """
    The user's email address.
    """

    default_database: Optional[str]
    """
    The user's default database
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonUser) -> User:
        """
        Creates a `User` from a `JsonUser`.
        """
        return User(
            endpoints,
            json["uid"],
            username = json["username"],
            email = json["email"],
            default_database = json["defaultDatabase"]
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, username: str, email: str, default_database: Optional[str]):
        self._endpoints = endpoints
        self.uid = uid
        self.username = username
        self.email = email
        self.default_database = default_database

    def __repr__(self) -> str:
        return basic_repr("User", self.uid, username = self.username, email = self.email)