#!/usr/bin/env python3
"""request_ledger.py -- count inference REQUESTS from row files, and gate spending on them.

WHY THIS EXISTS
---------------
Every status line this project wrote for six rounds carried a hand-maintained
"~466 of 4,320 requests used". The harness had already produced 1,095 (now 1,101) rows.
A budget nobody can count is a budget nobody can defend: the one live run that went
wrong (LIVE-SMOKE-CELL, dbed0e9d) burned 6 requests instead of ~130 and was stopped by a
human noticing a wall clock, not by a ledger. This module makes the number computable and
turns it into a door a conductor must walk through BEFORE it sends anything.

THE COUNTING RULE (closed vocabulary -- do not extend silently)
---------------------------------------------------------------
One request is counted per row that represents an inference call.

ONE REQUEST PER ROW THAT IS ONE WIRE REQUEST. Every kind below is traced to the make_row
call site that writes it and the gate/send that bills it (`longrun/run_longrun.py`):

  1. COUNT      kind == "turn"            -- run_longrun.py:2703; the turn's only send, or
                                             (k>=1 follow-ups) follow-up k's response row
  2. COUNT      kind == "tool-followup"   -- run_longrun.py:1126; one follow-up request
                                             (gate.acquire at :1115)
  3. COUNT      kind == "turn-initial"    -- run_longrun.py:2726-2729; the INITIAL send's own
                                             row under ROW-ATTRIBUTION. run_longrun.py:2672:
                                             k>=1 follow-ups means k+1 requests, one row per
                                             send. Its omission is the 30-row gap that
                                             refused RUN-A-STAR-2 at gate 2.
  4. COUNT      kind == "digest"          -- run_longrun.py:2479 gate.acquire(t,"digest") then
                                             :2481 send_chat; a planning request on the wire
  5. DO NOT COUNT  billed is False                       (billed: false)
  6. DO NOT COUNT  followup_suppressed is truthy          (a follow-up the client skipped)
  7. DO NOT COUNT  served_from == "prompt"                (served out of the prompt, no call)
  8. COUNT + FLAG  assumed_billed -- the row carries NO kind (legacy schema). Rules 1-4 cannot
                   decide it, so we count it (an unmarked row that reached the wire must not
                   vanish from the budget) and report the doubt instead of laundering it.
  9. REFUSE     an unrecognised non-empty kind -> UnrecognisedKind. NOT billed (that invents
                a request the vocabulary never authorised) and NOT unbilled (that deletes a
                request that may have hit the wire). An exception is the only honest answer.

Rules 5-7 are the only exclusions. Everything else -- including rows carrying an HTTP error,
a checkpoint row and a failure row -- is counted: a rejected request still consumed a slot.

`row_bills()` is the single implementation of this rule and `run_a_star.py::_row_counts`
imports it. Two tallies of one number is how `792` vs `660` and `1176` vs `1321` happened.

THE DUPLICATE RULE (REQUEST-LEDGER-2, from TVS-REGRADE)
-------------------------------------------------------
The writer emitted the same request twice -- a `kind=tool-followup` row and a `kind=turn`
row sharing `ts` (to the millisecond), `content_sha256`, `prompt_tokens` and
`completion_tokens`, with identical ttft_s/latency_s. Those mirrors are not requests.

    identical (ts, content_sha256, prompt_tokens, completion_tokens) within one file;
    first occurrence kept

The rule is applied ONLY where the schema can decide it: a file is `decided` when every row
carries a non-empty `content_sha256` and a millisecond-resolution `ts`. The 3 legacy-schema
files (second-resolution `ts_utc`, no `content_sha256`) are marked `not_applicable` and are
NOT deduplicated -- on their schema the literal tuple over-merges demonstrably distinct
requests (different rep, different latency_s), so applying it would fabricate a saving. The
collisions the tuple WOULD have merged on those files are still counted and reported under
`collisions_not_applied`, so the non-application is visible rather than silently chosen.

BOTH FIGURES ARE PUBLISHED. `requests_raw` (rows counted by rules 1-2) and
`requests_deduplicated` (after the duplicate rule) both appear in the report and in
docs/REQUEST-LEDGER.md. Neither figure is ever dropped: a reader re-derives either.

REVERSAL 2026-10-26 (LEDGER-CONSERVATIVE) -- the headline is the RAW figure.
----------------------------------------------------------------------------
This module published `requests` = 1,071 (de-duplicated, 3,249 remaining) for one pass. That
was withdrawn: the duplicate rule's tuple cannot decide request identity, because its only
discriminating field is a hash of the RESPONSE. `content_sha256` is
sha256(assistant `content`) -- `run_longrun.py:1555`, and every one of the 869 rows that
carry it satisfies `content_sha256 == sha256(content)`. Two different requests that returned
the same text (a repeated "OK", a retried turn, a deterministic short answer) therefore share
the tuple, and subtracting the excess UNDERSTATES spend. `V-DUPLICATE-RULE` graded attack 3
(`overall: fail`) for exactly this.

So the published headline `requests` is **raw** (1,101 / 3,219 remaining) and the
de-duplicated figure lives under `diagnostic`, visible and explicitly NOT deducted, until a
request-identity hash exists (`DEDUPE-ROOT-CAUSE`). The rule itself is untouched: it still
runs, still reports its groups, and is still evidence. Only its AUTHORITY TO SUBTRACT was
revoked, and `deduction_permitted()` is the single place that decides -- it requires both a
flag and an evidence path, so the number cannot flip back silently.

EXCLUSION MARKERS -- WHAT THE WRITER ACTUALLY EMITS
---------------------------------------------------
Rules 3-5 name `billed`, `followup_suppressed` and `served_from`. A census of the corpus
finds those three on ZERO top-level rows: they are dead branches at row level (they do occur
nested inside `tool_calls[]`, where they describe the served block or a refused follow-up --
not the billing of the row). The fields the writer really emits are `billed_round`,
`fetch_followup` and `prompt_served`, and NONE of them is a request-suppression marker:

  * `billed_round: false`  -- a follow-up that read no fresh lines (a pinned prompt serve).
                              It costs no fetch ROUND; it is still a request. The writer's own
                              `followups_spent()` counts it ("cost no round ... not free").
  * `fetch_followup: true`  -- marks a row that IS a real follow-up request. Excluding it
                              would delete 68 real requests.
  * `prompt_served`         -- a per-round cache-accounting counter (0/1/2), not
                              `served_from`. A row with `prompt_served=1` still bought a call.

`build_report()["marker_reconciliation"]` reports all six with their corpus occurrence count
and whether each can change the count. No marker in the corpus can: the exclusion branches
are implemented (a future writer may emit `billed: false` and it will be honoured) but today
they are unreachable, and the report says so instead of pretending they are exercised.

Note on fields that LOOK like suppression but are not licensed as such:
  * `is_checkpoint` is NOT a billing marker. In the real corpus the 23 is_checkpoint=True
    rows are distinct inference calls with their own prompt/completion tokens (0 duplicate
    (arm,task,turn,rep) keys), so they count.
If you want a new exclusion, add it here AND in docs/REQUEST-LEDGER.md, with a corpus count.

USAGE
-----
  python3 experiments/ptr-engine/tools/request_ledger.py                    # report
  python3 ...request_ledger.py --would-spend 40 --cap 4320 --reserve 200    # gate
  python3 ...request_ledger.py --write experiments/ptr-engine/measure/REQUEST-LEDGER.json
  python3 ...request_ledger.py --glob 'measure/rows-*.jsonl'               # tests use this

EXIT CODES
----------
  0  within budget (spent + would_spend <= cap - reserve)
  3  usage error (bad arguments, no row files, unreadable directory)
  4  would exceed budget -- the arithmetic is printed on stderr, using the DE-DUPLICATED
     spend figure and saying so
  5  a row file is unreadable or unparseable -- nothing is counted silently

The tool writes ONLY its own output file (--write) and never a row file.
"""

