#!/usr/bin/env python3
"""run_grid_report.py — the ONE command that turns finished grid cell files into GRID-REPORT-2.

WHAT THIS IS
------------
A consumer, not an analyser.  Given the grid's `rows-cell-*.jsonl` files and their
manifests, it emits `measure/GRID-REPORT-2.json` + `docs/GRID-REPORT-2.md` in terms
that were fixed BEFORE the data existed (docs/PREREG-TRANCHE-1.md), so a nine-hour
live run cannot end in a hand-written summary chosen after the intervals were seen.

Every statistic is imported, never re-implemented:

  experiments/ptr-engine/longrun/analyze_stats.py
      turn_latency_rows      one row per TURN (turn-initial preferred, followup dropped)
      quantile_ci            the percentile-bootstrap interval + its InsufficientSamples text
      min_n_for              n floor for a quantile (p95 -> 60)
      split_truncated        the cap-length-turn exclusion rule
      select_usable_cells    `usable_for: []` exclusion by name
      provenance_cells       the arm's load-bearing provenance cell
      accuracy_from_grade    H3 population (grade_v5 cells, never row-derived)
  experiments/ptr-engine/tools/row_provenance.py
      same_provenance        THE comparability gate (refuses unknown-vs-known)
  experiments/ptr-engine/tools/verify_tranche1.py
      h1_admissible / h1_estimate / h1_compare / h2_tokens / h2_compare / h3 /
      tvs_for_arm / RULES    the frozen decision procedure of the prereg
  experiments/ptr-engine/tools/p95_power_probe.py
      lag1                   the lag-1 autocorrelation used by n_eff

A FINDING, NOT A REIMPLEMENTATION: `analyze_stats` has **no** `minimum` function.
The only floor it defines is `MIN_N = 20` (analyze_stats.py:112) and `min_n_for(0.95)
== 60` (analyze_stats.py:330).  This tool therefore uses those two and does not
invent a third.  Nothing else the card named was missing.

THE THREE REFUSAL MODES (all first-class output, never a crash, never a headline)
---------------------------------------------------------------------------------
  not_adjudicable_floor          raw n on the binding arm < 60; the analyser's own
                                 `quantile_ci` refusal text is quoted verbatim.
  not_adjudicable_effective_n    n_eff = n(1-r)/(1+r) < 60 on the binding arm, with
                                 r recomputed over THIS grid's own turn-ordered series.
  not_adjudicable_quality        H3/H2 undecidable (no grade, no pair, refused McNemar).
Plus two structural refusals that stop the emission instead of printing a number:
  a cell whose `usable_for` is ABSENT (analyze_stats.py:749 includes it -- this tool
  refuses it), and a missing ledger baseline (the spend delta is never assumed from 0).

WHY `usable_for` ABSENCE IS A REFUSAL HERE
------------------------------------------
`analyze_stats.select_usable_cells` keeps an unstamped cell and reports it
`unstamped` ("not a certification").  That is the right default for an exploratory
table and the wrong one for a pre-registered gate: an unstamped grid cell has not
been certified analysable, so a report that pools it can produce an `adjudicable`
verdict out of a cell nobody screened.  This consumer therefore refuses it BY NAME,
with the analyser's own record kept beside the refusal.

OFFLINE.  Zero requests.  Read-only: no rows file, manifest, grade document, ledger,
pin or published page is written.  The only writes are the two declared artefacts,
and only under `--write`.

Usage
-----
  python3 experiments/ptr-engine/tools/run_grid_report.py --write
  python3 experiments/ptr-engine/tools/run_grid_report.py --rows <file> --grade <grade.json> --print
  python3 experiments/ptr-engine/tools/run_grid_report.py --out /tmp/r.json --md /tmp/r.md

Exit codes: 0 emitted (may contain refusals) · 2 no analysable cell · 3 baseline missing.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                       # experiments/ptr-engine
ROOT = os.path.abspath(os.path.join(ENGINE, "..", ".."))
LONG = os.path.join(ENGINE, "longrun")
MEASURE = os.path.join(ENGINE, "measure")
DOCS = os.path.join(ROOT, "docs")

ANALYZER = os.path.join(LONG, "analyze_stats.py")
ROW_PROV = os.path.join(HERE, "row_provenance.py")
VERIFY = os.path.join(HERE, "verify_tranche1.py")
P95_PROBE = os.path.join(HERE, "p95_power_probe.py")

DEFAULT_BASELINE = os.path.join(MEASURE, "LEDGER-GRID-BASELINE-2.json")
DEFAULT_LEDGER = os.path.join(MEASURE, "REQUEST-LEDGER.json")
DEFAULT_SHAPE = os.path.join(MEASURE, "GRID-SHAPE.json")
DEFAULT_SANITY = os.path.join(MEASURE, "GRID-CELL-SANITY.json")
OUT_JSON = os.path.join(MEASURE, "GRID-REPORT-2.json")
OUT_MD = os.path.join(DOCS, "GRID-REPORT-2.md")

#: The effective-n floor the card fixes.  Numerically the same floor `min_n_for(0.95)`
#: returns (60), which is why it is quoted against that function rather than restated.
EFFECTIVE_N_FLOOR = 60

#: The price the card declares.  No artefact states 1,056; `measure/GRID-PARAMS.json`
#: prices the same grid at 1,016 and the mismatch is emitted, never smoothed over.
PRICE_EXPECTATION = 1056

REFUSAL_FLOOR = "not_adjudicable_floor"
REFUSAL_EFFECTIVE_N = "not_adjudicable_effective_n"
REFUSAL_QUALITY = "not_adjudicable_quality"
REFUSAL_UNSTAMPED = "refused_usable_for_absent"
REFUSAL_BASELINE = "refused_baseline_missing"
#: One report, more than one declared provenance: NO pooled term may print a number.
#: `V-GRID-REPORT` attempt 4 printed `ratio 2.5000` and `TVS 100800.0` across fixture
#: v7 + v8 because H2/TVS/verbosity were fed the global included rows.
REFUSAL_MIXED_ERA = "refused_mixed_era"
TVS_UNDEFINED = "tvs_undefined"


class RefusedEmission(Exception):
    """The report cannot be emitted at all -- a structural refusal, not a verdict."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def _load(name, path):
    if not os.path.isfile(path):
        raise RefusedEmission("missing_dependency",
                              "refusing: %s is missing (%s)" % (path, name))
    if LONG not in sys.path:
        sys.path.insert(0, LONG)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load("analyze_stats", ANALYZER)
RP = _load("row_provenance", ROW_PROV)
V = _load("verify_tranche1", VERIFY)
PP = _load("p95_power_probe", P95_PROBE)


# ---------------------------------------------------------------------------
# reading, identity, hashing
# ---------------------------------------------------------------------------
def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def load_rows(path):
    """A rows file -> dicts.  A half-written tail is skipped, never fatal."""
    rows = []
    with open(path, "rb") as fh:
        blob = fh.read()
    for line in blob.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _finite(value):
    """verify_tranche1's own numeric coercion (never a second copy of it)."""
    return V._finite(value)


def _artefact_list(paths):
    """`name:sha256` over the sorted basenames -- the pin recipe, for rows and graders."""
    items = sorted((os.path.basename(p), sha256_file(p)) for p in paths)
    return sha256_bytes("".join("%s:%s\n" % pair for pair in items).encode("utf-8"))


