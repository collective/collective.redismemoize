# AGENTS.md

Instructions for coding agents working in this repository. Humans want the
[documentation](https://collective.github.io/collective.redismemoize/), which
covers the same ground in prose.

## What this repository is

`collective.redismemoize`, a Plone add-on that replaces `plone.memoize`'s
`ICacheChooser` so cached values are stored in Redis or Valkey and shared
between instances. Values that are not plain data stay in each process's RAM
cache.

| Path | Holds |
|---|---|
| `src/collective/redismemoize/` | The package |
| `tests/` | The test suite, one directory per kind of test |
| `docs/` | The published documentation, with its own `uv` environment |
| `news/` | Towncrier fragments |

There is **no GenericSetup profile and no browser layer**, on purpose. The
chooser is a global utility registered in `overrides.zcml`; it takes effect
for every site in the process as soon as the ZCML loads. Do not add a profile
to "install" it.

## Setup

```shell
make install       # uv virtual environment, Plone, and the package
make create-site   # first run only
make start         # http://localhost:8080/
```

Python is `>=3.10`; dependencies are managed with `uv`, never raw `pip`.

## Gates

Run these before proposing a commit. CI runs the same ones.

| Command | Checks |
|---|---|
| `make check` | `make format`, `make lint`, and `make check-pragmas` |
| `make test` | Every test that needs no container (`-m "not docker"`) |
| `make test-coverage` | The same, with coverage; **`fail_under = 100`** |
| `make test-docker` | The tests against real Redis 7 and Valkey 8 containers |
| `make docs-html` | Sphinx from scratch with `-W`, warnings as errors |
| `make docs-vale` | Prose style. **Errors must be zero**; warnings are advisory |

## Rules that are easy to get wrong

### Run `make format` before staging

The formatters rewrite files. Formatting after `git add` leaves the staged and
working copies disagreeing.

### Coverage is 100%, and a pragma needs a reason

`make check-pragmas` fails on a `# pragma: no cover` without a justification
on the same line. Prefer a test to a pragma.

### Configuration comes from the environment only

Settings are read from `REDIS_MEMOIZE_*` variables once per process
(`config.py`). The chooser runs outside any site, so the Plone registry is not
an option. Tests change settings through `collective.redismemoize.testing`'s
`activate()`, never by editing `os.environ` and hoping.

### The shareability check is a security boundary

`serializer.py` accepts exact types only, and its unpickler resolves only
`SAFE_GLOBALS`. Widening either is a security decision: it needs a test in
`tests/unit/test_serializer.py` and a line in the documentation's concepts
pages. Never fall back to plain `pickle.loads`.

### Some documentation is generated or checked by the tests

- `tests/docs/http-examples/` is written by `tests/docs/test_rest_examples.py`
  and included by the REST API reference. Regenerate it with `make test`; do
  not edit it by hand.
- The guides include the files in `tests/docs/snippets/`, which the tests run.
  Change the snippet, not a copy of it in a page.
- The configuration and log messages reference tables are parsed and compared
  with the code.

### Every change carries a news fragment

Name it `<issue>.<type>`, or `+<slug>.<type>` when no issue exists, in `news/`.
Types: `breaking`, `feature`, `bugfix`, `documentation`, `internal`, `tests`.
Write in the past tense for somebody reading the changelog, and end with the
author's GitHub handle.

### A bugfix carries a test that fails without it

Verify that by removing the fix and watching the test go red.

## Documentation

The documentation follows the Plone documentation style guide and the Diátaxis
framework:

- One sentence per line.
- Cite the source file a page is based on in an HTML comment under its title.
- Reference pages are tables and definition lists; rationale belongs in
  `concepts/`.
- Every page ends with **Related** or **Next steps**.
- Every `index.md` has a grid of cards, each title starting with an emoji.

## Releasing

**Do not run a release.** A release publishes to PyPI and tags the
repository, which cannot be taken back. Preparing one (fragments, metadata,
documentation) is fair game; cutting one is a person's job.

## Security

Do not open an issue for a vulnerability. Follow [SECURITY.md](SECURITY.md).
