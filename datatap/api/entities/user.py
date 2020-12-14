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

    first_name: str
    """
    The user's first name.
    """

    last_name: str
    """
    The user's last name.
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
            first_name = json["firstName"],
            last_name = json["lastName"],
            email = json["email"],
            default_database = json["defaultDatabase"]
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, first_name: str, last_name: str, email: str, default_database: Optional[str]):
        self._endpoints = endpoints
        self.uid = uid
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.default_database = default_database

    def __repr__(self) -> str:
        return basic_repr("User", self.uid, first_name = self.first_name, last_name = self.last_name, email = self.email)