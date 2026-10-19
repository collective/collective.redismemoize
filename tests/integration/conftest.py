"""Fixtures for the integration package; everything runs on ``portal``."""

from . import CALLS
from collections.abc import Callable
from collective.redismemoize.routing import router as process_router
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _clean_calls(portal) -> None:
    """Forget the calls recorded by earlier tests; needs the layer."""
    CALLS.clear()


@pytest.fixture
def routes() -> Callable[[], dict[str, Any]]:
    """Return a callable reading the process router's snapshot."""
    return process_router.snapshot