# ---------------------------------------------------------------------------
# THE GUARDS.  Each one is a named function so a test can neuter exactly it and
# watch the corresponding assertion go red (the red->green proof).
# ---------------------------------------------------------------------------
def cell_inclusion(record):
    """-> (included, kind, reason).  Guard 1: an ABSENT stamp is a refusal.

    `analyze_stats.select_usable_cells` EXCLUDES only `usable_for: []` and keeps an
    unstamped cell (`analyze_stats.py:749`, `excluded = analyses is not None and
    len(analyses) == 0`).  For a pre-registered gate that is the include-on-absence
    trap: a cell nobody screened would be pooled into an `adjudicable` verdict.
    """
    analyses = record.get("usable_for")
    if analyses is None:
        return False, REFUSAL_UNSTAMPED, (
            "usable_for is ABSENT for %s (source=%s): the analyser keeps an unstamped "
            "cell (analyze_stats.py:749 includes on absence); this consumer refuses it "
            "rather than certifying it by omission"
            % (record.get("name"), record.get("source")))
    if isinstance(analyses, (list, tuple)) and len(analyses) == 0:
        return False, "excluded_by_stamp", (
            "%s carries usable_for: [] (reason: %s) -- excluded by name, %d row(s) "
            "never analysed"
            % (record.get("name"), record.get("reason") or "(none recorded)",
               record.get("rows") or 0))
    return True, "", ""


def raw_floor_verdict(n_raw, floor=EFFECTIVE_N_FLOOR):
    """Guard 2: the raw-n floor.  < floor -> not_adjudicable_floor."""
    if n_raw is None or n_raw < int(floor):
        return REFUSAL_FLOOR
    return None


def effective_n_verdict(n_eff, floor=EFFECTIVE_N_FLOOR):
    """Guard 3: the effective-n floor.  n_eff < floor -> not_adjudicable_effective_n."""
    if n_eff is None:
        return REFUSAL_EFFECTIVE_N
    if n_eff < float(floor):
        return REFUSAL_EFFECTIVE_N
    return None


def effective_n(n, r):
    """n_eff = n(1-r)/(1+r) -- the card's formula, applied to this grid's own r."""
    if n is None or n <= 0 or r is None or not math.isfinite(r) or r >= 1.0:
        return None
    return float(n) * (1.0 - r) / (1.0 + r)


def per_arm_series(rows, dedupe=True):
    """-> (arm, selected_rows, meta) per arm, turn-ordered, plus dedupe/truncation counts.

    `turn_latency_rows` decides WHICH row is a turn's latency row.  This function only
    dedupes turn identities (a rep is part of the identity, so reps still pool) and
    hands the kept rows to `split_truncated`, whose rule is the analyser's.
    """
    selected, meta = S.turn_latency_rows(rows)
    by_arm = {}
    for row in selected:
        by_arm.setdefault(row.get("arm") or "?", []).append(row)
    out = {}
    for arm, arm_rows in by_arm.items():
        seen = set()
        kept = []
        for row in arm_rows:
            key = (row.get("arm"), row.get("rep"),
                   row.get("turn_index", row.get("turn")))
            if dedupe and key in seen:
                continue
            seen.add(key)
            kept.append(row)
        kept.sort(key=lambda r: (r.get("rep") or 0,
                                 r.get("turn_index", r.get("turn")) or 0))
        latency_rows, trunc = S.split_truncated(kept)
        out[arm] = {"selected": kept, "n_raw": len(arm_rows),
                    "n_dedup": len(kept), "latency": latency_rows,
                    "truncated": trunc, "meta": meta}
    return out, meta


def arm_stats(arm, bucket, paths):
    """One arm's H1 record: n counts, r over its own series, n_eff, p50/p95 or refusals."""
    latency = bucket["latency"]
    values = []
    for row in latency:
        v = _finite(row.get("ttft_ms"))
        if v is not None:
            values.append(v)
    n_used = len(values)
    r = PP.lag1(values) if n_used >= 3 else None
    n_eff = effective_n(n_used, r)

    def _quant(q):
        try:
            point, lo, hi, n = S.quantile_ci(values, q)
        except S.InsufficientSamples as exc:
            return {"refused": str(exc)}
        except ValueError as exc:            # pragma: no cover - defensive
            return {"refused": str(exc)}
        return {"value": point, "lo": lo, "hi": hi, "n": n}

    p50, p95 = _quant(0.50), _quant(0.95)
    return {
        "arm": arm,
        "n_raw": bucket["n_raw"],
        "n_dedup": bucket["n_dedup"],
        "n_used": n_used,
        "n_truncated_excluded": int(bucket["truncated"]["excluded"]),
        "truncated_by_stop_reason": dict(bucket["truncated"]["by_stop_reason"]),
        "r_lag1": r,
        "n_eff": n_eff,
        "n_eff_formula": "n(1-r)/(1+r) over this grid's own turn-ordered series",
        "p50": p50,
        "p95": p95,
        "source_paths": [os.path.basename(p) for p in paths],
        "selector_meta": {k: bucket["meta"][k] for k in
                          ("definition", "definition_version", "mode",
                           "definition_fallback", "n_input", "n_selected",
                           "explicit_initial_rows", "fallback_rows",
                           "mirrored_rows", "dropped_followup",
                           "dropped_turn_followup", "dropped_duplicate")},
    }


# ---------------------------------------------------------------------------
# grids: provenance clusters (era A and era B can never pool)
# ---------------------------------------------------------------------------
def era_of(cell):
    tools = str(cell.get("tools_mode") or "").lower()
    if tools in ("off", "none", "false", "0"):
        return "era_a_tools_off"
    if tools in ("on", "true", "read_file", "1"):
        return "era_b_tools_on"
    return "era_unknown"


def grid_id_of(cell):
    payload = json.dumps({k: cell.get(k) for k in sorted(S.PROVENANCE_LOAD_BEARING)},
                         sort_keys=True, default=str)
    return "grid:%s:%s" % (sha256_bytes(payload.encode("utf-8"))[:12], era_of(cell))


def cluster_cells(entries):
    """-> list of clusters; a new file/arm joins a cluster only if same_provenance agrees.

    `same_provenance` is THE gate: unknown-vs-known and unknown-vs-unknown both refuse,
    so an unstamped provenance can never be pooled into a named grid.
    """
    clusters = []
    for entry in entries:
        for cl in clusters:
            ok, _differing = RP.same_provenance(cl["cell"], entry["cell"])
            if ok:
                cl["entries"].append(entry)
                break
        else:
            clusters.append({"cell": dict(entry["cell"]), "entries": [entry]})
    return clusters


# ---------------------------------------------------------------------------
# provenance agreement: the gate every POOLED term passes before it may print a number
# ---------------------------------------------------------------------------
def provenance_detail(cluster):
    """One cluster described well enough to be blamed by name in a refusal."""
    cell = cluster["cell"]
    first = cluster["entries"][0]
    # `fixture_id` is not in PROVENANCE_LOAD_BEARING, so `provenance_cells` does not
    # carry it; the rows do, and naming the era's fixture is the point of the refusal.
    first_row = (first.get("rows") or [{}])[0]
    paths = sorted({os.path.basename(e["path"]) for e in cluster["entries"]})
    return {
        "grid": grid_id_of(cell),
        "era": era_of(cell),
        "fixture_sha256": cell.get("fixture_sha256"),
        "fixture_id": cell.get("fixture_id") or first_row.get("fixture_id"),
        "model": cell.get("model"),
        "thinking": cell.get("thinking"),
        "tools_mode": cell.get("tools_mode"),
        "introduced_by": os.path.basename(first["path"]),
        "introduced_by_arm": first["arm"],
        "paths": paths,
        "unknown_fields": _unknown_fields(cell),
    }


def _unknown_fields(cell):
    """Load-bearing fields this cell never declared (`unknown` is not agreement)."""
    unknown = str(getattr(S, "PROVENANCE_UNKNOWN", "unknown"))
    return [name for name in S.PROVENANCE_LOAD_BEARING
            if str(cell.get(name)) == unknown]