from __future__ import annotations

import argparse
import collections
import glob as globmod
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# --- exit codes ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_USAGE = 3
EXIT_OVER = 4
EXIT_ROWS = 5

DEFAULT_CAP = 4320
DEFAULT_RESERVE = 0

RULE = (
    "one request per row that IS one wire request: kind in {turn, tool-followup, "
    "turn-initial, digest} count (each traced to its make_row call site in run_longrun.py); "
    "billed=false, followup_suppressed, served_from=='prompt' do not; a row with NO kind is "
    "counted and flagged assumed_billed; an UNRECOGNISED non-empty kind is refused "
    "(UnrecognisedKind), never silently billed or unbilled"
)

DEDUP_RULE = (
    "identical (ts, content_sha256, prompt_tokens, completion_tokens) within one file; "
    "first occurrence kept"
)

# The closed vocabulary of kinds that each cost exactly ONE wire request. Every entry has
# a make_row call site as evidence (see row_bills). Adding one requires that evidence.
COUNTED_KINDS = ("turn", "tool-followup", "turn-initial", "digest",
                 # agentic_cell.py: one row per step, and every step is exactly one
                 # send_chat call (run_episode's loop increments `requests` immediately
                 # before `send`).  `work` is a non-final step, `final` the last one.
                 "work", "final")

# --- WHAT MAY BE DEDUCTED (LEDGER-CONSERVATIVE, 2026-10-26) -----------------------------
# The rule above stays as it is: it is evidence and it still runs. This flag decides only
# whether its excess may be SUBTRACTED from the published spend. It may not: the tuple's
# discriminating field is a hash of the RESPONSE, so tuple identity is not request identity
# and a deduction understates spend by the excess (30 requests today).
DEDUCTION_RULE_SOUND = False
DEDUCTION_EVIDENCE_KEY = "request_identity_hash"
DEDUCTION_REASON = (
    "rule unsound: content_sha256 hashes assistant content (run_longrun.py:1493, 869/869), "
    "so tuple identity is not request identity; V-DUPLICATE-RULE overall fail"
)
DEDUCTION_EVIDENCE_NOTE = (
    "the card's line number has drifted: the assignment is run_longrun.py:1555 "
    "(`\"content_sha256\": (sha256_text(recorded_content)`), i.e. sha256 of the assistant's "
    "`content` field; re-measured offline over all 1,101 rows -- 869 carry the hash and "
    "869/869 equal sha256(content)"
)


