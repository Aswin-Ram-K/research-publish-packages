"""Invariant 5 + 6: cache normalisation (with counted clamping) and CacheRow."""

from __future__ import annotations

import dataclasses
import json

import pytest

from resextract.context import CacheMeter, CacheRow, normalise_cache, rows_from_jsonl
from resextract.context import meter as meter_module


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (None, (0, 0)),
        ({}, (0, 0)),
        ({"prompt_tokens": 100}, (100, 0)),
        ({"prompt_tokens": 100, "prompt_tokens_details": None}, (100, 0)),
        ({"prompt_tokens": 612, "prompt_tokens_details": {"cached_tokens": 0}}, (612, 0)),
        ({"prompt_tokens": 612, "prompt_tokens_details": {"cached_tokens": 576}}, (612, 576)),
        ({"prompt_tokens": 807, "prompt_tokens_details": {"cached_tokens": 768}}, (807, 768)),
        # DEFECT 4: an impossible pair is clamped, never passed through.
        ({"prompt_tokens": 5, "prompt_tokens_details": {"cached_tokens": 999}}, (5, 5)),
        ({"prompt_tokens": 612, "prompt_tokens_details": {"cached_tokens": -40}}, (612, 0)),
        ({"prompt_tokens": -7, "prompt_tokens_details": {"cached_tokens": 3}}, (0, 0)),
    ],
)
def test_normalise_cache_maps_null_to_zero(usage, expected) -> None:
    prompt, cached = normalise_cache(usage)
    assert (prompt, cached) == expected
    assert 0 <= cached <= prompt, "normalise_cache must never return cached > prompt"


def test_normalise_cache_accepts_top_level_cached_tokens() -> None:
    prompt, cached = normalise_cache({"prompt_tokens": 807, "cached_tokens": 576})
    assert (prompt, cached) == (807, 576)
    # Without a prompt count the pair is impossible (0 prompt, 576 cached), so
    # the clamp collapses it to (0, 0) instead of reporting a cache hit larger
    # than the prompt it came from.
    assert normalise_cache({"cached_tokens": 576}) == (0, 0)


def test_clamp_is_counted_and_reported_not_silent() -> None:
    meter_module.reset_clamp_stats()
    assert normalise_cache(
        {"prompt_tokens": 5, "prompt_tokens_details": {"cached_tokens": 999}}
    ) == (5, 5)
    assert normalise_cache(
        {"prompt_tokens": 100, "prompt_tokens_details": {"cached_tokens": 120}}
    ) == (100, 100)
    stats = meter_module.clamp_stats()
    assert stats == {"clamped": 2, "max_overrun": 994}, (
        f"clamps must be counted and their worst overrun reported, got {stats}"
    )

    # A legitimate value is not counted, and negative cached tokens are not an
    # overrun (they clamp to 0 before the upper clamp is considered).
    normalise_cache({"prompt_tokens": 100, "prompt_tokens_details": {"cached_tokens": 64}})
    normalise_cache({"prompt_tokens": 100, "prompt_tokens_details": {"cached_tokens": -1}})
    assert meter_module.clamp_stats() == {"clamped": 2, "max_overrun": 994}

    meter_module.reset_clamp_stats()
    assert meter_module.clamp_stats() == {"clamped": 0, "max_overrun": 0}


def make_row(**overrides) -> CacheRow:
    values = dict(
        cell="cell-a",
        arm="main",
        policy="pointer",
        case_id="case-01",
        turn=2,
        rep=1,
        salt="0123456789abcdef",
        prompt_tokens=612,
        cached_tokens=576,
        uncached=36,
        ttft_ms=12.5,
        wall_ms=40.25,
        completion_tokens=17,
        status=200,
        evicted=False,
        prefix_sha256="a" * 64,
    )
    values.update(overrides)
    return CacheRow(**values)


def test_cache_row_json_round_trip_preserves_every_field() -> None:
    row = make_row()
    blob = json.dumps(row.to_dict(), sort_keys=True)
    restored = CacheRow.from_dict(json.loads(blob))

    assert restored == row
    assert restored.to_dict() == row.to_dict()
    assert [f.name for f in dataclasses.fields(CacheRow)] == list(row.to_dict())


def test_cache_row_null_status_round_trips() -> None:
    row = make_row(status=None, evicted=True)
    restored = CacheRow.from_dict(json.loads(row.to_json()))
    assert restored.status is None
    assert restored.evicted is True


def test_meter_jsonl_round_trip(tmp_path) -> None:
    meter = CacheMeter()
    rows = [make_row(turn=1), make_row(turn=2, cached_tokens=576, uncached=36)]
    for row in rows:
        meter.record(row)

    assert meter.rows() == rows
    assert meter.rows() is not meter.rows(), "rows() must hand out a copy"

    path = meter.to_jsonl(tmp_path / "nested" / "rows.jsonl")
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 2
    assert rows_from_jsonl(path) == rows
