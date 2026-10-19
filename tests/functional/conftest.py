"""Fixtures for the functional package; everything runs on ``functional_portal``."""

from . import USERS
from collections.abc import Callable
from typing import Any

import pytest
import transaction


@pytest.fixture
def portal(functional_portal) -> Any:
    """The functional site, with one user per role, committed.

    The HTTP requests run in the server thread's own transaction, so the users
    are invisible to them until committed.
    """
    for role, (username, password) in USERS.items():
        functional_portal.acl_users.userFolderAddUser(username, password, [role], [])
    transaction.commit()
    return functional_portal


@pytest.fixture
def session_for(portal, request_factory) -> Callable[[str], Any]:
    """Return a callable building an HTTP session for a role.

    :returns: Callable taking ``"Manager"``, ``"Anonymous"`` or a key of
        :data:`tests.functional.USERS`.
    """

    def func(role: str) -> Any:
        if role in USERS:
            return request_factory(basic_auth=USERS[role])
        return request_factory(role=role)

    return func
