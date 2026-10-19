(how-to-install)=

# Install the package

<!-- source: pyproject.toml, src/collective/redismemoize/overrides.zcml, tests/spikes/test_spike_startup.py -->

This guide shows you how to add `collective.redismemoize` to a Plone project.
Installing it changes nothing until you configure a Redis URL; {doc}`configure` covers that.

## Add the dependency

Add the package to the dependencies of your project's backend, in its `pyproject.toml`:

```toml
[project]
dependencies = [
    "collective.redismemoize",
]
```

Then install the project as you always do, for example with `make install` in a Cookieplone project.

## Load the ZCML

There is no add-on to activate in the control panel and no GenericSetup profile.
The package replaces a global utility, so it works the moment its ZCML is loaded, for every site in the process.

With `plone.autoinclude`, which every Plone 6 project uses by default, there is nothing to do.
The package's entry point targets `plone`, and Plone loads its `configure.zcml` and its `overrides.zcml`.

If your site disables autoinclude, include the package **and** its overrides in your `site.zcml`, or in the ZCML your project loads:

```{literalinclude} ../../../tests/docs/snippets/without-autoinclude.zcml
:language: xml
```

```{important}
Including the package alone is not enough without autoinclude.
The cache chooser is registered in `overrides.zcml`, and only `includeOverrides` loads it.
```

Restart Plone after changing ZCML.

## Check it

Start Plone and request the status endpoint as a Manager:

```shell
curl -u admin:admin -H "Accept: application/json" http://localhost:8080/Plone/@redismemoize
```

The response has `"active": false` until you configure a URL.

## Next steps

- {doc}`configure`
- {doc}`/reference/zcml`
