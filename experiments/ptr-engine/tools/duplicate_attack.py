#!/usr/bin/env python3
"""Independent re-derivation and attack of the duplicate-row rule.

The rule under attack (orchestration/handoffs/TVS-REGRADE.json -> duplicate_rows):

    two rows are duplicates iff, WITHIN THE SAME FILE, they share
    (ts, content_sha256, prompt_tokens, completion_tokens); first kept.

This module imports nothing from the author's unit and applies nothing but that
literal tuple.  It deliberately does NOT import the author's helper: a verifier
that reuses the code under test reproduces the bug and proves nothing.

Attacks implemented here
  1. recompute groups / excess / decided, per file and total, and dump every row
     id in every group with excess > 1;
  2. second-attempt forensics: for every dropped row, diff every field OUTSIDE
     the four-tuple against the row that is kept for it;
  3. discriminating power: re-hash each row's payload and check which field the
     recorded content_sha256 actually equals, so we know whether it hashes the
     REQUEST body or the RESPONSE content;
  4. the not_applicable half: which files lack content_sha256 / millisecond ts,
     how many rows the skip leaves uncorrected, and whether those files contain
     same-second + same-token rows that a tuple applied naively would merge;
  5. (findings only, no arithmetic) the one-request-two-rows question: for every
     duplicate group, is any row an independent HTTP round trip?

Usage:
    python3 experiments/ptr-engine/tools/duplicate_attack.py [--json]

Run from the repository root.  Read-only: it never writes a rows file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

# The 14 files the author examined; discovery below checks that the set is
# complete so a file added since cannot silently escape the count.
AUTHOR_FILES = [
    "rows-longrun-v6-tools.jsonl",
    "rows-longrun-v4-tools-2026-10-26.jsonl",
    "rows-longrun-v5-tools.jsonl",
    "rows-longrun-2026-10-26.jsonl",
    "rows-longrun-c-2026-10-26.jsonl",
    "rows-longrun-v3-2026-10-26.jsonl",
    "rows-longrun-v4-2026-10-26.jsonl",
    "rows-longrun-2026-10-26-fix.jsonl",
    "rows-longrun-2026-10-26-policy.jsonl",
    "rows-baseline-2026-10-26.jsonl",
    "rows-equalinfo-2026-10-26.jsonl",
    "rows-live-2026-10-26.jsonl",
    "rows-cell-pointer-stable-20261026T145758Z.jsonl",
    "rows-pilot-thinking-2026-10-26.jsonl",
]

MEASURE_DIR = os.path.join("experiments", "ptr-engine", "measure")
MS_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,}Z$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def ts_key(row: dict):
    """The rule is written on `ts`; legacy rows carry `ts_utc` instead.  We use
    ts_utc only to reproduce the author's informational legacy groups -- those
    files are still reported as NOT APPLICABLE, never as decided."""
    return row.get("ts") if row.get("ts") is not None else row.get("ts_utc")


def tuple_of(row: dict) -> tuple:
    """The literal rule tuple.  Missing keys become None, never a wildcard."""
    return (
        ts_key(row),
        row.get("content_sha256"),
        row.get("prompt_tokens"),
        row.get("completion_tokens"),
    )


def applicable(rows: list[dict]) -> bool:
    """The author's applicability boundary: content_sha256 present AND ms ts."""
    if not rows:
        return False
    if any(r.get("content_sha256") is None for r in rows):
        return False
    return all(isinstance(r.get("ts"), str) and MS_TS.match(r["ts"]) for r in rows)


def decidable_key(row: dict) -> tuple:
    """What a *sound* same-request test needs beyond the tuple: the response
    identity (content sha) AND the measurement identity (ttft/latency).  Used
    only for the report, never to redefine the rule."""
    return (row.get("ts"), row.get("content_sha256"),
            row.get("prompt_tokens"), row.get("completion_tokens"),
            row.get("ttft_s"), row.get("latency_s"))


