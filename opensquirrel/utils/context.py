from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def temporary_class_attr(cls: type[Any], attr: str, value: Any) -> Generator[None, None, None]:
    """Context method to temporarily assign a value to a class attribute.

    The assigned value will only be held within the context.

    Args:
        cls: Class of which the class attribute value is to be assigned.
        attr: Name of class attribute.
        value: Value to assign to class attribute (must be correct type).
    """
    original_value = getattr(cls, attr)
    setattr(cls, attr, value)
    try:
        yield
    finally:
        setattr(cls, attr, original_value)
