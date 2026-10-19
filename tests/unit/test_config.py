"""Settings from the environment."""

from collective.redismemoize import config
from collective.redismemoize.config import from_environ
from collective.redismemoize.config import redact_url
from collective.redismemoize.config import Settings

import pytest


class TestDefaults:
    def test_empty_environment_is_inert(self):
        """No variables at all: the package is inert."""
        settings = from_environ({})
        assert settings.active is False
        assert settings.url is None

    @pytest.mark.parametrize(
        "attr,expected",
        [
            ("prefix", "plone.memoize"),
            ("ttl", 86400),
            ("timeout", 0.25),
            ("retry_after", 30.0),
            ("max_size", 1048576),
            ("include", ()),
            ("exclude", ()),
        ],
    )
    def test_default(self, attr: str, expected):
        """Each setting has the documented default."""
        assert getattr(from_environ({}), attr) == expected

    def test_defaults_match_dataclass(self):
        """The environment defaults and the dataclass defaults agree."""
        assert from_environ({}) == Settings()

    def test_blank_values_mean_default(self):
        """A variable set to whitespace counts as unset."""
        settings = from_environ(dict.fromkeys(config.DEFAULTS, "  "))
        assert settings == Settings()


class TestParsing:
    @pytest.mark.parametrize(
        "name,raw,attr,expected",
        [
            (
                "REDIS_MEMOIZE_URL",
                "redis://cache:6379/1",
                "url",
                "redis://cache:6379/1",
            ),
            (
                "REDIS_MEMOIZE_URL",
                "rediss://cache:6380/0",
                "url",
                "rediss://cache:6380/0",
            ),
            (
                "REDIS_MEMOIZE_URL",
                "unix:///run/redis.sock",
                "url",
                "unix:///run/redis.sock",
            ),
            ("REDIS_MEMOIZE_PREFIX", "stack-a", "prefix", "stack-a"),
            ("REDIS_MEMOIZE_TTL", "60", "ttl", 60),
            ("REDIS_MEMOIZE_TIMEOUT", "1.5", "timeout", 1.5),
            ("REDIS_MEMOIZE_RETRY_AFTER", "0", "retry_after", 0.0),
            ("REDIS_MEMOIZE_MAX_SIZE", "10", "max_size", 10),
            (
                "REDIS_MEMOIZE_INCLUDE",
                "plone.*, my.addon.*",
                "include",
                ("plone.*", "my.addon.*"),
            ),
            ("REDIS_MEMOIZE_EXCLUDE", " a.b ,,c.* ", "exclude", ("a.b", "c.*")),
        ],
    )
    def test_variable(self, name: str, raw: str, attr: str, expected):
        """Every variable is parsed into its setting."""
        assert getattr(from_environ({name: raw}), attr) == expected

    def test_url_makes_active(self):
        """A URL activates the package."""
        assert from_environ({"REDIS_MEMOIZE_URL": "redis://cache"}).active is True

    def test_variables_are_stripped(self):
        """Surrounding whitespace is ignored."""
        assert from_environ({"REDIS_MEMOIZE_TTL": " 5 "}).ttl == 5


class TestInvalid:
    @pytest.mark.parametrize(
        "name,raw",
        [
            ("REDIS_MEMOIZE_URL", "http://cache:6379"),
            ("REDIS_MEMOIZE_URL", "cache:6379"),
            ("REDIS_MEMOIZE_PREFIX", "two words"),
            ("REDIS_MEMOIZE_TTL", "a day"),
            ("REDIS_MEMOIZE_TTL", "0"),
            ("REDIS_MEMOIZE_TTL", "1.5"),
            ("REDIS_MEMOIZE_TIMEOUT", "fast"),
            ("REDIS_MEMOIZE_TIMEOUT", "0"),
            ("REDIS_MEMOIZE_RETRY_AFTER", "-1"),
            ("REDIS_MEMOIZE_MAX_SIZE", "0"),
            ("REDIS_MEMOIZE_MAX_SIZE", "1MB"),
        ],
    )
    def test_names_the_variable(self, name: str, raw: str):
        """An invalid value raises a ValueError naming the variable."""
        with pytest.raises(ValueError, match=name):
            from_environ({name: raw})

    def test_url_error_hides_password(self):
        """The error for a bad URL does not leak its password."""
        with pytest.raises(ValueError) as info:
            from_environ({"REDIS_MEMOIZE_URL": "http://user:s3cret@cache:6379"})
        assert "s3cret" not in str(info.value)


