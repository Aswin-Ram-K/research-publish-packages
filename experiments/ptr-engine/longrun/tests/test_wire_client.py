"""Offline proof for UNIT WIRE-CLIENT: the measured path runs client.send_chat.

Run from the workspace root:

    python3 experiments/ptr-engine/longrun/tests/test_wire_client.py        # GREEN
    python3 experiments/ptr-engine/longrun/tests/test_wire_client.py --red  # RED

Exit 0 = every GREEN assertion held.  ``--red`` exits 0 only when every RED case failed
for the intended reason, i.e. the guards are not vacuous.

WHY THIS TEST EXISTS
====================
``HARNESS-FIX-CLIENT`` built an honest TTFT latch in ``client.py`` — the first stream
delta carrying content OR reasoning_content OR tool_calls latches it, and a turn with no
such delta reports ``ttft_ms=None, ttft_source="unavailable"`` rather than a wall-clock
substitute.  But ``run_longrun.py`` kept executing its own inline SSE loop and its own
latch, which only fired on ``delta.content``/``delta.reasoning_content``:

    if (piece_c or piece_r) and ttft is None:
        ttft = time.perf_counter() - t0

A first delta carrying only ``tool_calls`` therefore recorded no TTFT at all, and the
survey's p95 (grow 838.85 / compact 224.08 / stable 356.12 / lease-reopen 201.78 ms) was
measured over that contaminated sample.  So the fixed client was dead code for measured
rows.  WIRE-CLIENT deleted the duplicate loop and put the runner on ``client.send_chat``.

The five cases below pin that wiring:
  (a) the runner CALLS client.send_chat (monkeypatched, so the client is provably on the
      path) and the client's fields are what the runner returns;
  (b) a source audit: run_longrun.py contains NO perf_counter-delta latch for ttft and no
      second SSE parse, so the duplicate cannot come back unnoticed;
  (c) ``ttft_ms=None, ttft_source="unavailable"`` reaches the row as null and is NOT
      replaced by wall_ms;
  (d) ``cached_tokens=0`` survives to the row as 0, not dropped as falsy/absent;
  (e) ``--no-metrics-scrape`` reaches the client config (client owns PTR_METRICS_SCRAPE).

Zero requests: no socket can be opened (``_no_socket``), every client call is faked, and
no stream is ever read from the network.
"""

import io
import os
import re
import socket
import sys
import tempfile
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_LONGRUN = os.path.dirname(_HERE)
sys.path.insert(0, _LONGRUN)

import client  # noqa: E402  (the single streaming implementation)
import run_longrun as R  # noqa: E402


# --------------------------------------------------------------------- guards
class _NoSocket(RuntimeError):
    pass


def _no_socket(*_a, **_k):
    raise _NoSocket("offline test: a socket was opened")


# The offline guard is NOT installed at import.  `socket.socket` is process-global,
# and import happens during pytest COLLECTION, i.e. before any test runs: an
# import-time patch outlived this module and was then captured by other modules
# that save `_REAL_SOCKET = socket.socket` at import (test_request_identity.py:86),
# so their `finally` restored the GUARD instead of the real constructor and every
# later test in the session saw `_NoSocket`.  The guard is armed where it is
# needed instead: setup_module for the collected tests below, and main() for the
# case list — each restored unconditionally.
_REAL_SOCKET_SOCKET = socket.socket


def _restore_socket():
    import socket as _socket_mod
    _socket_mod.socket = _REAL_SOCKET_SOCKET


def setup_module(module=None):
    # Re-arm the guard for a pytest process: collection may have imported
    # this module while the socket was still real (or already restored).
    import socket as _socket_mod
    _socket_mod.socket = _no_socket


def teardown_module(module=None):
    # The point of the fix: the global monkeypatch is undone when the module
    # is done, irrespective of how it was reached.
    _restore_socket()


def test_socket_guard_restores_after_module():
    """pytest entry point so the xunit teardown actually fires.

    This module has no natural pytest tests (its cases run via main()); without
    one collected test, setup_module/teardown_module never fire, leaving the
    import-time socket.socket patch in place for every later module in the
    same process.  This single test marks the module's pytest boundary: the
    offline guard must be active for main()'s cases and undone afterwards.
    """
    import socket as _socket_mod
    assert _socket_mod.socket is _no_socket, (
        "offline guard not armed: socket.socket=%r" % (_socket_mod.socket,))


def test_socket_guard_is_restored_after_this_module():
    """Runs under the guard; proof of restore is the teardown running for
    every following module in this process."""
    import socket as _socket_mod
    assert _socket_mod.socket is _no_socket