def deduction_permitted(deduction_rule_sound=None, sound_rule_evidence=None) -> tuple[bool, str]:
    """May the duplicate rule's excess be subtracted? Returns ``(permitted, reason)``.

    Two conditions, in order: the flag, and EVIDENCE that a request-identity hash exists.
    A flag without evidence raises -- flipping it must not be a silent act, and it must not
    be possible by editing one boolean.
    """
    sound = DEDUCTION_RULE_SOUND if deduction_rule_sound is None else bool(deduction_rule_sound)
    if not sound:
        return False, DEDUCTION_REASON
    if not isinstance(sound_rule_evidence, dict):
        raise ValueError(
            "deduction_rule_sound=True requires sound_rule_evidence={%r: <hash name>}: a flag "
            "alone cannot authorise subtracting requests" % DEDUCTION_EVIDENCE_KEY
        )
    value = sound_rule_evidence.get(DEDUCTION_EVIDENCE_KEY)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "deduction_rule_sound=True but sound_rule_evidence carries no non-empty %r: the "
            "tuple is sound only once a request-identity hash exists (DEDUPE-ROOT-CAUSE), and "
            "no such hash does today" % DEDUCTION_EVIDENCE_KEY
        )
    return True, "deducted under sound rule: %s=%s" % (DEDUCTION_EVIDENCE_KEY, value.strip())

# Every marker the ledger knows about, and what it is allowed to do. `excludes` markers are
# implemented exclusions; `observes` markers are the fields the writer really emits and they
# are REPORTED, never subtracted (see the module docstring).
ROW_MARKER_FIELDS = (
    "billed",
    "followup_suppressed",
    "served_from",
    "billed_round",
    "fetch_followup",
    "prompt_served",
)

MARKER_POLICY = {
    "billed": {
        "scope": "row",
        "excludes": True,
        "verdict": (
            "implemented exclusion (row says it was not billed); DEAD in this corpus -- 0 rows "
            "carry the field, so it can never change the count today"
        ),
    },
    "followup_suppressed": {
        "scope": "row",
        "excludes": True,
        "verdict": (
            "implemented exclusion (client skipped the call); DEAD at row level -- 0 rows carry "
            "the field. It occurs only NESTED inside tool_calls[], where the writer records a "
            "follow-up the allowance refused; that refusal emitted no row, so a row-level check "
            "can never see it"
        ),
    },
    "served_from": {
        "scope": "row",
        "excludes": True,
        "verdict": (
            "implemented exclusion (served out of the prompt, no call); DEAD at row level -- 0 "
            "rows carry the field. `served_from: prompt` occurs NESTED inside tool_calls[], "
            "describing the served block of a follow-up that was still bought as a request"
        ),
    },
    "billed_round": {
        "scope": "row",
        "excludes": False,
        "verdict": (
            "writer-emitted, NOT an exclusion: it marks whether a follow-up read fresh lines and "
            "so consumed a fetch ROUND. A pinned prompt serve costs no round and is still a "
            "request -- the writer's own followups_spent() counts it. False rows stay counted"
        ),
    },
    "fetch_followup": {
        "scope": "row",
        "excludes": False,
        "verdict": (
            "writer-emitted, NOT an exclusion: it marks a row that IS a real follow-up request "
            "(kind=tool-followup). Treating it as suppression would delete 68 real requests"
        ),
    },
    "prompt_served": {
        "scope": "row",
        "excludes": False,
        "verdict": (
            "writer-emitted, NOT an exclusion: a per-round cache-accounting counter (0/1/2), not "
            "the `served_from` marker. A row with prompt_served=1 still bought a request"
        ),
    },
}

# Truthy spellings a row file may use for a boolean-ish JSON field.
_TRUE = {"true", "1", "yes", "y", "t"}


class RowsUnreadable(Exception):
    """A row file could not be read or parsed -- fatal under exit code 5."""


