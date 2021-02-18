from __future__ import annotations

from comet_ml.query import QueryExpression


class QueryExpression:
    def startswith(self, prefix: str) -> QueryExpression: ...

class Tag(QueryExpression):
    def __init__(self, tag: str) -> Tag: ...

class Metadata(QueryExpression):
    def __init__(self, metadata: str) -> Metadata: ...