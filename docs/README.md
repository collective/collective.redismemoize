# collective.redismemoize documentation

The sources of the documentation published at https://collective.github.io/collective.redismemoize/.
It is built with Sphinx, MyST, and the [Plone Sphinx Theme](https://github.com/plone/plone-sphinx-theme), and follows the [Plone documentation style guide](https://6.docs.plone.org/contributing/documentation/index.html).

## Build

From the repository root:

```shell
make docs-install
make docs-html
make docs-vale
```

`make docs-html` builds from scratch and treats every warning as an error.
`make docs-livehtml` serves the documentation with live reload on port 8050.

The documentation environment installs the package itself, from the repository, so the Python API reference documents the code next to it.

## Generated and tested content

Some pages include files the test suite owns:

- The REST API reference includes the requests and responses in `tests/docs/http-examples/`, which `make test` writes.
- The guides include the files in `tests/docs/snippets/`, which `make test` runs.
- `make test` also checks the tables in the configuration and log messages references against the code.

Change those files, not copies of them in the pages, and run `make test` after changing the code they describe.

## Layout

The pages follow the [Diátaxis](https://diataxis.fr/) framework:

- `docs/tutorials/`
- `docs/how-to-guides/`
- `docs/concepts/`
- `docs/reference/`
