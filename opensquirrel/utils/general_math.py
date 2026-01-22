import math


def acos(value: float) -> float:
    """Fix float approximations like 1.0000000000002, which acos does not like."""
    value = max(min(value, 1.0), -1.0)
    return math.acos(value)


def are_axes_consecutive(axis_a_index: int, axis_b_index: int) -> bool:
    """Check if axis 'a' immediately precedes axis 'b' (in a circular fashion [x, y, z, x...])."""
    return axis_a_index - axis_b_index in (-1, 2)
