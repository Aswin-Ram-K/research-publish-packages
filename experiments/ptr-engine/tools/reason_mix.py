#!/usr/bin/env python3
"""QUALITY-REASON-MIX: why does each checkpoint check fail, per arm, per grid?

OFFLINE. Reads only grade documents already on disk under
experiments/ptr-engine/measure/*.grade-v5.json (primary) and
*.grade-v4.json (secondary, superseded). Zero inference requests, no live run,
no fixture edit, no grader edit, no rewrite of a published document.

The question this answers
-------------------------
H3 frozen margin: `pointer-stable` beats `transcript-grow` on checkpoints by a
2-of-12 margin.  If the non-pointer failures are *wrong values*, the margin
compares pointer mechanics.  If they are *no answer line at all*, it compares
answer production.  If they are *right value, wrong shape*, it compares prompt
contract compliance.  The three are not interchangeable, and the published
headline cannot tell them apart because it collapses every non-pass into "fail".

Buckets (exactly one per non-pass cell)
--------------------------------------
never_answered                     the grader found no answer to grade
answered_wrong_value               a value was parsed and compared; it was wrong
answered_right_but_rejected_by_contract
                                   value/provenance looked right, a shape rule failed
undecidable                        the grader refused to decide (no verdict at all)
other:<name>                       named, not forced into a bucket
unclassifiable                     the document does not determine a bucket

Mapping rules are in REASON_BUCKET below, and every row carries the grader's
own `reason` string verbatim so the mapping can be audited without the document.
"""

import argparse
import glob
import json
import os
import sys
from collections import Counter, OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")

# ---------------------------------------------------------------------------
# Mapping rules. Keyed on the reason string the grader itself wrote - never on
# a re-derivation of the verdict. `:suffix` reasons are matched on their head.
# ---------------------------------------------------------------------------
REASON_BUCKET = {
    # --- v5 (grade_v5) ------------------------------------------------------
    "turn_missing": "never_answered",              # row absent at that turn
    "prose_only": "never_answered",                # content, no contract line
    "no_answer_line": "never_answered",
    "empty_answer": "never_answered",
    "empty_text": "never_answered",
    "empty_num": "never_answered",
    "prose_sentinel": "never_answered",
    "answer_not_contract": "answered_right_but_rejected_by_contract",
    "not_a_contract_form": "answered_right_but_rejected_by_contract",
    "multiple_answer_lines": "answered_right_but_rejected_by_contract",
    "row_fields_disagree_with_content":
        "answered_right_but_rejected_by_contract",
    # --- v4 (grade_v4), secondary/superseded -------------------------------
    "marker_missing": "never_answered",            # no ANSWER: marker at all
    "marker_without_value": "never_answered",       # marker, sentinel value
    "preamble_only": "never_answered",
    "truncated_without_value": "never_answered",
    "number_wrong": "answered_wrong_value",
    "missing_anchor": "answered_wrong_value",       # unit card: bucket 2
    "keyword_missing": "answered_wrong_value",
    "callee_mismatch": "answered_wrong_value",
    "keyword_mismatch": "answered_wrong_value",
    "value_not_in_concluding_position": "answered_wrong_value",
    # --- explicitly `other` -------------------------------------------------
    "refused_while_knowable": "other:refused_while_knowable",
    "repair_not_acknowledged": "other:repair_not_acknowledged",
    "unverifiable": "undecidable",
    "ok": None,  # a pass, never bucketed
}

# `unparseable` is the one reason the unit card lists in bucket 3 but whose
# cells are not all shape failures. Rule, applied per cell and reported:
#   answer_raw is the runner's no-answer sentinel, or absent -> never_answered
#   otherwise the text was there and could not be parsed -> contract bucket 3
SENTINELS = ("ANSWER: NOT-AN-ANSWER", "NOT-AN-ANSWER", "ANSWER: NONE")

# Grade documents written before Repair T3 (2026-10-26T15:56Z) used a grader
# in which a non-answer was `fail` and `not_a_contract_form` existed as a parse
# error; the on-disk grade_v5.py has neither. Pooling the two eras would confound
# a grader-version change with an arm difference, so every table is era-split.
T3_BOUNDARY = "2026-10-26T15:56"


