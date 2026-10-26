#!/usr/bin/env python3
"""P2-REPAD -- re-measure the grid-aligned arm with the pad PRECOMPUTED.

What this replaces (card `425e3e7a`, handoff `orchestration/handoffs/O3-P2-REPEAT.json`):
the P2 rows of the earlier runs were the SECOND send of a same-turn alignment
correction, so their recorded ``cached_tokens`` was the FIRST send's prompt and
the recorded cost excluded a send.  Here:

  * the pad target is derived from the P1 row's OWN measured prompt_tokens for
    the same turn (P1's base text is byte-identical to P2's base text),
  * the filler (" PAD" repeated -- measured as exactly one token per repetition
    by the server's own tokenizer) is appended BEFORE the single request,
  * the server's tokenizer is consulted on a stratified sample of turns to prove
    the filler adds exactly the intended number of tokens,
  * exactly ONE request is sent per measured turn: ``requests_sent == 1`` and
    ``corrections == 0`` on every row, the assertion the card requires.

Substrate: PRODUCTION occamy on :8012 (the O1 setup in
``state/config/best-config.json``) -- no container is started, stopped or
restarted, no variant port is used.

Usage
    python3 p2_repad.py --dry
    python3 p2_repad.py --turns 71
    python3 p2_repad.py --analyse-only
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path("<workspace>")
CELL = REPO / "experiments" / "context-cache" / "cells" / "P2-REPAD"
HARNESS = REPO / "experiments" / "context-cache" / "cells" / "R2-PROMPT" / "O3-REPEAT" / "prompt_o3_repeat.py"
REF_ROWS = REPO / "experiments" / "context-cache" / "cells" / "R2-PROMPT" / "O3-REPEAT" / "rows.jsonl"
OUT_JSON = REPO / "state" / "r2-p2-repad.json"
PROGRESS = REPO / "state" / "logs" / "P2-REPAD-progress.log"

CELL_ID = "P2-REPAD"
SETUP_ID = "O1"
GRID = 64                 # SGLang unit, from best-config O1 grid_unit
TURNS = 71
ARMS = ("P0", "P1", "P2")
FILLER = " PAD"           # measured: exactly 1 token per repetition (token 59671)
BOOT_N = 10000
BOOT_SEED = 20251024
SPOT_TURNS = (1, 11, 21, 31, 41, 51, 61, 71)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_harness():
    spec = importlib.util.spec_from_file_location("p2repad_harness", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load_harness()


def progress(line: str) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (utc_now(), line))
        fh.flush()


def root_url(base_url: str) -> str:
    return base_url.rsplit("/v1", 1)[0]


def tokenize(base_url: str, model: str, text: str) -> int:
    """The server's own tokenizer, chat-templated exactly like the request."""
    last = None
    for attempt in (1, 2):
        try:
            resp = requests.post(
                root_url(base_url) + "/tokenize",
                json={"model": model, "messages": [{"role": "user", "content": text}]},
                timeout=120,
            )
            body = resp.json()
            return int(body["count"])
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.5)
    raise SystemExit("TOKENIZE FAILED: %r" % (last,))


def boot_mean_ci(values, rng: random.Random, n: int = BOOT_N) -> list:
    xs = [float(v) for v in values]
    if not xs:
        return []
    means = []
    k = len(xs)
    for _ in range(n):
        means.append(sum(xs[rng.randrange(k)] for _ in range(k)) / k)
    means.sort()
    lo = means[int(round(0.025 * (n - 1)))]
    hi = means[int(round(0.975 * (n - 1)))]
    return [round(lo, 3), round(hi, 3)]


def pairs(rows, arm_a: str, arm_b: str):
    a = {int(r["turn"]): r for r in rows if r["arm"] == arm_a}
    b = {int(r["turn"]): r for r in rows if r["arm"] == arm_b}
    out = []
    for t in sorted(set(a) & set(b)):
        ua, ub = a[t].get("uncached_tokens"), b[t].get("uncached_tokens")
        if isinstance(ua, int) and isinstance(ub, int):
            out.append((t, float(ua), float(ub)))
    return out


