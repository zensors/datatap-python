from typing import List, TypeVar

_T = TypeVar("_T")

def assert_one(item_list: List[_T]) -> _T:
    """
    Given a list of items, asserts that the list is a singleton,
    and returns its value.
    """
    if len(item_list) != 1:
        raise AssertionError(f"Expected one item in list, but found {len(item_list)}", item_list)

    return item_list[0]