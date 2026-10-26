"""Offline proof for PROBE-CP3-V6: the no-bill rule (a) and the per-turn cap (b).

Run from the workspace root:
  python3 experiments/ptr-engine/longrun/tests/test_tool_channel3.py

Exit 0 = every assertion below held, and every RED case failed for the intended reason.

WHY THIS TEST EXISTS.  PROBE-CP3-V5 measured that the T46 checkpoint read of
`ptr_engine/resolve.py` L66-71 was refused host-side (`fetch_budget_exhausted`) because the
24-round per-arm fetch budget was spent by turn 3.  Two bounded changes fix the cause:

  (a) DO NOT BILL A RANGE THE PROMPT ALREADY CARRIES.  A call wholly inside a body the
      planner pinned for that turn is served from the pinned body:
      `served_from="prompt"`, no disk read, NO ROUND BILLED.
  (b) AT MOST 3 FETCH ROUNDS PER TURN, so one recon burst cannot spend the cell.

Both are proven RED-BEFORE-GREEN in this file: each scenario is executed twice — once with
the rule disabled, where the green assertion MUST fail, and once enabled, where it MUST
hold.  A test that only passes after the fix would not prove the fix does anything.

Zero requests, no network: send_chat is a canned function for the whole run and
socket.socket raises.
"""

import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
T46 = 46
T46_CALL = {"path": "ptr_engine/resolve.py", "start_line": 66, "end_line": 71}


class _Cfg:
    def __init__(self, tools="read_file", per_turn=None):
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
        if per_turn is not None:
            self.fetch_rounds_per_turn = per_turn


def _no_network():
    def _denied(*_a, **_k):
        raise AssertionError("the tool channel must never open a socket")
    socket.socket = _denied


def _resp(text):
    return {"content": text, "content_raw": text, "reasoning": "", "content_source": "content",
            "finish_reason": "stop", "truncated": False, "max_tokens": 256,
            "prompt_tokens": 10, "raw_cached": None, "token_source": "offline",
            "completion_tokens": 5, "ttft_s": 0.1, "ttft_ms": 100, "latency_s": 0.2,
            "usage_missing": False}


def _call_block(path, start, end):
    return f'<tool_call>read_file {{"path": "{path}", "start_line": {start}, "end_line": {end}}}'


def _t46_prompt(fixture):
    """The real T46 prompt, built offline by the real planner (no request)."""
    planner = R.Planner("pointer-stable", fixture, dry_run=True)
    return planner.build(T46)["prompt"]


def _run(cfg, fixture, prompt, first, script, rounds_used=0, per_turn_cap=None,
         may_request=None, served=None):
    """One fetch phase with a canned model: `first` is the turn's own reply, then `script`."""
    replies = list(script)
    seen = []

    def fake_send(_cfg, messages):
        seen.append(messages)
        return _resp(replies.pop(0) if replies else "")

    saved = R.send_chat
    R.send_chat = fake_send
    try:
        out = R.fetch_rounds(
            cfg, fixture, "pointer-stable", 1, "v6-offline", T46, "manifest-sha", {},
            [{"role": "system", "content": "offline"},
             {"role": "user", "content": prompt}],
            _resp(first), len(seen), 100, rounds_used, served if served is not None else {},
            R.pinned_views(fixture, prompt), per_turn_cap, may_request)
    finally:
        R.send_chat = saved
    return out, len(seen)


# ------------------------------------------------------------------------ (a)
def _green_a(result):
    """The (a) assertion set: a pinned-range fetch is served from the prompt, billed 0."""
    _m, _resp_, _sent, rounds_used, calls, followups = result
    assert rounds_used == 0, f"a prompt-served fetch must bill no round, got {rounds_used}"
    assert calls, "the call must still be recorded"
    rec = calls[0]
    assert rec.get("served_from") == "prompt", rec
    assert rec.get("billed") is False, rec
    assert rec.get("base") == "prompt", rec
    assert rec.get("executed") is False, "served from the prompt must not touch the disk"
    assert rec.get("lines_returned") == 6, rec
    assert len(followups) == 1, "the served lines still ride exactly one follow-up request"
    assert followups[0]["billed_round"] is False, followups[0]["billed_round"]
    assert followups[0]["prompt_served"] == 1, followups[0]["prompt_served"]
    assert followups[0]["fetch_rounds_cap_per_turn"] == R.TOOL_FETCH_ROUNDS_PER_TURN
    return rec, followups[0]


