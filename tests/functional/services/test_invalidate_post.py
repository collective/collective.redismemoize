"""``POST @redismemoize/invalidate``."""

from tests.integration import COMPUTE
from tests.integration import compute
from tests.integration import COMPUTE_OTHER
from tests.integration import compute_other

import pytest


@pytest.mark.parametrize(
    "role,status_code",
    [
        ("Manager", 200),
        ("Site Administrator", 401),
        ("Editor", 401),
        ("Anonymous", 401),
    ],
)
def test_permission(session_for, role: str, status_code: int):
    """Only Manager, the one role holding ``cmf.ManagePortal``, may invalidate."""
    response = session_for(role).post("/@redismemoize/invalidate", json={})
    assert response.status_code == status_code


class TestInvalidate:
    def test_one_function(self, redis_client, session_for):
        """A body naming a function drops that function only."""
        compute("en")
        compute_other("en")
        response = session_for("Manager").post(
            "/@redismemoize/invalidate", json={"function": COMPUTE}
        )
        assert response.status_code == 200
        assert response.json() == {"function": COMPUTE, "removed": 1}
        assert redis_client.keys(f"test.memoize:{COMPUTE}:*") == []
        assert len(redis_client.keys(f"test.memoize:{COMPUTE_OTHER}:*")) == 1

    def test_everything(self, redis_client, session_for):
        """An empty body drops everything under the prefix.

        Serving the request runs Plone's own cached functions, the theming
        ones, so more than the two values stored here are removed.
        """
        compute("en")
        compute_other("en")
        response = session_for("Manager").post("/@redismemoize/invalidate", json={})
        data = response.json()
        assert data["function"] is None
        assert data["removed"] >= 2
        assert redis_client.keys(f"test.memoize:{COMPUTE}:*") == []
        assert redis_client.keys(f"test.memoize:{COMPUTE_OTHER}:*") == []

    def test_no_body(self, redis_client, session_for):
        """No body at all also means everything."""
        compute("en")
        response = session_for("Manager").post("/@redismemoize/invalidate")
        assert response.status_code == 200
        assert response.json()["function"] is None
        assert redis_client.keys(f"test.memoize:{COMPUTE}:*") == []

    @pytest.mark.parametrize("body", [{"function": ""}, {"function": 3}, [COMPUTE]])
    def test_bad_request(self, redis_server, session_for, body):
        """A malformed body is a 400."""
        response = session_for("Manager").post("/@redismemoize/invalidate", json=body)
        assert response.status_code == 400

    def test_not_json(self, redis_server, session_for):
        """A body that is not JSON is a 400."""
        response = session_for("Manager").post(
            "/@redismemoize/invalidate",
            data=b"function=x",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("path", ["/@redismemoize", "/@redismemoize/flush"])
    def test_other_paths(self, redis_server, session_for, path: str):
        """Only ``invalidate`` is a valid sub-path."""
        response = session_for("Manager").post(path, json={})
        assert response.status_code == 404
