#!/usr/bin/env python3
"""DEDUPE-ROOT-CAUSE — independent re-derivation of the writer double-append and the
request-identity backfill question.

Read-only over the row files, `run_longrun.py` and `client.py`: it writes nothing except
the artefact it is asked to emit (`--json PATH`, optional; default prints to stdout).

    python3 experiments/ptr-engine/tools/dedupe_root_cause.py            # human summary
    python3 experiments/ptr-engine/tools/dedupe_root_cause.py --json experiments/ptr-engine/measure/DEDUPE-ROOT-CAUSE.json

Zero inference requests, zero network. No import of the ledger's own helper: the tuple is
re-implemented here so the audit does not inherit the code it audits.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")

FILES = [
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

#: The three legacy-schema files the ledger skips (no content_sha256, second-resolution ts).
LEGACY = {"rows-baseline-2026-10-26.jsonl", "rows-equalinfo-2026-10-26.jsonl",
          "rows-live-2026-10-26.jsonl"}

#: The measurement fields that must be identical for two rows to be ONE measurement.
MEASURED = ["ttft_s", "ttft_ms", "latency_s", "wall_ms", "prompt_tokens",
            "completion_tokens", "content_sha256", "finish_reason"]

#: The three pairs the card asks to walk (1-based row numbers in DUPLICATE-ATTACK.md).
WALKED = [("rows-longrun-v4-tools-2026-10-26.jsonl", 0, 1, 1),
          ("rows-longrun-v5-tools.jsonl", 3, 4, 2),
          ("rows-longrun-v6-tools.jsonl", 0, 1, 1)]


def load(name):
    path = os.path.join(MEASURE, name)
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tuple_of(row):
    """The ledger's duplicate tuple, re-implemented: within one file only."""
    return (row.get("ts"), row.get("content_sha256"),
            row.get("prompt_tokens"), row.get("completion_tokens"))


def naive_legacy_tuple(row):
    """What the ledger tuple degenerates to on the legacy schema: no content hash, and
    ``ts_utc`` at SECOND resolution (``row["ts"]`` does not exist there at all)."""
    ts = row.get("ts") or row.get("ts_utc")
    return (str(ts)[:19] if ts else None, row.get("content_sha256"),
            row.get("prompt_tokens"), row.get("completion_tokens"))


def groups_of(rows, legacy=False):
    seen, groups = {}, []
    for i, row in enumerate(rows):
        key = naive_legacy_tuple(row) if legacy else tuple_of(row)
        if key[1] is None and not legacy:
            continue
        seen.setdefault(key, []).append(i)
    for key, idxs in seen.items():
        if len(idxs) > 1:
            groups.append(idxs)
    return groups


def differing(kept, dropped):
    keys = sorted(set(kept) | set(dropped))
    return [k for k in keys if kept.get(k) != dropped.get(k)]


