"""The chooser's decision, without a Plone layer."""

from collective.redismemoize import config
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.chooser import choose_cache
from plone.memoize.ram import RAMCacheAdapter
from tests import FUN_NAME

import pytest


@pytest.fixture
def environment(monkeypatch):
    """Return a callable that sets variables and reloads the settings."""

    def func(**variables: str) -> None:
        for name in config.DEFAULTS:
            monkeypatch.delenv(name, raising=False)
        for name, value in variables.items():
            monkeypatch.setenv(name, value)
        config.reload()

    yield func
    monkeypatch.undo()
    config.reload()


def test_inactive_is_stock(environment):
    """No URL: the stock RAM adapter, and never a Redis one."""
    environment()
    adapter = choose_cache(FUN_NAME)
    assert type(adapter) is RAMCacheAdapter
    assert adapter.globalkey == FUN_NAME


def test_active(environment):
    """A URL: a Redis adapter, built without contacting Redis."""
    environment(REDIS_MEMOIZE_URL="redis://127.0.0.1:1/0")
    assert isinstance(choose_cache(FUN_NAME), RedisCacheAdapter)


def test_excluded(environment):
    """An excluded function: the stock RAM adapter."""
    environment(
        REDIS_MEMOIZE_URL="redis://127.0.0.1:1/0", REDIS_MEMOIZE_EXCLUDE="tests.*"
    )
    assert type(choose_cache(FUN_NAME)) is RAMCacheAdapter
