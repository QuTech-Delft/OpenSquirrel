from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar, cast

_T = TypeVar("_T")


class Singleton(type, Generic[_T]):
    _instances: ClassVar[dict[type, Any]] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> _T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cast(_T, cls._instances[cls])
