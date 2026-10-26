"""Red→green guard for the ``live`` convention: an explicit MARKER, never a name.

Background — the false-green generator this pins shut
----------------------------------------------------
``tests/conftest.py`` used to decide skips with::

    skip = pytest.mark.skip(reason="live test — run with --live or RESEXTRACT_LIVE=1")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)

``item.keywords`` is a mapping of *bare* keyword keys built by pytest for an
item: the item's own full name (``test_param[live]``), the enclosing module and
class names, its mark names — and **every parametrisation id as a bare key**.
So ``@pytest.mark.parametrize("mode", ["live"])``, or a module/class literally
named ``live``, silently skipped tests that never touch the network.  ``x in
item.keywords`` is therefore *not* the name-substring test it looks like, but
the flaw is the same in kind: an arbitrary identifier decides whether a test
runs, and a skipped test reports success.

RED→GREEN PROOF (pytest 9.1.1, ``PYTHONDONTWRITEBYTECODE=1``; fixed
``tests/conftest.py`` sha256
``72ac7401ff18a7b790e9060ccaca63e85f42c732e5671114ede5934bb82214aa``)
----------------------------------------------------------------------
GREEN (fixed conftest): ``10 passed``.

(a) **Name/keyword rule restored** (only the skip loop reverted to
    ``if "live" in item.keywords``): ``3 failed, 6 passed, 1 skipped`` —
      - ``test_parametrised_id_live_is_not_a_marker[live]`` is **silently
        skipped** by conftest (bare keyword key ``live``);
      - ``test_no_item_is_skipped_without_the_live_marker`` FAILS::

          AssertionError: these items were skipped by the 'live' convention
          without carrying @pytest.mark.live (name-based skip regression?):
          ['tests/test_live_marker_convention.py::test_parametrised_id_live_is_not_a_marker[live]']

      - ``test_conftest_hook_skips_only_live_marked_items`` and
        ``test_does_not_decide_live_by_name_or_keywords`` also FAIL.
      ⇒ **RED**; ``tests/conftest.py`` restored **bit-identically** (sha256
      ``72ac7401…``).

(b) **Marker handling removed** (the ``get_closest_marker("live")`` branch
    deleted, everything else kept): ``2 failed, 8 passed`` —
      - ``test_conftest_hook_skips_only_live_marked_items`` FAILS::

          AssertionError: a live-marked item was NOT skipped without --live

      - ``test_does_not_decide_live_by_name_or_keywords`` FAILS: the
        ``get_closest_marker("live")`` call is gone.
      ⇒ **RED**; restored **bit-identically** (sha256 ``72ac7401…``).

GREEN again after restore: ``10 passed``.  ``--live`` still runs live-marked
items (asserted against the hook below, and ``pytest tests/ --collect-only
--live`` reports ``0 skipped`` versus ``1`` without it).
"""

from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

import pytest

CONFTEST_PATH = Path(__file__).resolve().with_name("conftest.py")
LIVE_SKIP_REASON = "live test — run with --live or RESEXTRACT_LIVE=1"


def _live_requested(config: pytest.Config) -> bool:
    return bool(config.getoption("--live")) or os.environ.get("RESEXTRACT_LIVE") == "1"


