#!/usr/bin/env python3
"""NEVER-ANSWERED-ROOT-2 -- explain the 63 never_answered cells FROM THE TURN TEXT.

Population: the 63 `never_answered` checkpoint cells of QUALITY-REASON-MIX.json
(era T3, real `rows-longrun-*` grids). For every cell this opens the rows file
read-only, takes the last row for (arm, turn) exactly as grade_v5 does
(`by_turn = {turn: row}`), and buckets it with the unit-card vocabulary:

  turn_absent          no row for that (arm, turn)
  empty_completion     row exists, completion_tokens == 0 or content == ""
  cap_hit              completion_tokens at the ceiling (max_tokens, or the
                       stage-1 128-token cap) / truncated / finish_reason length
  reasoning_only       content empty, reasoning non-empty
  tool_loop            only kind=tool-followup rows, no final assistant text
  prose_asserts_value  substantive prose that STATES a number or a call, with
                       no `^ANSWER:` line
  prose_other          substantive prose with no asserted value
  no_answer_no_prose   content present but nothing substantive (tool-call or
                       pointer noise only)

`prose_asserts_value` is checked against the checkpoint truth (grade doc
`truth[].expected`) and recorded right/wrong.

Read-only. Emits measure/NEVER-ANSWERED-ROOT.json. No network, no requests.

Usage: python3 never_answered.py [--print] [--json OUT]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
REGRADE = os.path.join(MEASURE, "regrade")
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")

ANSWER_LINE = re.compile(r"^ANSWER:[ ]*\S.*$", re.MULTILINE)
NUMERAL = re.compile(r"(?<![\w.@])\d+(?:\.\d+)?(?![\w.@])")
POINTER = re.compile(r"@knowledge:[^@\s]+@\d+")
TOOLCALL = re.compile(r"<tool_call>.*?(?:</tool_call>|$)", re.DOTALL)
FENCE = re.compile(r"```.*?(?:```|$)", re.DOTALL)
COPULA = re.compile(r"\b(is|are|was|were|equals?|amounts? to|totals?|defines?|"
                    r"returns?|default|budget)\b", re.I)
FILE_EXT = ("py", "json", "jsonl", "md", "txt", "sh", "yaml", "yml", "toml",
            "lock", "js", "ts", "html", "cfg", "ini", "csv")
CALL_EXPR = re.compile(r"\b([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\(")
CALLEE_TRUE = "ledger.record_refusal"
# numerals that are file/line references, byte sizes, or pointers -- not answers
REF_NOISE = [
    re.compile(r"#?L\d+(?:\s*[-\u2013]\s*L?\d+)?"),
    re.compile(r"\blines?\s+\d+(?:\s*[-\u2013]\s*\d+)?", re.I),
    re.compile(r"\b\d+\s*(?:B|bytes?)\b"),
    re.compile(r"\b\d+\.\d+\b"),
]

BUCKETS = ["turn_absent", "empty_completion", "cap_hit", "reasoning_only",
           "tool_loop", "prose_asserts_value", "prose_other", "no_answer_no_prose"]

STAGE1_CAP = 128  # run_longrun.py:2698 -- Stage 1 capped every completion at 128


def load_rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def rows_path_for(doc):
    rel = doc.get("rows_file") or ""
    names = [os.path.join(ROOT, rel), os.path.join(MEASURE, os.path.basename(rel)),
             os.path.join(ROOT, "experiments", "ptr-engine", rel)]
    for c in names:
        if os.path.isfile(c):
            return c
    return None


def fixture_index():
    """sha256 -> fixture path, for every fixture-shaped json under longrun/."""
    idx = {}
    for dirpath, _dirs, files in os.walk(LONGRUN):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, "rb") as fh:
                    idx[hashlib.sha256(fh.read()).hexdigest()] = p
            except OSError:
                continue
    return idx


def fixture_contract(path):
    """(answer_marker_required, fixture_version, path) or (None, None, path)."""
    if not path:
        return None, None, None
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None, None, path
    am = d.get("answer_marker")
    req = None
    if isinstance(am, dict):
        req = bool(am.get("required"))
    elif am is None:
        req = False
    return req, d.get("fixture_version"), path


def prose_zone(content):
    """Content with tool-call blocks, fenced code and pointer handles removed."""
    z = TOOLCALL.sub(" ", content)
    z = FENCE.sub(" ", z)
    z = POINTER.sub(" ", z)
    return z


def prose_clean(content):
    """Prose zone with line/byte references removed before numeral extraction."""
    z = prose_zone(content)
    for rx in REF_NOISE:
        z = rx.sub(" ", z)
    return z


def substantive_words(text):
    return len(re.findall(r"[A-Za-z]{2,}", text))


def assert_value(zone, content):
    """Return (asserted numerals, asserted call text?, evidence sentence)."""
    nums, evidence, bare = [], "", ""
    stripped = content.strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
        return [stripped], None, "bare numeral: " + stripped
    for sent in re.split(r"(?<=[.!?])\s+|\n+", zone):
        found = NUMERAL.findall(sent)
        if not found:
            continue
        if COPULA.search(sent):
            nums.extend(found)
            if not evidence:
                evidence = sent.strip()[:220]
    first = next((ln.strip() for ln in content.splitlines() if ln.strip()), "")
    if re.fullmatch(r"-?\d+(?:\.\d+)?", first) and first not in nums:
        nums.insert(0, first)
        evidence = evidence or ("leading numeral: " + first)
    call = None
    for m in CALL_EXPR.finditer(zone):
        if m.group(2) in FILE_EXT:
            continue
        call = m.group(0).rstrip("(")
        break
    if call and not evidence:
        evidence = call
    return nums, call, evidence


def to_float(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def judge_assertion(nums, call, kind, expected):
    """('right'|'wrong'|'unknown', asserted values as written)."""
    asserted = list(nums)
    if call:
        asserted = asserted + [call]
    kind = (kind or "").upper()
    if kind == "CALL":
        if not call:
            return "unknown", asserted
        truth_callee = (expected or {}).get("callee") if isinstance(expected, dict) else None
        if truth_callee and truth_callee in call:
            return "right", asserted
        return "wrong", asserted
    exp = to_float(expected)
    if exp is None or not asserted:
        return "unknown", asserted
    vals = [(v, to_float(v)) for v in asserted]
    if any(v is not None and abs(v - exp) < 1e-9 for _s, v in vals):
        return "right", asserted
    return "wrong", asserted


def classify(row, per_turn):
    """Return (bucket-or-None, detail). Every decision is read off the row text."""
    if row is None:
        return "turn_absent", {
            "row_kind_set": [], "content": "", "reasoning_chars": 0,
            "completion_tokens": None, "max_tokens": None, "truncated": None,
            "finish_reason": None, "thinking": None, "reasoning_head": "",
            "n_rows_for_turn": 0,
        }
    content = row.get("content") or ""
    reasoning = row.get("reasoning") or row.get("reasoning_content") or ""
    try:
        ct = int(row.get("completion_tokens") or 0)
    except (TypeError, ValueError):
        ct = 0
    raw_mt = row.get("max_tokens")
    try:
        mt = int(raw_mt) if raw_mt not in (None, "", "None") else None
    except (TypeError, ValueError):
        mt = None
    trunc = str(row.get("truncated")) == "True"
    fin = row.get("finish_reason")
    detail = {
        "row_kind_set": sorted({str(r.get("kind")) for r in per_turn}),
        "content": content,
        "reasoning_chars": len(reasoning),
        "reasoning_head": reasoning[:300],
        "completion_tokens": ct,
        "max_tokens": mt,
        "truncated": trunc,
        "finish_reason": fin,
        "thinking": row.get("thinking"),
        "n_rows_for_turn": len(per_turn),
    }
    stripped = content.strip()
    if stripped == "" and reasoning.strip() != "":
        return "reasoning_only", detail
    if ct == 0 or stripped == "":
        return "empty_completion", detail
    # stage-1 runner wrote no max_tokens field and stopped at 128 tokens
    at_stage1_cap = (mt is None and ct == STAGE1_CAP and fin in (None, "None", ""))
    if (mt is not None and ct >= mt) or trunc or fin == "length" or at_stage1_cap:
        return "cap_hit", detail
    if detail["row_kind_set"] == ["tool-followup"]:
        return "tool_loop", detail
    zone = prose_zone(content)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
        return None, detail  # a bare numeral IS a stated value
    if substantive_words(zone) == 0:
        return "no_answer_no_prose", detail
    return None, detail  # prose verdict needs the checkpoint truth -> main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(MEASURE, "NEVER-ANSWERED-ROOT.json"))
    ap.add_argument("--print", dest="do_print", action="store_true")
    args = ap.parse_args()

    mix = json.load(open(os.path.join(MEASURE, "QUALITY-REASON-MIX.json"),
                         encoding="utf-8"))
    cells = [r for r in mix["rows"]
             if r.get("bucket") == "never_answered" and r.get("era") == "T3"]
    assert len(cells) == 63, len(cells)

    fx_idx = fixture_index()
    doc_cache, rows_cache, contract_cache = {}, {}, {}
    out_rows = []
    for cell in cells:
        src = cell["source"]
        if src not in doc_cache:
            doc_cache[src] = json.load(open(os.path.join(MEASURE, src),
                                            encoding="utf-8"))
        doc = doc_cache[src]
        rp = rows_path_for(doc)
        if rp not in rows_cache:
            rows_cache[rp] = load_rows(rp)
        rows = rows_cache[rp]
        arm, turn, cid = cell["arm"], int(cell["turn"]), cell["checkpoint_id"]

        arows = [r for r in rows if r.get("arm") == arm]
        per_turn = [r for r in arows if int(r.get("turn", -1)) == turn]
        row = per_turn[-1] if per_turn else None
        bucket, detail = classify(row, per_turn)

        truth = next((t for t in doc.get("truth") or [] if t.get("id") == cid), {})
        expected = truth.get("expected")
        kind = truth.get("kind")

        zone = prose_zone(detail["content"])
        nums, call, evidence = assert_value(prose_clean(detail["content"]),
                                            detail["content"])
        verdict, asserted = judge_assertion(nums, call, kind, expected)
        if bucket is None:
            bucket = "prose_asserts_value" if (nums or call) else "prose_other"
        marker_present = bool(ANSWER_LINE.search(detail["content"]))

        # fixture contract, from the rows' own fixture_sha256 (fallback: doc)
        shas = sorted({str(r.get("fixture_sha256")) for r in arows
                       if r.get("fixture_sha256")})
        fx_path = fx_idx.get(shas[0]) if shas else None
        if fx_path not in contract_cache:
            contract_cache[fx_path] = fixture_contract(fx_path)
        freqs, fver, fpath = contract_cache[fx_path]
        if freqs is None and doc.get("fixture_file"):
            freqs, fver, fpath = fixture_contract(
                os.path.join(ROOT, doc["fixture_file"]))

        era = "stage1_128_cap" if (row is not None and row.get("max_tokens")
                                   in (None, "", "None")) else "post_128_cap"

        out_rows.append({
            "grid": cell["grid"], "arm": arm, "checkpoint": cid, "turn": turn,
            "bucket": bucket,
            "row_kind_set": detail["row_kind_set"],
            "completion_tokens": detail["completion_tokens"],
            "max_tokens": detail["max_tokens"],
            "content_chars": len(detail["content"]),
            "numeral_present": nums,
            "numerals_raw": sorted({n for n in NUMERAL.findall(
                POINTER.sub(" ", detail["content"]))}, key=lambda x: (len(x), x))[:8],
            "carries_64": bool(re.search(r"(?<![\d.])64(?![\d.])",
                                         POINTER.sub(" ", detail["content"]))),
            "asserted_values": asserted,
            "asserted_call": call,
            "assertion_evidence": evidence,
            "assertion_verdict": verdict if (nums or call) else "none",
            "asserts_value": bool(nums or call),
            "answer_marker_present": marker_present,
            "checkpoint_kind": kind,
            "checkpoint_truth": expected,
            "finish_reason": detail["finish_reason"],
            "truncated": detail["truncated"],
            "thinking": detail["thinking"],
            "reasoning_chars": detail["reasoning_chars"],
            "reasoning_head": detail["reasoning_head"],
            "n_rows_for_turn": detail["n_rows_for_turn"],
            "grader_reason": cell["reason"],
            "grader_bucket": cell["bucket"],
            "grader_verdict": cell["verdict"],
            "era": era,
            "fixture_sha256": shas[0] if shas else None,
            "fixture_path": os.path.relpath(fpath, ROOT) if fpath else None,
            "fixture_version": fver,
            "fixture_answer_marker_required": freqs,
            "rows_file": os.path.relpath(rp, ROOT),
            "grade_doc": src,
            "cap_hit_asserts": bool((nums or call)) if bucket == "cap_hit" else False,
        "answer_text": detail["content"][:600],
            "answer_text_chars": len(detail["content"]),
        })

    def tally(key):
        t = collections.defaultdict(collections.Counter)
        for r in out_rows:
            t[r[key]][r["bucket"]] += 1
        return {k: {b: c.get(b, 0) for b in BUCKETS} for k, c in sorted(t.items())}

    totals = collections.Counter(r["bucket"] for r in out_rows)

    # ---- prose assertion correctness --------------------------------------
    prose = [r for r in out_rows if r["bucket"] == "prose_asserts_value"]
    wrong = [r for r in prose if r["assertion_verdict"] == "wrong"]
    right = [r for r in prose if r["assertion_verdict"] == "right"]
    cap_assert = [r for r in out_rows if r["bucket"] == "cap_hit" and r["asserts_value"]]

    # ---- discriminators ----------------------------------------------------
    era_split = tally("era")
    contract_split = collections.defaultdict(collections.Counter)
    for r in out_rows:
        contract_split["marker_required=%s" % r["fixture_answer_marker_required"]][
            r["bucket"]] += 1
    grid_key = collections.defaultdict(collections.Counter)
    for r in out_rows:
        k = "%s | %s | marker_required=%s" % (
            r["grid"], r["era"], r["fixture_answer_marker_required"])
        grid_key[k][r["bucket"]] += 1
    # arm within one grid and one era
    ridge_arm = collections.defaultdict(collections.Counter)
    for r in out_rows:
        ridge_arm["%s | %s" % (r["grid"], r["era"])][r["arm"]] += 1

    # ---- v4 / v5 seam ------------------------------------------------------
    v4_docs = {}
    for d in (MEASURE, REGRADE):
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.endswith(".grade-v4.json"):
                v4_docs[name] = json.load(open(os.path.join(d, name),
                                               encoding="utf-8"))

    def v4_check(rows_file, arm, cid):
        base = os.path.basename(rows_file or "")
        for name, d in v4_docs.items():
            if os.path.basename(d.get("rows_file") or "") != base:
                continue
            checks = ((d.get("arms") or {}).get(arm) or {}).get("checks") or []
            for c in checks:
                if c.get("id") == cid:
                    return name, c
        return None, None

    seam = []
    for r in out_rows:
        vname, vc = v4_check(r["rows_file"], r["arm"], r["checkpoint"])
        if vc is None:
            continue
        seam.append({
            "grid": r["grid"], "arm": r["arm"], "checkpoint": r["checkpoint"],
            "turn": r["turn"],
            "v4_doc": vname, "v4_pass": vc.get("pass"), "v4_reason": vc.get("reason"),
            "v4_found_excerpt": (vc.get("found_excerpt") or "")[:300],
            "v5_bucket": r["bucket"], "v5_grader_reason": r["grader_reason"],
            "v5_content_chars": r["content_chars"],
            "v5_answer_text": r["answer_text"],
            "v4_read_a_value": vc.get("pass") is True or str(vc.get("reason") or "")
            .startswith(("number_wrong", "missing_anchor", "value_not_in_")),
        })
    seam_matched = [s for s in seam if s["v4_read_a_value"]]
    seam_prose_only = [s for s in seam_matched
                       if s["v5_grader_reason"] == "prose_only"]

    doc = {
        "unit": "NEVER-ANSWERED-ROOT-2",
        "live_requests": 0,
        "network": False,
        "population": {
            "source": "QUALITY-REASON-MIX.json rows: bucket==never_answered and era==T3",
            "n_cells": len(out_rows),
            "grids": sorted({r["grid"] for r in out_rows}),
            "arms": sorted({r["arm"] for r in out_rows}),
            "turns": sorted({r["turn"] for r in out_rows}),
        },
        "bucket_totals": {b: totals.get(b, 0) for b in BUCKETS},
        "per_arm": tally("arm"),
        "per_grid": tally("grid"),
        "per_turn": {k: dict(v) for k, v in sorted(tally("turn").items())},
        "discriminator": {
            "rows_era": era_split,
            "fixture_contract": {k: {b: c.get(b, 0) for b in BUCKETS}
                                 for k, c in sorted(contract_split.items())},
            "grid_x_era_x_contract": {k: {b: c.get(b, 0) for b in BUCKETS}
                                      for k, c in sorted(grid_key.items())},
            "arm_within_grid_era_cells": {k: dict(v)
                                          for k, v in sorted(ridge_arm.items())},
        },
        "prose_assertions": {
            "n_prose_asserts_value": len(prose),
            "n_wrong": len(wrong),
            "n_right": len(right),
            "n_cap_hit_asserts_value": len(cap_assert),
            "cap_hit_asserting_cells": [{k: r[k] for k in
                                         ("grid", "arm", "checkpoint", "turn",
                                          "asserted_values", "checkpoint_truth",
                                          "assertion_verdict", "assertion_evidence")}
                                        for r in cap_assert],
            "wrong_cells": [{k: r[k] for k in
                             ("grid", "arm", "checkpoint", "turn", "era",
                              "asserted_values", "checkpoint_truth",
                              "assertion_evidence", "content_chars")}
                            for r in wrong],
            "right_cells": [{k: r[k] for k in
                             ("grid", "arm", "checkpoint", "turn", "era",
                              "asserted_values", "checkpoint_truth",
                              "assertion_evidence", "content_chars")}
                            for r in right],
            "unknown_cells": [{k: r[k] for k in
                               ("grid", "arm", "checkpoint", "turn",
                                "asserted_values", "checkpoint_truth")}
                              for r in prose if r["assertion_verdict"] == "unknown"],
        },
        "v4_v5_seam": {
            "n_matched_with_v4_check": len(seam),
            "n_v4_read_a_value": len(seam_matched),
            "n_v5_prose_only": len(seam_prose_only),
            "cells": seam,
            "cells_v4_read_v5_prose_only": seam_prose_only,
        },
        "rows": out_rows,
    }

    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)

    if args.do_print:
        print("TOTALS", doc["bucket_totals"])
        print("\nPER ARM")
        for a, c in doc["per_arm"].items():
            print(" ", a, {b: c[b] for b in BUCKETS if c[b]})
        print("\nPER GRID")
        for g, c in doc["per_grid"].items():
            print(" ", g, {b: c[b] for b in BUCKETS if c[b]})
        print("\nERA", doc["discriminator"]["rows_era"])
        print("\nCONTRACT", doc["discriminator"]["fixture_contract"])
        print("\nGRID x ERA x CONTRACT")
        for k, v in doc["discriminator"]["grid_x_era_x_contract"].items():
            print(" ", k, {b: n for b, n in v.items() if n})
        print("\nPROSE asserts=%d wrong=%d right=%d" % (
            len(prose), len(wrong), len(right)))
        for r in wrong:
            print("  WRONG", r["grid"], r["arm"], r["checkpoint"], "asserted",
                  r["asserted_values"], "truth", r["checkpoint_truth"],
                  "|", r["assertion_evidence"][:120])
        for r in right:
            print("  RIGHT", r["grid"], r["arm"], r["checkpoint"], "asserted",
                  r["asserted_values"], "truth", r["checkpoint_truth"])
        print("\nSEAM matched=%d v4_read_value=%d v5_prose_only=%d" % (
            len(seam), len(seam_matched), len(seam_prose_only)))
        for s in seam_prose_only:
            print("  ", s["grid"], s["arm"], s["checkpoint"], "v4:", s["v4_reason"],
                  "|", s["v4_found_excerpt"][:110])
    return 0


if __name__ == "__main__":
    sys.exit(main())
