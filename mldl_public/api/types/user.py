from typing_extensions import TypedDict

class JsonUser(TypedDict):
    uid: str
    firstName: str
    lastName: str
    email: str