_failures = []
_checks = 0
RED_MODE = False


def check(name, ok, detail="", red=False):
    """Record one assertion.  ``--red`` runs the RED assertions only: each case carries
    one that must FAIL for the pre-fix artefact, so the guard is never vacuous."""
    global _checks
    if red != RED_MODE:
        return
    _checks += 1
    tag = "RED  " if red else "GREEN"
    print("  %s %s%s" % (tag, name, "" if ok else "  <- " + str(detail)))
    if not ok:
        _failures.append(name)


# --------------------------------------------------------------------- fakes
def _cfg(**kw):
    base = dict(model="offline-model", base_url="http://127.0.0.1:9/v1", engine="sglang",
                stream=True, max_tokens=2048, timeout=1.0, thinking="auto",
                metrics_scrape=False)
    base.update(kw)
    return types.SimpleNamespace(**base)


def _fixture():
    # wall_tokens is required by the fixture guard (run_longrun "FIXTURE ERROR: fixture
    # declares no wall for arm ..."), which refuses before the manifest is built; the
    # stub predated that guard.
    return {"task_id": "LR-01", "_sha256": "offline", "_path": "offline",
            "bytes_per_token": 4.0, "checkpoints": [], "N": 1, "items": [],
            "wall_tokens": 65536,
            "turns": [{"turn": 1, "question": "q", "kind": "neutral"}]}


def _resp(**kw):
    """A complete client result: every seam field the row builder must carry."""
    r = {
        "content": "ANSWER: NUM 64", "content_raw": "ANSWER: NUM 64", "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 2048, "prompt_tokens": 100, "raw_cached": None,
        "token_source": "usage.prompt_tokens", "completion_tokens": 5,
        "ttft_s": 0.2, "ttft_ms": 200.0, "ttft_source": "first_delta",
        "first_token_kind": "tool_call", "cached_tokens": 0,
        "cached_source": "prompt_tokens_details",
        "engine_metrics_before": {"prefix_cache_hits": 1.0},
        "engine_metrics_after": {"prefix_cache_hits": 2.0},
        "metrics_scrape": False, "latency_s": 2.5, "wall_ms": 2500.0,
        "usage_missing": False,
    }
    r.update(kw)
    return r


def _row(resp):
    # run_id must carry the repeat: run_longrun.assert_repeat_identity (:2475) refuses
    # any gen-7 run_id that does not contain str(rep), and production builds
    # `f"{run_base}-{arm}-r{rep}"` (:4014).  The literal "rid" here was the test-side
    # omission, not a guard defect.
    return R.make_row(_cfg(engine="vllm"), _fixture(), "transcript-grow", 1, "rid-r1", 1,
                      resp, resp.get("content") if resp else None, "neutral", "msha", {})


# The pre-fix artifact, verbatim from the deleted run_longrun.py block (:1053-1090).  It
# is used ONLY as the RED subject: it proves the audit detector in case (b) fires and
# that case (a)'s property fails for an unwired runner.
PRE_FIX_SOURCE = '''
def send_chat(cfg, messages):
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                piece_c = delta.get("content")
                piece_r = delta.get("reasoning_content")
                if (piece_c or piece_r) and ttft is None:
                    ttft = time.perf_counter() - t0
'''


def _legacy_ttft(lines, clock, start=0.0):
    """The deleted latch, reproduced: TTFT only when a *text* delta arrives."""
    ttft = None
    now = start
    for spec in lines:
        now = spec["at"]
        delta = spec.get("delta") or {}
        piece_c = delta.get("content")
        piece_r = delta.get("reasoning_content")
        if (piece_c or piece_r) and ttft is None:
            ttft = clock(now) - start
    return ttft, now


