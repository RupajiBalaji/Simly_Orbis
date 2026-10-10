"""
Simulation module registry.

Holds registered district modules and provides lookup mechanisms.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.base import SimModule

log = logging.getLogger(__name__)

_REGISTRY: dict[str, SimModule] = {}


def register(module: SimModule) -> None:
    """Register a simulation module singleton."""
    if not module.id:
        raise ValueError("Module must have a non-empty 'id'")
    _REGISTRY[module.id] = module
    log.info("Registered simulation module: %s (%s)", module.id, module.district)


def get_module(module_id: str) -> SimModule:
    """
    Retrieve a simulation module by its identifier.

    Raises KeyError if the module is unknown.
    """
    if module_id not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(
            f"Unknown simulation module '{module_id}'. Available modules: {available}"
        )
    return _REGISTRY[module_id]


def list_modules() -> list[SimModule]:
    """Return all currently registered simulation modules."""
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Clear all registered modules (used in tests)."""
    _REGISTRY.clear()
