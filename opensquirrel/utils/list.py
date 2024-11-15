from __future__ import annotations

import functools
import operator
from typing import Any


def flatten_list(list_to_flatten: list[list[Any]]) -> list[Any]:
    return functools.reduce(operator.iadd, list_to_flatten, [])
