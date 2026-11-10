import json
import sys
from pathlib import Path

import httpx
import pytest

CELL = Path(__file__).resolve().parents[2]
RUN = CELL / "run"
sys.path.insert(0, str(RUN))
import driver  # type: ignore


def _tmp_paths(tmp_path):
    return dict(
        rows_path=tmp_path / "rows.jsonl",
        intents_path=tmp_path / "intents.jsonl",
        counter_path=tmp_path / "spent.json",
        graded_dir=tmp_path / "graded",
        artifacts_dir=tmp_path / "artifacts",
        lock_path=str(tmp_path / "lock"),
    )


def _ok_handler():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        body = (
            'data: {"choices":[{"delta":{"content":"print(1)\\n"}}],'
            '"finish_reason":"stop"}\n'
            'data: {"usage":{"prompt_tokens":10,"completion_tokens":5}}\n'
            "data: [DONE]\n"
        )
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    return handler, calls


def test_rows_full_schema(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)
    rows = driver.run_experiment(transport=transport, limit=1, cap=10, **paths)
    assert len(rows) == 1
    r = rows[0]
    for k in [
        "send_id", "started_utc", "ended_utc", "status", "finish_reason", "text",
        "prompt_sha256", "prompt_bytes", "prompt_tokens", "cached_tokens",
        "derived", "usage_raw", "fingerprints", "task", "arm", "turn", "max_tokens",
    ]:
        assert k in r, k
    assert r["status"] == 200
    assert r["cached_tokens"] is None  # usage omitted cached_tokens
    assert r["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] is None
    graded = list((tmp_path / "graded").rglob("*.json"))
    assert len(graded) == 1


def test_cached_tokens_null_when_omitted(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)
    rows = driver.run_experiment(transport=transport, limit=1, cap=10, **paths)
    assert rows[0]["cached_tokens"] is None


def test_counter_stops_at_cap(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)
    with pytest.raises(RuntimeError):
        driver.run_experiment(transport=transport, limit=4, cap=3, **paths)
    counter = json.loads((tmp_path / "spent.json").read_text())
    assert counter["spent"] == 3
    assert counter["spent"] <= counter["cap"]
    rows = [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 3


def test_500_recorded_no_retry(tmp_path):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500, text="boom")

    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)
    rows = driver.run_experiment(transport=transport, limit=1, cap=10, **paths)
    assert len(rows) == 1
    assert rows[0]["status"] == 500
    assert calls["n"] == 1  # no retry


def test_resume_no_duplicate(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)
    driver.run_experiment(transport=transport, limit=2, cap=10, **paths)
    handler2, calls2 = _ok_handler()
    transport2 = httpx.MockTransport(handler2)
    driver.run_experiment(transport=transport2, limit=2, cap=10, resume_arm=True, **paths)
    rows = [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    keys = [(r["task"], r["arm"], r["turn"]) for r in rows]
    assert len(set(keys)) == len(keys)


def test_watcher_error_rate_stops(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)

    def watcher_check(completed_count):
        if completed_count >= 2:
            return "ERROR_RATE"
        return None

    with pytest.raises(RuntimeError, match="ERROR_RATE"):
        driver.run_experiment(transport=transport, limit=5, cap=10, watcher_check=watcher_check, **paths)
    rows = [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 2


def test_watcher_process_vanished_stops(tmp_path):
    handler, calls = _ok_handler()
    transport = httpx.MockTransport(handler)
    paths = _tmp_paths(tmp_path)

    def watcher_check(completed_count):
        if completed_count >= 1:
            return "PROCESS_VANISHED"
        return None

    with pytest.raises(RuntimeError, match="PROCESS_VANISHED"):
        driver.run_experiment(transport=transport, limit=5, cap=10, watcher_check=watcher_check, **paths)
    rows = [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 1
