#!/usr/bin/env python3
"""Guard for the documentation contract in AGENTS.md §3 — offline, read-only, pure.

Two failure modes it exists to catch, both of which have actually bitten this workspace:

* **Orphan doc** — a file under ``docs/`` exists on disk but no line of ``docs/INDEX.md`` mentions it.
  It is unreachable in practice: a session reads ``docs/STATE.md`` then the index, never all 176
  files, so the document is silently lost the moment it is written.
* **Ghost index entry** — a row of ``docs/INDEX.md`` names a document that does not exist, whether as
  a ``docs/…`` token or as a relative markdown link target such as ``](NOT-A-FILE.md)``. The map
  promises a file that is not there, and the session that follows it loses the thread.
* **Stale state page** — ``docs/STATE.md`` dated older than the newest ``journal/YYYY-MM-DD.md``.
  STATE is the first page every session reads; when it lags the journal, the first page a session
  reads lies about what is live, what was measured, and what is blocked.

Three further checks cover the other ways the contract goes quietly false: a moved/renamed checkout
(``AGENTS.md`` names a workspace root that no longer exists — this repo was renamed once already), a
journal index that stops covering the journal, and an experiment directory that carries a machine
readable ``RUN.json`` without the ``EVIDENCE.md`` that says what was measured.

The guard is pure, offline and read-only: stdlib only, no writes, no subprocesses, no network. It
takes ``root`` as an argument so tests can point it at a fixture tree.

Red→green: every check is proven to fail before it passes by a fixture test in
``tests/test_agent_context.py`` —

* workspace root  → ``test_missing_workspace_root_path_fails``
* state page      → ``test_missing_state_page_fails``, ``test_state_page_older_than_journal_fails``
* docs index      → ``test_orphan_doc_fails_then_passes``, ``test_ghost_index_entry_fails``,
  ``test_ghost_relative_link_fails_then_passes``, ``test_relative_link_to_real_doc_passes``,
  ``test_docs_prefixed_ghost_row_yields_one_failure``
* journal index   → ``test_journal_entry_absent_from_index_fails``
* experiment shape→ ``test_experiment_without_evidence_fails``
* the CLI itself  → ``test_main_root_flag_returns_1_then_0``

Usage:
    python3 tools/doc_check.py [--root PATH] [--quiet]

Exit 0 only when clean; exit 1 with one ``FAIL ...`` line per failure, so the command can be
recorded as a verdict and re-run by the next session.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WORKSPACE_ROOT_RE = re.compile(r"\*\*Workspace root:\*\*\s*`([^`]+)`")
STATE_DATE_RE = re.compile(r"\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})")
JOURNAL_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
MD_TOKEN_RE = re.compile(r"[A-Za-z0-9._/-]+\.md")
INDEX_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
LINK_SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _md_tokens(text: str) -> set[str]:
    """Every ``*.md`` path-like token in a markdown document, as written."""
    return set(MD_TOKEN_RE.findall(text))


def _journal_dates(root: Path) -> list[date]:
    journal = root / "journal"
    if not journal.is_dir():
        return []
    out: list[date] = []
    for path in journal.iterdir():
        if path.is_file() and JOURNAL_NAME_RE.match(path.name):
            out.append(date.fromisoformat(path.name[: -len(".md")]))
    return sorted(out)


def _workspace_root_failures(root: Path) -> list[str]:
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return [f"AGENTS.md is missing at {agents.as_posix()} (there is no declared workspace root)"]
    match = WORKSPACE_ROOT_RE.search(_read(agents))
    if match is None:
        return ["AGENTS.md has no `**Workspace root:** `<path>`` line (session pickup depends on it)"]
    declared = match.group(1)
    if not Path(declared).expanduser().is_dir():
        return [
            f"AGENTS.md declares workspace root {declared!r} which does not exist "
            "(moved or renamed checkout)"
        ]
    return []


def _state_failures(root: Path) -> list[str]:
    state = root / "docs" / "STATE.md"
    if not state.is_file():
        return ["docs/STATE.md is missing: the first page a session reads does not exist"]
    match = STATE_DATE_RE.search(_read(state))
    if match is None:
        return ["docs/STATE.md has no `**Last updated:** YYYY-MM-DD` line, so its age is unknowable"]
    stated = date.fromisoformat(match.group(1))
    dates = _journal_dates(root)
    if dates and stated < dates[-1]:
        return [
            f"stale state page: docs/STATE.md Last updated {stated.isoformat()} is older than the "
            f"newest journal entry {dates[-1].isoformat()}"
        ]
    return []


def _docs_index_failures(root: Path) -> list[str]:
    docs_dir = root / "docs"
    index = docs_dir / "INDEX.md"
    if not index.is_file():
        return ["docs/INDEX.md is missing: nothing maps the documents under docs/ (all are orphans)"]
    text = _read(index)
    out: list[str] = []
    mentioned: set[str] = set()
    ghosted: set[Path] = set()
    for token in sorted(_md_tokens(text)):
        if token.startswith("docs/"):
            mentioned.add(token[len("docs/") :])
            if not (root / token).is_file():
                out.append(f"ghost index entry: docs/INDEX.md names {token}, which does not exist")
                ghosted.add((root / token).resolve())
        else:
            mentioned.add(token[2:] if token.startswith("./") else token)
    # A row may name its doc with a relative link target instead of a ``docs/…`` token, so resolve
    # every ``](target.md)`` too: a ``docs/…`` target is relative to the root, anything else is
    # relative to ``docs/`` (``GRID-2-FINAL.md`` → ``docs/GRID-2-FINAL.md``, ``../STRUCTURE.md`` →
    # ``STRUCTURE.md``). A target that resolves nowhere is the same ghost as above, so a target
    # already reported as a token ghost is skipped and one bad row yields one failure.
    for lineno, line in enumerate(text.splitlines(), start=1):
        for target in INDEX_LINK_RE.findall(line):
            target = target.strip("<>")
            if target.startswith(LINK_SKIP_PREFIXES):
                continue
            rel = target.split("#", 1)[0]
            if not rel.lower().endswith(".md"):
                continue
            resolved = (root / rel if rel.startswith("docs/") else docs_dir / rel).resolve()
            if resolved in ghosted:
                continue
            ghosted.add(resolved)
            if not resolved.is_file():
                out.append(f"ghost index link: docs/INDEX.md:{lineno} -> {target}")
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            rel = path.relative_to(docs_dir).as_posix()
            if rel == "INDEX.md" or rel in mentioned:
                continue
            out.append(f"orphan doc: docs/{rel} exists but no line of docs/INDEX.md mentions it")
    return out


def _journal_index_failures(root: Path) -> list[str]:
    journal = root / "journal"
    index = journal / "INDEX.md"
    if not index.is_file():
        return ["journal/INDEX.md is missing: the journal has no narrative index"]
    text = _read(index)
    out: list[str] = []
    if journal.is_dir():
        for path in sorted(journal.iterdir()):
            if path.is_file() and JOURNAL_NAME_RE.match(path.name) and path.name not in text:
                out.append(f"journal entry journal/{path.name} has no row or mention in journal/INDEX.md")
    for token in sorted(_md_tokens(text)):
        if "/" in token:
            if token.startswith("journal/") and not (root / token).is_file():
                out.append(f"ghost journal link: journal/INDEX.md names {token}, which does not exist")
        elif JOURNAL_NAME_RE.match(token) and not (journal / token).is_file():
            out.append(f"ghost journal link: journal/INDEX.md names {token}, which does not exist")
    return out


def _experiment_failures(root: Path) -> list[str]:
    base = root / "experiments"
    if not base.is_dir():
        return []
    out: list[str] = []
    for child in sorted(p for p in base.iterdir() if p.is_dir()):
        if (child / "RUN.json").is_file() and not (child / "EVIDENCE.md").is_file():
            out.append(
                f"experiment experiments/{child.name} has RUN.json but no EVIDENCE.md "
                "(AGENTS.md §3.4: the run record is not the record of what was measured)"
            )
    return out


def check(root: Path) -> list[str]:
    """Return a human-readable failure per violation of the documentation contract; ``[]`` when clean."""
    root = Path(root)
    failures: list[str] = []
    failures += _workspace_root_failures(root)
    failures += _state_failures(root)
    failures += _docs_index_failures(root)
    failures += _journal_index_failures(root)
    failures += _experiment_failures(root)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the AGENTS.md §3 documentation contract (offline, read-only)."
    )
    parser.add_argument("--root", default=str(ROOT), help="repository root to check (default: this checkout)")
    parser.add_argument("--quiet", action="store_true", help="print failures only, no summary line")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    failures = check(root)
    for failure in failures:
        print(f"FAIL {failure}")
    if not args.quiet:
        if failures:
            print(f"{len(failures)} failure(s) under {root.as_posix()}")
        else:
            print(f"OK docs clean under {root.as_posix()}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
