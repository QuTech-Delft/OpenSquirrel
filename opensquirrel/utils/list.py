from __future__ import annotations

import functools
import operator
from typing import Any


def flatten_list(list_to_flatten: list[list[Any]]) -> list[Any]:
    return functools.reduce(operator.iadd, list_to_flatten, [])


def flatten_irregular_list(list_to_flatten: list[Any]) -> list[Any]:
    if isinstance(list_to_flatten, list):
        return [element for i in list_to_flatten for element in flatten_irregular_list(i)]

    return [list_to_flatten]