def attack1_groups(files: dict[str, list[dict]]) -> dict:
    per_file = []
    total_groups = total_excess = decided_groups = decided_excess = 0
    big_groups = []
    for name, rows in files.items():
        keyed = defaultdict(list)
        for idx, row in enumerate(rows):
            keyed[tuple_of(row)].append(idx)
        groups = {k: v for k, v in keyed.items() if len(v) > 1}
        excess = sum(len(v) - 1 for v in groups.values())
        ok = applicable(rows)
        per_file.append({
            "file": name, "rows": len(rows), "groups": len(groups),
            "excess": excess, "decided": bool(ok),
            "group_sizes": sorted((len(v) for v in groups.values()), reverse=True),
        })
        total_groups += len(groups)
        total_excess += excess
        if ok:
            decided_groups += len(groups)
            decided_excess += excess
        for k, v in groups.items():
            if len(v) - 1 > 1:
                big_groups.append({
                    "file": name, "indices": v, "n": len(v),
                    "ts": k[0], "prompt_tokens": k[2],
                    "completion_tokens": k[3],
                    "content_sha256": (k[1] or "")[:16],
                })
    return {
        "per_file": per_file, "groups": total_groups, "excess": total_excess,
        "decided_groups": decided_groups, "decided_excess": decided_excess,
        "groups_with_excess_gt_1": big_groups,
    }


def attack2_forensics(files: dict[str, list[dict]]) -> dict:
    """For every dropped row, is it distinguishable as a SECOND ATTEMPT?"""
    diff_fields = [
        "turn", "rep", "arm", "kind", "latency_s", "wall_ms", "ttft_s",
        "ttft_ms", "http_status", "error", "tool_calls", "fetch_followup",
        "billed_round", "prompt_served", "prompt_sha256", "max_tokens",
        "finish_reason", "stop_reason", "reasoning_sha256", "run_id",
        "tool_followup", "attempt", "msg_index", "started_at",
    ]
    out = {"duplicate_groups": 0, "dropped_rows": 0, "distinct_attempt_evidence": [],
           "all_dropped": []}
    for name, rows in files.items():
        if not applicable(rows):
            continue
        keyed = defaultdict(list)
        for idx, row in enumerate(rows):
            keyed[tuple_of(row)].append(idx)
        for key, idxs in keyed.items():
            if len(idxs) < 2:
                continue
            out["duplicate_groups"] += 1
            keep = idxs[0]
            for drop in idxs[1:]:
                out["dropped_rows"] += 1
                krow, drow = rows[keep], rows[drop]
                diffs = {}
                for f in diff_fields:
                    in_keep, in_drop = f in krow, f in drow
                    if not in_keep and not in_drop:
                        continue
                    if krow.get(f) != drow.get(f):
                        diffs[f] = {"kept": krow.get(f), "dropped": drow.get(f)}
                # An independent round trip must differ in at least one
                # *measurement* field (a wall clock or a server timing).
                measured = {f: v for f, v in diffs.items()
                            if f in ("latency_s", "wall_ms", "ttft_s", "ttft_ms")}
                entry = {
                    "file": name, "kept_idx": keep, "dropped_idx": drop,
                    "turn": drow.get("turn"), "kind_kept": krow.get("kind"),
                    "kind_dropped": drow.get("kind"),
                    "content_sha256": (key[1] or "")[:16],
                    "identical_measurement": not measured,
                    "measurement_diffs": measured,
                    "all_field_diffs": sorted(diffs),
                }
                out["all_dropped"].append(entry)
                if measured:
                    out["distinct_attempt_evidence"].append(entry)
    return out


def attack3_hash_definition(files: dict[str, list[dict]], writer: str) -> dict:
    """What does content_sha256 hash?  Compare against the row's own payloads."""
    checked = matched_content = matched_prompt = matched_messages = 0
    sample = []
    for name, rows in files.items():
        for row in rows:
            if row.get("content_sha256") is None:
                continue
            csha = row["content_sha256"]
            if row.get("content") is not None:
                checked += 1
                if sha256_text(row["content"]) == csha:
                    matched_content += 1
                elif row.get("reasoning") and sha256_text(row["reasoning"]) == csha:
                    matched_prompt += 1
            if len(sample) < 3 and row.get("content"):
                sample.append({
                    "file": name, "recorded": csha[:16],
                    "sha_of_content": sha256_text(row["content"])[:16],
                    "sha_of_prompt_sha_field": (row.get("prompt_sha256") or "")[:16],
                    "sha_of_content_plus_prompt": sha256_text(
                        str(row.get("prompt_sha256")) + row["content"])[:16],
                })
    writer_note = "writer file not found"
    if os.path.exists(writer):
        src = open(writer, encoding="utf-8").read()
        m = re.search(r'"content_sha256":\s*\(sha256_text\(recorded_content\)', src)
        writer_note = ("run_longrun.py:1493  content_sha256 = sha256_text(recorded_content) "
                       "-- hash of the ASSISTANT CONTENT, not the request body"
                       if m else "content_sha256 assignment not matched at expected shape")
    return {
        "rows_with_content_sha": checked,
        "content_sha256_equals_sha256_of_content": matched_content,
        "content_sha256_equals_sha256_of_reasoning_or_other": checked - matched_content,
        "samples": sample,
        "writer_definition": writer_note,
        "conclusion": ("content_sha256 is a RESPONSE-content hash; it says nothing about "
                       "max_tokens / tools / thinking / message list, so tuple equality is "
                       "response identity, not request identity."),
    }


