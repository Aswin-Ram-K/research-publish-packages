"""BILLED-TOKENS contract: billed_tokens means tokens the server CHARGED for.

Guards the three consumer cases (field present / derivable / nothing to bill), the
source stamp in ``run_longrun.make_row``, and the corrected re-score of the existing
100-turn SGLang billed proof. No live requests: the rows file already exists.
"""

import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import score_longrun as sl

ROWS = os.path.join(os.path.dirname(LONGRUN), "measure",
                    "rows-spcc-billedproof-2026-11-10.jsonl")


def _load_rows():
    with open(ROWS, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --------------------------------------------------------------- consumer: case 1
def test_case_field_present_sums_the_field():
    recs = [
        {"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 60,
         "billed_tokens": 60},
        {"prompt_tokens": 120, "cached_tokens": 20, "uncached_tokens": 100,
         "billed_tokens": 100},
    ]
    b = sl.billing_block(recs)
    assert b["billed_tokens"] == 160
    assert b["billed_source"] == "field"
    assert b["attribution"] == "available"
    assert b["billed_coverage"] == 1.0


def test_field_wins_over_derivation():
    # A stamped row is authoritative even if the raw columns would derive something else.
    recs = [{"prompt_tokens": 100, "cached_tokens": 90, "uncached_tokens": 10,
             "billed_tokens": 25}]
    assert sl.billing_block(recs)["billed_tokens"] == 25


# --------------------------------------------------------------- consumer: case 2
def test_case_derivable_without_the_field():
    # Legacy row shape: no billed_tokens key at all.
    recs = [
        {"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 60},
        {"prompt_tokens": 120, "cached_tokens": None, "uncached_tokens": None,
         "cached_tokens_normalized": 0, "turn": 1},
    ]
    b = sl.billing_block(recs)
    # 100-40 from the reported cache, plus turn 1's 120 in full: no prior prefix exists
    # on the first request, so the whole prompt is billed by mechanism.
    assert b["billed_tokens"] == 180
    assert b["billed_source"] == "mixed"
    assert b["attribution"] == "available"
    assert b["billed_coverage"] == 1.0


def test_mixed_block_reports_unknown_rows_and_the_upper_bound():
    # Two known rows (one reported cache, one first-turn) + one unknown turn-5 row.
    recs = [
        {"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 60, "turn": 2},
        {"prompt_tokens": 120, "cached_tokens": None, "uncached_tokens": None, "turn": 4},
        {"prompt_tokens": 300, "cached_tokens": None, "uncached_tokens": None, "turn": 1},
    ]
    b = sl.billing_block(recs)
    assert b["billed_tokens_known"] == 60 + 300
    assert b["billed_upper_bound_tokens"] == 60 + 300 + 120
    assert b["billed_unknown_rows"] == 1
    assert b["billed_unknown_turns"] == [4]
    assert b["billed_coverage"] == 2 / 3
    assert b["billed_coverage"] < 1.0
    assert b["billed_tokens"] == b["billed_tokens_known"]
    assert b["attribution"] == "partial"


def test_derivation_is_prompt_minus_cached_not_uncached():
    # uncached is the server's prefill report, which leaves a residual unexplained;
    # billing must follow prompt - cached, never uncached.
    recs = [{"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 55}]
    b = sl.billing_block(recs)
    assert b["billed_tokens"] == 60
    assert b["billed_tokens"] != 55
    assert b["reconcile_delta_total"] == 5


# --------------------------------------------------------------- consumer: case 3
def test_case_absent_is_null_not_zero():
    recs = [{"cached_tokens": None}, {"cached_tokens": 10, "uncached_tokens": 5}]
    b = sl.billing_block(recs)
    assert b["billed_tokens"] is None
    assert b["billed_source"] is None
    assert b["attribution"] == "unavailable"
    assert b["billed_coverage"] == 0.0
    assert b["cached_fraction_of_prompt"] is None


def test_empty_records_is_null_not_zero():
    b = sl.billing_block([])
    assert b["billed_tokens"] is None
    assert b["attribution"] is None
    assert b["cached_fraction_of_accounted"] is None


def test_no_prompt_never_bills_as_zero():
    # A failed turn carries no prompt: it must not contribute a 0 to the sum.
    recs = [{"prompt_tokens": None, "cached_tokens": None, "uncached_tokens": None}]
    assert sl.billing_block(recs)["billed_tokens"] is None


# --------------------------------------------------------------- both fractions
def test_fractions_name_their_denominators():
    recs = [{"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 60},
            {"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 55}]
    b = sl.billing_block(recs)
    assert b["cached_fraction_of_prompt"] == 80 / 200
    assert b["cached_fraction_of_accounted"] == 80 / (80 + 115)
    assert "cached_fraction" not in b


# --------------------------------------------------------------- source stamp
def _stamp(prompt, cached, normalized=0, turn=1):
    cfg = types.SimpleNamespace(engine="sglang", stream=False, max_tokens=8,
                                temperature=0, seed=42, fetch_policy="strict",
                                generation="gen-7", claim=None)
    fixture = {"task_id": "T", "_path": "fx.json", "_sha256": "0" * 64,
               "bytes_per_token": 4.0, "items": [], "turns": [], "N": 0}
    resp = {"prompt_tokens": prompt, "cached_tokens": cached,
            "raw_cached": cached, "completion_tokens": 3, "content_raw": "ok",
            "reasoning": "", "ttft_s": 0.01, "latency_s": 0.02,
            "finish_reason": "stop", "token_source": "usage"}
    row = __import__("run_longrun").make_row(
        cfg, fixture, "a", 1, "run-x-r1", turn, resp, "ok", "turn", "1" * 64,
        {"is_checkpoint": False, "checkpoint": None})
    if cached is None:
        row["cached_tokens_normalized"] = normalized if normalized is not None else None
    return row


def test_stamp_bills_prompt_minus_cached_and_keeps_the_residual_visible():
    row = _stamp(prompt=100, cached=40)
    assert row["billed_tokens"] == 60
    assert row["uncached_tokens"] == 60
    assert row["reconcile_delta_tokens"] == 0
    assert row["billed_source"] == "reported"


def test_stamp_first_turn_bills_whole_prompt_by_mechanism():
    # The first request of a run has no prior prefix to hit, so cached = 0 follows from
    # the cache MECHANISM, not from an assumption about the missing counter.
    row = _stamp(prompt=261, cached=None)
    assert row["cached_tokens"] is None
    assert row["billed_tokens"] == 261
    assert row["billed_source"] == "first-turn-no-cache"
    assert row["reconcile_delta_tokens"] is None


def test_stamp_later_turn_null_cache_is_unknown_not_the_whole_prompt():
    # ABSENT is not 0: on turn 5 there IS a prior prefix, so a null counter leaves the
    # billed quantity UNKNOWN -- it must not be billed as the full prompt.
    row = _stamp(prompt=296, cached=None, turn=5)
    assert row["cached_tokens"] is None
    assert row["billed_tokens"] is None
    assert row["billed_source"] == "unknown"
    assert row["uncached_tokens"] is None


def test_stamp_is_null_when_there_is_no_prompt():
    cfg = types.SimpleNamespace(engine="sglang", stream=False, max_tokens=8,
                                temperature=0, seed=42, fetch_policy="strict",
                                generation="gen-7", claim=None)
    fixture = {"task_id": "T", "_path": "fx.json", "_sha256": "0" * 64,
               "bytes_per_token": 4.0, "items": [], "turns": [], "N": 0}
    row = __import__("run_longrun").make_row(
        cfg, fixture, "a", 1, "run-x-r1", 1, None, None, "turn", "1" * 64,
        {"is_checkpoint": False, "checkpoint": None})
    assert row["billed_tokens"] is None
    assert row["reconcile_delta_tokens"] is None


# --------------------------------------------------------------- the real re-score
def test_existing_run_rescores_to_substantive_billed():
    rows = _load_rows()
    # Preconditions of the correction: the file is the unfixed shape -- no row stamps
    # billed_tokens, so the block below is the DERIVED reading.
    assert len(rows) == 100
    assert all("billed_tokens" not in r for r in rows)
    b = sl.billing_block(rows)
    assert b["prompt_tokens"] == 174047
    assert b["cached_tokens"] == 159744
    assert b["uncached_tokens"] == 13746
    # ABSENT is not 0: turns [1, 5] carry no cached_tokens. Turn 1 is settled by the
    # cache MECHANISM (no prior prefix), turn 5 is genuinely unknown -- so the billed
    # quantity is a BOUND, never the 14,303 the old full-prompt assumption published.
    assert b["billed_tokens_known"] == 14007
    assert b["billed_upper_bound_tokens"] == 14303
    assert b["billed_unknown_rows"] == 1
    assert b["billed_unknown_turns"] == [5]
    assert b["billed_coverage"] == 0.99
    assert b["billed_coverage"] < 1.0
    assert b["billed_tokens"] == b["billed_tokens_known"]
    assert b["billed_tokens_known"] < 14303
    # Nothing is derived from the server's prefill report: it is null on both rows.
    assert b["billed_tokens_known"] != b["uncached_tokens"]
    assert round(b["cached_fraction_of_prompt"], 6) == 0.917821
    assert round(b["cached_fraction_of_accounted"], 6) == 0.920768
    assert b["coverage"] == 0.98
    # The 557-token prompt/cached/uncached residual is reported, not corrected.
    assert b["reconcile_delta_total"] == 557
    assert b["reconcile_within_tolerance"] is True
    # billed is exactly the prompt not reported as cached, over known rows only
    assert b["billed_tokens_known"] == (b["prompt_tokens"] - 261 - 296) - b["cached_tokens"] + 261
