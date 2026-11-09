#!/usr/bin/env python3
"""STOP-REASON-AUDIT — classify rows that bill completion tokens but carry no content.

Unit: STOP-REASON-AUDIT.  Read-only: this tool opens rows-*.jsonl for reading and
writes exactly one artefact, experiments/ptr-engine/measure/STOP-REASON.json.
It never calls an endpoint, never re-runs a cell, never rewrites a row.

WHY THIS EXISTS
---------------
`matrix_audit.py` (unit MATRIX-HONESTY) reported 7 cells in state
`missing_answer_empty` and its next_unit_hint named the shape of the defect:
"7 cells carry empty content with 128 completion tokens ... a serving/truncation
fact, not a wrong answer."  An empty answer that was billed for tokens is not a
wrong answer, and it is not nothing either.  Until its cause has a name it can
only be counted as unexplained.  This tool gives it a name, per row, and keeps
it out of the wrong-answer column.

CLASSIFICATION (the vocabulary `docs/STOP-REASON.md` fixes)
----------------------------------------------------------
A row is classified from the fields the row actually carries — never from a
token count alone:

  reasoning_only          finish_reason is a length cap, content is empty, and
                          reasoning text or reasoning tokens were produced: the
                          thinking channel consumed the whole budget.
  truncated_answer        finish_reason is a length cap and content is NON-empty:
                          a partial answer.  It is graded like any answer (it is
                          not an empty-content row at all), and flagged so the
                          truncation is visible beside the verdict.
  cap_exhausted_no_content
                          finish_reason is a length cap, content is empty, and no
                          reasoning was recorded.  The server spent the entire
                          budget on something it did not surface as content.
  empty_string_bug        a clean finish_reason (stop / eos / end_turn / null-but-
                          present) with empty content and no reasoning: a
                          well-formed reply that contains nothing.
  unrecorded_empty_content
                          the row carries NO finish_reason field at all, so the
                          channel cannot be split from the row.  Recorded as
                          what it is: an empty answer whose cause the schema did
                          not capture.
  zero_tokens_no_content  empty content and zero completion tokens: no generation
                          happened (not a spent-budget case).

Every one of these with empty content becomes `empty_content: <cause>` and its
matrix state is `missing_answer_empty`.  It is NEVER `fail`: a row that produced
no answer cannot have produced a wrong one.

CLI
---
    python3 experiments/ptr-engine/tools/stop_reason_audit.py            # scan all, write JSON
    python3 experiments/ptr-engine/tools/stop_reason_audit.py --check     # re-scan, diff, no write
    python3 experiments/ptr-engine/tools/stop_reason_audit.py --file rows-longrun-2026-10-26.jsonl
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MEASURE = os.path.abspath(os.path.join(HERE, "..", "measure"))
ROWS_GLOB = "rows-*.jsonl"
STOP_REASON_JSON = os.path.join(MEASURE, "STOP-REASON.json")

# Finish reasons that mean "the model stopped because the output budget ran out".
LENGTH_REASONS = {"length", "max_tokens", "max_output_tokens", "token_limit"}
# Finish reasons that mean "the model chose to stop".
CLEAN_REASONS = {"stop", "eos", "end_turn", "stop_sequence", "null", "completed"}

# Field names a row may use for reasoning text, across the row schemas on disk.
REASONING_TEXT_KEYS = ("reasoning_content", "reasoning", "thinking")
REASONING_TOKEN_KEYS = ("reasoning_tokens", "reasoning_token_count", "thinking_tokens")


# Field names a row may use for the ANSWER text, across the row schemas on disk.
# Stage-1 and the long-run arms write `content`; older probe/baseline rows write
# `answer_text` and carry no `content` key at all.  Reading only `content` would
# libel every probe row as an empty answer — the precise error this unit exists to
# avoid — so the answer text is resolved by key presence, never by guesswork.
ANSWER_TEXT_KEYS = ("content", "answer_text", "answer_raw")


def _answer_text(row):
    """Return (text, field_used); field_used is None when the row carries no answer field."""
    for key in ANSWER_TEXT_KEYS:
        if key in row and row[key] is not None:
            value = row[key]
            return (value if isinstance(value, str) else str(value)), key
    return "", None


def _reasoning_text(row):
    """Return the reasoning text a row carries, or '' if it carries none."""
    for key in REASONING_TEXT_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _reasoning_tokens(row):
    """Return an int reasoning-token count if the row carries one, else None."""
    for key in REASONING_TOKEN_KEYS:
        value = row.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, dict):
            for inner in ("reasoning_tokens", "total", "count"):
                if isinstance(value.get(inner), (int, float)):
                    return int(value[inner])
    usage = row.get("usage")
    if isinstance(usage, dict):
        details = usage.get("completion_tokens_details")
        if isinstance(details, dict) and isinstance(details.get("reasoning_tokens"), (int, float)):
            return int(details["reasoning_tokens"])
    return None


def classify_row(row):
    """Classify one row.  Pure function of the row's own fields.

    Returns a dict with:
      empty            True when the row carries no answer text
      cause            the empty-content cause, or None for an answered row
      label            'empty_content: <cause>' for empty rows, else None
      truncated        True when a length cap stopped the stream
      finish_reason    the raw value, or None when the field is absent
      has_finish_field whether the row schema carries finish_reason at all
      reasoning        'text' | 'tokens' | '' — what reasoning evidence the row carries
      content_len      length of the recorded answer text
      answer_field     which key the answer text came from (None = row has none)
      completion_tokens
    """
    content, answer_field = _answer_text(row)
    empty = not content.strip()

    has_finish_field = "finish_reason" in row and row.get("finish_reason") is not None
    finish = row.get("finish_reason")
    finish_norm = finish.lower() if isinstance(finish, str) else (None if finish is None else str(finish))

    tokens = row.get("completion_tokens")
    tokens = int(tokens) if isinstance(tokens, (int, float)) and not isinstance(tokens, bool) else 0

    r_text = _reasoning_text(row)
    r_tokens = _reasoning_tokens(row)
    reasoning = "text" if r_text else ("tokens" if (r_tokens or 0) > 0 else "")

    capped = finish_norm in LENGTH_REASONS or row.get("truncated") is True
    clean = finish_norm in CLEAN_REASONS

    cause = None
    if not empty:
        # An answered row is never an empty-content row.  It is flagged when a cap
        # stopped it, but the answer that arrived is still graded as an answer.
        cause = None
    elif answer_field is None:
        # The schema carries no answer text field at all (live nonce probes): the
        # row cannot express an answer, so it is not evidence about a model.
        cause = "no_answer_text_field"
    else:
        if tokens <= 0:
            cause = "zero_tokens_no_content"
        elif not has_finish_field and not capped:
            # Stage-1 rows carry no finish_reason at all: the cause exists but the
            # schema did not record which channel spent the budget.
            cause = "unrecorded_empty_content"
        elif capped and reasoning:
            cause = "reasoning_only"
        elif capped:
            cause = "cap_exhausted_no_content"
        elif clean or finish_norm is None:
            cause = "empty_string_bug" if not reasoning else "reasoning_only"
        else:
            cause = "unrecorded_empty_content"

    return {
        "empty": empty,
        "cause": cause,
        "label": ("empty_content: %s" % cause) if cause else None,
        "truncated": bool(capped),
        "truncated_answer": bool(capped and not empty),
        "finish_reason": finish,
        "has_finish_field": has_finish_field,
        "reasoning": reasoning,
        "content_len": len(content),
        "answer_field": answer_field,
        "completion_tokens": tokens,
        "max_tokens": row.get("max_tokens"),
        "http_status": row.get("http_status"),
        "error": row.get("error"),
    }


def row_state(row):
    """The matrix state a row earns.  Empty content is NEVER `fail`.

    Returns {'state': 'missing_answer_empty'|'gradable',
             'cause': <cause or None>, 'label': <label or None>}.
    """
    info = classify_row(row)
    if info["empty"]:
        return {"state": "missing_answer_empty", "cause": info["cause"], "label": info["label"]}
    return {"state": "gradable", "cause": None, "label": None}


def _normalise(text):
    return " ".join(str(text or "").split()).strip().lower().rstrip(".")


def verdict(row, expected=None):
    """Grade one row: 'pass' | 'fail' | 'missing_answer_empty'.

    A row with no answer text is `missing_answer_empty` — never `fail`.  A row
    that answered is `pass`/`fail` on its text; emptiness never decides a fail.
    When `expected` is None the answered row is reported 'gradable' (the caller
    owns the judgement).
    """
    state = row_state(row)
    if state["state"] == "missing_answer_empty":
        return "missing_answer_empty"
    if expected is None:
        return "gradable"
    return "pass" if _normalise(_answer_text(row)[0]) == _normalise(expected) else "fail"


def row_identity(row):
    """A stable, human-readable handle for a row inside its file."""
    parts = []
    for key in ("run_id", "arm", "rep", "turn", "cell", "kind"):
        if row.get(key) is not None:
            parts.append("%s=%s" % (key, row[key]))
    return " ".join(parts)


def scan_file(path):
    """Scan one rows file.  Read-only.  Returns a per-file report dict."""
    rows = []
    bad_lines = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                bad_lines += 1

    per_arm = {}
    hits = []          # empty-content rows with completion_tokens > 0
    reasoning_hits = []  # rows with reasoning text but empty content
    truncated_answers = []
    causes = {}
    finish_reasons = {}
    rows_with_finish_field = 0
    rows_with_reasoning_field = 0
    tokens_spent_on_empty = 0
    answer_fields_seen = {}

    for index, row in enumerate(rows):
        info = classify_row(row)
        key = str(info["answer_field"])
        answer_fields_seen[key] = answer_fields_seen.get(key, 0) + 1
        arm = row.get("arm") or "(no arm)"
        bucket = per_arm.setdefault(arm, {
            "rows": 0,
            "answered_rows": 0,
            "empty_content_rows": 0,
            "empty_content_completion_tokens": 0,
            "reasoning_only_rows": 0,
        })
        bucket["rows"] += 1
        if info["has_finish_field"]:
            rows_with_finish_field += 1
        if info["reasoning"]:
            rows_with_reasoning_field += 1
        finish_reasons[str(info["finish_reason"])] = finish_reasons.get(str(info["finish_reason"]), 0) + 1

        if not info["empty"]:
            bucket["answered_rows"] += 1
            if info["truncated_answer"]:
                truncated_answers.append({
                    "index": index,
                    "identity": row_identity(row),
                    "completion_tokens": info["completion_tokens"],
                    "finish_reason": info["finish_reason"],
                    "content_len": info["content_len"],
                })
            continue

        bucket["empty_content_rows"] += 1
        if info["completion_tokens"] <= 0:
            causes[info["cause"]] = causes.get(info["cause"], 0) + 1
            continue

        # The pattern this unit exists to name.
        bucket["empty_content_completion_tokens"] += info["completion_tokens"]
        tokens_spent_on_empty += info["completion_tokens"]
        causes[info["cause"]] = causes.get(info["cause"], 0) + 1
        if info["cause"] == "reasoning_only":
            bucket["reasoning_only_rows"] += 1
        detail = {
            "index": index,
            "identity": row_identity(row),
            "arm": row.get("arm"),
            "turn": row.get("turn"),
            "rep": row.get("rep"),
            "completion_tokens": info["completion_tokens"],
            "content_len": info["content_len"],
            "content_sha256": row.get("content_sha256"),
            "answer_field": info["answer_field"],
            "cause": info["cause"],
            "label": info["label"],
            "finish_reason": info["finish_reason"],
            "has_finish_field": info["has_finish_field"],
            "reasoning": info["reasoning"],
            "max_tokens": info["max_tokens"],
            "truncated": info["truncated"],
            "http_status": info["http_status"],
            "error": info["error"],
        }
        hits.append(detail)
        if info["reasoning"]:
            reasoning_hits.append(detail)

    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()

    answered_count = len(rows) - sum(1 for r in rows if classify_row(r)["empty"])
    empty_count = sum(1 for r in rows if classify_row(r)["empty"])
    if rows and empty_count == len(rows):
        file_shape = "empty_file_all_rows"
    elif empty_count == 0:
        file_shape = "no_empty_rows"
    else:
        file_shape = "partial_empty_rows"

    return {
        "file": os.path.basename(path),
        "path": path,
        "sha256": digest,
        "rows": len(rows),
        "file_shape": file_shape,
        "unparseable_lines": bad_lines,
        "rows_with_finish_reason_field": rows_with_finish_field,
        "rows_with_reasoning_field": rows_with_reasoning_field,
        "finish_reason_values": dict(sorted(finish_reasons.items())),
        "answered_rows": len(rows) - sum(1 for r in rows if classify_row(r)["empty"]),
        "empty_content_rows": sum(1 for r in rows if classify_row(r)["empty"]),
        # The two numbers TASK 3 asks for, stated separately:
        "empty_content_with_completion_tokens": len(hits),
        "reasoning_with_empty_content": len(reasoning_hits),
        "completion_tokens_spent_on_empty_content": tokens_spent_on_empty,
        "causes": dict(sorted(causes.items())),
        "truncated_answer_rows": len(truncated_answers),
        "per_arm": dict(sorted(per_arm.items())),
        "file_shape": file_shape,
        "distinct_completion_tokens_on_empty": sorted(
            {hit["completion_tokens"] for hit in hits}),
        "answer_fields_seen": dict(sorted(answer_fields_seen.items())),
        "hits": hits,
        "truncated_answers": truncated_answers,
    }


def scan_dir(rows_dir=MEASURE, pattern=ROWS_GLOB):
    """Scan every rows file in `rows_dir`.  Read-only."""
    paths = sorted(glob.glob(os.path.join(rows_dir, pattern)))
    files = [scan_file(path) for path in paths]
    totals = {
        "rows": sum(f["rows"] for f in files),
        "answered_rows": sum(f["answered_rows"] for f in files),
        "empty_content_rows": sum(f["empty_content_rows"] for f in files),
        "empty_content_with_completion_tokens": sum(
            f["empty_content_with_completion_tokens"] for f in files),
        "reasoning_with_empty_content": sum(f["reasoning_with_empty_content"] for f in files),
        "completion_tokens_spent_on_empty_content": sum(
            f["completion_tokens_spent_on_empty_content"] for f in files),
        "truncated_answer_rows": sum(f["truncated_answer_rows"] for f in files),
    }
    causes = {}
    for item in files:
        for cause, count in item["causes"].items():
            causes[cause] = causes.get(cause, 0) + count
    totals["causes"] = dict(sorted(causes.items()))
    return {"files": files, "totals": totals}


def build_report(rows_dir=MEASURE, pattern=ROWS_GLOB):
    """The full STOP-REASON.json payload."""
    scan = scan_dir(rows_dir, pattern)
    stage1 = next((f for f in scan["files"] if f["file"] == "rows-longrun-2026-10-26.jsonl"), None)
    return {
        "unit": "STOP-REASON-AUDIT",
        "generated_by": "experiments/ptr-engine/tools/stop_reason_audit.py",
        "live_requests": 0,
        "read_only": True,
        "rule": ("a row with empty content and non-zero completion tokens is "
                 "'empty_content: <cause>', is never graded fail, and is counted "
                 "missing_answer_empty in the matrix with its cause attached "
                 "(docs/STOP-REASON.md)"),
        "causes_defined": {
            "reasoning_only": "length cap hit, content empty, reasoning produced — thinking spent the budget",
            "truncated_answer": "length cap hit, content NON-empty — a partial answer, graded as an answer",
            "cap_exhausted_no_content": "length cap hit, content empty, no reasoning recorded",
            "empty_string_bug": "clean finish reason, empty content, no reasoning",
            "unrecorded_empty_content": "row carries no finish_reason field; the cause channel was not recorded",
            "zero_tokens_no_content": "empty content and zero completion tokens — no generation billed",
        },
        "cap_128": {
            "is_harness_cap": True,
            "cap_value": 128,
            "frozen_in_manifest": {
                "path": "experiments/ptr-engine/longrun/manifests/stage1-lr01-lease-reopen-r1.json",
                "line": 36,
                "text": '"max_tokens": 128,',
            },
            "raised_by": {
                "path": "experiments/ptr-engine/longrun/manifests/v6-run-longrun-pre-edit.py",
                "lines": [1548, 1549, 1550, 1551, 1552],
                "text": ("# 16384 (was 128 -> 1024 -> 4096): Stage 1 (RUN-STAGE1-LR01) truncated "
                         "140/192 rows at 128; at 1024 a measured 7/12 smoke rows still hit "
                         'finish_reason="length"; at 4096 the 4-row fix run still truncated '
                         "transcript-grow T3 at 4096 completion tokens with completion on the "
                         "reasoning channel only and no answer."),
            },
            "corroborated_by": {
                "path": "experiments/ptr-engine/longrun/METRICS.md",
                "line": 60,
                "text": "completions capped at 128, 99/192 rows without TTFT.",
            },
            "verdict": "128 is a harness cap (the Stage-1 --max-tokens value), not a serving floor",
        },
        "stage1_file": ({
            "file": stage1["file"],
            "rows": stage1["rows"],
            "empty_content_with_completion_tokens": stage1["empty_content_with_completion_tokens"],
            "distinct_completion_tokens_on_empty": sorted({
                hit["completion_tokens"] for hit in stage1["hits"]}),
            "rows_with_finish_reason_field": stage1["rows_with_finish_reason_field"],
            "rows_with_reasoning_field": stage1["rows_with_reasoning_field"],
            "http_status_values": sorted({str(hit["http_status"]) for hit in stage1["hits"]}),
            "error_values": sorted({str(hit["error"]) for hit in stage1["hits"]}),
            "causes": stage1["causes"],
        } if stage1 else None),
        "totals": scan["totals"],
        "files": scan["files"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows-dir", default=MEASURE)
    parser.add_argument("--pattern", default=ROWS_GLOB)
    parser.add_argument("--file", default=None,
                        help="print one file's report to stdout instead of writing the JSON")
    parser.add_argument("--check", action="store_true",
                        help="re-scan and compare against the on-disk STOP-REASON.json; no write")
    args = parser.parse_args(argv)

    if args.file:
        path = args.file if os.path.isabs(args.file) else os.path.join(args.rows_dir, args.file)
        print(json.dumps(scan_file(path), indent=1))
        return 0

    report = build_report(args.rows_dir, args.pattern)

    if args.check:
        if not os.path.exists(STOP_REASON_JSON):
            print("MISSING %s — run without --check" % STOP_REASON_JSON)
            return 2
        with open(STOP_REASON_JSON, "r", encoding="utf-8") as handle:
            on_disk = json.load(handle)
        if on_disk.get("totals") != report["totals"]:
            print("STALE %s: totals differ from a fresh scan" % STOP_REASON_JSON)
            print("  on disk: %s" % json.dumps(on_disk.get("totals"), sort_keys=True))
            print("  rescan : %s" % json.dumps(report["totals"], sort_keys=True))
            return 1
        print("OK %s matches a fresh scan" % STOP_REASON_JSON)
        return 0

    with open(STOP_REASON_JSON, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=False)
        handle.write("\n")
    totals = report["totals"]
    print("wrote %s" % STOP_REASON_JSON)
    print("rows %d, answered %d, empty %d, empty-with-tokens %d, reasoning-with-empty-content %d"
          % (totals["rows"], totals["answered_rows"], totals["empty_content_rows"],
             totals["empty_content_with_completion_tokens"], totals["reasoning_with_empty_content"]))
    print("causes %s" % json.dumps(totals["causes"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