def era_of(generated_at):
    return "pre-T3" if str(generated_at or "") < T3_BOUNDARY else "T3"


def head(reason):
    return (reason or "").split(":", 1)[0]


def classify(verdict, reason, answer_raw, parse_error=None):
    """-> (bucket, note). Never guesses: unknown reasons come back unclassifiable."""
    reason = reason or ""
    if verdict == "pass":
        return None, ""
    if verdict not in ("pass", "fail", "text", "undecidable"):
        return "undecidable", "no verdict recorded (pass: null): %r" % verdict
    if verdict == "undecidable" and not reason:
        return "undecidable", "undecidable with no reason"
    h = head(reason)
    raw = (answer_raw or "").strip()
    if h == "unparseable":
        if raw == "" or raw in SENTINELS:
            return "never_answered", (
                "reason %r but answer_raw is the no-answer sentinel/empty %r"
                % (reason, raw))
        return "answered_right_but_rejected_by_contract", (
            "reason %r with parseable-but-off-contract text" % reason)
    bucket = REASON_BUCKET.get(h)
    if bucket is None:
        return "unclassifiable", "reason %r not in REASON_BUCKET" % reason
    note = ""
    # A cell whose reason and parse error disagree keeps the reason-based
    # bucket (the reason is the document of record) and is FLAGGED, then
    # counted in the sensitivity table.
    if (parse_error and h == "answer_not_contract"
            and parse_error in ("no_answer_line", "prose_only")):
        note = ("reason %r disagrees with answer_parse_error %r; kept on reason"
                % (reason, parse_error))
    return bucket, note


# ---------------------------------------------------------------------------
# Document readers
# ---------------------------------------------------------------------------
def grid_name(rows_file):
    return os.path.basename(str(rows_file or "?"))


def is_demo(grid):
    """Grids whose rows file is not under measure/ - the self-test fixtures."""
    return not grid.startswith("rows-longrun-")


def read_v5(path):
    doc = json.load(open(path))
    grid = grid_name(doc.get("rows_file"))
    era = era_of(doc.get("generated_at"))
    out = []
    for c in doc.get("cells") or []:
        bucket, note = classify(c.get("verdict"), c.get("reason"),
                                c.get("answer_raw"), c.get("answer_parse_error"))
        out.append(OrderedDict(
            grid=grid, arm=c.get("arm"), checkpoint_id=c.get("id"),
            turn=c.get("turn"), verdict=c.get("verdict"),
            reason=c.get("reason"), answer_parse_error=c.get("answer_parse_error"),
            answer_raw=c.get("answer_raw"), bucket=bucket, note=note,
            source=os.path.basename(path), grader="grade_v5", era=era,
            generated_at=doc.get("generated_at")))
    return grid, out


def read_v4(path):
    doc = json.load(open(path))
    grid = grid_name(doc.get("rows_file"))
    era = era_of(doc.get("generated_at"))
    out = []
    for arm, av in sorted((doc.get("arms") or {}).items()):
        for c in av.get("checks") or []:
            cid = c.get("id") or ""
            if not cid.startswith("cp."):
                continue  # acc.n3b / repair.t30 are not v5 checkpoint cells
            verdict = "pass" if c.get("pass") else "fail"
            bucket, note = classify(verdict, c.get("reason"),
                                    c.get("found_excerpt"),
                                    c.get("detail") or None)
            out.append(OrderedDict(
                grid=grid, arm=arm, checkpoint_id=cid, turn=c.get("turn"),
                verdict=verdict, reason=c.get("reason"),
                answer_parse_error=None, answer_raw=c.get("found_excerpt"),
                bucket=bucket, note=note, source=os.path.basename(path),
                grader="grade_v4", era=era,
                generated_at=doc.get("generated_at")))
    return grid, out


def load_all():
    """v5 is primary wherever it exists; v4 files are the superseded view."""
    v5, v4 = [], []
    for p in sorted(glob.glob(os.path.join(MEASURE, "*.grade-v5.json"))):
        v5.append(read_v5(p))
    v4 = []
    for p in sorted(glob.glob(os.path.join(MEASURE, "*.grade-v4.json"))):
        v4.append(read_v4(p))
    return v5, v4


