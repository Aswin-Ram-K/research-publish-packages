#!/usr/bin/env python3
"""UNIT MISS-LAW-2 stage 2 -- pin the residue-{0,1} avalanche and the mechanism of the +B term.

Stage 1 (probe2.py) showed
  * instrument B (request_prefill_kv_computed_tokens) agrees with instrument A exactly,
    so it restates A rather than corroborating it;
  * server TTFT (vllm:time_to_first_token_seconds, per request) is an independent timing
    observable that steps hard at the block multiple;
  * cached = (floor(P1/B)-1)*B for P1 mod B >= 2, but cached = 0 (whole prompt re-billed)
    at P1 mod B in {0,1} -- i.e. vLLM ALSO avalanches, which MISS-LAW attributes to SGLang only.

This stage answers two questions stage 1 left open:
  1. Is the avalanche residue-based (P1 mod B in {0,1}) or a one-off at 7392?
     -> fresh P1 = 6337 (res 1) and 8449 (res 1): two more block indices.
  2. At an avalanche cell, did the PRIME insert its blocks at all?
     -> after the prime, re-send the IDENTICAL message list (no append). If cached > 0 the
        blocks are resident and the failure is in matching across the append; if cached = 0
        the prime itself stored nothing.
Also records CLIENT wall-clock (non-stream, max_tokens=1) next to the server TTFT, so the
timing instrument has a second, host-side reading.

All cell keys carry an "r2_" prefix so nonces differ from stage 1 and every prime is cold.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("p2", os.path.join(HERE, "probe2.py"))
p2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p2)

OUT = os.path.join(HERE, "rows.jsonl")
B = p2.B


def chat_plain(messages, max_tokens=1):
    body = {"model": p2.MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0.0}
    t = time.time()
    j, err = None, None
    for _ in range(2):
        try:
            j = p2.ml.http_json(p2.BASE + "/v1/chat/completions", body, timeout=600)
            err = None
            break
        except Exception as e:                            # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:250]}"
            time.sleep(2)
    return (j or {}).get("usage") or {}, time.time() - t, err


def one(fd, *, pair_id, cell, role, rep=0, round_=0, messages, P1=None, notes=""):
    pre = p2.snap()
    usage, el, err = chat_plain(messages)
    post = p2.snap()
    pt = usage.get("prompt_tokens")
    kvc = int(round(p2.dd(post, pre, p2.K_KV + p2.HS)))
    kvn = int(round(p2.dd(post, pre, p2.K_KV + p2.HC)))
    ttfs = p2.dd(post, pre, p2.K_TTFT + p2.HS)
    ttfn = int(round(p2.dd(post, pre, p2.K_TTFT + p2.HC)))
    cached = int(round(p2.dd(post, pre, p2.K_CACHED)))
    row = {
        "pair_id": pair_id, "cell": cell, "role": role, "rep": rep, "round": round_, "stage": 2,
        "P1_target": None, "P1": P1, "prompt_tokens": pt,
        "L_app": (None if (pt is None or P1 is None) else pt - P1),
        "prompt_tokens_details": usage.get("prompt_tokens_details", "ABSENT"),
        "cached_tokens": cached,
        "prefix_cache_hits_delta": int(round(p2.dd(post, pre, p2.K_HITS))),
        "prefix_cache_queries_delta": int(round(p2.dd(post, pre, p2.K_QUER))),
        "prompt_tokens_total_delta": int(round(p2.dd(post, pre, p2.K_PTOT))),
        "by_source_local_cache_hit": int(round(p2.dd(post, pre, p2.K_SRC % "local_cache_hit"))),
        "by_source_local_compute": int(round(p2.dd(post, pre, p2.K_SRC % "local_compute"))),
        "by_source_external": int(round(p2.dd(post, pre, p2.K_SRC % "external_kv_transfer"))),
        "kvcomp_sum_delta": kvc, "kvcomp_count_delta": kvn,
        "kvcomp_bucket_le": p2.bucket_of(p2.bucket_delta(post, pre, p2.K_KV), kvn),
        "ttft_server_s": (round(ttfs / ttfn, 6) if ttfn else None),
        "ttft_server_count_delta": ttfn,
        "ttft_client_s": None,
        "client_elapsed_s": round(el, 4),   # non-stream, max_tokens=1 -> ~= TTFT
        "gen_tokens_delta": int(round(p2.dd(post, pre, p2.K_GEN))),
        "kv_cache_usage_perc": post.get(p2.K_USAGE),
        "uncached_from_cached": (None if pt is None else pt - cached),
        "uncached_from_kvcomp": (kvc if kvn == 1 else None),
        "error": err, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "notes": notes,
    }
    os.write(fd, (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode())
    os.fsync(fd)
    return row


def main() -> int:
    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    rows = []
    t0 = time.time()
    try:
        print("=== stage 2: residue-{0,1} avalanche at more block indices ===", flush=True)
        for P1t in (6337, 8449, 7390, 7394):
            for rep in range(2):
                pid = f"G7-P{P1t}-r{rep}"
                pm = p2.prime_msgs(f"r2_g7_{P1t}_{rep}", P1t - 53)
                r = one(fd, pair_id=pid, cell="G7", role="prime", rep=rep, messages=pm,
                        notes="prime (residue cell, fresh nonce)")
                rows.append(r)
                P1 = r["prompt_tokens"]
                r2 = one(fd, pair_id=pid, cell="G7", role="measure", rep=rep, round_=1,
                         messages=pm + [{"role": "assistant", "content": "OK."},
                                        {"role": "user", "content": " the"}],
                         P1=P1, notes="single 1-token append")
                rows.append(r2)
                print(f"  {pid}: P1={P1} res={P1 % B} cached={r2['cached_tokens']} "
                      f"unc_c={r2['uncached_from_cached']} unc_k={r2['uncached_from_kvcomp']} "
                      f"ttft_srv={r2['ttft_server_s']} wall={r2['client_elapsed_s']}", flush=True)

        print("\n=== G6: did the prime insert its blocks? (identical re-send, no append) ===",
              flush=True)
        for P1t in (7392, 7394):
            for rep in range(2):
                pid = f"G6-P{P1t}-r{rep}"
                pm = p2.prime_msgs(f"r2_g6_{P1t}_{rep}", P1t - 53)
                r = one(fd, pair_id=pid, cell="G6", role="prime", rep=rep, messages=pm,
                        notes="prime (insertion test)")
                rows.append(r)
                P1 = r["prompt_tokens"]
                rr = one(fd, pair_id=f"{pid}-same", cell="G6", role="measure", rep=rep,
                         round_=1, messages=pm, P1=P1,
                         notes="IDENTICAL re-send of the prime (no append)")
                rows.append(rr)
                ra = one(fd, pair_id=f"{pid}-app", cell="G6", role="measure", rep=rep,
                         round_=2, messages=pm + [{"role": "assistant", "content": "OK."},
                                                  {"role": "user", "content": " the"}],
                         P1=P1, notes="append after the identical re-send")
                rows.append(ra)
                print(f"  {pid}: prime P={P1} res={P1 % B} | identical-re-send cached="
                      f"{rr['cached_tokens']} unc_c={rr['uncached_from_cached']} "
                      f"ttft_srv={rr['ttft_server_s']} wall={rr['client_elapsed_s']} | "
                      f"append cached={ra['cached_tokens']} unc_c={ra['uncached_from_cached']} "
                      f"ttft_srv={ra['ttft_server_s']} wall={ra['client_elapsed_s']}", flush=True)
    finally:
        os.close(fd)

    print(f"\nstage 2 done: {len(rows)} rows, {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
