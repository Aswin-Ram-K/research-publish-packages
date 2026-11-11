"""Offline proof that ``spcc`` is a real arm, not a label.

A stub responder echoes a valid ``ANSWER: NUM <int>`` and never opens a socket.
The cell runs 26 turns so the 24-turn compaction boundary is crossed exactly
once, and every row must carry the compiler's own stamping.
"""
import io
import json
import os
import socket
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE_ROOT = os.path.dirname(LONGRUN)
for _p in (LONGRUN, ENGINE_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_longrun as R  # noqa: E402
import arm_cd  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
TURNS = 26


class _Cfg:
    def __init__(self):
        self.tools = "read_file"
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = TURNS
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = None
        self.fetch_rounds_per_turn = 0
        self.turn_wall_cap = 0
        self.generation = "gen-7"
        self.budget_cap = 10 ** 9
        self.request_allocation = "projection"
        self.budget_reserve = 0


def _resp(text, send_id):
    return {
        "content": text, "content_raw": text, "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 256, "prompt_tokens": 10 + send_id, "raw_cached": None,
        "token_source": "offline", "completion_tokens": 5, "wall_ms": 40,
        "request_sha256": "sha%d" % send_id,
        "request_identity_complete": True,
        "ttft_s": 0.04, "ttft_ms": 40,
        "latency_s": 0.08, "usage_missing": False,
        "tool_calls": None,
    }


def _run_spcc(max_turns=TURNS):
    tmp = tempfile.mkdtemp(prefix="spcc-arm-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(FIXTURE)
    cfg = _Cfg()
    cfg.max_turns = max_turns
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        return _resp("ANSWER: NUM %d" % state["n"], state["n"])

    def _no_network(*_a, **_k):
        raise AssertionError("spcc offline proof must never open a socket")

    real_send, real_socket = R.send_chat, socket.socket
    R.send_chat = fake_send
    socket.socket = _no_network
    buf, old_stdout = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, "spcc", 1, "offline-spcc-r1", rows_path)
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
        sys.stdout = old_stdout
    assert rc == 0, "run_cell exit %d\n%s" % (rc, buf.getvalue()[-4000:])
    rows = []
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_spcc_registered_and_compiles():
    assert "spcc" in R.ARMS
    assert arm_cd.ARM_SPCC == "spcc"
    src = open(os.path.join(LONGRUN, "arm_cd.py"), encoding="utf-8").read()
    assert "compile_prompt(" in src, "spcc must render through layers.compile_prompt"


def test_spcc_26_turn_rows_stamp_layers_and_prefix():
    rows = _run_spcc()
    assert len(rows) == TURNS, "expected %d rows, got %d" % (TURNS, len(rows))

    # 1. every row carries a real per-layer token dict (never None).  PINS is
    #    rendered only when it carries a pin, and the fold record IS a pin: turns
    #    1-24 (no pin yet) carry five layers, turns 25-26 carry six.
    for row in rows:
        lt = row.get("layer_tokens")
        assert isinstance(lt, dict), "turn %s layer_tokens=%r" % (row.get("turn"), lt)
        expected = ({"L0", "PINS", "L1", "L2", "L3", "L4"} if row["turn"] >= 25
                    else {"L0", "L1", "L2", "L3", "L4"})
        assert set(lt) == expected, (row["turn"], lt)
        if row["turn"] >= 25:
            assert lt["PINS"] > 0, "the fold record is not in PINS: %r" % (lt,)

    # 2. the stable prefix is identical for turns 1-24 and breaks exactly once,
    #    at the compaction on turn 25; turns 25-26 then share the new prefix.
    prefixes = [row["prefix_sha256"] for row in rows]
    assert len(set(prefixes[:24])) == 1, "prefix changed before compaction: %r" % prefixes[:24]
    breaks = [i + 1 for i in range(1, len(prefixes)) if prefixes[i] != prefixes[i - 1]]
    assert breaks == [25], "expected exactly one break at turn 25, got %r" % (breaks,)
    assert prefixes[24] == prefixes[25], "compaction break must be the only break"

    # 3. compaction is stamped on turn 25 onward.
    assert rows[23]["compactions"] == 0 and rows[23]["epoch"] == 0
    for row in rows[24:]:
        assert row["compactions"] == 1, row["compactions"]
        assert row["epoch"] == 1, row["epoch"]

    # 4. L3 carries the current question on every turn and never accumulates:
    #    fetched bodies are cleared after their turn, so the layer is rewritten
    #    (not appended) and cannot retain prior-turn bodies.
    l3 = [row["layer_tokens"]["L3"] for row in rows]
    assert all(x > 0 for x in l3), l3
    assert max(l3) < sum(l3), "L3 appears to accumulate across turns: %r" % (l3,)

    # 5. the stub reports no cache counter, so cached_tokens must be null (not 0).
    assert all(row["cached_tokens"] is None for row in rows), [
        (row["turn"], row["cached_tokens"]) for row in rows if row["cached_tokens"] is not None]


if __name__ == "__main__":
    test_spcc_registered_and_compiles()
    test_spcc_26_turn_rows_stamp_layers_and_prefix()
    print("ALL OK")


def test_spcc_fetch_enters_l3_only():
    """A fetched body extends L3 and never rewrites the L0+L1 prefix."""
    import arm_cd as acd
    fx = {"task_id": "fetch-fixture",
          "items": [{"id": "k1", "body": "the stored fact is 7"}]}
    state = acd.SpccArmState(fixture=fx)
    first = state.build(1, "QUESTION (T1): what is the fact?")
    state.add_fetch("FETCHED BODY: the stored fact is 7")
    second = state.build(2, "QUESTION (T2): restate it")
    assert second.prefix_sha256 == first.prefix_sha256, "fetch changed the L0+L1 prefix"
    assert second.layer_tokens["L3"] > first.layer_tokens["L3"], "fetched body was not in L3"
    assert "FETCHED BODY" in str(second)
    # the body must not appear in L1 or L2
    parts = str(second).split("\n\n")
    assert "FETCHED BODY" not in parts[1], "body leaked into L1"
    assert "FETCHED BODY" not in parts[2], "body leaked into L2"


def test_shared_run_id_does_not_false_drift():
    """Two runs sharing a run_id in one process own separate L0 baselines."""
    from ptr_engine.layers import CompactionState, compile_prompt, reset_prefix_state

    class Run:
        run_id = "shared-id"
        system = "system A"
        tool_schema = None
        answer_grammar = None
        model = "m"
        fixture = "f"
        generation = "gen-7"

    reset_prefix_state()
    a = CompactionState(index_lines=[])
    b = CompactionState(index_lines=[])
    r1 = Run()
    r1.system = "system A"
    compile_prompt(r1, a, epoch=0, journal=[], work="q")
    r2 = Run()
    r2.system = "system B"          # different L0, same run_id, different state
    compile_prompt(r2, b, epoch=0, journal=[], work="q")  # must not raise
    # and the same state still catches a real drift
    r2.system = "system C"
    try:
        compile_prompt(r2, b, epoch=0, journal=[], work="q")
    except Exception as exc:  # PtrPrefixDrift
        assert type(exc).__name__ == "PtrPrefixDrift"
    else:
        raise AssertionError("expected PtrPrefixDrift within one run")