def attack4_skip(files: dict[str, list[dict]], extra: dict[str, list[dict]]) -> dict:
    skipped = {}
    uncorrected_rows = 0
    latent = []
    for name, rows in files.items():
        if applicable(rows):
            continue
        uncorrected_rows += len(rows)
        has_sha = sum(1 for r in rows if r.get("content_sha256") is not None)
        ts_field = "ts" if any("ts" in r for r in rows) else (
            "ts_utc" if any("ts_utc" in r for r in rows) else None)
        second_res = bool(rows) and all(
            isinstance(r.get(ts_field), str) and not MS_TS.match(r[ts_field] or "")
            for r in rows) if ts_field else False
        # Naive literal tuple on this file's own clock: same second + same tokens.
        keyed = defaultdict(list)
        for idx, r in enumerate(rows):
            keyed[(r.get(ts_field), r.get("content_sha256"), r.get("prompt_tokens"),
                   r.get("completion_tokens"))].append(idx)
        naive_groups = {k: v for k, v in keyed.items() if len(v) > 1}
        # Same-second + same-token rows, ignoring the (absent) sha.
        keyed2 = defaultdict(list)
        for idx, r in enumerate(rows):
            keyed2[(r.get(ts_field), r.get("prompt_tokens"),
                    r.get("completion_tokens"))].append(idx)
        same_tokens = {k: v for k, v in keyed2.items() if len(v) > 1}
        distinguishable = 0
        for k, v in same_tokens.items():
            sigs = {(rows[i].get("rep"), rows[i].get("latency_s"),
                     rows[i].get("client_elapsed_s")) for i in v}
            if len(sigs) == len(v):
                distinguishable += 1
        skipped[name] = {
            "rows": len(rows), "ts_field": ts_field,
            "has_content_sha256": has_sha, "second_resolution_ts": second_res,
            "naive_tuple_groups": len(naive_groups),
            "naive_tuple_excess": sum(len(v) - 1 for v in naive_groups.values()),
            "same_second_same_token_groups": len(same_tokens),
            "same_token_groups_with_distinct_rep_or_latency": distinguishable,
            "sample_naive_group": next(
                ({"indices": v, "ts": k[0], "prompt": k[1], "completion": k[2]}
                 for k, v in same_tokens.items()), None),
        }
        if same_tokens:
            latent.append({"file": name, "groups": len(same_tokens),
                           "excess": sum(len(v) - 1 for v in same_tokens.values())})
    out = {"skipped_files": skipped, "rows_uncorrected": uncorrected_rows,
           "latent_same_second_same_token": latent}
    for name, rows in extra.items():
        has_sha = any(r.get("content_sha256") is not None for r in rows)
        out.setdefault("unexamined_files", []).append({
            "file": name, "rows": len(rows), "has_content_sha256": has_sha,
            "schema": sorted(rows[0].keys())[:8] if rows else []})
    return out


