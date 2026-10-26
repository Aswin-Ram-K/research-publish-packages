"""Offline proof for FETCH-CHANNEL-FIX (engine base, durable rounds, duplicate billing).

Run from the workspace root:
  python3 experiments/ptr-engine/longrun/tests/test_tool_channel2.py
Exit 0 = every assertion below held.  The five required assertions:
  (a) `ptr_engine/resolve.py` resolves via the ENGINE base and returns lines 66-71 of
      the real experiments/ptr-engine/ptr_engine/resolve.py
  (b) `../../etc/passwd` and `/etc/passwd` are `path_refused` with ZERO reads from
      either base
  (c) an identical duplicate call in one turn executes once and bills once
      (`calls_billed == 1`), the second result carrying cached="true"
  (d) `--resume` with existing follow-up rows does NOT reset the round counter
      (24 spent -> the next call is refused `fetch_budget_exhausted`)
  (e) `--tools` off is byte-identical to the pre-fix runner (stdout sha unchanged)

Zero requests, no network: socket.socket raises for the whole run, send_chat is a
counting tripwire except where a canned function is installed, and the two dry-run
subprocesses in (e) are `--dry-run` only (they cannot reach the network by
construction: run_dry never calls send_chat).
"""

import builtins
import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

ENGINE_ROOT = os.path.join(WORKSPACE, R.ENGINE_ROOT_REL)
REAL_RESOLVE = os.path.join(ENGINE_ROOT, "ptr_engine", "resolve.py")
RESOLVE_REL = "ptr_engine/resolve.py"
FIXTURE2 = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
FIXTURE_OFF = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.json")
BASELINE = os.path.join(LONGRUN, "manifests", "v4tools2-baseline-pre.py")

OBSERVED_TURN = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                 '"start_line": 66, "end_line": 71}')
DUPLICATED_TURN = OBSERVED_TURN + "\n" + OBSERVED_TURN
# PROBE-CP3-V6 moved the per-arm refusal from PER TURN to PER CALL: a range the prompt
# already pins is served for zero rounds, so the round-budget refusal must be proven with a
# range the prompt does NOT carry.  L1-30 of resolve.py lies outside the pinned body (the
# pointer arm pins L36-110), so (d) still proves exactly what it proved in V5: a resumed
# cell whose round counter reads 24/24 buys no further fetch and sends no follow-up.
UNPINNED_TURN = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                 '"start_line": 1, "end_line": 30}')


class _Cfg:
    def __init__(self, tools=""):
        self.tools = tools
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model-was-never-called"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = 0
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = os.path.join(LONGRUN, "manifests")


def _no_network():
    def _denied(*_a, **_k):
        raise AssertionError("the tool channel must never open a socket")
    return _denied


def _messages():
    return [{"role": "system", "content": "offline"}, {"role": "user", "content": "Q"}]


def _fake_fixture():
    return {"task_id": "LR-01", "_sha256": "offline", "bytes_per_token": 4.0,
            "checkpoints": [], "N": 1, "items": [], "turns": [{"turn": 1, "question": "q"}]}


def _resp(text):
    return {"content": text, "content_raw": text, "reasoning": "", "content_source": "content",
            "finish_reason": "stop", "truncated": False, "max_tokens": 256,
            "prompt_tokens": 10, "raw_cached": None, "token_source": "offline",
            "completion_tokens": 5, "ttft_s": 0.1, "ttft_ms": 100, "latency_s": 0.2,
            "usage_missing": False}


def _open_tripwire():
    """Swap builtins.open for a recorder that raises; returns (reads, restore)."""
    reads = []
    saved = builtins.open

    def _tripwire(*a, **k):
        reads.append(a)
        raise AssertionError(f"a refused path must never be read: {a!r}")

    builtins.open = _tripwire
    return reads, lambda: setattr(builtins, "open", saved)


