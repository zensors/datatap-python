from typing_extensions import TypedDict
from .request import ApiNamespace

class ApiUser(TypedDict):
    uid: str
    firstName: str
    lastName: str
    email: str

class User(ApiNamespace):
    def current(self):
        return self.get[ApiUser]("/user")
