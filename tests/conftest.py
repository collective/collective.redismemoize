"""Layers, and the fixtures more than one test package needs."""

from collections.abc import Iterator
from collective.redismemoize import testing
from collective.redismemoize.testing import FUNCTIONAL_TESTING
from collective.redismemoize.testing import INTEGRATION_TESTING
from pytest_plone import fixtures_factory
from tests import PREFIX
from typing import Any

import pytest


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory((
        (FUNCTIONAL_TESTING, "functional"),
        (INTEGRATION_TESTING, "integration"),
    ))
)


@pytest.fixture
def activate() -> Iterator[Any]:
    """Return a callable that activates the package against ``fakeredis``.

    Call it with ``REDIS_MEMOIZE_*`` variables to override the defaults of
    :data:`collective.redismemoize.testing.TEST_ENVIRON`. Everything is
    restored after the test, whether or not it was called.

    :returns: Callable returning the ``fakeredis.FakeServer``.
    """

    def func(**variables: str) -> Any:
        return testing.activate(**{"REDIS_MEMOIZE_PREFIX": PREFIX, **variables})

    yield func
    testing.deactivate()


@pytest.fixture
def redis_server(activate) -> Any:
    """Activate the package with the default test settings.

    :returns: The ``fakeredis.FakeServer`` the package talks to.
    """
    return activate()


@pytest.fixture
def redis_client(redis_server) -> Any:
    """Return a client on the same fake server, to inspect what was stored.

    :param redis_server: The fake server.
    :returns: A ``fakeredis.FakeRedis``.
    """
    import fakeredis

    return fakeredis.FakeRedis(server=redis_server)