# ------------------------------------------------------------------------ (a)
def assertion_a_engine_base():
    target, reason, base = R.resolve_read_path_base(RESOLVE_REL, WORKSPACE, ENGINE_ROOT)
    assert reason is None, reason
    assert base == "engine", base
    assert target == os.path.realpath(REAL_RESOLVE), target
    # the defect: the workspace root alone cannot see it, which is why 54 calls failed
    assert R.resolve_read_path_base(RESOLVE_REL, WORKSPACE) == (None, "path_not_found", None)
    res = R.execute_tool_call(
        {"path": RESOLVE_REL, "start_line": 66, "end_line": 71}, WORKSPACE, ENGINE_ROOT)
    rec, block = res["record"], res["block"]
    assert rec["executed"] is True and rec["base"] == "engine", rec
    assert rec["start_line"] == 66 and rec["end_line"] == 71, rec
    assert 'base="engine"' in block and 'lines="66-71"' in block, block[:160]
    expected = open(REAL_RESOLVE, encoding="utf-8").readlines()[65:71]
    for line in expected:
        assert line.rstrip("\n") in block, line
    assert "def _refuse(" in block and "ledger.record_refusal(" in block, block
    print(f"  (a) engine base: {RESOLVE_REL} -> {target} base={rec['base']} "
          f"lines=66-71 executed={rec['executed']} first_line="
          f"{res['text'].splitlines()[0][:52]!r}")
    return res


# ------------------------------------------------------------------------ (b)
def assertion_b_unsafe_refused():
    results = []
    for path in ("../../etc/passwd", "/etc/passwd"):
        for engine in (None, ENGINE_ROOT):
            assert R.resolve_read_path(path, WORKSPACE, engine) == (None, "path_refused"), \
                (path, engine, R.resolve_read_path(path, WORKSPACE, engine))
            reads, restore = _open_tripwire()
            try:
                res = R.execute_tool_call(
                    {"path": path, "start_line": 1, "end_line": 3}, WORKSPACE, engine)
            finally:
                restore()
            assert res["record"]["executed"] is False, res["record"]
            assert res["record"].get("error") == "path_refused", res["record"]
            assert res["block"] == '<tool_result error="path_refused"/>', res["block"]
            assert res["text"] == "", res["text"]
            assert reads == [], reads
            results.append(f"{path}@{'engine' if engine else 'workspace'}={res['record']['error']}"
                           f"/reads={len(reads)}")
    # a secret-shaped basename is refused from the engine base too (no read, no stat)
    secret = "ptr_engine/.en" + "v"
    assert R.resolve_read_path(secret, WORKSPACE, ENGINE_ROOT) == (None, "path_refused")
    print(f"  (b) unsafe refused with 0 reads from both bases: {' '.join(results)}; "
          f"secret_shaped=path_refused")
    return results


