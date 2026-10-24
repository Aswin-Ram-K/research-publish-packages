#!/usr/bin/env python3
"""R2-VLLM -- FIX-INSTRUMENT: prove each of the four harness defects red->green.

Offline only: 0 model requests, no lock, no box, no network.  The REAL ``httpx`` is
never imported here (``selftest_offline`` aliases it to a stand-in before importing the
cell), and every "request" this file issues is refused by an in-process transport
(``127.0.0.1:1``) -- it exercises the row-writing path without a server.

Four defects.  Each names the check that must FAIL on the defective harness and PASS
on the repaired one, and red is taken twice so the proof survives the source moving:

  * ``literal`` -- the historical defective code, carried inline (:data:`LITERALS`).
  * ``source``  -- the repaired cell with this one repair mechanically reverted on a
                   COPY of its text (:func:`source_revert`).  A revert whose anchor
                   no longer exists reports ``matched: false`` -- a drift alarm, never
                   a silent pass.

  D1  launch does not populate ``usage.prompt_tokens_details``: every ``cached_tokens``
      on that config is unobserved yet recorded as 0, and nothing on the row says the
      instrument was blind.                     check: R1_flag_in_oh1_oh1l_a1_unchanged
  D2  ``Runner.send`` neither persists the ``extra`` payload nor accepts the
      ``extra=`` keyword ``phase_battery`` passes.  Live effect: ``PHASE FAILED OH1:
      Runner.send() got an unexpected keyword argument 'extra'`` -- the battery issued
      no row.                                                  check: R8_send_persists_extra
  D3  ``cached=None`` (unobserved) is collapsed to 0, and the ledger, the analyser
      and the usage coverage then sum unobserved as zero.  check: R2_absence_is_none_not_zero
  D4  the per-turn salt of pass 1 is overwritten by the arm salt, so turn N's prompt
      is a superset of turn N-1's: the "cold" pass is contaminated by construction.
                                                                 check: R5_true_cold_pass

Usage:
  .venv/bin/python defects_offline.py            # full, with a 4-turn fake battery
  .venv/bin/python defects_offline.py --draw 0   # source-only red, no request path
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import inspect
import json
import sys
import textwrap
import time
import types
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import selftest_offline as S  # noqa: E402  (installs the no-network httpx stub)

cell = S.cell
REPO = HERE.parents[3]
OUT = REPO / "state" / "logs" / "R2-VLLM-defects.json"

# The historical defective code, as it stood in the harness that produced the rows
# this card is about (``rows.jsonl`` 420-row dry run; ``logs/rerun-console.log``).
LITERALS = {
    "D1": {
        "why": "the OH1/OH1L launch carried no accounting flag and the shared recipe did "
               "not carry it either -- the flag arrived only in the A1 spec",
        "how": "exec the historical module text into a module and run the flag check",
        "subs": [
            ('    "--reasoning-parser", "qwen3", "--trust-remote-code",\n'
             '    # REPAIR A: one legal way only.  The specs below carry this too, and\n'
             '    # build_spec de-duplicates, so the flag appears exactly once either way.\n'
             '    "--enable-prompt-tokens-details",\n]',
             '    "--reasoning-parser", "qwen3", "--trust-remote-code",\n]'),
            # all THREE configs carried the empty list historically (OH1/OH1L/A1)
            ('"extra": ["--enable-prompt-tokens-details"]', '"extra": []', "all"),
        ],
    },
    "D3": {
        "why": "the reader used `(... .get('cached_tokens') or 0)`, so 'details absent' "
               "became a true zero and every downstream sum was fabricated",
        "how": "compile the historical literal as the row reader and run the "
               "'absence is None, not zero' check against it",
        "expr": ("(lambda usage: int((((usage or {}).get('prompt_tokens_details') or {})"
                 ".get('cached_tokens') or 0)))"),
    },
    "D4": {
        "why": "one arm salt was used for every turn, so the pass-1 chain was a "
               "sequential walk and A1 recorded 1056 cached tokens on a rep=0 turn 3",
        "how": "compile the historical per-arm salt expression and run the true-cold check",
        "expr": "cell.make_salt(int(seed))",
    },
}

# How each repair is reverted INSIDE the repaired source (the ``source`` red):
# ``name: ([(old, new), ...], check_name, expect)`` where ``expect`` is the shape of
# the red -- ``"assert"`` for a check that must catch it, ``"type"`` for a crash the
# live run actually died of (a crash is the defect, not a check fault).  ``main``
# reads only the first two elements; the tag is documentation.
REVERTS = {
    "D1": (LITERALS["D1"]["subs"], "R1_flag_in_oh1_oh1l_a1_unchanged", "assert"),
    # BOTH halves of the defect the re-run died of: the dropped keyword AND the
    # dropped payload.  The payload alone is the silent shape (nothing reads the
    # declared policies); together they raise the literal TypeError.
    "D2": ([
        ('             note="", extra: dict | None = None) -> dict:',
         '             note="") -> dict:'),
        ('                        request_index=self.n_rows() + 1, extra=extra)',
         '                        request_index=self.n_rows() + 1, extra=None)'),
    ], "R8_send_persists_extra"),
    "D3": ([
        # the historical `or 0` on the field itself (the "^ historical" anchor); the
        # early return below is the "carry on with the same collapse" form the same
        # defect takes inside today's reader.
        ('    cached = None if raw is None else int(raw)\n',
         '    cached = int(raw or 0)  # REVERTED: absence collapses to a miss\n'),
        # the CLIENT override must go too, or it would launder the collapsed 0 back
        # the CLIENT override must go too, or it would launder the collapsed 0 back
        ('                "cached": None if u["cached"] is None else min(u["cached"], u["prompt_tokens"]),',
         '                "cached": min(u["cached"], u["prompt_tokens"]),'),
    ], "R2_absence_is_none_not_zero", "assert"),
    # the historical scheme: one arm salt for every turn, on BOTH passes.  The seat
    # that decides the RENDERED bytes is ``battery_salt``'s per-turn branch, not the
    # call site -- the prompts come from ``salt_for_turn`` -- so reverting the call
    # site alone is invisible to R5's byte evidence (it is still checked, at R8).
    "D4": ([
        ("    if turn is None:\n        return make_salt(int(seed))\n"
         "    return make_salt(int(seed) * 1000 + int(turn))",
         "    return make_salt(int(seed))  # REVERTED: one salt per arm on pass 1 too"),
    ], "R5_true_cold_pass", "assert"),
}


DEPS = {}
for _name in ("httpx", "fcntl", "subprocess", "shlex", "argparse", "os", "re",
              "datetime", "pathlib", "hashlib", "time", "sys"):
    DEPS.setdefault(_name, sys.modules.get(_name))
DEPS["htm"] = cell.httpx          # whatever alias the repaired module imported


def load_reverted(source: str, name: str, prefer: str):
    """Exec ``source`` and repair the dependency bindings it could not resolve.

    ``selftest_offline`` execs a module FROM SOURCE without registering it in
    ``sys.modules``, so a re-export alias unpacked from a non-package (``selftest``
    does ``from pmu16_cell import *`` -> ``htm``) is unresolvable there, and the
    ``httpx`` the module gets is the no-network stub.  Neither changes the code under
    test, so both are pointed at the repaired module's bindings.
    """
    mod = S.load_cell(source=source, name=name)
    mod.htm = DEPS["htm"]
    return mod


def client_for(module, port: int):
    """A cell ``Client`` built without touching the real ``httpx`` (see the stub).

    The no-network stub replaced ``sys.modules["httpx"]`` at import time, which the
    cell's OWN ``import json`` cannot see -- but ``_offline_client`` temporarily swaps
    the module's ``httpx`` binding, so ``Client.chat_full`` must get a transport, not
    a socket.  The stub also leaks into attribute lookups: nothing here reads it.
    """
    return S._offline_client(module, port)


def source_revert(which: str, source: str) -> tuple[str, list[dict]]:
    """Apply ``REVERTS[which]`` to ``source``; report each anchor's fate."""
    src = source
    matched = []
    for subs in REVERTS[which][0]:
        old, new = subs[0], subs[1]
        every = len(subs) > 2 and subs[2] == "all"
        n = src.count(old)
        matched.append({"anchor": old.strip()[:70], "count": n, "expect": n})
        if (every and n >= 1) or n == 1:
            src = src.replace(old, new) if every else src.replace(old, new, 1)
    return src, matched


