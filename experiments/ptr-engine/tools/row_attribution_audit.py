#!/usr/bin/env python3
"""row_attribution_audit.py - the accounting of the record for turn/row attribution.

READ-ONLY over the historical rows files.  It answers three questions and writes the
machine-readable answer to ``experiments/ptr-engine/measure/ROW-ATTRIBUTION.json``:

  1. per tools grid: how many ``kind="turn"`` rows are MIRRORS of a ``tool-followup``
     row (same arm/rep/turn and the same measured ``ttft_s``/``latency_s``), and how
     many are genuine turn measurements;
  2. whether any published per-turn latency figure was computed over such mirrors, so
     the figure is measured on the FOLLOW-UP request rather than on the turn's own;
  3. the sha256 of every rows file BEFORE and AFTER the audit, which must match --
     this tool never writes a row file, a grade file, or a report.

Usage (from the workspace root):

    python3 experiments/ptr-engine/tools/row_attribution_audit.py
    python3 experiments/ptr-engine/tools/row_attribution_audit.py --check   # exit 1 if a sha moved

The pre-fix writer is described in ``orchestration/handoffs/DEDUPE-ROOT-CAUSE.json``
(``evidence.double_append``); the model this audit contradicts is stated in
``docs/ROW-MODEL.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(HERE)                      # experiments/ptr-engine
WORKSPACE = os.path.dirname(os.path.dirname(PTR))
MEASURE = os.path.join(PTR, "measure")
OUT = os.path.join(MEASURE, "ROW-ATTRIBUTION.json")
REPORT = os.path.join(MEASURE, "LATENCY-REPORT.json")

# The grid table is READ from the report tool when it imports cleanly (one source of
# truth); the literal below is the fallback so this audit can never fail to name a grid.
GRID_FALLBACK = [
    ("G1", "stage1", "rows-longrun-2026-10-26.jsonl"),
    ("G2", "smoke-rp", "rows-longrun-2026-10-26-policy.jsonl"),
    ("G3", "fix-smoke", "rows-longrun-2026-10-26-fix.jsonl"),
    ("G4", "RUN-C-V2", "rows-longrun-c-2026-10-26.jsonl"),
    ("G5", "V3", "rows-longrun-v3-2026-10-26.jsonl"),
    ("G6", "V4", "rows-longrun-v4-2026-10-26.jsonl"),
    ("G7", "V4-TOOLS", "rows-longrun-v4-tools-2026-10-26.jsonl"),
    ("G8", "V5-TOOLS", "rows-longrun-v5-tools.jsonl"),
    ("G9", "V6-TOOLS", "rows-longrun-v6-tools.jsonl"),
    ("G10", "CELL-145758Z", "rows-cell-pointer-stable-20261026T145758Z.jsonl"),
]

#: Fields whose agreement proves the turn row carries another request's measurement.
MEASURED = ("ttft_s", "latency_s", "wall_ms", "prompt_tokens", "completion_tokens")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grids() -> list[tuple[str, str, str]]:
    path = os.path.join(PTR, "tools", "latency_report.py")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        out = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('{"grid_id"'):
                continue
        # simple, dependency-free parse of the GRIDS literal
        import ast
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", None) == "GRIDS" for t in node.targets):
                val = ast.literal_eval(node.value)
                out = [(g["grid_id"], g["label"], g["rows_file"]) for g in val]
        if out:
            return out
    except Exception:
        pass
    return GRID_FALLBACK


def read_rows(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _key(row: dict) -> tuple:
    return (row.get("arm") or "default", row.get("rep"), row.get("turn"))


def audit_file(path: str) -> dict:
    rows = read_rows(path)
    by_key: dict[tuple, list[dict]] = {}
    for r in rows:
        by_key.setdefault(_key(r), []).append(r)
    turn_rows = [r for r in rows if r.get("kind") == "turn"]
    follow_rows = [r for r in rows if r.get("kind") == "tool-followup"]
    mirrors, genuine, mirror_turns = [], [], []
    for tr in turn_rows:
        peers = [f for f in by_key.get(_key(tr), []) if f.get("kind") == "tool-followup"]
        hit = None
        for f in peers:
            # The mirror is proven by the MEASUREMENT, not by bookkeeping: a turn row
            # and a tool-followup row of the same turn that agree exactly on ttft_s AND
            # latency_s cannot be two different requests (they are one resp object).
            if (tr.get("ttft_s") is not None
                    and tr.get("ttft_s") == f.get("ttft_s")
                    and tr.get("latency_s") == f.get("latency_s")):
                hit = f
                break
        if hit is not None:
            mirrors.append({
                "turn": tr.get("turn"), "arm": tr.get("arm"), "rep": tr.get("rep"),
                "ttft_s": tr.get("ttft_s"), "latency_s": tr.get("latency_s"),
                "content_sha256": tr.get("content_sha256"),
                "request_sha256": tr.get("request_sha256"),
                # every measured field that agrees, and the bookkeeping that differs
                "agreeing": [k for k in MEASURED
                             if tr.get(k) is not None and tr.get(k) == hit.get(k)],
                "prompt_sha256_turn": tr.get("prompt_sha256"),
                "prompt_sha256_followup": hit.get("prompt_sha256"),
            })
            mirror_turns.append([tr.get("arm"), tr.get("rep"), tr.get("turn")])
        else:
            genuine.append({"turn": tr.get("turn"), "arm": tr.get("arm"),
                            "rep": tr.get("rep"), "ttft_s": tr.get("ttft_s")})
    turn_keys = {_key(t) for t in turn_rows}
    follow_turns = {_key(f) for f in follow_rows}
    turns_with_followups = len(follow_turns)
    return {
        "rows": len(rows),
        "turn_rows": len(turn_rows),
        "tool_followup_rows": len(follow_rows),
        "turns_with_followups": turns_with_followups,
        "mirror_turn_rows": len(mirrors),
        "genuine_turn_rows": len(genuine),
        "turn_rows_with_neither_a_mirror_nor_a_measured_initial_send": len(genuine),
        "turn_rows_whose_initial_send_is_unmeasured": len(mirrors),
        "mirrors": mirrors,
        "genuine": genuine,
        "turns_never_having_a_turn_row": len(follow_turns - turn_keys),
        "is_tools_grid": bool(follow_rows),
    }


def published_figures() -> dict:
    if not os.path.exists(REPORT):
        return {}
    with open(REPORT, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when a rows file's sha256 moved during the audit")
    args = ap.parse_args(argv)

    table = grids()
    before = {}
    for gid, label, name in table:
        path = os.path.join(MEASURE, name)
        if os.path.exists(path):
            before[name] = sha256(path)

    report = published_figures()
    cells = report.get("cells") or []
    per_grid = []
    for gid, label, name in table:
        path = os.path.join(MEASURE, name)
        if not os.path.exists(path):
            continue
        a = audit_file(path)
        pub = [c for c in cells if c.get("grid_id") == gid]
        disputed = []
        for c in pub:
            if a["mirror_turn_rows"]:
                disputed.append({
                    "grid_id": gid, "label": label, "arm": c.get("arm"),
                    "n_turn": c.get("n_turn"), "n_turn_dedup": c.get("n_turn_dedup"),
                    "n_followup": c.get("n_followup"),
                    "p50_point": (c.get("p50") or {}).get("point"),
                    "p95_point": (c.get("p95") or {}).get("point"),
                    "n_dedup": c.get("n_dedup"),
                    "attribution_disputed": True,
                    "why": ("%d of this grid's %d kind=turn rows carry a tool-followup "
                            "row's measurement; the turn's own initial request has no row, "
                            "so a figure computed over these rows is the follow-up's "
                            "latency, and the last follow-up is counted twice"
                            % (a["mirror_turn_rows"], a["turn_rows"])),
                })
        per_grid.append({
            "grid_id": gid, "label": label, "rows_file": name,
            "sha256": before.get(name),
            "is_tools_grid": a["is_tools_grid"],
            "rows": a["rows"], "turn_rows": a["turn_rows"],
            "tool_followup_rows": a["tool_followup_rows"],
            "turns_with_followups": a["turns_with_followups"],
            "mirror_turn_rows": a["mirror_turn_rows"],
            "genuine_turn_rows": a["genuine_turn_rows"],
            "turns_never_having_a_turn_row": a["turns_never_having_a_turn_row"],
            "mirrors": a["mirrors"],
            "genuine": a["genuine"],
            "published_figures_affected": disputed,
        })

    after = {}
    for name in before:
        path = os.path.join(MEASURE, name)
        after[name] = sha256(path) if os.path.exists(path) else None
    moved = [n for n in before if before[n] != after[n]]

    tools_grids = [g for g in per_grid if g["is_tools_grid"]]
    disputed_cells = [d for g in per_grid for d in g["published_figures_affected"]]
    findings = {
        "schema": "consonance.row-attribution-audit/1",
        "unit": "TURN-ROW-ATTRIBUTION",
        "generated_by": "experiments/ptr-engine/tools/row_attribution_audit.py",
        "rows_files_touched": [],
        "rows_file_sha256_before": before,
        "rows_file_sha256_after": after,
        "rows_files_sha_moved": moved,
        "rows_files_sha_unchanged": not moved,
        "grids": per_grid,
        "tools_grids": [g["grid_id"] for g in tools_grids],
        "mirror_counts_per_tools_grid": {
            g["grid_id"]: {"mirror_turn_rows": g["mirror_turn_rows"],
                           "genuine_turn_rows": g["genuine_turn_rows"],
                           "turn_rows": g["turn_rows"]} for g in tools_grids},
        "attribution_disputed_published_figures": disputed_cells,
        "attribution_disputed_grids": sorted({d["grid_id"] for d in disputed_cells}),
        "statement": (
            "Historical rows were written by the pre-fix writer: per turn with k>=1 "
            "follow-ups it wrote k follow-up rows plus one kind=turn row built from the "
            "LAST follow-up response, so the turn's own initial request has no row and "
            "the last follow-up's measurement is written twice. Every grid with any "
            "mirror is therefore attribution_disputed for per-turn latency, including "
            "G8 (V5-TOOLS) and G9 (V6-TOOLS), the two published pointer-stable tools "
            "grids. Those figures were NOT recomputed or edited here."),
    }

    os.makedirs(MEASURE, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=1, sort_keys=True)
        fh.write("\n")

    print("row_attribution_audit: wrote %s" % os.path.relpath(OUT, WORKSPACE))
    for g in per_grid:
        flag = "TOOLS" if g["is_tools_grid"] else "     "
        print("  %s %-12s %-45s turn=%-3d mirrors=%-3d genuine=%-3d followups=%-3d%s"
              % (g["grid_id"], flag, g["rows_file"], g["turn_rows"],
                 g["mirror_turn_rows"], g["genuine_turn_rows"], g["tool_followup_rows"],
                 "  ATTRIBUTION_DISPUTED" if g["published_figures_affected"] else ""))
    print("  rows files sha256 unchanged: %s" % ("yes" if not moved else "NO: %s" % moved))
    if args.check and moved:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
