from typing import List, Optional

from .user import User
from .database import Database
from ..endpoints import ApiEndpoints

class Api:
    """
    The `Api` object is the primary method of interacting with the MLDL API.

    The `Api` constructor takes two optional arguments.

    The first, `api_key`, should be the current user's personal API key. In
    order to encourage good secret practices, this class will use the value
    found in the `MLDL_API_KEY` if no key is passed in. Consider using
    environment variables or another secret manager for your API keys.

    The second argument is `uri`. This should only be used if you would like
    to target a different API server than the default. For instance, if you
    are using a proxy to reach the API, you can use the `uri` argument to
    point toward your proxy.

    This object encapsulates most of the logic for interacting with API.
    For instance, to get a list of all datasets that a user has access to,
    you can run

    ```py
    from mldl_public import Api

    api = Api()
    print([
        dataset
        for database in api.get_database_list()
        for dataset in database.get_dataset_list()
    ])
    ```

    For more details on the functionality provided by the Api object, take
    a look at its documentation.
    """
    def __init__(self, api_key: Optional[str] = None, uri: Optional[str] = None):
        self.endpoints = ApiEndpoints(api_key, uri)

    def get_current_user(self) -> User:
        """
        Returns the current logged-in user.
        """
        return User.from_json(self.endpoints, self.endpoints.user.current())

    def get_database_list(self) -> List[Database]:
        """
        Returns a list of all databases that the current user has access to.
        """
        return [
            Database.from_json(self.endpoints, json_db)
            for json_db in self.endpoints.database.list()
        ]

    def get_default_database(self) -> Database:
        """
        Returns the default database for the user (this defaults to the public
        database).
        """

        # TODO(zwade): Have a way of specifying a per-user default
        db_list = self.get_database_list()

        if len(db_list) == 0:
            raise Exception("Trying to find the default database, but none is specified")
        if len(db_list) > 1:
            raise Exception("Trying to find the default database, but too many are specified")

        return db_list[0]

    def get_database_by_uid(self, uid: str) -> Database:
        """
        Queries a database by its UID and returns it.
        """
        return Database.from_json(self.endpoints, self.endpoints.database.query(uid))
