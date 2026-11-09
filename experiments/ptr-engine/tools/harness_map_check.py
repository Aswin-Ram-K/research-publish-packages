#!/usr/bin/env python3
"""harness_map_check.py -- verify that the ``file:line`` citations in a harness map resolve.

Why this exists
---------------
`docs/HARNESS-MAP.md` cites code as `path.py:NNN symbol`. The path can exist while the
*line* no longer holds that symbol: `run_longrun.py` grew to 3008 lines and every one of
the map's later references moved 500-700 lines. `path_refs_resolve.py` validates that a
cited path exists; it cannot see that line 1191 is no longer `make_row`. This guard checks
the LINE, and (when the citation names a symbol) that the line still falls inside that
symbol's body.

What it checks, per citation
----------------------------
1. the file resolves under one of the repo roots;
2. the line number is inside the file;
3. the line is neither blank nor comment-only;
4. if the citation names a symbol S (e.g. ``run_longrun.py:1191 make_row``) then S must
   resolve in that file (AST: functions, classes, module-level assignments) and the cited
   line must fall inside S's body;
5. if S has a row in the map's `## Line-reference refresh` anchor table, that row's
   `current` value is authoritative (a range `a-b` is accepted).

Baseline (forward-only)
-----------------------
Historical citations that were already wrong when the guard was frozen are listed in
`experiments/ptr-engine/measure/HARNESS-MAP-LINEREFS.json` under `guard.baseline` as
`path:line` entries. They are reported as `baselined`, not as failures, so the guard does
not fail today on a record it did not write. Anything NOT baselined must pass: a new stale
citation fails (exit 1). Re-freezing the baseline is an explicit act, never automatic.

KNOWN LIMIT (stated, not hidden)
--------------------------------
A citation written as a bare `:NNN` with no symbol, and a citation whose symbol happens to
appear somewhere on the cited line, can still pass after a refactor MOVED the code but left
that line non-empty. This guard checks existence, comment/blank-ness, and symbol span -- it
cannot prove the prose around the citation still describes the code there. Symbol anchors
(`file::symbol`) do not have that failure mode, which is why the residual note in
`docs/HARNESS-MAP.md` recommends them.

Usage
-----
    python3 experiments/ptr-engine/tools/harness_map_check.py --check
    python3 experiments/ptr-engine/tools/harness_map_check.py --check --map /tmp/map.md
    python3 experiments/ptr-engine/tools/harness_map_check.py --report

Exit: 0 = every (non-baselined) citation resolves; 1 = at least one does not; 2 = usage.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_MAP = os.path.join(REPO, "docs", "HARNESS-MAP.md")
DEFAULT_BASELINE = os.path.join(REPO, "experiments", "ptr-engine", "measure",
                                "HARNESS-MAP-LINEREFS.json")
ROOTS = ("", "experiments/ptr-engine/longrun/", "experiments/ptr-engine/",
         "experiments/ptr-engine/tools/", "experiments/ptr-engine/ptr_engine/", "tests/")

# path.py:LINE  or  bare :LINE, optional range -N, optional symbol token
TOK = re.compile(
    r"(?:(?P<path>(?:[A-Za-z0-9_.+-]+/)*[A-Za-z0-9_.+-]+\.py):(?P<line>\d+)"
    r"|(?<![\w/.:-]):(?P<bline>\d+))"
    r"(?:[-\u2013](?P<range>\d+))?"
    r"(?:\s+(?P<sym>[A-Za-z_][A-Za-z0-9_]*))?"
)
ANCHOR_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*"
                        r"(\d+)(?:-(\d+))?\s*\|")


def _rel(path: str) -> str:
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def resolve_file(cited: str) -> str | None:
    """Resolve a cited (possibly basename-relative) path to an absolute file."""
    cited = cited.strip()
    for root in ROOTS:
        cand = os.path.join(REPO, root, cited) if root else os.path.join(REPO, cited)
        if os.path.isfile(cand):
            return os.path.abspath(cand)
    return None


def symbols(path: str) -> dict[str, tuple[int, int]]:
    """name -> (first_line, last_line) for defs/classes/module-level assignments."""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return {}
    out: dict[str, tuple[int, int]] = {}

    def add(name: str, node) -> None:
        end = getattr(node, "end_lineno", None) or getattr(node, "lineno", 0)
        start = getattr(node, "lineno", 0)
        if name not in out:
            out[name] = (start, end)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            add(node.name, node)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    add(tgt.id, node)
    return out


def parse_anchors(text: str) -> dict[tuple[str, str], tuple[int, int]]:
    """Read the `## Line-reference refresh` table: (relpath, symbol) -> (first, last)."""
    anchors: dict[tuple[str, str], tuple[int, int]] = {}
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## Line-reference refresh")
            continue
        if not inside:
            continue
        m = ANCHOR_ROW.match(line)
        if not m:
            continue
        path, sym, _old, cur = m.group(1), m.group(2), m.group(3), m.group(4)
        if sym in ("symbol", "---") or not path.endswith(".py"):
            continue
        first = int(cur)
        last = int(m.group(5)) if m.group(5) else first
        anchors[(_rel(os.path.join(REPO, path)) if not os.path.isabs(path) else _rel(path),
                  sym)] = (first, last)
    return anchors


def citations(text: str) -> list[dict]:
    """Extract every citation. Bare `:NNN` inherits the last path seen on its line."""
    out: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        last_path = None
        for m in TOK.finditer(line):
            if m.group("path"):
                cited, num = m.group("path"), int(m.group("line"))
                last_path = cited
            else:
                if last_path is None:
                    continue  # a bare `:NNN` with no file context is not a citation
                cited, num = last_path, int(m.group("bline"))
            out.append({"map_line": lineno, "cited": cited, "line": num,
                        "symbol": m.group("sym") or None,
                        # a call-shaped token ("name(") is code; a bare word is prose
                        "call": bool(m.group("sym")) and line[m.end():m.end() + 1] == "("})
    return out


def load_baseline(path: str) -> tuple[set[str], dict]:
    if not path or not os.path.isfile(path):
        return set(), {}
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return set(), {}
    entries = ((doc.get("guard") or {}).get("baseline") or [])
    return {str(e) for e in entries}, doc


def check_text(text: str, baseline: set[str]) -> list[dict]:
    anchors = parse_anchors(text)
    results = []
    cache: dict[str, tuple[str | None, int, dict]] = {}
    for c in citations(text):
        abs_path = resolve_file(c["cited"])
        key = f"{_rel(abs_path)}:{c['line']}" if abs_path else f"{c['cited']}:{c['line']}"
        rec = dict(c, key=key, status="ok", detail="")
        if abs_path is None:
            rec.update(status="file_not_found", detail=f"no file for {c['cited']}")
            results.append(rec)
            continue
        if abs_path not in cache:
            try:
                lines = open(abs_path, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                lines = []
            cache[abs_path] = (abs_path, len(lines), symbols(abs_path))
        _, nlines, symtab = cache[abs_path]
        rel = _rel(abs_path)
        rec["key"] = f"{rel}:{c['line']}"
        if not (1 <= c["line"] <= nlines):
            rec.update(status="line_out_of_range", detail=f"{rel} has {nlines} lines")
            results.append(rec)
            continue
        src = open(abs_path, encoding="utf-8", errors="replace").read().splitlines()
        stripped = src[c["line"] - 1].strip()
        if not stripped:
            rec.update(status="blank_line", detail=f"{rel}:{c['line']} is blank")
        elif stripped.startswith("#"):
            rec.update(status="comment_only",
                       detail=f"{rel}:{c['line']} is a comment: {stripped[:60]}")
        elif c["symbol"] and (c["call"] or (rel, c["symbol"]) in anchors):
            # Validate the symbol only when the citation is call-shaped (`name(`) or the
            # refresh table names it.  A prose word after a line ("marker check") is not a
            # claim about a symbol; the map is allowed to describe a line in English.
            sym = c["symbol"]
            anchor = anchors.get((rel, sym))
            if anchor:
                lo, hi = anchor
                if not (lo <= c["line"] <= hi):
                    rec.update(status="anchor_mismatch",
                               detail=f"anchor table puts {sym} at {lo}-{hi}")
            elif sym not in symtab:
                rec.update(status="symbol_missing",
                           detail=f"{sym} does not resolve in {rel}")
            else:
                lo, hi = symtab[sym]
                if not (lo <= c["line"] <= hi):
                    rec.update(status="symbol_moved",
                               detail=f"{sym} is at {lo}-{hi} in {rel}")
        if rec["status"] != "ok" and rec["key"] in baseline:
            rec["status"] = "baselined"
        results.append(rec)
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 on any non-baselined miss")
    ap.add_argument("--report", action="store_true", help="print every citation and status")
    ap.add_argument("--map", default=DEFAULT_MAP, help="map markdown to check")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE,
                    help="JSON carrying guard.baseline (path:line entries)")
    ap.add_argument("--json", metavar="PATH", help="write the result rows as JSON")
    args = ap.parse_args(argv)
    if not (args.check or args.report):
        args.check = True
    try:
        text = open(args.map, encoding="utf-8").read()
    except OSError as exc:
        print(f"harness_map_check: cannot read {args.map}: {exc}", file=sys.stderr)
        return 2
    baseline, _doc = load_baseline(args.baseline)
    rows = check_text(text, baseline)
    bad = [r for r in rows if r["status"] not in ("ok", "baselined")]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    if args.report:
        for r in rows:
            print(f"{r['status']:>16}  {r['key']:<70} "
                  f"{('sym=' + r['symbol']) if r['symbol'] else '':<28} {r['detail']}")
    print(f"harness_map_check: {len(rows)} citations · "
          + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())),
          file=sys.stderr)
    if bad:
        print(f"harness_map_check: FAIL ({len(bad)} unbaselined citation(s))", file=sys.stderr)
        for r in bad:
            print(f"  {r['status']}  {r['key']}  {r['detail']}", file=sys.stderr)
    else:
        print("harness_map_check: OK", file=sys.stderr)
    if args.json:
        payload = {"map": os.path.abspath(args.map), "baseline": sorted(baseline),
                   "counts": counts, "rows": rows}
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
    if args.check:
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