# --------------------------------------------------------- fake-transport battery


class _ProbeCrash(RuntimeError):
    """A transport-level crash surfaced through phase_battery's own handler."""


class _FakeStream:
    """SSE body for one injected round; counts as 0 model requests."""

    def __init__(self, body: bytes, status: int):
        self._body, self.status_code = body, status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Transport:
    """Replaces ``httpx.Client.stream``; never opens a socket.

    By default it reports a cache MISS that is OBSERVED (``prompt_tokens_details``
    present with ``cached_tokens`` 0): the only reading that says "the instrument
    worked and the cache truly missed".  ``details=False`` models the launch WITHOUT
    ``--enable-prompt-tokens-details`` -- the blind instrument D1 is about.  ``prompt_tokens`` is derived from the POSTed bytes so the row's
    ``blocks_available`` stays consistent with the prompt actually sent.
    """

    def __init__(self, mode: str = "200", cached: int | None = 0, details: bool = True):
        self.mode, self.calls, self.cached, self.details = mode, 0, cached, details

    def post(self, *a, **kw):                 # /tokenize is absent on this build
        r = _FakeStream(b"{}", 404)
        return r

    def stream(self, method, url, json=None, timeout=None, **kw):
        forced = kw.pop("_force_cached", None)
        self.calls += 1
        if self.mode == "refuse":
            raise ConnectionError("ConnectError(Errno 111 Connection refused)")
        prompt_tokens = prompt_tokens_of(json or {})
        cached = forced if forced is not None else (self.cached or 0)
        usage = {"prompt_tokens": prompt_tokens, "completion_tokens": 1}
        if self.details:
            usage["prompt_tokens_details"] = {"cached_tokens": min(cached, prompt_tokens)}
        j = sys.modules["json"]
        body = ("data: " + j.dumps({"choices": [{"delta": {"content": "ok"}}]}) + "\n"
                + "data: " + j.dumps({"usage": usage}) + "\n"
                + "data: [DONE]\n")
        return _FakeStream(body.encode(), 200)


