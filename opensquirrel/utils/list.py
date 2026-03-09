from __future__ import annotations

import functools
import operator
from typing import Any


def flatten_list(list_to_flatten: list[list[Any]]) -> list[Any]:
    """Flattens a list of lists into a single list.

    Args:
        list_to_flatten (list[list[Any]]): The list of lists to flatten.

    Returns:
        A single flattened list.

    """
    return functools.reduce(operator.iadd, list_to_flatten, [])