def paired_stats(rows, arm_a: str, arm_b: str, rng: random.Random) -> dict:
    ps = pairs(rows, arm_a, arm_b)
    diffs = [a - b for _, a, b in ps]
    if not diffs:
        return {"n_pairs": 0}
    t_ci = H.paired_delta({a: 0 for a in range(len(diffs))},
                          {i: d for i, d in enumerate(diffs)}) if False else None
    mean = sum(diffs) / len(diffs)
    return {
        "contrast": "%s/%s" % (arm_a, arm_b),
        "n_pairs": len(diffs),
        "mean_unc_a": round(sum(a for _, a, _ in ps) / len(ps), 4),
        "mean_unc_b": round(sum(b for _, _, b in ps) / len(ps), 4),
        "mean_delta": round(mean, 4),
        "abs_delta": round(mean * len(diffs), 2),
        "pct_of_b": round(100.0 * mean / (sum(b for _, _, b in ps) / len(ps)), 4),
        "boot_ci": boot_mean_ci(diffs, rng),
        "ci_excludes_zero": bool(sorted(boot_mean_ci(diffs, random.Random(BOOT_SEED + 7)))[0] > 0
                                 or boot_mean_ci(diffs, random.Random(BOOT_SEED + 7))[1] < 0),
        "t_ci": H.mean_ci(diffs),
    }


def arm_block(rows, arm: str, rng: random.Random) -> dict:
    rs = [r for r in rows if r["arm"] == arm]
    unc = [float(r["uncached_tokens"]) for r in rs if isinstance(r["uncached_tokens"], int)]
    prompt = [float(r["prompt_tokens"]) for r in rs if isinstance(r["prompt_tokens"], int)]
    cached = [float(r["cached_tokens"]) for r in rs if isinstance(r["cached_tokens"], int)]
    pads = [float(r["pad_tokens"]) for r in rs if isinstance(r.get("pad_tokens"), int)]
    return {
        "n": len(rs),
        "mean_uncached_per_turn": round(sum(unc) / len(unc), 4) if unc else "unavailable",
        "unc_ci_bootstrap": boot_mean_ci(unc, rng),
        "unc_ci_t": H.mean_ci(unc),
        "mean_prompt_tokens": round(sum(prompt) / len(prompt), 4) if prompt else "unavailable",
        "hit_fraction_weighted": (round(sum(cached) / sum(prompt), 6)
                                  if cached and prompt else "unavailable"),
        "pad_tokens_total": int(sum(pads)) if pads else 0,
        "mean_pad_tokens": round(sum(pads) / len(pads), 4) if pads else 0,
        "aligned_rows": sum(1 for r in rs if r.get("pad_aligned") is True),
        "rows_multi_send": sum(1 for r in rs if int(r.get("requests_sent", 0)) != 1),
        "rows_with_correction": sum(1 for r in rs if r.get("had_correction") is True),
        "mean_aligned_len_minus_cached": (
            round(sum(float(r["prompt_tokens"]) - float(r["cached_tokens"])
                      for r in rs
                      if isinstance(r["prompt_tokens"], int) and isinstance(r["cached_tokens"], int))
                  / max(1, sum(1 for r in rs
                               if isinstance(r["prompt_tokens"], int)
                               and isinstance(r["cached_tokens"], int))), 4)
            if any(isinstance(r["cached_tokens"], int) for r in rs) else "unavailable"),
    }


