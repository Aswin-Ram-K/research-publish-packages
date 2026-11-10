"""Null-accounting guard for the typed-context pilot adapter.

The contract (``handoff from consonance/INTERFACE_CONTRACT.md`` §2) says an
absent ``cached_tokens`` means *not reported*, never zero.  The shared meter
(``resextract.context.meter.normalise_cache``) violates that by design — it
maps a missing ``prompt_tokens_details`` to ``0`` — and the STATE-CLIFF rows
show the consequence: every row carries ``usage: null`` and a numeric 0, so a
run that never reported cache detail is indistinguishable from a run that
reported a genuine zero.

These tests pin the adapter's behaviour in both directions, offline.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

ADAPTER_PATH = Path(
    os.environ.get(
        "HL_ADAPTER_PATH",
        str(
            Path(__file__).resolve().parents[1]
            / "experiments/context-cache/cells/HL-PILOT/tools/adapter.py"
        ),
    )
)


def _load_adapter():
    spec = importlib.util.spec_from_file_location("hl_pilot_adapter", ADAPTER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter_mod = _load_adapter()


def _sse(chunks: list[dict]) -> httpx.Response:
    lines = [f"data: {json.dumps(c)}" for c in chunks]
    lines.append("data: [DONE]")
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        text="\n\n".join(lines) + "\n\n",
    )


def _chunks(usage: dict | None, *, text: str = "ok") -> list[dict]:
    out = [
        {
            "choices": [
                {"index": 0, "delta": {"content": text}, "finish_reason": None}
            ]
        }
    ]
    final: dict = {
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    if usage is not None:
        final["usage"] = usage
    out.append(final)
    return out


def _run(usage: dict | None) -> dict:
    def handler(request: httpx.Request) -> httpx.Response:
        return _sse(_chunks(usage))

    a = adapter_mod.Adapter(transport=httpx.MockTransport(handler))
    return a.chat(
        [{"role": "user", "content": "hello"}],
        max_tokens=4,
        run_id="t",
        arm="A",
        task_id="t1",
        step=1,
    )


def test_absent_cache_details_stay_unknown():
    row = _run({"prompt_tokens": 900, "completion_tokens": 3})
    assert row["prompt_tokens"] == 900
    assert row["cached_tokens"] is None
    assert row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] is None
    assert row["cache_usage_reported"] is False


def test_null_cache_details_stay_unknown():
    row = _run(
        {"prompt_tokens": 900, "completion_tokens": 3, "prompt_tokens_details": None}
    )
    assert row["cached_tokens"] is None
    assert row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] is None


def test_empty_cache_details_stay_unknown():
    row = _run(
        {"prompt_tokens": 900, "completion_tokens": 3, "prompt_tokens_details": {}}
    )
    assert row["cached_tokens"] is None


def test_reported_zero_is_kept_as_zero():
    row = _run(
        {
            "prompt_tokens": 900,
            "completion_tokens": 3,
            "prompt_tokens_details": {"cached_tokens": 0},
        }
    )
    assert row["cached_tokens"] == 0
    assert row["cache_usage_reported"] is True
    assert row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] == 900


def test_reported_hit_is_retained():
    row = _run(
        {
            "prompt_tokens": 900,
            "completion_tokens": 3,
            "prompt_tokens_details": {"cached_tokens": 832},
        }
    )
    assert row["cached_tokens"] == 832
    assert row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] == 68


def test_missing_usage_block_is_an_instrument_error_not_a_zero():
    with pytest.raises(adapter_mod.InstrumentError):
        _run(None)


def test_uncached_prefill_is_never_claimed_as_measured():
    row = _run(
        {
            "prompt_tokens": 900,
            "completion_tokens": 3,
            "prompt_tokens_details": {"cached_tokens": 832},
        }
    )
    assert row["uncached_prefill_tokens"] is None
    assert "uncached_prefill_tokens_from_prompt_minus_cached" in row["derived"]
