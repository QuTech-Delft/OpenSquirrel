from __future__ import annotations

import typing as t

_T = t.TypeVar("_T")


class Singleton(type, t.Generic[_T]):
    _instances: t.ClassVar[dict[type, t.Any]] = {}

    def __call__(cls, *args: t.Any, **kwargs: t.Any) -> _T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return t.cast(_T, cls._instances[cls])