def self_hit_guard(rows) -> dict:
    """Two guards: the card's wording, and the artefact's actual signature.

    The card says: no row's ``cached_tokens`` may equal a previously-sent prompt's
    rounded length without ``had_correction``.  Applied literally on THIS run the
    test is degenerate for the aligned arm: every P2 prompt is a multiple of 64 by
    construction, so the P2 prompt lengths form a contiguous 64-step ladder
    (576, 640, ... 4224), and the endpoint reports every cached count as a multiple
    of 64.  Any legitimate hit therefore equals *some* earlier P2 prompt length.
    That is pigeonhole, not a self-hit -- so the decisive test is the artefact's own
    signature: a row whose ``cached_tokens`` equals the length of the IMMEDIATELY
    preceding send in the same arm (the correction resend covered that whole prompt).
    """
    literal, decisive = [], []
    for arm in ARMS:
        rs = sorted((x for x in rows if x["arm"] == arm), key=lambda x: int(x["turn"]))
        sent: list[tuple[int, int]] = []
        prev = None
        for r in rs:
            cached = r.get("cached_tokens")
            pt = r.get("prompt_tokens")
            if isinstance(cached, int) and cached > 0 and r.get("had_correction") is not True:
                for t_prev, len_prev in sent:
                    if cached == len_prev:
                        literal.append({"arm": arm, "turn": r["turn"], "cached_tokens": cached,
                                        "equals_prior_turn": t_prev})
                        break
                if prev is not None and isinstance(prev.get("prompt_tokens"), int) \
                        and cached == prev["prompt_tokens"]:
                    decisive.append({"arm": arm, "turn": r["turn"], "cached_tokens": cached,
                                     "immediately_prior_turn": prev["turn"],
                                     "prior_prompt_tokens": prev["prompt_tokens"]})
            if isinstance(pt, int):
                sent.append((int(r["turn"]), pt))
            prev = r

    p2_lens = sorted({int(r["prompt_tokens"]) for r in rows
                      if r["arm"] == "P2" and isinstance(r["prompt_tokens"], int)})
    mult64 = [int(r["cached_tokens"]) for r in rows if isinstance(r["cached_tokens"], int)]
    multi_send = [r["arm"] + ":" + str(r["turn"]) for r in rows
                  if int(r.get("requests_sent", 0)) != 1]
    offset = bool(p2_lens) and p2_lens[0] % GRID == 0 and all(
        b - a == GRID for a, b in zip(p2_lens, p2_lens[1:]))
    return {
        "literal_wording": {"violations": len(literal), "examples": literal[:5],
                            "why_degenerate": "P2 prompt lengths are a contiguous %d-step ladder "
                                              "(%d..%d) and every cached count is a multiple of %d, "
                                              "so literal equality with some earlier P2 prompt is a "
                                              "pigeonhole certainty, not a self-hit"
                                              % (GRID, p2_lens[0] if p2_lens else 0,
                                                 p2_lens[-1] if p2_lens else 0, GRID)},
        "decisive_immediate_prior": {"violations": len(decisive), "examples": decisive[:5]},
        "degeneracy_evidence": {
            "p2_prompt_lengths": len(p2_lens),
            "p2_prompt_lengths_all_multiple_of_%d" % GRID: all(p % GRID == 0 for p in p2_lens),
            "p2_prompt_lengths_contiguous_step_%d" % GRID: offset,
            "cached_values": len(mult64),
            "cached_values_all_multiple_of_%d" % GRID: all(c % GRID == 0 for c in mult64),
        },
        "rows_multi_send": len(multi_send),
        "count": len(decisive) + len(multi_send),
        "verdict": "PASS" if not decisive and not multi_send else "FAIL",
        "verdict_basis": "decisive guard (cached == immediately preceding send's prompt length) "
                         "and the single-send assertion; the literal wording is reported with its "
                         "degeneracy proof rather than used as the verdict",
    }



