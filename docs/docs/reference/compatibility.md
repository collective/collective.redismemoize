(reference-compatibility)=

# Compatibility

<!-- source: pyproject.toml, .github/workflows/main.yml, tests/docker-compose.yml -->

| Component | Tested | Expected to work |
| --- | --- | --- |
| Plone | 6.2 | 6.1 |
| Python | 3.14 | 3.10 to 3.13 |
| Redis | 7.4 | 4.0 and later |
| Valkey | 8 | 7.2 and later |
| redis-py | 8.1 | 5.0 and later |

"Tested" means the versions the complete test suite ran against before this release, including the tests against real servers.
For Plone, Python and redis-py, "expected to work" means the versions the continuous integration matrix and the declared dependencies cover.
For the servers, it means the versions that have every command the package sends: `GET`, `SET` with `EX`, `DEL`, `UNLINK`, `SCAN`, `PING`, and `INFO`.

## Related

- {doc}`/how-to-guides/use-valkey`
