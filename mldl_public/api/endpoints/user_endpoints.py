from .request import ApiNamespace
from ..types import JsonUser

class User(ApiNamespace):
    def current(self):
        return self.get[JsonUser]("/user")