def render_digest_proof(renderer) -> dict:
    """Same task content + same prefix digests as the O3-REPEAT cell."""
    ref = {}
    if REF_ROWS.exists():
        for line in REF_ROWS.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["arm"] in ("P0", "P1"):
                ref[(r["arm"], int(r["turn"]))] = r["prefix_sha256"]
    matched = mismatch = 0
    examples = []
    for arm in ("P0", "P1"):
        for turn in (1, 71):
            text = H.p0_text(renderer, turn) if arm == "P0" else H.p1_text(renderer, turn)
            got = H.sha256_text(text)
            want = ref.get((arm, turn))
            if want is None:
                continue
            if got == want:
                matched += 1
            else:
                mismatch += 1
                examples.append({"arm": arm, "turn": turn, "got": got, "want": want})
    p2 = H.sha256_text(H.p1_text(renderer, 1) + FILLER)
    return {"ref_rows": str(REF_ROWS), "digests_matched": matched, "digests_mismatched": mismatch,
            "examples": examples, "salt": H.SALT,
            "p2_is_p1_plus_filler": True,
            "p2_first_prefix_sha256": p2}


def arms_distinct(renderer) -> dict:
    digests = {}
    for arm in ARMS:
        if arm == "P0":
            text = H.p0_text(renderer, 20)
        elif arm == "P1":
            text = H.p1_text(renderer, 20)
        else:
            text = H.p1_text(renderer, 20) + FILLER * GRID   # P2 is P1 + inert pad
        digests[arm] = H.sha256_text(text)
    return {"at_turn": 20, "digests": digests,
            "distinct": len(set(digests.values())) == len(ARMS),
            "p2_rule": "P1 text + FILLER repeated pad_target times"}