def _truthy(value) -> bool:
    """Interpret a JSON field as a boolean without inventing meaning for absent values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in _TRUE
    return bool(value)


def _value_label(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def suppression_marker(row: dict) -> str | None:
    """Return the name of the top-level exclusion marker this row carries, or None.

    The vocabulary is closed by the unit contract; see the module docstring. Only the three
    markers that mean "no request left the client" are here -- `billed_round`,
    `fetch_followup` and `prompt_served` are deliberately absent (they mark real requests).
    """
    if "billed" in row and not _truthy(row["billed"]):
        return "billed:false"
    if "followup_suppressed" in row and _truthy(row["followup_suppressed"]):
        return "followup_suppressed"
    if row.get("served_from") == "prompt":
        return "served_from:prompt"
    return None


class UnrecognisedKind(Exception):
    """A row declares a `kind` the closed vocabulary does not contain.

    LEDGER-KIND-RULE: this is a REFUSAL, not a default. Billing it would invent a request
    the rule never authorised; not billing it would delete a request that may well have hit
    the wire. Either guess corrupts the budget silently, so neither is made.
    """


# --- THE ONE RULE (LEDGER-KIND-RULE, 2026-10-27) ----------------------------------------
# `row_bills` is the ONLY authority on "does this row cost one request". It is imported by
# run_a_star.py::_row_counts, so the recount (request_ledger) and the attribution
# (run_a_star) cannot diverge again -- they did, by 30 `turn-initial` rows, and refused a
# 1,056-request grid at gate 2 with zero sent.
def row_bills(row: dict) -> bool:
    """True iff this row is ONE wire request. THE rule; every other tally delegates here.

    Evidence per kind, from the writer (`longrun/run_longrun.py` make_row call sites) and
    the sender (`longrun/client.py` send_chat):

      turn          -- run_longrun.py:2703 make_row(..., "turn", ...); the request is gated
                       at :2527 gate.acquire(t, "turn") and sent before it. It is the row of
                       the turn's only send, or (with k>=1 follow-ups) of follow-up k.
      tool-followup -- run_longrun.py:1126 make_row(..., "tool-followup", ...); gated at
                       :1115 gate.acquire(t, "tool-followup"), one follow-up request each.
      turn-initial  -- run_longrun.py:2726-2729 make_row(..., "turn-initial", ...); the
                       INITIAL send's own row under ROW-ATTRIBUTION. run_longrun.py:2672:
                       "With k >= 1 follow-ups this turn made k+1 requests: the initial send
                       (row_initial, below), follow-ups 1..k-1 ... and follow-up k, whose
                       row IS this turn row." One row per send, so it bills.
      digest        -- run_longrun.py:2479 gate.acquire(t, "digest") then :2481
                       resp = send_chat(cfg, msg); rows at :2491/:2504/:2512 "digest".
                       A planning request on the wire; it bills.
      (no kind)     -- legacy schema (rows-baseline/rows-equalinfo/rows-live): the row
                       cannot decide, so it is COUNTED and flagged assumed_billed. Counting
                       is the conservative direction: a real request must not vanish from
                       the budget.
      tool_call     -- NOT a kind and never passed to make_row. `tool_calls` is a row FIELD
                       (run_longrun.py:2692 row_extra["tool_calls"] = turn_calls) describing
                       calls the turn row already bills; it adds no request of its own.

    Unknown non-empty kind -> UnrecognisedKind. No silent bill, no silent unbill.
    """
    if suppression_marker(row) is not None:
        return False
    kind = row.get("kind")
    if kind is None:
        return True
    if isinstance(kind, str) and kind in COUNTED_KINDS:
        return True
    raise UnrecognisedKind(
        "unrecognised row kind %r (known: %s) -- refusing to bill OR unbill it; extend "
        "COUNTED_KINDS only with a make_row call site that proves one wire request"
        % (kind, ", ".join(sorted(COUNTED_KINDS))))


def classify(row: dict) -> tuple[int, int]:
    """Return (requests, assumed_billed) for one row. Exactly one of them is 1 when counted."""
    if suppression_marker(row) is not None:
        return 0, 0
    row_bills(row)
    kind = row.get("kind")
    if kind is None:
        # No kind marker: counted, and the doubt is reported rather than laundered.
        return 1, 1
    return 1, 0


def _ts_key(row: dict) -> tuple:
    """Ordering key for a row timestamp: parsed instant when possible, else the raw string."""
    raw = row.get("ts", row.get("ts_utc"))
    if raw is None:
        return (2, "")
    text = str(raw)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return (0, "", parsed.timestamp())
    except (ValueError, TypeError):
        return (1, text, 0.0)


def _ts_text(row: dict) -> str | None:
    raw = row.get("ts", row.get("ts_utc"))
    return None if raw is None else str(raw)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dedup_key(row: dict) -> tuple:
    """The duplicate rule's tuple, exactly as TVS-REGRADE defined it (no field invented)."""
    return (
        str(row.get("ts")),
        row.get("content_sha256"),
        row.get("prompt_tokens"),
        row.get("completion_tokens"),
    )


def undecidable_key(row: dict) -> tuple:
    """What the tuple would collapse to on a legacy file, where content_sha256 is absent.

    Used ONLY to report the collisions the rule would have merged had it been applied -- the
    number is never subtracted from a count.
    """
    return (
        str(row.get("ts", row.get("ts_utc"))),
        None,
        row.get("prompt_tokens"),
        row.get("completion_tokens"),
    )


def dedup_decidable(rows: list[tuple[int, dict, int]]) -> tuple[bool, str]:
    """Can the duplicate rule be decided on this file's schema?

    Decidable only when EVERY row carries a non-empty `content_sha256` and a
    millisecond-resolution `ts`. The 5-file/9-file split asserted by the card is not what the
    corpus shows (11 files carry content_sha256 and a millisecond ts; 3 are legacy-schema);
    this function asks the schema, not the card, and the report carries both counts.
    """
    if not rows:
        return False, "empty file: nothing to decide"
    for lineno, row, _counted in rows:
        digest = row.get("content_sha256")
        if not isinstance(digest, str) or not digest:
            return False, (
                f"legacy schema: line {lineno} has no content_sha256, so the tuple cannot "
                f"distinguish a duplicate from a second identical request"
            )
        ts = row.get("ts")
        if not isinstance(ts, str) or "." not in ts:
            return False, (
                f"legacy schema: line {lineno} ts is not millisecond-resolution, so two distinct "
                f"requests inside one second collide on the tuple"
            )
    return True, (
        "decided: every row carries content_sha256 and a millisecond-resolution ts, so the "
        "tuple distinguishes a duplicate from a second identical request"
    )


