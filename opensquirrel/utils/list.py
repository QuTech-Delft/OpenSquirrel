from __future__ import annotations

import functools
import operator
from typing import TypeVar

T = TypeVar("T")  # Define type variable "T"


def flatten_list(list_to_flatten: list[list[T]]) -> list[T]:
    return functools.reduce(operator.iadd, list_to_flatten, [])
