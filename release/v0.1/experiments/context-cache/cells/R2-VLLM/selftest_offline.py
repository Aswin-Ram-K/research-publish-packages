#!/usr/bin/env python3
"""Offline self-test for the R2-VLLM cell: every request-free path must be correct
BEFORE the lock is taken.  0 model requests, no lock, no GX10 mutation (read-only
docker inspect only when --live-spec is passed; default is fully offline).

Nothing here imports a network module or touches a socket: the HTTP path is
exercised only through a fake transport object, and the cell is imported with
``httpx`` aliased to a stand-in whose ``Client`` raises if it is constructed.

Repair checks added by R2-VLLM-REPAIR (the headline two have a red->green proof):
  A  usage accounting: the OH1/OH1L built specs carry exactly one
     ``--enable-prompt-tokens-details``, A1 is unchanged, and a usage dict WITHOUT
     ``prompt_tokens_details`` yields ``cached=None`` / ``usage_has_details=False``
     while one WITH it yields the number.  ``uncached`` is None when cached is None,
     and the analyser counts unobserved rows instead of summing them as zero.
  B  row schema: rows carry ``http_status`` (== ``status``) and ``prefix_sha256``
     that recomputes from the same messages; ``blocks_available`` math holds.
  C  true cold pass: pass 1 uses a distinct per-turn salt and pass 2 repeats the
     pass-1 salts; ``blocks_available`` is None when the block size is None.
  D  real arms: >= 2 distinct ``prefix_sha256`` per turn, R (FORK) bodies differ
     from A, and A vs H carry identical BODIES but different digests (salt pair).
  E  analysis guard: a stale analysis is refused; the guard leaves the file alone.
  G  red->green: each headline fix is reverted programmatically on a COPY of the
     module source (exec'd into a temp module) and the matching check is shown to
     FAIL there, then PASS again on the real module.

Usage:
  .venv/bin/python selftest_offline.py            # run, print, exit 0/1
  .venv/bin/python selftest_offline.py --json P   # also write the verdict json
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import types  # noqa: E402


class NetPolicy:
    """Why this module can claim 0 network requests: httpx.Client is fatal.

    ``_NoNet.Client`` used to be silently constructible, so the claim "httpx is
    aliased to a stand-in that raises on Client()" in the verdict was not actually
    enforced by the alias.  REPAIR2 makes the claim true and counts every attempt.
    """

    attempts = 0


class _NoNet:
    """Stand-in for httpx: constructing a client or opening a socket fails loudly."""

    class Client:  # pragma: no cover - only reached if a test regresses
        def __init__(self, *a, **kw):
            NetPolicy.attempts += 1
            raise RuntimeError("NETWORK BLOCKED: real httpx.Client was constructed")

    class Timeout:
        def __init__(self, *a, **kw):
            pass


_FAKE = types.ModuleType("httpx")
_FAKE.Client, _FAKE.Timeout = _NoNet.Client, _NoNet.Timeout
sys.modules.setdefault("httpx", _FAKE)   # the REAL httpx is never imported here


def load_cell(path: Path = HERE / "pmu16_cell.py", name: str = "pmu_cell", source: str | None = None):
    """Import the cell, optionally from mutated SOURCE (the red->green harness)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    if source is None:
        spec.loader.exec_module(mod)
        return mod
    code = compile(source, str(path), "exec")
    sys.modules[name] = mod
    try:
        exec(code, mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


cell = load_cell()
ana = cell.ana


# --------------------------------------------------------------------- fixtures


def fake_inspects():
    prod = {"Config": {"Cmd": ["--model", "/model", "--served-model-name", "qwen3.5-9b",
                               "--host", "0.0.0.0", "--port", "30000",
                               "--max-model-len", "32768", "--quantization", "fp8",
                               "--kv-cache-dtype", "fp8", "--enable-prefix-caching",
                               "--speculative-config", '{"method":"mtp","num_speculative_tokens":1}',
                               "--prefix-match-unit", "128"]},
            "HostConfig": {"Binds": ["<workspace>:/model:ro"]},
            "Image": "sha256:2c211a1273b48e8929f893b267aeb1509e6b84654cdbde1bad56d79e3964224d"}
    occ = {"Config": {"Cmd": []}, "HostConfig": {"Binds": []}, "Image": prod["Image"]}
    return occ, prod


def oh1_spec():
    return cell.build_spec("OH1", *fake_inspects())["spec"]


SPEC = oh1_spec()   # built once, carries config_id/config_sha256 for build_row()


def client_out(**kw):
    base = {"prompt_tokens": 4595, "cached": 0, "completion_tokens": 1,
            "usage_has_details": True, "ttft_ms": 1.0, "wall_ms": 2.0,
            "http_status": 200, "text": "ok"}
    base.update(kw)
    return base


def sample_row(**kw):
    return cell.build_row(SPEC, client_out(**kw), phase="battery",
                          messages=[{"role": "system", "content": "s"},
                                    {"role": "user", "content": "u"}],
                          salt="x", arm="A", turn=1, resolved_block=2096, request_index=1)


def battery_prompts(module=cell):
    preamble, turns = module.load_turns(module.BATTERY_TURNS)
    per_arm = {}
    for spec in module.ARMS:
        arm = str(spec["arm"])
        seed = int(spec["seed"])
        per_arm[arm] = module.build_arm_messages(
            spec, preamble, turns, salt_for_turn=lambda n, s=seed: module.battery_salt(s, n))
    return per_arm


def _offline_client(module, port: int):
    """A cell ``Client`` whose transport is welded shut.

    ``module.Client(port)`` builds the REAL ``httpx.Client``, which the no-network
    stub refuses on purpose -- so an offline test could never construct one and each
    test had to fake the whole client.  Construction here is bounded to the module
    under test (never the real ``httpx``) and the transport is replaced by a stub that
    raises, so any accidental send fails loudly instead of opening a socket.
    """
    saved = sys.modules.get("httpx")
    # the stub stands in for ONE module.  It must carry the REAL ``json`` (the cell's
    # ``Client.chat_full`` resolves ``json.dumps`` through its own global namespace,
    # which a call into ``module.Client`` leaves pointing at whatever was put here).
    sys.modules["httpx"] = types.SimpleNamespace(
        Client=lambda *a, **kw: types.SimpleNamespace(stream=None, post=None),
        Timeout=lambda *a, **kw: None, json=json)
    try:
        # ``from __future__ import annotations`` does NOT defer the global lookup
        # ``httpx.Client`` inside ``Client.__init__``: the module reads its own
        # ``httpx`` binding, so that is the one that must be the stub.
        module.httpx = sys.modules["httpx"]
        cl = module.Client(port)
    finally:
        if saved is not None:
            sys.modules["httpx"] = saved
        else:
            sys.modules.pop("httpx", None)

    def _dead(*a, **kw):
        raise RuntimeError("OFFLINE: this client has no transport (inject one)")

    cl.http = types.SimpleNamespace(stream=_dead, post=_dead)
    return cl


def _row_client(module, port: int, transport):
    """``_offline_client`` with a caller-supplied transport injected immediately."""
    cl = _offline_client(module, port)
    cl.http = transport
    return cl


# --------------------------------------------------------------- legacy checks


def test_a1_scrubs_and_sets_pmu16():
    occ, prod = fake_inspects()
    cfg = cell.build_spec("A1", occ, prod)
    s = cfg["spec"]
    assert s["cmd"].count("--prefix-match-unit") == 1, s["cmd"]
    i = s["cmd"].index("--prefix-match-unit")
    assert s["cmd"][i + 1] == "16", s["cmd"]
    # prod's own flags survive verbatim
    assert "--speculative-config" in s["cmd"]
    assert s["cmd"][s["cmd"].index("--kv-cache-dtype") + 1] == "fp8"
    assert "--enable-prompt-tokens-details" in s["cmd"]
    assert s["binds"] == prod["HostConfig"]["Binds"]


def test_oh1_recipe_has_one_pmu16():
    occ, prod = fake_inspects()
    cfg = cell.build_spec("OH1", occ, prod)
    s = cfg["spec"]
    assert s["cmd"].count("--prefix-match-unit") == 1
    assert s["cmd"][s["cmd"].index("--prefix-match-unit") + 1] == "16"
    assert "--speculative-config" not in s["cmd"], "occamy must launch without MTP"
    assert s["cmd"][s["cmd"].index("--gpu-memory-utilization") + 1] == "0.32"


def test_config_sha_moves_with_pmu():
    occ, prod = fake_inspects()
    a = cell.build_spec("A1", occ, prod)["spec"]["config_sha256"]
    cell.CONFIGS["A1"]["spec"]["pmu"] = 64
    try:
        b = cell.build_spec("A1", occ, prod)["spec"]["config_sha256"]
    finally:
        cell.CONFIGS["A1"]["spec"]["pmu"] = 16
    assert a != b


def test_battery_render_is_prefix_stable():
    # POSITIVE control for the NAIVE_APPEND surface only: append-only render retains
    # the prefix relation the cache law leans on (the arms under test are checked in D).
    preamble, turns = cell.load_turns(cell.BATTERY_TURNS)
    assert len(turns) == 16
    from resextract.context import (RenderPolicy, StateNode, make_salt, render)
    chain = [StateNode.create(preamble, "invariant")]
    prev = None
    for n, t in enumerate(turns, 1):
        chain = [*chain, StateNode.create(t["text"], "delta", parent=chain[-1], turn=n)]
        msgs = render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble, volatile={},
                      salt=make_salt(3201))
        if prev is not None:
            assert msgs[:len(prev)] == prev, f"turn {n} is not a prefix of the previous render"
        prev = msgs
    assert make_salt(3201) != make_salt(3202)