# ------------------------------------------------------------------------ (c)
def assertion_c_duplicate_billed_once():
    calls = R.parse_tool_calls(DUPLICATED_TURN)
    assert len(calls) == 2, calls
    batch, overflow = R.limit_calls(calls)
    assert len(batch) == 2 and overflow == [], (batch, overflow)
    sent_box = {"n": 1}

    def fake_send_chat(cfg, messages):
        sent_box["n"] += 1
        return _resp("ANSWER: 42")

    served: dict = {}
    real = R.send_chat
    R.send_chat = fake_send_chat
    try:
        cfg = _Cfg(tools="read_file")
        _m, _r, sent1, rounds1, turn_calls, followups = R.fetch_rounds(
            cfg, _fake_fixture(), "pointer-stable", 1, "offline", 3, "sha", {},
            _messages(), {"content": DUPLICATED_TURN}, 1,
            1 + R.TOOL_FETCH_ROUNDS_PER_ARM, 0, served)
        # same turn content again on a LATER turn: the content is already in the
        # conversation, so it is served cached and no follow-up request is bought.
        _m2, _r2, sent2, rounds2, calls2, followups2 = R.fetch_rounds(
            cfg, _fake_fixture(), "pointer-stable", 1, "offline", 4, "sha", {},
            _messages(), {"content": DUPLICATED_TURN}, sent1, 1 + R.TOOL_FETCH_ROUNDS_PER_ARM,
            rounds1, served)
    finally:
        R.send_chat = real
    calls_billed = sent1 - 1
    executed = [c for c in turn_calls if c.get("executed") and not c.get("cached")]
    cached = [c for c in turn_calls if c.get("cached")]
    assert calls_billed == 1, calls_billed
    assert len(executed) == 1 and len(cached) == 1, turn_calls
    assert executed[0]["base"] == "engine", executed[0]
    assert cached[0].get("cache_scope") == "turn", cached[0]
    assert rounds1 == 1 and len(followups) == 1, (rounds1, len(followups))
    # the duplicate is served as the SAME body with cached="true" in the opening tag
    fresh = R.execute_tool_call(calls[0], WORKSPACE, ENGINE_ROOT)
    dupe = R._cached_result(fresh, "turn")
    assert dupe["text"] == fresh["text"] and dupe["record"]["cached"] is True
    assert 'cached="true"' in dupe["block"].split(">")[0], dupe["block"][:160]
    # across turns: no request, no round, every call marked cached
    assert sent2 == sent1 and rounds2 == rounds1, (sent1, sent2, rounds1, rounds2)
    assert followups2 == [], followups2
    assert calls2 and all(c.get("cached") for c in calls2), calls2
    assert all(c.get("cache_scope") == "conversation" for c in calls2), calls2
    print(f"  (c) duplicate billing: calls_parsed=2 executed={len(executed)} cached={len(cached)} "
          f"calls_billed={calls_billed} followup_requests={len(followups)} "
          f"cached_dupe_block_opening={dupe['block'].split('>')[0][:78]!r}; "
          f"next_turn identical call: requests+{sent2 - sent1} rounds+{rounds2 - rounds1} "
          f"cached={len(calls2)}")
    return calls_billed


