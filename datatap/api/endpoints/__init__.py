"""
Encapsulates all of the raw API requests.

In most cases, it is preferable to interact with the api through the
`datatap.api.entities` submodule. However, this module can be used
as well.

```py
from datatap.api.endpoints import ApiEndpoints

api_endpoints = ApiEndpoints()

print(api_endpoints.user.current())
print(api_endpoints.database.list())
```
"""

from .endpoints import ApiEndpoints

__all__ = [
    "ApiEndpoints"
]