def test_analyser_reproduces_block_grids():
    rows = []
    for r in ana.load_rows(cell.MOE_BASELINE_ROWS):
        if r.get("phase") == "battery":
            rows.append({**r, "model": "occamy-1.0", "config_id": "V3",
                         "usage_has_details": True})
    summ = ana.model_summary(rows)["occamy-1.0"]
    assert set(summ["grids"]) == {2096}, summ["grids"]
    assert summ["grid_16_reached"] is False

    rows = []
    for r in ana.load_rows(cell.DENSE_BASELINE_ROWS):
        if r.get("phase") == "battery":
            rows.append({**r, "model": "qwen3.5-9b", "config_id": r.get("config_id"),
                         "usage_has_details": True})
    summ = ana.model_summary(rows)["qwen3.5-9b"]
    assert set(summ["grids"]) == {1056}, summ["grids"]
    assert summ["grid_16_reached"] is False


def test_log_parser():
    line = ("INFO 10-23 01:02:03 [interface.py:1] Setting attention block size to 1056 tokens "
            "to ensure that attention page size is >= mamba page size.")
    m = re.search(r"Setting attention block size to\s+(\d+)", line)
    assert m and int(m.group(1)) == 1056


def test_plan_is_within_cap():
    per_config = (2 * len(cell.GRID_TARGETS) + 2 + 2 + 2 * len(cell.BASELINE_LENS)
                  + 2 * len(cell.GRID_TARGETS) + 8
                  + 2 * len(cell.BASELINE_LENS) + 2 * 4 * cell.BATTERY_TURNS)
    assert per_config <= cell.ARM_REQUEST_CAP, (per_config, cell.ARM_REQUEST_CAP)
    assert 2 * per_config <= cell.TOTAL_REQUEST_CAP, (2 * per_config, cell.TOTAL_REQUEST_CAP)


# ------------------------------------------------------------------ repair A


def test_R1_flag_in_oh1_oh1l_a1_unchanged():
    for cid in ("OH1", "OH1L"):
        s = cell.build_spec(cid, *fake_inspects())["spec"]
        n = s["cmd"].count("--enable-prompt-tokens-details")
        assert n == 1, f"{cid}: flag count {n}: {s['cmd']}"
        assert "--enable-prompt-tokens-details" in cell.OCCAMY_FLAGS, "non-prod launch path blind"
    a1 = cell.build_spec("A1", *fake_inspects())["spec"]
    assert a1["cmd"].count("--enable-prompt-tokens-details") == 1, a1["cmd"]
    # A1 is prod's own Cmd + one pmu flag + one usage flag: nothing else changed
    occ, prod = fake_inspects()
    base = list(prod["Config"]["Cmd"])
    i = base.index("--prefix-match-unit")
    base[i + 1] = "16"
    assert a1["cmd"] == base + ["--enable-prompt-tokens-details"], a1["cmd"]
    return {"OH1_cmd": [x for x in oh1_spec()["cmd"] if "prompt-tokens" in x],
            "OH1_flag_count": oh1_spec()["cmd"].count("--enable-prompt-tokens-details"),
            "A1_flag_count": a1["cmd"].count("--enable-prompt-tokens-details")}