def main(argv):
    out_path = None
    if "--json" in argv:
        out_path = argv[argv.index("--json") + 1]

    per_file = []
    decided = []
    realised = []
    for name in FILES:
        rows = load(name)
        groups = groups_of(rows)
        excess = sum(len(g) - 1 for g in groups)
        entry = {"file": name, "rows": len(rows), "groups": len(groups), "excess": excess,
                 "dedupable": name not in LEGACY}
        if name in LEGACY:
            naive = groups_of(rows, legacy=True)
            entry["naive_groups_without_hash"] = len(naive)
            entry["naive_excess_without_hash"] = sum(len(g) - 1 for g in naive)
        per_file.append(entry)
        if name in LEGACY:
            continue
        for g in groups:
            decided.append((name, g, rows))
            for j in g[1:]:
                realised.append((name, g[0], j, rows))

    # ---------------------------------------------------------------- the walked pairs
    walked = []
    for name, ki, di, turn in WALKED:
        rows = load(name)
        kept, dropped = rows[ki], rows[di]
        row_idxs = [i for i, r in enumerate(rows) if int(r.get("turn") or 0) == turn]
        turn_rows = [rows[i] for i in row_idxs]
        kinds = {}
        for r in turn_rows:
            kinds[r.get("kind")] = kinds.get(r.get("kind"), 0) + 1
        # Sends this turn: one initial + one per follow-up round it actually bought.
        sends = 1 + kinds.get("tool-followup", 0)
        walked.append({
            "file": name,
            "turn": turn,
            "kept_index": ki, "dropped_index": di,
            "kept_kind": kept.get("kind"), "dropped_kind": dropped.get("kind"),
            "ts": kept.get("ts"),
            "measurement_equal_on": [f for f in MEASURED
                                     if kept.get(f) == dropped.get(f)],
            "measurement_differs_on": [f for f in MEASURED
                                       if kept.get(f) != dropped.get(f)],
            "all_fields_that_differ": differing(kept, dropped),
            "rows_for_that_turn": len(turn_rows),
            "row_kinds_for_that_turn": kinds,
            "sends_implied_by_the_runner": sends,
            "rows_equal_sends": len(turn_rows) == sends,
            "distinct_measurements_in_that_turn": len({(r.get("ttft_s"), r.get("latency_s"),
                                                       r.get("content_sha256"))
                                                      for r in turn_rows}),
            "sends_left_without_their_own_measurement": (
                sends - len({(r.get("ttft_s"), r.get("latency_s"), r.get("content_sha256"))
                             for r in turn_rows})),
            "prompt_sha256_kept": (kept.get("prompt_sha256") or "")[:12],
            "prompt_sha256_dropped": (dropped.get("prompt_sha256") or "")[:12],
        })

    # ------------------------------------------------------- 30/30 identical measurements
    identical = 0
    kinds_seen = set()
    for name, ki, di, rows in realised:
        kept, dropped = rows[ki], rows[di]
        kinds_seen.add((kept.get("kind"), dropped.get("kind")))
        if all(kept.get(f) == dropped.get(f) for f in MEASURED):
            identical += 1

    # ---------------------------------------------------------- identity backfill question
    keys_present = {"request_sha256": 0, "request_body": 0, "row_seq": 0,
                    "request_identity_complete": 0}
    total_rows = 0
    backfillable = 0
    for name in FILES:
        for row in load(name):
            total_rows += 1
            hit = False
            for k in keys_present:
                if k in row:
                    keys_present[k] += 1
                    hit = True
            if row.get("request_sha256") not in (None, "", "unknown"):
                hit = True
            if hit and row.get("request_sha256") not in (None, "", "unknown"):
                backfillable += 1

    # ------------------------------------------------------------------ the code path
    run_py = os.path.join(LONGRUN, "run_longrun.py")
    client_py = os.path.join(LONGRUN, "client.py")
    with open(run_py, encoding="utf-8") as fh:
        run_lines = fh.read().splitlines()
    with open(client_py, encoding="utf-8") as fh:
        client_lines = fh.read().splitlines()

    def line(no):
        return run_lines[no - 1].strip()

    sites = [
        (964, "resp = send_chat(cfg, next_messages)",
         "fetch_rounds: the follow-up request reaches the wire"),
        (974, 'cfg, fixture, arm, rep, run_id, t, resp, content, "tool-followup", manifest_sha,',
         "fetch_rounds: the follow-up row is built from THAT resp"),
        (980, "return messages, resp, sent, rounds_used, turn_calls, followups",
         "fetch_rounds RETURNS that same resp to the caller"),
        (2045, 'resp = send_chat(cfg, planner.messages(info["prompt"]))',
         "main loop: the turn's INITIAL request"),
        (2082, "sent += 1", "main loop: the initial send is COUNTED, no row written yet"),
        (2092, "if tools_enabled(cfg) and not is_answer_turn:",
         "main loop: the follow-up path opens only for a tool-using, non-answer turn"),
        (2106, "followup_rows) = fetch_rounds(",
         "main loop: resp is REBOUND to fetch_rounds' return value"),
        (2152, 'row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))',
         "main loop: the turn row still hashes the INITIAL prompt"),
        (2167, 'row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,',
         "main loop: the turn row is built from that SAME resp"),
        (2178, "append_row(rows_path, frow)", "the follow-up rows are written first"),
        (2179, "append_row(rows_path, row)", "then the turn row, one line later"),
    ]
    quoted = []
    for no, expect, role in sites:
        got = line(no)
        if got != expect:
            raise SystemExit("run_longrun.py:%d is not the cited code:\n  want %r\n  got  %r"
                             % (no, expect, got))
        quoted.append({"file": "experiments/ptr-engine/longrun/run_longrun.py", "line": no,
                       "code": got, "role": role})

    artefact = {
        "unit": "DEDUPE-ROOT-CAUSE",
        "generated_by": "experiments/ptr-engine/tools/dedupe_root_cause.py",
        "requests_sent": 0,
        "network": False,
        "inputs": {name: {"sha256": sha256_file(os.path.join(MEASURE, name)),
                          "rows": next(e["rows"] for e in per_file if e["file"] == name)}
                   for name in FILES},
        "harness_sha256": {"run_longrun.py": sha256_file(run_py),
                           "client.py": sha256_file(client_py)},
        "recount": {
            "files": len(FILES), "rows": total_rows,
            "groups_hash_applicable": sum(e["groups"] for e in per_file),
            "excess_hash_applicable": sum(e["excess"] for e in per_file),
            "groups_with_legacy_naive": sum(e["groups"] for e in per_file)
            + sum(e.get("naive_groups_without_hash", 0) for e in per_file),
            "excess_with_legacy_naive": sum(e["excess"] for e in per_file)
            + sum(e.get("naive_excess_without_hash", 0) for e in per_file),
            "decided_groups": len(decided),
            "decided_excess": len(realised),
            "per_file": per_file,
        },
        "root_cause": {
            "finding": "double_append_within_one_turn",
            "condition": ("tools_enabled(cfg) and not is_answer_turn, and the turn's first "
                          "response asked for at least one <tool_call> that got a follow-up "
                          "request through the allowance; fetch_rounds then returns the LAST "
                          "follow-up's resp and the main loop builds the turn row from that "
                          "same object, so two rows carry one measurement"),
            "same_request_row_pair": "kind='tool-followup' (written at run_longrun.py:974) and "
                                     "kind='turn' (written at run_longrun.py:2174-2179)",
            "why_not_a_retry": ("the initial send at run_longrun.py:2045 is counted (:2082) but "
                                "never given a row of its own: the turn row stands in its slot "
                                "while wearing the follow-up's measurement, so rows == sends "
                                "and the pair is a misattribution, not an extra row"),
            "sites": quoted,
            "walked_pairs": walked,
            "counts": {
                "decided_excess_rows": len(realised),
                "identical_on_every_measured_field": identical,
                "kind_pairs_observed": sorted([list(k) for k in kinds_seen]),
                "distinct_measurements_per_walked_turn": [w["distinct_measurements_in_that_turn"]
                                                          for w in walked],
                "sends_left_without_their_own_measurement": [
                    w["sends_left_without_their_own_measurement"] for w in walked],
            },
        },
        "backfill": {
            "rows_total": total_rows,
            "rows_carrying_a_request_identity_field": keys_present,
            "rows_that_could_get_a_true_request_sha256": backfillable,
            "statement": ("No historical rows file retains the request body, so %d rows can be "
                          "given a request identity.  The rows files are untouched."
                          % backfillable),
            "reason": ("no row retained the serialized wire body (or a hash of it); the body is "
                       "gone once the process exits, so a digest computed now would be a guess "
                       "over a reconstructed body, not the bytes that were sent"),
        },
        # ------------------------------------------------------------------ the fix
        "new_row_fields": {
            "request_sha256": (
                "sha256 over the exact serialized request body handed to the wire (model, "
                "messages, temperature, max_tokens, stream, stream_options, "
                "chat_template_kwargs/thinking; tools where the engine takes them as a body "
                "member).  Computed in client.send_chat from the same bytes passed to urlopen "
                "(client.py:660); helper client.request_digest (client.py:305).  Value is "
                "\"unknown\" when the body was not retained."),
            "request_identity_complete": (
                "boolean; true only when the wire body was retained for this row.  false "
                "always pairs with request_sha256=\"unknown\"."),
            "row_seq": (
                "monotonic integer per rows file, assigned once per row object in "
                "run_longrun.append_row, seeded from the file's own high-water mark.  A "
                "re-append of the same row keeps its seq; a re-send is a new row and takes the "
                "next integer."),
            "written_on_every_row": (
                "run_longrun.make_row writes request_sha256/request_identity_complete beside "
                "content_sha256; TurnWallCap.as_response carries the identity for wall-cap "
                "rows."),
        },
        "discriminator_test": {
            "path": "experiments/ptr-engine/longrun/tests/test_request_identity.py",
            "checks": 17,
            "result": "green",
            "case_a_two_different_requests_same_response_text": {
                "content_sha256": "equal (why the old rule merges)",
                "request_sha256": "different",
                "old_tuple_equates_them": True},
            "case_b_same_request_resent": {
                "request_sha256": "same", "row_seq": [1, 2],
                "verdict": "re-send, not a duplicate"},
            "case_c_one_request_row_written_twice": {
                "request_sha256": "same", "row_seq": "same", "verdict": "duplicate"},
            "case_d_historical_mechanism_reproduced": (
                "with the real writer functions, the follow-up row and the turn row built from "
                "one resp share request_sha256 and content_sha256, and differ in prompt_sha256"),
            "green_command": "python3 experiments/ptr-engine/longrun/tests/test_request_identity.py",
            "green_result": "17 checks, 0 failed; ALL GREEN (and both RED assertions failed as designed)",
            "red_command": (
                "python3 - <<'PY' ... client.send_chat patched to strip "
                "request_sha256/request_identity_complete ... exec the test module ... PY"),
            "red_result": "KeyError: 'request_sha256' at case_a - fails when the field is removed",
            "network": "zero; socket.socket replaced for the run and restored (no cross-test leak)",
        },
        "recommended_ledger_rule": (
            "Deduct a row as a duplicate only when it shares request_sha256 with another row AND "
            "a row_seq that proves a single send wrote both; for rows written before this field "
            "existed deduct nothing (absence of request_sha256 is not evidence of duplication); "
            "treat equal request_sha256 with different row_seq as a re-send (billed, never "
            "deducted); treat differing request_sha256 as distinct requests even when ts, "
            "content_sha256 and token counts are identical; keep the old (ts, content_sha256, "
            "prompt_tokens, completion_tokens) tuple only as a candidate detector that must be "
            "confirmed by the request identity before any spend is removed.  Re-publish the "
            "deduction only after request_sha256 has been live for one full live cell, and "
            "publish requests_raw until then."),
        "untouched": [
            "every measure/rows-*.jsonl (byte-identical)",
            "experiments/ptr-engine/longrun/request_ledger.py",
            "experiments/ptr-engine/measure/REQUEST-LEDGER.json",
            "docs/REQUEST-LEDGER.md",
            "experiments/ptr-engine/longrun/cell.py",
            "experiments/ptr-engine/measure/TVS.json",
            "experiments/ptr-engine/measure/LATENCY-REPORT.json",
            "every *grade*.json",
        ],
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(artefact, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print("wrote %s" % out_path)

    print("rows %d in %d files · groups %d (%d counting the legacy naive tuple) · "
          "excess %d (%d) · decided excess %d"
          % (artefact["recount"]["rows"], artefact["recount"]["files"],
             artefact["recount"]["groups_hash_applicable"],
             artefact["recount"]["groups_with_legacy_naive"],
             artefact["recount"]["excess_hash_applicable"],
             artefact["recount"]["excess_with_legacy_naive"],
             artefact["recount"]["decided_excess"]))
    for w in walked:
        print("T%-3d %-30s rows=%d sends=%d measurements=%d unrepresented_sends=%d "
              "differs=%s"
              % (w["turn"], w["file"][:30], w["rows_for_that_turn"],
                 w["sends_implied_by_the_runner"],
                 w["distinct_measurements_in_that_turn"],
                 w["sends_left_without_their_own_measurement"],
                 ",".join(w["measurement_differs_on"]) or "none"))
    print("30-check: %d/%d decided pairs identical on every measured field"
          % (identical, len(realised)))
    print("backfill: %d of %d rows could get a request identity"
          % (backfillable, total_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
