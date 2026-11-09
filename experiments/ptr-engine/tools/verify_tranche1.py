#!/usr/bin/env python3
"""verify_tranche1.py — the machine-checkable executor of `docs/PREREG-TRANCHE-1.md`.

WHAT THIS IS: the frozen decision procedure for RUN-A*, written as code so the second pass
of `V-TRANCHE-1` cannot choose a rule after seeing the intervals. It recomputes every
reported figure with its own code, importing `analyze_stats` for the estimator and the
McNemar test rather than copying them.

WHAT THIS IS NOT: it does not analyse real rows before they exist. When the declared
artefacts are absent it writes `{"verdict": "awaiting_rows"}` and exits 0 WITHOUT computing
a statistic; it never averages over whichever subset happens to be on disk.

  --check        compare the frozen threshold table in the doc with PREREG-TRANCHE-1.json;
                 exit 1 on drift.
  --self-test    write five synthetic cases under /tmp (never into measure/) and print
                 the verdict each receives.
  (default)      discover the tranche artefacts and, if complete, analyse them.

Offline. Zero requests. Exit codes: 0 ok/awaiting, 1 threshold drift or failed self-test,
2 usage error.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.abspath(os.path.join(HERE, "..", "longrun"))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
MANIFESTS = os.path.join(LONG, "manifests")
GATES = os.path.join(MEASURE, "GATE-LEDGER.json")
PREREG_JSON = os.path.join(MEASURE, "PREREG-TRANCHE-1.json")
PREREG_DOC = os.path.join(ROOT, "docs", "PREREG-TRANCHE-1.md")
OUT = os.path.join(MEASURE, "tranche1-verify.json")

if LONG not in sys.path:
    sys.path.insert(0, LONG)
import analyze_stats as S  # noqa: E402

#: The tranche as declared by RUN-A* / TRANCH1-DRYRUN-2 (10 cells, 48 turns each).
DECLARED_CELLS = [
    ("pointer-stable", 1), ("pointer-stable", 2), ("pointer-stable", 3),
    ("transcript-grow", 1), ("transcript-grow", 2), ("transcript-grow", 3),
    ("transcript-compact", 1), ("transcript-compact", 2),
    ("lease-reopen", 1), ("lease-reopen", 2),
]
C_ARM = "pointer-stable"
A_ARM = "transcript-grow"
TURNS_PER_CELL = 48
DECLARED_N = 12
NONE_IDS = ("cp.3.t14", "cp.5.t20", "cp.10.t42")

#: Every adjudicating threshold, mirroring `docs/PREREG-TRANCHE-1.md` §7 and
#: `measure/PREREG-TRANCHE-1.json`. `--check` refuses drift between the three.
RULES = {
    "MIN_N_USABLE": 60,        # T1  analyze_stats.py:330 / PREREG-ARM-RUN.md:36
    "TAIL_MIN": 3,             # T2  analyze_stats.py:111
    "MIN_N": 20,               # T3  analyze_stats.py:112
    "LEVEL": 0.95,             # T4  analyze_stats.py:110
    "RESAMPLES": 10000,        # T5  analyze_stats.py:113
    "SEED": 20261020,          # T6  analyze_stats.py:114
    "DIRECTION": "C_lower",    # T7  PREREG-ARM-RUN.md:38-41
    "DIRECTION_STRICT_DISJOINT": True,  # T7  PREREG-ARM-RUN.md:38-41
    "H2_INCLUSIVE": 0.95,      # T8  PREREG-ARM-RUN.md:69
    "H2_UNCACHED": 1.00,       # T9  PREREG-ARM-RUN.md:70
    "H2_REQUIRE_BOTH": True,   # T8-T9 neither limb is picked
    "H3_MAX_LOSS": 2,          # T10 PREREG-ARM-RUN.md:99
    "H3_MIN_DECIDABLE": 8,     # T13 PREREG-ARM-RUN.md:113
    "MCNEMAR_FLOOR": 6,        # T14 PREREG-ARM-RUN.md:107 / analyze_stats.py:430
    "MCNEMAR_ALPHA": 0.05,     # T15 PREREG-ARM-RUN.md:107
    "TVS_CENSOR_AS_ZERO": False,       # docs/TVS.md §censoring
    "TURN_MISSING_COUNTS_AS_FAIL": False,  # PARM-1: missing leaves denominator
}


def _finite(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


# --- H1 ---------------------------------------------------------------------
def h1_admissible(n, q, rules):
    """The frozen refusal floor: n >= 60 AND n*(1-q) >= 3 (rules override only in tests)."""
    if n < int(rules["MIN_N"]):
        return False, "insufficient_n_absolute"
    if n < int(rules["MIN_N_USABLE"]):
        return False, "insufficient_n_floor"
    if n * (1.0 - q) < float(rules["TAIL_MIN"]):
        return False, "insufficient_tail"
    return True, "admissible"


def h1_estimate(values, rules, q=0.95):
    vals = [v for v in (_finite(x) for x in values) if v is not None]
    n = len(vals)
    ok, reason = h1_admissible(n, q, rules)
    if not ok:
        return {"admissible": False, "reason": reason, "n": n,
                "floor": int(rules["MIN_N_USABLE"]), "tail_min": int(rules["TAIL_MIN"]),
                "refusal": ("n=%d refused for p%.0f: need n >= %d and n*(1-q) >= %d "
                            "(n*(1-q)=%.2f)" % (n, q * 100, int(rules["MIN_N_USABLE"]),
                                                int(rules["TAIL_MIN"]), n * (1.0 - q)))}
    try:
        point, lo, hi, used = S.quantile_ci(
            vals, q, resamples=int(rules["RESAMPLES"]), seed=int(rules["SEED"]))
    except S.InsufficientSamples as exc:
        return {"admissible": False, "reason": "estimator_refused", "n": n,
                "refusal": str(exc)}
    return {"admissible": True, "reason": "admissible", "n": used,
            "point": point, "lo": lo, "hi": hi}


def h1_compare(c_est, a_est, rules):
    if not c_est.get("admissible") or not a_est.get("admissible"):
        return {"verdict": "refused",
                "why": "at least one arm is below the frozen refusal floor"}
    strict = bool(rules["DIRECTION_STRICT_DISJOINT"])
    c_lower = rules.get("DIRECTION", "C_lower") == "C_lower"
    if strict and c_est["hi"] < a_est["lo"]:
        verdict = "separated_lower" if c_lower else "separated_higher"
    elif strict and a_est["hi"] < c_est["lo"]:
        verdict = "separated_higher" if c_lower else "separated_lower"
    elif strict:
        verdict = "overlap"
    else:  # a reverted rule: point comparison -- exists only so a test can show this is red
        low = c_est["point"] < a_est["point"]
        verdict = ("separated_lower" if low else "separated_higher") if c_lower else \
                  ("separated_higher" if low else "separated_lower")
    return {"verdict": verdict,
            "rule": ("C hi < A lo (strict)" if strict else "point comparison (REVERTED)")}


# --- H2 ---------------------------------------------------------------------
def _dedupe_key(row):
    return (row.get("arm"), row.get("rep"),
            row.get("turn_index", row.get("turn")),
            row.get("ts"), row.get("content_sha256"))


def h2_tokens(rows, selected_keys, rules):
    """Mean prompt tokens per completed turn, cache-inclusive and uncached (PARM-1 H2)."""
    seen = set()
    inc = unc = 0.0
    n = excluded = dup = 0
    for row in rows:
        key = (row.get("arm"), row.get("rep"),
               row.get("turn_index", row.get("turn")))
        if key not in selected_keys:
            continue
        dk = _dedupe_key(row)
        if dk in seen:
            dup += 1
            continue
        seen.add(dk)
        pt = _finite(row.get("prompt_tokens"))
        if pt is None:
            excluded += 1
            continue
        cached = _finite(row.get("cached_tokens")) or 0.0
        inc += pt
        unc += max(0.0, pt - cached)
        n += 1
    return {"n": n, "excluded_null_token_rows": excluded, "duplicate_rows_skipped": dup,
            "mean_prompt_inclusive": (inc / n) if n else None,
            "mean_prompt_uncached": (unc / n) if n else None}


def h2_compare(rows, selected_keys, rules):
    c = h2_tokens([r for r in rows if r.get("arm") == C_ARM], selected_keys, rules)
    a = h2_tokens([r for r in rows if r.get("arm") == A_ARM], selected_keys, rules)
    if not c["n"] or not a["n"]:
        return {"verdict": "refused", "why": "an arm has no completed billed turn", "C": c, "A": a}
    r_inc = c["mean_prompt_inclusive"] / a["mean_prompt_inclusive"]
    r_unc = c["mean_prompt_uncached"] / a["mean_prompt_uncached"]
    pass_inc = r_inc <= float(rules["H2_INCLUSIVE"])
    pass_unc = r_unc < float(rules["H2_UNCACHED"])
    if pass_inc and pass_unc:
        verdict = "h2_pass"
    elif (pass_inc or pass_unc) and not rules.get("H2_REQUIRE_BOTH", True):
        verdict = "h2_pass"      # a reverted rule: one limb is enough -- red by construction
    elif pass_inc or pass_unc:
        verdict = "h2_failed_split"
    else:
        verdict = "h2_failed"
    return {"verdict": verdict, "C": c, "A": a,
            "ratio_inclusive": r_inc, "ratio_uncached": r_unc,
            "pass_inclusive": pass_inc, "pass_uncached": pass_unc,
            "rule": "both limbs must pass; neither limb is picked"}


# --- H3 ---------------------------------------------------------------------
def _cells_by_arm(grade, arm):
    out = {}
    for cell in grade.get("cells") or []:
        if (cell.get("arm") or "default") != arm:
            continue
        cid = cell.get("id")
        verdict = cell.get("verdict")
        reason = cell.get("reason")
        if verdict in ("pass", "fail"):
            state = "pass" if verdict == "pass" else "fail"
        elif reason == "turn_missing":
            state = "fail"          # PARM-1: missing is a SUBSET of fail
        else:
            state = "undecidable"
        out[cid] = {"state": state, "verdict": verdict, "reason": reason,
                    "turn": cell.get("turn")}
    return out


def h3(grade, rules):
    c_cells, a_cells = _cells_by_arm(grade, C_ARM), _cells_by_arm(grade, A_ARM)
    ids = sorted(set(c_cells) | set(a_cells)) or list(NONE_IDS)
    declared = DECLARED_N if len(ids) <= DECLARED_N else len(ids)
    rows = {}
    for name, cells in ((C_ARM, c_cells), (A_ARM, a_cells)):
        acc = S.accuracy_from_grade(grade, name)
        # PREREG-ARM-RUN.md:98-99 / PARM-1: a `turn_missing` cell leaves the
        # denominator (it is printed by name). grade_v5 counts it inside `fail`, so
        # the denominator is the module's count MINUS the missing subset -- never a
        # row-derived count. The reverted rule (tests only) leaves it in.
        if not rules["TURN_MISSING_COUNTS_AS_FAIL"]:
            acc["decidable"] = max(0, acc["decidable"] - acc["missing"])
            acc["failed"] = max(0, acc["failed"] - acc["missing"])
        passes = [cid for cid, cell in cells.items() if cell["state"] == "pass"]
        substantive = [cid for cid in passes if cid not in NONE_IDS]
        missing_ids = sorted(cid for cid, cell in cells.items()
                             if (cell.get("reason") == "turn_missing"
                                 and not rules["TURN_MISSING_COUNTS_AS_FAIL"]))
        rows[name] = {"accuracy": acc, "x_of_12": len(passes),
                      "x_of_9_substantive": len(substantive),
                      "none_passes": len(passes) - len(substantive),
                      "missing_ids": missing_ids,
                      "answered_ratio": (acc["decidable"] / declared) if declared else None,
                      "contract_adherence": "pre-check column; not folded into accuracy"}
    c_pass = {cid for cid, cell in c_cells.items() if cell["state"] == "pass"}
    a_pass = {cid for cid, cell in a_cells.items() if cell["state"] == "pass"}
    loss = len(a_pass - c_pass)          # C loses a checkpoint A passes
    pairs = [(cid in c_pass, cid in a_pass) for cid in ids
             if cid in c_cells and cid in a_cells
             and c_cells[cid]["state"] in ("pass", "fail")
             and a_cells[cid]["state"] in ("pass", "fail")]
    disc = len(pairs) - sum(1 for c, a in pairs if c == a)
    mcn = {"discordant": disc, "floor": int(rules["MCNEMAR_FLOOR"]),
           "alpha": float(rules["MCNEMAR_ALPHA"]), "b": None, "c": None, "p": None,
           "licensed": False, "refusal": ""}
    if disc >= int(rules["MCNEMAR_FLOOR"]):
        try:
            b, c, p = S.mcnemar_exact(pairs)
            mcn.update({"b": b, "c": c, "p": p, "licensed": True})
        except S.RefusedTest as exc:
            mcn["refusal"] = str(exc)
            mcn.update({"b": getattr(exc, "b", None), "c": getattr(exc, "c", None),
                        "p": getattr(exc, "p", None)})
    else:
        mcn["refusal"] = ("refusing McNemar: only %d discordant pairs, below the frozen "
                          "floor of %d" % (disc, int(rules["MCNEMAR_FLOOR"])))
    veto = bool(mcn["licensed"] and mcn["p"] is not None
                and mcn["p"] < float(rules["MCNEMAR_ALPHA"]) and (mcn["b"] or 0) > (mcn["c"] or 0))
    c_dec, a_dec = rows[C_ARM]["accuracy"]["decidable"], rows[A_ARM]["accuracy"]["decidable"]
    if c_dec < int(rules["H3_MIN_DECIDABLE"]) or a_dec < int(rules["H3_MIN_DECIDABLE"]):
        verdict = "not_adjudicable"
    elif loss > int(rules["H3_MAX_LOSS"]) or veto:
        verdict = "h3_fail"
    else:
        verdict = "h3_pass"
    return {"verdict": verdict, "per_arm": rows, "checkpoint_loss": loss,
            "max_loss": int(rules["H3_MAX_LOSS"]), "mcnemar": mcn, "veto": veto,
            "rule": "loses > 2 of 12 fails; McNemar veto when licensed"}


# --- TVS --------------------------------------------------------------------
def tvs_for_arm(rows, grade, arm, rules):
    cells = sorted((c for c in (grade.get("cells") or []) if c.get("arm") == arm),
                   key=lambda c: c.get("turn") or 0)
    first_pass = next((c for c in cells if c.get("verdict") == "pass"), None)
    arm_rows = [r for r in rows if r.get("arm") == arm]
    last_turn = max((r.get("turn_index", r.get("turn")) or 0) for r in arm_rows) if arm_rows else 0
    if first_pass is None:
        if rules["TVS_CENSOR_AS_ZERO"]:
            return {"tvs": 0, "censored": False, "censored_at_turn": last_turn,
                    "censor_kind": "none"}
        return {"tvs": None, "censored": True, "censored_at_turn": last_turn,
                "censor_kind": "no_verified_checkpoint"}
    limit = first_pass.get("turn")
    seen, total, used, excluded, dup = set(), 0, 0, 0, 0
    for row in sorted(arm_rows, key=lambda r: (r.get("turn_index", r.get("turn")) or 0,
                                               r.get("ts") or "")):
        turn = row.get("turn_index", row.get("turn")) or 0
        if limit is not None and turn > limit:
            continue
        dk = _dedupe_key(row)
        if dk in seen:
            dup += 1
            continue
        seen.add(dk)
        pt, ct = _finite(row.get("prompt_tokens")), _finite(row.get("completion_tokens"))
        if pt is None or ct is None:
            excluded += 1
            continue
        total += pt + ct
        used += 1
    return {"tvs": total, "censored": False, "checkpoint_id": first_pass.get("id"),
            "through_turn": limit, "billed_rows": used,
            "excluded_null_token_rows": excluded, "duplicate_records_skipped": dup,
            "certified_by": "grade_v5"}


# --- the procedure over a population ----------------------------------------
def analyze(rows, grade, rules=None):
    rules = dict(RULES if rules is None else rules)
    selected, meta = S.turn_latency_rows(rows)
    keys = set()
    for row in selected:
        keys.add((row.get("arm"), row.get("rep"),
                  row.get("turn_index", row.get("turn"))))
    per_arm_latency = {}
    for arm in (C_ARM, A_ARM, "transcript-compact", "lease-reopen"):
        vals = [r.get("ttft_ms") for r in selected if r.get("arm") == arm]
        per_arm_latency[arm] = h1_estimate(vals, rules, 0.95)
    h1 = {"reading": "R-all (every selected turn of the arm, all reps pooled)",
          "C": C_ARM, "A": A_ARM,
          "per_arm": per_arm_latency,
          "comparison": h1_compare(per_arm_latency[C_ARM], per_arm_latency[A_ARM], rules),
          "selector_meta": meta}
    return {"schema": "consonance.tranche1-verify/1",
            "rules": rules,
            "h1": h1,
            "h2": h2_compare(rows, keys, rules),
            "h3": h3(grade, rules),
            "tvs": {arm: tvs_for_arm(rows, grade, arm, rules)
                    for arm in (C_ARM, A_ARM, "transcript-compact", "lease-reopen")}}


# --- discovery --------------------------------------------------------------
def _read_rows(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows, bad


def discover(rows_dir=MEASURE, manifest_dir=MANIFESTS, gates_path=GATES):
    files = sorted(glob.glob(os.path.join(rows_dir, "rows-runA-*.jsonl")))
    missing = []
    if not files:
        return {"complete": False, "verdict": "awaiting_rows",
                "missing": ["measure/rows-runA-*.jsonl (no tranche rows file exists)"],
                "rows_files": []}
    rows, bad, per_file = [], 0, []
    for path in files:
        got, count_bad = _read_rows(path)
        rows.extend(got)
        bad += count_bad
        per_file.append({"path": os.path.relpath(path, ROOT), "rows": len(got),
                         "unparseable_lines": count_bad})
    present = {(r.get("arm"), r.get("rep")) for r in rows}
    for arm, rep in DECLARED_CELLS:
        if (arm, rep) not in present:
            missing.append("cell %s rep %d: no rows" % (arm, rep))
    if len(files) < len(DECLARED_CELLS):
        missing.append("%d rows files for %d declared cells"
                       % (len(files), len(DECLARED_CELLS)))
    manifests, live = [], []
    for path in sorted(glob.glob(os.path.join(manifest_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        manifests.append(os.path.relpath(path, ROOT))
        if isinstance(doc, dict) and doc.get("dry_run") is False:
            live.append(doc)
    basenames = {os.path.basename(p) for p in files}
    bound = set()
    for doc in live:
        rows_path = doc.get("rows_path") or ""
        if os.path.basename(rows_path) in basenames:
            bound.add((doc.get("arm"), doc.get("rep")))
    for arm, rep in DECLARED_CELLS:
        if (arm, rep) not in bound:
            missing.append("cell %s rep %d: no live gate manifest bound to its rows file"
                           % (arm, rep))
    if not os.path.exists(gates_path):
        missing.append("measure/GATE-LEDGER.json (gate ledger absent)")
    if missing:
        return {"complete": False, "verdict": "awaiting_rows", "missing": missing,
                "rows_files": per_file, "unparseable_lines": bad,
                "manifests_seen": len(manifests)}
    return {"complete": True, "verdict": "complete", "rows": rows,
            "rows_files": per_file, "unparseable_lines": bad,
            "manifests": manifests, "gates_path": os.path.relpath(gates_path, ROOT)}


def grade_path_for(rows_files):
    """The grade document for these rows: sidecar `*.grade-v5.json` or a manifest-named one."""
    for entry in rows_files:
        stem = os.path.splitext(os.path.basename(entry["path"]))[0]
        for cand in glob.glob(os.path.join(MEASURE, stem + "*.grade-v5.json")):
            return cand
    found = sorted(glob.glob(os.path.join(MEASURE, "rows-runA-*.grade-v5.json")))
    return found[0] if found else None


# --- --check: the document and the JSON must agree --------------------------
_TABLE_ROW = re.compile(r"^\|\s*(T\d+)\s*\|(.*?)\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")


def _norm(text):
    """A table cell without emphasis: a drifted VALUE must still be caught, a backtick not."""
    return re.sub(r"[*`]", "", text or "").strip()


def parse_doc_thresholds(path=PREREG_DOC):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = _TABLE_ROW.match(line.strip())
            if not m:
                continue
            ident, _name, value, source = m.groups()
            out[ident] = {"value": value.strip(), "source": source.strip()}
    return out


def check_prereg(doc_path=PREREG_DOC, json_path=PREREG_JSON):
    with open(json_path, encoding="utf-8") as fh:
        record = json.load(fh)
    with open(doc_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    doc = parse_doc_thresholds(doc_path)
    drift = []
    for entry in record.get("thresholds") or []:
        ident = entry["id"]
        got = doc.get(ident)
        if got is None:
            drift.append("%s: missing from the document table" % ident)
            continue
        if _norm(got["value"]) != _norm(entry["value_doc"]):
            drift.append("%s: value %r in doc vs %r in json"
                         % (ident, got["value"], entry["value_doc"]))
        for src in entry.get("sources") or []:
            if src not in got["source"]:
                drift.append("%s: source %r absent from doc row %r" % (ident, src, got["source"]))
    for ident in doc:
        if ident not in {e["id"] for e in record.get("thresholds") or []}:
            drift.append("%s: in the document table but not in the JSON" % ident)
    return {"ok": not drift, "drift": drift, "document_sha256": digest,
            "recorded_sha256": record.get("document", {}).get("sha256"),
            "sha_matches": digest == record.get("document", {}).get("sha256"),
            "thresholds": len(doc)}


# --- self-test --------------------------------------------------------------
def _rows(arm, reps, ttft, n_turns=48, prompt=1000, cached=0, pass_at=None):
    out = []
    for rep in range(1, reps + 1):
        for turn in range(1, n_turns + 1):
            row = {"kind": "turn-initial", "arm": arm, "rep": rep, "turn": turn,
                   "ttft_ms": ttft(turn, rep), "prompt_tokens": prompt,
                   "cached_tokens": cached, "completion_tokens": 10,
                   "ts": "2026-10-26T18:00:%02d.000Z" % (turn % 60),
                   "content_sha256": "s-%s-%d-%d" % (arm, rep, turn)}
            out.append(row)
    return out


def synthetic_cases(tmpdir=None):
    base = tmpdir or tempfile.mkdtemp(prefix="tranche1-selftest-")
    ids = ["cp.0.t06", "cp.1.t08", "cp.2.t12", "cp.3.t14", "cp.4.t18", "cp.5.t20",
           "cp.6.t24", "cp.7.t26", "cp.8.t32", "cp.9.t36", "cp.10.t42", "cp.11.t46"]
    cases = {}

    good_c = _rows(C_ARM, 3, lambda t, r: 100.0 + t)
    good_a = _rows(A_ARM, 3, lambda t, r: 400.0 + t)
    cases["disjoint"] = {"rows": good_c + good_a, "grade": {"cells": []},
                         "expect": {"h1": "separated_lower"}}
    overlap_a = _rows(A_ARM, 3, lambda t, r: 100.0 + t)  # same law: intervals overlap
    cases["overlap"] = {"rows": good_c + overlap_a, "grade": {"cells": []},
                        "expect": {"h1": "overlap"}}
    short_c = _rows(C_ARM, 1, lambda t, r: 100.0 + t)   # n = 48 < 60
    cases["below_floor"] = {"rows": short_c + good_a, "grade": {"cells": []},
                            "expect": {"h1": "refused", "reason": "insufficient_n_floor"}}
    grade_censored = {"cells": [{"arm": C_ARM, "id": ids[0], "turn": 6, "verdict": "fail"},
                                {"arm": C_ARM, "id": ids[2], "turn": 12, "verdict": "fail"}]}
    cases["censored_tvs"] = {
        "rows": _rows(C_ARM, 1, lambda t, r: 100.0 + t) + _rows(A_ARM, 1, lambda t, r: 400.0 + t),
        "grade": grade_censored, "expect": {"tvs_censored": True}}
    turn_missing = {"cells": [
        {"arm": C_ARM, "id": ids[0], "turn": 6, "verdict": "fail", "reason": "turn_missing"},
        {"arm": C_ARM, "id": ids[1], "turn": 8, "verdict": "pass"},
        {"arm": A_ARM, "id": ids[0], "turn": 6, "verdict": "pass"},
        {"arm": A_ARM, "id": ids[1], "turn": 8, "verdict": "pass"},
    ]}
    cases["turn_missing"] = {
        "rows": _rows(C_ARM, 1, lambda t, r: 100.0 + t) + _rows(A_ARM, 1, lambda t, r: 400.0 + t),
        "grade": turn_missing,
        "expect": {"missing_id": ids[0], "h3": "not_adjudicable"}}
    # H2 split: inclusive passes (C<=0.95*A), uncached fails (C cached less -> uncached larger)
    cases["h2_split"] = {
        "rows": (_rows(C_ARM, 3, lambda t, r: 100.0 + t, prompt=900, cached=0)
                 + _rows(A_ARM, 3, lambda t, r: 400.0 + t, prompt=1000, cached=950)),
        "grade": {"cells": []}, "expect": {"h2": "h2_failed_split"}}
    # McNemar: b=0, c=6? pairs (C,A): b=C-wrong/A-right => b=7, c=0 -> C worse, p=0.0156
    mcn_cells = []
    for i, cid in enumerate(ids):
        mcn_cells.append({"arm": C_ARM, "id": cid, "turn": 6 + i, "verdict": "fail"})
        mcn_cells.append({"arm": A_ARM, "id": cid, "turn": 6 + i,
                          "verdict": "fail" if i < 5 else "pass"})
    cases["mcnemar"] = {
        "rows": _rows(C_ARM, 1, lambda t, r: 100.0 + t) + _rows(A_ARM, 1, lambda t, r: 400.0 + t),
        "grade": {"cells": mcn_cells},
        "expect": {"mcnemar_b": 7, "mcnemar_licensed": True, "h3": "h3_fail"}}
    return base, cases


def run_self_test(tmpdir=None):
    base, cases = synthetic_cases(tmpdir)
    results = {}
    for name, case in cases.items():
        report = analyze(case["rows"], case["grade"])
        got = {"h1": report["h1"]["comparison"]["verdict"],
               "h1_reason": report["h1"]["per_arm"][C_ARM].get("reason"),
               "reason": report["h1"]["per_arm"][C_ARM].get("reason"),
               "h2": report["h2"]["verdict"],
               "h3": report["h3"]["verdict"],
               "tvs_censored": report["tvs"][C_ARM]["censored"],
               "missing_id": (report["h3"]["per_arm"][C_ARM]["missing_ids"] or [None])[0],
               "mcnemar_b": report["h3"]["mcnemar"]["b"],
               "mcnemar_licensed": report["h3"]["mcnemar"]["licensed"]}
        expect = case["expect"]
        ok = all(got.get(k) == v for k, v in expect.items())
        results[name] = {"ok": ok, "expected": expect, "got": got}
    return {"tmpdir": base, "cases": results,
            "all_ok": all(r["ok"] for r in results.values())}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows-dir", default=MEASURE)
    ap.add_argument("--manifest-dir", default=MANIFESTS)
    ap.add_argument("--gates", default=GATES)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true", help="threshold-table drift check")
    ap.add_argument("--self-test", action="store_true", help="run synthetic cases under /tmp")
    args = ap.parse_args(argv)
    if args.check:
        result = check_prereg()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if args.self_test:
        result = run_self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["all_ok"] else 1
    found = discover(args.rows_dir, args.manifest_dir, args.gates)
    if not found["complete"]:
        payload = {"schema": "consonance.tranche1-verify/1", "verdict": "awaiting_rows",
                   "analysis": None, "missing": found["missing"],
                   "rows_files": found.get("rows_files", []),
                   "rules": RULES,
                   "note": ("refusing to analyse: the declared tranche artefacts are absent. "
                            "No statistic was computed over a partial grid.")}
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
        print(json.dumps({"verdict": "awaiting_rows", "out": os.path.relpath(args.out, ROOT),
                          "missing": found["missing"]}, indent=2))
        return 0
    grade_path = grade_path_for(found["rows_files"])
    if not grade_path:
        payload = {"schema": "consonance.tranche1-verify/1", "verdict": "awaiting_rows",
                   "analysis": None, "missing": ["grade-v5 document for the tranche rows"],
                   "rows_files": found["rows_files"], "rules": RULES}
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
        print(json.dumps({"verdict": "awaiting_rows", "missing": payload["missing"]}, indent=2))
        return 0
    with open(grade_path, encoding="utf-8") as fh:
        grade = json.load(fh)
    report = analyze(found["rows"], grade)
    payload = {"schema": "consonance.tranche1-verify/1", "verdict": "analysed",
               "prereg_sha256": hashlib.sha256(open(PREREG_DOC, "rb").read()).hexdigest(),
               "rows_files": found["rows_files"], "grade": os.path.relpath(grade_path, ROOT),
               "gates": found["gates_path"], "analysis": report}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"verdict": "analysed", "out": os.path.relpath(args.out, ROOT),
                      "h1": report["h1"]["comparison"]["verdict"],
                      "h2": report["h2"]["verdict"],
                      "h3": report["h3"]["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
