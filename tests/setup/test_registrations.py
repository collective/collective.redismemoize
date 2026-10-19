"""The package registers a chooser and a service, and no profile."""

from . import SERVICE
from collective.redismemoize import PACKAGE_NAME
from collective.redismemoize.chooser import choose_cache
from plone.memoize.interfaces import ICacheChooser
from plone.rest.interfaces import IService
from Products.CMFCore.interfaces import ISiteRoot
from zope.component import getGlobalSiteManager
from zope.component import queryUtility

import pytest


def services(method: str) -> list:
    """Return the registered ``@redismemoize`` services for one method."""
    return [
        registration
        for registration in getGlobalSiteManager().registeredAdapters()
        if registration.name == f"{method}_application_json_{SERVICE}"
    ]


class TestRegistrations:
    def test_chooser(self, portal):
        """The ICacheChooser utility is ours."""
        assert queryUtility(ICacheChooser) is choose_cache

    @pytest.mark.parametrize("method", ["GET", "POST"])
    def test_service(self, portal, method: str):
        """The service is registered for the site root, for every layer."""
        (registration,) = services(method)
        assert registration.required[0] is ISiteRoot
        assert IService.implementedBy(registration.factory)

    @pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
    def test_no_other_methods(self, portal, method: str):
        """Nothing else is registered under the service name."""
        assert services(method) == []


class TestNoProfile:
    def test_no_profiles(self, portal, setup_tool):
        """No GenericSetup profile belongs to the package."""
        profiles = [p["id"] for p in setup_tool.listProfileInfo()]
        assert [p for p in profiles if p.startswith(f"{PACKAGE_NAME}:")] == []

    def test_profiles_are_listed(self, portal, setup_tool):
        """Control: the listing the test above reads is not empty."""
        profiles = [p["id"] for p in setup_tool.listProfileInfo()]
        assert "plone.app.contenttypes:default" in profiles
