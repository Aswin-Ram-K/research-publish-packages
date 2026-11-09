"""Fixture tests for ``tools/doc_check.py`` — each test reproduces one documented failure mode.

Red→green in the house style (AGENTS.md §4): every check in the guard is first shown to FAIL on a
broken fixture tree, then shown to pass on the repaired tree — the orphan-doc test does both acts in
one test, ``test_main_root_flag_returns_1_then_0`` does both through the CLI. Fixture roots are built
under ``tmp_path`` so nothing here depends on, or writes to, the real checkout.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_doc_check():
    path = ROOT / "tools" / "doc_check.py"
    spec = importlib.util.spec_from_file_location("doc_check_under_test", path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doc_check = _load_doc_check()

DAY = "2026-10-10"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_tree(tmp_path: Path, *, state_date: str = DAY, journal_day: str = DAY) -> Path:
    """A minimal tree that passes every check, so each test breaks exactly one thing in it."""
    root = tmp_path
    _write(root / "AGENTS.md", f"# AGENTS.md\n\n**Workspace root:** `{root.as_posix()}`\n")
    _write(root / "docs" / "STATE.md", f"# STATE\n\n**Last updated:** {state_date} · **By:** fixture\n")
    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md) — current state, read first\n- [a](a.md) — fixture doc\n",
    )
    _write(root / "docs" / "a.md", "# a\n")
    _write(root / "journal" / f"{journal_day}.md", f"# {journal_day}\n\nfixture entry\n")
    _write(
        root / "journal" / "INDEX.md",
        "# Journal index\n\n| Date | Headline |\n|---|---|\n"
        f"| [{journal_day}]({journal_day}.md) | fixture |\n",
    )
    _write(root / "experiments" / "demo" / "README.md", "# demo\n")
    _write(root / "experiments" / "demo" / "RUN.json", "{}\n")
    _write(root / "experiments" / "demo" / "EVIDENCE.md", "# evidence\n")
    return root


def test_orphan_doc_fails_then_passes(tmp_path: Path) -> None:
    """Failure mode 1: a doc exists on disk but no index line mentions it — then one line fixes it."""
    root = _make_tree(tmp_path)
    assert doc_check.check(root) == []

    _write(root / "docs" / "orphan.md", "# orphan\n")
    failures = doc_check.check(root)
    assert any("orphan.md" in failure for failure in failures), failures

    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n- [o](orphan.md)\n",
    )
    assert doc_check.check(root) == []


def test_ghost_index_entry_fails(tmp_path: Path) -> None:
    """The converse of failure mode 1: the index names a file that does not exist."""
    root = _make_tree(tmp_path)
    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n- [g](docs/ghost.md)\n",
    )
    failures = doc_check.check(root)
    assert any("ghost" in failure and "docs/ghost.md" in failure for failure in failures), failures


def test_ghost_relative_link_fails_then_passes(tmp_path: Path) -> None:
    """Probe P6: a row written ``[NOT-A-FILE](NOT-A-FILE.md)`` names a doc that does not exist.

    The target is relative, not ``docs/``-prefixed, so it resolves against ``docs/``; a guard that
    only existence-checks ``docs/…`` tokens passes this row, which is weaker than AGENTS.md §3.3.
    The second act creates the target and the check passes, so the assertion tracks whether the
    file exists rather than how many messages were printed.
    """
    root = _make_tree(tmp_path)
    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n"
        "| [NOT-A-FILE](NOT-A-FILE.md) | x | current |\n",
    )
    failures = doc_check.check(root)
    assert any("ghost index link" in f and "NOT-A-FILE.md" in f for f in failures), failures

    _write(root / "docs" / "NOT-A-FILE.md", "# the doc the row names\n")
    assert doc_check.check(root) == []


def test_relative_link_to_real_doc_passes(tmp_path: Path) -> None:
    """Resolution both ways: ``](a.md)`` is under ``docs/``, ``](../STRUCTURE.md)`` is under the root."""
    root = _make_tree(tmp_path)
    _write(root / "STRUCTURE.md", "# structure\n")
    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n- [s](../STRUCTURE.md)\n"
        "- [h](STATE.md#top) is an anchor on a real doc\n"
        "- [e](https://example.com/x.md) and [top](#top) are not file paths\n",
    )
    assert doc_check.check(root) == []


def test_docs_prefixed_ghost_row_yields_one_failure(tmp_path: Path) -> None:
    """One bad row is one failure: the token ghost and the link ghost name the same missing file."""
    root = _make_tree(tmp_path)
    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n- [g](docs/ghost.md)\n",
    )
    ghosts = [failure for failure in doc_check.check(root) if "ghost" in failure]
    assert len(ghosts) == 1, ghosts


def test_missing_state_page_fails(tmp_path: Path) -> None:
    """Failure mode 2, first variant: the page every session reads first is absent."""
    root = _make_tree(tmp_path)
    (root / "docs" / "STATE.md").unlink()
    failures = doc_check.check(root)
    assert any("docs/STATE.md" in failure for failure in failures), failures


def test_state_page_older_than_journal_fails(tmp_path: Path) -> None:
    """Failure mode 2: STATE says 2026-10-01 while a journal entry is dated 2026-10-15 — the page lies."""
    root = _make_tree(tmp_path, state_date="2026-10-01", journal_day="2026-10-15")
    failures = doc_check.check(root)
    assert any("2026-10-01" in failure and "2026-10-15" in failure for failure in failures), failures


def test_journal_entry_absent_from_index_fails(tmp_path: Path) -> None:
    """A dated journal entry with no row in ``journal/INDEX.md`` is invisible to the narrative index."""
    root = _make_tree(tmp_path)
    _write(root / "journal" / "2026-10-11.md", "# 2026-10-11\n\nsecond entry\n")
    failures = doc_check.check(root)
    assert any("2026-10-11.md" in failure for failure in failures), failures


def test_missing_workspace_root_path_fails(tmp_path: Path) -> None:
    """A renamed or moved checkout: ``AGENTS.md`` names a workspace root that no longer exists."""
    root = _make_tree(tmp_path)
    _write(root / "AGENTS.md", "# AGENTS.md\n\n**Workspace root:** `/nonexistent/research extractor`\n")
    failures = doc_check.check(root)
    assert any("/nonexistent/research extractor" in failure for failure in failures), failures


def test_experiment_without_evidence_fails(tmp_path: Path) -> None:
    """AGENTS.md §3.4: an experiment carrying ``RUN.json`` must also carry ``EVIDENCE.md``."""
    root = _make_tree(tmp_path)
    (root / "experiments" / "demo" / "EVIDENCE.md").unlink()
    failures = doc_check.check(root)
    assert any("demo" in failure and "EVIDENCE.md" in failure for failure in failures), failures


def test_main_root_flag_returns_1_then_0(tmp_path: Path, capsys) -> None:
    """``--root`` is honoured: exit 1 on the broken fixture tree, exit 0 once it is repaired."""
    root = _make_tree(tmp_path)
    _write(root / "docs" / "orphan.md", "# orphan\n")
    assert doc_check.main(["--root", str(root)]) == 1
    assert "FAIL" in capsys.readouterr().out

    _write(
        root / "docs" / "INDEX.md",
        "# Docs index\n\n- [state](STATE.md)\n- [a](a.md)\n- [o](orphan.md)\n",
    )
    assert doc_check.main(["--root", str(root), "--quiet"]) == 0


def test_current_tree_is_clean() -> None:
    """The real checkout passes every check — this is the post-``docs/INDEX.md``-landing state.

    ``docs/`` holds 176 ``.md`` files including ``INDEX.md``, and every one of them has a row, so
    this asserts that the index covers the tree as it stands now (no orphans, no ghost entries or
    relative link targets) rather than a future state.
    """
    assert doc_check.check(ROOT) == []
