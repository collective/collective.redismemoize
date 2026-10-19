"""The override wins in a real startup, and how to get it without autoinclude.

The test layer loads ``overrides.zcml`` by hand, because ``plone.app.testing``
disables autoinclude. That proves nothing about a real site, so these load
ZCML as Zope itself does, in a subprocess.
"""

from . import OUR_CHOOSER
from . import STARTUP_SCRIPT
from . import STOCK_CHOOSER

import json
import pytest
import subprocess
import sys


INCLUDE = '<include package="collective.redismemoize" />'
INCLUDE_OVERRIDES = (
    '<includeOverrides package="collective.redismemoize" file="overrides.zcml" />'
)


def chooser_after_startup(*args: str) -> str:
    """Run the startup script and return the chooser it found.

    :param args: Arguments for the script.
    :returns: Dotted name of the registered ``ICacheChooser``.
    """
    result = subprocess.run(  # noqa: S603 -- our own script, fixed arguments
        [sys.executable, "-W", "ignore", str(STARTUP_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])["chooser"]


@pytest.mark.parametrize(
    "args,expected",
    [
        ((), OUR_CHOOSER),
        ((INCLUDE,), OUR_CHOOSER),
        (("--disable-autoinclude",), STOCK_CHOOSER),
        (("--disable-autoinclude", INCLUDE), STOCK_CHOOSER),
        (("--disable-autoinclude", INCLUDE, INCLUDE_OVERRIDES), OUR_CHOOSER),
    ],
    ids=[
        "autoinclude",
        "autoinclude-and-include",
        "control-no-autoinclude",
        "no-autoinclude-include-only",
        "no-autoinclude-include-overrides",
    ],
)
def test_chooser_after_startup(args: tuple[str, ...], expected: str):
    """Which chooser a real startup ends up with.

    Autoinclude loads ``overrides.zcml`` through ``Products.CMFPlone``'s own
    ``overrides.zcml``. Without autoinclude, including the package is not
    enough: the overrides need ``includeOverrides``, as the install guide says.
    """
    assert chooser_after_startup(*args) == expected
