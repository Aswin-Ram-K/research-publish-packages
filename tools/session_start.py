#!/usr/bin/env python3
"""Ten-second orientation snapshot — read-only, no writes, no network.

A session that re-reads five files (STATE, the newest journal, the handoffs directory, the request
ledger, git) to answer "where am I, what is live, what changed, what am I allowed to spend" burns
minutes and still guesses. This prints the answer in one screen: the root it is working from, whether
the current directory is that root or an omp worktree (a worktree carries tracked files only — the
~1,300 untracked files that *are* the current state are invisible there, so every edit lands in the
wrong tree), the git checkpoint, the STATE date, the newest journal entries and handoffs, the request
ledger, and the documentation guard's verdict.

It is deliberately tolerant: every missing file, failed git call or unparseable JSON degrades to a
short note instead of an exception, and it exits 0 always — a documentation failure is a WARN for the
human reading it, not a tool failure.

Usage:
    python3 tools/session_start.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEDGER_CANDIDATES = (
    "measure/REQUEST-LEDGER.json",
    "experiments/ptr-engine/measure/REQUEST-LEDGER.json",
)
JOURNAL_RE = r"^\d{4}-\d{2}-\d{2}\.md$"
POINTERS = (
    "docs/STATE.md §1 — the live experiment",
    "docs/GRID-RUNBOOK.md — how to run it",
    "AGENTS.md §10 — the close-out checklist",
)


def _git(*args: str) -> str | None:
    """Run one read-only git command under the root; ``None`` when git is absent or the call fails."""
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _git_line() -> str:
    status = _git("status", "--porcelain=v1")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    head = _git("rev-parse", "--short", "HEAD")
    when = _git("log", "-1", "--format=%cI")
    if status is None or branch is None:
        return "git      : unavailable (not a checkout, or git failed)"
    lines = status.splitlines()
    untracked = sum(1 for line in lines if line.startswith("??"))
    modified = sum(1 for line in lines if line and not line.startswith(("??", "!!")))
    return (
        f"git      : branch {branch} · HEAD {head or 'unknown'} · {when or 'date unknown'} · "
        f"tracked-modified {modified} · untracked {untracked}"
    )


def _state_line() -> str:
    state = ROOT / "docs" / "STATE.md"
    try:
        text = state.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "state    : docs/STATE.md missing"
    for line in text.splitlines():
        if "**Last updated:**" in line:
            return f"state    : {line.strip()}"
    return "state    : docs/STATE.md has no Last updated line"


def _journal_lines(limit: int = 3) -> list[str]:
    journal = ROOT / "journal"
    try:
        entries = sorted(
            (p for p in journal.iterdir() if p.is_file() and p.suffix == ".md" and p.name[:4].isdigit()),
            key=lambda p: p.name,
            reverse=True,
        )[:limit]
    except OSError:
        return ["journal  : journal/ missing"]
    out: list[str] = []
    for path in entries:
        heading = ""
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("#"):
                    heading = line.lstrip("#").strip()
                    break
        except OSError:
            heading = "(unreadable)"
        out.append(f"journal  : {path.name} — {heading or '(no heading)'}")
    return out or ["journal  : no dated journal entries"]


def _handoff_lines(limit: int = 3) -> list[str]:
    handoffs = ROOT / "orchestration" / "handoffs"
    try:
        paths = sorted(handoffs.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    except OSError:
        return ["handoffs : orchestration/handoffs/ missing"]
    out: list[str] = []
    for path in paths:
        stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        status = "unparseable"
        try:
            status = str(json.loads(path.read_text(encoding="utf-8")).get("status", "(no status field)"))
        except (OSError, ValueError, AttributeError):
            pass
        out.append(f"handoffs : {path.name} · {stamp} · status {status}")
    return out or ["handoffs : none"]


def _ledger_line() -> str:
    for candidate in LEDGER_CANDIDATES:
        path = ROOT / candidate
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return f"ledger   : {candidate} unreadable"
        if not isinstance(data, dict):
            return f"ledger   : {candidate} has no ledger object"
        block = data.get("cap") if isinstance(data.get("cap"), dict) else data.get("budget")
        if isinstance(block, dict):
            # the ledger of record nests the budget: budget.cap / budget.spent / budget.remaining
            requests = data.get("requests", block.get("spent"))
            remaining = data.get("remaining", block.get("remaining"))
            cap = block.get("cap")
        else:
            requests = data.get("requests")
            remaining = data.get("remaining")
            cap = block or data.get("budget")
        if cap is None and isinstance(requests, int) and isinstance(remaining, int):
            cap = requests + remaining
        return f"ledger   : cap {cap if cap is not None else '?'} · requests {requests if requests is not None else '?'} · remaining {remaining if remaining is not None else '?'}  ({candidate})"
    return "ledger   : no REQUEST-LEDGER.json (skipped)"


def _doc_lines() -> list[str]:
    path = ROOT / "tools" / "doc_check.py"
    spec = importlib.util.spec_from_file_location("doc_check_for_session_start", path)
    if spec is None or spec.loader is None:
        return ["docs     : FAIL (tools/doc_check.py not loadable)"]
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        failures = module.check(ROOT)
    except Exception as exc:  # noqa: BLE001 - a broken guard is reported, never raised at the session
        return [f"docs     : FAIL (guard raised {type(exc).__name__}: {exc})"]
    if not failures:
        return ["docs     : PASS"]
    out = [f"docs     : FAIL ({len(failures)})"]
    out += [f"           {failure}" for failure in failures[:3]]
    return out


def main(argv: list[str] | None = None) -> int:
    cwd = Path.cwd().resolve()
    lines = ["session_start — read-only orientation snapshot", f"root     : {ROOT.as_posix()}"]
    try:
        inside = cwd == ROOT or ROOT in cwd.parents
    except OSError:
        inside = False
    lines.append(f"cwd      : {cwd.as_posix()}")
    if not inside:
        lines.append(
            "WARN     : cwd is OUTSIDE the workspace root — an omp worktree checkout carries tracked "
            "files only; untracked state is invisible and writes land in the wrong tree. Use absolute "
            f"paths under {ROOT.as_posix()}."
        )
    lines.append(_git_line())
    lines.append(_state_line())
    lines += _journal_lines()
    lines += _handoff_lines()
    lines.append(_ledger_line())
    lines += _doc_lines()
    lines.append("next     : " + " · ".join(POINTERS))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
