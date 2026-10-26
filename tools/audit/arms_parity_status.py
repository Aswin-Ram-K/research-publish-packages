#!/usr/bin/env python3
"""arms_parity_status.py — guard that the ARMS-PARITY verdict stays withdrawn.

WHY THIS EXISTS
---------------
Unit ``ARMS-PARITY`` (2026-10-24 01:57) concluded that ``cells/PROMPT-O1``'s arm-R
``cached_tokens`` were a ``(prompt_tokens, cached_tokens)`` dedupe artefact, that its
mean ``583.14`` was therefore corrupt, and that the publishable figure was
``A - R = +133.3`` ("A costlier, pointer layout HELPS").  Three later units falsified it:

  * ``GROUND-TRUTH-R``      fresh R re-measurement within -0.08 % of the published value;
  * ``GROUND-TRUTH-PROMPT`` fresh R = **589.2029** uncached/turn (n=69, 0 non-200)
                            vs restored 583.14 (+1.0 %) and repaired 391.48 (+50.5 %);
  * ``CACHED-AUDIT``        the "duplicate cached_tokens" signature is not discriminating
                            (fires 37/69 on the fresh ground truth), so the artefact
                            premise is unavailable, and the only physically impossible
                            corpus is the repair itself (40 cached values off the
                            64-token grid).

``RESTORE-O1`` then restored ``rows.jsonl`` and withdrew ``+137.82``, but the ARMS-PARITY
record still carried its verdict and its *inverted* prescription ("-53.8 must be
withdrawn … +133.3 is publishable").  ``CACHED-AUDIT``'s hint named the gap: *mark it
withdrawn*.  This module is the mechanical form of that mark — a reader (or the next
unit) that resurrects the +133.3 premise is failed by ``--check`` rather than argued
with.

THE INVERSION, STATED ONCE
--------------------------
The standing figure is **A - R = -53.8451, 95 % CI [-96.6197, -10.4085]** — *A cheaper*.
ARMS-PARITY withdrew the correct number and promoted the corrupt one.  A withdrawal that
does not say that is how the error gets made twice.

WHAT IS CHECKED
---------------
  C1 record   state/logs/arms-parity.json carries status WITHDRAWN, the withdrawal
              record exists, and it names the standing figure.
  C2 corpus   recomputed from cells/PROMPT-O1/rows.jsonl: R = 583.1408,
              A - R = -53.8451 (tolerance 1e-4).  Re-applying the falsified repair
              flips this to +137.8 and fails here.
  C3 basis    rows.jsonl sha256 == the restored pre-correction bytes, and rows.jsonl
              is byte-identical to rows.pre-correction.jsonl.
  C4 artefact the kept `rows.repaired-DO-NOT-USE.jsonl` is the off-grid corpus
              (sha256 58c95f…, 40 cached values off the 64-token grid): the falsified
              figure is reproducible only from a corpus the server cannot have emitted.
  C5 surfaces no *claim-bearing* published surface states a falsified figure as live.
              A line quoting one is allowed only when the same line marks it withdrawn
              or falsified.

Read-only everywhere; zero live requests.  Exit 1 if any check has a problem.

USAGE
  python3 tools/audit/arms_parity_status.py [--json] [--root DIR] [--cells DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG_REL = os.path.join("state", "logs", "arms-parity.json")
WITHDRAW_REL = os.path.join("state", "logs", "arms-parity-withdraw.json")
CELL_REL = os.path.join("experiments", "context-cache", "cells")

GRID = 64

# The restored basis (verified independently by RESTORE-O1 and re-derived by this unit).
BASIS_SHA = "dc0774d8ef7dc4dcaa6b295460bc9a73bf676f21db93b40d6ba3b18542101eff"
BASIS_BYTES = 238087
REPAIRED_SHA = "58c95fae92f08de63ad4ad1ace59228e20edf02ba7d3849cbe9eded121c9269c"

STANDING = {
    "A_minus_R": -53.8451,
    "R_mean": 583.1408,
    "A_mean": 529.2958,
    "ci95": [-96.6197, -10.4085],
}
TOL = 1e-3

# Figures ARMS-PARITY promoted, or that RESTORE-O1 withdrew.  None may stand.
FALSIFIED_PATTERNS = (
    r"\+\s*133\.3\b",
    r"\+\s*138\.(?:50|5|68)\b",
    r"\+\s*137\.8(?:2)?\b",
    r"pointer layout helps",
    r"bookkeeping artifact",
)
# A claim-bearing line is exempt only when it marks the figure dead on that line.
EXEMPT = re.compile(r"withdraw|falsif|not publishable|void|supersed|retract", re.I)
FALSIFIED = re.compile("|".join(FALSIFIED_PATTERNS), re.I)

CLAIM_SURFACES = (
    os.path.join("papers", "context-cache"),
    os.path.join("submission-kit"),
    os.path.join("docs"),
)
CLAIM_ROOT_FILES = ("MANUSCRIPT.md", "CLAIMS.md")


# --------------------------------------------------------------------------- helpers
def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def sha256_file(path: str) -> str:
    return hashlib.sha256(_read(path)).hexdigest()


def load_rows(path: str) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def arm_means(rows: list) -> dict:
    """Mean numeric ``uncached_tokens`` per arm; non-numeric (unavailable) rows skipped."""
    acc: dict = {}
    for row in rows:
        u = row.get("uncached_tokens")
        if isinstance(u, bool) or not isinstance(u, (int, float)):
            continue
        acc.setdefault(row.get("arm"), []).append(float(u))
    return {arm: (sum(v) / len(v), len(v)) for arm, v in acc.items()}


def offgrid_cached(rows: list, grid: int = GRID) -> list:
    bad = []
    for row in rows:
        c = row.get("cached_tokens")
        if isinstance(c, bool) or not isinstance(c, int):
            continue
        if c % grid:
            bad.append((row.get("arm"), row.get("turn"), c))
    return bad


# ---------------------------------------------------------------------------- checks
def check_record(root: str) -> list:
    problems = []
    log_path = os.path.join(root, LOG_REL)
    rec_path = os.path.join(root, WITHDRAW_REL)
    try:
        log = json.loads(_read(log_path).decode("utf-8"))
    except FileNotFoundError:
        return [f"{LOG_REL}: missing — the ARMS-PARITY verdict has no record to withdraw"]
    except json.JSONDecodeError as exc:
        return [f"{LOG_REL}: unparseable ({exc})"]

    status = str(log.get("status", "")).upper()
    if status != "WITHDRAWN":
        problems.append(
            f"{LOG_REL}: status={status or '<absent>'!r}, expected 'WITHDRAWN' — "
            "ARMS-PARITY's verdict (+133.3 publishable, -53.8 withdrawn) is falsified "
            "by GROUND-TRUTH-PROMPT 589.2029 and must stay marked dead"
        )
    wd = log.get("withdrawn") or {}
    if str(wd.get("by_unit", "")) != "ARMS-PARITY-WITHDRAW":
        problems.append(f"{LOG_REL}: withdrawn.by_unit != 'ARMS-PARITY-WITHDRAW'")

    try:
        rec = json.loads(_read(rec_path).decode("utf-8"))
    except FileNotFoundError:
        return problems + [f"{WITHDRAW_REL}: missing withdrawal record"]
    except json.JSONDecodeError as exc:
        return problems + [f"{WITHDRAW_REL}: unparseable ({exc})"]

    if str(rec.get("status", "")).upper() != "WITHDRAWN":
        problems.append(f"{WITHDRAW_REL}: status must be WITHDRAWN")
    sup = rec.get("superseded_by") or {}
    fig = sup.get("standing_figure") or {}
    try:
        got = float(fig.get("A_minus_R"))
    except (TypeError, ValueError):
        problems.append(f"{WITHDRAW_REL}: superseded_by.standing_figure.A_minus_R missing")
    else:
        if abs(got - STANDING["A_minus_R"]) > TOL:
            problems.append(
                f"{WITHDRAW_REL}: standing A_minus_R={got} but the restored corpus "
                f"gives {STANDING['A_minus_R']}"
            )
    if not sup.get("corpus", {}).get("sha256"):
        problems.append(f"{WITHDRAW_REL}: superseded_by.corpus.sha256 missing")
    return problems


def check_corpus(cells_dir: str) -> list:
    problems = []
    # accept either the cells root or the cell itself, so a mis-pointed CLI fails on
    # the data rather than on a path that looks "missing"
    if os.path.basename(os.path.normpath(cells_dir)) == "PROMPT-O1":
        o1 = cells_dir
    else:
        o1 = os.path.join(cells_dir, "PROMPT-O1")
    rows_path = os.path.join(o1, "rows.jsonl")
    pre_path = os.path.join(o1, "rows.pre-correction.jsonl")
    rep_path = os.path.join(o1, "rows.repaired-DO-NOT-USE.jsonl")

    if not os.path.exists(rows_path):
        return [f"{rows_path}: missing"]

    # C2 — the standing figure, recomputed.
    rows = load_rows(rows_path)
    means = arm_means(rows)
    if "R" not in means or "A" not in means:
        problems.append(f"{rows_path}: arms A and R must both carry numeric uncached_tokens")
    else:
        r_mean, r_n = means["R"]
        a_mean, _ = means["A"]
        a_minus_r = a_mean - r_mean
        if abs(r_mean - STANDING["R_mean"]) > TOL:
            problems.append(
                f"{rows_path}: R mean {r_mean:.4f} != {STANDING['R_mean']} — the corpus "
                "is not the restored pre-correction bytes"
            )
        if abs(a_minus_r - STANDING["A_minus_R"]) > TOL:
            direction = "positive (ARMS-PARITY's falsified sign)" if a_minus_r > 0 else "wrong magnitude"
            problems.append(
                f"{rows_path}: A - R = {a_minus_r:+.4f} != {STANDING['A_minus_R']} [{direction}]"
            )
        off = offgrid_cached(rows)
        if off:
            problems.append(
                f"{rows_path}: {len(off)} cached_tokens off the {GRID}-token grid "
                f"(e.g. {off[0]}) — the row set cannot be server-emitted"
            )

    # C3 — basis identity.
    if os.path.exists(pre_path):
        if sha256_file(rows_path) != sha256_file(pre_path):
            problems.append(
                f"{rows_path}: sha256 differs from rows.pre-correction.jsonl — the "
                "restore was disturbed"
            )
        if sha256_file(rows_path) != BASIS_SHA:
            problems.append(f"{rows_path}: sha256 != restored {BASIS_SHA[:16]}…")
        if os.path.getsize(rows_path) != BASIS_BYTES:
            problems.append(f"{rows_path}: {os.path.getsize(rows_path)} B != {BASIS_BYTES} B")

    # C4 — the kept artefact is the impossible corpus, and only it yields +137.8.
    if os.path.exists(rep_path):
        if sha256_file(rep_path) != REPAIRED_SHA:
            problems.append(f"{rep_path}: sha256 != {REPAIRED_SHA[:16]}… (evidence kept for the record)")
        rep_off = offgrid_cached(load_rows(rep_path))
        if len(rep_off) != 40:
            problems.append(f"{rep_path}: expected 40 off-grid cached values, found {len(rep_off)}")
    else:
        problems.append(f"{rep_path}: missing — the falsified corpus must stay visible")
    return problems


def claim_surfaces(root: str) -> list:
    out = []
    for rel in CLAIM_SURFACES:
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in files:
                if name.endswith(".md"):
                    out.append(os.path.join(dirpath, name))
    for name in CLAIM_ROOT_FILES:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            out.append(path)
    return sorted(out)


def check_surfaces(paths) -> list:
    problems = []
    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                if FALSIFIED.search(line) and not EXEMPT.search(line):
                    problems.append(
                        f"{path}:{lineno}: falsified figure stated as live: {line.strip()[:110]}"
                    )
    return problems


def audit(root: str = ROOT, cells_dir: str | None = None, surfaces=None) -> dict:
    cells = cells_dir or os.path.join(root, CELL_REL)
    surf = claim_surfaces(root) if surfaces is None else list(surfaces)
    checks = {
        "C1_record": check_record(root),
        "C2_corpus": check_corpus(cells),
        "C5_surfaces": check_surfaces(surf),
    }
    problems = [p for v in checks.values() for p in v]
    return {
        "unit": "ARMS-PARITY-WITHDRAW",
        "ok": not problems,
        "checks": checks,
        "problems": problems,
        "surfaces_scanned": len(surf),
        "standing": STANDING,
        "live_requests": 0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--cells", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    report = audit(args.root, args.cells)
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        verdict = "PASS" if report["ok"] else "FAIL"
        print(f"ARMS-PARITY WITHDRAWAL GUARD {verdict}  surfaces={report['surfaces_scanned']} "
              f"standing A-R={STANDING['A_minus_R']}")
        for name, problems in report["checks"].items():
            print(f"  {name}: {'ok' if not problems else str(len(problems)) + ' problem(s)'}")
        for p in report["problems"]:
            print(f"  ! {p}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
