from typing_extensions import TypedDict

class JsonUser(TypedDict):
    """
    The API type of an individual user.
    """
    uid: str
    firstName: str
    lastName: str
    email: str
