#!/usr/bin/env python3
"""UNIT MISS-LAW-2 -- re-derive the vLLM '+1056' term with SECOND and THIRD instruments.

MISS-LAW's vLLM half rests on ONE quantity: the delta of
`vllm:prompt_tokens_cached_total` (its `prefix_cache_hits_total` is an identity of
that series, so "the two agree" is not corroboration).

Instruments read per serialized request:

  A  counter   unc_c = usage.prompt_tokens - delta(prompt_tokens_cached_total)
       (+ identities recorded but NEVER counted as corroboration: prefix_cache_hits,
        prompt_tokens_by_source{local_cache_hit}, and the complement
        local_compute = prompt_tokens_total - cached)
  B  compute   unc_k = delta(request_prefill_kv_computed_tokens_sum)
       "new KV tokens computed during prefill (excluding cached tokens)" --
       scheduler/executor accounting, empirically NOT an identity of A. Per-request
       resolution comes from _sum/_count deltas; the _bucket deltas give the bucket.
  C  timing    client-measured TTFT of a streamed response (first content chunk).
       Physics. Shares no provenance with either counter. A cache hit and a cache
       miss on the same total length differ by b * 1056 tokens of prefill.

Grids
  CAL   template-constant calibration (P1 asked -> P1 reported)
  CAL-T cold TTFT-vs-length line (a + b*computed), for the timing scale
  G1    block-multiple bands: P1 around 6*B, 7*B, 8*B + plateau anchors
  G2    one session, SIX successive one-token appends (does +B grow with round?)
  G3    one session whose appends CROSS a block multiple (n=300, n=100, n=1)
  G4    the same measure request sent TWICE (was the boundary block ever matched?)
  G5    cold control (nonce broken between prime and measure)

Hard rules honoured: sole writer on :8014, strictly serial requests, no /flush_cache,
no restart, max_tokens=1 so decode cannot pollute TTFT.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # experiments/miss-law
OUT = os.path.join(HERE, "rows.jsonl")
SUMMARY = os.path.join(HERE, "summary.txt")
HOST, PORT = "192.168.2.168", 8014
BASE = f"http://{HOST}:{PORT}"
MODEL = "qwen3.5-9b"
B = 1056

_spec = importlib.util.spec_from_file_location("ml_run", os.path.join(ROOT, "run.py"))
ml = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ml)
CFG = ml.SERVERS["vllm"]

LBL = 'engine="0",model_name="qwen3.5-9b"'
K_CACHED = "vllm:prompt_tokens_cached_total{%s}" % LBL
K_HITS = "vllm:prefix_cache_hits_total{%s}" % LBL
K_QUER = "vllm:prefix_cache_queries_total{%s}" % LBL
K_PTOT = "vllm:prompt_tokens_total{%s}" % LBL
K_SRC = "vllm:prompt_tokens_by_source_total{" + LBL + ',source="%s"}'
K_KV = "vllm:request_prefill_kv_computed_tokens"          # histogram family (needs labels)
K_TTFT = "vllm:time_to_first_token_seconds"
K_RPT = "vllm:request_prompt_tokens"
K_GEN = "vllm:generation_tokens_total{%s}" % LBL
K_USAGE = "vllm:kv_cache_usage_perc{%s}" % LBL
HS = "_sum{" + LBL + "}"
HC = "_count{" + LBL + "}"


# ------------------------------------------------------------------ metrics
def snap() -> dict:
    with urllib.request.urlopen(BASE + "/metrics", timeout=30) as r:
        txt = r.read().decode()
    out = {}
    for line in txt.splitlines():
        if not line or line[0] == "#":
            continue
        i = line.rfind(" ")
        try:
            out[line[:i]] = float(line[i + 1:])
        except ValueError:
            pass
    return out


def dd(post: dict, pre: dict, key: str) -> float:
    return post.get(key, 0.0) - pre.get(key, 0.0)


def bucket_delta(post: dict, pre: dict, name: str) -> dict:
    got = {}
    pat = re.compile(r"^%s_bucket\{[^}]*?le=\"([^\"]+)\"" % re.escape(name))
    for k in post:
        m = pat.match(k)
        if m:
            got[m.group(1)] = dd(post, pre, k)
    return got


def bucket_of(bd: dict, n: int):
    if n <= 0 or not bd:
        return None

    def f(x):
        return float("inf") if x == "+Inf" else float(x)

    for le in sorted(bd, key=f):
        if bd[le] >= n:
            return le
    return None


# ------------------------------------------------------------------ requests
def chat_stream(messages: list, max_tokens: int = 1):
    """Streamed request; returns (usage, ttft_client, total_s, err)."""
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.0, "stream": True,
                       "stream_options": {"include_usage": True}}).encode()
    usage, first, err = None, None, None
    conn = http.client.HTTPConnection(HOST, PORT, timeout=600)
    t = time.time()
    try:
        conn.request("POST", "/v1/chat/completions", body,
                     {"Content-Type": "application/json"})
        r = conn.getresponse()
        if r.status != 200:
            err = "HTTP %d: %s" % (r.status, r.read()[:200].decode("utf-8", "replace"))
        else:
            while True:
                line = r.readline()
                if not line:
                    break
                s = line.strip()
                if not s.startswith(b"data:"):
                    continue
                p = s[5:].strip()
                if p == b"[DONE]":
                    break
                try:
                    obj = json.loads(p)
                except Exception:                       # noqa: BLE001
                    continue
                if obj.get("usage"):
                    usage = obj["usage"]
                for ch in obj.get("choices") or []:
                    d = ch.get("delta") or {}
                    if first is None and (d.get("content") or d.get("reasoning_content")):
                        first = time.time() - t
    except Exception as e:                              # noqa: BLE001
        err = f"{type(e).__name__}: {str(e)[:250]}"
    finally:
        conn.close()
    return usage, first, time.time() - t, err


def one(fd, *, pair_id, cell, role, rep, round_=0, n_payload=0,
        messages=None, P1=None, P1_target=None, notes=""):
    pre = snap()
    usage, ttft, tot, err = chat_stream(messages)
    post = snap()
    usage = usage or {}
    pt = usage.get("prompt_tokens")

    kvc = int(round(dd(post, pre, K_KV + HS)))
    kvn = int(round(dd(post, pre, K_KV + HC)))
    ttfs = dd(post, pre, K_TTFT + HS)
    ttfn = int(round(dd(post, pre, K_TTFT + HC)))
    rps = int(round(dd(post, pre, K_RPT + HS)))
    rpn = int(round(dd(post, pre, K_RPT + HC)))
    cached = int(round(dd(post, pre, K_CACHED)))

    row = {
        "pair_id": pair_id, "cell": cell, "role": role, "rep": rep,
        "round": round_, "n_payload": n_payload,
        "P1_target": P1_target, "P1": P1,
        "prompt_tokens": pt,
        "L_app": (None if (pt is None or P1 is None) else pt - P1),
        "prompt_tokens_details": usage.get("prompt_tokens_details", "ABSENT"),
        # --- A: cache counters (tokens; hits/source/local_compute are identities)
        "cached_tokens": cached,
        "prefix_cache_hits_delta": int(round(dd(post, pre, K_HITS))),
        "prefix_cache_queries_delta": int(round(dd(post, pre, K_QUER))),
        "prompt_tokens_total_delta": int(round(dd(post, pre, K_PTOT))),
        "by_source_local_cache_hit": int(round(dd(post, pre, K_SRC % "local_cache_hit"))),
        "by_source_local_compute": int(round(dd(post, pre, K_SRC % "local_compute"))),
        "by_source_external": int(round(dd(post, pre, K_SRC % "external_kv_transfer"))),
        # --- B: prefill KV tokens actually computed
        "kvcomp_sum_delta": kvc, "kvcomp_count_delta": kvn,
        "kvcomp_bucket_le": bucket_of(bucket_delta(post, pre, K_KV), kvn),
        # --- C: timing
        "ttft_client_s": (None if ttft is None else round(ttft, 4)),
        "ttft_server_sum_delta": round(ttfs, 6), "ttft_server_count_delta": ttfn,
        "ttft_server_s": (round(ttfs / ttfn, 6) if ttfn else None),
        "ttft_server_bucket_le": bucket_of(bucket_delta(post, pre, K_TTFT), ttfn),
        "total_client_s": round(tot, 4),
        "req_prompt_sum_delta": rps, "req_prompt_count_delta": rpn,
        "gen_tokens_delta": int(round(dd(post, pre, K_GEN))),
        "kv_cache_usage_perc": post.get(K_USAGE),
        # --- derived
        "uncached_from_cached": (None if pt is None else pt - cached),
        "uncached_from_kvcomp": (kvc if kvn == 1 else None),
        "client_elapsed_s": round(tot, 4), "error": err,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "notes": notes,
    }
    os.write(fd, (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode())
    os.fsync(fd)
    return row


def prime_msgs(key: str, filler_tokens: int):
    """[system: NONCE + FILLER + QUESTION, user: 'Reply ...'] with an EXACT filler length.

    NONCE is a permutation of ten one-token words -> CONSTANT 10 tokens, unique prefix
    per cell (cold), exactly as in MISS-LAW.
    """
    nonce = ml.make_nonce(key, 0, set())
    filler = ml.build_filler(filler_tokens, CFG)
    return [{"role": "system", "content": nonce + "\n\n" + filler + "\n\n" + ml.QUESTION},
            {"role": "user", "content": "Reply with the single word OK."}]


def main() -> int:
    os.makedirs(HERE, exist_ok=True)
    with urllib.request.urlopen(BASE + "/metrics", timeout=30) as r:
        raw = r.read().decode()
    with open(os.path.join(HERE, "metrics_raw.txt"), "w") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())

    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    rows, log = [], []
    t0 = time.time()

    def say(s):
        log.append(s)
        print(s, flush=True)

    try:
        say(f"=== MISS-LAW-2 probes on {BASE} ({MODEL}) ; B = {B} ===")

        # ---------- CAL: template constant
        rc = one(fd, pair_id="CAL", cell="CAL", role="prime", rep=0,
                 messages=prime_msgs("calib-0001", 7000 - 53), P1_target=7000,
                 notes="template-constant calibration")
        rows.append(rc)
        OFF = (rc["prompt_tokens"] - 7000) if rc["prompt_tokens"] else 0
        say(f"  CAL: asked 7000 -> got {rc['prompt_tokens']} (template constant "
            f"{(rc['prompt_tokens'] or 0) - (7000 - 53)}), offset {OFF}")

        # ---------- CAL-T: cold TTFT vs length
        for Lt in (1000, 2000, 3000, 5000):
            r = one(fd, pair_id=f"CALT-{Lt}", cell="CAL-T", role="prime", rep=0,
                    messages=prime_msgs(f"calt_{Lt}", Lt - 53 - OFF), P1_target=Lt,
                    notes="cold TTFT calibration point")
            rows.append(r)
            say(f"  CAL-T L={Lt}: P={r['prompt_tokens']} cached={r['cached_tokens']} "
                f"unc_k={r['uncached_from_kvcomp']} ttft={r['ttft_client_s']} "
                f"srv_ttft={r['ttft_server_s']}")

        # ---------- G1: block-multiple bands + plateau anchors
        G1 = [7000, 7200, 7330, 7450,                       # plateau anchors
              6334, 6336, 6338,                              # band around 6*B = 6336
              7386, 7390, 7391, 7392, 7393, 7394, 7398,      # band around 7*B = 7392
              8446, 8448, 8450]                              # band around 8*B = 8448
        for P1t in G1:
            for rep in range(2):
                pid = f"G1-P{P1t}-r{rep}"
                pm = prime_msgs(f"g1_{P1t}_{rep}", P1t - 53 - OFF)
                r = one(fd, pair_id=pid, cell="G1", role="prime", rep=rep,
                        messages=pm, P1_target=P1t, notes="prime")
                rows.append(r)
                P1 = r["prompt_tokens"]
                r2 = one(fd, pair_id=pid, cell="G1", role="measure", rep=rep, round_=1,
                         n_payload=1, messages=pm + [{"role": "assistant", "content": "OK."},
                                                     {"role": "user", "content": " the"}],
                         P1=P1, P1_target=P1t, notes="single 1-token append")
                rows.append(r2)
                say(f"  {pid}: P1={P1} L={r2['L_app']} cached={r2['cached_tokens']} "
                    f"unc_c={r2['uncached_from_cached']} unc_k={r2['uncached_from_kvcomp']} "
                    f"kvn={r2['kvcomp_count_delta']} ttft={r2['ttft_client_s']}")

        # ---------- G2: six one-token appends in ONE session
        for rep in range(2):
            pid = f"G2-r{rep}"
            pm = prime_msgs(f"g2_{rep}", 7000 - 53 - OFF)
            r = one(fd, pair_id=pid, cell="G2", role="prime", rep=rep, messages=pm,
                    P1_target=7000, notes="prime (6-append session)")
            rows.append(r)
            Pprev, msgs = r["prompt_tokens"], list(pm)
            for k in range(1, 7):
                msgs = msgs + [{"role": "assistant", "content": "OK."},
                               {"role": "user", "content": " the"}]
                rk = one(fd, pair_id=f"{pid}-k{k}", cell="G2", role="measure", rep=rep,
                         round_=k, n_payload=k, messages=list(msgs), P1=Pprev,
                         P1_target=7000, notes=f"append round {k} of 6")
                rows.append(rk)
                say(f"  {pid} k={k}: P_prev={Pprev} P={rk['prompt_tokens']} L={rk['L_app']} "
                    f"cached={rk['cached_tokens']} unc_c={rk['uncached_from_cached']} "
                    f"unc_k={rk['uncached_from_kvcomp']} ttft={rk['ttft_client_s']}")
                if rk["prompt_tokens"]:
                    Pprev = rk["prompt_tokens"]

        # ---------- G3: appends that CROSS 7*B = 7392 inside one session
        for rep in range(2):
            pid = f"G3-r{rep}"
            pm = prime_msgs(f"g3_{rep}", 7000 - 53 - OFF)
            r = one(fd, pair_id=pid, cell="G3", role="prime", rep=rep, messages=pm,
                    P1_target=7000, notes="prime (crossing-append session)")
            rows.append(r)
            Pprev, msgs = r["prompt_tokens"], list(pm)
            for k, n in enumerate((300, 100, 1), start=1):
                msgs = msgs + [{"role": "assistant", "content": "OK."},
                               {"role": "user", "content": " the" * n}]
                rk = one(fd, pair_id=f"{pid}-k{k}", cell="G3", role="measure", rep=rep,
                         round_=k, n_payload=n, messages=list(msgs), P1=Pprev,
                         P1_target=7000, notes=f"append n={n} (crossing round {k})")
                rows.append(rk)
                say(f"  {pid} k={k}: P_prev={Pprev} P={rk['prompt_tokens']} L={rk['L_app']} "
                    f"cached={rk['cached_tokens']} unc_c={rk['uncached_from_cached']} "
                    f"unc_k={rk['uncached_from_kvcomp']} ttft={rk['ttft_client_s']}")
                if rk["prompt_tokens"]:
                    Pprev = rk["prompt_tokens"]

        # ---------- G4: identical repeat
        for rep in range(2):
            pid = f"G4-r{rep}"
            pm = prime_msgs(f"g4_{rep}", 7000 - 53 - OFF)
            r = one(fd, pair_id=pid, cell="G4", role="prime", rep=rep, messages=pm,
                    P1_target=7000, notes="prime (identical repeat)")
            rows.append(r)
            P1 = r["prompt_tokens"]
            mm = pm + [{"role": "assistant", "content": "OK."},
                       {"role": "user", "content": " the"}]
            for k in (1, 2):
                rk = one(fd, pair_id=f"{pid}-i{k}", cell="G4", role="measure", rep=rep,
                         round_=k, n_payload=1, messages=mm, P1=P1, P1_target=7000,
                         notes="identical repeat #%d" % k)
                rows.append(rk)
                say(f"  {pid} identical#{k}: P={rk['prompt_tokens']} "
                    f"cached={rk['cached_tokens']} unc_c={rk['uncached_from_cached']} "
                    f"unc_k={rk['uncached_from_kvcomp']} ttft={rk['ttft_client_s']}")

        # ---------- G5: cold control
        for rep in range(2):
            pid = f"G5-r{rep}"
            one(fd, pair_id=pid, cell="G5", role="prime", rep=rep,
                messages=prime_msgs(f"g5_{rep}a", 7000 - 53 - OFF), P1_target=7000,
                notes="prime (cold control)")
            cold = prime_msgs(f"g5_{rep}b", 7000 - 53 - OFF)
            r = one(fd, pair_id=pid, cell="G5", role="measure", rep=rep, round_=1,
                    n_payload=1, messages=cold + [{"role": "assistant", "content": "OK."},
                                                  {"role": "user", "content": " the"}],
                    P1_target=7000, notes="COLD: nonce broken between prime and measure")
            rows.append(r)
            say(f"  {pid} cold: P={r['prompt_tokens']} cached={r['cached_tokens']} "
                f"unc_c={r['uncached_from_cached']} unc_k={r['uncached_from_kvcomp']} "
                f"ttft={r['ttft_client_s']}")
    finally:
        os.close(fd)

    say(f"total elapsed {time.time() - t0:.1f}s, rows={len(rows)}")

    # ------------------------------------------------------------ aggregation
    def get(r, k, default=None):
        v = r.get(k)
        return default if v is None else v

    say("\n=== G1: plateau, step, and both instruments side by side ===")
    say(f"{'P1':>6} {'res':>5} {'cached':>7} {'unc_c':>6} {'unc_k':>6} {'A-B':>5} "
        f"{'pred':>6} {'ttft_ms':>8} {'srv_ms':>7} {'unc_k_bucket':>12}")
    for r in rows:
        if r["cell"] != "G1" or r["role"] != "measure" or not r["prompt_tokens"]:
            continue
        P1, L = r["P1"], r["L_app"]
        pred = (P1 % B) + B + L
        uk = r["uncached_from_kvcomp"]
        say(f"{P1:>6} {P1 % B:>5} {r['cached_tokens']:>7} {r['uncached_from_cached']:>6} "
            f"{str(uk):>6} {(None if uk is None else r['uncached_from_cached'] - uk)!s:>5} "
            f"{pred:>6} {round(get(r, 'ttft_client_s', 0) * 1000, 1):>8} "
            f"{str(None if r['ttft_server_s'] is None else round(r['ttft_server_s'] * 1000, 1)):>7} "
            f"{str(r['kvcomp_bucket_le']):>12}")

    say("\n=== G2: six one-token appends (does the +B term grow with round?) ===")
    say(f"{'pair':>11} {'k':>2} {'P1':>6} {'P':>6} {'L':>3} {'cached':>7} {'unc_c':>6} "
        f"{'res':>5} {'+B term':>7} {'unc_k':>6} {'ttft_ms':>8}")
    for r in rows:
        if r["cell"] != "G2" or r["role"] != "measure" or not r["prompt_tokens"]:
            continue
        P1, L = r["P1"], r["L_app"]
        say(f"{r['pair_id']:>11} {r['round']:>2} {P1:>6} {r['prompt_tokens']:>6} {L:>3} "
            f"{r['cached_tokens']:>7} {r['uncached_from_cached']:>6} {P1 % B:>5} "
            f"{r['uncached_from_cached'] - (P1 % B) - L:>7} "
            f"{str(r['uncached_from_kvcomp']):>6} "
            f"{round(get(r, 'ttft_client_s', 0) * 1000, 1):>8}")

    say("\n=== G3: appends that cross 7*B (does cached step, does +B stay one block?) ===")
    say(f"{'pair':>9} {'k':>2} {'P1':>6} {'P':>6} {'L':>4} {'cached':>7} {'unc_c':>6} "
        f"{'res':>5} {'+B term':>7} {'unc_k':>6} {'ttft_ms':>8}")
    for r in rows:
        if r["cell"] != "G3" or r["role"] != "measure" or not r["prompt_tokens"]:
            continue
        P1, L = r["P1"], r["L_app"]
        say(f"{r['pair_id']:>9} {r['round']:>2} {P1:>6} {r['prompt_tokens']:>6} {L:>4} "
            f"{r['cached_tokens']:>7} {r['uncached_from_cached']:>6} {P1 % B:>5} "
            f"{r['uncached_from_cached'] - (P1 % B) - L:>7} "
            f"{str(r['uncached_from_kvcomp']):>6} "
            f"{round(get(r, 'ttft_client_s', 0) * 1000, 1):>8}")

    say("\n=== G4: identical repeat (was the dropped block ever matched?) ===")
    for r in rows:
        if r["cell"] == "G4":
            say(f"  {r['pair_id']:>11} {r['role']:>7} P={r['prompt_tokens']} "
                f"cached={r['cached_tokens']} unc_c={r['uncached_from_cached']} "
                f"unc_k={r['uncached_from_kvcomp']} ttft={r['ttft_client_s']}")

    say("\n=== G5: cold control ===")
    for r in rows:
        if r["cell"] == "G5":
            say(f"  {r['pair_id']:>9} {r['role']:>7} P={r['prompt_tokens']} "
                f"cached={r['cached_tokens']} unc_c={r['uncached_from_cached']} "
                f"unc_k={r['uncached_from_kvcomp']} ttft={r['ttft_client_s']}")

    # ---- instrument C calibration: cold points (all tokens computed)
    pts = [(r["uncached_from_kvcomp"], r["ttft_client_s"]) for r in rows
           if r["role"] == "prime" and r["uncached_from_kvcomp"] and r["ttft_client_s"]]
    if len(pts) >= 2:
        n = len(pts)
        sx = sum(p[0] for p in pts)
        sy = sum(p[1] for p in pts)
        sxx = sum(p[0] ** 2 for p in pts)
        sxy = sum(p[0] * p[1] for p in pts)
        b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        a = (sy - b * sx) / n
        say(f"\n=== instrument C calibration: COLD primes, n={n}, "
            f"TTFT = {a:.4f} + {b * 1000:.4f} ms/token * computed ===")
        say(f"{'computed':>8} {'ttft_ms':>8} {'fit_ms':>8} {'resid_ms':>9}")
        for x, y in sorted(pts):
            say(f"{x:>8} {y * 1000:>8.1f} {(a + b * x) * 1000:>8.1f} "
                f"{(y - a - b * x) * 1000:>9.1f}")

        say("\n=== boundary differentials: same total length, one block multiple crossed ===")
        say(f"{'cell pair':>22} {'d_unc_c':>8} {'d_unc_k':>8} {'d_ttft_ms':>10} "
            f"{'implied ms/tok':>15}")
        meas = {}
        for r in rows:
            if r["cell"] == "G1" and r["role"] == "measure" and r["prompt_tokens"]:
                meas.setdefault(r["P1"], []).append(r)
        for lo, hi in [(6338, 6336), (6336, 6334), (7398, 7394), (7394, 7392),
                       (7392, 7391), (7391, 7390), (7390, 7386), (8448, 8446), (8450, 8448)]:
            if lo in meas and hi in meas:
                rl, rh = meas[lo][0], meas[hi][0]
                duc = rl["uncached_from_cached"] - rh["uncached_from_cached"]
                duk = (rl["uncached_from_kvcomp"] or 0) - (rh["uncached_from_kvcomp"] or 0)
                dt = ((rl["ttft_client_s"] or 0) - (rh["ttft_client_s"] or 0)) * 1000
                imp = (dt / duc) if duc else None
                say(f"{'P%d - P%d' % (lo, hi):>22} {duc:>8} {duk:>8} {dt:>10.1f} "
                    f"{'' if imp is None else round(imp, 4)!s:>15}")

    shapes = {}
    for r in rows:
        k = json.dumps(r["prompt_tokens_details"])
        shapes[k] = shapes.get(k, 0) + 1
    say("\n=== prompt_tokens_details across all rows ===")
    for k, v in shapes.items():
        say(f"  {v:>3} rows: {k}")

    errs = [r for r in rows if r["error"]]
    say(f"\nerrors: {len(errs)}")
    for r in errs[:5]:
        say(f"  {r['pair_id']}: {r['error']}")
    kvzero = [r for r in rows if r["kvcomp_count_delta"] != 1]
    say(f"rows where the kvcomp histogram did not register exactly one sample: {len(kvzero)}")
    for r in kvzero[:5]:
        say(f"  {r['pair_id']} kvn={r['kvcomp_count_delta']}")

    with open(SUMMARY, "w") as f:
        f.write("\n".join(log) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return 0


if __name__ == "__main__":
    sys.exit(main())
