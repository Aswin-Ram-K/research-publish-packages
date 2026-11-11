#!/usr/bin/env python3
"""predict_answer_slot.py — the answer-slot-binding rule, as a predictor with no model call.

WHAT U-SPCC-67 CLAIMED, AND WHAT THIS TOOL DOES WITH IT
-------------------------------------------------------
U-SPCC-67 diagnosed the 6/48 masking-arm gap (`docs/STATE.md` §U-SPCC-64, subsection "The
6/48 gap is answer-slot binding") as a prompt-format effect: the masking arm's flat
transcript replays every prior turn as

    QUESTION (Tt) / TOOL OUTPUTS: / TOOL_OUTPUT (doc@rev): body / ANSWER (Tt): value

so the answer slot sits immediately BELOW a tool-output block, and a model that has read
29 such blocks answers the next slot from the block above it.  On a checkpoint turn the
fixture delivers a body for a *different* document than the one the question names, so the
positional rule copies the wrong document's value.  The `spcc` arm replays no `ANSWER`
lines at all (its journal carries `T{n}|{role}|{content}`), so it has no positional rule to
bind to.

That diagnosis was made by READING five prompts (`prompt_at_turn.py`), i.e. after the fact,
on the turns that had already failed.  This tool turns it into a PREDICTION that can be
made before the answers are looked at, over all 48 checkpoints of both arms.

THE RULE (fixed before this tool ever read the rows)
---------------------------------------------------
For a checkpoint turn `T` of a settled cell, re-materialise the exact prompt `T` received
with the `prompt_at_turn.py` method (import `run_longrun`, replace `send_chat` with a
recorder, drive `run_cell` with the recorded assistant replies — the runner's own
`Planner.build` and `checkpoint_prompt`, not a re-implementation).

1. `replays_answers` = the rendered transcript contains at least one `ANSWER (T<d>):` line.
   A prompt that replays answers teaches the positional rule; a prompt that does not
   (`spcc`'s layered compiler) has nothing for a position to bind to.  `replays_answers`
   false  ->  `FREE`, reason `no_answer_replay`.
2. Otherwise (`flat-transcript-replay`), strip the host-appended checkpoint contract
   (`\\n\\nCHECKPOINT TURN.` …), find the current turn's `QUESTION (T{T}):` line, and take
   the LAST `TOOL_OUTPUT (doc@rev): body` block after it — the block immediately above the
   answer slot.  No such block  ->  `FREE`, reason `no_delivery_above`.
3. A block above is a delivery of a document DIFFERENT from the asked document AND it
   carries a line for the asked symbol position (`VAL_C = 4083`)  ->  `BOUND`, with
   `predicted_value` the value on that line.  Same document  ->  `FREE`
   (`same_document`); different document without the asked symbol  ->  `FREE`
   (`symbol_not_in_delivery`).
4. `predicted_answer_class`: `BOUND` predicts a WRONG answer (it copies the delivered
   value), `FREE` predicts a RIGHT answer.

No threshold, distance cut, turn list or naming rule was chosen after seeing the rows: the
rule reads only prompt SHAPE and the fixture's own checkpoint metadata.  The report states
this in `thresholds_chosen_after_seeing_rows: false`, and the predictor never reads a
row's answer to decide a classification — the answer is joined afterwards, only to score
the prediction.

ZERO NETWORK
------------
The same five outbound primitives `prompt_at_turn.py` pins (`urllib.request.urlopen`,
`urllib.request.build_opener`, `http.client.HTTPConnection.connect`,
`http.client.HTTPSConnection.connect`, `socket.create_connection`) are replaced with
recorders that raise, and the tool REFUSES to report (exit 9) if any attempt was recorded.
`run_cell` also probes the endpoint for the manifest's provenance fingerprints
(`run_longrun.probe_fingerprints`); that probe is refused at its single outbound primitive
(`run_longrun._http_get_json`) and counted SEPARATELY, because a fingerprint probe is not a
request on the measured path.  `requests_sent` is 0 by construction.

    python3 experiments/ptr-engine/tools/predict_answer_slot.py \
        --fixture experiments/ptr-engine/longrun/tasks-v7/TX-04.v1.json \
        --rows experiments/ptr-engine/measure/rows-e3-retain-2026-11-10.jsonl \
        --arms masking-no-fetch,spcc --rep 1 \
        --compact-every 200 --window-turns 200 \
        --json /tmp/predict_answer_slot.json
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import io
import json
import os
import re
import socket
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PTR_ENGINE = os.path.dirname(HERE)
LONGRUN_DIR = os.path.join(PTR_ENGINE, "longrun")
LONGRUN_TOOLS = os.path.join(LONGRUN_DIR, "tools")
for _p in (LONGRUN_DIR, LONGRUN_TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------- zero-network guard
NET_ATTEMPTS: list[str] = []
PROBE_REFUSALS: list[str] = []


def _forbidden(name):
    def boom(*_a, **_k):
        NET_ATTEMPTS.append(name)
        raise AssertionError(
            f"NETWORK REFUSED: {name}() was called — predict_answer_slot.py must never "
            "construct an HTTP client (U-SPCC-77: zero requests)")
    return boom


_ORIGINALS: dict = {}


def install_tripwires() -> None:
    """Replace the five outbound primitives.  Structural, not promised.

    NOT installed at import: this module is imported by the test suite, which shares one
    process with every other test, and a process-global socket patch would turn an
    unrelated test's loopback connection into a failure.  `main()` arms them, and a caller
    that wants them (a test) arms them itself and `restore_tripwires()` when done.
    """
    if not _ORIGINALS:
        _ORIGINALS.update({
            "urllib.request.urlopen": urllib.request.urlopen,
            "urllib.request.build_opener": urllib.request.build_opener,
            "http.client.HTTPConnection.connect": http.client.HTTPConnection.connect,
            "http.client.HTTPSConnection.connect": http.client.HTTPSConnection.connect,
            "socket.create_connection": socket.create_connection,
        })
    urllib.request.urlopen = _forbidden("urllib.request.urlopen")
    urllib.request.build_opener = _forbidden("urllib.request.build_opener")
    http.client.HTTPConnection.connect = _forbidden("http.client.HTTPConnection.connect")
    http.client.HTTPSConnection.connect = _forbidden("http.client.HTTPSConnection.connect")
    socket.create_connection = _forbidden("socket.create_connection")


def restore_tripwires() -> None:
    """Put the primitives back and clear the ledgers (test teardown).

    The state restored is the state found at first install, which in this repo is
    `prompt_at_turn`'s own guard (it arms the same five primitives at its import), so a
    test that arms mine cannot leave the rest of the suite weakly guarded.
    """
    if not _ORIGINALS:
        return
    urllib.request.urlopen = _ORIGINALS["urllib.request.urlopen"]
    urllib.request.build_opener = _ORIGINALS["urllib.request.build_opener"]
    http.client.HTTPConnection.connect = _ORIGINALS["http.client.HTTPConnection.connect"]
    http.client.HTTPSConnection.connect = _ORIGINALS["http.client.HTTPSConnection.connect"]
    socket.create_connection = _ORIGINALS["socket.create_connection"]
    NET_ATTEMPTS.clear()
    PROBE_REFUSALS.clear()
    PT.NET_ATTEMPTS.clear()


import prompt_at_turn as PT  # noqa: E402  (reuse load_settled / canned_resp / make_cfg)
import run_longrun as R  # noqa: E402  (armed by main(); import is side-effect free)


def refuse_fingerprint_probes() -> None:
    """`run_cell` builds a manifest, which probes the endpoint for provenance.

    A fingerprint probe is not a request on the measured path, so it is refused at its
    single outbound primitive and counted on its own ledger (`PROBE_REFUSALS`): the
    manifest then records the documented UNSOURCEABLE value for every probed field.
    """
    def blocked(url, timeout=2.0):  # noqa: ARG001
        PROBE_REFUSALS.append(str(url))
        return None, "offline-replay: fingerprint probe refused by predict_answer_slot.py"
    R._http_get_json = blocked



# ---------------------------------------------------------------- prompt shapes
ANSWER_REPLAY_RE = re.compile(r"(?m)^ANSWER \(T(\d+)\): ")
QUESTION_RE = re.compile(r"(?m)^QUESTION \(T(\d+)\): ")
TOOL_OUTPUT_RE = re.compile(r"^TOOL_OUTPUT \(([^@\s)]+)@([^)\s]+)\): (.*)$")
CONTRACT_MARK = "\n\nCHECKPOINT TURN."
HOST_QUESTION_MARK = "\n\nCHECKPOINT QUESTION: "
GRAMMAR_FLAT = "flat-transcript-replay"
GRAMMAR_LAYERED = "layered-compiler"


def split_host_contract(prompt: str) -> tuple[str, str | None]:
    """Cut the host-appended checkpoint contract off the runner's own rendering.

    The answer slot this tool classifies is the TRANSCRIPT's slot — where the arm's own
    grammar puts `ANSWER (T{t}):` — not the end of the host's instruction block.  The
    contract (and the checkpoint question the host appends when the fixture turn does not
    already carry it) is host text, so it is removed and reported separately.
    """
    cut = len(prompt)
    for mark in (CONTRACT_MARK, HOST_QUESTION_MARK):
        i = prompt.find(mark)
        if 0 <= i < cut:
            cut = i
    return prompt[:cut], (prompt[cut:] if cut < len(prompt) else None)


def parse_deliveries(lines: list[str], start: int) -> list[dict]:
    """Deliveries declared after line ``start`` (a turn block's TOOL OUTPUTS section).

    Shape produced by ``run_longrun.turn_block`` (and by the C arm's current-turn
    rendering): a `TOOL OUTPUTS:` header, then one `TOOL_OUTPUT (doc@rev): first line`
    per entry, each entry's body continuing on the following lines until the next
    `TOOL_OUTPUT (` header or the end of the slice.
    """
    out: list[dict] = []
    i = start
    while i < len(lines):
        if lines[i].strip() == "TOOL OUTPUTS:":
            i += 1
            continue
        m = TOOL_OUTPUT_RE.match(lines[i])
        if not m:
            i += 1
            continue
        doc_id, revision, first = m.group(1), m.group(2), m.group(3)
        body = [first]
        j = i + 1
        while j < len(lines) and not TOOL_OUTPUT_RE.match(lines[j]):
            body.append(lines[j])
            j += 1
        out.append({"doc_id": doc_id, "revision": revision,
                    "body": "\n".join(body), "line": i + 1})
        i = j
    return out


def answer_slot_shape(prompt: str, turn: int) -> dict:
    """Where the answer slot is, and what sits immediately above it.

    Returns a dict with the grammar it found, whether the shape replays answers, and the
    block above the slot (``None`` when nothing was delivered above it).
    """
    transcript, contract = split_host_contract(prompt)
    replays = [int(m.group(1)) for m in ANSWER_REPLAY_RE.finditer(transcript)]
    shape = {
        "grammar": GRAMMAR_FLAT if replays else GRAMMAR_LAYERED,
        "answer_replay_lines": len(replays),
        "replays_answers": bool(replays),
        "contract_present": contract is not None,
        "transcript_lines": len(transcript.split("\n")),
        "question_found": False,
        "block_above": None,
    }
    if not replays:
        return shape
    lines = transcript.split("\n")
    q_idx = None
    for i, line in enumerate(lines):
        m = QUESTION_RE.match(line)
        if m and int(m.group(1)) == int(turn):
            q_idx = i
    if q_idx is None:
        return shape
    shape["question_found"] = True
    shape["question_line"] = q_idx + 1
    shape["question_text"] = lines[q_idx]
    deliveries = parse_deliveries(lines, q_idx + 1)
    shape["deliveries_after_question"] = [
        {k: d[k] for k in ("doc_id", "revision", "line")} for d in deliveries]
    if deliveries:
        shape["block_above"] = deliveries[-1]
    return shape


# ---------------------------------------------------------------- the rule
def asked_fields(cp: dict) -> tuple[str | None, str | None]:
    """(asked document, asked symbol position) from the checkpoint's own metadata.

    The document comes from `ground_truth.doc` (the fixture's authority, not a regex over
    prose).  The symbol position is read from the question's own grammar
    (`What is VAL_C of doc-fact-08?`), with the `answer_spec` derivation as the fallback
    (`F08_VAL_C`), so the rule never guesses a position the fixture did not name.
    """
    doc = ((cp or {}).get("ground_truth") or {}).get("doc")
    question = (cp or {}).get("question") or ""
    m = re.search(r"\bof\s+(doc-[A-Za-z0-9_.-]+)\b", question)
    if doc is None and m:
        doc = m.group(1)
    symbol = None
    m = re.search(r"\bWhat is\s+([A-Z][A-Z0-9_]*)\s+of\b", question)
    if m:
        symbol = m.group(1)
    if symbol is None:
        derived = (((cp or {}).get("answer_spec") or {}).get("derive") or {}).get("symbol") or ""
        m = re.search(r"(VAL_[A-Za-z0-9]+)$", str(derived))
        if m:
            symbol = m.group(1)
    return doc, symbol


def symbol_value(body: str, symbol: str | None) -> int | None:
    """The integer on `<symbol> = <int>` inside a delivered body, or ``None``."""
    if not symbol:
        return None
    m = re.search(r"(?m)^\s*" + re.escape(symbol) + r"\s*=\s*(-?\d+)\s*$", body or "")
    return int(m.group(1)) if m else None


def classify(shape: dict, cp: dict) -> dict:
    """Apply the rule to one checkpoint's shape.  Pure: no row answer is consulted."""
    asked_doc, asked_symbol = asked_fields(cp)
    block = shape.get("block_above")
    out = {"asked_doc": asked_doc, "asked_symbol": asked_symbol,
           "prediction": "FREE", "predicted_value": None, "reason": None,
           "delivered_doc": None, "delivered_revision": None}
    if not shape.get("replays_answers"):
        out["reason"] = "no_answer_replay"
        return out
    if block is None:
        out["reason"] = "no_delivery_above"
        return out
    out["delivered_doc"] = block["doc_id"]
    out["delivered_revision"] = block["revision"]
    if asked_doc is not None and block["doc_id"] == asked_doc:
        out["reason"] = "same_document"
        return out
    value = symbol_value(block["body"], asked_symbol)
    if value is None:
        out["reason"] = "symbol_not_in_delivery"
        return out
    out.update({"prediction": "BOUND", "predicted_value": value,
                "reason": "mismatched_delivery_above"})
    return out


# ---------------------------------------------------------------- replay
def drive_prompts(fixture: dict, settled: dict, arm: str, rep: int, workdir: str,
                  compact_every: int, window_turns: int,
                  budget_cap: int, request_allocation: int) -> dict:
    """Replay ONE cell and capture the exact user content of every turn it sends.

    Same method as ``prompt_at_turn.drive`` (import the runner, replace `send_chat` with a
    recorder, drive `run_cell` with the recorded replies), widened from one target turn to
    the whole cell so the provenance check covers every row instead of one.  The module
    global that ``prompt_at_turn.drive`` restores from is not reusable outside its own
    ``main()``; this driver keeps its own saved reference.
    """
    rows_path = os.path.join(workdir, f"rows-{arm}-r{rep}.jsonl")
    for stale in (rows_path,):
        if os.path.exists(stale):
            os.remove(stale)
    cfg = PT.make_cfg(workdir)
    # The live cell's own launch parameters, restated so the replay is not gated by the
    # corpus spend (this tool spends nothing) and prices the same request count.
    cfg.budget_cap = int(budget_cap)
    cfg.budget_reserve = 0
    cfg.request_allocation = int(request_allocation)
    state = {"turn": 0}
    captured: dict[int, dict] = {}
    saved_send = R.send_chat

    def recorder(_cfg, messages):
        turn = state["turn"] + 1
        state["turn"] = turn
        row = settled.get((arm, rep, turn))
        if row is None:
            raise AssertionError(f"no settled row for {arm} r{rep} T{turn} — cannot replay")
        user = messages[1]["content"]
        captured[turn] = {
            "prompt": user,
            "sha256": PT.sha256_text(user),
            "settled_prompt_sha256": row.get("prompt_sha256"),
            "byte_identical": PT.sha256_text(user) == row.get("prompt_sha256"),
            "user_bytes": len(user.encode("utf-8")),
        }
        return PT.canned_resp(row)

    R.send_chat = recorder
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            R.run_cell(cfg, fixture, arm, rep, f"predict-{arm}-r{rep}", rows_path,
                       compact_every=compact_every, window_turns=window_turns)
    finally:
        R.send_chat = saved_send
    if not captured:
        raise AssertionError(f"{arm}: run_cell sent nothing (driver tail: "
                             f"{buf.getvalue()[-400:]!r})")
    mismatches = [{"turn": t, "sha256": c["sha256"],
                   "settled_prompt_sha256": c["settled_prompt_sha256"]}
                  for t, c in sorted(captured.items()) if not c["byte_identical"]]
    return {"captured": captured, "driver_tail": buf.getvalue()[-800:],
            "sha_provenance": {"checked": len(captured), "mismatches": mismatches}}


# ---------------------------------------------------------------- diagnostics
def _replayed_answer_lines(transcript: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"(?m)^ANSWER \(T(\d+)\): (.*)$", transcript):
        out.append((int(m.group(1)), m.group(2)))
    return out


def diagnose_free_failure(prompt: str, cp: dict, row: dict) -> dict:
    """Name the mechanism of a FREE-but-wrong turn.  A DIAGNOSTIC, not a predictor input.

    Two residuals are known from U-SPCC-67 and are reported by name so a reader can see
    what the positional rule does not cover: a value already echoed by a replayed
    `ANSWER` line for the same document (a different symbol), and a value adjacent to the
    expected one inside the same body.
    """
    transcript, _contract = split_host_contract(prompt)
    answered = row.get("answer_value")
    expected = row.get("expected")
    answered_text = str(answered)
    reasons = []
    echoes = [ln for ln in _replayed_answer_lines(transcript)
              if re.search(r"(?<![\d.])" + re.escape(answered_text) + r"(?![\d.])", ln[1])]
    if echoes:
        reasons.append({"kind": "prior_answer_echo",
                        "detail": "answered value %s was already replayed as ANSWER (T%d)"
                                  % (answered_text, echoes[-1][0]),
                        "line": "ANSWER (T%d): %s" % echoes[-1]})
    doc = ((cp or {}).get("ground_truth") or {}).get("doc") or ""
    symbol = asked_fields(cp)[1] or ""
    for d in parse_deliveries(transcript.split("\n"), 0):
        if d["doc_id"] != doc:
            continue
        lines = d["body"].split("\n")
        for i, line in enumerate(lines):
            if re.search(r"(?<![\d.])" + re.escape(str(expected)) + r"(?![\d.])", line):
                near = lines[max(0, i - 1): i + 2]
                for j, other in enumerate(near):
                    if other is not line and re.search(
                            r"(?<![\d.])" + re.escape(answered_text) + r"(?![\d.])", other):
                        reasons.append({
                            "kind": "adjacent_symbol_in_same_body",
                            "detail": "answered %s is %s the expected %s inside %s"
                                      % (answered_text,
                                         "above" if j < (i - max(0, i - 1)) else "below",
                                         str(expected), d["doc_id"]),
                            "symbol": symbol})
                        break
    if not reasons:
        reasons.append({"kind": "unexplained_by_the_rule",
                        "detail": "no prior-answer echo and no adjacent symbol in the asked "
                                  "document's body"})
    return {"diagnostics": reasons}


# ---------------------------------------------------------------- report
def confusion(pairs: list[tuple[str, bool]]) -> dict:
    """predicted class x actually-wrong matrix.  ``bool`` True == the row was wrong."""
    m = {"BOUND": {"wrong": 0, "right": 0}, "FREE": {"wrong": 0, "right": 0}}
    for pred, wrong in pairs:
        m[pred]["wrong" if wrong else "right"] += 1
    return m


def analyse_arm(arm: str, fixture: dict, settled: dict, replay: dict, rep: int) -> dict:
    by_turn = {int(c["turn"]): c for c in (fixture.get("checkpoints") or [])}
    cps = sorted(by_turn.values(), key=lambda c: int(c["turn"]))
    captured = replay["captured"]
    pairs: list[tuple[str, bool]] = []
    rows_out: list[dict] = []
    bound_turns: list[dict] = []
    unpredicted: list[dict] = []
    per_distance: dict[str, dict] = {}
    shape_counts: dict[str, int] = {}
    for cp in cps:
        turn = int(cp["turn"])
        row = settled.get((arm, rep, turn))
        if row is None:
            raise AssertionError(f"{arm}: no settled row at checkpoint T{turn}")
        cap = captured.get(turn)
        if cap is None:
            raise AssertionError(f"{arm}: no replayed prompt at checkpoint T{turn}")
        shape = answer_slot_shape(cap["prompt"], turn)
        cls = classify(shape, cp)
        wrong = not bool(row.get("answer_verified"))
        pairs.append((cls["prediction"], wrong))
        shape_counts[shape["grammar"]] = shape_counts.get(shape["grammar"], 0) + 1
        actual = row.get("answer_value")
        cell = {
            "turn": turn, "checkpoint_id": cp.get("id"), "distance": cp.get("distance"),
            "asked_doc": cls["asked_doc"], "asked_symbol": cls["asked_symbol"],
            "delivered_doc": cls["delivered_doc"],
            "delivered_revision": cls["delivered_revision"],
            "prediction": cls["prediction"], "reason": cls["reason"],
            "predicted_value": cls["predicted_value"],
            "expected": cp.get("expected"), "actual": actual,
            "actual_wrong": wrong,
            "actual_equals_predicted_value": (cls["predicted_value"] is not None
                                              and actual == cls["predicted_value"]),
            "answer_replay_lines": shape["answer_replay_lines"],
            "grammar": shape["grammar"],
            "prompt_sha256": cap["sha256"],
        }
        rows_out.append(cell)
        d = str(cp.get("distance"))
        bucket = per_distance.setdefault(d, {"checkpoints": 0, "actual_wrong": 0,
                                             "predicted_bound": 0, "bound_and_wrong": 0,
                                             "free_and_wrong": 0, "bound_and_right": 0})
        bucket["checkpoints"] += 1
        bucket["actual_wrong"] += 1 if wrong else 0
        if cls["prediction"] == "BOUND":
            bucket["predicted_bound"] += 1
            bucket["bound_and_wrong" if wrong else "bound_and_right"] += 1
            bound_turns.append(cell)
        elif wrong:
            bucket["free_and_wrong"] += 1
            diag = diagnose_free_failure(cap["prompt"], cp, row)
            unpredicted.append({**{k: cell[k] for k in
                                   ("turn", "checkpoint_id", "distance", "asked_doc",
                                    "asked_symbol", "expected", "actual", "reason")},
                                **diag})
    cm = confusion(pairs)
    actual_wrong = sum(1 for _p, w in pairs if w)
    pred_bound = cm["BOUND"]["wrong"] + cm["BOUND"]["right"]
    return {
        "arm": arm,
        "checkpoints": len(rows_out),
        "confusion": cm,
        "totals": {
            "checkpoints": len(rows_out),
            "predicted_bound": pred_bound,
            "predicted_free": len(rows_out) - pred_bound,
            "actual_wrong": actual_wrong,
            "actual_right": len(rows_out) - actual_wrong,
            "bound_and_wrong": cm["BOUND"]["wrong"],
            "bound_and_right": cm["BOUND"]["right"],
            "free_and_wrong": cm["FREE"]["wrong"],
            "free_and_right": cm["FREE"]["right"],
            # recall over the failures, and precision over the predictions, both named
            # so neither can be quoted for the other.
            "failure_recall_of_bound": (None if actual_wrong == 0
                                        else round(cm["BOUND"]["wrong"] / actual_wrong, 4)),
            "bound_precision": (None if pred_bound == 0
                                else round(cm["BOUND"]["wrong"] / pred_bound, 4)),
        },
        "shape_counts": shape_counts,
        "bound_turns": bound_turns,
        "unpredicted_failures": unpredicted,
        "per_distance": dict(sorted(per_distance.items(), key=lambda kv: int(kv[0]))),
        "cells": rows_out,
    }


def claim_verdict(per_arm: dict) -> dict:
    """Score the three-part claim this unit tests, from the measured numbers alone."""
    m = per_arm.get("masking-no-fetch")
    s = per_arm.get("spcc")
    out = {"claimed": {
        "all_masking_failures_predicted_bound": True,
        "spcc_predicted_bound": 0,
        "spcc_false_positives": 0,
    }}
    if m:
        total = m["totals"]["actual_wrong"]
        caught = m["totals"]["bound_and_wrong"]
        out["measured_masking"] = {
            "actual_wrong": total,
            "failures_predicted_bound": caught,
            "failures_not_predicted": total - caught,
            "predicted_bound": m["totals"]["predicted_bound"],
            "bound_but_right": m["totals"]["bound_and_right"],
        }
        out["all_masking_failures_predicted_bound"] = (caught == total)
    if s:
        out["measured_spcc"] = {
            "actual_wrong": s["totals"]["actual_wrong"],
            "predicted_bound": s["totals"]["predicted_bound"],
        }
        out["spcc_predicted_bound"] = s["totals"]["predicted_bound"]
    return out


def text_table(per_arm: dict) -> list[str]:
    lines = []
    for arm, rep in per_arm.items():
        cm = rep["confusion"]
        t = rep["totals"]
        lines.append(f"{arm}: {t['checkpoints']} checkpoints, grammars={rep['shape_counts']}")
        lines.append("  confusion (predicted x actual):")
        lines.append(f"    predicted BOUND : wrong {cm['BOUND']['wrong']:3d} | right "
                     f"{cm['BOUND']['right']:3d}")
        lines.append(f"    predicted FREE  : wrong {cm['FREE']['wrong']:3d} | right "
                     f"{cm['FREE']['right']:3d}")
        lines.append(f"  actual wrong {t['actual_wrong']}/{t['checkpoints']}; predicted BOUND "
                     f"{t['predicted_bound']}; recall of failures "
                     f"{t['failure_recall_of_bound']}; precision of BOUND "
                     f"{t['bound_precision']}")
        for c in rep["bound_turns"]:
            lines.append(f"    BOUND T{c['turn']:<3d} {c['checkpoint_id']:<20s} "
                         f"asked {c['asked_doc']}.{c['asked_symbol']} expected "
                         f"{c['expected']} delivered {c['delivered_doc']} -> predicted "
                         f"{c['predicted_value']}; actual {c['actual']} "
                         f"({'WRONG' if c['actual_wrong'] else 'right'}; "
                         f"{'= predicted' if c['actual_equals_predicted_value'] else '!= predicted'})")
        for f in rep["unpredicted_failures"]:
            kinds = ",".join(d["kind"] for d in f["diagnostics"])
            lines.append(f"    FREE-but-wrong T{f['turn']:<3d} {f['checkpoint_id']:<20s} "
                         f"expected {f['expected']} actual {f['actual']} "
                         f"(reason {f['reason']}; {kinds})")
        lines.append("  per distance: " + "; ".join(
            f"d{d} n={v['checkpoints']} wrong={v['actual_wrong']} "
            f"bound={v['predicted_bound']} bound&wrong={v['bound_and_wrong']}"
            for d, v in rep["per_distance"].items()))
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--arms", default="masking-no-fetch,spcc")
    ap.add_argument("--rep", type=int, default=1)
    # The cell's own launch parameters: they change the rendered prompt, so they are
    # inputs, not constants.  Defaults are the E3 cell's (U-SPCC-64).
    ap.add_argument("--compact-every", type=int, default=200, dest="compact_every")
    ap.add_argument("--window-turns", type=int, default=200, dest="window_turns")
    ap.add_argument("--budget-cap", type=int, default=10 ** 6, dest="budget_cap",
                    help="cap the replay's request gate is set to; the replay sends none")
    ap.add_argument("--request-allocation", type=int, default=10 ** 4,
                    dest="request_allocation")
    ap.add_argument("--workdir", default="/tmp/predict-answer-slot-work")
    ap.add_argument("--json", default="/tmp/predict_answer_slot.json")
    args = ap.parse_args(argv)

    # Arm the wires before anything else: the refusal is structural, and an attempt made
    # before this call (a test arming them itself) is already on the ledger.  `PT` arms the
    # same five primitives at its own import, so its ledger counts attempts that landed on
    # its wires before mine replaced them; both are checked, never one alone.
    install_tripwires()
    refuse_fingerprint_probes()
    recorded = sorted(set(NET_ATTEMPTS) | set(PT.NET_ATTEMPTS))
    if recorded:
        print("REFUSING TO REPORT: a network attempt is already recorded "
              f"({recorded}) — this tool has no report to make when the "
              "no-network premise is violated. Nothing was sent.", file=sys.stderr)
        return 9

    fixture = R.load_fixture(args.fixture)
    settled = PT.load_settled(args.rows)
    os.makedirs(args.workdir, exist_ok=True)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    replays: dict[str, dict] = {}
    for arm in arms:
        replays[arm] = drive_prompts(fixture, settled, arm, args.rep, args.workdir,
                                     args.compact_every, args.window_turns,
                                     args.budget_cap, args.request_allocation)

    sha_ok = True
    for arm, r in replays.items():
        if r["sha_provenance"]["mismatches"]:
            sha_ok = False
            print(f"SHA MISMATCH: {arm} {len(r['sha_provenance']['mismatches'])} of "
                  f"{r['sha_provenance']['checked']} replayed prompts are not byte-identical "
                  f"to the settled row (first: T"
                  f"{r['sha_provenance']['mismatches'][0]['turn']})", file=sys.stderr)

    if not sha_ok:
        print("HARD FAILURE: the re-materialised prompts are not the prompts the endpoint "
              "received, so no prediction is reported. Nothing was sent.", file=sys.stderr)
        return 8

    per_arm = {arm: analyse_arm(arm, fixture, settled, replays[arm], args.rep)
               for arm in arms}

    out = {
        "schema": "consonance.answer-slot-predictor/1",
        "unit": "U-SPCC-77",
        "rule": {
            "statement": ("BOUND iff the arm's rendered prompt replays ANSWER lines, the "
                          "block immediately above the current answer slot (after the host "
                          "checkpoint contract is stripped) is a TOOL_OUTPUT delivery of a "
                          "document other than the asked one, and that delivery carries a "
                          "line for the asked symbol position; FREE otherwise."),
            "predicted_answer_class": {"BOUND": "wrong (copies the delivered value)",
                                       "FREE": "correct"},
            "inputs": ["prompt shape", "fixture checkpoint metadata (ground_truth.doc, "
                       "question, answer_spec)"],
            "never_reads": ["the row's answer", "distance", "turn number beyond locating "
                            "the current question line"],
            "thresholds_chosen_after_seeing_rows": False,
            "notes": [
                "The rule was fixed before any row was joined; the answer join scores the "
                "prediction and never feeds it.",
                "A prompt with no ANSWER replay (spcc's layered compiler) is FREE by "
                "construction: there is no positional rule in its grammar to bind to.",
            ],
        },
        "fixture": fixture["_path"],
        "fixture_sha256": fixture["_sha256"],
        "rows": os.path.abspath(args.rows),
        "rows_sha256": hashlib.sha256(open(args.rows, "rb").read()).hexdigest(),
        "arms": arms,
        "rep": args.rep,
        "cell_params": {"compact_every": args.compact_every,
                        "window_turns": args.window_turns,
                        "checkpoints": len(fixture.get("checkpoints") or [])},
        "method": ("imported-runner: run_longrun.send_chat replaced by a recorder that "
                   "returns each settled row's canned reply; run_cell driven over the whole "
                   "cell; every turn's user content captured and sha256-compared to the "
                   "row's prompt_sha256"),
        "sha_provenance": {arm: {"checked": r["sha_provenance"]["checked"],
                                 "mismatches": len(r["sha_provenance"]["mismatches"]),
                                 "ok": not r["sha_provenance"]["mismatches"]}
                           for arm, r in replays.items()},
        "per_arm": per_arm,
        "claim_tested": claim_verdict(per_arm),
        "no_http_proof": {
            "patched": ["urllib.request.urlopen", "urllib.request.build_opener",
                        "http.client.HTTPConnection.connect",
                        "http.client.HTTPSConnection.connect", "socket.create_connection"],
            "network_attempts": NET_ATTEMPTS,
            "inherited_guard_attempts": PT.NET_ATTEMPTS,
            "fingerprint_probes_refused": PROBE_REFUSALS,
            "ok": not (NET_ATTEMPTS or PT.NET_ATTEMPTS),
        },
        "requests_sent": 0,
    }
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)

    print(f"fixture={fixture['task_id']} sha256={fixture['_sha256'][:16]} "
          f"rows={os.path.basename(args.rows)} arms={','.join(arms)} rep={args.rep}")
    print("sha provenance: " + "; ".join(
        f"{arm} {v['checked'] - v['mismatches']}/{v['checked']} byte-identical"
        for arm, v in out["sha_provenance"].items()))
    for line in text_table(per_arm):
        print(line)
    print(f"claim_tested={json.dumps(out['claim_tested'], sort_keys=True)}")
    print(f"report: {args.json}")
    if NET_ATTEMPTS or PT.NET_ATTEMPTS:
        print(f"NO-HTTP PROOF FAILED: attempts={sorted(set(NET_ATTEMPTS) | set(PT.NET_ATTEMPTS))}",
              file=sys.stderr)
        return 9
    print(f"NO-HTTP PROOF ok: 5 clients patched, network_attempts={NET_ATTEMPTS}, "
          f"inherited_guard_attempts={PT.NET_ATTEMPTS}, "
          f"fingerprint_probes_refused={len(PROBE_REFUSALS)}, requests_sent=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
