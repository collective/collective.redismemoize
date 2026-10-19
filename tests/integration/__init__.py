"""The chooser and plone.memoize on a Plone site (integration layer)."""

from plone.memoize import ram


#: How many times :func:`compute` and :func:`compute_other` really ran.
CALLS: list[tuple] = []


def _key(fun, lang, region="BR"):
    return (lang, region)


@ram.cache(_key)
def compute(lang, region="BR"):
    """A function cached the way Plone's own are."""
    CALLS.append(("compute", lang, region))
    return {"lang": lang, "region": region}


@ram.cache(_key)
def compute_other(lang, region="BR"):
    """A second function with the same keys, to check they do not collide."""
    CALLS.append(("compute_other", lang, region))
    return {"other": lang}


def _skip(fun, lang):
    raise ram.DontCache


@ram.cache(_skip)
def never_cached(lang):
    """A function whose key function refuses to cache."""
    CALLS.append(("never_cached", lang))
    return lang


#: Dotted names, as ``plone.memoize`` builds them.
COMPUTE = f"{__name__}.compute"
COMPUTE_OTHER = f"{__name__}.compute_other"