# ---------------------------------------------------------------------------
# Arm-blindness probe: is the grader reading the arm label?
# ---------------------------------------------------------------------------
def arm_blindness_probe():
    """Feed ONE answer text through grade_v5 twice, under two arm labels.

    Offline and in memory: no rows file is read, no fixture or grader is edited.
    If the verdict/reason pair is identical for both labels, the grader is
    arm-blind by construction and an arm difference can only come from what the
    arm's own rows said.
    """
    sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine", "longrun"))
    here = os.getcwd()
    try:
        os.chdir(os.path.join(ROOT, "experiments", "ptr-engine", "longrun"))
        import grade_v5  # noqa: E402
    finally:
        os.chdir(here)
    fixture = grade_v5.load_fixture(os.path.join(
        ROOT, "experiments", "ptr-engine", "longrun", "tasks-v5", "runtime-v5",
        "LR-01.v5.json"))

    cases = [
        ("accepted_by_pointer", {12: "ANSWER: 64", 24: "ANSWER: 31",
                                 46: "ANSWER: CALL ledger.record_refusal("
                                     "code=error.code, scope=scope_name, "
                                     "serialized_ref=text)"}),
        ("rejected_as_not_a_contract_form", {12: "ANSWER: 64", 24: "ANSWER: 31",
                                            46: "ANSWER: ledger.record_refusal("
                                                "scope=scope_name, "
                                                "serialized_ref=text, "
                                                "code=error.code)"}),
    ]
    res = []
    for name, by_turn in cases:
        runs = {}
        for arm in ("pointer-stable", "transcript-grow"):
            rows = [{"arm": arm, "turn": t, "content": txt,
                     "row": 0, "arm_turn": 0}
                    for t, txt in sorted(by_turn.items())]
            doc = grade_v5.grade_rows(fixture, rows)
            runs[arm] = [(c["id"], c["verdict"], c.get("reason"))
                         for c in doc["cells"]]
        identical = runs["pointer-stable"] == runs["transcript-grow"]
        res.append({"case": name, "answers": by_turn,
                    "verdicts_by_arm": runs, "identical_for_both_arms": identical,
                    "pointer_verdicts": runs["pointer-stable"]})
    return res


# ---------------------------------------------------------------------------
def summarise(rows):
    cells = [r for r in rows]
    passes = [r for r in cells if r["verdict"] == "pass"]
    return cells, passes


