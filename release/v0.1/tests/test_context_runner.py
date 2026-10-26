"""Invariant 7 + harness behaviour: 64-token tax, injected-send runner, analysis.

Everything here is offline.  ``runner.run_cell`` takes ``send`` as a callable;
the fakes below return the same 7-tuple shape as ``client.chat``.  ``client``
is only *imported* and inspected -- calling it would need the live endpoint.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from resextract.context import CacheRow, make_salt

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "context-cache"


def load_module(stem: str):
    path = EXPERIMENT / f"{stem}.py"
    name = f"ctxcache_{stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return load_module("runner")


@pytest.fixture(scope="module")
def analyze():
    return load_module("analyze")


def row(**overrides) -> CacheRow:
    values = dict(
        cell="c",
        arm="main",
        policy="pointer",
        case_id="case",
        turn=1,
        rep=1,
        salt="0" * 16,
        prompt_tokens=612,
        cached_tokens=576,
        uncached=36,
        ttft_ms=10.0,
        wall_ms=20.0,
        completion_tokens=5,
        status=200,
        evicted=False,
        prefix_sha256="p" * 64,
    )
    values.update(overrides)
    return CacheRow(**values)


# --------------------------------------------------------------------------- #
# Invariant 7: uncached == prompt mod 64
# --------------------------------------------------------------------------- #
def test_tax_error_is_zero_on_the_64_token_grid(analyze) -> None:
    rows = [
        row(prompt_tokens=612, cached_tokens=576, uncached=612 % 64),
        row(prompt_tokens=807, cached_tokens=768, uncached=807 % 64),
        row(prompt_tokens=640, cached_tokens=640, uncached=0),
    ]
    assert analyze.tax_error(rows) == 0


def test_tax_error_reports_the_off_grid_residue(analyze) -> None:
    rows = [row(prompt_tokens=612, cached_tokens=576, uncached=612 % 64 + 40)]
    assert analyze.tax_error(rows) == 40


# --------------------------------------------------------------------------- #
# Runner with an injected send
# --------------------------------------------------------------------------- #
class FakeSend:
    """Records messages and replays a deterministic cached-token schedule."""

    def __init__(self, cold_cached: int = 0, warm_cached: int = 576) -> None:
        self.cold_cached = cold_cached
        self.warm_cached = warm_cached
        self.messages: list[list[dict]] = []

    def __call__(self, messages: list[dict]):
        self.messages.append(messages)
        cached = self.cold_cached if len(self.messages) == 1 else self.warm_cached
        return (612, cached, 9, 11.0, 30.0, 200, "ok")


def make_case(runner, turns: int = 3):
    return runner.Case(
        "case-01",
        "You are a careful analyst.",
        tuple(runner.Turn(f"turn {i}: inspect item {i}", {"step": str(i)}) for i in range(1, turns + 1)),
    )


def test_runner_records_rows_without_any_network(runner, analyze, tmp_path) -> None:
    send = FakeSend()
    case = make_case(runner)
    cell = runner.Cell(
        "cell-a", "main", "pointer", case.case_id, depth=3, reps=2,
        salt=make_salt(3), budget_tokens=10**9, keep_last=2,
    )

    result = runner.run_cell(cell, case, send)

    assert result.evicted is False
    assert result.events == []
    assert len(result.rows) == 6
    assert len(send.messages) == 6
    assert [r.turn for r in result.rows] == [1, 2, 3, 1, 2, 3]
    assert [r.rep for r in result.rows] == [1, 1, 1, 2, 2, 2]
    assert all(r.cell == "cell-a" and r.arm == "main" and r.policy == "pointer" for r in result.rows)
    assert all(r.salt == make_salt(3) for r in result.rows)
    assert result.rows[0].uncached == 612 and result.rows[0].cached_tokens == 0
    assert result.rows[1].uncached == 612 - 576 == 36
    assert all(len(r.prefix_sha256) == 64 for r in result.rows)

    # POINTER's invariant head is byte-stable, so its digest must not change.
    for rep in (1, 2):
        digests = {r.prefix_sha256 for r in result.rows if r.rep == rep}
        assert len(digests) == 1

    assert analyze.hit_rate(result.rows) == pytest.approx(5 * 576 / (6 * 612))
    assert len(analyze.per_turn_series(result.rows)) == 6
    assert len(analyze.summary_table(result.rows)) == 1
    assert analyze.summary_table(result.rows)[0]["rows"] == 6


def test_runner_flags_a_cell_that_has_cache_on_turn_one(runner) -> None:
    send = FakeSend(cold_cached=128)
    result = runner.run_cell(
        runner.Cell("cell-b", "main", "pointer", "case-01", 1, 2, make_salt(4)),
        make_case(runner, turns=1),
        send,
    )
    assert result.evicted is True
    assert all(r.evicted for r in result.rows), "the cell-level flag must land on every row"


def test_runner_detects_a_later_drop_to_zero(runner) -> None:
    calls = {"n": 0}

    def drop(messages):
        calls["n"] += 1
        cached = 0 if calls["n"] == 1 else (576 if calls["n"] == 2 else 0)
        return {"prompt_tokens": 640, "cached_tokens": cached, "completion_tokens": 1,
                "ttft_ms": 1.0, "wall_ms": 2.0, "status": 200, "text": ""}

    result = runner.run_cell(
        runner.Cell("cell-c", "main", "pointer", "case-01", 3, 1, make_salt(5)),
        make_case(runner),
        drop,
    )
    assert [r.cached_tokens for r in result.rows] == [0, 576, 0]
    assert result.evicted is True


def test_runner_compacts_at_the_token_budget(runner) -> None:
    case = make_case(runner)
    cell = runner.Cell(
        "cell-d", "main", "pointer", "case-01", 4, 1, make_salt(6),
        budget_tokens=4, keep_last=1,
    )
    summarised = runner.run_cell(cell, case, FakeSend())
    assert summarised.events, "a 4-token budget must trigger compaction"
    assert all(event["forked"] is False for event in summarised.events)
    assert summarised.events[0]["tokens_before"] > summarised.events[0]["tokens_after"]

    forked = runner.run_cell(cell, case, FakeSend(), compaction="fork")
    assert forked.events and all(event["forked"] for event in forked.events)


def test_runner_writes_jsonl_the_analyzer_can_read(runner, analyze, tmp_path) -> None:
    from resextract.context import CacheMeter, rows_from_jsonl

    meter = CacheMeter()
    case = make_case(runner)
    cell = runner.Cell("cell-e", "main", "pointer", case.case_id, 2, 1, make_salt(7))
    runner.run_cell(cell, case, FakeSend(), meter)

    path = meter.to_jsonl(tmp_path / "rows.jsonl")
    restored = rows_from_jsonl(path)
    assert restored == meter.rows()
    assert json.loads(path.read_text().splitlines()[0])["cell"] == "cell-e"
    assert analyze.compaction_effect(restored)["prefix_breaks"] == 0


def test_mutable_policy_prefix_digest_changes_every_turn(runner) -> None:
    case = make_case(runner, turns=3)
    cell = runner.Cell("cell-f", "main", "naive_mutable", case.case_id, 3, 1, make_salt(8))
    result = runner.run_cell(cell, case, FakeSend())
    digests = [r.prefix_sha256 for r in result.rows]
    assert len(set(digests)) == 3, "NAIVE_MUTABLE must rewrite the cacheable head each turn"


# --------------------------------------------------------------------------- #
# Client is written but never exercised (no live calls in U1)
# --------------------------------------------------------------------------- #
def test_client_module_exposes_chat_without_touching_the_network() -> None:
    client = load_module("client")
    assert callable(client.chat)
    payload = client.ChatClient().payload(
        [{"role": "user", "content": "hi"}], max_tokens=8, thinking=False, stream=True
    )
    assert payload["temperature"] == 0
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["stream_options"] == {"include_usage": True}
    assert "serving-host" in client.DEFAULT_BASE_URL


def test_analyze_compaction_effect_reports_ttft_and_cache(analyze) -> None:
    rows = [
        row(turn=1, ttft_ms=10.0, prefix_sha256="a" * 64, cached_tokens=0),
        row(turn=2, ttft_ms=12.0, prefix_sha256="a" * 64, cached_tokens=576),
        row(turn=3, ttft_ms=90.0, prefix_sha256="b" * 64, cached_tokens=0),
    ]
    effect = analyze.compaction_effect(rows)
    assert effect["prefix_breaks"] == 1
    assert effect["ttft_before_ms"] == pytest.approx(12.0)
    assert effect["ttft_after_ms"] == pytest.approx(90.0)
    assert effect["delta_ttft_ms"] == pytest.approx(78.0)
    assert effect["cached_after_mean"] == pytest.approx(0.0)
