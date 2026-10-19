"""Fixtures that bring up Redis and Valkey with pytest-docker."""

from . import REQUIRE_DOCKER
from . import SERVICES
from collections.abc import Iterator
from collective.redismemoize import client
from collective.redismemoize import config
from collective.redismemoize.routing import router
from pathlib import Path
from typing import Any

import os
import pytest
import redis
import shutil
import subprocess
import uuid


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig) -> Path:
    """Point pytest-docker at the compose file next to the tests.

    :param pytestconfig: The pytest config, for the rootdir.
    :returns: Path to the compose file.
    """
    return Path(str(pytestconfig.rootdir)).resolve() / "tests" / "docker-compose.yml"


def _docker_available() -> bool:
    """Report whether a usable Docker daemon is reachable.

    :returns: Whether the compose stack could be started.
    """
    if (
        shutil.which("docker") is None
    ):  # pragma: no cover - environment branch: not taken on a machine that has Docker
        return False
    try:
        return (
            subprocess.run(
                ["docker", "info"],  # noqa: S607
                capture_output=True,
                timeout=20,
                check=False,
            ).returncode
            == 0
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ):  # pragma: no cover - defensive: a broken docker binary, not reachable with a working one
        return False


def _responsive(url: str) -> bool:
    """Report whether a server answers ``PING``.

    :param url: Redis URL.
    :returns: Whether it is up.
    """
    try:
        return bool(redis.Redis.from_url(url, socket_timeout=1).ping())
    except redis.RedisError:  # pragma: no cover - timing branch: only taken when the server is slower to boot than the first poll
        return False


@pytest.fixture(scope="session")
def docker_ready() -> None:
    """Skip, or fail when Docker is required, if Docker is not available."""
    if not _docker_available():  # pragma: no cover - environment branch: the run that measures coverage has Docker
        message = "Docker is not available; skipping the Redis and Valkey tests"
        if os.environ.get(REQUIRE_DOCKER):
            raise AssertionError(f"{message}, but {REQUIRE_DOCKER} is set")
        pytest.skip(message)


@pytest.fixture(scope="session", params=SERVICES)
def server_url(request, docker_ready, docker_ip, docker_services) -> str:
    """Bring up one server and return its URL; every test runs on each.

    :returns: A ``redis://`` URL for the running server.
    """
    port = docker_services.port_for(request.param, 6379)
    url = f"redis://{docker_ip}:{port}/0"
    docker_services.wait_until_responsive(
        timeout=60.0, pause=0.5, check=lambda: _responsive(url)
    )
    return url


@pytest.fixture
def product(server_url, request) -> str:
    """Return which product the current server is."""
    return request.node.callspec.params["server_url"]


@pytest.fixture
def prefix() -> str:
    """Return a prefix no other test uses."""
    return f"docker-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def configured(server_url, prefix, monkeypatch) -> Iterator[config.Settings]:
    """Configure the process for the real server, and restore afterwards.

    :returns: The settings in force.
    """
    monkeypatch.setenv("REDIS_MEMOIZE_URL", server_url)
    monkeypatch.setenv("REDIS_MEMOIZE_PREFIX", prefix)
    client.set_factory(None)
    router.reset()
    yield config.reload()
    raw = redis.Redis.from_url(server_url)
    keys = list(raw.scan_iter(match=f"{prefix}:*"))
    if keys:
        raw.unlink(*keys)
    monkeypatch.undo()
    config.reload()
    client.set_factory(None)
    router.reset()


@pytest.fixture
def raw(server_url) -> Any:
    """Return a plain client on the server, to inspect what was stored."""
    return redis.Redis.from_url(server_url)