def check_a(red_green):
    fixture = R.load_fixture(FIXTURE)
    prompt = _t46_prompt(fixture)
    pinned = R.pinned_views(fixture, prompt)
    assert pinned, "the pointer arm pins the item bodies; pinned_views saw none"
    view = R.find_pinned_view(pinned, T46_CALL)
    assert view is not None, "resolve.py 66-71 must lie inside the pinned body"
    cfg = _Cfg()

    saved = R.TOOL_SERVE_FROM_PROMPT
    try:
        R.TOOL_SERVE_FROM_PROMPT = True
        green, nreq = _run(cfg, fixture, prompt, _call_block(T46_CALL["path"], T46_CALL["start_line"], T46_CALL["end_line"]),
                           ["ANSWER: ledger.record_refusal(...)"])
        rec, frow = _green_a(green)
        print(f"  (a) GREEN: served_from={rec['served_from']} billed={rec['billed']} "
              f"rounds_used={green[3]} followup_requests={nreq} "
              f"billed_round={frow['billed_round']}")
        served_block = R.serve_from_prompt(view, T46_CALL)["block"]
        assert "def _refuse" in served_block and "ledger.record_refusal" in served_block, \
            served_block[:200]
        assert 'base="prompt"' in served_block and 'served_from="prompt"' in served_block
        print(f"      block: {served_block.splitlines()[0]}")
        print(f"      line 2: {served_block.splitlines()[1][:80]}")
        red_green.append(("a", "green", True))

        R.TOOL_SERVE_FROM_PROMPT = False
        red, nreq_red = _run(cfg, fixture, prompt, _call_block(T46_CALL["path"], T46_CALL["start_line"], T46_CALL["end_line"]),
                             ["ANSWER: ledger.record_refusal(...)"])
        rec_red = red[4][0]
        assert rec_red.get("executed") is True, rec_red
        assert "served_from" not in rec_red, rec_red
        assert red[3] == 1, f"with the rule disabled the same fetch bills a round, got {red[3]}"
        print(f"  (a) RED (rule disabled): executed={rec_red.get('executed')} "
              f"base={rec_red.get('base')} rounds_used={red[3]} (the round T46 cannot spare)")
        failed = _must_fail(_green_a, red)
        red_green.append(("a", "red", failed))
        print(f"      green assertion on the red path -> AssertionError: {failed}")
    finally:
        R.TOOL_SERVE_FROM_PROMPT = saved


# ------------------------------------------------------------------------ (b)
UNPINNED = [(160, 200), (200, 260), (260, 320), (320, 380), (380, 440)]


def _green_b(result, cap):
    _m, _resp_, _sent, rounds_used, calls, followups = result
    assert rounds_used <= cap, f"at most {cap} rounds may be billed in one turn, got {rounds_used}"
    assert len(followups) <= cap, f"{len(followups)} follow-ups bought, cap is {cap}"
    refused = [c for c in calls if c.get("error") == "per_turn_round_cap"]
    assert refused, f"the calls past the cap must be refused host-side: {calls}"
    for c in refused:
        assert c.get("billed") is False, c
    return rounds_used, len(refused)


def check_b(red_green):
    fixture = R.load_fixture(FIXTURE)
    prompt = _t46_prompt(fixture)
    cfg = _Cfg(per_turn=R.TOOL_FETCH_ROUNDS_PER_TURN)
    script = [_call_block("ptr_engine/resolve.py", s, e) for s, e in UNPINNED]
    first = _call_block("ptr_engine/resolve.py", *UNPINNED[0])
    res, nreq = _run(cfg, fixture, prompt, first, script[1:],
                     per_turn_cap=R.TOOL_FETCH_ROUNDS_PER_TURN)
    used, refused = _green_b(res, R.TOOL_FETCH_ROUNDS_PER_TURN)
    print(f"  (b) GREEN: cap={R.TOOL_FETCH_ROUNDS_PER_TURN}/turn billed={used} "
          f"refused={refused} followup_requests={nreq}")
    red_green.append(("b", "green", True))

    # RED: the pre-V6 behaviour (no per-turn cap) buys every round a burst asks for.
    res_red, nreq_red = _run(cfg, fixture, prompt, first, script[1:], per_turn_cap=0)
    print(f"  (b) RED (cap disabled): billed={res_red[3]} followup_requests={nreq_red} "
          f"(one burst spends the arm's 24-round budget)")
    failed = _must_fail(lambda r: _green_b(r, R.TOOL_FETCH_ROUNDS_PER_TURN), res_red)
    red_green.append(("b", "red", failed))
    print(f"      green assertion on the red path -> AssertionError: {failed}")


# ------------------------------------------------------------------ (c) tools off
def check_c(red_green):
    fixture = R.load_fixture(FIXTURE)
    cfg = _Cfg(tools="")
    before = R.tools_enabled(cfg)
    out, nreq = _run(cfg, fixture, "offline prompt",
                     '<tool_call>read_file {"path": "ptr_engine/resolve.py"}', [],
                     per_turn_cap=R.TOOL_FETCH_ROUNDS_PER_TURN)
    assert before is False
    assert out[0] is not None and out[2] == 0 and out[3] == 0, out[2:4]
    assert out[4] == [] and out[5] == [], "with --tools off the channel must record nothing"
    assert nreq == 0, "with --tools off no request may be sent"
    print(f"  (c) tools OFF: no call parsed, no round, no follow-up request (requests={nreq})")
    red_green.append(("c", "inert", True))


def _must_fail(fn, arg):
    try:
        fn(arg)
    except AssertionError as exc:
        return str(exc) or "assertion failed"
    raise SystemExit("RED CASE DID NOT FAIL: the guard it is supposed to prove is absent")


def main():
    _no_network()
    print("PROBE-CP3-V6 offline proof — (a) no-bill pinned serve, (b) 3 rounds per turn")
    print(f"  fixture={os.path.relpath(FIXTURE, WORKSPACE)} T{T46} "
          f"call={T46_CALL['path']} L{T46_CALL['start_line']}-{T46_CALL['end_line']}")
    red_green = []
    check_a(red_green)
    check_b(red_green)
    check_c(red_green)
    green = [x for x in red_green if x[1] == "green"]
    red = [x for x in red_green if x[1] == "red"]
    assert len(green) == 2 and len(red) == 2, red_green
    print(f"PASS: {len(red_green)} checks; {len(green)} green assertions held and "
          f"{len(red)} red cases failed as required; send_chat was canned (0 real requests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
