"""``GET @redismemoize``."""

from .. import STATUS_KEYS
from tests.integration import COMPUTE
from tests.integration import compute

import pytest


@pytest.mark.parametrize(
    "role,status_code",
    [
        ("Manager", 200),
        ("Site Administrator", 401),
        ("Editor", 401),
        ("Member", 401),
        ("Anonymous", 401),
    ],
)
def test_permission(session_for, role: str, status_code: int):
    """Only Manager, the one role holding ``cmf.ManagePortal``, may read the status."""
    response = session_for(role).get("/@redismemoize")
    assert response.status_code == status_code


class TestInactive:
    def test_shape(self, session_for):
        """Unconfigured: the documented keys, and no server."""
        data = session_for("Manager").get("/@redismemoize").json()
        assert sorted(data) == STATUS_KEYS
        assert data["active"] is False
        assert data["server"] is None


class TestActive:
    def test_shape(self, activate, session_for):
        """Configured: settings, breaker and server are reported."""
        activate()
        data = session_for("Manager").get("/@redismemoize").json()
        assert sorted(data) == STATUS_KEYS
        assert data["active"] is True
        assert data["breaker"] == {"open": False, "seconds_until_retry": 0.0}
        assert data["server"]["product"] == "redis"

    def test_url_redacted(self, activate, session_for):
        """The URL's password never leaves the server."""
        activate(REDIS_MEMOIZE_URL="redis://:s3cret@cache:6379/0")
        response = session_for("Manager").get("/@redismemoize")
        assert response.json()["settings"]["url"] == "redis://:***@cache:6379/0"
        assert "s3cret" not in response.text

    def test_routing_table(self, activate, session_for):
        """Calls made earlier in the process show in the routing table."""
        activate()
        compute("en")
        compute("en")
        functions = session_for("Manager").get("/@redismemoize").json()["functions"]
        assert functions[COMPUTE]["route"] == "redis"
        assert functions[COMPUTE]["counters"]["redis_misses"] == 1
        assert functions[COMPUTE]["counters"]["redis_hits"] == 1