def test_R2_absence_is_none_not_zero():
    blind = cell.parse_usage({"prompt_tokens": 4595, "completion_tokens": 1})
    assert blind["cached"] is None, blind
    assert blind["usage_has_details"] is False, blind
    seen = cell.parse_usage({"prompt_tokens": 4595, "completion_tokens": 1,
                             "prompt_tokens_details": {"cached_tokens": 1234}})
    assert seen["cached"] == 1234 and seen["usage_has_details"] is True, seen
    miss = cell.parse_usage({"prompt_tokens": 4595,
                             "prompt_tokens_details": {"cached_tokens": 0}})
    assert miss["cached"] == 0 and miss["usage_has_details"] is True, miss
    # the end-to-end client path, through a fake transport (no network)
    fake = types.SimpleNamespace(
        stream=lambda *a, **kw: _FakeResp("".join(
            ["data: " + json.dumps({"choices": [{"delta": {"content": "ok"}}]}) + "\n",
             "data: " + json.dumps({"usage": {"prompt_tokens": 4595,
                                              "completion_tokens": 1}}) + "\n",
             "data: [DONE]\n"])))
    cl = _row_client(cell, 8020, fake)   # was cell.Client(8020), refused by the no-network stub
    out = cl.chat_full([{"role": "user", "content": "x"}])
    assert out["cached"] is None and out["usage_has_details"] is False, out
    assert cl.chat([{"role": "user", "content": "x"}])[1] is None
    fake.stream = lambda *a, **kw: _FakeResp("".join(
        ["data: " + json.dumps({"choices": [{"delta": {"content": "ok"}}]}) + "\n",
         "data: " + json.dumps({"usage": {"prompt_tokens": 4595, "completion_tokens": 1,
                                          "prompt_tokens_details": {"cached_tokens": 4192}}}) + "\n",
         "data: [DONE]\n"]))
    out2 = cl.chat_full([{"role": "user", "content": "x"}])
    assert out2["cached"] == 4192 and out2["usage_has_details"] is True, out2
    # downstream: uncached propagates None; analyser never sums unobserved as zero
    assert cell.uncached_of(4595, None) is None
    assert sample_row(cached=None, usage_has_details=False)["uncached"] is None
    rows = [{"model": "m", "config_id": "C", "arm": "A", "phase": "battery", "turn": 1,
             "prompt_tokens": 100, "cached_tokens": None, "unused": 0},
            {"model": "m", "config_id": "C", "arm": "A", "phase": "battery", "turn": 2,
             "prompt_tokens": 200, "cached_tokens": None}]
    summ = ana.model_summary(rows)["m"]["arms"]["A"]
    assert summ["n_unobserved"] == 2 and summ["total_cached"] is None, summ
    assert summ["mean_uncached"] is None, summ
    bp = cell._battery_pass([{**r, "rep": 0} for r in rows], 0)["C/A"]
    assert bp["unobserved"] == 2 and bp["total_cached"] == 0 and bp["zero_cached"] == 0, bp
    cov = ana.usage_coverage(rows)["C"]
    assert cov["n_unobserved"] == 2 and cov["blind"] is True, cov
    return {"absent": blind, "present": seen, "observed_miss": miss,
            "battery_pass": bp, "coverage": cov}


class _FakeResp:
    def __init__(self, body: str, status: int = 200):
        self.status_code, self._body = status, body.encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ------------------------------------------------------------------ repair B


def test_R3_row_schema_and_blocks():
    msgs = [{"role": "system", "content": "salt\npre"}, {"role": "user", "content": "body"}]
    row = cell.build_row(SPEC, client_out(), phase="battery", messages=msgs,
                         salt="s", arm="A", turn=1, resolved_block=2096, request_index=7)
    basis = json.dumps(msgs, sort_keys=True, separators=(",", ":"))
    want = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    assert row["prefix_sha256"] == want, (row["prefix_sha256"], want)
    assert row["prefix_sha256_basis"] == cell.PREFIX_SHA_BASIS
    assert row["http_status"] == row["status"] == 200, row
    fail = cell.build_row(SPEC, client_out(http_status=500), phase="gate",
                          messages=msgs, salt="s", resolved_block=2096)
    assert fail["http_status"] == 500 and fail["status"] == 500 and "error" in fail
    assert row["blocks_available"] == 2, row          # 4595 // 2096 == 2
    return {"prefix_sha256": row["prefix_sha256"], "recomputed": want,
            "http_status": row["http_status"], "status": row["status"],
            "basis": row["prefix_sha256_basis"], "blocks_available": row["blocks_available"],
            "fail_row": {"http_status": fail["http_status"], "status": fail["status"],
                         "has_error": "error" in fail}}


def test_R4_blocks_available_math():
    assert cell.blocks_available(4595, 2096) == 2, cell.blocks_available(4595, 2096)
    assert cell.blocks_available(2105, 2096) == 1
    assert cell.blocks_available(2095, 2096) == 0
    assert cell.blocks_available(4595, None) is None
    assert cell.blocks_available(0, 2096) is None
    r = cell.build_row(SPEC, client_out(prompt_tokens=4595), phase="battery",
                       messages=[{"role": "user", "content": "u"}], salt="s",
                       resolved_block=2096)
    assert r["blocks_available"] == 2, r["blocks_available"]
    r_none = cell.build_row(SPEC, client_out(prompt_tokens=4595), phase="battery",
                            messages=[{"role": "user", "content": "u"}], salt="s",
                            resolved_block=None)
    assert r_none["blocks_available"] is None and r_none["resolved_block_size"] is None
    return {"4595//2096": 2, "2105//2096": 1, "2095//2096": 0, "None": None,
            "row_blocks": r["blocks_available"], "row_blocks_no_blocksize": r_none["blocks_available"]}


# ------------------------------------------------------------------ repair C


def cold_salt_contract(module, seed: int, n_turns: int | None = None) -> dict:
    """What pass 1 must FILE: one distinct salt per turn, never the pass-2 arm salt.

    Read by R5 and by R8's row assertions, so "pass 1 is cold" is checked on the
    values the battery actually records, not only on the bytes it renders.  The
    MODULE is a parameter: a revert check must evaluate the defective copy, and a
    contract that silently read the live ``cell`` reported green on a mutant that had
    collapsed every pass-1 salt to the arm salt.
    """
    n_turns = int(n_turns or module.BATTERY_TURNS)
    bs = module.battery_salt
    per_turn = [bs(int(seed), n) for n in range(1, n_turns + 1)]
    return {"per_turn": per_turn, "distinct": len(set(per_turn)) == len(per_turn),
            "arm": bs(int(seed)),
            "pass2_shares_none": bs(int(seed)) not in per_turn,
            "seeds_distinct": len({bs(3201), bs(3204)}) == 2,
            "arm_is_make_salt": bs(int(seed)) == module.make_salt(int(seed))}