def mixed_provenance(clusters):
    """-> (poolable, detail).  False means every pooled term REFUSES by name.

    `cluster_cells` already splits on `row_provenance.same_provenance`, so a report with
    more than one cluster is a report whose included cells do NOT agree on the
    load-bearing provenance (`fixture_sha256` / `model` / `thinking` / `tools_mode`).
    A mean, ratio, interval or `n` summed over such a set is an artefact of the pooling,
    not a measurement -- exactly the `5/92` vs `5/43` class of error.  One cluster is
    poolable (every cell agrees), and the guard never refuses that case.
    """
    detail = [provenance_detail(cl) for cl in clusters]
    if len(clusters) > 1:
        return False, detail
    # ONE cluster is still not agreement if a load-bearing field is `unknown`: a set whose
    # provenance nobody can name is not a set whose provenance agrees (the same rule
    # `epochs_never_pooled` already states for grids).
    if detail and detail[0]["unknown_fields"]:
        return False, detail
    return True, None


def mixed_era_text(detail):
    """The refusal sentence: every era present, and the cell that introduced it."""
    parts = []
    for i, rec in enumerate(detail, 1):
        parts.append(
            "%d) grid `%s` era `%s`: fixture_sha256 `%s` / fixture_id `%s` / model `%s` "
            "/ thinking `%s` / tools_mode `%s`, introduced by `%s` (arm `%s`; files %s)"
            % (i, rec["grid"], rec["era"], str(rec["fixture_sha256"])[:16],
               rec["fixture_id"], rec["model"], rec["thinking"], rec["tools_mode"],
               rec["introduced_by"], rec["introduced_by_arm"],
               ", ".join("`%s`" % p for p in rec["paths"])))
    unknown = []
    for rec in detail:
        for name in rec["unknown_fields"]:
            unknown.append("`%s` is `unknown` in grid `%s` (files %s)"
                           % (name, rec["grid"],
                              ", ".join("`%s`" % p for p in rec["paths"])))
    tail = ("; additionally a load-bearing field is unknown, which is never evidence of "
            "agreement: %s" % "; ".join(unknown)) if unknown else ""
    return ("these included cells do not share one provenance, so the pooled terms H2, TVS "
            "and verbosity would sum across eras -- no mean, interval, ratio, accuracy or n "
            "is printed for them. Provenances present (each is its own grid in H1): %s%s"
            % ("; ".join(parts), tail))


# ---------------------------------------------------------------------------
# H2 / H3 / TVS / verbosity / spend
# ---------------------------------------------------------------------------
def h2_block(rows, per_arm_rows, paths_by_arm):
    """Per-arm limb means (verify_tranche1.h2_tokens) + the pair comparison and its signs."""
    keys = set()
    for rows_arm in per_arm_rows.values():
        for row in rows_arm:
            keys.add((row.get("arm"), row.get("rep"),
                      row.get("turn_index", row.get("turn"))))
    per_arm = []
    for arm in sorted(per_arm_rows):
        tok = V.h2_tokens(per_arm_rows[arm], keys, V.RULES)
        inc, unc = tok["mean_prompt_inclusive"], tok["mean_prompt_uncached"]
        sign = None
        if inc is not None and unc is not None:
            diff = inc - unc
            sign = 0 if diff == 0 else (1 if diff > 0 else -1)
        per_arm.append({
            "arm": arm,
            "cached_inclusive_tokens_per_turn": inc,
            "uncached_tokens_per_turn": unc,
            "difference_sign": sign,
            "n": tok["n"],
            "excluded_null_token_rows": tok["excluded_null_token_rows"],
            "duplicate_rows_skipped": tok["duplicate_rows_skipped"],
            "source_paths": [os.path.basename(p) for p in paths_by_arm.get(arm, ())],
        })

    def _sgn(a, b):
        if a is None or b is None:
            return None
        return 0 if a == b else (1 if a > b else -1)

    comparison = {}
    have_pair = V.C_ARM in per_arm_rows and V.A_ARM in per_arm_rows
    if have_pair:
        cmp = V.h2_compare(rows, keys, V.RULES)
        comparison = dict(cmp)
        comparison["inclusive_sign"] = _sgn(cmp["C"]["mean_prompt_inclusive"],
                                            cmp["A"]["mean_prompt_inclusive"])
        comparison["uncached_sign"] = _sgn(cmp["C"]["mean_prompt_uncached"],
                                           cmp["A"]["mean_prompt_uncached"])
        comparison["sign_basis"] = ("sign(C - A) on each limb; +1 means C pays MORE. "
                                    "Both limbs are reported and neither is picked.")
    else:
        comparison = {"verdict": "not_adjudicable", "why":
                      "H2 is a C-vs-A comparison and %s/%s are not both present in "
                      "an included, admissible grid" % (V.C_ARM, V.A_ARM)}
    return {"per_arm": per_arm,
            "comparison": comparison,
            "difference_sign_basis": ("sign(cached_inclusive - uncached) per arm: +1 "
                                      "means the arm's per-turn prompt work exceeds its "
                                      "uncached work, i.e. cache was credited; 0 equal"),
            "rules": {k: V.RULES[k] for k in ("H2_INCLUSIVE", "H2_UNCACHED",
                                              "H2_REQUIRE_BOTH")}}


def h3_block(grade_path, grade_sha):
    """H3 from grade_v5 cells only, through verify_tranche1.h3 (no second copy of the rule)."""
    if not grade_path:
        return {"x_12": None, "x_9": None, "none_flagged": [], "answered_ratio": None,
                "contract_adherence": None, "mcnemar": {"b": None, "c": None, "p": None},
                "verdict": "not_adjudicable",
                "reason": ("no grade_v5 document supplied (--grade absent): x/12, x/9, "
                           "answered_ratio and McNemar are NOT imputed from rows, "
                           "which would be the wrong population")}
    with open(grade_path, encoding="utf-8") as fh:
        grade = json.load(fh)
    if not isinstance(grade, dict) or "cells" not in grade:
        return {"x_12": None, "x_9": None, "none_flagged": [], "answered_ratio": None,
                "contract_adherence": None, "mcnemar": {"b": None, "c": None, "p": None},
                "verdict": "not_adjudicable",
                "reason": "refusing: %s is not a grade_v5 document (no `cells`)"
                          % os.path.basename(grade_path)}
    res = V.h3(grade, V.RULES)
    primary = res["per_arm"][V.C_ARM]
    none_flagged = []
    for cid in V.NONE_IDS:
        seen = [c for c in (grade.get("cells") or []) if c.get("id") == cid]
        none_flagged.append({"id": cid, "in_grade": bool(seen),
                             "verdicts": sorted({str(c.get("verdict")) for c in seen})})
    return {
        "arm": V.C_ARM,
        "x_12": primary["x_of_12"],
        "x_9": primary["x_of_9_substantive"],
        "none_flagged": none_flagged,
        "none_passes": primary["none_passes"],
        "missing_ids": primary["missing_ids"],
        "answered_ratio": primary["answered_ratio"],
        "contract_adherence": primary["contract_adherence"],
        "contract_adherence_note": ("grade_v5 carries NO contract-adherence column; the "
                                    "string above is the frozen placeholder, never a "
                                    "measured number"),
        "mcnemar": {"b": res["mcnemar"]["b"], "c": res["mcnemar"]["c"],
                    "p": res["mcnemar"]["p"],
                    "licensed": res["mcnemar"]["licensed"],
                    "discordant": res["mcnemar"]["discordant"],
                    "floor": res["mcnemar"]["floor"],
                    "refusal": res["mcnemar"]["refusal"]},
        "per_arm": res["per_arm"],
        "checkpoint_loss": res["checkpoint_loss"],
        "verdict": res["verdict"],
        "veto": res["veto"],
        "source": {"path": grade_path, "sha256": grade_sha},
        "rule": res["rule"],
    }


