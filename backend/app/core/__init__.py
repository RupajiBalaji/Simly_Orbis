"""Core simulation engine interfaces and registry."""

from app.core.base import DistrictType, RealityCheck, RunResult, SimModule
from app.core.registry import clear_registry, get_module, list_modules, register
from app.core.version import ENGINE_VERSION

__all__ = [
    "DistrictType",
    "ENGINE_VERSION",
    "RealityCheck",
    "RunResult",
    "SimModule",
    "clear_registry",
    "get_module",
    "list_modules",
    "register",
]
