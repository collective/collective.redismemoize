"""Record the HTTP examples the REST API reference renders.

Each test is a real assertion and a generator: it calls the endpoint, checks
the property the reference page states, and writes the request and response.
"""

from . import save_example
from tests.integration import COMPUTE
from tests.integration import compute
from tests.integration import compute_other


class TestStatus:
    def test_status_get(self, redis_server, docs_session):
        """``GET @redismemoize`` reports settings, breaker, server and functions."""
        compute("en")
        compute("en")
        response = save_example("status_get", docs_session.get("/@redismemoize"))
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True
        assert data["functions"][COMPUTE]["counters"]["redis_hits"] == 1

    def test_status_get_inactive(self, docs_session):
        """Unconfigured, the status has no server and no breaker."""
        response = save_example(
            "status_get_inactive", docs_session.get("/@redismemoize")
        )
        assert response.status_code == 200
        assert response.json()["server"] is None


class TestInvalidate:
    def test_invalidate_function(self, redis_server, docs_session):
        """A body naming a function drops that function's values."""
        compute("en")
        compute_other("en")
        response = save_example(
            "invalidate_function",
            docs_session.post("/@redismemoize/invalidate", json={"function": COMPUTE}),
        )
        assert response.json() == {"function": COMPUTE, "removed": 1}

    def test_invalidate_all(self, redis_server, docs_session):
        """An empty body drops everything under the prefix."""
        compute_other("en")
        response = save_example(
            "invalidate_all",
            docs_session.post("/@redismemoize/invalidate", json={}),
        )
        data = response.json()
        assert data["function"] is None
        assert data["removed"] >= 1
