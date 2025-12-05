from opensquirrel.passes.mapper.mip_mapper import MIPMapper
from opensquirrel.passes.mapper.simple_mappers import HardcodedMapper, IdentityMapper, RandomMapper

try:
    from opensquirrel.passes.mapper.qgym_mapper.qgym_mapper import QGymMapper
except ImportError:
    QGymMapper: type | None = None  # type: ignore[no-redef]

__all__ = [
    "HardcodedMapper",
    "IdentityMapper",
    "MIPMapper",
    "QGymMapper",
    "RandomMapper",
]
