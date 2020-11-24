"""
The `datatap.api` module provides two different interfaces for the API.

The simplest of these is found in `endpoints`, and contains classes and methods
for directly interfacing with the API using its HTTP/JSON protocol.

The more powerful interface is the `entities` interface, which wraps these
endpoints into python objects with convenience methods for accessing other
entities.
"""

__all__ = [
    "endpoints",
    "entities",
    "types",
]