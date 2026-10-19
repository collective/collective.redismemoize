"""Which functions in a stock Plone use ``plone.memoize.ram``.

The concepts page documents where each of them lands. A new Plone release
that adds, removes or renames one fails here, so the table is updated rather
than silently wrong.
"""

from . import PLONE_RAM_CACHES
from pathlib import Path

import ast
import importlib.util
import itertools
import plone


#: Namespaces scanned: the whole of Plone's own code in the environment.
ROOTS = ("plone", "Products")


def _decorator_name(node: ast.expr) -> str | None:
    """Return the dotted name a decorator call is made on.

    :param node: A decorator, or a bare call statement's function.
    :returns: ``"ram.cache"`` for ``@ram.cache(key)``, and so on.
    """
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return None


def _imports_ram(tree: ast.Module) -> tuple[bool, bool]:
    """Report how a module imports ``plone.memoize.ram``.

    :param tree: Parsed module.
    :returns: Whether it imports ``ram``, and whether it imports ``cache``
        from ``plone.memoize.ram``.
    """
    module = name = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "plone.memoize":
            module = module or any(a.name == "ram" for a in node.names)
        if isinstance(node, ast.ImportFrom) and node.module == "plone.memoize.ram":
            name = name or any(a.name == "cache" for a in node.names)
    return module, name


def _users_in_module(
    tree: ast.Module, dotted: str, accepted: set[str]
) -> dict[str, bool]:
    """Find the cached functions of one module.

    A decorator applied with ``@`` is found on the function. One written as a
    bare call statement in a class body, right before the method, is found
    too: it looks like a decorator and caches nothing.

    :param tree: Parsed module.
    :param dotted: Its dotted name.
    :param accepted: Decorator names that go through the chooser.
    :returns: ``{dotted name: whether the decorator is actually applied}``.
    """
    found: dict[str, bool] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and any(
            _decorator_name(d) in accepted for d in node.decorator_list
        ):
            found[f"{dotted}.{node.name}"] = True
        if isinstance(node, ast.ClassDef):
            body = node.body
            for stmt, following in itertools.pairwise(body):
                if (
                    isinstance(stmt, ast.Expr)
                    and _decorator_name(stmt.value) in accepted
                    and isinstance(following, ast.FunctionDef)
                ):
                    found[f"{dotted}.{following.name}"] = False
    return found


def _modules() -> list[tuple[str, Path]]:
    """List Plone's own modules that mention ``plone.memoize``.

    :returns: ``(dotted name, path)`` pairs, tests excluded.
    """
    modules = []
    for root in ROOTS:
        spec = importlib.util.find_spec(root)
        assert spec is not None
        for location in spec.submodule_search_locations or ():
            base = Path(location)
            for path in base.rglob("*.py"):
                if "tests" in path.parts or path.name.startswith("test"):
                    continue
                dotted = ".".join((root, *path.relative_to(base).with_suffix("").parts))
                modules.append((dotted, path))
    return modules


def ram_cache_users() -> dict[str, bool]:
    """Find every function cached through ``plone.memoize.ram``.

    :returns: ``{dotted name: whether the decorator is actually applied}``.
    """
    found: dict[str, bool] = {}
    for dotted, path in _modules():
        source = path.read_text(encoding="utf-8", errors="replace")
        if "plone.memoize" not in source:
            continue
        tree = ast.parse(source)
        module_ram, name_cache = _imports_ram(tree)
        accepted = {"ram.cache"} if module_ram else set()
        if name_cache:
            accepted.add("cache")
        found.update(_users_in_module(tree, dotted, accepted))
    return found


def test_plone_namespace_is_scanned():
    """Control: the scan looks at the installed Plone, not at nothing."""
    assert any("site-packages" in p for p in plone.__path__)


def test_the_table_is_complete():
    """The documented table lists exactly the RAM-cached functions there are."""
    users = ram_cache_users()
    assert sorted(users) == sorted(PLONE_RAM_CACHES)


def test_undecorated_entries():
    """Entries marked ``None`` are calls written without ``@``: never cached."""
    users = ram_cache_users()
    assert {name for name, applied in users.items() if not applied} == {
        name for name, route in PLONE_RAM_CACHES.items() if route is None
    }
