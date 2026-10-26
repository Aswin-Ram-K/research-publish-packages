"""Contract test for the ARMS-PARITY withdrawal record (unit ARMS-PARITY-WITHDRAW2).

WHY THIS FILE EXISTS
--------------------
Card ``b8722e77`` (second attempt) named the missing half of unit ``ARMS-PARITY-WITHDRAW``:
``state/logs/arms-parity.json`` had been marked ``status: WITHDRAWN`` but carried none of the
machine-readable contract fields a reader (or the board) can act on.  This test pins the
fields the withdrawal must expose:

  * the record parses as a JSON object;
  * ``status`` is ``withdrawn`` (case-insensitive — the record spells it ``WITHDRAWN`` to
    stay compatible with ``tools/audit/arms_parity_status.py`` and
    ``tests/test_arms_parity_status.py``, which assert the upper-case spelling);
  * ``original_verdict`` is present — the falsified verdict text must stay readable, never
    be deleted;
  * ``superseded_by == "GROUND-TRUTH-PROMPT"`` — the unit that falsified it;
  * ``withdrawn_by`` is non-empty;
  * ``withdrawn_reason`` is non-empty AND names the falsifier measurement (589.2029).

RED -> GREEN (the proof, run against a /tmp copy so the repo file is never mutated):

    cp state/logs/arms-parity.json /tmp/arms-parity.contract.json
    # for each of superseded_by / withdrawn_by / withdrawn_reason:
    #   delete the key from the /tmp copy, then:
    ARMS_PARITY_LOG=/tmp/arms-parity.contract.json \
        .venv/bin/python -m pytest tests/test_arms_parity_withdrawn.py -q   # MUST fail
    .venv/bin/python -m pytest tests/test_arms_parity_withdrawn.py -q       # MUST pass

The ``ARMS_PARITY_LOG`` override exists solely for that red proof; with it unset the test
always reads the repository record.  Read-only otherwise: no live requests, no network.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = os.path.join(ROOT, "state", "logs", "arms-parity.json")
LOG = os.environ.get("ARMS_PARITY_LOG", DEFAULT_LOG)


def _record():
    with open(LOG, encoding="utf-8") as fh:
        return json.load(fh)


def test_record_parses():
    rec = _record()
    assert isinstance(rec, dict), f"{LOG}: not a JSON object"


def test_status_is_withdrawn():
    status = str(_record().get("status", ""))
    assert status.lower() == "withdrawn", (
        f"{LOG}: status={status!r}, expected 'withdrawn' — the ARMS-PARITY verdict is falsified "
        "by GROUND-TRUTH-PROMPT 589.2029 and must stay marked dead"
    )


def test_original_verdict_preserved():
    rec = _record()
    text = rec.get("original_verdict")
    assert text, f"{LOG}: original_verdict missing or empty — the falsified verdict text must stay readable"
    assert "390.80" in str(text), (
        f"{LOG}: original_verdict does not carry the original verdict text (expected the 390.80 claim)"
    )


def test_superseded_by_names_ground_truth_prompt():
    got = _record().get("superseded_by")
    assert got == "GROUND-TRUTH-PROMPT", (
        f"{LOG}: superseded_by={got!r}, expected 'GROUND-TRUTH-PROMPT' — that is the unit whose "
        "fresh re-measurement (589.2029) falsified the verdict"
    )


def test_withdrawn_by_non_empty():
    got = str(_record().get("withdrawn_by", ""))
    assert got.strip(), f"{LOG}: withdrawn_by is empty — the record must name who withdrew it"


def test_withdrawn_reason_names_the_falsifier():
    reason = str(_record().get("withdrawn_reason", ""))
    assert reason.strip(), f"{LOG}: withdrawn_reason is empty"
    assert "589.2029" in reason, (
        f"{LOG}: withdrawn_reason does not name the falsifier measurement (589.2029 uncached/turn)"
    )
