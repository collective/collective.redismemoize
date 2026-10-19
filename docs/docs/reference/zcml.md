(reference-zcml)=

# ZCML

<!-- source: src/collective/redismemoize/configure.zcml, overrides.zcml, services/configure.zcml -->

The package has no GenericSetup profile and no browser layer.
Its registrations are global, and take effect for every site in the process as soon as its ZCML is loaded.

## `overrides.zcml`

Registers `collective.redismemoize.chooser.choose_cache` as the `plone.memoize.interfaces.ICacheChooser` utility, replacing the one `plone.memoize` registers.

```{literalinclude} ../../../src/collective/redismemoize/overrides.zcml
:language: xml
```

## `configure.zcml`

Loads `plone.memoize` and `plone.restapi`, and registers the REST API services.

| Name | Method | For | Permission |
| --- | --- | --- | --- |
| `@redismemoize` | `GET` | `Products.CMFCore.interfaces.ISiteRoot` | `cmf.ManagePortal` |
| `@redismemoize` | `POST` | `Products.CMFCore.interfaces.ISiteRoot` | `cmf.ManagePortal` |

## Loading

With `plone.autoinclude`, the package's `plone` entry point makes Plone load both files.
Without it, you must include both:

```{literalinclude} ../../../tests/docs/snippets/without-autoinclude.zcml
:language: xml
```

## Related

- {doc}`/how-to-guides/install`
- {doc}`/concepts/how-plone-memoize-picks-a-cache`