def tvs_block(rows, grade_path, grade_sha, rows_sha, paths_by_arm):
    """TVS or the literal string "UNDEFINED" -- never 0, never an imputed number."""
    if not grade_path:
        return "UNDEFINED", ("no grade_v5 document supplied: TVS is certified by a graded "
                             "checkpoint pass in a grade_v5 document, and without one the "
                             "figure is UNDEFINED rather than imputed from the rows")
    with open(grade_path, encoding="utf-8") as fh:
        grade = json.load(fh)
    if not isinstance(grade, dict) or "cells" not in grade:
        return "UNDEFINED", "the --grade document is not a grade_v5 document (no `cells`)"
    have_pair = V.C_ARM in paths_by_arm and V.A_ARM in paths_by_arm
    if not have_pair:
        return "UNDEFINED", ("C/A pair incomplete (%s and %s must both be included)"
                             % (V.C_ARM, V.A_ARM))
    per_arm = {}
    for arm in (V.C_ARM, V.A_ARM):
        rec = V.tvs_for_arm(rows, grade, arm, V.RULES)
        rec["source_paths"] = [os.path.basename(p) for p in paths_by_arm[arm]]
        per_arm[arm] = rec
    first = per_arm[V.C_ARM]
    if first.get("censored") or first.get("tvs") is None:
        return "UNDEFINED", ("no declared checkpoint passed for %s (censored at turn %s); "
                             "a censored TVS is never assigned a number and never compared"
                             % (V.C_ARM, first.get("censored_at_turn")))
    if first.get("tvs") == 0:
        return "UNDEFINED", ("the computed TVS is 0 tokens, which is not a measurement of "
                             "prompt+completion work; refusing the value")
    return {"value": first["tvs"], "arm": V.C_ARM,
            "rows_sha256": rows_sha, "grader_sha256": grade_sha,
            "through_turn": first.get("through_turn"),
            "checkpoint_id": first.get("checkpoint_id"),
            "billed_rows": first.get("billed_rows"),
            "excluded_null_token_rows": first.get("excluded_null_token_rows"),
            "duplicate_records_skipped": first.get("duplicate_records_skipped"),
            "source_paths": first["source_paths"],
            "per_arm": per_arm}, ""


def verbosity_block(per_arm_rows, paths_by_arm):
    """Completion tokens and answer length per arm -- emitted BEFORE any cost line."""
    out = []
    for arm in sorted(per_arm_rows):
        toks, chars = [], []
        for row in per_arm_rows[arm]:
            if S.is_truncated(row):
                continue
            ct = _finite(row.get("completion_tokens"))
            if ct is not None:
                toks.append(ct)
            answer = row.get("answer_raw")
            if answer is None:
                answer = row.get("content")
            if isinstance(answer, str):
                chars.append(float(len(answer)))
        out.append({
            "arm": arm,
            "mean_completion_tokens": (sum(toks) / len(toks)) if toks else None,
            "mean_answer_chars": (sum(chars) / len(chars)) if chars else None,
            "n_turns": len(toks),
            "n_answers": len(chars),
            "source_paths": [os.path.basename(p) for p in paths_by_arm.get(arm, ())],
        })
    return {"per_arm": out,
            "note": "verbosity is emitted before spend so no cost claim can be read as "
                    "a verbosity result (or the reverse)"}


def spend_block(baseline_path, ledger_path):
    """Spend as a DELTA against the frozen baseline; a missing baseline is a refusal."""
    if not baseline_path or not os.path.isfile(baseline_path):
        raise RefusedEmission(REFUSAL_BASELINE,
                              "refusing: ledger baseline %r is missing -- the spend delta "
                              "is NOT assumed from 0 and no price line is printed"
                              % (baseline_path,))
    with open(baseline_path, encoding="utf-8") as fh:
        base = json.load(fh)
    base_requests = base.get("requests")
    if base_requests is None:
        base_requests = (base.get("budget") or {}).get("spent")
    if base_requests is None:
        raise RefusedEmission(REFUSAL_BASELINE,
                              "refusing: baseline %s carries no `requests` field"
                              % os.path.basename(baseline_path))
    block = {
        "baseline": {"path": baseline_path,
                     "sha256": sha256_file(baseline_path),
                     "requests": base_requests,
                     "remaining": base.get("remaining"),
                     "cap": base.get("cap"),
                     "frozen_at": base.get("frozen_at")},
        "spent_now": None,
        "delta": None,
        "price_expectation": PRICE_EXPECTATION,
        "price_expectation_source": ("declared by card ERA-B-ANALYSIS-CONTRACT; no artefact "
                                     "states 1,056"),
    }
    ledger = {}
    if ledger_path and os.path.isfile(ledger_path):
        try:
            with open(ledger_path, encoding="utf-8") as fh:
                ledger = json.load(fh) or {}
        except (OSError, ValueError):
            ledger = {}
    spent = (ledger.get("budget") or {}).get("spent_raw")
    if spent is None:
        spent = (ledger.get("budget") or {}).get("spent")
    if spent is None:
        block["refused"] = ("REQUEST-LEDGER carries no budget.spent_raw/spent; spent_now "
                            "and delta are left null rather than derived from the rows")
        return block
    block["spent_now"] = spent
    block["delta"] = spent - base_requests
    block["fits_in_remaining"] = (base.get("remaining") is not None
                                  and block["delta"] <= base["remaining"])
    return block


def price_artefact_block(shape_path):
    """The artefact's own price, printed beside the card's expectation, mismatch or not."""
    params = os.path.join(MEASURE, "GRID-PARAMS.json")
    out = {"path": params, "present": os.path.isfile(params)}
    if os.path.isfile(params):
        try:
            with open(params, encoding="utf-8") as fh:
                doc = json.load(fh) or {}
        except (OSError, ValueError):
            doc = {}
        price = doc.get("price") or {}
        out["price_total"] = price.get("total")
        out["components"] = price.get("components")
        out["schema"] = doc.get("schema")
    out["matches_price_expectation"] = out.get("price_total") == PRICE_EXPECTATION
    out["note"] = ("the card's 1,056 and the artefact's total are different quantities: "
                   "the difference is a finding to reconcile, not a number to round")
    if shape_path and os.path.isfile(shape_path):
        out["grid_shape"] = os.path.basename(shape_path)
    return out


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------
def discover_cells(rows_paths=None, pattern="rows-cell-*.jsonl"):
    if rows_paths:
        return [os.path.abspath(p) for p in rows_paths]
    return sorted(glob.glob(os.path.join(MEASURE, pattern)))


