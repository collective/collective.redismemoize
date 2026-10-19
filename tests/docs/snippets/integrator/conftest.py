from collective.redismemoize.testing import REDIS_MEMOIZE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from pytest_plone import fixtures_factory


pytest_plugins = ["pytest_plone"]

INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_FIXTURE, REDIS_MEMOIZE_FIXTURE),
    name="MyAddon:RedisIntegrationTesting",
)

globals().update(fixtures_factory(((INTEGRATION_TESTING, "integration"),)))
