"""Real Redis and Valkey servers, in containers; marked ``docker``.

Run with ``make test-docker``. Without Docker the tests skip, unless
:data:`REQUIRE_DOCKER` is set in the environment, as CI does: there a skip
would hide the one run that matters.
"""

#: Set this in CI so a missing Docker fails instead of skipping.
REQUIRE_DOCKER = "REDIS_MEMOIZE_REQUIRE_DOCKER"

#: The compose services, each a server product.
SERVICES = ("redis", "valkey")

#: A port nothing listens on, for the outage tests.
CLOSED_URL = "redis://127.0.0.1:1/0"
