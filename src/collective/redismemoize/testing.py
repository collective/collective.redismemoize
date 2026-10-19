"""Test layers, and helpers to test an add-on against a fake Redis.

:data:`REDIS_MEMOIZE_FIXTURE` is for add-on authors: put it in a layer's
bases and every ``@ram.cache`` function goes through this package, backed by
an in-process ``fakeredis`` server instead of a real Redis. Each test starts
with an empty prefix, an empty RAM cache, a closed breaker and no learned
routes. ``fakeredis`` is not a dependency of this package; add it to your
test extra.

:func:`activate` and :func:`deactivate` are the same thing for a test runner
without layers, such as a plain pytest fixture.
"""

from collective.redismemoize import api
from collective.redismemoize import client
from collective.redismemoize import config
from collective.redismemoize.chooser import choose_cache
from collective.redismemoize.routing import router
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.memoize.interfaces import ICacheChooser
from plone.testing import Layer
from plone.testing import zca
from plone.testing.zope import WSGI_SERVER_FIXTURE
from typing import Any
from zope.component import getGlobalSiteManager

import collective.redismemoize
import os


#: What :func:`activate` sets unless told otherwise. The URL is never
#: contacted: the client factory is replaced by ``fakeredis``.
TEST_ENVIRON = {
    "REDIS_MEMOIZE_URL": "redis://fakeredis:6379/0",
    "REDIS_MEMOIZE_PREFIX": "test.memoize",
}

_saved_environ: dict[str, str | None] | None = None


def activate(server: Any = None, **variables: str) -> Any:
    """Point the package at a ``fakeredis`` server.

    :param server: A ``fakeredis.FakeServer``; a new one when omitted.
    :param variables: ``REDIS_MEMOIZE_*`` variables to set on top of
        :data:`TEST_ENVIRON`.
    :returns: The server.
    """
    import fakeredis

    global _saved_environ
    if server is None:
        server = fakeredis.FakeServer()
    environ = {**TEST_ENVIRON, **variables}
    if _saved_environ is None:
        _saved_environ = {name: os.environ.get(name) for name in config.DEFAULTS}
    for name in config.DEFAULTS:
        os.environ.pop(name, None)
    os.environ.update(environ)
    config.reload()
    client.set_factory(lambda settings: fakeredis.FakeRedis(server=server))
    router.reset()
    # Values cached in RAM before activation would answer every Redis miss.
    for cache in api.ram_caches():
        cache.invalidateAll()
    return server


def deactivate() -> None:
    """Restore the environment :func:`activate` changed, and reset the state."""
    global _saved_environ
    if _saved_environ is not None:
        for name, value in _saved_environ.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        _saved_environ = None
    config.reload()
    client.set_factory(None)
    router.reset()


def clean() -> None:
    """Empty the prefix and the RAM cache, close the breaker, forget routes."""
    client.reset()
    api.invalidate_all()
    router.reset()


class RedisMemoizeLayer(Layer):
    """Route ``plone.memoize`` through this package and a fake Redis.

    Loads the package's ``overrides.zcml`` into a stacked component registry,
    so the chooser is in place even in a layer that never loaded this
    package's ZCML.
    """

    defaultBases = (zca.ZCML_DIRECTIVES,)

    def setUp(self) -> None:
        """Register the chooser and activate the fake server."""
        self["configurationContext"] = context = zca.stackConfigurationContext(
            self.get("configurationContext")
        )
        zca.pushGlobalRegistry()
        from zope.configuration import xmlconfig

        xmlconfig.includeOverrides(
            context, "overrides.zcml", package=collective.redismemoize
        )
        context.execute_actions()
        self["redis_server"] = activate()

    def tearDown(self) -> None:
        """Deactivate the fake server and drop the stacked registry."""
        deactivate()
        del self["redis_server"]
        zca.popGlobalRegistry()
        del self["configurationContext"]

    def testSetUp(self) -> None:
        """Start every test from an empty cache, with this package's chooser.

        The registry stacked in :meth:`setUp` is not always the one a test
        sees. A Plone site's component registry is based on the global
        registry of the moment the site was created, so for a layer such as
        ``PLONE_FIXTURE``, set up before or after this one, the stock chooser
        ``plone.memoize`` registered there wins. For the duration of each
        test, every registry in the global chain that registers another
        chooser gets this package's one instead.
        """
        self._replaced_choosers = []
        for registry in _global_registries():
            for registration in registry.registeredUtilities():
                if (
                    registration.provided is ICacheChooser
                    and registration.name == ""
                    and registration.component is not choose_cache
                ):
                    self._replaced_choosers.append((registry, registration.component))
        for registry, _component in self._replaced_choosers:
            registry.registerUtility(choose_cache, ICacheChooser)
        clean()

    def testTearDown(self) -> None:
        """Put back the choosers :meth:`testSetUp` replaced."""
        for registry, component in self.__dict__.pop("_replaced_choosers", []):
            registry.registerUtility(component, ICacheChooser)


def _global_registries() -> list[Any]:
    """Return the global component registry and all its bases.

    :returns: The registries, the current global one first.
    """
    registries: list[Any] = []
    pending = [getGlobalSiteManager()]
    while pending:
        registry = pending.pop(0)
        registries.append(registry)
        pending.extend(registry.__bases__)
    return registries


REDIS_MEMOIZE_FIXTURE = RedisMemoizeLayer()


class PackageLayer(PloneSandboxLayer):
    """The package's ZCML, overrides included, on a Plone site."""

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Load the package's ZCML.

        ``plone.autoinclude`` is disabled in the Plone fixture, so the
        overrides are loaded here the way a real startup would load them.
        """
        self.loadZCML(package=collective.redismemoize)
        from zope.configuration import xmlconfig

        xmlconfig.includeOverrides(
            configurationContext, "overrides.zcml", package=collective.redismemoize
        )
        configurationContext.execute_actions()


FIXTURE = PackageLayer()

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="Collective.RedismemoizeLayer:IntegrationTesting",
)


FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE),
    name="Collective.RedismemoizeLayer:FunctionalTesting",
)
