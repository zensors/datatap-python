from typing import Any, Dict, Generator, Optional, overload

from typing_extensions import Literal

class Response:
    content: bytes
    ok: bool

    def json(self) -> Any: ...
    @overload
    def iter_lines(self, *, decode_unicode: Literal[True], chunk_size: int = ...) -> Generator[str, None, None]: ...
    @overload
    def iter_lines(self, *,  decode_unicode: Optional[Literal[False]] = ..., chunk_size: int = ...) -> Generator[bytes, None, None]: ...

def get(
    url: str,
    params: Dict[str, str] | None = ...,
    headers: Dict[str, str | None] | None = ...,
    stream: bool = ...,
) -> Response: ...

def post(
    url: str,
    params: Dict[str, str] | None = ...,
    headers: Dict[str, str | None] | None = ...,
    stream: bool = ...,
    json: Any = ...
) -> Response: ...