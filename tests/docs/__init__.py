"""Tests that generate, or check, what the documentation shows.

- The REST API reference does not hand-write its requests and responses: it
  includes the ``.req`` / ``.resp`` pairs ``test_rest_examples`` writes to
  ``http-examples/``, the way ``plone.restapi`` does. Regenerate them with
  ``make test``, or on their own with ``.venv/bin/pytest tests/docs``.
- The configuration reference's table is parsed and compared with
  :mod:`collective.redismemoize.config`.
- Every snippet a guide tells the reader to use lives in ``snippets/``, is
  included by the page with ``literalinclude``, and is run here.

Only a fixed set of headers is written, the test server's port is normalized,
and the one value that varies between runs, the ``PING`` latency, is replaced
by a fixed number: an example that changes on every run is noise in a diff.
"""

from itertools import dropwhile
from itertools import takewhile
from pathlib import Path
from typing import Any

import json
import re


#: Where the generated pairs are written.
EXAMPLES_DIR = Path(__file__).parent / "http-examples"

#: Where the snippets the guides include live.
SNIPPETS_DIR = Path(__file__).parent / "snippets"

#: The documentation sources.
DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "docs"

#: Request headers worth showing.
REQUEST_HEADERS = ("accept", "authorization", "content-type")

#: Response headers worth showing.
RESPONSE_HEADERS = ("content-type",)

#: The port of the test server is not fixed; it is normalized to the one
#: ``plone.restapi``'s own examples use.
CANONICAL_NETLOC = "localhost:55001"

#: The latency every recorded status reports.
CANONICAL_LATENCY = 0.25

#: Written with explicit newlines so macOS and Linux produce identical files.
OPEN_KWARGS: dict[str, Any] = {"newline": "\n"}


def normalize(value: str) -> str:
    """Replace the test server's random port with a stable one.

    :param value: Text that may carry the server's host and port.
    :returns: The text with the port normalized.
    """
    return re.sub(r"localhost:\d{4,5}", CANONICAL_NETLOC, value)


def stabilize(data: Any) -> Any:
    """Replace the values of a status payload that vary between runs.

    :param data: A decoded JSON payload.
    :returns: The payload, with the ``PING`` latency fixed.
    """
    server = data.get("server") if isinstance(data, dict) else None
    if isinstance(server, dict) and server.get("latency_ms") is not None:
        server["latency_ms"] = CANONICAL_LATENCY
    return data


def pretty_json(data: Any) -> str:
    """Serialize a payload the way the committed examples hold it.

    :param data: The decoded JSON payload.
    :returns: Sorted, indented text ending with a newline.
    """
    rendered = json.dumps(data, sort_keys=True, indent=4, separators=(",", ": "))
    stripped = "\n".join(line.rstrip() for line in rendered.splitlines())
    return normalize(stripped + "\n")


def save_request(name: str, response: Any) -> None:
    """Write the request that produced ``response`` as ``<name>.req``.

    :param name: Base name of the example.
    :param response: The ``requests`` response whose request is written.
    """
    request = response.request
    lines = [f"{request.method} {request.path_url} HTTP/1.1"]
    for key, value in sorted(request.headers.items()):
        if key.lower() in REQUEST_HEADERS:
            lines.append(f"{key.title()}: {value}")
    body = ""
    if request.body:
        # ``json.loads`` reads the bytes ``requests`` encodes ``json=`` into.
        body = "\n" + pretty_json(json.loads(request.body))
    path = EXAMPLES_DIR / f"{name}.req"
    with open(path, "w", **OPEN_KWARGS) as handle:
        handle.write(normalize("\n".join(lines)) + "\n" + body)


def save_response(name: str, response: Any) -> None:
    """Write ``response`` as ``<name>.resp``.

    :param name: Base name of the example.
    :param response: The ``requests`` response to write.
    """
    lines = [f"HTTP/1.1 {response.status_code} {response.reason}"]
    for key, value in response.headers.items():
        if key.lower() in RESPONSE_HEADERS:
            lines.append(f"{key.title()}: {normalize(value)}")
    body = pretty_json(stabilize(response.json()))
    path = EXAMPLES_DIR / f"{name}.resp"
    with open(path, "w", **OPEN_KWARGS) as handle:
        handle.write("\n".join(lines) + "\n\n" + body)


def save_example(name: str, response: Any) -> Any:
    """Write both halves of one example.

    :param name: Base name; the documentation includes ``<name>.req`` and
        ``<name>.resp``.
    :param response: The ``requests`` response to record.
    :returns: The response, to assert on.
    """
    EXAMPLES_DIR.mkdir(exist_ok=True)
    save_request(name, response)
    save_response(name, response)
    return response


def markdown_table(text: str, heading: str) -> list[dict[str, str]]:
    """Parse the first Markdown table after a heading.

    :param text: The page source.
    :param heading: The heading's text, without the ``#`` marks.
    :returns: One dict per row, keyed by the header cells.
    """
    lines = text.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.lstrip("#").strip() == heading
    )
    after = lines[start + 1 :]
    table = takewhile(
        lambda line: line.startswith("|"),
        dropwhile(lambda line: not line.startswith("|"), after),
    )
    header, _separator, *body = (
        [cell.strip() for cell in line.strip().strip("|").split("|")] for line in table
    )
    return [dict(zip(header, cells, strict=True)) for cells in body]
