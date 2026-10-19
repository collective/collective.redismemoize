"""The reference tables say what the code does."""

from . import DOCS_DIR
from . import markdown_table
from collective.redismemoize import config
from pathlib import Path

import collective.redismemoize
import pytest
import re


SOURCE_DIR = Path(collective.redismemoize.__file__).parent


def unquote(cell: str) -> str:
    """Strip the backticks around a cell's code.

    :param cell: A table cell.
    :returns: The text inside the backticks, or the cell as written.
    """
    return cell.removeprefix("`").removesuffix("`")


@pytest.fixture(scope="module")
def variables() -> dict[str, str]:
    """Each variable of the configuration table, with its default."""
    text = (DOCS_DIR / "reference" / "configuration.md").read_text()
    table = markdown_table(text, "Environment variables")
    return {unquote(row["Variable"]): row["Default"] for row in table}


@pytest.fixture(scope="module")
def messages() -> list[dict[str, str]]:
    """The rows of the log messages table."""
    text = (DOCS_DIR / "reference" / "log-messages.md").read_text()
    return markdown_table(text, "Messages")


@pytest.fixture(scope="module")
def source() -> str:
    """Every Python module of the package, concatenated."""
    return "\n".join(p.read_text() for p in sorted(SOURCE_DIR.rglob("*.py")))


class TestConfiguration:
    def test_every_variable_is_documented(self, variables):
        """The table lists exactly the variables the package reads."""
        assert sorted(variables) == sorted(config.DEFAULTS)

    @pytest.mark.parametrize("name", sorted(config.DEFAULTS))
    def test_default(self, variables, name: str):
        """Each default in the table is the one the code applies."""
        default = config.DEFAULTS[name]
        expected = {None: "unset", "": "empty"}.get(default, f"`{default}`")
        assert variables[name] == expected


class TestLogMessages:
    def test_table_has_rows(self, messages):
        """The table was found and parsed."""
        assert len(messages) == 3

    def test_messages_are_logged(self, messages, source):
        """Each message is logged at the level the table gives."""
        for row in messages:
            message = unquote(row["Message"])
            level = unquote(row["Level"]).lower()
            pattern = rf'logger\.{level}\(\s*"{re.escape(message)}"'
            assert re.search(pattern, source), row
