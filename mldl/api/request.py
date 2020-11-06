from __future__ import annotations

import os
import json
from base64 import b64encode
from urllib.parse import urljoin
from typing import Generator, Optional, Dict, TypeVar, Generic, Type, Any

import requests

# TODO(zwade): replace this with the real URI
DEFAULT_API_URI = os.getenv("MLDL_API_URI", "http://10.11.18.50:8080")

_T = TypeVar("_T")
_S = TypeVar("_S")

class GetRequester(Generic[_T]):
    api_key: str
    uri: str

    def __init__(self, api_key: str, uri: str):
        self.api_key = api_key
        self.uri = uri

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

class StreamRequester(Generic[_T]):
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

        for line in response.iter_lines(decode_unicode=True):
            yield json.loads(line)


class Request:
    def __init__(self, api_key: Optional[str] = None, uri: Optional[str] = None):
        api_key = api_key or os.getenv("MLDL_API_KEY")
        uri = uri or DEFAULT_API_URI
        if api_key is None:
            raise Exception("No API key available. Either provide it or use the [MLDL_API_KEY] environment variable")

        self.get = GetRequester[Any](api_key, uri)
        self.stream = StreamRequester[Any](api_key, uri)

class ApiNamespace:
    def __init__(self, request: Request):
        self.request = request
        self.get = request.get
        self.stream = request.stream