def build_report(rows_paths=None, manifest_paths=None, manifest_dir=None,
                 sanity_path=None, grade_path=None, baseline_path=DEFAULT_BASELINE,
                 ledger_path=DEFAULT_LEDGER, shape_path=DEFAULT_SHAPE):
    paths = discover_cells(rows_paths)
    if not paths:
        raise RefusedEmission("no_cells",
                              "refusing: no rows-cell-*.jsonl found under measure/ -- "
                              "there is nothing to report and no empty table is printed "
                              "as a success")

    manifests = S.load_cell_manifests(manifest_paths, manifest_dir=manifest_dir)
    sanity = DEFAULT_SANITY if sanity_path is None else sanity_path
    files = []
    for path in paths:
        rows = load_rows(path)
        files.append((path, len(rows), rows))

    # --- usability: the analyser's record, then THIS tool's stricter gate ---------
    _kept, records = S.select_usable_cells(files, manifests=manifests, sanity=sanity)
    cell_records = []
    included = []
    refusals = []
    by_path = {rec["path"]: rec for rec in records}
    for path, count, rows in files:
        rec = by_path.get(path)
        if rec is None:                      # pragma: no cover - select_usable_cells covers all
            rec = {"path": path, "name": os.path.basename(path), "rows": count,
                   "usable_for": None, "reason": "", "source": "unstamped"}
        ok, kind, why = cell_inclusion(rec)
        cell_records.append({"path": path, "name": rec["name"], "sha256": sha256_file(path),
                             "rows": count, "usable_for": rec["usable_for"],
                             "source": rec["source"], "reason": rec["reason"],
                             "included": ok, "refusal_kind": kind or ""})
        if ok:
            included.append((path, count, rows))
        else:
            refusals.append({"kind": kind, "scope": rec["name"], "text": why})

    # An all-refused run is a REPORT, not a crash: the artifact must exist and must say
    # why nothing was analysed. Only "no cell files at all" stops the emission.

    # --- provenance clusters (era A never pools with era B) ----------------------
    entries = []
    for path, _count, rows in included:
        prov = S.provenance_cells(rows)
        for arm, cell in prov.items():
            arm_rows = [r for r in rows if (r.get("arm") or "?") == arm]
            if not arm_rows:
                continue
            entries.append({"path": path, "arm": arm, "cell": dict(cell),
                            "rows": arm_rows})
    clusters = cluster_cells(entries)

    grade_sha = sha256_file(grade_path) if (grade_path and os.path.isfile(grade_path)) else None
    rows_sha = _artefact_list([p for p, _c, _r in included]) if included else ""

    grids = []
    for cl in clusters:
        cell = cl["cell"]
        gid = grid_id_of(cell)
        paths_by_arm = {}
        per_arm_rows = {}
        for entry in cl["entries"]:
            paths_by_arm.setdefault(entry["arm"], []).append(entry["path"])
            per_arm_rows.setdefault(entry["arm"], []).extend(entry["rows"])
        buckets, meta = per_arm_series(
            [r for arm_rows in per_arm_rows.values() for r in arm_rows])
        arms = [arm_stats(arm, buckets[arm], paths_by_arm[arm]) for arm in sorted(buckets)]
        # the pair comparison decides nothing here; it names what is missing
        by_arm = {a["arm"]: a for a in arms}
        pair_present = V.C_ARM in by_arm and V.A_ARM in by_arm
        comparison = {"c_arm": V.C_ARM, "a_arm": V.A_ARM, "pair_present": pair_present}
        if pair_present:
            c_est = {"admissible": "value" in by_arm[V.C_ARM]["p95"],
                     "hi": by_arm[V.C_ARM]["p95"].get("hi"),
                     "lo": by_arm[V.C_ARM]["p95"].get("lo"),
                     "point": by_arm[V.C_ARM]["p95"].get("value"),
                     "n": by_arm[V.C_ARM]["p95"].get("n")}
            a_est = {"admissible": "value" in by_arm[V.A_ARM]["p95"],
                     "hi": by_arm[V.A_ARM]["p95"].get("hi"),
                     "lo": by_arm[V.A_ARM]["p95"].get("lo"),
                     "point": by_arm[V.A_ARM]["p95"].get("value"),
                     "n": by_arm[V.A_ARM]["p95"].get("n")}
            comparison.update(V.h1_compare(c_est, a_est, V.RULES))
            comparison["p95_interval_overlap"] = (
                "ranges overlap or touch" if by_arm[V.C_ARM]["p95"].get("hi") is not None
                and by_arm[V.A_ARM]["p95"].get("lo") is not None
                and not (by_arm[V.C_ARM]["p95"]["hi"] < by_arm[V.A_ARM]["p95"]["lo"]
                         or by_arm[V.A_ARM]["p95"]["hi"] < by_arm[V.C_ARM]["p95"]["lo"])
                else "disjoint")
        else:
            comparison.update({"verdict": "not_adjudicable",
                               "why": "pair incomplete: %s"
                                      % (" or ".join(a for a in (V.C_ARM, V.A_ARM)
                                                     if a not in by_arm))})

        # --- verdict: floor first, then effective n, then adjudicable ----------
        binding = None
        for arm in arms:
            if binding is None or (arm["n_eff"] is not None and
                                   (binding["n_eff"] is None or arm["n_eff"] < binding["n_eff"])):
                binding = arm
        floor_refusal = None
        verdict = None
        if binding is not None:
            verdict = raw_floor_verdict(binding["n_raw"])
            if verdict:
                floor_refusal = (by_arm.get(binding["arm"], {})
                                 .get("p95", {}).get("refused"))
        if verdict is None and binding is not None:
            verdict = effective_n_verdict(binding["n_eff"])
        if verdict is None:
            verdict = "adjudicable"

        others = [g for g in clusters if g is not cl]
        disjoint = True
        for other in others:
            ok, _d = RP.same_provenance(cell, other["cell"])
            if ok:
                disjoint = False
        grid = {
            "grid": gid,
            "era": era_of(cell),
            "provenance": {k: cell.get(k) for k in sorted(S.PROVENANCE_LOAD_BEARING)},
            "arms": arms,
            "comparison": comparison,
            "pooled_disjoint": disjoint,
            "pooled_disjoint_basis": ("same_provenance refuses agreement with every other "
                                      "grid on this report" if disjoint else
                                      "another grid shares this provenance signature"),
            "binding_arm": binding["arm"] if binding else None,
            "binding_n_eff": binding["n_eff"] if binding else None,
            "binding_n_raw": binding["n_raw"] if binding else None,
            "verdict": verdict,
            "selector_meta": meta,
        }
        if verdict == REFUSAL_FLOOR:
            grid["refusal"] = floor_refusal or (
                "raw n=%s on binding arm %s is below the p95 floor %d"
                % (binding["n_raw"], binding["arm"], S.min_n_for(0.95)))
            refusals.append({"kind": REFUSAL_FLOOR, "scope": gid,
                             "text": "%s: binding arm %s has n_raw=%s < %d; analyser: %s"
                                     % (gid, binding["arm"], binding["n_raw"],
                                        S.min_n_for(0.95), grid["refusal"])})
        elif verdict == REFUSAL_EFFECTIVE_N:
            grid["refusal"] = (
                "binding arm %s: n_eff=%s < %d (n_used=%s, r_lag1=%s) -- consecutive "
                "turns are not independent, so the interval is narrower than its n claims"
                % (binding["arm"],
                   ("%.2f" % binding["n_eff"]) if binding["n_eff"] is not None
                   else "not computable",
                   EFFECTIVE_N_FLOOR, binding["n_used"], _fmt(binding["r_lag1"], 4)))
            refusals.append({"kind": REFUSAL_EFFECTIVE_N, "scope": gid,
                             "text": grid["refusal"]})
        grids.append(grid)

    # --- the report -----------------------------------------------------------
    included_rows = [r for _p, _c, rows in included for r in rows]
    per_arm_all = {}
    paths_arm_all = {}
    for path, _count, rows in included:
        for row in rows:
            arm = row.get("arm") or "?"
            per_arm_all.setdefault(arm, []).append(row)
            paths_arm_all.setdefault(arm, []).append(path)
    for arm in per_arm_all:
        paths_arm_all[arm] = sorted(set(paths_arm_all[arm]))

    # --- the pooling gate: one report may pool only cells that agree on provenance ---
    poolable, mixed_detail = mixed_provenance(clusters)
    if poolable:
        h2 = h2_block(included_rows, per_arm_all, paths_arm_all)
        tvs, tvs_reason = tvs_block(included_rows, grade_path, grade_sha, rows_sha,
                                    paths_arm_all)
        verbosity = verbosity_block(per_arm_all, paths_arm_all)
    else:
        why = mixed_era_text(mixed_detail)
        h2 = {"per_arm": [],
              "comparison": {"verdict": REFUSAL_MIXED_ERA, "why": why},
              "difference_sign_basis": why,
              "provenances_present": mixed_detail,
              "rules": {k: V.RULES[k] for k in ("H2_INCLUSIVE", "H2_UNCACHED",
                                                "H2_REQUIRE_BOTH")}}
        tvs, tvs_reason = "UNDEFINED", ("%s: %s" % (REFUSAL_MIXED_ERA, why))
        verbosity = {"per_arm": [], "refusal": REFUSAL_MIXED_ERA, "reason": why,
                     "provenances_present": mixed_detail,
                     "note": ("verbosity is pooled over included rows like every cost term; "
                              "across provenances it refuses by name (see section 8)")}
        for rec in mixed_detail:
            refusals.append({
                "kind": REFUSAL_MIXED_ERA,
                "scope": "%s [era %s]" % (rec["grid"], rec["era"]),
                "text": ("%s: era `%s` grids over cells %s (introduced by `%s`, arm `%s`) "
                         "declare fixture_sha256 `%s` / fixture_id `%s` / tools_mode `%s`%s, "
                         "which does not agree with another grid on this report -- H2, TVS "
                         "and verbosity print no mean, interval, ratio, accuracy or n"
                         % (REFUSAL_MIXED_ERA, rec["era"],
                            ", ".join("`%s`" % p for p in rec["paths"]),
                            rec["introduced_by"], rec["introduced_by_arm"],
                            str(rec["fixture_sha256"])[:16], rec["fixture_id"],
                            rec["tools_mode"],
                            ("; unknown load-bearing field(s): %s"
                             % ", ".join("`%s`" % f for f in rec["unknown_fields"]))
                            if rec["unknown_fields"] else "")),
            })
    h3 = h3_block(grade_path, grade_sha)
    spend = spend_block(baseline_path, ledger_path)

    if h3.get("verdict") == "not_adjudicable" and h3.get("reason"):
        refusals.append({"kind": REFUSAL_QUALITY, "scope": "H3",
                         "text": h3["reason"]})
    if tvs == "UNDEFINED":
        refusals.append({"kind": TVS_UNDEFINED, "scope": "TVS", "text": tvs_reason})
    if h2["comparison"].get("verdict") == "not_adjudicable":
        refusals.append({"kind": REFUSAL_QUALITY, "scope": "H2",
                         "text": h2["comparison"].get("why", "")})

    epochs = []
    if len(grids) > 1:
        for grid in grids:
            epochs.append({
                "grid": grid["grid"], "era": grid["era"],
                "paths": sorted({p for arm in grid["arms"]
                                 for p in arm["source_paths"]}),
                "reason": ("kept apart: its provenance differs from every other grid on "
                           "a load-bearing field (or is unknown, which is never evidence "
                           "of agreement), so no interval and no mean pools across grids"),
            })
    missing_arms = []
    shape = {}
    if shape_path and os.path.isfile(shape_path):
        try:
            with open(shape_path, encoding="utf-8") as fh:
                shape = json.load(fh) or {}
        except (OSError, ValueError):
            shape = {}
        declared = [c.get("arm") for c in (shape.get("cells") or []) if c.get("arm")]
        for arm in sorted(set(declared)):
            if arm not in per_arm_all:
                missing_arms.append(arm)

    doc = {
        "schema": "consonance.grid-report/2",
        "unit": "ERA-B-ANALYSIS-CONTRACT",
        "offline": {"requests_sent": 0, "network_events": 0, "live_cells": 0},
        "terms": {
            "h1": "pooled R-all per arm, quantile_ci with module defaults; effective n "
                  "recomputed here from the grid's own lag-1 autocorrelation",
            "h2": "both limbs, neither picked; sign of C-A per limb",
            "h3": "x/12 gate, x/9 decomposition, exact McNemar, answered_ratio and the "
                  "contract_adherence placeholder",
            "tvs": "grade_v5-certified, 3 truth ids; a censored TVS is UNDEFINED, never 0",
            "verbosity": "emitted before spend",
        },
        "inputs": {
            "rows": [{"path": p, "sha256": sha256_file(p)} for p, _c, _r in included],
            "rows_sha256": rows_sha,
            "ledger_baseline": os.path.basename(baseline_path or ""),
            "ledger": os.path.basename(ledger_path or ""),
            "grade": os.path.basename(grade_path) if grade_path else None,
            "grader_sha256": grade_sha,
            "harness_pin": os.path.join(MEASURE, "HARNESS-PIN.json"),
            "harness_pin_present": os.path.isfile(os.path.join(MEASURE, "HARNESS-PIN.json")),
            "grid_shape": os.path.basename(shape_path or "") or None,
            "declared_cells": len(shape.get("cells") or []) or None,
            "declared_arms": sorted({c.get("arm") for c in (shape.get("cells") or [])
                                     if c.get("arm")}) or None,
        },
        "cells": cell_records,
        "h1": {"grids": grids,
               "floor": {"p95_min_n": S.min_n_for(0.95), "effective_n_floor": EFFECTIVE_N_FLOOR,
                         "min_n": S.MIN_N, "source": "analyze_stats.min_n_for(0.95)",
                         "raw_n_needed_for_effective_60": _raw_n_needed(),
                         "raw_n_note": ("inverting n(1-r)/(1+r) >= 60 gives n >= "
                                        "60(1+r)/(1-r): the effective-n floor is a RAW-n "
                                        "floor that moves with the grid's own autocorrelation")}},
        "h2": h2,
        "h3": h3,
        "tvs": tvs,
        "verbosity": verbosity,
        "spend": spend,
        "price_artefact": price_artefact_block(shape_path),
        "provenance_pooled": {"poolable": poolable,
                              "grids": [g["grid"] for g in grids],
                              "eras_present": sorted({g["era"] for g in grids}),
                              "provenances_present": mixed_detail or []},
        "epochs_never_pooled": epochs,
        "missing_arms": missing_arms,
        "refusals": refusals,
        "verdicts": {
            "h1": {g["grid"]: g["verdict"] for g in grids},
            "h2": h2["comparison"].get("verdict"),
            "h3": h3.get("verdict"),
            "tvs": "UNDEFINED" if tvs == "UNDEFINED" else "assigned",
            "overall": ("not_adjudicable" if any(
                g["verdict"] != "adjudicable" for g in grids) or
                h3.get("verdict") in (None, "not_adjudicable") else "adjudicable"),
        },
    }
    if tvs == "UNDEFINED":
        doc["tvs_reason"] = tvs_reason
    else:
        doc["tvs_reason"] = ""
    doc["generated_at"] = _utc_now()
    return doc


