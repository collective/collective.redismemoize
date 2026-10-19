"""Load ZCML the way a real Zope startup does, and report the cache chooser.

Run in a subprocess by ``test_spike_startup``: the global component registry
it fills cannot be torn down, so it must not be the test process's.

The ``site.zcml`` below is the one ``cookiecutter-zope-instance`` generates.
It is loaded with the two steps ``Zope2.App.startup.startup()`` takes before
opening the database: ``import_products()`` and ``load_site()``. With no
``disable-autoinclude`` feature, ``Products.CMFPlone`` runs
``plone.autoinclude`` for every distribution whose ``z3c.autoinclude.plugin``
entry point targets ``plone``, overrides included.

Usage: ``python startup.py [--disable-autoinclude] [ZCML ...]``, where each
``ZCML`` is a snippet added to ``site.zcml``, inside ``<configure>``, before
the products load. Prints one JSON line.
"""

from pathlib import Path

import json
import sys
import tempfile


SITE_ZCML = """\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:meta="http://namespaces.zope.org/meta"
    xmlns:five="http://namespaces.zope.org/five">
  {features}
  <include package="Products.Five" />
  <meta:redefinePermission from="zope2.Public" to="zope.Public" />
  <five:loadProducts file="meta.zcml"/>
  {snippets}
  <five:loadProducts />
  <five:loadProductsOverrides />
  <securityPolicy component="AccessControl.security.SecurityPolicy" />
</configure>
"""

DISABLE_AUTOINCLUDE = '<meta:provides feature="disable-autoinclude" />'


def main(argv: list[str]) -> None:
    """Load the site ZCML and print where the chooser comes from.

    :param argv: Command line arguments, without the program name.
    """
    features = ""
    if argv and argv[0] == "--disable-autoinclude":
        features = DISABLE_AUTOINCLUDE
        argv = argv[1:]
    from App.config import getConfiguration
    from OFS.Application import import_products
    from plone.memoize.interfaces import ICacheChooser
    from zope.component import queryUtility

    import Zope2.App.zcml

    with tempfile.TemporaryDirectory() as tmp:
        etc = Path(tmp) / "etc"
        etc.mkdir()
        (etc / "site.zcml").write_text(
            SITE_ZCML.format(features=features, snippets="\n  ".join(argv))
        )
        getConfiguration().instancehome = tmp
        import_products()
        Zope2.App.zcml.load_site(force=True)
    chooser = queryUtility(ICacheChooser)
    print(json.dumps({"chooser": f"{chooser.__module__}.{chooser.__name__}"}))


if __name__ == "__main__":
    main(sys.argv[1:])
