"""The ledger: one row per request, refusals counted, and no lying zeros."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ptr_engine import (
    FRAMING_TOKENS,
    LEDGER_CODES,
    LEDGER_LAW_CODES,
    SERVER_PROFILES,
    HitLedger,
    Ledger,
    law_L,
    parse,
    predict_uncached,
    resolve,
)
from ptr_engine.errors import PtrError, PtrTokenSourceRequiredError
from ptr_engine.ledger import ROW_KEYS

# The measured rows this law was derived from: read, never written, never fabricated.
MISS_LAW_ROWS = Path(__file__).resolve().parents[2] / "miss-law" / "rows.jsonl"


def test_n_resolves_write_n_rows(ledger, scope, index):
    refs = [parse(text) for text in index.texts()[:3]]
    for ref in refs:
        resolve(ref, scope, ledger)
    assert len(ledger) == 3
    rows = ledger.read_rows()
    assert len(rows) == 3
    assert [row["refs_resolved"] for row in rows] == [1, 1, 1]
    assert [row["refs_refused"] for row in rows] == [0, 0, 0]
    assert [row["ledger_id"].split(":")[1] for row in rows] == ["0000", "0001", "0002"]
    assert len({row["ledger_id"] for row in rows}) == 3


def test_refusals_are_counted_not_swallowed(ledger, scope):
    with pytest.raises(Exception):
        resolve(parse("@knowledge:does-not-exist@3"), scope, ledger)
    resolve(parse("@knowledge:k01@3"), scope, ledger)
    with pytest.raises(Exception):
        resolve(parse("@knowledge:also-missing@3"), scope, ledger)
    assert len(ledger) == 3
    assert ledger.resolved_count() == 1
    assert ledger.refused_count() == 2
    assert [row["refs_refused"] for row in ledger.rows] == [1, 0, 1]


def test_missing_tokens_are_null_never_zero(ledger, scope):
    resolve(parse("@knowledge:k01@3"), scope, ledger)
    row = ledger.read_rows()[-1]
    for field in ("prompt_tokens", "cached_tokens", "uncached_tokens", "token_source"):
        assert field in row
        assert row[field] is None, f"{field} must be null when the host has no count"
        assert row[field] != 0
    assert set(row) == set(ROW_KEYS)


def test_token_counts_without_a_source_are_refused(ledger):
    with pytest.raises(PtrTokenSourceRequiredError) as excinfo:
        ledger.record(
            ledger_id="sess-01:0000:aaaaaaaaaaaa",
            scope="sess-01",
            prompt_tokens=100,
        )
    assert excinfo.value.code == "PTR_TOKEN_SOURCE_REQUIRED"
    assert len(ledger) == 0


def test_token_counts_with_a_source_are_recorded(ledger):
    row = ledger.record(
        ledger_id="sess-01:0000:aaaaaaaaaaaa",
        scope="sess-01",
        refs_resolved=1,
        bytes_appended=16,
        token_source="vllm:usage",
        prompt_tokens=2048,
        cached_tokens=1920,
        uncached_tokens=128,
    )
    assert row["token_source"] == "vllm:usage"
    assert row["prompt_tokens"] == 2048
    assert ledger.read_rows()[-1] == json.loads(json.dumps(row))


def test_append_remainder_matches_the_bytes_appended(ledger, scope, index):
    ref = parse("@knowledge:k01@3")
    resolve(ref, scope, ledger)
    row = ledger.rows[-1]
    assert row["bytes_appended"] == len("@knowledge:k01@3".encode())
    assert row["block_size"] == 64
    assert row["append_remainder"] == row["bytes_appended"] % row["block_size"] == 16


def test_ledger_reopens_and_keeps_counting(warmpool, scope):
    path = warmpool / "reopen.jsonl"
    first = Ledger(path, block_size=64)
    resolve(parse("@knowledge:k01@3"), scope, first)
    second = Ledger(path, block_size=64)
    assert len(second) == 1
    resolve(parse("@knowledge:k02@3"), scope, second)
    assert len(second) == 2
    assert [row["refs_resolved"] for row in Ledger(path).read_rows()] == [1, 1]


def test_refusal_needs_a_named_code(ledger):
    with pytest.raises(ValueError):
        ledger.record_refusal(scope="s", serialized_ref="@knowledge:k1", code="nope")


def test_ledger_failures_carry_a_named_code_not_a_bare_valueerror(ledger):
    from ptr_engine import LEDGER_CODES, Ledger, PtrError

    cases = [
        (lambda: ledger.record(ledger_id="s:0000:x", scope="s", refs_resolved=-1), "PTR_LEDGER_COUNT"),
        (lambda: Ledger(ledger.path, block_size=0), "PTR_LEDGER_BLOCK_SIZE"),
        (lambda: ledger.record(ledger_id="", scope="s"), "PTR_LEDGER_ID"),
        (lambda: ledger.record(ledger_id="s:0000:x", scope=""), "PTR_LEDGER_SCOPE"),
        (
            lambda: ledger.record_refusal(
                scope="s", serialized_ref="@knowledge:k1", code="nope"
            ),
            "PTR_LEDGER_REFUSAL_CODE",
        ),
        (
            lambda: ledger.record(ledger_id="s:0000:x", scope="s", block_size=-2),
            "PTR_LEDGER_BLOCK_SIZE",
        ),
    ]
    seen = []
    for case, expected in cases:
        with pytest.raises(PtrError) as excinfo:
            case()
        assert excinfo.value.code == expected
        assert str(excinfo.value).startswith(expected)
        assert isinstance(excinfo.value, ValueError)  # pre-code callers still catch it
        seen.append(excinfo.value.code)
    assert set(seen) == set(LEDGER_CODES)

# ---------------------------------------------------------------------------
# The billing law (HIT-LEDGER): one append onto a primed prefix, two servers,
# one avalanche. Every number below is a value from experiments/miss-law/rows.jsonl,
# written as a literal so that changing a profile constant fails a test.
# ---------------------------------------------------------------------------


def test_law_reproduces_both_servers_at_named_residues():
    """Residues 0, 1, 2, 63 and a payload boundary, on both measured servers."""
    # SGLang / occamy-1.0, B = 64: uncached = (P1 mod B) + L, except residue 0/1.
    assert (8000 % 64, predict_uncached("sglang", 8000, 13)) == (0, (8013, True))
    assert (8001 % 64, predict_uncached("sglang", 8001, 13)) == (1, (8014, True))
    assert (8002 % 64, predict_uncached("sglang", 8002, 13)) == (2, (15, False))
    assert (8063 % 64, predict_uncached("sglang", 8063, 13)) == (63, (76, False))
    # payload boundaries: P1 = 8064 is an avalanche even with a 64-token payload
    # (measured 8140); P1 = 8005 with a 128-token payload is a plain tail (measured 145).
    assert predict_uncached("sglang", 8064, law_L(64)) == (8140, True)
    assert predict_uncached("sglang", 8005, law_L(128)) == (145, False)

    # vLLM / qwen3.5-9b, B = 1056: uncached = (P1 mod B) + B + L -- one whole block extra.
    assert (7000 % 1056, predict_uncached("vllm", 7000, 13)) == (664, (1733, False))
    assert (7396 % 1056, predict_uncached("vllm", 7396, 13)) == (4, (1073, False))
    assert (7394 % 1056, predict_uncached("vllm", 7394, 13)) == (2, (1071, False))
    assert (7455 % 1056, predict_uncached("vllm", 7455, 13)) == (63, (1132, False))
    # A vLLM block boundary (8 * 1056) never appeared in the sweep, so its avalanche
    # is an extrapolation -- reported, flagged, not silently assumed measured.
    assert (8448 % 1056, predict_uncached("vllm", 8448, 13)) == (0, (8461, True))

    # L is the appended length including framing, never the raw payload count.
    assert law_L(1) == 13 and law_L(64) == 76
    assert predict_uncached("sglang", 8002, 1) == (3, False)  # the n-as-L mistake
    assert predict_uncached("sglang", 8002, law_L(1)) == (15, False)


def test_profiles_are_the_measured_ones():
    """The grid is measured, not configurable: an unmeasured server is refused."""
    sglang, vllm = SERVER_PROFILES["sglang"], SERVER_PROFILES["vllm"]
    assert (sglang.block_size, sglang.boundary_blocks) == (64, 0)
    assert (vllm.block_size, vllm.boundary_blocks) == (1056, 1)
    assert sglang.avalanche_residues == frozenset({0, 1})
    assert vllm.avalanche_residues == frozenset({0, 1})
    assert sglang.avalanche_measured is True
    assert vllm.avalanche_measured is False  # residue 0/1 was never sampled on vLLM
    with pytest.raises(PtrError) as excinfo:
        predict_uncached("some-other-build", 8000, 13)
    assert excinfo.value.code == "PTR_LAW_UNKNOWN_SERVER"


def test_reconcile_names_the_mismatching_turn():
    """A mismatch is named, with its server and cell, not absorbed into a total."""
    hits = HitLedger("sglang")
    hits.record(P1=8002, L=13, cell="res-8002-n1", observed_uncached=15)
    hits.record(P1=8003, L=13, cell="res-8003-n1", observed_uncached=99)
    hits.record(P1=8004, L=13, cell="res-8004-n1", observed_uncached=17)

    report = hits.reconcile()
    assert len(report.exact) == 2
    assert [c.turn for c in report.mismatched] == [1]
    bad = report.mismatched[0]
    assert (bad.server, bad.cell) == ("sglang", "res-8003-n1")
    assert (bad.predicted_uncached, bad.observed_uncached, bad.delta) == (16, 99, 83)
    assert report.unknown == ()
    assert report.explained_fraction == pytest.approx(2 / 3)
    (line,) = report.unexplained()
    assert "could not explain" in line and "res-8003-n1" in line and "delta +83" in line
    # the same series supplied separately reconciles identically
    assert hits.reconcile([15, 99, 17]).as_dict() == report.as_dict()


def test_avalanche_is_its_own_outcome_with_its_own_cost():
    """Residue 0/1 is not a big tail: it is a different outcome, and it is priced."""
    hits = HitLedger("sglang")
    avalanche = hits.record(P1=8000, payload_tokens=1, cell="res-8000-n1")
    tail = hits.record(P1=8002, payload_tokens=1, cell="res-8002-n1")

    assert (avalanche.residue, avalanche.avalanche) == (0, True)
    assert (tail.residue, tail.avalanche) == (2, False)
    assert avalanche.predicted_uncached == 8013 and tail.predicted_uncached == 15
    # the same append costs 7998 more tokens for a 2-token difference in P1
    assert avalanche.predicted_uncached - tail.predicted_uncached == 7998
    # and the avalanche's own cost is priced against what the tail formula would have said
    assert (avalanche.tail_uncached, avalanche.avalanche_tokens) == (13, 8000)
    assert tail.avalanche_tokens == 0
    assert avalanche.avalanche_extrapolated is False

    summary = hits.summarise()
    assert summary.avalanche_count == 1
    assert summary.avalanche_tokens == 8013
    assert summary.avalanche_extra_tokens == 8000
    assert summary.billed_tokens == 8028
    assert [list(pair) for pair in summary.residues] == [[0, 1], [2, 1]]

    # extrapolation is flagged where the grid was never swept
    vllm = HitLedger("vllm")
    assert vllm.record(P1=7392, payload_tokens=1).avalanche_extrapolated is True
    assert vllm.record(P1=7396, payload_tokens=1).avalanche_extrapolated is False


def test_unknown_observed_is_not_zero_and_not_a_match():
    """No observation is a third outcome: it is not a zero, and it is not explained."""
    hits = HitLedger("sglang")
    entry = hits.record(P1=8002, L=13, cell="res-8002-n1")
    assert entry.observed_uncached is None
    assert entry.delta is None  # not -15: an unobserved turn has no delta at all

    report = hits.reconcile()
    assert len(report.unknown) == 1
    assert report.exact == () and report.mismatched == ()
    check = report.unknown[0]
    assert (check.status, check.delta, check.observed_uncached) == ("unknown", None, None)
    assert report.explained_fraction == 0.0
    assert "not zero" in report.unexplained()[0]
    # an explicit None in a supplied series behaves the same way, and a 0 does not
    assert hits.reconcile([None]).unknown[0].status == "unknown"
    assert hits.reconcile([0]).mismatched[0].delta == -15

    summary = hits.summarise()
    assert summary.observed_billed_tokens is None
    assert summary.observed_unknown_turns == 1
    assert summary.billed_tokens == 15


def test_law_failures_carry_a_named_code_not_a_bare_valueerror():
    hits = HitLedger("sglang")
    hits.record(P1=8000, L=13)
    cases = [
        (lambda: HitLedger("some-other-build"), "PTR_LAW_UNKNOWN_SERVER"),
        (lambda: predict_uncached("sglang", -1, 13), "PTR_LAW_BOUND_INVALID"),
        (lambda: predict_uncached("sglang", 8000, True), "PTR_LAW_BOUND_INVALID"),
        (lambda: hits.record(P1=8000), "PTR_LAW_BOUND_INVALID"),
        (lambda: hits.record(P1=8000, L=13, payload_tokens=1), "PTR_LAW_BOUND_INVALID"),
        (lambda: hits.record(P1=8000, L=13, observed_uncached=-5), "PTR_LAW_BOUND_INVALID"),
        (lambda: hits.reconcile([1, 2]), "PTR_LAW_SERIES_LENGTH"),
        (lambda: hits.reconcile(["8000"]), "PTR_LAW_OBSERVED_INVALID"),
        (lambda: hits.reconcile([{"nope": 1}]), "PTR_LAW_OBSERVED_INVALID"),
        (lambda: hits.reconcile([{"observed_uncached": 13, "server": "vllm"}]),
         "PTR_LAW_OBSERVED_INVALID"),
    ]
    seen = []
    for case, expected in cases:
        with pytest.raises(PtrError) as excinfo:
            case()
        assert excinfo.value.code == expected
        assert str(excinfo.value).startswith(expected)
        assert isinstance(excinfo.value, ValueError)  # the ledger error family
        seen.append(excinfo.value.code)
    assert set(seen) == set(LEDGER_LAW_CODES)


def test_law_codes_extend_the_enumeration_without_colliding():
    from ptr_engine import PtrError as _PtrError  # noqa: F401

    controls = {
        "PTR_SYNTAX",
        "PTR_UNKNOWN_KIND",
        "PTR_UNKNOWN_ID",
        "PTR_SCOPE_UNGRANTED",
        "PTR_PROJECTION_UNENUMERATED",
        "PTR_POINTER_INVALID",
        "PTR_BUDGET_EXCEEDED",
    }
    assert len(set(LEDGER_LAW_CODES)) == 4
    assert set(LEDGER_LAW_CODES).isdisjoint(controls)
    assert set(LEDGER_LAW_CODES).isdisjoint(LEDGER_CODES)
    assert len(controls | set(LEDGER_CODES) | set(LEDGER_LAW_CODES)) == 16
    # the seven controls and five ledger codes are untouched
    assert len(controls) == 7 and len(set(LEDGER_CODES)) == 5


@pytest.mark.skipif(not MISS_LAW_ROWS.exists(), reason="the miss-law rows are not on disk")
def test_replay_of_the_measured_rows_reconciles_exactly():
    """Read the real rows (never fabricated) and reconcile every single-append turn."""
    raw = [json.loads(line) for line in MISS_LAW_ROWS.read_text(encoding="utf-8").splitlines()
           if line.strip()]
    measure = [row for row in raw
               if row.get("role") == "measure" and row.get("prev_prompt_tokens") is not None]
    assert len(measure) > 300

    # the rows' own L is the payload plus the framing tokens -- the constant is real
    assert all(row["L_app"] == row["n_payload"] + FRAMING_TOKENS for row in measure)

    ledgers = {server: HitLedger(server) for server in ("sglang", "vllm")}
    for row in measure:
        ledgers[row["server"]].record(
            P1=row["prev_prompt_tokens"],
            payload_tokens=row["n_payload"],
            observed_uncached=row["uncached_tokens"],
            cell=row["cell"],
        )

    total = explained = 0
    for server, hits in ledgers.items():
        report = hits.reconcile()
        assert report.mismatched == (), f"{server}: {report.unexplained()[:3]}"
        assert report.unknown == ()
        total += report.total
        explained += len(report.exact)
    assert explained == total == len(measure)

    # every null-cache row is an avalanche, every avalanche is a null-cache row,
    # and the avalanche residue set is exactly {0, 1} -- measured, not assumed.
    null_cached = [row for row in measure if not row["cached_reported"]]
    avalanches = [entry for entry in ledgers["sglang"].entries if entry.avalanche]
    assert len(avalanches) == len(null_cached) == 83
    assert {entry.residue for entry in avalanches} == {0, 1}
    assert ledgers["vllm"].summarise().avalanche_count == 0
    summary = ledgers["sglang"].summarise()
    assert summary.explained_fraction == 1.0
    assert summary.avalanche_tokens > 50 * max(entry.tail_uncached for entry in avalanches)