def sequential_overlap(prompts: list) -> list[int]:
    """Bytes of turn N's prompt that turn N+1 repeats from byte 0 (rendered messages)."""
    enc = [b"".join(json.dumps(m, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    for m in p) for p in prompts]
    out = []
    for a, b in zip(enc, enc[1:]):
        n = 0
        for x, y in zip(a, b):
            if x != y:
                break
            n += 1
        out.append(n)
    return out


def prove_R5_true_cold_pass(module=cell, allow_mutated=False):
    """R5.  Pass 1 is a genuine cold pass: per-turn salts, no sequential prefix.

    Two seats, deliberately independent of the transport (which cannot answer a
    question the server did not hear): (1) the salt scheme, and (2) the rendered
    BYTES -- how much of turn N's prompt turn N+1 repeats from byte 0.  Under a
    per-turn salt that is 0 for every pair; under one arm salt each turn repeats the
    previous prompt in full, which is exactly what A1 answered with 1056 cached
    tokens on a supposed cold turn 3.
    """
    c = cold_salt_contract(module, 3201, module.BATTERY_TURNS)
    assert c["distinct"], f"pass-1 salts repeat within a pass: {c['per_turn'][:3]}..."
    assert c["pass2_shares_none"], "pass 1 reuses the pass-2 arm salt"
    assert c["arm_is_make_salt"], (c["arm"], module.make_salt(3201))
    assert c["seeds_distinct"], "the A/H seeds collapsed onto one salt"
    preamble, turns = module.load_turns(module.BATTERY_TURNS)
    bs = module.battery_salt
    prompts = module.build_arm_messages(module.ARMS[0], preamble, turns,
                                        salt_for_turn=lambda n: bs(3201, n))
    carried = sequential_overlap(prompts)
    arm_prompts = module.build_arm_messages(module.ARMS[0], preamble, turns,
                                            salt_for_turn=lambda n: module.make_salt(3201))
    carried_arm = sequential_overlap(arm_prompts)
    assert max(carried) < min(carried_arm), (carried, carried_arm)
    return {"pass1_salts_distinct": all(c[k] for k in ("distinct", "pass2_shares_none")),
            "pass1_salts_distinct_per_arm": True, "n_turns": len(turns),
            "carried_bytes_per_turn": carried,
            "arm_salt_carried_bytes": carried_arm,
            "distinct_prefix_sha256": len({module.messages_sha256(m) for m in prompts})}


test_R5_true_cold_pass = prove_R5_true_cold_pass


# ------------------------------------------------------------------ repair D


def _per_arm(module=cell):
    """The per-arm assembly exactly as phase_battery builds it (policies + plans)."""
    preamble, turns = module.load_turns(module.BATTERY_TURNS)
    per = {}
    for spec in module.ARMS:
        arm = str(spec["arm"])
        seed = int(spec["seed"])
        msgs = module.build_arm_messages(spec, preamble, turns,
                                         salt_for_turn=lambda n, s=seed: module.battery_salt(s, n))
        per[arm] = {"messages": msgs, "seed": seed,
                    "declared_policy": module.CompactionPolicy(spec["compaction"]).value,
                    "nodes": module.build_arm_messages.last_nodes.get(arm)}
    return per


def test_R6_real_arms():
    # (the same assembly phase_battery uses: policies + per-arm plans + renders)
    prompts = {a: v["messages"] for a, v in _per_arm().items()}
    rep = cell.arm_identity_report(_per_arm(cell))
    assert rep["ok"], json.dumps(rep)[:800]
    assert rep["min_distinct_prefix_sha256_per_turn"] >= 2, rep
    # D's two required facts: R (FORK) produces a different body set from A, and the
    # arms are separable per turn by the POSTed bytes and by their declared plan.
    assert rep["body_differs"].get("A_vs_R"), rep["body_differs"]
    assert rep["body_differs"].get("A_vs_C"), rep["body_differs"]
    assert rep["min_distinct_prefix_sha256_per_turn"] == len(cell.ARMS), rep
    assert rep["prompt_plan_differ"].get("A_vs_R") is True and rep["prompt_plan_differ"].get("A_vs_C") is True
    # A and H: same declared policy, different seed -> same BODIES, different DIGESTS,
    # and the only arm pair allowed to share a plan
    assert not rep["body_differs"]["A_vs_H"], rep["body_differs"]
    # A/H are NOT a seed replica: different seeds, so they are a POLICY replicate
    # pair only (same compaction policy, distinct bytes); the only arm pair allowed
    # to merge at the plan level is one sharing a declared policy.
    assert rep["expected_salt_merges"] == [["A", "H"]], rep["expected_salt_merges"]
    assert len({cell.battery_salt(3201), cell.battery_salt(3204)}) == 2, "A/H seeds collapsed"
    assert all(p["merged_arms_at_this_turn"] in ([["A", "H"]], []) for p in rep["per_turn_plans"]), \
        rep["per_turn_plans"][:2]
    digests = {a: {cell.messages_sha256(m) for m in msgs} for a, msgs in prompts.items()}
    assert digests["A"] != digests["H"], "A/H must differ by salt (different digests)"
    bodies = {a: {tuple(json.dumps(x, sort_keys=True) for x in m[1:]) for m in msgs}
              for a, msgs in prompts.items()}
    assert bodies["A"] == bodies["H"], "A/H are a salt replicate pair"
    assert bodies["R"] != bodies["A"], "R (FORK) must differ from A in body"
    got = {str(s["arm"]): cell.ARM_RENDER[cell.CompactionPolicy(s["compaction"])].value
           for s in cell.ARMS}
    assert got["R"] == "pointer_fork" and got["C"] == "naive_append", got
    # each arm really compacted, and R's fork marker is in its transcript
    events = cell.build_arm_messages.last_events
    assert set(events) == {"A", "C", "R", "H"}, events
    assert all(events[a] for a in events), events
    fork_turn = events["R"][0]["turn"]
    fork_text = " ".join(str(m["content"]) for m in prompts["R"][fork_turn - 1])
    assert "[fork]" in fork_text, "the FORK arm's provenance marker is missing"
    return {"identity_ok": rep["ok"],
            "min_distinct_sha_per_turn": rep["min_distinct_prefix_sha256_per_turn"],
            "per_turn_distinct": [p["distinct_prefix_sha256"] for p in rep["per_turn"]],
            "body_differs": rep["body_differs"],
            "render_policy_by_arm": got,
            "prompt_plan_differ": rep["prompt_plan_differ"],
           "salt_merge_pair": rep["expected_salt_merges"],
           "compaction_events": {a: len(v) for a, v in events.items()}}


# ------------------------------------------------------------------ repair E


def test_R7_analysis_guard():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rows_path = td / "rows.jsonl"
        rows = [{"model": "m", "config_id": "C", "arm": "A", "phase": "battery", "turn": 1,
                 "prompt_tokens": 100, "cached_tokens": 0, "usage_has_details": True},
                {"model": "m", "config_id": "C", "arm": "A", "phase": "battery", "turn": 2,
                 "prompt_tokens": 200, "cached_tokens": 100, "usage_has_details": True},
                {"model": "m", "config_id": "C", "arm": "A", "phase": "battery", "turn": 3,
                 "prompt_tokens": 300, "cached_tokens": 200, "usage_has_details": True}]
        rows_path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        digest = hashlib.sha256(rows_path.read_bytes()).hexdigest()
        ap = td / "analysis.json"
        # legacy stale analysis (no digests, different chain counts) -> refused
        ap.write_text(json.dumps({"m": {"arms": {"A": {"n": 2}}}}), encoding="utf-8")
        before = ap.read_bytes()
        g1 = cell.analysis_guard(rows_path, ap)
        assert g1["refused"] is True, g1
        assert ap.read_bytes() == before, "a refused analysis must not be touched"
        assert "legacy analysis predates the rows" in g1["why"][0], g1
        # fresh analysis stamped with what it was computed from -> admitted
        ap.write_text(json.dumps({"_source": {"rows_sha256": digest, "n_rows": 3,
                                              "submitted_rows_sha256": digest}}),
                      encoding="utf-8")
        g2 = cell.analysis_guard(rows_path, ap)
        assert g2["refused"] is False and g2["action"] == "write", g2
        # rows move under the analysis -> refused again
        rows_path.write_text(rows_path.read_text(encoding="utf-8")
                             + json.dumps(rows[0]) + "\n", encoding="utf-8")
        g3 = cell.analysis_guard(rows_path, ap)
        assert g3["refused"] is True, g3
        assert "rows moved under the analysis" in g3["why"][0], g3
        # force -> backup + separate write, original preserved byte for byte
        keep = ap.read_bytes()
        cell.FORCE["on"] = True
        try:
            g4 = cell.analysis_guard(rows_path, ap)
        finally:
            cell.FORCE["on"] = False
        assert g4["refused"] is False and g4["action"].startswith("forced"), g4
        assert ap.read_bytes() == keep, "force must not silently inherit the stale file"
        backup = Path(g4["backup"])
        assert backup.exists() and backup.read_bytes() == keep, g4
        # the REAL analysis.json on disk must be refused when it is stale vs rows.jsonl.
        # "Stale" is a FILE property, not a fixture: a fresh run may legitimately have
        # written a matching analysis (R2-VLLM-RERUN2 did, 236 rows) -- absence is also
        # admissible, because nothing can be stale against nothing.
        real = cell.analysis_guard(cell.ROWS_PATH, cell.ANALYSIS_PATH)
        real_before = (cell.ANALYSIS_PATH.read_bytes()
                       if cell.ANALYSIS_PATH.exists() else None)
        if real_before is None:
            assert cell.ANALYSIS_PATH.exists() is False, "the guard wrote an analysis"
        elif real.get("previous", {}).get("rows_sha256") == real["rows_sha256"]:
            assert real["refused"] is False, real
        else:
            assert real["refused"] is True, real
            assert cell.ANALYSIS_PATH.read_bytes() == real_before
        return {"fresh": g2["action"], "stale_refused": g1["refused"],
                "moved_refused": g3["refused"], "forced": g4["action"],
                "real_repo_refused": real["refused"],
                "real_repo_analysis_exists": real_before is not None,
                "real_repo_n_rows": real["n_rows"],
                "real_repo_prev_n_rows": (real.get("previous") or {}).get("n_rows")}


# -------------------------------------------- REPAIR2: the real send path offline
#
# WHY THESE EXIST.  R2-VLLM-REPAIR shipped 14/14 green while the live battery was
# broken: no check ever drove ``phase_battery`` through ``Runner.send``.  The live
# run then died at its FIRST battery request (``Runner.send() got an unexpected
# keyword argument 'extra'``) and, once that was patched, twice on the request cap
# (``arm cap reached for OH1: 219/200``).  Both defects are reachable offline, so
# both are checked below against the REAL ``phase_battery`` -- not a re-implementation.

BATTERY_ROW_KEYS = ("arm_compaction", "arm_render", "prompt_nodes")
PRE_BATTERY_FOOTPRINT = 54          # gate 2 + grid 14 + control? + tokens 32 + baseline 6
MEASURED_WORST_CONFIG_ROWS = 219    # logs/run.json: 'arm cap reached for OH1: 219/200'


class FakeChatClient:
    """In-memory stand-in for ``pmu16_cell.Client``: no httpx, no socket, no model."""

    def __init__(self):
        self.model = ""
        self.calls: list[list] = []

    def chat_full(self, messages, max_tokens=4, timeout=240.0) -> dict:
        self.calls.append(messages)
        return {"prompt_tokens": 1000 + len(messages), "cached": 0,
                "completion_tokens": 1, "usage_has_details": True,
                "ttft_ms": 1.0, "wall_ms": 2.0, "http_status": 200, "text": "ok"}

    def tokenize(self, messages, served_model=None):
        return None          # forces the row path, never the /tokenize probe


_MISSING = object()


def _drive_battery(mod, config_id="OH1", pre_rows=PRE_BATTERY_FOOTPRINT):
    with tempfile.TemporaryDirectory() as td:
        mod.ROWS_PATH = pathlib.Path(td) / "rows.jsonl"
        mod.ROWS_PATH.write_text("", encoding="utf-8")
        before = mod.ROWS_PATH.read_text(encoding="utf-8")
        if pre_rows:
            mod.ROWS_PATH.write_text("".join(
                json.dumps({"config_id": config_id, "phase": "grid", "request_index": i}) + "\n"
                for i in range(pre_rows)), encoding="utf-8")
        client = FakeChatClient()
        mod.RUNNER = mod.Runner({**mod.build_spec(config_id, *fake_inspects())["spec"],
                                 "config_id": config_id}, client)
        out = _capture_stdout(mod.phase_battery)
        rows = [json.loads(ln) for ln in mod.ROWS_PATH.read_text(encoding="utf-8").splitlines()
                if ln.strip()]
        return out, client, rows, before


def _capture_stdout(fn):
    """phase_battery prints one line per row; swallow it so the test log stays readable."""
    buf = io.StringIO()
    saved, sys.stdout = sys.stdout, buf
    try:
        out = fn()
    finally:
        sys.stdout = saved
    out = dict(out)
    out["_printed_rows"] = sum(1 for ln in buf.getvalue().splitlines() if ln.startswith("ROW "))
    return out


def prove_R8_real_battery_send_path(module=cell, allow_mutated=False):
    """R-transport proof 8.  Registered as ``test_R8_*`` below; named prove_* so the
    runner reaches it only through its module-aware wrapper.
    """
    """The check that catches defect (1): phase_battery must survive Runner.send.

    Drives the real phase_battery for all 4 arms x 2 passes through the real Runner
    and asserts the per-row payload survives the send path end to end.
    """
    # RESTORE WHAT THE DRIVE MUTATES.  ``_drive_battery`` points ``module.ROWS_PATH``
    # at a temp dir and replaces ``module.RUNNER``; leaving that behind made a LATER
    # red->green revert read the temporary (already deleted) rows path through the
    # live module and pass -- a false red in the harness, not in the cell.
    # The snapshot is taken BEFORE the drive for two reasons: the drive overwrites
    # these globals, and a module that has no ``ROWS_PATH`` key yet (a fresh exec'd
    # copy) must end the drive without one too, or it answers later checks from a
    # deleted temp dir.
    _saved = {k: module.__dict__.get(k, _MISSING) for k in ("ROWS_PATH", "RUNNER", "N_REQUESTS")}
    try:
        result, client, rows, _ = _drive_battery(module)
    finally:
        for k, v in _saved.items():
            if v is _MISSING:
                module.__dict__.pop(k, None)
            else:
                module.__dict__[k] = v
    bat = [r for r in rows if r.get("phase") == "battery"]
    # 1. it completes at all (defect 1 killed it at the FIRST request)
    assert result["turns"] == module.BATTERY_TURNS, result["turns"]
    # 2. every battery row carries the three extras -- on the ROW, through the real send
    missing = {k: sum(1 for r in bat if k not in r) for k in BATTERY_ROW_KEYS}
    assert not any(missing.values()), f"extra fields lost on the send path: {missing}"
    assert all(r["arm_compaction"] in {"append_note", "summarise_in_place", "fork"}
               for r in bat), {r["arm_compaction"] for r in bat}
    assert all(isinstance(r["prompt_nodes"], dict) and r["prompt_nodes"].get("turn") == r["turn"]
               for r in bat), "prompt_nodes is not the per-row node record"
    assert all(r["arm_render"] in {"pointer", "naive_append", "pointer_fork"} for r in bat)
    # 3. 4 arms x 2 passes x 16 turns, each arm/pass/turn exactly once
    arms = [str(s["arm"]) for s in module.ARMS]
    assert len(arms) == 4 and len({(r["arm"], r["rep"], r["turn"]) for r in bat}) == 128
    assert {r["arm"] for r in bat} == set(arms), {r["arm"] for r in bat}
    assert {r["rep"] for r in bat} == {0, 1}, {r["rep"] for r in bat}
    assert all(len([r for r in bat if r["arm"] == a and r["rep"] == p]) == module.BATTERY_TURNS
               for a in arms for p in (0, 1))
    per_turn = {}
    for r in bat:
        if r["rep"] == 0:
            per_turn.setdefault(r["turn"], set()).add(r["prefix_sha256"])
    assert sorted(per_turn) == list(range(1, module.BATTERY_TURNS + 1))
    assert all(len(v) == 4 for v in per_turn.values()), \
        f"expected 4 distinct prefix_sha256 per turn: { {k: len(v) for k, v in per_turn.items()} }"
    # 4. pass 1 salts distinct per turn; pass 2 re-sends pass-1 BYTES.  R5's row
    #    contract is applied to EVERY arm's filed salts here (one owner, two seats).
    contract = _r5_check(module=module, allow_mutated=True)
    for arm in arms:
        pass1_salts = [r["salt"] for r in bat if r["arm"] == arm and r["rep"] == 0]
        pass2_salts = [r["salt"] for r in bat if r["arm"] == arm and r["rep"] == 1]
        assert len(set(pass1_salts)) == module.BATTERY_TURNS, \
            f"{arm}: pass-1 salts are not distinct per turn: {sorted(set(pass1_salts))}"
        assert set(pass2_salts) == {module.battery_salt(int(next(
            s["seed"] for s in module.ARMS if str(s["arm"]) == arm)))}, \
            f"{arm}: pass 2 must file exactly the arm salt"
        assert not set(pass1_salts) & set(pass2_salts), f"{arm}: pass 1 reused the arm salt"
        assert contract["pass1_salts_distinct"], contract
        assert contract["pass1_salts_distinct_per_arm"], contract
    s1 = {r["turn"]: r["salt"] for r in bat if r["arm"] == "A" and r["rep"] == 0}
    assert len(set(s1.values())) == module.BATTERY_TURNS, "pass-1 salts are not distinct per turn"
    p1 = {(r["arm"], r["turn"]): r["prefix_sha256"] for r in bat if r["rep"] == 0}
    p2 = {(r["arm"], r["turn"]): r["prefix_sha256"] for r in bat if r["rep"] == 1}
    assert p1 == p2, "pass 2 must re-send exactly the pass-1 byte strings"
    # 5. exactly 128 rows, and 128 real requests went out
    assert len(bat) == 128, len(bat)
    assert len(client.calls) == 128, len(client.calls)
    assert result["_printed_rows"] == 128, result["_printed_rows"]
    return {"arms": arms, "passes": [0, 1], "battery_rows": len(bat),
            "extra_fields_present": all(not v for v in missing.values()),
            "distinct_prefix_sha256_per_turn": sorted({len(v) for v in per_turn.values()}),
            "pass1_salts_distinct": len(set(s1.values())),
            "pass2_equals_pass1": p1 == p2, "client_calls": len(client.calls)}


test_R8_real_battery_send_path = prove_R8_real_battery_send_path


def prove_R9_battery_budget_preflight(module=cell, allow_mutated=False):
    """R-transport proof 9.  Registered as ``test_R9_*`` below.
    """
    """The check that catches defect (2): a capped run must fail at ZERO cost."""
    pre = module.PRE_BATTERY_FOOTPRINT if hasattr(module, "PRE_BATTERY_FOOTPRINT") \
        else PRE_BATTERY_FOOTPRINT
    # (a) the real pre-battery footprint (54 rows) still fits and the battery completes
    result, client, rows, _ = _drive_battery(module, pre_rows=pre)
    bat = [r for r in rows if r.get("phase") == "battery"]
    assert len(bat) == 128, f"battery incomplete with {pre} pre-battery rows: {len(bat)}"
    assert len(client.calls) == 128, len(client.calls)
    needed = pre + 128
    assert needed <= module.ARM_REQUEST_CAP, (needed, module.ARM_REQUEST_CAP)
    # the measured live worst case (219 rows for a config that replayed its prefix) fits too
    assert MEASURED_WORST_CONFIG_ROWS <= module.ARM_REQUEST_CAP, \
        (MEASURED_WORST_CONFIG_ROWS, module.ARM_REQUEST_CAP)
    # (b) the arithmetic is exposed and named, not implicit in a send-loop
    assert module.battery_request_cost() == 2 * len(module.ARMS) * module.BATTERY_TURNS == 128
    # (c) a deliberately too-small cap must raise the NAMED error BEFORE any row/request
    saved_cap, saved_client, raised = module.ARM_REQUEST_CAP, None, None
    module.ARM_REQUEST_CAP = 100                       # cannot possibly hold 54 + 128
    try:
        with tempfile.TemporaryDirectory() as td:
            module.ROWS_PATH = pathlib.Path(td) / "rows.jsonl"
            module.ROWS_PATH.write_text("".join(
                json.dumps({"config_id": "OH1", "phase": "grid", "request_index": i}) + "\n"
                for i in range(pre)), encoding="utf-8")
            saved_client = FakeChatClient()
            module.RUNNER = module.Runner({**module.build_spec("OH1", *fake_inspects())["spec"],
                                           "config_id": "OH1"}, saved_client)
            before = module.ROWS_PATH.read_text(encoding="utf-8")
            try:
                _capture_stdout(module.phase_battery)
            except Exception as exc:                   # noqa: BLE001 - must be the named one
                raised = exc
            after = module.ROWS_PATH.read_text(encoding="utf-8")
            assert raised is not None, "a too-small cap did NOT raise -- it would starve mid-battery"
            assert type(raised).__name__ == "BatteryBudgetExceeded", repr(raised)
            assert "battery budget exceeded for OH1" in str(raised), str(raised)
            assert after == before, "the pre-flight wrote rows (or requests) before refusing"
            assert saved_client.calls == [], f"{len(saved_client.calls)} requests sent before refusing"
    finally:
        module.ARM_REQUEST_CAP = saved_cap
    # (d) the cap is satisfiable AND actually bounds: 260 is a real ceiling, not infinity
    assert module.ARM_REQUEST_CAP == 260, module.ARM_REQUEST_CAP
    return {"pre_battery_rows": pre, "battery_rows": len(bat), "needed": needed,
            "arm_cap": module.ARM_REQUEST_CAP, "headroom": module.ARM_REQUEST_CAP - needed,
            "measured_worst_config_rows": MEASURED_WORST_CONFIG_ROWS,
            "cost_expr": module.BATTERY_COST_EXPR, "cost": module.battery_request_cost(),
            "small_cap_error": type(raised).__name__,
            "small_cap_message": str(raised)[:160],
            "rows_written_before_refusal": 0, "requests_before_refusal": 0}


# -------------------------------------------------------- red->green harness

_SRC = (HERE / "pmu16_cell.py").read_text(encoding="utf-8")

# The red SHAPE each revert must produce: "assert" -- a check catches it; "type" -- a
# crash the live run actually died of (that crash IS the defect, not a check fault).
REVERT_EXPECT = {"extra_keyword_removed_from_Runner_send": "type"}

# RED->GREEN.  Each headline fix is reverted BEHAVIOURALLY on a copy of the module
# source (exec'd into a temp module): the two literal patterns that produced each
# defect (an empty ``extra`` list / a hardcoded ``RenderPolicy.NAIVE_APPEND``) no
# longer exist in the repaired source, so the revert reproduces their EFFECT.
REVERTS = {
    # repair A: the OH1/OH1L launch loses the accounting flag again -- the literal
    # empty ``extra`` list restored, and the flag dropped from the shared recipe.
    "flag_dropped_from_OH1": (
        [('"--reasoning-parser", "qwen3", "--trust-remote-code",\n'
          '    # REPAIR A: one legal way only.  The specs below carry this too, and\n'
          '    # build_spec de-duplicates, so the flag appears exactly once either way.\n'
          '    "--enable-prompt-tokens-details",\n]',
          '"--reasoning-parser", "qwen3", "--trust-remote-code",\n]'),
         ('"extra": ["--enable-prompt-tokens-details"]', '"extra": []')],
        "R1_flag_in_oh1_oh1l_a1_unchanged"),
    # repair D, behavioural revert: every arm is forced onto A's compaction policy
    # (the effect of the old hardcoded NAIVE_APPEND, which no longer exists as a
    # literal to drop).  The check must not be able to tell the arms apart.
    "arms_forced_to_one_policy": (
        [("    policy = CompactionPolicy(policy if policy is not None else spec[\"compaction\"])",
          "    policy = CompactionPolicy.APPEND_NOTE  # REVERTED: every arm is A")],
        "R6_real_arms"),
    # REPAIR2: defect 1 -- the live send path crashed on phase_battery's `extra=`.
    # REPAIR A, restated: the extra payload is silently discarded on the way to the
    # row -- exactly the re-run's crash, minus the TypeError wrapper.
    "extra_dropped_from_Runner_send": (
        [("                        request_index=self.n_rows() + 1, extra=extra)",
          "                        request_index=self.n_rows() + 1, extra=None)")],
        "test_R8_real_battery_send_path"),
    # REPAIR2: the same defect's LOUD half -- the keyword is gone from the signature, so
    # the battery dies on its FIRST row with `unexpected keyword argument 'extra'` and
    # writes nothing (the live re-run).  A signature edit alone is not enough: the
    # keyword use must be rebound to a positional slot, or the missing branch returns
    # through `extra=None` and the revert stays green.
    "extra_keyword_removed_from_Runner_send": (
        [('             note="", extra: dict | None = None) -> dict:',
          '             note="") -> dict:'),
         ("                        request_index=self.n_rows() + 1, extra=extra)",
          "                        request_index=self.n_rows() + 1)")],
        "test_R8_real_battery_send_path"),
    # REPAIR2: defect 2 -- the unsatisfiable per-config cap, and the missing pre-flight.
    "arm_cap_restored_to_200": (
        [("ARM_REQUEST_CAP = 260", "ARM_REQUEST_CAP = 200"),
         ('BATTERY_COST_EXPR = "2 * len(ARMS) * BATTERY_TURNS"',
          'BATTERY_COST_EXPR = "2 * len(ARMS) * BATTERY_TURNS"\n'
          'def battery_request_cost_unused():  # REVERTED: cost is not named\n'
          '    return 0')],
        "test_R9_battery_budget_preflight"),
    # REPAIR C -- the SALT the battery FILES.  (An earlier revert rewrote the call
    # site's expression; the rendered prompts are built from `salt_for_turn`, not from
    # that expression, so R5's byte evidence could not see it.  The one that matters
    # is `battery_salt` itself: without its per-turn seat pass 1 collapses to one arm
    # salt, which R5 detects both in the bytes and in `cold_salt_contract`.)
    "salt_collapsed_to_one_arm_salt": (
        [("    if turn is None:\n        return make_salt(int(seed))\n"
          "    return make_salt(int(seed) * 1000 + int(turn))",
          "    return make_salt(int(seed))  # REVERTED: one salt per arm on pass 1 too")],
        "R5_true_cold_pass"),
}




def _apply(source: str, subs) -> str:
    out = source
    for old, new in subs:
        assert old in out, f"revert pattern not found: {old[:60]!r}"
        out = out.replace(old, new, 1)
    return out


def red_green() -> dict:
    """REVERT each headline fix on a COPY of the source; the check must fail there."""
    out = {}
    for name, spec in REVERTS.items():
        subs, check_name = spec[0], spec[1]
        expect = REVERT_EXPECT.get(name, "assert")
        rec = {"reverted_by": [s[0][:50] for s in subs], "check": check_name,
               "expect": expect}
        try:
            mutated = _apply(_SRC, subs)
            mod = load_cell(source=mutated, name=f"pmu_cell_rev_{name}")
            try:
                _call_check(check_name, mod)
                rec["red"] = False
            except UnboundLocalError as exc:
                # the D2 revert re-execs the repaired source WITHOUT the local
                # `extra` binding, so the row construction can die before the TypeError
                # is even reached.  Both are the same defect; neither is a check fault.
                rec["red"] = expect == "type" and ("extra" in str(exc))
                rec["red_error"] = f"UNBOUND {exc}"
            except AssertionError as exc:
                rec["red"] = expect == "assert"
                rec["red_error"] = str(exc)[:300]
                if not rec["red"]:
                    rec["red_error"] = f"expected a {expect!r} red, got an assertion: {rec['red_error']}"
            except TypeError as exc:
                # "type" reverts reproduce a crash the live run died of (the re-run's
                # `Runner.send() got an unexpected keyword argument 'extra'`); any
                # other TypeError means the check could not take the module at all.
                rec["red"] = expect == "type" and "unexpected keyword argument" in str(exc)
                rec["red_error"] = f"TYPE {exc}"
        except Exception as exc:
            rec["red"] = None
            rec["red_error"] = f"SETUP {type(exc).__name__}: {exc}"[:300]
        try:
            _call_check(check_name, cell)
            rec["green"] = True
        except Exception as exc:
            rec["green"] = False
            rec["green_error"] = str(exc)[:300]
        out[name] = rec
    out["all_red_then_green"] = all(v.get("red") is True and v.get("green") is True
                                    for k, v in out.items() if k != "all_red_then_green")
    return out


# The two red->green targets must be parametrisable over a module, so they are
# re-declared here as module-aware wrappers (the plain tests call them with the
# live module).
C = {"globals": {}}
def _call_check(check_name, module, allow_mutated=True):
    """Invoke a registered check over ANY module: the live one or a mutated copy.

    ``C["globals"]`` is consulted FIRST.  The plain ``test_R5_*``/``prove_R5_*``
    functions close over the LIVE ``cell`` and ignore the ``module`` they are handed,
    so resolving them from ``globals()`` made a revert check the real cell and report
    green -- the whole point of the revert lost in a name resolution.  A plain
    function that takes ``module`` is no better: it reads ``cell`` internally.
    """
    fn = C["globals"].get(check_name) or globals().get(check_name)
    if fn is None:
        raise KeyError(check_name)
    if check_name in ("R8_real_battery_send_path", "test_R8_real_battery_send_path"):
        return _r8_check(module=module, allow_mutated=allow_mutated)
    if check_name in ("R9_battery_budget_preflight", "test_R9_battery_budget_preflight"):
        return _r9_check(module=module, allow_mutated=allow_mutated)
    return fn(module=module, allow_mutated=allow_mutated) if module is not cell else fn()


test_R9_battery_budget_preflight = prove_R9_battery_budget_preflight


# REPAIR2: these two checks drive the real phase_battery, so they are called through
# module-aware wrappers like the two REPAIR checks above -- one body, two modules.
def _r8_check(module=cell, allow_mutated=False):
    if module is cell and not allow_mutated:
        return prove_R8_real_battery_send_path()
    return prove_R8_real_battery_send_path(module=module, allow_mutated=allow_mutated)


def _r9_check(module=cell, allow_mutated=False):
    if module is cell and not allow_mutated:
        return prove_R9_battery_budget_preflight()
    return prove_R9_battery_budget_preflight(module=module, allow_mutated=allow_mutated)


def _r5_check(module=cell, allow_mutated=False):
    return prove_R5_true_cold_pass(module=module, allow_mutated=allow_mutated)


def _flag_check(module=cell, allow_mutated=False):
    if module is cell:
        return test_R1_flag_in_oh1_oh1l_a1_unchanged()
    for cid in ("OH1", "OH1L"):
        s = module.build_spec(cid, *fake_inspects())["spec"]
        n = s["cmd"].count("--enable-prompt-tokens-details")
        assert n == 1, f"{cid}: flag count {n}"
    assert "--enable-prompt-tokens-details" in module.OCCAMY_FLAGS
    a1 = module.build_spec("A1", *fake_inspects())["spec"]
    assert a1["cmd"].count("--enable-prompt-tokens-details") == 1
    return {"flag": True}


def _arms_check(module=cell, allow_mutated=False):
    rep = module.arm_identity_report(_per_arm(module))
    assert rep["ok"], f"arm identity collapsed: {json.dumps(rep)[:400]}"
    assert rep["body_differs"].get("A_vs_R"), rep["body_differs"]
    return {"identity_ok": rep["ok"], "body_differs": rep["body_differs"]}


C["globals"] = {"R1_flag_in_oh1_oh1l_a1_unchanged": _flag_check, "R6_real_arms": _arms_check,
                "R5_true_cold_pass": _r5_check}


# --------------------------------------------------------------------- driver


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out_json = None
    if "--json" in argv:
        out_json = Path(argv[argv.index("--json") + 1])
    results, fails = {}, []
    globs = dict(globals())
    for name in sorted([n for n in globs if n.startswith("test_")]):
        fn = globs[name]
        if name == "test_R1_flag_in_oh1_oh1l_a1_unchanged":
            fn = _flag_check
        elif name == "test_R6_real_arms":
            fn = _arms_check
        elif name == "test_R8_real_battery_send_path":
            fn = _r8_check
        elif name == "test_R9_battery_budget_preflight":
            fn = _r9_check
        try:
            detail = fn()
            results[name] = {"ok": True, "detail": detail}
            print("ok", name, flush=True)
        except Exception as exc:
            results[name] = {"ok": False, "error": repr(exc),
                             "trace": traceback.format_exc()[-1200:]}
            fails.append(name)
            print("FAIL", name, repr(exc), flush=True)
    rg = red_green()
    for k, v in rg.items():
        if k != "all_red_then_green":
            print(f"red->green {k}: red={v.get('red')} green={v.get('green')} "
                  f"{v.get('red_error', '')[:120]}", flush=True)
    if not rg["all_red_then_green"]:
        fails.append("red_green")
    verdict = {"unit": "R2-VLLM-REPAIR", "selftest": "selftest_offline.py",
               "pass": len(results) - sum(1 for v in results.values() if not v["ok"]),
               "fail": sum(1 for v in results.values() if not v["ok"]),
               "n_checks": len(results), "failed": fails,
               "checks": results, "red_green": rg,
               "network": {"httpx_imported_real": False,
                           "note": "httpx aliased to a stand-in that raises on Client(); "
                                   "no socket, ssh or docker call site is executed"}}
    print(f"SUMMARY pass={verdict['pass']} fail={verdict['fail']} "
          f"red_green={rg['all_red_then_green']}", flush=True)
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
        print("wrote", out_json, flush=True)
    return 0 if not fails else 1


def _selfcheck():
    """The two red->green targets must be callable over any module."""
    assert _flag_check(module=cell)["flag"] is True
    assert _arms_check(module=cell)["identity_ok"] is True


# Shapes of the revert patterns, asserted at import: a revert that no longer
# matches the source would make its red->green vacuously "red".
for _name, (_subs, _check) in REVERTS.items():
    for _old, _new in _subs:
        assert _old in _SRC, f"revert pattern drifted from the source: {_name}: {_old[:60]!r}"


if __name__ == "__main__":
    raise SystemExit(main())