def _raw_n_needed(floor=EFFECTIVE_N_FLOOR, rs=(0.05, 0.10, 0.20, 0.30, 0.40)):
    """The raw n a grid needs at each lag-1 r to reach n_eff >= floor (arithmetic only)."""
    return {"%.2f" % r: round(floor * (1.0 + r) / (1.0 - r), 2) for r in rs}


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------
def _fmt(value, digits=2):
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return ("%%.%df" % digits) % value
    return str(value)


def _interval(rec):
    if not isinstance(rec, dict):
        return "—"
    if "refused" in rec:
        return "REFUSED: %s" % rec["refused"]
    return "%.2f [%.2f, %.2f] n=%s" % (rec["value"], rec["lo"], rec["hi"], rec["n"])


def render_markdown(doc):
    lines = []
    add = lines.append
    add("# GRID-REPORT-2 — the grid in terms fixed before the data existed")
    add("")
    add("Generated by `experiments/ptr-engine/tools/run_grid_report.py` from "
        "`measure/rows-cell-*.jsonl` and their manifests. Every statistic is imported "
        "from `analyze_stats` / `verify_tranche1` / `row_provenance`; none is re-implemented "
        "here. **Offline: 0 requests, 0 live cells.** Generated %s."
        % doc.get("generated_at", "—"))
    add("")
    add("**No headline below lacks an `n` and a source path.** Where a number could not be "
        "obtained from its licensed estimator the row says `REFUSED` or `UNDEFINED` and "
        "quotes the refusal — it is never replaced by a plausible figure.")
    add("")
    add("## 0. Cells read, cells refused")
    add("")
    add("| cell | rows | usable_for | source | included |")
    add("|---|---|---|---|---|")
    for cell in doc["cells"]:
        add("| `%s` | %d | %s | %s | %s |"
            % (cell["name"], cell["rows"],
               "absent" if cell["usable_for"] is None else json.dumps(cell["usable_for"]),
               cell["source"], "yes" if cell["included"] else "**no** (%s)" % cell["refusal_kind"]))
    add("")
    if doc.get("missing_arms"):
        add("Declared arms with no included rows on disk: %s."
            % ", ".join("`%s`" % a for a in doc["missing_arms"]))
        add("")
    add("## 1. H1 — pooled R-all latency per arm, with effective n")
    add("")
    add("Floor: `min_n_for(0.95)` = **%s** raw turns; effective-n floor **%s**; "
        "`n_eff = n(1−r)/(1+r)` with `r` the lag-1 autocorrelation recomputed over the "
        "grid's own turn-ordered series." % (doc["h1"]["floor"]["p95_min_n"],
                                             doc["h1"]["floor"]["effective_n_floor"]))
    add("")
    need = doc["h1"]["floor"]["raw_n_needed_for_effective_60"]
    add("Inverted, the floor is a RAW-n requirement that moves with the grid's own "
        "autocorrelation (`n >= 60(1+r)/(1−r)`): r=0.05 → n≥%s · r=0.10 → n≥%s · "
        "r=0.20 → n≥%s · r=0.30 → n≥%s · r=0.40 → n≥%s. A 48-turn cell is one rep: "
        "this is why the reading is R-all over reps, and why a single 60-turn arm can "
        "fail the effective-n floor even with 60 completed turns."
        % (need["0.05"], need["0.10"], need["0.20"], need["0.30"], need["0.40"]))
    add("")
    if not doc["h1"]["grids"]:
        add("**No grid.** Every input cell was refused above, so no arm has an `n`, no `r` "
            "was recomputed, and no interval exists — the report says that instead of "
            "printing an empty table as a result.")
        add("")
    for grid in doc["h1"]["grids"]:
        add("### grid `%s` (%s) — **%s**" % (grid["grid"], grid["era"], grid["verdict"]))
        add("")
        add("provenance: %s · pooled_disjoint: %s"
            % (json.dumps(grid["provenance"]), grid["pooled_disjoint"]))
        add("")
        add("| arm | n_raw | n_dedup | n_used | truncated excl. | r_lag1 | n_eff | p50 | p95 |")
        add("|---|---|---|---|---|---|---|---|---|")
        for arm in grid["arms"]:
            add("| `%s` | %d | %d | %d | %d | %s | %s | %s | %s |"
                % (arm["arm"], arm["n_raw"], arm["n_dedup"], arm["n_used"],
                   arm["n_truncated_excluded"], _fmt(arm["r_lag1"], 4),
                   _fmt(arm["n_eff"], 2), _interval(arm["p50"]), _interval(arm["p95"])))
        add("")
        add("source: %s" % ", ".join("`%s`" % p for p in
                                     sorted({p for a in grid["arms"] for p in a["source_paths"]})))
        add("")
        if grid.get("refusal"):
            add("**Refusal (`%s`), binding arm `%s`:** %s"
                % (grid["verdict"], grid["binding_arm"], grid["refusal"]))
            add("")
        cmp = grid["comparison"]
        add("Pair %s vs %s: %s%s" % (cmp.get("c_arm"), cmp.get("a_arm"),
                                     cmp.get("verdict"),
                                     (" — " + cmp["why"]) if cmp.get("why") else ""))
        add("")
    add("## 2. H2 — total prompt work, both limbs, neither picked")
    add("")
    if not doc["h2"]["per_arm"] and doc["h2"]["comparison"].get("verdict") == REFUSAL_MIXED_ERA:
        add("**`%s`** — %s" % (REFUSAL_MIXED_ERA, doc["h2"]["comparison"].get("why", "")))
        add("")
    elif not doc["h2"]["per_arm"]:
        add("No arm contributed a billed turn: H2 is `not_adjudicable`, and no limb mean is "
            "printed without its n.")
        add("")
    else:
        add("| arm | cache-inclusive tok/turn | uncached tok/turn | cached share | sign(incl−unc) | n | source |")
        add("|---|---|---|---|---|---|---|")
    for row in (doc["h2"]["per_arm"] if doc["h2"]["per_arm"] else ()):
        share = None
        if row["cached_inclusive_tokens_per_turn"]:
            share = (row["cached_inclusive_tokens_per_turn"]
                     - (row["uncached_tokens_per_turn"] or 0)) / row["cached_inclusive_tokens_per_turn"]
        add("| `%s` | %s | %s | %s | %s | %d | %s |"
            % (row["arm"], _fmt(row["cached_inclusive_tokens_per_turn"]),
               _fmt(row["uncached_tokens_per_turn"]),
               _fmt(share, 4) if share is not None else "—",
               "—" if row["difference_sign"] is None else "%+d" % row["difference_sign"],
               row["n"], ", ".join("`%s`" % p for p in row["source_paths"])))
    add("")
    cmp = doc["h2"]["comparison"]
    if cmp.get("verdict") == REFUSAL_MIXED_ERA:
        pass
    elif cmp.get("verdict") in ("h2_pass", "h2_fail", "h2_failed", "h2_failed_split"):
        add("Both limbs, C−A: cache-inclusive ratio **%.4f** (sign %+d, pass=%s), uncached "
            "ratio **%.4f** (sign %+d, pass=%s) → **%s**."
            % (cmp["ratio_inclusive"], cmp.get("inclusive_sign") or 0, cmp["pass_inclusive"],
               cmp["ratio_uncached"], cmp.get("uncached_sign") or 0, cmp["pass_uncached"],
               cmp["verdict"]))
    else:
        add("**%s** — %s" % (cmp.get("verdict"), cmp.get("why", "")))
    add("")
    add("## 3. H3 — quality veto (grade_v5 cells only)")
    add("")
    h3 = doc["h3"]
    if h3.get("x_12") is None:
        add("**not_adjudicable** — %s" % (h3.get("reason") or "no grade document"))
    else:
        add("Gate **x/12 = %d/12**, decomposition **x/9 = %d/9**, NONE passes %s of the "
            "flagged ids; `answered_ratio` = %s; verdict **%s** (arm `%s`, source `%s`)."
            % (h3["x_12"], h3["x_9"], h3["none_passes"], _fmt(h3["answered_ratio"], 4),
               h3["verdict"], h3["arm"], os.path.basename(h3["source"]["path"])))
        add("")
        add("`contract_adherence`: %s — *%s*"
            % (h3["contract_adherence"], h3["contract_adherence_note"]))
        add("")
        mcn = h3["mcnemar"]
        if mcn.get("licensed"):
            add("McNemar (C,A): b=%s c=%s p=%s, discordant=%s (floor %s)."
                % (mcn["b"], mcn["c"], _fmt(mcn["p"], 4), mcn["discordant"], mcn["floor"]))
        else:
            add("McNemar: **refused** — %s" % (mcn.get("refusal") or "not licensed"))
        add("")
        add("NONE ids: %s" % "; ".join("`%s` in_grade=%s" % (n["id"], n["in_grade"])
                                       for n in h3["none_flagged"]))
    add("")
    add("## 4. TVS — tokens to verified success")
    add("")
    if doc["tvs"] == "UNDEFINED":
        add("**UNDEFINED** — %s" % doc.get("tvs_reason", ""))
    else:
        tvs = doc["tvs"]
        add("**%s** tokens through turn %s (checkpoint `%s`), arm `%s`, %s distinct billed "
            "rows, rows_sha256 `%s`, grader_sha256 `%s`."
            % (tvs["value"], tvs["through_turn"], tvs["checkpoint_id"], tvs["arm"],
               tvs["billed_rows"], tvs["rows_sha256"][:16], tvs["grader_sha256"][:16]))
    add("")
    add("## 5. Verbosity — before any cost line")
    add("")
    if not doc["verbosity"]["per_arm"] and doc["verbosity"].get("refusal"):
        add("**`%s`** — %s" % (doc["verbosity"]["refusal"], doc["verbosity"].get("reason", "")))
        add("")
    elif not doc["verbosity"]["per_arm"]:
        add("No arm has a row on disk: no verbosity figure is printed, and therefore no cost "
            "figure is either.")
        add("")
    else:
        add("| arm | mean completion tokens | mean answer chars | n turns | n answers | source |")
        add("|---|---|---|---|---|---|")
    for row in doc["verbosity"]["per_arm"]:
        add("| `%s` | %s | %s | %d | %d | %s |"
            % (row["arm"], _fmt(row["mean_completion_tokens"]),
               _fmt(row["mean_answer_chars"]), row["n_turns"], row["n_answers"],
               ", ".join("`%s`" % p for p in row["source_paths"])))
    add("")
    add("## 6. Spend — a delta against the frozen baseline")
    add("")
    spend = doc["spend"]
    base = spend["baseline"]
    add("baseline `%s` (sha256 `%s`): **%s** requests, remaining %s, cap %s, frozen %s."
        % (os.path.basename(base["path"]), base["sha256"][:16], base["requests"],
           base.get("remaining"), base.get("cap"), base.get("frozen_at")))
    add("")
    if spend.get("spent_now") is None:
        add("**spent_now / delta left null** — %s" % spend.get("refused"))
    else:
        add("spent_now **%s**, delta **%+d**, fits in remaining: %s."
            % (spend["spent_now"], spend["delta"], spend.get("fits_in_remaining")))
    add("")
    art = doc["price_artefact"]
    add("`price_expectation` **%s** (%s). The artefact `%s` prices it at **%s** "
        "(components %s) → matches: %s. %s"
        % (spend["price_expectation"], spend["price_expectation_source"],
           os.path.basename(art["path"]), art.get("price_total"),
           json.dumps(art.get("components")), art.get("matches_price_expectation"),
           art.get("note")))
    add("")
    add("## 7. Epochs never pooled")
    add("")
    if not doc["h1"]["grids"]:
        add("No grid was formed: every input cell was refused, so there is nothing to pool "
            "and no interval exists that could have spanned an era boundary.")
    elif doc["epochs_never_pooled"]:
        for ep in doc["epochs_never_pooled"]:
            add("- `%s` (%s): %s — files %s"
                % (ep["grid"], ep["era"], ep["reason"],
                   ", ".join("`%s`" % p for p in ep["paths"])))
    else:
        add("One grid only: nothing to keep apart, and the report says so rather than "
            "claiming a cross-era comparison it never made.")
    add("")
    add("## 8. Refusals on this run (first-class output)")
    add("")
    if doc["refusals"]:
        for rec in doc["refusals"]:
            add("- **%s** (%s): %s" % (rec["kind"], rec["scope"], rec["text"]))
    else:
        add("None: every term was obtained from its licensed estimator. That is the only "
            "state in which this report contains no refusal line.")
    add("")
    add("## 9. How the three refusal modes are proven (synthetic, no live data)")
    add("")
    add("`experiments/ptr-engine/tests/test_run_grid_report.py` builds cells under a pytest "
        "tmp dir — never under `measure/` — and pins each mode:")
    add("")
    add("| mode | synthetic cell | assertion |")
    add("|---|---|---|")
    add("| `not_adjudicable_floor` | 40 turns/arm, no lift | `verdict == not_adjudicable_floor` and the analyser's `quantile_ci` text is quoted |")
    add("| `not_adjudicable_effective_n` | 120 turns/arm, r ≈ 0.9 | `verdict == not_adjudicable_effective_n`, binding arm named with both numbers |")
    add("| `not_adjudicable_quality` | no grade document / refused McNemar | `h3.verdict == not_adjudicable`, `tvs == \"UNDEFINED\"`, never `0` |")
    add("")
    add("## 10. Reproduce")
    add("")
    add("```")
    add("python3 experiments/ptr-engine/tools/run_grid_report.py --write")
    add("# refusals included; exit 0 means emitted, 2 means nothing analysable, 3 no baseline")
    add("python3 -m pytest experiments/ptr-engine/tests/test_run_grid_report.py -q")
    add("```")
    add("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rows", action="append", default=None,
                    help="a cell rows file (repeatable); default measure/rows-cell-*.jsonl")
    ap.add_argument("--manifest", action="append", default=None,
                    help="a cell manifest (repeatable)")
    ap.add_argument("--manifest-dir", default=None, help="manifests directory")
    ap.add_argument("--sanity", default=None,
                    help="GRID-CELL-SANITY.json (default: none -- stamps then come from manifests)")
    ap.add_argument("--grade", default=None, help="a grade_v5 document (H3/TVS)")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, help="frozen ledger baseline")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="the live request ledger")
    ap.add_argument("--shape", default=DEFAULT_SHAPE, help="GRID-SHAPE.json")
    ap.add_argument("--out", default=None, help="JSON destination")
    ap.add_argument("--md", default=None, help="markdown destination")
    ap.add_argument("--write", action="store_true",
                    help="write the two declared artefacts (%s, %s)" % (OUT_JSON, OUT_MD))
    ap.add_argument("--print", dest="print_json", action="store_true",
                    help="print the JSON document")
    args = ap.parse_args(argv)

    try:
        doc = build_report(rows_paths=args.rows, manifest_paths=args.manifest,
                           manifest_dir=args.manifest_dir, sanity_path=args.sanity,
                           grade_path=args.grade, baseline_path=args.baseline,
                           ledger_path=args.ledger, shape_path=args.shape)
    except RefusedEmission as exc:
        sys.stderr.write(str(exc) + "\n")
        return 3 if exc.kind == REFUSAL_BASELINE else 2

    out_json = OUT_JSON if args.write else args.out
    out_md = OUT_MD if args.write else args.md
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=False)
            fh.write("\n")
        print("wrote %s" % out_json)
    if out_md:
        os.makedirs(os.path.dirname(os.path.abspath(out_md)), exist_ok=True)
        with open(out_md, "w", encoding="utf-8") as fh:
            fh.write(render_markdown(doc))
        print("wrote %s" % out_md)
    if args.print_json or (not out_json and not out_md):
        print(json.dumps(doc, indent=1))
    print("h1: %s" % json.dumps(doc["verdicts"]["h1"]))
    print("h2: %s | h3: %s | tvs: %s"
          % (doc["verdicts"]["h2"], doc["verdicts"]["h3"], doc["verdicts"]["tvs"]))
    print("refusals: %d" % len(doc["refusals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
