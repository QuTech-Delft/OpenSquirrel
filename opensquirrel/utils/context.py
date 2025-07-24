from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def temporary_class_attr(cls: type[Any], attr: str, value: Any) -> Generator[None, None, None]:
    original_value = getattr(cls, attr)
    setattr(cls, attr, value)
    try:
        yield
    finally:
        setattr(cls, attr, original_value)