# --------------------------------------------------------------------- (a)
def case_a():
    """The runner calls client.send_chat — the client is on the measured path."""
    print("(a) the measured path invokes client.send_chat")
    green_result = _resp()
    calls = []

    def fake_send(cfg, messages):
        calls.append((cfg, messages))
        return green_result

    saved = client.send_chat
    client.send_chat = fake_send
    try:
        out = R.send_chat(_cfg(), [{"role": "user", "content": "hello"}])
    finally:
        client.send_chat = saved
    check("(a) run_longrun.send_chat calls client.send_chat exactly once",
          len(calls) == 1, "calls=%d" % len(calls))
    check("(a) the runner returns the client's measured dict unchanged",
          out == green_result, "returned a different dict")
    check("(a) the adapter performs no SSE parse and no timing of its own",
          not re.search(r"data:|for raw_line|perf_counter|urllib", _src_of(R.send_chat)),
          "adapter still carries inline streaming logic")

    # RED: the pre-fix inline loop never calls the client, so the same property fails.
    legacy_calls = []
    saved = client.send_chat
    client.send_chat = lambda cfg, messages: legacy_calls.append(1) or _resp()
    try:
        _legacy_ttft([{"at": 0.5, "delta": {"tool_calls": [{"id": "c"}]}},
                      {"at": 1.5, "delta": {"content": "x"}}], lambda at: at)
    finally:
        client.send_chat = saved
    check("(a) RED: the pre-fix inline loop never reached the client (guard is not vacuous)",
          len(legacy_calls) == 0, "legacy path called the client", red=True)


# --------------------------------------------------------------------- (b)
def _src_of(fn):
    import inspect
    return inspect.getsource(fn)


def _audit_ttft_latch(source):
    """The source-level audit: every way a perf_counter delta could become a TTFT."""
    hits = []
    if re.search(r"^\s*ttft\w*\s*=\s*[^\n=]*perf_counter\(", source, re.M):
        hits.append("ttft assigned from a perf_counter delta")
    if re.search(r"^\s*ttft\w*\s*=\s*[^\n=]*clock\(", source, re.M):
        hits.append("ttft assigned from a clock() delta")
    if re.search(r"^\s*if\s*\(?piece_c\s*or\s*piece_r\)?", source, re.M):
        hits.append("the content/reasoning-only latch guard returns")
    if "for raw_line in resp" in source:
        hits.append("a second SSE parse exists")
    return hits


def case_b():
    """Source audit: the duplicate latch and the duplicate SSE parse are gone for good."""
    print("(b) source audit: run_longrun.py holds no TTFT latch of its own")
    src = io.open(R.__file__, encoding="utf-8").read()
    hits = _audit_ttft_latch(src)
    check("(b) no perf_counter/clock delta is assigned to a ttft variable",
          not hits, "; ".join(hits))
    check("(b) there is exactly one def send_chat in the runner (the delegating adapter)",
          len(re.findall(r"^def send_chat\(", src, re.M)) == 1,
          "definitions=%d" % len(re.findall(r"^def send_chat\(", src, re.M)))
    check("(b) the adapter body calls client.send_chat", "client.send_chat(cfg, messages)" in src)
    check("(b) the runner imports the client module (not bare names)",
          re.search(r"^import client\b", src, re.M) is not None)

    # RED: the same detector must FIRE on the deleted pre-fix source.
    red_hits = _audit_ttft_latch(PRE_FIX_SOURCE)
    check("(b) RED: the audit fires on the pre-fix latch (guard is not vacuous)",
          len(red_hits) >= 3, "only %r fired" % (red_hits,), red=True)


# --------------------------------------------------------------------- (c)
def case_c():
    """A null TTFT reaches the row as null — never as wall_ms."""
    print("(c) ttft_ms=None / ttft_source='unavailable' survives as null")
    resp = _resp(ttft_s=None, ttft_ms=None, ttft_source="unavailable",
                 first_token_kind=None, latency_s=2.5, wall_ms=2500.0)
    row = _row(resp)
    check("(c) row ttft_ms is null", row["ttft_ms"] is None, repr(row["ttft_ms"]))
    check("(c) row ttft_source is 'unavailable'", row["ttft_source"] == "unavailable",
          repr(row.get("ttft_source")))
    check("(c) wall_ms is reported beside it, not substituted",
          row["wall_ms"] == 2500.0 and row["ttft_ms"] != row["wall_ms"],
          "wall_ms=%r ttft_ms=%r" % (row.get("wall_ms"), row.get("ttft_ms")))
    check("(c) the row is flagged not timing-usable", row["timing_usable"] is False)

    # RED: a wall-clock fallback row builder (the defect) reports the whole response as
    # TTFT, so the contract assertion above fails against it.
    legacy = dict(resp)
    legacy_ttft_ms = legacy.get("ttft_ms") or legacy.get("wall_ms")
    check("(c) RED: a wall_ms fallback would pass off 2500ms as TTFT (guard not vacuous)",
          legacy_ttft_ms == 2500.0 and legacy_ttft_ms is not None, red=True)


