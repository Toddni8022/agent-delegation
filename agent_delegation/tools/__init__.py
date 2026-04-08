"""Utility tools for practical infrastructure workflows."""

from __future__ import annotations

from typing import Any

__all__ = (
    "CabinetLocation",
    "FiberRunEstimate",
    "calculate_fiber_run",
    "load_cabinet_locations",
)


def __getattr__(name: str) -> Any:
    """Lazy-load tool symbols to avoid import side effects."""
    if name in __all__:
        from . import fiber_run_estimator

        return getattr(fiber_run_estimator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
