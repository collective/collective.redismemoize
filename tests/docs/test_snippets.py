"""Every snippet the guides include is run, and every one is included."""

from . import DOCS_DIR
from . import SNIPPETS_DIR
from collective.redismemoize import config
from pathlib import Path
from tests.spikes import OUR_CHOOSER
from tests.spikes.test_spike_startup import chooser_after_startup

import importlib.util
import pytest
import shutil
import subprocess
import sys
import yaml


def load_module(path: Path):
    """Import a snippet file as a module.

    :param path: The snippet.
    :returns: The module.
    """
    spec = importlib.util.spec_from_file_location(f"snippet_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snippet_files() -> list[Path]:
    """Return every snippet file, recursively."""
    return sorted(
        p
        for p in SNIPPETS_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )


class TestWithoutAutoinclude:
    def test_snippet_installs_the_chooser(self):
        """The install guide's ZCML gives the chooser to a site without autoinclude."""
        lines = (SNIPPETS_DIR / "without-autoinclude.zcml").read_text().splitlines()
        assert chooser_after_startup("--disable-autoinclude", *lines) == OUR_CHOOSER


@pytest.fixture(scope="module")
def compose() -> dict:
    """The Compose file the configuration guide shows."""
    return yaml.safe_load((SNIPPETS_DIR / "docker-compose.yml").read_text())


class TestCompose:
    def test_settings_are_valid(self, compose):
        """The backend's variables parse into active settings."""
        settings = config.from_environ(compose["services"]["backend"]["environment"])
        assert settings.active is True
        assert settings.prefix == "example-org"

    def test_url_names_the_service(self, compose):
        """The URL's host is the Redis service."""
        url = compose["services"]["backend"]["environment"]["REDIS_MEMOIZE_URL"]
        assert url.split("//")[1].split(":")[0] in compose["services"]

    def test_redis_publishes_no_port(self, compose):
        """Redis is reachable from the backend only."""
        assert "ports" not in compose["services"]["redis"]

    def test_network_is_internal(self, compose):
        """The network Redis is on has no route outside."""
        assert compose["networks"]["cache"]["internal"] is True
        assert compose["services"]["redis"]["networks"] == ["cache"]

    @pytest.mark.parametrize(
        "flag,value",
        [
            ("--save", ""),
            ("--appendonly", "no"),
            ("--maxmemory", "256mb"),
            ("--maxmemory-policy", "allkeys-lru"),
        ],
    )
    def test_redis_flags(self, compose, flag: str, value: str):
        """Persistence is off and memory is bounded, with LRU eviction."""
        command = compose["services"]["redis"]["command"]
        assert command[command.index(flag) + 1] == value


class TestTtlDecorator:
    def test_snippet(self, redis_client, portal):
        """The TTL guide's function is cached in Redis for five minutes."""
        module = load_module(SNIPPETS_DIR / "ttl.py")
        assert module.country_names("pt")["br"] == "Brasil"
        assert module.country_names("en")["br"] == "Brazil"
        keys = redis_client.keys("test.memoize:*country_names:*")
        assert len(keys) == 2
        assert all(295 <= redis_client.ttl(key) <= 300 for key in keys)


class TestIntegratorExample:
    def test_runs(self, tmp_path: Path):
        """The testing guide's conftest and test module pass, in their own run."""
        target = tmp_path / "integrator"
        shutil.copytree(SNIPPETS_DIR / "integrator", target)
        (target / "pytest.ini").write_text("[pytest]\n")
        result = subprocess.run(  # noqa: S603 -- our own snippet, fixed arguments
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "-W",
                "ignore",
                "-c",
                str(target / "pytest.ini"),
                "--rootdir",
                str(target),
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        assert result.returncode == 0, result.stdout[-3000:]
        assert "2 passed" in result.stdout


@pytest.mark.parametrize("path", snippet_files(), ids=lambda p: p.name)
def test_snippet_is_included(path: Path):
    """Each snippet is included by a documentation page, so none is orphaned."""
    relative = path.relative_to(SNIPPETS_DIR).as_posix()
    pages = [p for p in DOCS_DIR.rglob("*.md") if relative in p.read_text()]
    assert pages, f"no page includes snippets/{relative}"