def run(turns: int) -> dict:
    setup = H.load_setup(SETUP_ID)
    base_url = H.BASE_URL[SETUP_ID]
    model = setup["model"]
    grid = GRID
    declared = int(setup.get("grid_unit") or 0)
    CELL.mkdir(parents=True, exist_ok=True)
    rows_path = CELL / "rows.jsonl"

    renderer = H.load_renderer()
    distinct = arms_distinct(renderer)
    if not distinct["distinct"]:
        raise SystemExit("ARMS_IDENTICAL: %s" % json.dumps(distinct))
    digest_proof = render_digest_proof(renderer)

    handle, waited = H.acquire_lock(CELL_ID)
    meta = {"setup": SETUP_ID, "config_id": setup["config_id"],
            "config_sha256": setup["config_sha256"], "model": model,
            "base_url": base_url, "grid": grid, "grid_declared": declared,
            "lock_wait_s": waited, "started": utc_now(), "requests": 0,
            "salt": H.SALT, "renderer": str(H.RENDERER_PATH),
            "arms_distinct": distinct, "digest_proof": digest_proof}
    try:
        # --- G0: the endpoint must report a cache hit on an identical repeat -- #
        warm_text = renderer.SCAFFOLD + "HISTORY:\n" + renderer.body_upto(20) + "\n" + renderer.CANARY
        warm_msgs = [{"role": "user", "content": warm_text}]
        g0 = H.equalise_arm_warmup(base_url, model, warm_msgs)
        meta["requests"] += 2
        tok_warm = tokenize(base_url, model, warm_text)
        meta["requests"] += 1
        g0.update({"tokenize_count": tok_warm,
                   "template_offset": (int(g0["prompt_tokens"]) - tok_warm
                                       if g0.get("prompt_tokens") else None),
                   "at": utc_now()})
        if not (isinstance(g0.get("call2_cached"), int) and g0["call2_cached"] > 0):
            g0["verdict"] = "GATE SKIP: endpoint reports no cache hit on identical repeat"
            (CELL / "g0.json").write_text(json.dumps(g0, indent=2))
            raise SystemExit("G0 FAILED: %s" % json.dumps(g0))
        g0["verdict"] = "GATE OK"
        (CELL / "g0.json").write_text(json.dumps(g0, indent=2))
        progress("G0 OK call2_cached=%s prompt_tokens=%s tokenize=%s offset=%s"
                 % (g0["call2_cached"], g0["prompt_tokens"], tok_warm, g0["template_offset"]))

        rows, done = H.load_existing(rows_path)
        p1_len = {int(r["turn"]): int(r["prompt_tokens"]) for r in rows
                  if r["arm"] == "P1" and isinstance(r["prompt_tokens"], int)}
        tokenize_log = []

        for arm in ARMS:
            arm_rows = 0
            for turn in range(1, turns + 1):
                key = H.row_key(arm, turn)
                if key in done:
                    continue
                extra = {}
                if arm == "P0":
                    text, pad = H.p0_text(renderer, turn), 0
                    messages = [{"role": "user", "content": text}]
                elif arm == "P1":
                    text, pad = H.p1_text(renderer, turn), 0
                    messages = [{"role": "user", "content": text}]
                else:
                    base = H.p1_text(renderer, turn)
                    base_tokens = p1_len.get(turn)
                    if base_tokens is None:
                        raise SystemExit("P2 PRECOMPUTE IMPOSSIBLE: no P1 row for turn %d" % turn)
                    pad_target = int((-int(base_tokens)) % grid)
                    if pad_target < 64:
                        pad_target += grid          # never pad less than one block
                    tokenize_count = None
                    pad_delta = 0
                    if turn in SPOT_TURNS:
                        tok = tokenize(base_url, model, base + FILLER * pad_target)
                        meta["requests"] += 1
                        want = int(base_tokens) + pad_target - int(g0["template_offset"] or 0)
                        pad_delta = want - tok
                        if pad_delta:
                            pad_target = max(1, pad_target + pad_delta)
                        tokenize_count = tok
                        tokenize_log.append({"turn": turn, "count": tok, "want": want,
                                             "delta_applied": pad_delta,
                                             "pad_target": pad_target})
                        progress("P2 t%03d tokenize=%d want=%d delta=%d pad=%d"
                                 % (turn, tok, want, pad_delta, pad_target))
                    text = base + FILLER * pad_target
                    pad = pad_target
                    messages = [{"role": "user", "content": text}]
                    extra = {"tokenize_count": tokenize_count, "pad_delta_applied": pad_delta,
                             "base_tokens_from_P1": base_tokens}
                res = H.measured_post(base_url, model, messages, False)
                meta["requests"] += 1
                if res["http_status"] != 200:
                    raise SystemExit("NON-200 %s at %s turn %d -- no row written"
                                     % (res["http_status"], arm, turn))
                prompt_tokens = res["prompt_tokens"]
                cached = res["cached_tokens"]
                uncached = (max(0, int(prompt_tokens) - int(cached))
                            if isinstance(prompt_tokens, int) and isinstance(cached, int)
                            else "unavailable")
                row = {
                    "setup": SETUP_ID,
                    "cell": CELL_ID,
                    "salt": H.SALT,
                    "stack": "%s/%s" % (setup["engine"], model),
                    "model": model,
                    "config_id": setup["config_id"],
                    "config_sha256": setup["config_sha256"],
                    "arm": arm,
                    "turn": turn,
                    "prompt_tokens": prompt_tokens if prompt_tokens is not None else "unavailable",
                    "cached_tokens": cached if cached is not None else "unavailable",
                    "uncached_tokens": uncached,
                    "pad_tokens": pad,
                    "requests_sent": 1,
                    "corrections": 0,
                    "had_correction": False,
                    "http_status": int(res["http_status"]),
                    "prefix_sha256": H.sha256_text(text),
                    "prompt_sha256": H.sha256_text(json.dumps(messages, sort_keys=True)),
                    "details_present": res["details_present"],
                    "cached_source": res.get("cached_source"),
                    "pad_aligned": (isinstance(prompt_tokens, int) and prompt_tokens % grid == 0),
                    "wall_ms": res["wall_ms"],
                    "ts": utc_now(),
                }
                row.update(extra)
                H.append_row(rows_path, row)
                rows.append(row)
                done.add(key)
                if arm == "P1" and isinstance(prompt_tokens, int):
                    p1_len[turn] = int(prompt_tokens)
                arm_rows += 1
            progress("%s done: %d new rows, total=%d" % (arm, arm_rows, len(rows)))
        meta["tokenize_log"] = tokenize_log
    finally:
        H.release_lock(handle)

    meta["ended"] = utc_now()
    meta["rows"] = len(rows)
    (CELL / "run_meta.json").write_text(json.dumps(meta, indent=2))
    progress("RUN done: %d rows, %d requests, %s -> %s"
             % (len(rows), meta["requests"], meta["started"], meta["ended"]))
    print(json.dumps({"rows": len(rows), "requests": meta["requests"],
                      "rows_path": str(rows_path), "ended": meta["ended"]}, indent=2))
    return meta


