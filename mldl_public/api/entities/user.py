from mldl_public.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonUser

class User:
    _endpoints: ApiEndpoints

    uid: str
    first_name: str
    last_name: str
    email: str

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonUser):
        return User(
            endpoints,
            json["uid"],
            first_name = json["firstName"],
            last_name = json["lastName"],
            email = json["email"]
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, first_name: str, last_name: str, email: str):
        self._endpoints = endpoints
        self.uid = uid
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def __repr__(self):
        return basic_repr("User", self.uid, first_name = self.first_name, last_name = self.last_name, email = self.email)