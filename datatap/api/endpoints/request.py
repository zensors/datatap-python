from __future__ import annotations
from datatap.utils.environment import Environment

import json
from base64 import b64encode
from urllib.parse import urljoin
from typing import Generator, Optional, Dict, TypeVar, Generic, Type, Any

import requests

_T = TypeVar("_T")
_S = TypeVar("_S")

class GetRequester(Generic[_T]):
    """
    A callable-class for performing typed `GET` requests to the API.
    """
    api_key: str
    uri: str

    def __init__(self, api_key: str, base_uri: str):
        self.api_key = api_key
        self.uri = base_uri

    def __getitem__(self, s: Type[_S]) -> GetRequester[_S]:
        return self

    def __call__(self, endpoint: str, query_params: Optional[Dict[str, str]] = None) -> _T:
        qualified_uri = urljoin(self.uri, "/api/" + endpoint)
        encoded_api_key = b64encode(bytes(self.api_key, "ascii")).decode("ascii")

        response = requests.get(
            qualified_uri,
            params=query_params,
            headers={
                "Authorization": f"Bearer {encoded_api_key}"
            },
        )

        if not response.ok:
            error: str
            try:
                error = response.json()["error"]
            except:
                error = response.content.decode("ascii")
            raise Exception(error)

        return response.json()

class PostRequester(Generic[_T]):
    """
    A callable-class for performing typed `Post` requests to the API.
    """
    api_key: str
    uri: str

    def __init__(self, api_key: str, base_uri: str):
        self.api_key = api_key
        self.uri = base_uri

    def __getitem__(self, s: Type[_S]) -> PostRequester[_S]:
        return self

    def __call__(self, endpoint: str, body: Dict[str, Any], query_params: Optional[Dict[str, str]] = None) -> _T:
        qualified_uri = urljoin(self.uri, "/api/" + endpoint)
        encoded_api_key = b64encode(bytes(self.api_key, "ascii")).decode("ascii")

        response = requests.post(
            qualified_uri,
            params=query_params,
            headers={
                "Authorization": f"Bearer {encoded_api_key}"
            },
            json=body,
        )

        if not response.ok:
            error: str
            try:
                error = response.json()["error"]
            except:
                error = response.content.decode("ascii")
            raise Exception(error)

        return response.json()

class StreamRequester(Generic[_T]):
    """
    A callable-class for performing typed stream requests to the API.
    """
    api_key: str
    uri: str

    def __init__(self, api_key: str, uri: str):
        self.api_key = api_key
        self.uri = uri

    def __getitem__(self, s: Type[_S]) -> StreamRequester[_S]:
        return self

    def __call__(self, endpoint: str, query_params: Optional[Dict[str, str]] = None) -> Generator[_T, None, None]:
        qualified_uri = urljoin(self.uri, "/api/" + endpoint)
        encoded_api_key = b64encode(bytes(self.api_key, "ascii")).decode("ascii")

        response = requests.get(
            qualified_uri,
            params=query_params,
            headers={
                "Authorization": f"Bearer {encoded_api_key}"
            },
            stream=True
        )

        if not response.ok:
            error: str
            try:
                error = response.json()["error"]
            except:
                error = response.content.decode("ascii")
            raise Exception(error)

        for line in response.iter_lines(decode_unicode=True):
            yield json.loads(line)


class Request:
    """
    A helper class that encapsulates the logic for making requests to the
    dataTap server. It is passed an optional `api_key`, which defaults to
    the `DATATAP_API_KEY` environment variable. It can also be passed a base
    `uri` for connecting to a different dataTap server (such as through a
    proxy).
    """

    get: GetRequester[Any]
    """
    Function for typesafe `GET` requests.
    """

    post: PostRequester[Any]
    """
    Function for typesafe `POST` requests.
    """

    stream: StreamRequester[Any]
    """
    Function for typesafe streaming requests.
    """

    def __init__(self, api_key: Optional[str] = None, base_uri: Optional[str] = None):
        api_key = api_key or Environment.API_KEY
        base_uri = base_uri or Environment.BASE_URI
        if api_key is None:
            raise Exception("No API key available. Either provide it or use the [DATATAP_API_KEY] environment variable")

        self.get = GetRequester[Any](api_key, base_uri)
        self.post = PostRequester[Any](api_key, base_uri)
        self.stream = StreamRequester[Any](api_key, base_uri)

class ApiNamespace:
    """
    Base class for API endpoints.
    """
    def __init__(self, request: Request):
        self.request = request
        self.get = request.get
        self.post = request.post
        self.stream = request.stream
