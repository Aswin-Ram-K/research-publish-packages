"""OFFLINE tests for the V2 billing instrument.  No HTTP, no server, no network.

The audited runner priced the append as ``L = prompt_tokens + FRAMING`` (the whole
prefix) and never persisted what the server said it billed.  These tests pin both
halves of the fix on ONE synthetic append turn:

    turn 2  P1_previous = 10000, P1 = 10245, server cached_tokens = 10000
            true append  L = 245        true uncached bill = 245

red   -- replay the audited formula on that row; the guard must raise.
green -- the delta formula on the same row; the guard must pass.
null  -- a null ``usage.prompt_tokens_details`` stays ``cached_tokens: null`` with
         ``cached_reported: false``; it is never written as the 0 it is not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

QUALITY = Path(__file__).resolve().parents[1]
if str(QUALITY) not in sys.path:
    sys.path.insert(0, str(QUALITY))

import runner_v2  # noqa: E402

P1_PREVIOUS = 10000
P1 = 10245
CACHED = 10000
TRUE_APPEND = P1 - P1_PREVIOUS          # 245

REPORTED = {"prompt_tokens": P1, "prompt_tokens_details": {"cached_tokens": CACHED}}


def _v2_row() -> dict:
    """The row runner_v2 writes for the synthetic append turn."""
    return runner_v2.billing_row(
        2, P1, P1_PREVIOUS, REPORTED
    )


def _audited_row() -> dict:
    """The same turn as the AUDITED runner recorded it.

    ``L = prompt_tokens + FRAMING`` (runner.py:495); the law column was
    ``residue + L``; and ``cached_tokens`` was read then dropped, so the shipped
    ``rows.jsonl`` request rows carry no such key at all (48/48).
    """
    row = dict(_v2_row())
    row["L"] = P1 + 12                                   # runner.py:495, verbatim formula
    row["L_source"] = "delta"                            # V2 labels every append turn so
    row["predicted_uncached"] = (P1 % 64) + row["L"]      # 5 + 10257 = 10262
    row["billed"] = row["predicted_uncached"]             # billed = residue + L
    row.pop("cached_tokens", None)                        # never persisted
    row["cached_reported"] = False
    row["server_uncached"] = None
    return row


def test_old_formula_fails_the_alignment_guard() -> None:
    """(a) ``L = prompt_tokens + FRAMING`` must FAIL -- the test is worthless otherwise."""
    audited = _audited_row()
    with pytest.raises(AssertionError) as caught:
        runner_v2.assert_billing_alignment([audited])
    message = str(caught.value)
    print("\nRED  (audited L = prompt_tokens + FRAMING):", message)

    # The failure quotes the row index and BOTH counts.
    assert "row 0" in message, message
    assert "billed=10262" in message, message
    assert f"{P1} - 0 + 0 = {P1}" in message, message

    # The same defect is caught a second way: even when the bill is corrected to the
    # server's reading, the audited L is not the append its own source implies.
    corrected_bill = dict(audited)
    corrected_bill["billed"] = P1 - CACHED               # 245
    corrected_bill["cached_tokens"] = CACHED
    corrected_bill["cached_reported"] = True
    corrected_bill["server_uncached"] = P1 - CACHED
    with pytest.raises(AssertionError) as caught2:
        runner_v2.assert_billing_alignment([corrected_bill])
    message2 = str(caught2.value)
    print("RED2 (audited L against a corrected bill):", message2)
    assert f"L_source='delta' implies L={TRUE_APPEND}" in message2, message2


def test_delta_formula_passes_the_alignment_guard() -> None:
    """(b) the delta formula must PASS on the same synthetic row."""
    row = _v2_row()
    assert row["L_source"] == "delta"
    assert row["L"] == TRUE_APPEND, row
    assert row["cached_tokens"] == CACHED and row["cached_reported"] is True
    assert row["billed"] == TRUE_APPEND, row

    result = runner_v2.assert_billing_alignment([row])
    assert result is None
    print("\nGREEN(delta L = P2 - P1):", json.dumps(
        {k: row[k] for k in ("turn", "prompt_tokens", "P1_previous", "L", "L_source",
                             "cached_tokens", "billed", "billed_source")},
        sort_keys=True,
    ))


def test_null_cached_tokens_is_persisted_as_null_never_zero() -> None:
    """(c) no reported ``cached_tokens`` -> explicit null, ``cached_reported: false``."""
    for label, usage in (
        ("key absent", {"prompt_tokens": 900}),
        ("details null", {"prompt_tokens": 900, "prompt_tokens_details": None}),
        ("details empty", {"prompt_tokens": 900, "prompt_tokens_details": {}}),
    ):
        row = runner_v2.billing_row(1, 900, 0, usage)
        assert row["cached_tokens"] is None, label
        assert row["cached_reported"] is False, label
        assert row["server_uncached"] is None, label
        persisted = json.loads(json.dumps(row))          # what lands in rows.jsonl
        assert persisted["cached_tokens"] is None, label
        assert persisted["cached_reported"] is False, label
        assert persisted["billed"] == 900, label         # the whole prompt, as a bound
        runner_v2.assert_billing_alignment([row])        # and it still aligns
    print("\nNULL (details null -> cached_tokens: null, cached_reported: false):",
          json.dumps({"cached_tokens": None, "cached_reported": False}))

    # A REPORTED zero is not a null: the server spoke and said zero.
    reported_zero = runner_v2.billing_row(
        1, 900, 0, {"prompt_tokens": 900, "prompt_tokens_details": {"cached_tokens": 0}}
    )
    assert reported_zero["cached_tokens"] == 0
    assert reported_zero["cached_reported"] is True