# ------------------------------------------------------------------------ (d)
def assertion_d_resume_counter():
    tmp = tempfile.mkdtemp(prefix="v4tools2-resume-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    manifest_path = os.path.join(tmp, "v4tools2-manifest.json")
    fixture = R.load_fixture(FIXTURE2)
    arm, rep, run_id = "pointer-stable", 1, "offline-resume"
    cfg = _Cfg(tools="read_file")
    cfg.max_turns = 2
    cfg.resume = True
    cfg.manifest_path = manifest_path
    cfg.manifest_dir = tmp
    doc = R.build_manifest(cfg, fixture, arm, rep, run_id, rows_path)
    data, msha = R.write_manifest(manifest_path, doc)
    frozen = json.loads(open(manifest_path, encoding="utf-8").read())["tools"]["fetch_rounds_used"]
    # 24 follow-up rows already spent in this cell, all on the turn already recorded
    rows = [{"run_id": run_id, "task_id": fixture["task_id"], "arm": arm, "rep": rep,
             "turn": 1, "kind": "tool-followup", "fetch_followup": True, "content": "x",
             "run_manifest_sha256": msha} for _ in range(R.TOOL_FETCH_ROUNDS_PER_ARM)]
    with open(rows_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
    derived = R.fetch_rounds_spent(rows)
    assert derived == R.TOOL_FETCH_ROUNDS_PER_ARM == 24, derived
    assert max(frozen, derived) == 24, (frozen, derived)
    sent_box = {"n": 0}

    def fake_send_chat(cfg, messages):
        sent_box["n"] += 1
        return _resp(UNPINNED_TURN)

    buf, old_stdout = io.StringIO(), sys.stdout
    real = R.send_chat
    R.send_chat = fake_send_chat
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, arm, rep, run_id, rows_path)
    finally:
        R.send_chat = real
        sys.stdout = old_stdout
    out = buf.getvalue()
    assert rc == 0, (rc, out[-400:])
    assert "fetch rounds already spent=24/24" in out, out[-600:]
    assert "derived_from_rows=24" in out, out[-600:]
    assert sent_box["n"] == 1, sent_box  # only the T2 turn request; the fetch bought nothing
    written = [json.loads(line) for line in open(rows_path, encoding="utf-8")]
    t2 = [r for r in written if r.get("turn") == 2 and r.get("kind") == "turn"]
    assert len(t2) == 1, [r.get("kind") for r in written]
    assert t2[0]["fetch_rounds_used"] == 24, t2[0]["fetch_rounds_used"]
    errs = [c.get("error") for c in t2[0]["tool_calls"]]
    assert errs == ["fetch_budget_exhausted"], errs
    assert not any(r.get("fetch_followup") for r in written if r.get("turn") == 2)
    print(f"  (d) resume counter: manifest_counter={frozen} derived_from_rows={derived} "
          f"-> used={max(frozen, derived)}/24; T2 tool_calls error={errs[0]} "
          f"followup_requests_after_resume=0 requests_sent={sent_box['n']} "
          f"row_fetch_rounds_used={t2[0]['fetch_rounds_used']}")
    return derived


# ------------------------------------------------------------------------ (e)
def assertion_e_tools_off_identical():
    assert os.path.exists(BASELINE), f"pre-fix baseline missing: {BASELINE}"
    raw, filtered = {}, {}
    for tag, script in (("before", BASELINE),
                        ("after", os.path.join(LONGRUN, "run_longrun.py"))):
        mp = os.path.join(LONGRUN, "manifests", f"v4tools2-proof-off-{tag}.json")
        proc = subprocess.run(
            [sys.executable, script, "--fixture", FIXTURE_OFF, "--arms", "pointer-stable",
             "--dry-run", "--manifest-path", mp],
            cwd=WORKSPACE, capture_output=True, text=True)
        assert proc.returncode == 0, (tag, proc.returncode, proc.stderr[-500:])
        raw[tag] = hashlib.sha256(proc.stdout.encode()).hexdigest()
        # the only volatile line is the manifest header: it embeds created_utc, so its
        # sha256 changes every run by construction.  Everything else must match.
        kept = [ln for ln in proc.stdout.splitlines() if not ln.startswith("manifest[")]
        filtered[tag] = hashlib.sha256("\n".join(kept).encode()).hexdigest()
        assert "fetch_rounds_cap" not in proc.stdout, "tools-off run must print no tool line"
    assert filtered["before"] == filtered["after"], (filtered, "tools-off output drifted")
    print(f"  (e) --tools off byte-identical: stdout_sha before={raw['before'][:16]} "
          f"after={raw['after'][:16]} (differ only in the manifest line); "
          f"filtered_stdout_sha={filtered['after']} equal=True")
    return filtered["after"]


def main() -> int:
    assert os.path.realpath(os.getcwd()) == os.path.realpath(WORKSPACE), \
        f"run this from the workspace root, not {os.getcwd()}"
    assert not any(m in sys.modules for m in ("requests", "httpx", "urllib3")), \
        "the offline proof must not pull in an HTTP client"
    real_socket = socket.socket
    socket.socket = _no_network()
    send_calls = {"n": 0}
    real_send = R.send_chat

    def _counted(*_a, **_k):
        send_calls["n"] += 1
        raise AssertionError("no model request may be sent by the offline proof")

    R.send_chat = _counted
    try:
        print("FETCH-CHANNEL-FIX offline proof (no model, no network)")
        print(f"  workspace_root={WORKSPACE}  engine_root={ENGINE_ROOT}")
        assertion_a_engine_base()
        assertion_b_unsafe_refused()
        assertion_c_duplicate_billed_once()
        assertion_d_resume_counter()
        assertion_e_tools_off_identical()
        assert send_calls["n"] == 0, send_calls
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
    print("PASS: 5/5 assertions; send_chat calls in the offline proof = 0; "
          "no HTTP client imported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
