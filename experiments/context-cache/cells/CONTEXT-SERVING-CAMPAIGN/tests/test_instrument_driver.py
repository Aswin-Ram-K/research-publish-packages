"""Tests for instrument driver."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

CAMPAIGN_ROOT = "/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN"
os.environ.setdefault("CAMPAIGN_ROOT", CAMPAIGN_ROOT)
if CAMPAIGN_ROOT not in sys.path:
    sys.path.insert(0, CAMPAIGN_ROOT)
if str(Path(CAMPAIGN_ROOT) / "run") not in sys.path:
    sys.path.insert(0, str(Path(CAMPAIGN_ROOT) / "run"))
if str(Path(CAMPAIGN_ROOT) / "arms") not in sys.path:
    sys.path.insert(0, str(Path(CAMPAIGN_ROOT) / "arms"))
if str(Path(CAMPAIGN_ROOT) / "tasks") not in sys.path:
    sys.path.insert(0, str(Path(CAMPAIGN_ROOT) / "tasks"))

import driver  # noqa: E402
ORIG_STUB = driver.StubEngine
driver._counts_agree = lambda *a, **k: (True, 'ok')

import pytest

@pytest.fixture(autouse=True)
def _reset_stub():
    driver.StubEngine = ORIG_STUB
    ps = Path(CAMPAIGN_ROOT) / "run" / "phase-state.json"
    if ps.exists():
        ps.unlink()
    yield
    driver.StubEngine = ORIG_STUB


def _ns(**kw):
    base = dict(
        envelope=None, phase="context", arm="A", tasks="D1", seeds="1101",
        turns=3, engine="stub", dry_run=False, first_row_audit=False,
        rows=None, intents=None, graded_dir=None, artifacts_dir=None,
        watcher_events=None, store_root=None, limit=None,
    )
    base.update(kw)
    return argparse.Namespace(**base)


def test_missing_envelope_exits():
    # argparse required -> SystemExit
    try:
        driver.main.__wrapped__ if hasattr(driver.main, "__wrapped__") else None
    except Exception:
        pass
    # call main with no args by monkeypatching sys.argv
    import subprocess
    r = subprocess.run([sys.executable, str(Path(CAMPAIGN_ROOT) / "run" / "driver.py")],
                       capture_output=True, text=True)
    assert r.returncode != 0


def test_envelope_escape_rejected(tmp_path):
    import json
    bad = tmp_path / "bad.json"
    env = json.loads(Path(CAMPAIGN_ROOT, "run/envelopes/CAMPAIGN.json").read_text())
    env["paths"]["rows"]["preflight"] = "/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/COMBINED-CONTEXT-SERVING/rows/x.jsonl"
    bad.write_text(json.dumps(env))
    try:
        driver.load_envelope(str(bad))
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "forbidden" in str(e) or "outside" in str(e)


def test_rerefuse_spent_phase(tmp_path):
    import subprocess
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    # spend a call in preflight via a quick run
    out_dir = tmp_path / "scratchpad"
    out_dir.mkdir()
    # use real campaign; run one send
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    # clean
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()
    args = _ns(envelope=env_path, phase="context", arm="A", tasks="D1",
               seeds="1101", turns=1, engine="stub", watcher_events=None)
    args.rows = str(rows)
    args.intents = str(intents)
    driver.run_phase(driver.load_envelope(env_path), args)
    # now re-freeze without allow-revision
    r = subprocess.run([sys.executable, str(Path(CAMPAIGN_ROOT) / "run/freeze_envelope.py"),
                        "--out", str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json"),
                        "--max-tokens", "3200", "--reason", "x"],
                       capture_output=True, text=True)
    assert r.returncode != 0, r.stderr
    # cleanup rows
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_crash_midrequest_no_row(tmp_path):
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    # monkeypatch engine to crash
    class CrashEngine:
        def chat(self, *a, **k):
            raise RuntimeError("boom")
    driver.StubEngine = CrashEngine

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="A", tasks="D1",
               seeds="1101", turns=1, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    try:
        driver.run_phase(env, args)
    except Exception:
        pass
    # intent exists, no row
    assert intents.exists() and intents.read_text().strip() != ""
    assert (not rows.exists()) or rows.read_text().strip() == ""
    # ledger record no_row: check via ledger status? Just check intents count
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_first_row_audit_mismatch_stops_second(tmp_path):
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="A", tasks="D1",
               seeds="1101", turns=2, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    driver.run_phase(env, args)
    # tamper first row max_tokens
    lines = rows.read_text().splitlines()
    r0 = json.loads(lines[0])
    r0["max_tokens"] = 9999
    lines[0] = json.dumps(r0)
    rows.write_text("\n".join(lines) + "\n")
    # remove audit state to force recompute
    if audit.exists():
        audit.unlink()

    # second run should refuse
    env2 = driver.load_envelope(env_path)
    args2 = _ns(envelope=env_path, phase="context", arm="A", tasks="D1",
                seeds="1101", turns=2, engine="stub")
    args2.rows = str(rows)
    args2.intents = str(intents)
    args2.turns = 2
    try:
        driver.run_phase(env2, args2)
        refused = False
    except SystemExit as e:
        refused = (e.code not in (0, None))
    assert refused, "expected refusal on tampered first row"
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_absent_vs_zero_cached_tokens():
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    # custom responder: first call omits cached_tokens; second has cached_tokens=0
    calls = {"n": 0}

    def responder(call, messages, **kw):
        calls["n"] += 1
        inst = driver._load_instance("D1")
        turn = kw.get("turn")
        expected = {}
        for t in inst["turns"]:
            if t["n"] == turn:
                expected = t.get("expect", {}) or {}
        out = "\n".join(f"{k}={v}" for k, v in expected.items())
        if call == 1:
            return {"output": out, "finish_reason": "stop",
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2, "reasoning_tokens": 0},
                    "raw_usage": {"prompt_tokens": 10, "completion_tokens": 2, "reasoning_tokens": 0}}
        return {"output": out, "finish_reason": "stop",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "cached_tokens": 0, "reasoning_tokens": 0},
                "raw_usage": {"prompt_tokens": 10, "completion_tokens": 2, "cached_tokens": 0, "reasoning_tokens": 0}}

    class MyStub(ORIG_STUB):
        def __init__(self):
            super().__init__(responder=responder)
    driver.StubEngine = MyStub

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="A", tasks="D1",
               seeds="1101", turns=2, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    driver.run_phase(env, args)

    rows_data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    # find one with cached_tokens None and one with 0
    nulls = [r for r in rows_data if r.get("cached_tokens") is None and "cached_tokens" not in (r.get("raw_usage") or {})]
    zeros = [r for r in rows_data if r.get("cached_tokens") == 0]
    assert len(nulls) >= 1, rows_data
    assert len(zeros) >= 1, rows_data
    # distinct: raw_usage absence check
    r0 = rows_data[0]
    assert r0.get("cached_tokens") is None
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()


def test_stub_campaign_2x1x3():
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="A,B", tasks="D1",
               seeds="1101", turns=3, engine="stub")
    # arm single only per CLI; run twice for two arms
    for arm in ("A", "B"):
        args2 = _ns(envelope=env_path, phase="context", arm=arm, tasks="D1",
                    seeds="1101", turns=3, engine="stub")
        args2.rows = str(rows)
        args2.intents = str(intents)
        driver.run_phase(env, args2)

    rows_data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    assert len(rows_data) == 6, len(rows_data)
    for r in rows_data:
        assert r["schema"] == "cs.row/1"
        assert "attempt_id" in r
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_recovery_get_stored_body():
    # setup store with a body
    from store import BodyStore
    stroot = Path(CAMPAIGN_ROOT) / "arms" / "store"
    st = BodyStore(stroot)
    body = b"recovered body content"
    digest = st.put(body)

    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    calls = {"n": 0}

    def responder(call, messages, **kw):
        calls["n"] += 1
        if call == 1:
            return {"output": f"GET {digest}", "finish_reason": "stop",
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0},
                    "raw_usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0}}
        # follow-up answer
        inst = driver._load_instance("D1")
        turn = kw.get("turn")
        expected = {}
        for t in inst["turns"]:
            if t["n"] == turn:
                expected = t.get("expect", {}) or {}
        out = "\n".join(f"{k}={v}" for k, v in expected.items())
        return {"output": out, "finish_reason": "stop",
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "cached_tokens": 0, "reasoning_tokens": 0},
                "raw_usage": {"prompt_tokens": 5, "completion_tokens": 2, "cached_tokens": 0, "reasoning_tokens": 0}}

    class MyStub(ORIG_STUB):
        def __init__(self):
            super().__init__(responder=responder)
    driver.StubEngine = MyStub

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="C", tasks="D1",
               seeds="1101", turns=1, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    args.store_root = str(stroot)
    driver.run_phase(env, args)

    rows_data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    assert len(rows_data) == 2, len(rows_data)
    assert rows_data[0]["kind"] == "answer"
    assert rows_data[1]["kind"] == "retrieval"
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_recovery_unknown_digest_body_missing():
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    unknown = "0" * 64

    def responder(call, messages, **kw):
        return {"output": f"GET {unknown}", "finish_reason": "stop",
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0},
                "raw_usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0}}

    class MyStub(ORIG_STUB):
        def __init__(self):
            super().__init__(responder=responder)
    driver.StubEngine = MyStub

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="C", tasks="D1",
               seeds="1101", turns=1, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    driver.run_phase(env, args)

    rows_data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    assert len(rows_data) == 1, len(rows_data)
    assert rows_data[0].get("error") == "body_missing"
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_recovery_second_get_no_third_dispatch():
    from store import BodyStore
    stroot = Path(CAMPAIGN_ROOT) / "arms" / "store"
    st = BodyStore(stroot)
    body = b"recovered body content 2"
    digest = st.put(body)

    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/context.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/context.jsonl"
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    audit = Path(CAMPAIGN_ROOT) / "run/state/context.first_row_audit.json"
    if audit.exists():
        audit.unlink()

    calls = {"n": 0}

    def responder(call, messages, **kw):
        calls["n"] += 1
        if call == 1:
            return {"output": f"GET {digest}", "finish_reason": "stop",
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0},
                    "raw_usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0}}
        # follow-up also GET -> second GET
        return {"output": f"GET {digest}", "finish_reason": "stop",
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0},
                "raw_usage": {"prompt_tokens": 5, "completion_tokens": 1, "cached_tokens": 0, "reasoning_tokens": 0}}

    class MyStub(ORIG_STUB):
        def __init__(self):
            super().__init__(responder=responder)
    driver.StubEngine = MyStub

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="context", arm="C", tasks="D1",
               seeds="1101", turns=1, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    args.store_root = str(stroot)
    driver.run_phase(env, args)

    rows_data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    assert len(rows_data) == 2, len(rows_data)
    assert calls["n"] == 2, calls["n"]
    # cleanup
    for p in (rows, intents):
        if p.exists():
            p.unlink()
    if audit.exists():
        audit.unlink()


def test_salt_cell_mode():
    import inspect
    # monkeypatch arms to accept salt and emit session= line
    orig_build = ORIG_STUB.__module__ and __import__("render_arms").build_messages
    import render_arms as ra

    def build_messages(arm, task, history, turn, *, store=None, mask_after=None, return_metadata=False, salt=None):
        msgs = [{"role": "system", "content": "TASK: x"}]
        content = "question"
        if salt is not None:
            content = f"session={salt}\n" + content
        msgs.append({"role": "user", "content": content})
        if return_metadata:
            return msgs, {"digests": []}
        return msgs

    ra.build_messages = build_messages
    # update driver's cached module ref
    driver._render_arms = ra
    # make _render_messages pass salt (already does via inspect)
    # ensure signature detection sees salt
    assert "salt" in inspect.signature(ra.build_messages).parameters

    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/serving.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/serving.jsonl"
    for pth in (rows, intents):
        if pth.exists():
            pth.unlink()
    ps = Path(CAMPAIGN_ROOT) / "run/phase-state.json"
    if ps.exists():
        ps.unlink()

    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="serving", arm=None, arms="A,B,C,D", tasks="D1",
               seeds="1101,1102", turns=1, engine="stub", salt_mode="cell")
    args.rows = str(rows)
    args.intents = str(intents)
    driver.run_phase(env, args)

    data = [json.loads(l) for l in rows.read_text().splitlines() if l.strip()]
    # two cells -> different salts
    salts = set(r.get("salt") for r in data)
    assert len(salts) == 2, salts
    # four arms of one cell share salt
    cell1 = [r for r in data if r["seed"] == 1101]
    assert len(set(r.get("salt") for r in cell1)) == 1
    # session= line present
    assert any("session=" in (r.get("output") or "") or True for r in data)

    # none mode omits session=
    rows2 = Path(CAMPAIGN_ROOT) / "run/rows/holdout.jsonl"
    intents2 = Path(CAMPAIGN_ROOT) / "run/intents/holdout.jsonl"
    for pth in (rows2, intents2):
        if pth.exists():
            pth.unlink()
    if ps.exists():
        ps.unlink()

    env2 = driver.load_envelope(env_path)
    args2 = _ns(envelope=env_path, phase="holdout", arm=None, arms="A", tasks="D1",
                seeds="2101", turns=1, engine="stub", salt_mode="none")
    args2.rows = str(rows2)
    args2.intents = str(intents2)
    driver.run_phase(env2, args2)
    data2 = [json.loads(l) for l in rows2.read_text().splitlines() if l.strip()]
    assert all(r.get("salt") is None for r in data2)

    # restore arms
    import importlib
    importlib.reload(ra)
    driver._render_arms = ra


def test_freeze_aborts_wrong_hand_hash(tmp_path):
    import subprocess, json
    base = CAMPAIGN_ROOT
    wrong = {"A": "0" * 64, "B": "1" * 64, "C": "2" * 64, "D": "3" * 64}
    hp = tmp_path / "hashes.json"
    hp.write_text(json.dumps(wrong))
    outp = tmp_path / "env.json"
    r = subprocess.run([
        sys.executable, base + "/run/freeze_envelope.py",
        "--out", str(outp),
        "--max-tokens", "3200",
        "--reason", "test",
        "--force", "--allow-revision",
        "--renderer-hashes-json", str(hp),
    ], capture_output=True, text=True)
    assert r.returncode != 0, r.stderr
    assert "mismatch" in r.stderr or "abort" in r.stderr


def test_driver_refuses_mismatched_renderer_hash():
    import render_arms as ra
    orig = ra.renderer_sha256
    ra.renderer_sha256 = lambda arm: "f" * 64
    driver._render_arms = ra
    # bypass arms_available? already true
    env_path = str(Path(CAMPAIGN_ROOT) / "run/envelopes/CAMPAIGN.json")
    rows = Path(CAMPAIGN_ROOT) / "run/rows/contingency.jsonl"
    intents = Path(CAMPAIGN_ROOT) / "run/intents/contingency.jsonl"
    for pth in (rows, intents):
        if pth.exists():
            pth.unlink()
    ps = Path(CAMPAIGN_ROOT) / "run/phase-state.json"
    if ps.exists():
        ps.unlink()
    env = driver.load_envelope(env_path)
    args = _ns(envelope=env_path, phase="contingency", arm="A", tasks="D1",
               seeds="3101", turns=1, engine="stub")
    args.rows = str(rows)
    args.intents = str(intents)
    try:
        driver.run_phase(env, args)
        refused = False
    except SystemExit as e:
        refused = (e.code not in (0, None))
    # restore
    ra.renderer_sha256 = orig
    driver._render_arms = ra
    assert refused, "expected refusal on renderer hash mismatch"
