"""TURN-DEDUP-RECONCILE — the 48 / 46 / 43 discrepancy, as a test.

Three counts exist for one long-run tools cell:

    a = rows whose kind is a turn row (``turn-initial`` or legacy ``turn``)
    b = what survives the report tool's rule R (``latency_report.dedupe``)
    c = distinct ``content_sha256`` among the turn rows

They are NOT three estimates of one quantity.  ``a`` is the turn count; ``c`` is
a response-text diversity count (repeated refusals / repeated tool-call text),
which is not a turn count at all; ``b`` is the count after a rule that was
written to collapse *one measurement stored twice*.

The fix (``LATENCY-DEDUPE-FIX``) is in ``latency_report.dedupe``: on a key
collision a row whose ``kind`` is in ``TURN_ROW_KINDS`` now always beats a
non-turn row, so the mirrored copy R keeps is the one the frozen per-turn
definition selects and the turn count no longer falls: 46/37 -> 48/48, with the
kept-row count unchanged (70 G8 / 61 G9).  Between two turn-kind rows the later
``row_seq`` / ``send_index`` wins (file order when neither is persisted).

Run:  PYTHONPATH=src python3 -m pytest tests/test_turn_dedup.py -q
      (expected: 8 passed -- the two former red tests are now plain asserts)
No network.  Read-only against the corpus.
"""
import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


report = _load("latency_report", os.path.join(TOOLS, "latency_report.py"))
stats = _load("analyze_stats", os.path.join(LONGRUN, "analyze_stats.py"))

# The three counts this card reconciles, plus the v6 file for contrast.
CELLS = [
    ("rows-longrun-v5-tools.jsonl", 2),   # G8: the 48 -> 46 cell
    ("rows-longrun-v6-tools.jsonl", 11),  # G9: the same defect, larger
]


def rows_of(name):
    with open(os.path.join(MEASURE, name), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def counts(name):
    rows = rows_of(name)
    kept, _groups, _excess, status = report.dedupe_rows(rows)
    a, _ = stats.turn_latency_rows(rows)
    b, _ = stats.turn_latency_rows(kept)
    turn_rows = [r for r in rows if r.get("kind") in stats.TURN_ROW_KINDS]
    return {
        "status": status,
        "a": len(a),
        "b": len(b),
        "c": len({r.get("content_sha256") for r in turn_rows}),
        "d": len({r.get("prompt_sha256") for r in turn_rows}),
        "rows_raw": len(rows),
        "rows_kept": len(kept),
    }


@pytest.mark.parametrize("name,expected_excess", CELLS)
def test_counts_are_three_different_questions(name, expected_excess):
    """a, b and c are not three estimates of one number -- pin what each is."""
    got = counts(name)
    assert got["status"] == "decided"
    assert got["rows_raw"] - got["rows_kept"] == expected_excess
    # a is the turn count; c is a response-diversity count and is smaller.
    assert got["a"] == 48
    # b must equal a: rule R may drop a duplicate measurement, never a turn.
    assert got["b"] == 48
    assert got["c"] == 43
    # d (distinct request hashes) equals a: every dropped row is a distinct turn.
    assert got["d"] == 48


@pytest.mark.parametrize("name,_excess", CELLS)
def test_dropped_rows_are_the_mirrored_copy_of_a_surviving_tool_call(name, _excess):
    """EVIDENCE (green): each dropped row duplicates a kept TURN_KINDS row's
    *measurement* -- same ts, ttft, latency, token counts -- and differs only in
    kind and in prompt_sha256. So R is removing a genuine duplicate measurement,
    not two different turns; since the precedence fix the dropped copy is the
    `tool-followup` mirror and the kept copy is the turn row."""
    rows = rows_of(name)
    kept, _groups, _excess, _status = report.dedupe_rows(rows)
    kept_ids = {id(r) for r in kept}
    key = lambda r: (r.get("ts"), r.get("content_sha256"),
                     r.get("prompt_tokens"), r.get("completion_tokens"))
    kept_by_key = {key(r): r for r in kept}
    dropped = [r for r in rows if r.get("kind") not in stats.TURN_ROW_KINDS
               and id(r) not in kept_ids]
    assert len(dropped) == _excess, "expected rule R to drop exactly the mirrored copies"
    for r in dropped:
        twin = kept_by_key[key(r)]
        assert twin.get("kind") in stats.TURN_ROW_KINDS
        assert twin.get("turn") == r.get("turn")
        assert twin.get("ttft_ms") == r.get("ttft_ms")
        assert twin.get("latency_s") == r.get("latency_s")
        assert twin.get("completion_tokens") == r.get("completion_tokens")


@pytest.mark.parametrize("name,_excess", CELLS)
def test_rule_r_keeps_every_turn_the_definition_selects(name, _excess):
    """The frozen per-turn definition selects one row per turn; rule R must not
    lower that count, because a turn is an identity, not a measurement.

    Before the precedence fix this was red: the surviving copy of each mirrored
    pair was the `tool-followup`, which the definition never selects, so 48
    turns measured as 46 (G8) / 37 (G9). `latency_report.dedupe` now prefers the
    TURN_ROW_KINDS row on collision, keeping the measurement count identical
    (70 / 61 kept rows) and the turn count at 48.
    """
    rows = rows_of(name)
    kept, _groups, _excess, _status = report.dedupe_rows(rows)
    raw_turns, _ = stats.turn_latency_rows(rows)
    dedup_turns, _ = stats.turn_latency_rows(kept)
    assert len(dedup_turns) == len(raw_turns), (
        "rule R deleted %d of %d turns from the turn-level sample: the row it "
        "kept for each mirrored pair is kind='tool-followup', which the frozen "
        "definition never selects. Data loss, not de-duplication."
        % (len(raw_turns) - len(dedup_turns), len(raw_turns)))


@pytest.mark.parametrize("name,_excess", CELLS)
def test_dedupe_keeps_a_selectable_row_for_every_turn(name, _excess):
    """GREEN (the fix's own acceptance shape): after R, every turn identity still
    has exactly one row in TURN_ROW_KINDS."""
    rows = rows_of(name)
    kept, _groups, _excess, _status = report.dedupe_rows(rows)
    identities = {(r.get("arm") or "default", r.get("rep"), r.get("turn"))
                  for r in rows if r.get("kind") in stats.TURN_ROW_KINDS}
    survivors = {(r.get("arm") or "default", r.get("rep"), r.get("turn"))
                 for r in kept if r.get("kind") in stats.TURN_ROW_KINDS}
    missing = sorted(identities - survivors)
    assert not missing, "rule R left %d turn(s) with no selectable row: %r" % (
        len(missing), missing[:5])
