"""Settings, read from the environment once per process.

The environment rather than the Plone registry: the cache chooser runs
outside any site, the first time a cached function is called, and its answer
has to be the same for every site the process serves. It is also how Docker
and Swarm deployments configure everything else.

This module is pure Python and never imports Zope.
"""

from dataclasses import dataclass
from fnmatch import fnmatchcase
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import os


#: Schemes redis-py accepts in ``Redis.from_url``.
SCHEMES = ("redis", "rediss", "unix")

#: Every variable this package reads, with its default. ``None`` means unset.
DEFAULTS: dict[str, str | None] = {
    "REDIS_MEMOIZE_URL": None,
    "REDIS_MEMOIZE_PREFIX": "plone.memoize",
    "REDIS_MEMOIZE_TTL": "86400",
    "REDIS_MEMOIZE_TIMEOUT": "0.25",
    "REDIS_MEMOIZE_RETRY_AFTER": "30",
    "REDIS_MEMOIZE_MAX_SIZE": "1048576",
    "REDIS_MEMOIZE_INCLUDE": "",
    "REDIS_MEMOIZE_EXCLUDE": "",
}


@dataclass(frozen=True)
class Settings:
    """The package configuration, validated.

    :param url: Redis URL, or ``None`` when the package is inert.
    :param prefix: Namespace every key starts with.
    :param ttl: Lifetime of a stored value, in seconds.
    :param timeout: Socket connect and read timeout, in seconds.
    :param retry_after: Seconds to leave Redis alone after a failure.
    :param max_size: Largest serialized value sent to Redis, in bytes.
    :param include: ``fnmatch`` patterns of function names allowed into Redis;
        empty allows every function.
    :param exclude: Patterns always kept in RAM; they win over ``include``.
    """

    url: str | None = None
    prefix: str = "plone.memoize"
    ttl: int = 86400
    timeout: float = 0.25
    retry_after: float = 30.0
    max_size: int = 1048576
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        """Report whether a Redis URL is configured.

        :returns: ``False`` means the package behaves exactly like stock
            ``plone.memoize``.
        """
        return self.url is not None

    def exclusion_reason(self, fun_name: str) -> str | None:
        """Explain why a function is kept out of Redis by configuration.

        :param fun_name: Dotted name of the cached function.
        :returns: The reason, or ``None`` when the function may use Redis.
        """
        for pattern in self.exclude:
            if fnmatchcase(fun_name, pattern):
                return f"matches REDIS_MEMOIZE_EXCLUDE pattern {pattern!r}"
        if self.include and not any(fnmatchcase(fun_name, p) for p in self.include):
            return "matches no REDIS_MEMOIZE_INCLUDE pattern"
        return None

    @property
    def redacted_url(self) -> str | None:
        """Return the URL with any password replaced by ``***``.

        :returns: The URL safe to log or show, or ``None`` when unset.
        """
        return redact_url(self.url)


def redact_url(url: str | None) -> str | None:
    """Hide the password of a URL.

    :param url: A Redis URL, or ``None``.
    :returns: The URL with its password replaced by ``***``.
    """
    if url is None:
        return None
    parts = urlsplit(url)
    if parts.password is None:
        return url
    user = parts.username or ""
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port is not None else ""
    netloc = f"{user}:***@{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _number(name: str, raw: str, kind: type, minimum: float) -> int | float:
    """Parse one numeric variable.

    :param name: Variable name, for the error message.
    :param raw: Its value.
    :param kind: ``int`` or ``float``.
    :param minimum: Smallest value accepted.
    :returns: The parsed value.
    :raises ValueError: When the value does not parse or is too small.
    """
    try:
        value = kind(raw)
    except ValueError:
        raise ValueError(f"{name}={raw!r} is not a valid {kind.__name__}") from None
    if value < minimum:
        raise ValueError(f"{name}={raw!r} must be at least {minimum}")
    return value


def _patterns(raw: str) -> tuple[str, ...]:
    """Split a comma-separated list of patterns.

    :param raw: The variable's value.
    :returns: The non-empty, stripped patterns.
    """
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def from_environ(environ: dict[str, str] | None = None) -> Settings:
    """Build and validate settings from an environment.

    :param environ: Mapping to read; ``os.environ`` by default.
    :returns: The settings.
    :raises ValueError: Naming the variable, when a value is invalid.
    """
    env = os.environ if environ is None else environ

    def raw(name: str) -> str | None:
        value = env.get(name)
        if value is None or not value.strip():
            return DEFAULTS[name]
        return value.strip()

    url = raw("REDIS_MEMOIZE_URL")
    if url is not None and urlsplit(url).scheme not in SCHEMES:
        raise ValueError(
            f"REDIS_MEMOIZE_URL={redact_url(url)!r} must use one of the schemes "
            f"{', '.join(SCHEMES)}"
        )
    prefix = raw("REDIS_MEMOIZE_PREFIX") or ""
    if any(char.isspace() for char in prefix):
        raise ValueError(f"REDIS_MEMOIZE_PREFIX={prefix!r} must not contain spaces")
    return Settings(
        url=url,
        prefix=prefix,
        ttl=int(_number("REDIS_MEMOIZE_TTL", raw("REDIS_MEMOIZE_TTL") or "", int, 1)),
        timeout=float(
            _number(
                "REDIS_MEMOIZE_TIMEOUT",
                raw("REDIS_MEMOIZE_TIMEOUT") or "",
                float,
                0.001,
            )
        ),
        retry_after=float(
            _number(
                "REDIS_MEMOIZE_RETRY_AFTER",
                raw("REDIS_MEMOIZE_RETRY_AFTER") or "",
                float,
                0,
            )
        ),
        max_size=int(
            _number(
                "REDIS_MEMOIZE_MAX_SIZE", raw("REDIS_MEMOIZE_MAX_SIZE") or "", int, 1
            )
        ),
        include=_patterns(raw("REDIS_MEMOIZE_INCLUDE") or ""),
        exclude=_patterns(raw("REDIS_MEMOIZE_EXCLUDE") or ""),
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the process settings, reading the environment the first time.

    :returns: The settings.
    :raises ValueError: When a variable is invalid.
    """
    global _settings
    if _settings is None:
        _settings = from_environ()
    return _settings


def reload() -> Settings:
    """Read the environment again, replacing the process settings.

    Tests use it after changing a variable; a running site never needs it.

    :returns: The new settings.
    :raises ValueError: When a variable is invalid.
    """
    global _settings
    _settings = from_environ()
    return _settings