def prompt_tokens_of(payload: dict) -> int:
    """~4 bytes per token over the POSTed message contents (the cell's own ratio)."""
    msgs = payload.get("messages") or []
    blob = sys.modules["json"].dumps(msgs, sort_keys=True, separators=(",", ":"))
    return max(1, len(blob) // 4)


def _bytes(msgs) -> bytes:
    return b"".join(json.dumps(m, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    for m in msgs)


def _longest_common_prefix(a: bytes, b: bytes) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _sequential_overlap(prompts: list) -> list[int]:
    """Bytes of turn N's prompt that turn N+1's prompt repeats from byte 0.

    This is the rendered-byte, no-server form of "is pass 1 a sequential walk?".
    ``render()`` (``_linear_messages``) puts the salt in the head's first line and
    every body verbatim after it, so under a per-turn salt every prompt diverges from
    every other at the head and the overlap is 0, while under one arm salt turn N+1
    repeats turn N's prompt from byte 0 up to the length of N.
    """
    enc = [_bytes(p) for p in prompts]
    return [_longest_common_prefix(enc[i], enc[i + 1]) for i in range(len(enc) - 1)]


class _PrefixCache:
    """A strict-prefix cache over POSTed bytes: the server's side of the hypothesis.

    ``cached`` is the length (in the same units as ``prompt_tokens_of``) of the
    longest previously-served prompt that is a strict prefix of this one, else 0.
    """

    def __init__(self):
        self.seen: list[bytes] = []

    def key(self, payload: dict) -> bytes:
        msgs = payload.get("messages") or []
        return sys.modules["json"].dumps(msgs, sort_keys=True,
                                         separators=(",", ":")).encode("utf-8")

    def cached_tokens(self, payload: dict) -> int:
        key = self.key(payload)
        best = 0
        for prev in self.seen:
            if len(prev) < len(key) and key[:len(prev)] == prev:
                best = max(best, len(prev))
        return (best // 4) if best else 0

    def note(self, payload: dict):
        self.seen.append(self.key(payload))


class _PrefixCacheTransport(_Transport):
    """A transport whose ``cached_tokens`` is the prefix-cache model's answer."""

    def __init__(self, model: _PrefixCache):
        super().__init__(cached=0, details=True)
        self.model = model

    def stream(self, method, url, json=None, timeout=None, **kw):
        cached = self.model.cached_tokens(json or {})
        self.model.note(json or {})
        # reuse the base body construction with the model's answer
        return _Transport.stream(self, method, url, json=json, timeout=timeout,
                                 _force_cached=cached)

class _CorpusPath:
    """A stand-in for ``corpora/endtoend.json`` that yields ``n`` turns."""

    def __init__(self, turns, preamble):
        self._payload = {"scenarios": [{"preamble": preamble, "turns": turns}]}

    def read_text(self, encoding="utf-8"):
        return json.dumps(self._payload)


def spec_with_id(module, config_id: str = "OH1") -> dict:
    """The built spec WITH ``config_id`` on the top level.

    ``Runner.send`` reads ``self.spec["config_id"]`` (its request cap is per config),
    while ``build_spec`` returns ``config_id`` on the outer ``CONFIGS`` record.  The
    live path never notices -- ``run_config`` merges it -- but a fake Runner built
    straight from ``build_spec(...)["spec"]`` does.  Mirror ``run_config`` here.
    """
    return {**module.build_spec(config_id, *S.fake_inspects())["spec"],
            "config_id": config_id}


def fake_battery(module=cell, turns: int = 4, transport: _Transport | None = None):
    """Run ``module.phase_battery`` over a short corpus and a fake transport.

    Returns ``(rows, error)``.  ``error`` is what the battery raised, if anything --
    on the D2 mutant that is the TypeError the live re-run died of.  The module is
    mutated in place and restored, because ``phase_battery`` reads module globals.
    """
    _assert_phase_battery_home(module)
    preamble, corpus_turns = module.load_turns(module.BATTERY_TURNS)
    ctx = dict(module.__dict__)
    rows: list[dict] = []
    transport = transport or _Transport()
    # a battery costs 2 * ARMS * turns rows: the real cap guards the real rows file,
    # which may already hold a finished run's rows.  The cap has its own check (R9).
    module.ARM_REQUEST_CAP = 10 ** 6
    module.TOTAL_REQUEST_CAP = 10 ** 6

    def _fake_client(port):
        cl = client_for(module, port)
        cl.http = transport
        return cl

    class _FakeRunner(module.Runner):
        def __init__(self, spec, client):
            self.spec, self.client, self.resolved_block, self.requests = spec, client, 2096, 0
            self.client.model = spec["served_model"]

        def n_rows(self):
            return len(rows)

        def append(self, row):
            rows.append(row)

        def battery_rows(self, arm, rep=None):
            return rows

    # phase_battery catches its own exceptions and prints `PHASE FAILED ...`, so on a
    # mutant it would look like a clean "zero rows" run.  A crash raised INSIDE the
    # fake client (the send path under test) escapes into this frame instead: the
    # battery's log line is preserved, and the crash is not swallowed.  Never tripped
    # by the repaired module, which issues no such call.
    def _fake_client(port):     # noqa: F811 - deliberately replaces the plain factory
        cl = client_for(module, port)

        class _Transport:
            def __init__(self):
                self._t = transport
                self.calls = 0

            def stream(self, *a, **kw):
                self.calls += 1
                try:
                    return self._t.stream(*a, **kw)
                except BaseException as exc:      # noqa: BLE001 - report, do not hide
                    raise _ProbeCrash(exc) from exc

        cl.http = _Transport()
        return cl

    try:
        module.Runner = _FakeRunner
        module.CONFIGS_ACTIVE["model"] = "occamy-1.0"
        module.CORPUS_PATH = _CorpusPath(corpus_turns[:turns], preamble)
        module.RUNNER = _FakeRunner(spec_with_id(module, "OH1"), _fake_client(8020))
        err = None
        try:
            module.phase_battery()
        except _ProbeCrash as probe:
            _raise_battery_error(probe)
            err = f"{type(probe.__cause__).__name__}: {probe.__cause__}"
        except Exception as exc:          # the defect IS an exception on the mutant
            err = f"{type(exc).__name__}: {exc}"
    finally:
        module.__dict__.clear()
        module.__dict__.update(ctx)
    return rows, err


def _assert_phase_battery_home(module):
    """``phase_battery`` must resolve THIS module's globals, or the hijack is a no-op."""
    base = getattr(module, "_base", None)          # a defect proxy
    if base is not None and getattr(module, "__getattr__", None) is not None:
        module = base
    fn = getattr(module, "phase_battery", None)
    if fn is None or getattr(fn, "__globals__", None) is not getattr(module, "__dict__", None):
        raise RuntimeError("phase_battery does not resolve module globals: the battery "
                           "hijack would silently measure the real module")


def battery_extra_probe(module):
    """The D2 probe: does one battery round reach ``send`` with ``extra=``?"""
    rows, err = fake_battery(module, turns=4)
    has = [r for r in rows if "arm_compaction" in r]
    return {"rows_out": rows, "n_rows_written": len(rows),
            "n_rows_with_arm_compaction": len(has), "error": err,
            "lands_in_this_module": True}


# ------------------------------------------------------------------------ checks


def check_D1(module):
    """The launch carries the accounting flag, and a blind launch is observable.

    R1 proves the flag is present exactly once.  This adds the consequence R1 cannot
    see: a 200 whose ``usage`` has no ``prompt_tokens_details`` must read ``cached is
    None`` -- a missing flag shows up as "unobserved" on the row, not as a 0.
    """
    S.C["globals"]["R1_flag_in_oh1_oh1l_a1_unchanged"](module=module, allow_mutated=True)
    cl = client_for(module, 8020)
    cl.http = _Transport("200", details=False)
    out = cl.chat_full([{"role": "user", "content": "x"}])
    assert out["cached"] is None, f"a launch without the flag must read as unobserved: {out}"
    assert out["usage_has_details"] is False, out
    # an OBSERVED hit, at or below prompt_tokens: the instrument can see the cache
    cl2 = module.Client(8020)
    cl2.http = _Transport("200", cached=4, details=True)
    out2 = cl2.chat_full([{"role": "user", "content": "x"}])
    assert out2["cached"] == 4 and out2["usage_has_details"] is True, out2
    return {"flag_check": "pass", "blind_cached": out["cached"],
            "blind_usage_has_details": out["usage_has_details"],
            "observed_cached": out2["cached"]}


def check_D2(module):
    # unit level first: the keyword is ACCEPTED and the row carries the payload.  An
    # earlier version of this check read the refused-loopback row instead, whose
    # ``build_row`` was silently replaced by a lenient shim (``**kw``), so a mutant
    # that dropped ``extra`` still passed -- a false green in the proof itself.
    spec = SPEC_LIKE(module)
    good = {"prompt_tokens": 1200, "completion_tokens": 1, "cached": 1,
            "usage_has_details": True, "http_status": 200, "text": "", "ttft_ms": 1.0}
    row_u = module.build_row(spec, good, phase="battery", messages=MSGS, salt="s",
                             arm="A", turn=1, rep=0, request_index=7,
                             extra={"arm_compaction": "append_note",
                                    "arm_render": "pointer", "prompt_nodes": {"turn": 1}})
    assert row_u["arm_compaction"] == "append_note", sorted(row_u)
    assert row_u["arm_render"] == "pointer", sorted(row_u)
    assert row_u["prompt_nodes"] == {"turn": 1}, row_u.get("prompt_nodes")
    probe = battery_extra_probe(module)
    rows, err = probe["rows_out"], probe["error"]
    assert err is None, f"phase_battery raised: {err}"
    assert rows, "phase_battery issued no row"
    assert "arm_compaction" in rows[0], \
        f"the extra payload never reached the row: {sorted(rows[0])[:12]}"
    assert all("arm_compaction" in r and "arm_render" in r and "prompt_nodes" in r
               for r in rows), "some rows lost the extra payload"
    return {"n_rows": len(rows), "arm_compaction": rows[0]["arm_compaction"],
            "arm_render": rows[0]["arm_render"],
            "arms": sorted({r["arm"] for r in rows}), "passes": sorted({r["rep"] for r in rows})}


def check_D3(module):
    """Absence is UNOBSERVED, never a 0 -- and nothing downstream sums it as one.

    The reader (``Client.chat_full`` over a 200 whose usage has no details), the row
    writer, the analyser's per-arm summary and the usage coverage must all say
    "unobserved"; a fabricated 0 fails every one of them.
    """
    cl = client_for(module, 8020)
    cl.http = _Transport("200", details=False)
    out = cl.chat_full([{"role": "user", "content": "x"}])
    assert out["cached"] is None, f"absent details must read None, not 0: {out}"
    row = module.build_row(SPEC_LIKE(module), out, phase="battery", messages=MSGS,
                           salt="s", arm="A", turn=1, resolved_block=2096)
    assert row["cached_tokens"] is None and row["usage_has_details"] is False, row
    assert row["uncached"] is None, row
    rows = [{**row, "model": "occamy-1.0", "config_id": "OH1", "turn": t,
             "prompt_tokens": 100 * t} for t in (1, 2)]
    summ = module.ana.model_summary(rows)["occamy-1.0"]["arms"]["A"]
    assert summ["n_unobserved"] == 2, summ
    assert summ["total_cached"] is None, f"total_cached summed an unobserved value: {summ}"
    assert summ["mean_uncached"] is None, summ
    cov = module.ana.usage_coverage(rows)["OH1"]
    assert cov["n_unobserved"] == 2 and cov["blind"] is True, cov
    # CONTROL: an observed miss is a real 0 and is counted as one
    cl2 = module.Client(8020)
    cl2.http = _Transport("200", cached=0, details=True)
    out2 = cl2.chat_full([{"role": "user", "content": "x"}])
    assert out2["cached"] == 0 and out2["usage_has_details"] is True, out2
    row2 = module.build_row(SPEC_LIKE(module), out2, phase="battery", messages=MSGS,
                            salt="s", arm="A", turn=1, resolved_block=2096)
    assert row2["cached_tokens"] == 0, row2
    assert row2["uncached"] == row2["prompt_tokens"] - 0, row2
    return {"blind_cached": out["cached"], "row_cached": row["cached_tokens"],
            "row_uncached": row["uncached"], "arm_summary": summ,
            "coverage_blind": cov["blind"], "observed_miss": row2["cached_tokens"]}


def _d4_byte_evidence(module, pre, corpus):
    """The salt scheme, measured in the bytes ``phase_battery`` would render.

    ``CELL_CACHE`` is cleared first: the cell memoises ``make_salt`` per seed, so an
    exec'd copy would answer from the REPAIRED cell's cache and no salt revert could
    ever show up in its bytes -- a false red in the proof, not in the cell.

    ``salt_a``/``salt_b`` are the salt functions the battery itself injects -- built by
    calling the module's own ``battery_salt``, so a module that ignores the turn number
    yields one value for every turn and this measurement moves with it.  The arm salt
    (``make_salt(seed)``, the value the repaired code also uses on pass 2) is the
    CONTROL: if one arm salt does not make the chain a sequential walk, nothing here
    is measuring the salt.
    """
    getattr(module, "CELL_CACHE", {}).clear()
    salt_a = lambda n: module.battery_salt(3201, n)
    salt_b = lambda n: module.make_salt(3201)
    op = module.build_arm_messages(module.ARMS[0], pre, corpus, salt_for_turn=salt_a)
    op_arm = module.build_arm_messages(module.ARMS[0], pre, corpus, salt_for_turn=salt_b)
    return op, _sequential_overlap(op), op_arm, _sequential_overlap(op_arm)


def check_D4(module, strict: bool = True):
    """Pass 1 is first-sight: per-turn salts, no sequential prefix, no spurious hit.

    Driven end-to-end through a fake transport whose cache is a REAL prefix-cache
    model: ``cached = longest previously-served-prompt (bytes) that is a prefix of
    this one``.  On the repaired salt scheme every pass-1 turn shares no prefix with
    anything served before it, so every hit must be exactly 0; on one arm salt the
    chain is a sequential walk and turns 2..N report hits.
    """
    # the salt scheme, straight from the function the battery calls
    s1 = module.battery_salt(3201, 1)
    s1b = module.battery_salt(3201, 2)
    arm = module.battery_salt(3201)
    assert s1 != s1b, "pass-1 salts are not per-turn"
    assert s1 != arm, "pass 1 reuses the arm salt"
    model = _PrefixCache()
    transport = _PrefixCacheTransport(model)
    # NOTE: the lever is ``battery_salt`` -- the prefix cache is keyed on the rendered
    # BYTES, which the salt seeds; the module's own ``build_arm_messages`` renders
    # with the module's ``battery_salt``.
    rows, err = fake_battery(module, turns=6, transport=transport)
    if err is not None:
        # a red is the point of the non-strict call, so an abort there is evidence...
        # but a GREEN must never be reported from a run that issued no rows at all
        assert not strict, f"battery raised: {err}"
        aborted = {"aborted": err, "pass1_rows": len([r for r in rows if r["rep"] == 0])}
        assert not rows, "an aborted battery cannot answer: " + aborted["aborted"]
        return aborted
    pass1 = [r for r in rows if r["rep"] == 0]
    assert pass1, "no pass-1 rows"
    hits = [(r["turn"], r["cached_tokens"]) for r in pass1 if (r["cached_tokens"] or 0) > 0]
    assert not hits, f"pass-1 rows report cache hits on a sequential chain: {hits}"
    # REPAIR C, measured OFF the transport: how much of pass 1's earlier turns each
    # pass-1 prompt carries.  A per-turn salt makes every turn a first sight (0); one
    # arm salt makes turn N carry turns 1..N-1.  This is the deterministic form of the
    # defect -- the 1056 cached tokens A1 reported on a "cold" turn 3 were the SERVER's
    # answer to exactly this overlap, and no offline surface can fabricate that number.
    pre, corpus = module.load_turns(module.BATTERY_TURNS)
    op, carried, op_arm, carried_arm = _d4_byte_evidence(module, pre, corpus)
    assert min(carried_arm) > 0, f"one-arm salt carried nothing: {carried_arm}"
    steps = [carried_arm[i] - carried[i] for i in range(len(carried))]
    if strict:
        # DECISIVE: under one arm salt EVERY turn repeats the previous prompt (a
        # sequential walk); under per-turn salts NONE does.  A revert that leaves one
        # turn on the arm salt is caught by the same assertion, per turn.
        assert min(carried_arm) > max(carried), (carried, carried_arm)
        assert min(steps) > 0, steps
    # pass 2 repeats pass 1 byte-for-byte, so the block model must serve a hit there
    pass2 = [r for r in rows if r["rep"] == 1]
    return {"pass1_prompt_tokens": [int(r["prompt_tokens"]) for r in pass1],
            "pass1_rows": len(pass1), "pass1_hits": hits,
            "pass1_carried_bytes": carried, "arm_salt_carried_bytes": carried_arm,
            "pass2_rows": len(pass2),
            "pass2_max_cached": max((r["cached_tokens"] or 0) for r in pass2) if pass2 else None,
            "salt_pass1_vs_arm": [s1, arm]}



def module_bytes(messages) -> bytes:
    return json.dumps(messages, sort_keys=True, separators=(",", ":")).encode("utf-8")


MSGS = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
SPEC_CACHE: dict = {}


def SPEC_LIKE(module):
    """``build_spec``'s spec WITH the top-level ``config_id`` ``Runner.send`` reads.

    The live path gets it from ``run_config``'s merge; a fake Runner built straight
    from ``build_spec(...)["spec"]`` does not, so mirror the merge here.
    """
    if "spec" not in SPEC_CACHE:
        SPEC_CACHE["spec"] = spec_with_id(module, "OH1")
    return SPEC_CACHE["spec"]


CHECKS = {"D1": check_D1, "D2": check_D2, "D3": check_D3, "D4": check_D4}
NAMES = {"D1": "R1_flag_in_oh1_oh1l_a1_unchanged",
         "D2": "R8_send_persists_extra",
         "D3": "R2_absence_is_none_not_zero",
         "D4": "R5_true_cold_pass"}


class _RebuiltMakeSalt:
    """``make_salt`` for the defective salt expression.

    ``make_salt`` calls ``battery_salt(int(seed))`` to derive the per-turn salt, so
    exposing the module's own ``make_salt`` to the defect would either return the REAL
    function's answer (collapsing the fault to nothing) or, once mounted, recurse
    forever.  A deterministic stand-in keeps "one salt per arm" distinct from "one salt
    per (arm, turn)" -- which is all the defect needs -- without touching ``make_salt``.
    """

    @staticmethod
    def __call__(seed):
        import hashlib
        return "arm-salt:" + hashlib.sha256(f"{int(seed)}".encode()).hexdigest()[:16]


_rebuilt_make_salt = _RebuiltMakeSalt()


def _rebind(fn, g):
    """``fn`` with its globals pointed at ``g`` (a lambda's closure stays closed)."""
    return types.FunctionType(fn.__code__, g, fn.__name__, fn.__defaults__, fn.__closure__)


class _SaltGlue:
    """The defective salt, mounted over the real module's own functions.

    ``phase_battery`` and ``build_arm_messages`` resolve ``battery_salt`` -- and
    ``build_arm_messages`` -- through the MODULE's globals.  ``mount()`` swaps
    ``battery_salt`` in those globals for the defective version and wraps
    ``build_arm_messages`` so the ``salt_for_turn`` the battery injects is ignored;
    ``unmount()`` restores every binding it touched, by name, from the snapshot.
    """

    def __init__(self, base, expr: str):
        self.base, self.expr = base, expr
        self.saved: dict = {}

    def _salt(self, seed, turn=None):
        return eval(self.expr, {"cell": self.base, "make_salt": _rebuilt_make_salt,
                                "seed": seed, "turn": turn})

    def defective(self, seed, turn=None):
        """The literal as a FUNCTION VALUE (used for the proxy's own attribute)."""
        return self._salt(seed, turn)

    def mount(self):
        g = self.base.__dict__
        self.saved["battery_salt"] = g["battery_salt"]
        # the defective salt is built by the SAME closure and globals as the real one,
        # but it never resolves ``battery_salt`` -- ``make_salt`` is a separate import,
        # so pointing it back at ``battery_salt`` would recurse forever
        self.mounted = types.FunctionType(self.saved["battery_salt"].__code__, g,
                                          "battery_salt",
                                          self.saved["battery_salt"].__defaults__,
                                          self.saved["battery_salt"].__closure__)
        assert "battery_salt" not in self.mounted.__code__.co_names, \
            self.mounted.__code__.co_names
        g["battery_salt"] = self.mounted
        # ``salt_for_turn`` defaults are captured at FUNCTION DEFINITION, so the
        # battery's ``lambda n, s=seed: battery_salt(s, n)`` would still call the real
        # one: rebuild every lambda whose defaults hide an extra argument and point it
        # at the module globals (through which ``battery_salt`` is now the defect).
        for name, value in list(g.items()):
            if not (isinstance(value, types.FunctionType) and value.__globals__ is g):
                continue
            if name.startswith("__") or name == "battery_salt":
                continue
            consts = tuple(c if not isinstance(c, types.FunctionType) else
                           _rebind(c, g) for c in value.__code__.co_consts)
            self.saved[name] = value
            rebuilt = types.FunctionType(value.__code__.replace(co_consts=consts), g,
                                         value.__name__, value.__defaults__,
                                         value.__closure__)
            rebuilt.__kwdefaults__ = value.__kwdefaults__   # keyword-only defaults
            # function ATTRIBUTES (``build_arm_messages.last_nodes``) live on this copy
            for attr in getattr(value, "__dict__", {}):
                setattr(rebuilt, attr, getattr(value, attr))
            g[name] = rebuilt

    def unmount(self):
        g = self.base.__dict__
        for name, value in self.saved.items():
            g[name] = value
        self.saved.clear()


class _DefectModule:
    """A module proxy whose ``battery_salt`` carries the historical defective expression.

    ``faults`` picks what a check can actually OBSERVE:

    * ``"salt_only"`` (default) -- only the values ``phase_battery`` passes to
      ``build_row`` take the defect, so R5's own salt assertions see it (the rendered
      bytes do not move: ``salt_for_turn=lambda n: cell.battery_salt(...)`` is bound
      before the fault is mounted).
    * ``"battery"`` -- the defect is mounted over the module's globals for the
      duration of a ``with`` block, so the rendered prompts (and anything else that
      reads ``battery_salt``, including ``make-salt`` derivations) take it too.
    """

    SALT_NAMES = ("battery_salt",)

    def __init__(self, base, expr: str, faults=("salt_only",)):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_expr", expr)
        object.__setattr__(self, "_faults", tuple(faults))
        object.__setattr__(self, "_glue", _SaltGlue(base, expr))

    def __getattr__(self, name):
        if name in self.SALT_NAMES:
            glue = object.__getattribute__(self, "_glue")
            return getattr(glue, "mounted", None) or glue.defective
        return getattr(object.__getattribute__(self, "_base"), name)

    def __setattr__(self, name, value):
        if name in self.SALT_NAMES:
            raise AttributeError("the proxy's battery_salt is the defect")
        setattr(object.__getattribute__(self, "_base"), name, value)

    def __getitem__(self, key):
        return object.__getattribute__(self, "_base")[key]

    def __setitem__(self, key, value):
        object.__getattribute__(self, "_base")[key] = value

    def __enter__(self):
        object.__getattribute__(self, "_glue").mount()
        return self

    def __exit__(self, *a):
        object.__getattribute__(self, "_glue").unmount()
        return False


def _raise_battery_error(exc):
    """Find the TypeError hiding behind ``phase_battery``'s own error handling.

    The live re-run's console line was ``PHASE FAILED OH1: ...``: the phase's except
    block reports the crash and carries on, so the defect surfaces as a LOG LINE and
    zero rows, not as a raised exception.  On a mutated battery the fake client raises
    instead; unwrap either shape so the red is the same defect in both.
    """
    seen, cur = set(), exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, TypeError) and "unexpected keyword argument 'extra'" in str(cur):
            raise cur
        cur = cur.__cause__ or cur.__context__
    return exc


# ------------------------------------------------- D2 live path: refused loopback
#
# The ``live`` probe below uses the cell's REAL ``Client.chat_full`` against
# ``http://127.0.0.1:1/v1``: the connection is refused, the row is still built and
# appended, and that is the code path the re-run crashed on.  Port 1 on the loopback
# interface has no listener by construction, so this reproduces the *failure* shape
# and measures nothing -- ``model_requests`` stays 0.


@contextlib.contextmanager
def _real_httpx():
    """Import the REAL httpx just long enough to build one client object.

    ``selftest_offline`` aliased ``sys.modules["httpx"]`` to a no-network stub BEFORE
    the cell imported it; the cell's ``Client.__init__`` therefore holds the stub.
    Loading the genuine distribution here only constructs a socket-less client -- no
    request is ever issued through it (the transport is replaced immediately).
    """
    saved = {k: v for k, v in sys.modules.items() if k == "httpx" or k.startswith("httpx.")}
    for k in saved:
        sys.modules.pop(k, None)
    import importlib
    real = importlib.import_module("httpx")
    assert hasattr(real, "Client"), "the real httpx did not load"
    try:
        sys.modules["httpx"] = real
        yield real
    finally:
        for k in [k for k in sys.modules if k == "httpx" or k.startswith("httpx.")]:
            sys.modules.pop(k, None)
        sys.modules.update(saved)


def _row_facts(row: dict) -> dict:
    """The handful of row fields the probes judge (the rest of the row is not needed)."""
    return {"http_status": row.get("http_status"),
            "cached_tokens": row.get("cached_tokens"),
            "usage_has_details": row.get("usage_has_details"),
            "arm_compaction": row.get("arm_compaction"),
            "text": str(row.get("text"))[:80]}


def live_row_write(module) -> dict:
    """Real ``Client`` -> refused loopback; reports what ``send`` did with ``extra``.

    Nothing is measured here: the loopback port has no listener by construction.  The
    point is WHICH SHAPE the failure takes -- the repaired ``send`` builds the row,
    appends it (carrying the extras) and then re-raises on the non-200, while the
    mutant dies in its signature and appends nothing.
    """
    ctx = dict(module.__dict__)
    rows: list[dict] = []
    try:
        spec = SPEC_LIKE(module)
        # ``phase_battery`` is called (by the checks) with the module's ``Runner``
        # swapped; ``live_row_write`` never interns a copy module, but ``rev2`` in an
        # earlier draft did -- refuse it here too, so the probe cannot measure the
        # real module while claiming to measure a mutant.
        _assert_phase_battery_home(module)
        with _real_httpx() as real:
            # ``Client.__init__`` calls the CELL module's global ``httpx``, which
            # ``selftest_offline`` left as its no-network stub: bind the real module
            # under its own name (``_real_httpx`` only swaps ``sys.modules``).
            module.__dict__["httpx"] = real
            cl = module.Client(1)          # real httpx.Client; never asked to connect
            # ... pointed at a real httpx transport that refuses in-process
            cl.http = real.Client(transport=_RefuseTransport())
            cl.base = "http://127.0.0.1:1/v1"
            cl.model = spec["served_model"]

            class R(module.Runner):
                def __init__(self):
                    self.spec, self.client = spec, cl
                    self.resolved_block, self.requests = 2096, 0

                def n_rows(self):
                    return len(rows)

                def append(self, r):
                    rows.append(r)

            module.RUNNER = R()
            module.CONFIGS_ACTIVE["model"] = "occamy-1.0"
            out = {"ok": True}
            try:
                row = module.RUNNER.send("battery", [{"role": "user", "content": "x"}],
                                         salt="s", arm="A", turn=1, rep=0,
                                         extra={"arm_compaction": "append_note",
                                                "arm_render": "pointer"})
                out.update(_row_facts(row))
            except TypeError as exc:
                out.update({"ok": False, "error": f"TypeError: {exc}",
                            "n_rows": len(rows)})
                return out
            except Exception as exc:          # the row exists; send re-raised on status
                out["raise"] = f"{type(exc).__name__}: {exc}"[:120]
                if rows:
                    out.update(_row_facts(rows[-1]))
            out["n_rows"] = len(rows)
            return out
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:300]}
    finally:
        module.__dict__.clear()
        module.__dict__.update(ctx)