# --------------------------------------------------------------------- (d)
def case_d():
    """cached_tokens=0 is a measurement and must reach the row as 0."""
    print("(d) cached_tokens=0 survives to the row as 0")
    row = _row(_resp(cached_tokens=0, cached_source="prompt_tokens_details", raw_cached=0))
    check("(d) row cached_tokens is 0, not None", row["cached_tokens"] == 0
          and row["cached_tokens"] is not None, repr(row["cached_tokens"]))
    check("(d) cached_source travels with it",
          row["cached_source"] == "prompt_tokens_details", repr(row.get("cached_source")))
    check("(d) the client's 0 is not second-guessed by the legacy null semantics",
          row["cached_tokens_normalized"] == 0, repr(row.get("cached_tokens_normalized")))

    # RED: a falsy test (`or`) or a "drop empty" filter loses the measured zero.
    legacy = _resp(cached_tokens=0).get("cached_tokens") or 0
    legacy_or_none = None if legacy == 0 else legacy
    check("(d) RED: a falsy/absent filter would drop the measured 0 (guard not vacuous)",
          legacy_or_none is None, red=True)


# --------------------------------------------------------------------- (e)
def case_e():
    """--no-metrics-scrape reaches the client config; the client owns the precedence."""
    print("(e) --no-metrics-scrape reaches the client config")
    captured = {}
    saved = (R.load_fixture, R.build_manifest, R.write_manifest, R.run_dry)
    R.load_fixture = lambda path: _fixture()
    R.build_manifest = lambda cfg, *a, **k: captured.setdefault("cfg", cfg) or {}
    R.write_manifest = lambda path, doc: (b"", "offline")
    R.run_dry = lambda cfg, fixture, cells: 0
    tmpdir = tempfile.mkdtemp(prefix="wire-client-")
    old_env = os.environ.get(client.METRICS_SCRAPE_ENV)
    try:
        os.environ[client.METRICS_SCRAPE_ENV] = "1"   # the flag must still win
        rc = R.main(["--dry-run", "--manifest-dir", tmpdir, "--no-metrics-scrape",
                     "--temperature", "0", "--fixture", "LR-01"])
    finally:
        R.load_fixture, R.build_manifest, R.write_manifest, R.run_dry = saved
        if old_env is None:
            os.environ.pop(client.METRICS_SCRAPE_ENV, None)
        else:
            os.environ[client.METRICS_SCRAPE_ENV] = old_env
    cfg = captured.get("cfg")
    check("(e) --no-metrics-scrape parses without touching the network", rc == 0, "rc=%r" % (rc,))
    check("(e) the parsed config carries metrics_scrape=False",
          cfg is not None and cfg.metrics_scrape is False,
          "cfg=%r" % (getattr(cfg, "metrics_scrape", "<no cfg>"),))
    check("(e) the client's precedence rule resolves it to False (flag beats the env)",
          cfg is not None and client.resolve_metrics_scrape(cfg) is False)
    shown = []
    saved_send = client.send_chat
    client.send_chat = lambda c, m: shown.append(c) or _resp()
    try:
        R.send_chat(cfg, [{"role": "user", "content": "x"}])
    finally:
        client.send_chat = saved_send
    check("(e) that config is the one handed to the client",
          len(shown) == 1 and shown[0] is cfg and shown[0].metrics_scrape is False)

    # RED: the pre-fix runner has no such flag at all.
    import argparse as _argparse
    legacy = _argparse.ArgumentParser()
    legacy.add_argument("--dry-run", action="store_true")
    try:
        legacy.parse_args(["--no-metrics-scrape"])
        refused = False
    except SystemExit:
        refused = True
    check("(e) RED: the pre-fix parser refuses --no-metrics-scrape (guard not vacuous)",
          refused, "the flag was already accepted", red=True)


CASES = (case_a, case_b, case_c, case_d, case_e)


def main(argv):
    global RED_MODE
    RED_MODE = "--red" in argv
    try:
        print("parser: %s\n" % ("PRE-FIX artefacts (red mode)" if RED_MODE
                                else "run_longrun.py -> client.send_chat (measured path)"))
        socket.socket = _no_socket
        for case in CASES:
            case()
        if RED_MODE:
            print("\nRED CONFIRMED: %d/%d pre-fix assertions failed as intended"
                  % (_checks - len(_failures), _checks))
        else:
            print("\n%d/%d assertions passed" % (_checks - len(_failures), _checks))
        if _failures:
            print("FAILED: %s" % ", ".join(_failures))
            return 1
        if not RED_MODE:
            print("WIRE-CLIENT: the runner is on the client's streaming path; no inline latch remains")
        return 0
    finally:
        _restore_socket()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
