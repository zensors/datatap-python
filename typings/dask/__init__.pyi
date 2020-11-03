from typing import Callable, TypeVar, overload
from .delayed import Delayed

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")

T = TypeVar("T")

@overload
def delayed(fn: Callable[[A], T]) -> Callable[[A], Delayed[T]]: ...
@overload
def delayed(fn: Callable[[A, B], T]) -> Callable[[A, B], Delayed[T]]: ...
@overload
def delayed(fn: Callable[[A, B, C], T]) -> Callable[[A, B, C], Delayed[T]]: ...
@overload
def delayed(fn: Callable[[A, B, C, D], T]) -> Callable[[A, B, C, D], Delayed[T]]: ...
@overload
def delayed(fn: Callable[[A, B, C, D, E], T]) -> Callable[[A, B, C, D, E], Delayed[T]]: ...
def delayed(fn: Callable[..., T]) -> Callable[..., Delayed[T]]: ...
