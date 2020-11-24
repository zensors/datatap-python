from .request import ApiNamespace
from ..types import JsonUser

class User(ApiNamespace):
    """
    Raw API for interacting with user endpoints.
    """
    def current(self) -> JsonUser:
        """
        Returns a `JsonUser` representing the logged in user.
        """
        return self.get[JsonUser]("/user")