def attack5_row_request_mapping(files: dict[str, list[dict]], writer: str) -> dict:
    """Is a row 1:1 with an HTTP send?  The duplicate groups are
    (kind=tool-followup, kind=turn) pairs: check whether the turn row and the
    follow-up row carry the SAME measurement (one response) while the turn's own
    initial request has no row of its own."""
    kinds = defaultdict(int)
    for name, rows in files.items():
        for r in rows:
            kinds[(name, r.get("kind"))] += 1
    pair_shapes = defaultdict(int)
    mirror_rows = []       # (file, followup_idx, turn_idx) that DO share one measurement
    escaping = []          # same mirror, but the tuple misses it (ts differs by 1 ms)
    turns_with_followups = {}
    for name, rows in files.items():
        if not applicable(rows):
            continue
        keyed = defaultdict(list)
        for idx, row in enumerate(rows):
            keyed[tuple_of(row)].append(idx)
        for key, idxs in keyed.items():
            if len(idxs) > 1:
                pair_shapes[tuple(sorted(rows[i].get("kind") for i in idxs))] += 1
                mirror_rows.append({"file": name, "indices": idxs,
                                    "turn": rows[idxs[0]].get("turn"),
                                    "kinds": [rows[i].get("kind") for i in idxs]})
        by_turn = defaultdict(list)
        for idx, row in enumerate(rows):
            by_turn[(row.get("run_id"), row.get("turn"))].append(idx)
        n_turns = 0
        for tk, idxs in by_turn.items():
            if any(rows[i].get("kind") == "tool-followup" for i in idxs):
                n_turns += 1
                # last follow-up row vs the turn row: do they share one measurement?
                fu = [i for i in idxs if rows[i].get("kind") == "tool-followup"]
                tu = [i for i in idxs if rows[i].get("kind") == "turn"]
                if fu and tu:
                    a, b = rows[fu[-1]], rows[tu[-1]]
                    same = all(a.get(f) == b.get(f) for f in
                               ("ttft_s", "latency_s", "prompt_tokens",
                                "completion_tokens", "content_sha256"))
                    if same and (a.get("ts"), a.get("content_sha256"),
                                 a.get("prompt_tokens"), a.get("completion_tokens")) != (
                            b.get("ts"), b.get("content_sha256"),
                            b.get("prompt_tokens"), b.get("completion_tokens")):
                        escaping.append({"file": name, "turn": tk[1],
                                         "followup_idx": fu[-1], "turn_idx": tu[-1],
                                         "ts_followup": a.get("ts"), "ts_turn": b.get("ts"),
                                         "same_measurement": same})
        turns_with_followups[name] = n_turns
    return {
        "group_kind_shapes": {str(k): v for k, v in pair_shapes.items()},
        "mirror_groups": mirror_rows,
        "turns_with_followups": turns_with_followups,
        "mirrors_missed_by_tuple": escaping,
        "kinds_per_file": {f"{k[0]}:{k[1]}": v for k, v in sorted(kinds.items())},
        "writer_evidence": (
            "run_longrun.py fetch_rounds() appends one row per follow-up send, then the "
            "main loop appends the turn row from the SAME resp object returned by "
            "fetch_rounds; the turn's initial request has no row of its own."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files, missing = {}, []
    for name in AUTHOR_FILES:
        path = os.path.join(MEASURE_DIR, name)
        if os.path.exists(path):
            files[name] = load(path)
        else:
            missing.append(name)
    extra = {}
    for name in sorted(os.listdir(MEASURE_DIR)):
        if name.endswith(".jsonl") and name.startswith("rows-") and name not in files:
            extra[name] = load(os.path.join(MEASURE_DIR, name))

    a1 = attack1_groups(files)
    a2 = attack2_forensics(files)
    a3 = attack3_hash_definition(files, os.path.join(
        "experiments", "ptr-engine", "longrun", "run_longrun.py"))
    a4 = attack4_skip(files, extra)
    a5 = attack5_row_request_mapping(files, os.path.join(
        "experiments", "ptr-engine", "longrun", "run_longrun.py"))

    result = {
        "files_examined": len(files), "missing_files": missing,
        "rows_total": sum(len(v) for v in files.values()),
        "attack1_recompute": a1,
        "attack2_forensics": a2,
        "attack3_hash": a3,
        "attack4_skip": a4,
        "attack5_row_request_mapping": a5,
        "author_claim": {"groups": 41, "excess": 54, "decided": 30,
                         "dedup_requests": 1071, "raw_requests": 1101},
        "agreement": {
            "groups": a1["groups"] == 41, "excess": a1["excess"] == 54,
            "decided": a1["decided_excess"] == 30,
        },
    }
    if args.json:
        print(json.dumps(result, indent=1))
        return 0

    print(f"files={len(files)} rows={result['rows_total']} missing={missing}")
    print(f"groups={a1['groups']} excess={a1['excess']} "
          f"decided_groups={a1['decided_groups']} decided_excess={a1['decided_excess']}")
    print("per-file:")
    for r in a1["per_file"]:
        print(f"  {r['file']:<48} rows={r['rows']:>4} groups={r['groups']:>3} "
              f"excess={r['excess']:>3} decided={r['decided']} sizes={r['group_sizes']}")
    print("groups with excess>1:", json.dumps(a1["groups_with_excess_gt_1"]))
    print(f"dropped rows={a2['dropped_rows']} distinct-attempt evidence="
          f"{len(a2['distinct_attempt_evidence'])}")
    print("field diffs across dropped pairs:")
    for e in a2["all_dropped"][:3]:
        print("  ", json.dumps(e))
    print("hash:", json.dumps(a3, indent=1))
    print("skip:", json.dumps(a4, indent=1))
    print("mapping:", json.dumps(a5, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