def bucket_table(rows, arm_groups):
    tab = OrderedDict((g, Counter()) for g in arm_groups)
    order = ["never_answered", "answered_wrong_value",
             "answered_right_but_rejected_by_contract", "undecidable",
             "unclassifiable"]
    for r in rows:
        if r["verdict"] == "pass":
            continue
        for g, members in arm_groups.items():
            if r["arm"] in members:
                b = r["bucket"] or "unclassifiable"
                if b not in order and not b.startswith("other:"):
                    b = "unclassifiable"
                tab[g][b] += 1
    tot = Counter()
    for g in tab:
        tot.update(tab[g])
    return tab, tot, order


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(MEASURE, "QUALITY-REASON-MIX.json"))
    ap.add_argument("--no-probe", action="store_true")
    args = ap.parse_args(argv)

    v5docs, v4docs = load_all()
    v5rows = [r for _, rs in v5docs for r in rs]
    v4rows = [r for _, rs in v4docs for r in rs]

    grids_v5 = sorted({r["grid"] for r in v5rows})
    arms_v5 = sorted({r["arm"] for r in v5rows})

    # v6/pointer-only cell docs repeat a grid already covered by a wider doc;
    # every (grid, arm, checkpoint) must appear once. Detect duplicates.
    seen = Counter((r["grid"], r["arm"], r["checkpoint_id"]) for r in v5rows)
    dups = {("%s|%s|%s" % k): v for k, v in seen.items() if v > 1}

    arm_groups = OrderedDict([
        ("pointer-stable", {"pointer-stable"}),
        ("other-three-arms", set(arms_v5) - {"pointer-stable"}),
    ])
    tab, tot, order = bucket_table(v5rows, arm_groups)

    # real grids only (demo fixtures excluded from the H3 arithmetic)
    real = [r for r in v5rows if not is_demo(r["grid"])]
    demo = [r for r in v5rows if is_demo(r["grid"])]
    rtab, rtot, _ = bucket_table(real, arm_groups)

    # Primary population: current-era (T3) documents on real grids only.
    primary = [r for r in v5rows if r["era"] == "T3" and not is_demo(r["grid"])]
    ptab, ptot, _ = bucket_table(primary, arm_groups)
    pre = [r for r in v5rows if r["era"] == "pre-T3"]
    pretab, pretot, _ = bucket_table(pre, arm_groups)

    nonpointer = [r for r in primary
                  if r["verdict"] != "pass" and r["arm"] != "pointer-stable"]
    np_b3 = sum(1 for r in nonpointer
                if r["bucket"] == "answered_right_but_rejected_by_contract")
    np_b2 = sum(1 for r in nonpointer if r["bucket"] == "answered_wrong_value")
    all_np_b2 = sum(1 for r in v5rows if r["verdict"] != "pass"
                    and r["arm"] != "pointer-stable"
                    and r["bucket"] == "answered_wrong_value")
    all_b2 = sum(1 for r in v5rows if r["bucket"] == "answered_wrong_value")

    # sensitivity: the one cell whose reason contradicts its parse error
    sens = [r for r in v5rows if r.get("note") and "disagrees" in r["note"]]

    # v4 cross-tab: same (grid,arm,checkpoint), both graders on disk
    v5idx = {(r["grid"], r["arm"], r["checkpoint_id"]): r for r in v5rows}
    cross = Counter()
    for r in v4rows:
        k = (r["grid"], r["arm"], r["checkpoint_id"])
        v5r = v5idx.get(k)
        cross[(r["reason"], "PASS" if r["verdict"] == "pass" else r["bucket"],
               (v5r["reason"] if v5r else "not_a_v5_cell"))] += 1
    demoted = [
        {"grid": r["grid"], "arm": r["arm"], "checkpoint_id": r["checkpoint_id"],
         "v4_reason": r["reason"], "v5_reason": v5idx[(r["grid"], r["arm"],
                                                       r["checkpoint_id"])]["reason"],
         "v5_answer_raw": v5idx[(r["grid"], r["arm"],
                                 r["checkpoint_id"])]["answer_raw"],
         "source": v5idx[(r["grid"], r["arm"],
                          r["checkpoint_id"])]["source"]}
        for r in v4rows
        if r["verdict"] == "pass"
        and (r["grid"], r["arm"], r["checkpoint_id"]) in v5idx
        and v5idx[(r["grid"], r["arm"], r["checkpoint_id"])]["verdict"] != "pass"
    ]

    probe = [] if args.no_probe else arm_blindness_probe()

    doc = OrderedDict()
    doc["unit"] = "QUALITY-REASON-MIX"
    doc["live_requests"] = 0
    doc["network"] = False
    doc["scope"] = {
        "grade_v5_files": [os.path.basename(p) for p in
                           sorted(glob.glob(os.path.join(MEASURE, "*.grade-v5.json")))],
        "grade_v4_files": [os.path.basename(p) for p in
                           sorted(glob.glob(os.path.join(MEASURE, "*.grade-v4.json")))],
        "n_grade_v5_files": len(v5docs),
        "n_grade_v4_files": len(v4docs),
        "n_cells_v5": len(v5rows),
        "n_cells_v4_cp_only": len(v4rows),
        "grids_v5": grids_v5,
        "n_grids_v5": len(grids_v5),
        "arms_v5": arms_v5,
        "demo_grids": sorted({r["grid"] for r in demo}),
        "duplicate_cells": dups,
    }
    doc["mapping_rules"] = {
        "source_of_truth": "the grader's own `reason` string, quoted verbatim",
        "never_answered": ["turn_missing", "prose_only", "no_answer_line",
                           "empty_answer", "empty_text", "empty_num",
                           "marker_missing", "marker_without_value",
                           "preamble_only", "truncated_without_value"],
        "answered_wrong_value": ["number_wrong:*", "missing_anchor:*",
                                 "keyword_missing", "callee_mismatch",
                                 "keyword_mismatch",
                                 "value_not_in_concluding_position"],
        "answered_right_but_rejected_by_contract": [
            "answer_not_contract", "answer_not_contract:multiple_answer_lines",
            "not_a_contract_form", "multiple_answer_lines",
            "row_fields_disagree_with_content",
            "unparseable (only when answer_raw is not the no-answer sentinel)"],
        "undecidable": ["verdict not in {pass,fail,text,undecidable}: pass null",
                        "unverifiable"],
        "other": ["refused_while_knowable", "repair_not_acknowledged"],
        "unparseable_rule": (
            "reason `unparseable` with answer_raw == 'ANSWER: NOT-AN-ANSWER' "
            "(runner no-answer sentinel) or empty -> never_answered; with real "
            "text -> answered_right_but_rejected_by_contract"),
    }
    doc["rows"] = v5rows
    doc["bucket_table_all_grids"] = OrderedDict(
        (g, OrderedDict((b, tab[g][b]) for b in order)) for g in tab)
    doc["bucket_totals_all_grids"] = OrderedDict((b, tot[b]) for b in order)
    doc["bucket_table_real_grids_only"] = OrderedDict(
        (g, OrderedDict((b, rtab[g][b]) for b in order)) for g in rtab)
    doc["bucket_totals_real_grids_only"] = OrderedDict((b, rtot[b]) for b in order)
    doc["bucket_table_primary_T3_real"] = OrderedDict(
        (g, OrderedDict((b, ptab[g][b]) for b in order)) for g in ptab)
    doc["bucket_totals_primary_T3_real"] = OrderedDict((b, ptot[b]) for b in order)
    doc["bucket_table_pre_T3"] = OrderedDict(
        (g, OrderedDict((b, pretab[g][b]) for b in order)) for g in pretab)
    doc["bucket_totals_pre_T3"] = OrderedDict((b, pretot[b]) for b in order)
    doc["primary_population"] = OrderedDict(
        rule="grade_v5 documents generated at/after 2026-10-26T15:56Z, rows-longrun-*.jsonl grids only",
        n_cells=len(primary),
        sources=sorted({r["source"] for r in primary}),
        pointer_stable_passes=sum(1 for r in primary if r["arm"] == "pointer-stable"
                                  and r["verdict"] == "pass"),
        non_pointer_non_passes=len(nonpointer),
        all_cells_answered_wrong_value=all_b2)
    doc["per_arm"] = OrderedDict()
    for arm in arms_v5:
        rs = [r for r in v5rows if r["arm"] == arm]
        doc["per_arm"][arm] = OrderedDict(
            cells=len(rs),
            passed=sum(1 for r in rs if r["verdict"] == "pass"),
            non_pass=sum(1 for r in rs if r["verdict"] != "pass"),
            buckets=OrderedDict((b, sum(1 for r in rs if r["bucket"] == b))
                                for b in order),
            pass_cells=[OrderedDict(grid=r["grid"], checkpoint_id=r["checkpoint_id"],
                                    answer_raw=r["answer_raw"], reason=r["reason"],
                                    source=r["source"])
                        for r in rs if r["verdict"] == "pass"])
    doc["headline_numbers"] = OrderedDict(
        pointer_stable_passes=sum(1 for r in v5rows
                                  if r["arm"] == "pointer-stable"
                                  and r["verdict"] == "pass"),
        non_pointer_non_passes=len(nonpointer),
        bucket2_answered_wrong_value=np_b2,
        bucket3_contract=np_b3,
        bucket3_share_of_non_pointer_failures=(
            "%.1f%% (%d/%d)" % (100.0 * np_b3 / len(nonpointer), np_b3,
                                len(nonpointer)) if nonpointer else "n/a"),
        bucket3_share_numerator=np_b3, bucket3_share_denominator=len(nonpointer),
        threshold_pct=60.0,
        threshold_met=bool(nonpointer and 100.0 * np_b3 / len(nonpointer) >= 60.0),
        _scope="primary population: T3-era, real grids only",
        all_cells_answered_wrong_value=all_b2,
        all_cells_never_answered=sum(1 for r in v5rows
                                     if r["bucket"] == "never_answered"),
        all_non_passes=sum(1 for r in v5rows if r["verdict"] != "pass"),
    )
    doc["reason_disagreement_cells"] = sens
    # sensitivity: the unit card's LITERAL reading of bucket 3 (all `unparseable`
    # -> contract rejection, sentinel or not). Reported, never used for the verdict.
    lit = []
    for r in v5rows:
        b = r["bucket"]
        if r["verdict"] != "pass" and head(r["reason"]) == "unparseable":
            b = "answered_right_but_rejected_by_contract"
        lit.append((r, b))
    lit_np = [(r, b) for r, b in lit
              if r["verdict"] != "pass" and r["arm"] != "pointer-stable"
              and r["era"] == "T3" and not is_demo(r["grid"])]
    lit_b3 = sum(1 for r, b in lit_np
                 if b == "answered_right_but_rejected_by_contract")
    doc["sensitivity_literal_unparseable_bucket3"] = OrderedDict(
        rule="all `unparseable` cells counted as contract rejections, sentinel or not",
        all_cells_bucket3=sum(1 for r, b in lit
                              if b == "answered_right_but_rejected_by_contract"),
        all_non_passes=sum(1 for r, b in lit if r["verdict"] != "pass"),
        primary_non_pointer_bucket3=lit_b3,
        primary_non_pointer_non_passes=len(lit_np),
        share=("%.1f%% (%d/%d)" % (100.0 * lit_b3 / len(lit_np), lit_b3,
                                   len(lit_np)) if lit_np else "n/a"),
        threshold_met=bool(lit_np and 100.0 * lit_b3 / len(lit_np) >= 60.0))
    doc["v4_vs_v5_cross_tab"] = OrderedDict(
        ("%s | v4=%s | v5=%s" % k, v) for k, v in
        sorted(cross.items(), key=lambda kv: -kv[1]))
    doc["cells_demoted_v4_pass_to_v5_fail"] = demoted
    doc["arm_blindness_probe"] = probe
    doc["unclassifiable"] = [r for r in v5rows
                             if r["bucket"] == "unclassifiable"]

    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")

    # ---- console report ---------------------------------------------------
    print("grids(v5)=%d cells=%d arms=%s" % (len(grids_v5), len(v5rows), arms_v5))
    print("duplicates:", dups or "none")
    hdr = "%-46s %s" % ("arm class", "  ".join("%-8s" % b[:8] for b in order))
    print(hdr)
    for g in tab:
        print("%-46s %s" % (g, "  ".join("%-8d" % tab[g][b] for b in order)))
    print("%-46s %s" % ("TOTAL", "  ".join("%-8d" % tot[b] for b in order)))
    print("real-grids-only totals:",
          dict((b, rtot[b]) for b in order))
    print("PRIMARY (T3 era, real grids) n=%d" % len(primary))
    for g in ptab:
        print("  %-20s %s" % (g, "  ".join("%-8d" % ptab[g][b] for b in order)))
    print("  %-20s %s" % ("TOTAL", "  ".join("%-8d" % ptot[b] for b in order)))
    print("PRE-T3 (superseded grader) n=%d totals=%s"
          % (len(pre), dict((b, pretot[b]) for b in order)))
    print("headline:", json.dumps(doc["headline_numbers"]))
    for arm, blk in doc["per_arm"].items():
        print("  %-19s cells=%2d pass=%d non_pass=%2d %s"
              % (arm, blk["cells"], blk["passed"], blk["non_pass"],
                 dict((k, v) for k, v in blk["buckets"].items() if v)))
    print("unclassifiable:", len(doc["unclassifiable"]))
    for p in probe:
        print("probe %-34s arm-blind=%s -> %s"
              % (p["case"], p["identical_for_both_arms"],
                 p["pointer_verdicts"]))
    print("demoted v4 pass -> v5 fail:", [d["checkpoint_id"] + " " + d["v5_reason"]
                                          for d in demoted])
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
