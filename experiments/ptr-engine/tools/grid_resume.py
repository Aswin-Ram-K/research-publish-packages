#!/usr/bin/env python3
"""GRID-RESUME-TOOL: make a killed RUN-A-STAR-2 session resume from evidence.

One read-only command (the default action) prints, for the declared grid of
RUN-A-STAR-2 -- 10 era B cells (pointer-stable x3, transcript-grow x3,
transcript-compact x2, lease-reopen x2) plus the 4 canary arms -- the state of
every cell as it exists on disk right now:

    done            turns on disk == 48, file is era B, and no stamp says
                    usable_for: []   (never re-run)
    partial         1..47 turns: a killed invocation.  RESUMABLE ONLY BY A
                    FRESH CELL, never by appending to the file.
    abandoned       a turn row carries stop_reason runaway_turn/runaway_abort,
                    or a journal line names the cell/rows file ABANDONED
    era_a_excluded  the file is era A, proven by its own quoted stamp/fields
                    (tools_mode: "off", corroborated by usable_for: []), never
                    by filename
    absent          the cell has no rows file in measure/

Plus `next_cell`, `canary_next`, and the ledger delta against the v2 baseline
(measure/LEDGER-GRID-BASELINE-2.json, sha 3b79f476...) computed by delegating to
tools/ledger_delta.py -- this tool never re-implements the arithmetic -- and
whether the next cell's request price fits in remaining_now.

WHY the evidence rules are what they are
----------------------------------------
Era A and era B were run on the SAME fixture: the current LR-01.v8 sha256 is
0804b51575cc..., which is also the era A rows' fixture_sha256.  So the fixture
sha CANNOT separate the eras, and neither can the filename (both attempt files
are `rows-cell-pointer-stable-*.jsonl`).  The era A rows separate themselves:
all 27 carry `tools_mode: "off"` (era B is tools-on), and every stamping
document (measure/ANALYSIS-PATH.json era_a_rows, measure/GRID-CELL-SANITY.json)
marks that file `usable_for: []`.  Both limbs are quoted in `evidence`.

Read-only by construction: files are opened with mode "r" only; the only
subprocess is ledger_delta.py, which is itself read-only; nothing is written to
any rows-*.jsonl, grade-*.json, or manifest.

Usage (offline, zero requests):
    python3 experiments/ptr-engine/tools/grid_resume.py
    python3 experiments/ptr-engine/tools/grid_resume.py --json
    python3 experiments/ptr-engine/tools/grid_resume.py --no-ledger   # tests
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MEASURE = os.path.join(ROOT, "experiments/ptr-engine/measure")
JOURNALS = os.path.join(ROOT, "orchestration/journals")
MANIFESTS = os.path.join(ROOT, "experiments/ptr-engine/longrun/manifests")
LEDGER_DELTA = os.path.join(HERE, "ledger_delta.py")
GRID_PARAMS = os.path.join(MEASURE, "GRID-PARAMS.json")
SANITY = os.path.join(MEASURE, "GRID-CELL-SANITY.json")
ANALYSIS_PATH = os.path.join(MEASURE, "ANALYSIS-PATH.json")

DONE_TURNS = 48
CANARY_TURNS = 12
RUNAWAY_STOPS = ("runaway_turn", "runaway_abort")
CELL_ORDER = ([("pointer-stable", i) for i in (1, 2, 3)] +
              [("transcript-grow", i) for i in (1, 2, 3)] +
              [("transcript-compact", i) for i in (1, 2)] +
              [("lease-reopen", i) for i in (1, 2)])
CANARY_ARMS = ["pointer-stable", "transcript-grow", "transcript-compact", "lease-reopen"]
DEFAULT_CELL_PRICE = 108  # GRID-PARAMS.json per_cell_budget fallback; only a fallback


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:          # read-only
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:   # read-only
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_jsonl(path):
    """-> (rows, notes).  A torn trailing line is skipped and noted, never fatal."""
    rows, notes = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:   # read-only
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                notes.append("unparseable line %d skipped" % lineno)
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows, notes


def turn_rows(rows):
    return [r for r in rows if r.get("kind", "turn") == "turn"]


def stamp_index(root=ROOT, measure=MEASURE):
    """basename -> list of {source, usable_for, reason} from every stamping file.

    Sources: measure/GRID-CELL-SANITY.json cells[], measure/ANALYSIS-PATH.json
    era_a_rows, and longrun/manifests/*.json that name a rows file.  Only files
    that actually stamp a rows path are indexed; filename inference is never used.
    """
    idx = {}

    def add(path, source, cell):
        usable = cell.get("usable_for", cell.get("usable"))
        if usable is None:
            return
        idx.setdefault(os.path.basename(path), []).append(
            {"source": source, "usable_for": usable,
             "reason": cell.get("usable_for_reason") or cell.get("reason")})

    sanity = read_json(os.path.join(measure, "GRID-CELL-SANITY.json"))
    if isinstance(sanity, dict):
        for cell in sanity.get("cells") or []:
            if isinstance(cell, dict) and cell.get("path"):
                add(cell["path"], "measure/GRID-CELL-SANITY.json", cell)
    apath = read_json(os.path.join(measure, "ANALYSIS-PATH.json"))
    if isinstance(apath, dict):
        era = (apath.get("inputs") or {}).get("era_a_rows") or apath.get("era_a_rows")
        if isinstance(era, dict) and era.get("path"):
            add(era["path"], "measure/ANALYSIS-PATH.json", era)
    mdir = os.path.join(root, "experiments/ptr-engine/longrun/manifests")
    if os.path.isdir(mdir):
        for name in sorted(os.listdir(mdir)):
            if not name.endswith(".json"):
                continue
            doc = read_json(os.path.join(mdir, name))
            if not isinstance(doc, dict) or "usable_for" not in doc:
                continue
            for key in ("rows_path", "rows_file", "rows", "path"):
                val = doc.get(key)
                if isinstance(val, str) and val.endswith(".jsonl"):
                    add(val, "longrun/manifests/" + name, doc)
    return idx


def journal_abandoned(root=ROOT):
    """basename-or-arm -> [journal line text] for lines that name a cell ABANDONED."""
    hits = {}
    jdir = os.path.join(root, "orchestration/journals")
    if not os.path.isdir(jdir):
        return hits
    for name in sorted(os.listdir(jdir)):
        if not name.endswith(".jsonl"):
            continue
        path = os.path.join(jdir, name)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    up = line.upper()
                    if "ABANDONED" not in up:
                        continue
                    for token in _journal_tokens(line):
                        hits.setdefault(token, []).append(
                            "%s: %s" % (name, line.strip()[:240]))
        except OSError:
            continue
    return hits


def _journal_tokens(line):
    toks = []
    try:
        obj = json.loads(line)
    except ValueError:
        obj = None
    if isinstance(obj, dict):
        for key in ("rows", "rows_file", "rows_path", "file", "cell", "run_id"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                toks.append(os.path.basename(val))
        arm, rep = obj.get("arm"), obj.get("rep")
        if isinstance(arm, str) and rep is not None:
            toks.append("cell:%s-r%s" % (arm, rep))
    return toks


def classify_file(path, stamps=None, abandoned=None, done_turns=DONE_TURNS,
                  fixture_sha=None):
    """Classify ONE rows file.  Pure: reads `path`, returns a dict with evidence."""
    stamps = stamps or {}
    abandoned = abandoned or {}
    rows, notes = read_jsonl(path)
    trows = turn_rows(rows)
    n = len(trows)
    base = os.path.basename(path)
    evidence = []
    tools_modes = sorted({str(r.get("tools_mode")) for r in trows if "tools_mode" in r})
    fixture_shas = sorted({str(r.get("fixture_sha256")) for r in trows if r.get("fixture_sha256")})
    stamp_list = stamps.get(base, [])
    usable = None
    for s in stamp_list:
        if s["usable_for"] is not None:
            usable = s["usable_for"]
            evidence.append("stamp %s usable_for=%s%s" % (
                s["source"], json.dumps(s["usable_for"]),
                (" reason=%r" % s["reason"]) if s["reason"] else ""))
    ttft = sum(1 for r in trows if r.get("ttft_ms") is not None)
    prompt_tokens = [r.get("prompt_tokens") for r in trows
                     if isinstance(r.get("prompt_tokens"), (int, float))]
    spend_tokens = int(sum(prompt_tokens)) if prompt_tokens else None
    projected = (int(done_turns * prompt_tokens[-1])
                 if prompt_tokens and prompt_tokens[-1] > 0 else None)
    runaway = [(r.get("turn"), r.get("stop_reason")) for r in trows
               if r.get("stop_reason") in RUNAWAY_STOPS]
    ab_lines = list(abandoned.get(base, []))
    if not ab_lines:
        m = _match_arm_rep(base)
        if m:
            ab_lines = list(abandoned.get("cell:%s-r%s" % m, []))
    if tools_modes:
        evidence.append("tools_mode=%s in %d/%d turn row(s)" % (
            ",".join(tools_modes), len([r for r in trows if "tools_mode" in r]), n))
    if fixture_shas:
        evidence.append("fixture_sha256=%s" % ",".join(fixture_shas))
    if runaway:
        evidence.append("stop_reason=%s at turn(s) %s" % (
            ",".join(sorted({str(s) for _, s in runaway})),
            ",".join(str(t) for t, _ in runaway)))
    for line in ab_lines:
        evidence.append("journal ABANDONED: " + line)

    # --- era A FIRST: a 27-turn era A file is not a partial era B cell --------
    era_a = [t for t in tools_modes if t == "off"]
    if era_a:
        state = "era_a_excluded"
    elif runaway or ab_lines:
        state = "abandoned"
    elif n == done_turns and usable != []:
        state = "done"
    elif n == 0:
        state = "absent"
    elif 1 <= n < done_turns:
        state = "partial"
    elif n == done_turns and usable == []:
        state = "era_a_excluded"
    else:  # > done_turns: never "done" on a count that cannot be a cell end
        state = "partial"
        evidence.append("turn count %d > %d: over a cell's declared length" % (n, done_turns))
    if n == done_turns and usable == [] and state != "era_a_excluded":
        state = "era_a_excluded"
    reps = sorted({r.get("rep") for r in trows if isinstance(r.get("rep"), int)})
    return {
        "path": path, "file": base, "state": state, "turns": n,
        "reps": reps, "declared_turns": done_turns, "ttft_present": ttft,
        "ttft_all": n > 0 and ttft == n,
        "usable_for": usable, "tools_modes": tools_modes,
        "fixture_sha256": fixture_shas, "runaway": runaway,
        "tokens_spent": spend_tokens, "tokens_projected_48": projected,
        "evidence": evidence, "notes": notes,
        "sha256": sha256_file(path),
    }


def _match_arm_rep(basename):
    """rows-cell-<arm>-<ts>.jsonl -> (arm, rep) when the rep is in the stamp."""
    if not basename.startswith("rows-cell-") or not basename.endswith(".jsonl"):
        return None
    body = basename[len("rows-cell-"):-len(".jsonl")]
    for arm in CANARY_ARMS:
        if body.startswith(arm + "-"):
            tail = body[len(arm) + 1:]
            # reps are not in the file name; a journal may name arm+rep directly
            return (arm, None) if tail else None
    return None


def discover(measure, arm, canary=False):
    prefix = "rows-canary-%s-" % arm if canary else "rows-cell-%s-" % arm
    if not os.path.isdir(measure):
        return []
    out = []
    for name in sorted(os.listdir(measure)):
        if name.startswith(prefix) and name.endswith(".jsonl"):
            out.append(os.path.join(measure, name))
    return out


CELL_PRECEDENCE = {"done": 5, "abandoned": 4, "partial": 3, "era_a_excluded": 2, "absent": 1}


def build_report(measure=MEASURE, root=ROOT, done_turns=DONE_TURNS,
                 canary_turns=CANARY_TURNS):
    stamps = stamp_index(root, measure)
    abandoned = journal_abandoned(root)
    v8 = os.path.join(root, "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json")
    fixture_sha = sha256_file(v8) if os.path.isfile(v8) else None

    cells = []
    for arm, rep in CELL_ORDER:
        files = discover(measure, arm)
        classified = [classify_file(p, stamps, abandoned, done_turns, fixture_sha)
                      for p in files]
        # A cell owns the files whose rows declare that rep.  A rows file with
        # no rep stamp is not silently multiplied across reps.
        mine = [c for c in classified if rep in c["reps"]]
        if not classified:
            state = "absent"
        elif not mine:
            state = "absent"
        else:
            # Cell state is the strongest evidence any of its own files carries.
            state = max((c["state"] for c in mine),
                        key=lambda s: CELL_PRECEDENCE[s])
        cells.append({"cell": "%s r%d" % (arm, rep), "arm": arm, "rep": rep,
                      "state": state, "files": mine})

    canaries = []
    for arm in CANARY_ARMS:
        files = discover(measure, arm, canary=True)
        classified = [classify_file(p, stamps, abandoned, canary_turns, fixture_sha)
                      for p in files]
        state = "absent" if not classified else max(
            (c["state"] for c in classified), key=lambda s: CELL_PRECEDENCE[s])
        canaries.append({"arm": arm, "state": state, "files": classified})

    next_cell = next((c["cell"] for c in cells if c["state"] != "done"), None)
    canary_next = next((c["arm"] for c in canaries if c["state"] != "done"), None)
    if next_cell is not None:
        pending = next((c for c in cells if c["state"] != "done"), None)
        next_missing = [f["turns"] for f in pending["files"]] if pending else []
    else:
        next_missing = []
    return {"grid": "RUN-A-STAR-2", "measure_dir": measure,
            "fixture_sha256": fixture_sha, "cells": cells, "canaries": canaries,
            "next_cell": next_cell, "canary_next": canary_next,
            "done_turns": done_turns, "canary_turns": canary_turns}


def ledger_view(root=ROOT, measure=MEASURE, enabled=True):
    if not enabled:
        return {"status": "skipped"}
    delta_tool = os.path.join(root, "experiments/ptr-engine/tools/ledger_delta.py")
    if not os.path.isfile(delta_tool):
        return {"status": "unavailable", "why": "ledger_delta.py not found"}
    try:
        proc = subprocess.run([sys.executable, delta_tool], capture_output=True,
                              text=True, timeout=120, cwd=root)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unavailable", "why": repr(exc)}
    fields = {}
    for line in (proc.stdout or "").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] in (
                "spent_before", "spent_now", "delta", "remaining_now",
                "baseline_sha256", "verdict", "deficit", "requests_raw_now"):
            fields[parts[0]] = parts[1].strip()
    out = {"status": "ok" if proc.returncode == 0 else "FAILED",
           "exit_code": proc.returncode, "fields": fields}
    try:
        out["spent_now"] = int(fields["spent_now"])
        out["remaining_now"] = int(fields["remaining_now"])
        out["delta"] = int(fields["delta"])
    except (KeyError, ValueError):
        out["status"] = "unparseable"
    params = read_json(os.path.join(measure, "GRID-PARAMS.json")) or {}
    price = None
    for key in ("per_cell_budget", "price"):
        node = params.get(key)
        if isinstance(node, dict):
            for k in ("value", "per_cell", "per_cell_requests"):
                if isinstance(node.get(k), int):
                    price = node[k]
                    break
        if price is not None:
            break
    if price is None:
        price = DEFAULT_CELL_PRICE
    out["next_cell_price"] = price
    if "remaining_now" in out and isinstance(out["remaining_now"], int):
        out["next_cell_fits"] = out["remaining_now"] >= price
    return out


def render(rep, ledger):
    lines = []
    lines.append("GRID RESUME — RUN-A-STAR-2  (read-only, offline: 0 requests)")
    lines.append("measure_dir              %s" % rep["measure_dir"])
    lines.append("fixture LR-01.v8 sha256  %s" % (rep["fixture_sha256"] or "(missing)"))
    lines.append("era note                 era A and era B share this fixture sha; era is")
    lines.append("                         decided by the rows' own tools_mode/stamps, not names")
    lines.append("")
    lines.append("CELLS (declared order, %d):" % len(rep["cells"]))
    for i, cell in enumerate(rep["cells"], 1):
        lines.append(" %2d %-20s state=%-14s files=%d" % (
            i, cell["cell"], cell["state"], len(cell["files"])))
        for f in cell["files"]:
            tok = ""
            if f["tokens_spent"] is not None:
                tok = " tokens_spent=%d projected48=%s" % (
                    f["tokens_spent"], f["tokens_projected_48"])
            lines.append("      %-52s file_state=%-14s turns=%d/%d ttft=%d usable_for=%s%s" % (
                f["file"], f["state"], f["turns"], f["declared_turns"], f["ttft_present"],
                json.dumps(f["usable_for"]), tok))
            lines.append("      sha256 %s" % f["sha256"][:16])
            for ev in f["evidence"]:
                lines.append("      evidence: " + ev)
            for note in f["notes"]:
                lines.append("      note: " + note)
    lines.append("")
    lines.append("next_cell   %s" % rep["next_cell"])
    lines.append("CANARY ARMS (N=%d, 4):" % rep["canary_turns"])
    for c in rep["canaries"]:
        lines.append("  %-20s state=%s files=%d" % (
            c["arm"], c["state"], len(c["files"])))
        for f in c["files"]:
            lines.append("      %-52s turns=%d/%d ttft=%d" % (
                f["file"], f["turns"], f["declared_turns"], f["ttft_present"]))
    lines.append("canary_next %s" % rep["canary_next"])
    lines.append("")
    lines.append("LEDGER (delta vs measure/LEDGER-GRID-BASELINE-2.json):")
    if ledger.get("status") != "ok":
        lines.append("  status   %s %s" % (ledger.get("status"), ledger.get("why", "")))
    else:
        lines.append("  spent_now      %d" % ledger["spent_now"])
        lines.append("  remaining_now  %d" % ledger["remaining_now"])
        lines.append("  delta          %d" % ledger["delta"])
        lines.append("  baseline_sha   %s" % ledger["fields"].get("baseline_sha256", "?"))
        lines.append("  verdict        %s" % ledger["fields"].get("verdict", "?"))
        lines.append("  next cell price %d requests; fits=%s (remaining_now >= price)" % (
            ledger["next_cell_price"], ledger.get("next_cell_fits")))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="read-only RUN-A-STAR-2 resumption report")
    ap.add_argument("--measure-dir", default=MEASURE)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--done-turns", type=int, default=DONE_TURNS)
    ap.add_argument("--canary-turns", type=int, default=CANARY_TURNS)
    args = ap.parse_args(argv)
    rep = build_report(args.measure_dir, args.root, args.done_turns, args.canary_turns)
    led = ledger_view(args.root, args.measure_dir, enabled=not args.no_ledger)
    rep["ledger"] = led
    if args.json:
        print(json.dumps(rep, indent=1, sort_keys=True))
    else:
        print(render(rep, led))
    return 0


if __name__ == "__main__":
    sys.exit(main())
