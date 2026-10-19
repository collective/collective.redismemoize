"""Test suite for collective.redismemoize.

Every directory is a package: shared values live in its ``__init__``, test
modules import them relatively, and ``conftest`` modules hold fixtures only.

========================  ===================================================
Package                   What it tests
========================  ===================================================
``unit``                  Pure Python, no Plone layer, ``fakeredis``.
``spikes``                How Plone and plone.memoize behave, pinned so an
                          upstream change breaks a test rather than a site.
``integration``           The chooser and plone.memoize on a Plone site.
``functional``            The REST endpoint, over HTTP.
``docs``                  The documentation's generated examples and tables.
``docker``                Real Redis and Valkey servers; marked ``docker``.
``setup``                 What loading the package registers.
========================  ===================================================
"""

#: The prefix every test that activates the package uses.
PREFIX = "test.memoize"

#: A function name for tests that drive an adapter directly.
FUN_NAME = "tests.sample.compute"
