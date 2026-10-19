from collective.redismemoize import api


def _key(fun, lang):
    return lang


@api.cache(_key, ttl=300)
def country_names(lang: str) -> dict[str, str]:
    """Return country names in a language, cached for five minutes."""
    if lang == "pt":
        return {"br": "Brasil", "pt": "Portugal"}
    return {"br": "Brazil", "pt": "Portugal"}
