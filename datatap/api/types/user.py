from typing import Optional
from typing_extensions import TypedDict

class JsonUser(TypedDict):
    """
    The API type of an individual user.
    """
    uid: str
    username: str
    email: str
    defaultDatabase: Optional[str]