class TestExclusion:
    @pytest.mark.parametrize(
        "include,exclude,fun_name,excluded",
        [
            ((), (), "plone.app.theming.plugins.utils.getPlugins", False),
            (
                (),
                ("plone.app.theming.*",),
                "plone.app.theming.plugins.utils.getPlugins",
                True,
            ),
            (
                (),
                ("plone.app.theming.*",),
                "plone.app.content.browser.i18n._gettext_catalog",
                False,
            ),
            (
                ("plone.app.content.*",),
                (),
                "plone.app.content.browser.i18n._gettext_catalog",
                False,
            ),
            (("plone.app.content.*",), (), "plone.namedfile.scaling.tag", True),
            (("plone.*",), ("plone.namedfile.*",), "plone.namedfile.scaling.tag", True),
            (
                ("plone.*",),
                ("plone.namedfile.*",),
                "plone.app.layout.sitemap.sitemap.generate",
                False,
            ),
            (("*.tag",), (), "plone.namedfile.scaling.tag", False),
            (("Plone.*",), (), "plone.namedfile.scaling.tag", True),
        ],
    )
    def test_patterns(self, include, exclude, fun_name: str, excluded: bool):
        """Include and exclude are fnmatch patterns; exclude wins; case counts."""
        settings = Settings(url="redis://cache", include=include, exclude=exclude)
        assert (settings.exclusion_reason(fun_name) is not None) is excluded

    def test_exclude_wins_over_include(self):
        """A name matching both lists is excluded, and the reason says why."""
        settings = Settings(url="redis://cache", include=("a.*",), exclude=("a.b",))
        reason = settings.exclusion_reason("a.b")
        assert reason is not None
        assert "REDIS_MEMOIZE_EXCLUDE" in reason

    def test_include_reason(self):
        """A name outside the include list says so."""
        settings = Settings(url="redis://cache", include=("a.*",))
        assert "REDIS_MEMOIZE_INCLUDE" in settings.exclusion_reason("b.c")


class TestRedaction:
    @pytest.mark.parametrize(
        "url,expected",
        [
            (None, None),
            ("redis://cache:6379/0", "redis://cache:6379/0"),
            ("redis://:s3cret@cache:6379/0", "redis://:***@cache:6379/0"),
            ("rediss://plone:s3cret@cache/2", "rediss://plone:***@cache/2"),
            ("unix:///run/redis.sock", "unix:///run/redis.sock"),
        ],
    )
    def test_redact(self, url, expected):
        """The password, and only the password, is hidden."""
        assert redact_url(url) == expected

    def test_settings_property(self):
        """``Settings.redacted_url`` is the redacted URL."""
        settings = Settings(url="redis://:pw@cache:6379")
        assert settings.redacted_url == "redis://:***@cache:6379"


class TestProcessSettings:
    def test_get_settings_is_cached(self, monkeypatch):
        """The environment is read once, until ``reload``."""
        monkeypatch.setattr(config, "_settings", None)
        monkeypatch.setenv("REDIS_MEMOIZE_TTL", "11")
        first = config.get_settings()
        monkeypatch.setenv("REDIS_MEMOIZE_TTL", "22")
        assert config.get_settings() is first
        assert config.reload().ttl == 22
        assert config.get_settings().ttl == 22
        monkeypatch.delenv("REDIS_MEMOIZE_TTL")
        config.reload()