def live_row_write_mutant(module) -> dict:
    """``live_row_write`` with ``Runner.send`` replaced by the loud mutant."""
    with _SendMutant(module, "no_keyword"):
        return live_row_write(module)



class _RefuseTransport:
    """A real-httpx transport that refuses every request in-process."""

    def handle_request(self, request):
        import httpx as _h
        raise _h.ConnectError("[Errno 111] Connection refused", request=request)


# --------------------------------------------------------------------------- main


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _red(check, mod):
    """Run ``check`` over a defective module; return ``{"red": bool, ...}``.

    STRICT: a red means the check ASSERTED.  Any other exception is a defect in this
    file (a broken harness call, a mis-mounted mutant), never proof about the cell --
    so it is reported as ``red: None`` and named, rather than counted as evidence.
    """
    try:
        check(mod)
        return {"red": False, "error": "defective harness PASSED"}
    except AssertionError as exc:
        return {"red": True, "error": str(exc)[:300]}
    except Exception as exc:
        return {"red": None, "error": f"{type(exc).__name__}: {exc}"[:300]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw", type=int, default=4,
                    help="fake battery rounds per probe (0 = source-only red, no request path)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)

    t0 = time.time()
    repaired_src = (HERE / "pmu16_cell.py").read_text(encoding="utf-8")
    result = {
        "unit": "R2-VLLM", "phase": "fix-instrument", "schema": 1,
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "offline": True, "model_requests": 0, "lock_taken": False,
        "cell_source": {"path": "experiments/context-cache/cells/R2-VLLM/pmu16_cell.py",
                        "sha256": _sha(repaired_src),
                        "lines": repaired_src.count("\n") + 1},
        "draw": args.draw, "defects": {},
    }
    try:
        S.load_cell(name="pmu_cell_verify")
    except Exception as exc:
        result["repaired_import_error"] = f"{type(exc).__name__}: {exc}"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=1)[:3000])
        return 2

    for key, check in CHECKS.items():
        rec = {"check": NAMES[key],
               "literal_why": LITERALS.get(key, {}).get("why"),
               "literal_how": LITERALS.get(key, {}).get("how")}
        try:
            rec["green"] = {"pass": True, "evidence": check(cell)}
        except Exception as exc:
            rec["green"] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"[:400]}
        # RED 1 (literal): the historical defective code
        try:
            if key == "D1":
                rec["literal_red"] = _red(check, load_reverted(
                    S._apply(repaired_src, LITERALS["D1"]["subs"]), "pmu_cell_lit_D1", "D1"))
            elif key == "D4":
                # literal red: the historical salt, confined to what the battery passes
                # to build_row (R5's salt assertions see it).  The END-TO-END red -- the
                # rendered bytes the battery actually sent -- is source_red, where the
                # same literal is mounted over the module's globals.
                rec["literal_red"] = _red(
                    lambda m: check_D4(m, strict=False),
                    _DefectModule(cell, LITERALS["D4"]["expr"]))
            elif key == "D3":
                # the historical reader, put back as the module's own parse_usage;
                # ``Client.chat_full`` reaches it through these same globals.
                with _readers_mounted(cell, "parse_usage", parse_usage_literal()):
                    rec["literal_red"] = _red(check, cell)
            else:
                rec["literal_red"] = {"red": None,
                                      "error": "D2 is proven by mutation: the loud half "
                                               "is source_red, the silent half is "
                                               "literal_red_silent"}
        except Exception as exc:
            rec["literal_red"] = {"red": None, "error": f"setup: {type(exc).__name__}: {exc}"[:300]}
        # RED 2 (source): this repair mechanically reverted on a copy
        src_rev, matched = source_revert(key, repaired_src)
        rec["source_red"] = {"anchors": matched,
                             "matched": all(m["count"] >= 1 for m in matched)}
        if rec["source_red"]["matched"] and src_rev != repaired_src:
            try:
                mod = load_reverted(src_rev, f"pmu_cell_rev_{key}", key)
                if key == "D4":
                    # A one-line revert inside THIS battery does not flip R5: the arm
                    # prompts are rendered upstream (``build_arm_messages``) and R5's own
                    # prefix control calls ``battery_salt`` directly, so its assertions
                    # still hold.  What IS observable end to end is the historical salt,
                    # mounted over the module's globals; R5 then reads the bytes the
                    # battery really sent.  The anchor revert stays as the evidence that
                    # the line under repair is the one selecting the salt.
                    with _DefectModule(mod, LITERALS["D4"]["expr"],
                                       faults=("battery",)) as mounted:
                        rec["source_red"].update(_red(
                            lambda m: check_D4(m, strict=False), mounted))
                else:
                    rec["source_red"].update(_red(check, mod))
            except Exception as exc:
                rec["source_red"].update({"red": True, "via": "load/exec",
                                          "error": f"{type(exc).__name__}: {exc}"[:300]})
        else:
            rec["source_red"].update({"red": None, "error": "anchor drifted from the source"})
        rec["ok"] = bool(rec["green"]["pass"] and rec["source_red"].get("red") is True
                         and rec["literal_red"]["red"] in (True, None))
        if key == "D2":
            try:
                with _send_mounted(cell, "drop_extra"):
                    rec["literal_red_silent"] = _red(check, cell)
            except Exception as exc:
                rec["literal_red_silent"] = {"red": None,
                                             "error": f"setup: {type(exc).__name__}: {exc}"[:200]}
            rec["ok"] = bool(rec["ok"] and rec["literal_red_silent"].get("red") is True)
        result["defects"][key] = rec

    # D2 extras: the SILENT half as a literal, and the live row-write path both ways
    d2 = result["defects"]["D2"]
    live = {"repaired": live_row_write(cell), "reverted": live_row_write_mutant(cell),
            "surface": "real Client.chat_full -> real httpx.Client with a refusing "
                       "transport (loopback :1, no listener); the row is still built "
                       "and appended"}
    rep_, rev_ = live["repaired"], live["reverted"]
    live["ok"] = bool(rep_.get("ok") is True and rep_.get("n_rows") == 1
                      and rep_.get("http_status") == 0
                      and rep_.get("arm_compaction") == "append_note"
                      and "ConnectError" in str(rep_.get("raise", ""))
                      and "Connection refused" in str(rep_.get("raise", ""))
                      and rev_.get("ok") is False and rev_.get("n_rows") == 0
                      and "unexpected keyword argument 'extra'" in str(rev_.get("error", "")))
    d2["live_probe"] = live
    d2["ok"] = bool(d2["ok"] and live["ok"] and d2["literal_red_silent"].get("red") is True)

    # the round-driven evidence: a real battery over the injected transport
    if args.draw > 0:
        rows_ok, err_ok = fake_battery(cell, turns=4)
        with _send_mounted(cell, "no_keyword"):
            rows_bad, err_bad = fake_battery(cell, turns=4)
        result["battery_rounds"] = {
            "repaired": {"rows": len(rows_ok), "error": err_ok,
                         "arms": sorted({r["arm"] for r in rows_ok}),
                         "passes": sorted({r["rep"] for r in rows_ok}),
                         "extra_present": bool(rows_ok) and all("arm_compaction" in r
                                                                for r in rows_ok)},
            "reverted": {"rows": len(rows_bad), "error": err_bad},
            "turns_requested": 4,
        }
    else:
        result["battery_rounds"] = {"repaired": {"skipped": "draw=0"},
                                    "reverted": {"skipped": "draw=0"}}

    result["summary"] = {
        "n_defects": len(CHECKS),
        "green": sum(1 for r in result["defects"].values() if r["green"]["pass"]),
        "literal_red": sum(1 for r in result["defects"].values()
                           if r["literal_red"]["red"] is True),
        "source_red": sum(1 for r in result["defects"].values()
                          if r["source_red"].get("red") is True),
        "ok": all(r["ok"] for r in result["defects"].values()),
        "elapsed_s": round(time.time() - t0, 2),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for k, r in result["defects"].items():
        print(f"{k} green={'PASS' if r['green']['pass'] else 'FAIL'} "
              f"literal_red={r['literal_red']['red']} source_red={r['source_red'].get('red')} "
              f"ok={r['ok']}  {r['check']}")
        if not r["green"]["pass"]:
            print(f"   green: {r['green'].get('error')}")
        if r["source_red"].get("red") is not True:
            print(f"   source: {r['source_red'].get('error')}")
    print("live D2: " + json.dumps(live)[:600])
    print("battery: " + json.dumps(result["battery_rounds"])[:400])
    print("SUMMARY " + json.dumps(result["summary"]))
    print(f"wrote {args.out.relative_to(REPO)}")
    return 0 if result["summary"]["ok"] else 1


class _SendMutant:
    """``Runner.send`` swapped for a defective copy, for the duration of a block.

    The defect is in ``send`` itself, so it cannot be reached from an exec'd copy of the
    module: a copy's ``phase_battery`` resolves the COPY's globals, so hijacking
    ``Runner``/``CORPUS_PATH`` on the live module would leave the battery running
    against the real, repaired ``Runner``.  Mounting on the live class is the only
    mutation that actually reaches the code path.

    Two shapes, matching the two halves of the live defect:

    * ``drop_extra`` -- the keyword is accepted and never forwarded: every row is
      written, and none carries ``arm_compaction``/``arm_render``/``prompt_nodes``.
    * ``no_keyword`` -- the parameter is gone: ``phase_battery``'s ``extra=`` raises
      ``TypeError: unexpected keyword argument 'extra'`` on the FIRST row and the
      battery writes nothing (exactly what the live re-run died of).
    """

    # dedented: ``inspect.getsource`` of a method starts at column 0
    EXTRA_LINE = ("request_index=self.n_rows() + 1, extra=extra)")
    DROP_LINE = ("request_index=self.n_rows() + 1, extra=None)")

    def __init__(self, module, which: str):
        self.module, self.which = module, which

    def _mutant(self, own):
        src = textwrap.dedent(inspect.getsource(own))
        if self.which == "drop_extra":
            if src.count(self.EXTRA_LINE) != 1:
                raise RuntimeError("the send payload line moved: cannot build the mutant")
            ns = dict(self.module.__dict__)
            exec(compile(src.replace(self.EXTRA_LINE, self.DROP_LINE),
                         f"<{own.__qualname__}:drop_extra>", "exec"), ns)
            return ns[own.__name__]
        if self.which == "no_keyword":
            code = own.__code__
            if "extra" not in code.co_varnames:
                raise RuntimeError("send has no `extra` local to drop")
            new = code.replace(co_varnames=tuple(v for v in code.co_varnames if v != "extra"),
                               co_nlocals=code.co_nlocals - 1,
                               co_argcount=code.co_argcount - 1)
            fn = types.FunctionType(new, self.module.__dict__, own.__name__,
                                    own.__defaults__, own.__closure__)
            fn.__kwdefaults__ = {k: v for k, v in (own.__kwdefaults__ or {}).items()
                                 if k != "extra"}
            return fn
        raise ValueError(self.which)

    def __enter__(self):
        cls = self.module.__dict__.get("Runner")
        if cls is None:
            raise RuntimeError("no Runner in this module")
        if "send" not in cls.__dict__:
            raise RuntimeError("Runner.send is inherited: a class-level swap would not bind")
        self.saved = cls.send
        cls.send = self._mutant(cls.send)
        return self

    def __exit__(self, *a):
        self.module.__dict__["Runner"].send = self.saved
        return False


@contextlib.contextmanager
def _send_mounted(module, which: str):
    """The live module with ``Runner.send`` mutated for the block (see ``_SendMutant``)."""
    with _SendMutant(module, which):
        yield module


def parse_usage_literal():
    """The historical reader: ``(details.get("cached_tokens") or 0)`` -- absence -> 0."""
    def parse_usage(usage):
        details = (usage or {}).get("prompt_tokens_details") or {}
        return {"prompt_tokens": int((usage or {}).get("prompt_tokens") or 0),
                "completion_tokens": int((usage or {}).get("completion_tokens") or 0),
                "cached": int(details.get("cached_tokens") or 0),
                "usage_has_details": bool(details)}
    return parse_usage


@contextlib.contextmanager
def _readers_mounted(module, name: str, fn):
    """Swap ``module.name`` for ``fn`` for the duration of the block."""
    saved = module.__dict__[name]
    module.__dict__[name] = fn
    try:
        yield module
    finally:
        module.__dict__[name] = saved

if __name__ == "__main__":
    raise SystemExit(main())
