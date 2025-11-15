from opensquirrel.passes.mapper.mip_mapper import MIPMapper
from opensquirrel.passes.mapper.qgym_mapper import QGymMapper
from opensquirrel.passes.mapper.simple_mappers import HardcodedMapper, IdentityMapper, RandomMapper

try:
    from opensquirrel.passes.mapper.qgym_mapper import QGymMapper
except ImportError:
    QGymMapper = None

__all__ = [
    "HardcodedMapper",
    "IdentityMapper",
    "MIPMapper",
    "QGymMapper",
    "RandomMapper",
]