def scan_file(path: str) -> dict:
    """Count one row file. Raises RowsUnreadable on any unreadable/unparseable line."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise RowsUnreadable(f"{path}: unreadable: {exc}") from exc

    rows = requests = assumed = 0
    first_key = None
    last_key = None
    first_ts = last_ts = None
    suppressed: list[dict] = []
    scanned: list[tuple[int, dict, int]] = []
    census: dict[str, collections.Counter] = {field: collections.Counter() for field in ROW_MARKER_FIELDS}
    nested = collections.Counter()

    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RowsUnreadable(f"{path}:{lineno}: unparseable row: {exc}") from exc
        if not isinstance(row, dict):
            raise RowsUnreadable(f"{path}:{lineno}: row is {type(row).__name__}, not an object")

        rows += 1
        marker = suppression_marker(row)
        try:
            counted, flagged = classify(row)
        except UnrecognisedKind as exc:
            # A refusal, carried out as a row-file error: the total is unknowable, so
            # nothing is counted (exit 5) instead of a guessed figure being published.
            raise RowsUnreadable(f"{path}:{lineno}: {exc}") from exc
        requests += counted
        assumed += flagged
        scanned.append((lineno, row, counted))
        if marker is not None:
            suppressed.append({"file": os.path.basename(path), "line": lineno, "marker": marker})

        for field in ROW_MARKER_FIELDS:
            if field in row:
                census[field][_value_label(row[field])] += 1
        for call in row.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            if call.get("followup_suppressed"):
                nested["followup_suppressed"] += 1
            if call.get("served_from") == "prompt":
                nested["served_from:prompt"] += 1

        key = _ts_key(row)
        if first_key is None or key < first_key:
            first_key, first_ts = key, _ts_text(row)
        if last_key is None or key > last_key:
            last_key, last_ts = key, _ts_text(row)

    # --- the duplicate rule, applied only where the schema can decide it --------------------
    decidable, reason = dedup_decidable(scanned)
    duplicate_groups = 0
    duplicate_excess = 0
    dedup_requests = requests
    collisions_not_applied = None
    duplicate_rows: list[dict] = []

    dedupe_applied = True
    if dedupe_applied and decidable:
        seen: dict[tuple, int] = {}
        members: dict[tuple, list[int]] = {}
        for lineno, row, counted in scanned:
            if not counted:
                continue
            key = dedup_key(row)
            if key in seen:
                duplicate_excess += 1
                members[key].append(lineno)
                # Recorded, never subtracted on its own authority: the row, the row it
                # mirrors, and the fields the tuple matched. build_report decides whether
                # any of them may be deducted (today: none -- see deduction_permitted).
                duplicate_rows.append({
                    "file": os.path.basename(path),
                    "line": lineno,
                    "duplicate_of_line": seen[key],
                    "ts": row.get("ts"),
                    "content_sha256": row.get("content_sha256"),
                    "prompt_tokens": row.get("prompt_tokens"),
                    "completion_tokens": row.get("completion_tokens"),
                    "kind": row.get("kind"),
                })
            else:
                seen[key] = lineno
                members[key] = [lineno]
        duplicate_groups = sum(1 for grouped in members.values() if len(grouped) > 1)
        dedup_requests = requests - duplicate_excess
        rule_status = "decided"
    elif decidable:
        rule_status = "decided"
    else:
        rule_status = "not_applicable"
        # Observation only: what the literal tuple would have merged on this schema.
        groups = collections.Counter(
            undecidable_key(row) for _lineno, row, counted in scanned if counted
        )
        if any(size > 1 for size in groups.values()):
            collisions_not_applied = {
                "groups": sum(1 for size in groups.values() if size > 1),
                "excess": sum(size - 1 for size in groups.values()),
                "note": (
                    "the literal tuple would merge these, but rows that collide on a "
                    "second-resolution ts_utc differ in rep and latency_s -- distinct requests. "
                    "Not subtracted."
                ),
            }

    try:
        digest = sha256_file(path)
    except OSError as exc:
        raise RowsUnreadable(f"{path}: unreadable for hashing: {exc}") from exc

    return {
        "file": os.path.basename(path),
        "sha256": digest,
        "rows": rows,
        "requests": requests,
        "requests_deduplicated": dedup_requests,
        "dedup": dedup_requests,
        "duplicate_groups": duplicate_groups,
        "duplicate_excess": duplicate_excess,
        "duplicate_rows": duplicate_rows,
        "rule_status": rule_status,
        "rule_reason": reason,
        "assumed_billed": assumed,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "suppressed": suppressed,
        "marker_census": {field: dict(counter) for field, counter in census.items() if counter},
        "nested_markers": dict(nested),
        "collisions_not_applied": collisions_not_applied,
    }


def _marker_reconciliation(files: list[dict]) -> list[dict]:
    totals: dict[str, collections.Counter] = {field: collections.Counter() for field in ROW_MARKER_FIELDS}
    nested = collections.Counter()
    for entry in files:
        for field, values in entry["marker_census"].items():
            totals[field].update(values)
        nested.update(entry["nested_markers"])

    out = []
    for field in ROW_MARKER_FIELDS:
        policy = MARKER_POLICY[field]
        values = dict(totals[field])
        occurrences = sum(values.values())
        if not policy["excludes"]:
            can_change = False
            why = "reported, never subtracted: " + policy["verdict"]
        elif occurrences == 0:
            can_change = False
            why = policy["verdict"]
        else:
            can_change = True
            why = "implemented and exercised by this corpus"
        out.append(
            {
                "marker": field,
                "scope": policy["scope"],
                "excludes": policy["excludes"],
                "corpus_occurrences": occurrences,
                "corpus_values": values,
                "nested_occurrences": (
                    nested["followup_suppressed"] if field == "followup_suppressed"
                    else nested["served_from:prompt"] if field == "served_from"
                    else 0
                ),
                "can_change_count": can_change,
                "verdict": why,
            }
        )
    return out


def build_report(paths: list[str], cap: int, reserve: int, would_spend: int,
                 *, deduction_rule_sound=None, sound_rule_evidence=None) -> dict:
    files = []
    suppressed_all: list[dict] = []
    # Sorting by file NAME, never by directory-listing order.
    for path in sorted(paths, key=lambda p: os.path.basename(p)):
        entry = scan_file(path)
        suppressed_all.extend(entry.pop("suppressed"))
        files.append(entry)

    total_rows = sum(f["rows"] for f in files)
    requests_raw = sum(f["requests"] for f in files)
    requests_dedup = sum(f["requests_deduplicated"] for f in files)
    total_assumed = sum(f["assumed_billed"] for f in files)
    duplicate_excess = requests_raw - requests_dedup
    files_deduped = sum(1 for f in files if f["rule_status"] == "decided")
    files_na = sum(1 for f in files if f["rule_status"] == "not_applicable")
    headroom = cap - reserve

    # --- the ONE place a deduction is authorised -----------------------------------------
    # `requests` is what anything may spend against. It equals the RAW count unless a sound
    # rule is both flagged AND evidenced. The de-duplicated number is still computed and
    # still published -- in `diagnostic`, with `deducted: false` -- because a reversal that
    # hides the figure it reversed cannot be audited.
    deduct, deduction_reason = deduction_permitted(deduction_rule_sound, sound_rule_evidence)
    requests_published = (requests_raw - duplicate_excess) if deduct else requests_raw
    deducted_excess = duplicate_excess if deduct else 0

    projected = requests_published + would_spend
    projected_raw = requests_raw + would_spend
    projected_dedup = requests_dedup + would_spend

    candidate_rows = []
    for entry in files:
        for row in entry.get("duplicate_rows") or []:
            candidate_rows.append(dict(row, deducted=bool(deduct), reason=deduction_reason))

    return {
        "unit": "REQUEST-LEDGER",
        "requests_raw": requests_raw,
        "requests_deduplicated": requests_dedup,
        "requests": requests_published,
        "remaining_raw": headroom - projected_raw,
        "remaining": headroom - projected,
        "remaining_deduplicated": headroom - projected_dedup,
        "duplicate_excess": duplicate_excess,
        "dedup_rule": DEDUP_RULE,
        "deduction_rule_sound": bool(deduct),
        "deduction": {
            "applied": bool(deduct),
            "candidate_excess": duplicate_excess,
            "deducted_requests": deducted_excess,
            "reason": deduction_reason,
            "evidence_required": DEDUCTION_EVIDENCE_KEY,
            "evidence_note": DEDUCTION_EVIDENCE_NOTE,
            "publishes": "requests == requests_raw unless a sound rule with evidence is present",
        },
        "diagnostic": {
            "deducted": False,
            "why": ("kept visible so the reversal is auditable; NOT subtracted from spend "
                    "because the rule is unsound as a request-identity test"),
            "requests_deduplicated": requests_dedup,
            "duplicate_excess": duplicate_excess,
            "remaining_deduplicated": headroom - projected_dedup,
            "per_file_excess": {
                f["file"]: f["duplicate_excess"] for f in files if f["duplicate_excess"]
            },
            "per_file_deducted": {
                f["file"]: (f["duplicate_excess"] if deduct else 0)
                for f in files if f["duplicate_excess"]
            },
            "reason": deduction_reason,
            "evidence_note": DEDUCTION_EVIDENCE_NOTE,
            "rows": candidate_rows,
        },
        "files_deduped": files_deduped,
        "files_not_applicable": files_na,
        "dedup_decision": {
            "decidable_when": (
                "every row in the file carries a non-empty content_sha256 and a "
                "millisecond-resolution ts"
            ),
            "files_deduped": files_deduped,
            "files_not_applicable": files_na,
            "files_not_applicable_names": [
                f["file"] for f in files if f["rule_status"] == "not_applicable"
            ],
            "count_discrepancy": (
                "The REQUEST-LEDGER-2 card (and TVS-REGRADE's headline) say 9 decidable files and "
                "5 legacy files. A direct schema census says 11 and 3: the three files that cannot "
                "be decided are rows-baseline, rows-equalinfo and rows-live, all of which carry a "
                "second-resolution ts_utc and no content_sha256. The published arithmetic -- 30 "
                "excess rows, 1,071 de-duplicated requests -- is identical either way, because "
                "every one of the 30 excess rows sits in a decidable file."
            ),
        },
        "rule": RULE,
        "counting": {
            "counted_kinds": list(COUNTED_KINDS),
            "exclusion_markers": ["billed:false", "followup_suppressed", "served_from:prompt"],
            "not_exclusion_markers": {
                "billed_round": "fetch-ROUND accounting; a pinned serve is still a request",
                "fetch_followup": "marks a row that IS a real follow-up request",
                "prompt_served": "cache-accounting counter, not served_from",
                "is_checkpoint": "NOT a billing marker: checkpoint rows are genuine calls",
            },
            "assumed_billed_means": (
                "row carries no recognised kind marker; counted because an unmarked row that "
                "reached the wire must not vanish from the budget"
            ),
        },
        "marker_reconciliation": _marker_reconciliation(files),
        "budget": {
            "cap": cap,
            "reserve": reserve,
            "headroom": headroom,
            "spent": requests_published,
            "spent_deduplicated": requests_dedup,
            "spent_raw": requests_raw,
            "would_spend": would_spend,
            "projected": projected,
            "projected_raw": projected_raw,
            "projected_deduplicated": projected_dedup,
            "remaining": headroom - projected,
            "remaining_raw": headroom - projected_raw,
            "remaining_deduplicated": headroom - projected_dedup,
            "within_budget": projected <= headroom,
        },
        "total": {
            "files": len(files),
            "rows": total_rows,
            "requests": requests_published,
            "requests_raw": requests_raw,
            "requests_deduplicated": requests_dedup,
            "duplicate_excess": duplicate_excess,
            "assumed_billed": total_assumed,
            "files_deduped": files_deduped,
            "files_not_applicable": files_na,
        },
        "per_file": files,
        "files": files,  # back-compat alias; identical rows, never a second derivation
        "suppressed": suppressed_all,
    }


def reconcile(paths=None, pattern=None, cap=DEFAULT_CAP, reserve=DEFAULT_RESERVE,
          would_spend=0):
    """Reconcile row count on disk with ledger spend.

    Counts non-empty lines in rows-*.jsonl (how longrun/cell.py computes spend)
    and compares with build_report()["budget"]["spent"]. Returns
    {rows_on_disk, ledger_spent, delta, verdict}; verdict is "agree" only when
    they match. Prints a warning naming both numbers on disagreement; never
    auto-corrects either side.
    """
    if isinstance(paths, str):
        # allow a glob pattern to be passed positionally
        pattern = paths
        paths = None
    if paths is None:
        pat = resolve_pattern(pattern)
        paths = sorted(globmod.glob(pat), key=lambda p: os.path.basename(p))
    paths = list(paths or [])
    rows_on_disk = 0
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.strip():
                        rows_on_disk += 1
        except OSError:
            raise
    report = build_report(paths, cap, reserve, would_spend)
    ledger_spent = report["budget"]["spent"]
    delta = rows_on_disk - ledger_spent
    verdict = "agree" if delta == 0 else "disagree"
    if verdict == "disagree":
        print("WARNING: rows_on_disk=%d != ledger_spent=%d (delta=%d)"
              % (rows_on_disk, ledger_spent, delta), file=sys.stderr)
    return {"rows_on_disk": rows_on_disk, "ledger_spent": ledger_spent,
            "delta": delta, "verdict": verdict}


def print_table(report: dict, stream=sys.stdout) -> None:
    files = report["files"]
    width = max([len("file")] + [len(f["file"]) for f in files]) if files else 4
    head = (
        f"{'file':<{width}}  {'rows':>6}  {'raw':>6}  {'dedup':>6}  {'dup':>4}  "
        f"{'rule':<14}  {'assumed':>7}  {'first_ts':<27}  {'last_ts':<27}  sha256"
    )
    print(head, file=stream)
    print("-" * len(head), file=stream)
    for f in files:
        print(
            f"{f['file']:<{width}}  {f['rows']:>6}  {f['requests']:>6}  "
            f"{f['requests_deduplicated']:>6}  {f['duplicate_excess']:>4}  "
            f"{f['rule_status']:<14}  {f['assumed_billed']:>7}  "
            f"{str(f['first_ts']):<27}  {str(f['last_ts']):<27}  {f['sha256']}",
            file=stream,
        )
    total = report["total"]
    print("-" * len(head), file=stream)
    print(
        f"{'TOTAL':<{width}}  {total['rows']:>6}  {total['requests_raw']:>6}  "
        f"{total['requests_deduplicated']:>6}  {total['duplicate_excess']:>4}  "
        f"{total['files_deduped']:>2} decided/{total['files_not_applicable']} n/a  "
        f"{total['assumed_billed']:>7}  ({total['files']} files)",
        file=stream,
    )
    budget = report["budget"]
    print(
        f"budget: spent={budget['spent']} would_spend={budget['would_spend']} "
        f"cap={budget['cap']} reserve={budget['reserve']} headroom={budget['headroom']} "
        f"projected={budget['projected']} remaining={budget['remaining']} "
        f"(spent is the RAW count; de-duplicated diagnostic spent={budget['spent_deduplicated']} "
        f"remaining={budget['remaining_deduplicated']} -- NOT deducted)",
        file=stream,
    )
    for item in report["marker_reconciliation"]:
        flag = "SUBTRACTS" if item["can_change_count"] else "no effect"
        print(
            f"marker {item['marker']}: {item['corpus_occurrences']} row(s) "
            f"{item['corpus_values'] or ''} nested={item['nested_occurrences']} -> {flag}",
            file=stream,
        )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count inference requests from row files and gate spending against a cap.",
        epilog="exit: 0 within budget | 4 would exceed | 3 usage error | 5 unreadable row file",
    )
    parser.add_argument(
        "--glob",
        dest="pattern",
        default=None,
        help="glob pattern for row files (default: <repo>/experiments/ptr-engine/measure/rows-*.jsonl)",
    )
    parser.add_argument("--cap", type=int, default=DEFAULT_CAP, help=f"request cap (default {DEFAULT_CAP})")
    parser.add_argument("--reserve", type=int, default=DEFAULT_RESERVE, help="unspendable reserve (default 0)")
    parser.add_argument("--would-spend", type=int, default=0, dest="would_spend", help="requests about to be sent")
    parser.add_argument("--write", default=None, help="write the JSON report to this path (and only this)")
    parser.add_argument("--json", action="store_true", help="print the JSON report to stdout too")
    parser.add_argument("--quiet", action="store_true", help="print nothing on the within-budget path")
    parser.add_argument("--reconcile", action="store_true",
                        help="print reconcile() JSON (rows_on_disk vs ledger_spent) and exit")
    return parser.parse_args(argv)


def resolve_pattern(pattern: str | None) -> str:
    if pattern:
        return pattern
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "measure", "rows-*.jsonl")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.cap < 0 or args.reserve < 0 or args.would_spend < 0:
        print("usage error: --cap, --reserve and --would-spend must be >= 0", file=sys.stderr)
        return EXIT_USAGE
    if args.reserve > args.cap:
        print(
            f"usage error: --reserve {args.reserve} exceeds --cap {args.cap} (no headroom exists)",
            file=sys.stderr,
        )
        return EXIT_USAGE

    pattern = resolve_pattern(args.pattern)
    paths = sorted(globmod.glob(pattern), key=lambda p: os.path.basename(p))
    if not paths:
        print(f"usage error: no row files matched {pattern!r}", file=sys.stderr)
        return EXIT_USAGE

    try:
        report = build_report(paths, args.cap, args.reserve, args.would_spend)
    except RowsUnreadable as exc:
        print(f"row file error: {exc}", file=sys.stderr)
        print("nothing counted: an unreadable row file makes the total unknowable", file=sys.stderr)
        return EXIT_ROWS

    if getattr(args, "reconcile", False):
        rec = reconcile(paths, cap=args.cap, reserve=args.reserve, would_spend=args.would_spend)
        print(json.dumps(rec, indent=2, sort_keys=False, ensure_ascii=False))
        return EXIT_OK
    payload = json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n"

    if args.write:
        parent = os.path.dirname(os.path.abspath(args.write))
        if parent and not os.path.isdir(parent):
            print(f"usage error: output directory does not exist: {parent}", file=sys.stderr)
            return EXIT_USAGE
        try:
            with open(args.write, "w", encoding="utf-8") as handle:
                handle.write(payload)
        except OSError as exc:
            print(f"usage error: cannot write {args.write}: {exc}", file=sys.stderr)
            return EXIT_USAGE

    if not args.quiet:
        print_table(report)
        if args.json:
            print(payload, end="")

    budget = report["budget"]
    if not budget["within_budget"]:
        print(
            "OVER BUDGET: "
            f"spent={budget['spent']} + would_spend={budget['would_spend']} = {budget['projected']} "
            f"> cap={budget['cap']} - reserve={budget['reserve']} = {budget['headroom']} "
            f"(over by {budget['projected'] - budget['headroom']}) "
            f"[spent={budget['spent']} would_spend={budget['would_spend']} "
            f"cap={budget['cap']} reserve={budget['reserve']} headroom={budget['headroom']}] "
            f"(spent is the RAW count; the de-duplicated diagnostic figure is "
            f"{budget['spent_deduplicated']} and is NOT deducted -- the duplicate rule is "
            f"unsound as a request-identity test)",
            file=sys.stderr,
        )
        return EXIT_OVER

    if not args.quiet:
        print(
            f"within budget: {budget['projected']} <= {budget['headroom']} "
            f"({budget['remaining']} left; spent is the RAW count, de-duplicated diagnostic "
            f"{budget['spent_deduplicated']} is NOT deducted)",
        )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
