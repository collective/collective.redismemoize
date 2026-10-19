"""Fixtures for the documentation tests."""

from collections.abc import Callable
from typing import Any

import pytest
import transaction


#: The snippets are run by the tests, not collected as tests: the integrator
#: example brings its own layer and runs in a separate process.
collect_ignore = ["snippets"]


@pytest.fixture
def docs_session(functional_portal: Any, request_factory: Callable) -> Any:
    """A Manager session against the site, after a commit.

    Requests go to the plain site URL with an ``Accept`` header, which is how
    ``plone.restapi`` documents its endpoints.

    :returns: The session the examples are recorded from.
    """
    transaction.commit()
    return request_factory(role="Manager", api=False)
