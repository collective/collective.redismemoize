"""Fixtures to build the package's objects by hand, without Plone."""

from . import Clock
from collections.abc import Callable
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.client import Connection
from collective.redismemoize.config import Settings
from collective.redismemoize.routing import Router
from plone.memoize.ram import RAMCacheAdapter
from tests import FUN_NAME
from tests import PREFIX
from typing import Any
from zope.ramcache.ram import RAMCache

import fakeredis
import pytest


@pytest.fixture
def clock() -> Clock:
    """Return a clock the test moves by hand."""
    return Clock()


@pytest.fixture
def settings() -> Settings:
    """Return active settings with the test prefix."""
    return Settings(url="redis://fakeredis:6379/0", prefix=PREFIX)


@pytest.fixture
def server() -> fakeredis.FakeServer:
    """Return an empty fake Redis server."""
    return fakeredis.FakeServer()


@pytest.fixture
def inspector(server) -> fakeredis.FakeRedis:
    """Return a client on the fake server, to read what the code wrote."""
    return fakeredis.FakeRedis(server=server)


@pytest.fixture
def connection(settings, server, clock) -> Connection:
    """Return a connection to the fake server, on the test clock."""
    return Connection(
        settings, factory=lambda s: fakeredis.FakeRedis(server=server), clock=clock
    )


@pytest.fixture
def router() -> Router:
    """Return an empty router."""
    return Router()


@pytest.fixture
def ramcache() -> RAMCache:
    """Return an empty RAM cache, as ``plone.memoize``'s ``global_cache``."""
    cache = RAMCache()
    cache.update(maxAge=86400)
    return cache


@pytest.fixture
def make_adapter(settings, ramcache, router, connection) -> Callable[..., Any]:
    """Return a factory of adapters sharing this test's objects.

    :returns: Callable taking an optional ``fun_name`` and keyword overrides.
    """

    def func(fun_name: str = FUN_NAME, **kwargs: Any) -> RedisCacheAdapter:
        options = {
            "settings": settings,
            "ram": RAMCacheAdapter(ramcache, globalkey=fun_name),
            "router": router,
            "connection": connection,
            **kwargs,
        }
        return RedisCacheAdapter(fun_name, **options)

    return func


@pytest.fixture
def adapter(make_adapter) -> RedisCacheAdapter:
    """Return an adapter for :data:`tests.FUN_NAME`."""
    return make_adapter()