def _load_conftest() -> ModuleType:
    """Load ``tests/conftest.py`` by path so the hook can be exercised directly."""
    import sys

    spec = importlib.util.spec_from_file_location("u016_conftest_under_test", CONFTEST_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve annotations through sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


# --------------------------------------------------------------------------- #
# (a) A name / parametrisation id containing "live" is NOT a live marker.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("mode", ["live", "deliver", "lively", "olive", "livewire"])
def test_parametrised_id_live_is_not_a_marker(mode: str) -> None:
    """Under the old keyword rule the ``live`` id here was silently skipped.

    The other ids are the vocabulary values a neighbouring unit had to rename
    to escape that rule.
    """
    assert mode in {"live", "deliver", "lively", "olive", "livewire"}


def test_no_item_is_skipped_without_the_live_marker(request: pytest.FixtureRequest) -> None:
    """Nothing may carry the live skip reason unless it is explicitly marked ``live``.

    This is the guard that turns red when a name-based rule comes back: the
    parametrised item above is then skipped with this exact reason while
    carrying no ``live`` marker.
    """
    offenders: list[str] = []
    for item in request.session.items:
        if item.get_closest_marker("live") is not None:
            continue
        reasons = [m.kwargs.get("reason") for m in item.iter_markers(name="skip")]
        if LIVE_SKIP_REASON in reasons:
            offenders.append(item.nodeid)
    assert not offenders, (
        "these items were skipped by the 'live' convention without carrying "
        f"@pytest.mark.live (name-based skip regression?): {offenders}"
    )


# --------------------------------------------------------------------------- #
# (b) A MARKED item is skipped without --live, and runs with --live.
# --------------------------------------------------------------------------- #


class _Marker:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeItem:
    """Minimal stand-in for ``pytest.Item``.

    Deliberately has **no** ``keywords``/``name`` mapping: the correct hook must
    not need one, and the old rule cannot even be applied to it.
    """

    def __init__(self, nodeid: str, *, live: bool = False) -> None:
        self.nodeid = nodeid
        self._live = live
        self.added: list[Any] = []

    def get_closest_marker(self, name: str) -> _Marker | None:
        return _Marker(name) if (self._live and name == "live") else None

    def iter_markers(self, name: str | None = None) -> Iterable[_Marker]:
        if self._live and name in (None, "live"):
            return iter([_Marker("live")])
        return iter(())

    def add_marker(self, marker: Any) -> None:
        self.added.append(getattr(marker, "mark", marker))


class _FakeConfig:
    def __init__(self, live: bool) -> None:
        self._live = live

    def getoption(self, name: str) -> bool:
        assert name == "--live", name
        return self._live


def test_conftest_hook_skips_only_live_marked_items() -> None:
    """Marker ⇒ skipped without ``--live``; unmarked ⇒ untouched; ``--live`` ⇒ untouched."""
    module = _load_conftest()
    hook = module.pytest_collection_modifyitems

    marked = _FakeItem("tests/fake.py::test_needs_occamy", live=True)
    plain = _FakeItem("tests/fake.py::test_vocabulary[live]")
    hook(_FakeConfig(live=False), [marked, plain])
    assert len(marked.added) == 1, "a live-marked item was NOT skipped without --live"
    assert marked.added[0].name == "skip"
    assert marked.added[0].kwargs.get("reason") == module.LIVE_SKIP_REASON
    assert plain.added == [], "an unmarked item was skipped — the rule is not marker-only"

    marked_flagged = _FakeItem("tests/fake.py::test_needs_occamy", live=True)
    plain_flagged = _FakeItem("tests/fake.py::test_vocabulary[live]")
    hook(_FakeConfig(live=True), [marked_flagged, plain_flagged])
    assert marked_flagged.added == [], "--live no longer runs live-marked items"
    assert plain_flagged.added == []


def test_does_not_decide_live_by_name_or_keywords() -> None:
    """Static pin: no *executable* comparison against a name/keyword may return.

    Comments and docstrings that quote the old rule are ignored — this walks the
    AST, so only real code counts.
    """
    tree = ast.parse(CONFTEST_PATH.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.In, ast.NotIn)):
            continue
        left = ast.unparse(node.left)
        right = ast.unparse(node.comparators[0])
        if "live" in left and any(t in right for t in ("keywords", "name", "nodeid")):
            offenders.append(ast.unparse(node))
    assert not offenders, f"the skip decision reads an item's name again: {offenders}"
    assert 'get_closest_marker("live")' in CONFTEST_PATH.read_text(encoding="utf-8")


def test_live_marker_is_registered(pytestconfig: pytest.Config) -> None:
    """pytest must know the mark, or it warns about an unknown mark."""
    registered = [entry.split(":", 1)[0].strip() for entry in pytestconfig.getini("markers")]
    assert "live" in registered, f"'live' marker not registered: {registered}"


def test_skipped_live_tests_are_announced_not_counted_as_passes() -> None:
    """A skipped live test must be announced, never silently counted as a pass."""
    module = _load_conftest()

    class _Report:
        # pytest prefixes the reason in the report repr: "Skipped: <reason>".
        longrepr = ("tests/fake.py", 1, f"Skipped: {module.LIVE_SKIP_REASON}")

    class _Reporter:
        def __init__(self) -> None:
            self.stats = {"skipped": [_Report()]}
            self.seps: list[str] = []

        def write_sep(self, sep: str, title: str, **markup: Any) -> None:
            self.seps.append(title)

    loud = _Reporter()
    module.pytest_terminal_summary(loud, 0, _FakeConfig(live=False))
    assert any("SKIPPED" in line and "NOT passed" in line for line in loud.seps), loud.seps

    quiet = _Reporter()
    module.pytest_terminal_summary(quiet, 0, _FakeConfig(live=True))
    assert quiet.seps == []