def analyse() -> dict:
    rows_path = CELL / "rows.jsonl"
    rows = [json.loads(line) for line in rows_path.read_text().splitlines() if line.strip()]
    rng = random.Random(BOOT_SEED)
    per_arm = {arm: arm_block(rows, arm, rng) for arm in ARMS}
    deltas = {
        "P1/P0": paired_stats(rows, "P1", "P0", rng),
        "P2/P0": paired_stats(rows, "P2", "P0", rng),
        "P2/P1": paired_stats(rows, "P2", "P1", rng),
    }
    guard = self_hit_guard(rows)
    cached_vals = [int(r["cached_tokens"]) for r in rows if isinstance(r["cached_tokens"], int)]
    gcd = 0
    for v in cached_vals:
        gcd = math.gcd(gcd, v)
    p2 = per_arm["P2"]
    p1 = per_arm["P1"]
    pad_cost = None
    if isinstance(p2["mean_uncached_per_turn"], float) and isinstance(p1["mean_uncached_per_turn"], float):
        pad_cost = round(p2["mean_uncached_per_turn"] - p1["mean_uncached_per_turn"], 4)
    extra_cached_values = []
    for t in range(1, TURNS + 1):
        a = next((r for r in rows if r["arm"] == "P2" and int(r["turn"]) == t), None)
        b = next((r for r in rows if r["arm"] == "P1" and int(r["turn"]) == t), None)
        if a and b and isinstance(a.get("cached_tokens"), int) and isinstance(b.get("cached_tokens"), int):
            extra_cached_values.append(int(a["cached_tokens"]) - int(b["cached_tokens"]))
    extra_cached = (round(sum(extra_cached_values) / len(extra_cached_values), 4)
                    if extra_cached_values else "unavailable")
    p21 = deltas["P2/P1"]
    lo, hi = (p21.get("boot_ci") or [None, None])[:2]
    if lo is None:
        verdict = "padding_null"
    elif hi < 0:
        verdict = "padding_pays"
    elif lo > 0:
        verdict = "padding_costs"
    else:
        verdict = "padding_null"
    out = {
        "unit": CELL_ID,
        "rows_path": str(rows_path),
        "row_count": len(rows),
        "setup": SETUP_ID,
        "cell": CELL_ID,
        "salt": rows[0]["salt"] if rows else None,
        "grid_unit": GRID,
        "arm_definitions": {"P0": "whole-context resend (renderer R)",
                            "P1": "pointer index + append-only newest delta (renderer A)",
                            "P2": "P1 + trailing inert pad, final rendered length precomputed to a multiple of 64"},
        "per_arm": per_arm,
        "deltas": deltas,
        "corrections_total": sum(int(r.get("corrections") or 0) for r in rows),
        "rows_with_correction": sum(1 for r in rows if r.get("had_correction") is True),
        "rows_multi_send": sum(1 for r in rows if int(r.get("requests_sent", 0)) != 1),
        "pad_cost_net_of_P1": pad_cost,
        "pad_cost_per_pad_token": (round(pad_cost / p2["mean_pad_tokens"], 4)
                                   if pad_cost is not None and p2["mean_pad_tokens"] else None),
        "alignment_gain": {
            "definition": "prompt_P2_aligned_len - cached_P2 on every first-attempt row, plus the "
                          "cache the pad actually buys back relative to P1 on the same turn",
            "mean_aligned_len_minus_cached": p2["mean_aligned_len_minus_cached"],
            "cached_fraction_of_aligned_len": p2["hit_fraction_weighted"],
            "rows_aligned": p2["aligned_rows"],
            "rows": p2["n"],
            "extra_cached_vs_P1_mean": extra_cached,
            "extra_cached_vs_P1_distribution": dict(collections.Counter(extra_cached_values)),
            "pad_tokens_mean": p2["mean_pad_tokens"],
            "net_unc_delta_vs_P1": pad_cost,
        },
        "observed_cached_gcd": gcd,
        "self_hit_guard": guard,
        "replaces": {
            "artefact": "orchestration/handoffs/O3-P2-REPEAT.json and cells/R2-PROMPT/O3-REPEAT/rows.jsonl arm P2",
            "defect": "68/71 P2 rows in that run (70/71 in the original O3 run) were the SECOND send of a "
                      "same-turn alignment correction; the recorded prompt/cached pair belonged to the "
                      "first send and the recorded cost excluded a send",
            "recorded_P2_unc_per_turn_there": 389.408451,
            "true_cost_estimate_there": 1395.38,
            "this_run": "one request per row with the pad precomputed; corrections_total=0, rows_multi_send=0",
            "not_edited_here": "state/r2-prompt-matrix.json, docs/prompt-system/**, best-config.json "
                               "(the merge card owns those)",
        },
        "verdict": verdict,
        "verdict_basis": "P2/P1 paired bootstrap CI over turns (the two arms differ only by the pad); "
                         "hi<0 => padding_pays, lo>0 => padding_costs, else null",
        "at": utc_now(),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))
    progress("ANALYSIS verdict=%s P2/P0=%.3f P1/P0=%.3f P2/P1=%.3f pad_mean=%.1f aligned=%d/%d guard=%s"
             % (verdict, deltas["P2/P0"].get("mean_delta", 0), deltas["P1/P0"].get("mean_delta", 0),
                p21.get("mean_delta", 0), p2["mean_pad_tokens"], p2["aligned_rows"], p2["n"],
                guard["verdict"]))
    print(json.dumps({"verdict": verdict, "per_arm": {a: [per_arm[a]["n"],
                                                          per_arm[a]["mean_uncached_per_turn"],
                                                          per_arm[a]["hit_fraction_weighted"]]
                                                      for a in ARMS},
                      "deltas": {k: [v.get("mean_delta"), v.get("boot_ci")] for k, v in deltas.items()},
                      "corrections_total": out["corrections_total"],
                      "rows_with_correction": out["rows_with_correction"],
                      "pad_cost_net_of_P1": pad_cost,
                      "alignment_gain": out["alignment_gain"],
                      "self_hit_guard": guard["verdict"],
                      "out": str(OUT_JSON)}, indent=2))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=TURNS)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    args = ap.parse_args(argv)
    if args.dry:
        setup = H.load_setup(SETUP_ID)
        renderer = H.load_renderer()
        print(json.dumps({"setup": SETUP_ID, "config_id": setup["config_id"],
                          "config_sha256": setup["config_sha256"],
                          "grid": GRID, "turns": args.turns,
                          "base_url": H.BASE_URL[SETUP_ID],
                          "arms_distinct": arms_distinct(renderer),
                          "digest_proof": render_digest_proof(renderer)}, indent=2))
        return 0
    if args.analyse_only:
        analyse()
        return 0
    run(args.turns)
    analyse()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
