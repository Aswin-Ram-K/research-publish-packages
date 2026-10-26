#!/usr/bin/env python3
"""UNIT MISS-LAW -- measure the append-cost (re-billed tail) law.

Law under test: for a prefix-cached server with cache block size B, a request that
repeats a prefix of length P1 and appends L_app tokens more is billed

    uncached = P2 - cached,      cached = floor(P1 / B) * B

so the re-billed tail is  R = (P1 mod B) + L_app  -- i.e. history that does not
end on a block boundary is re-billed on EVERY append.  Variants of this
(partial trailing block of the *new* length being reusable, etc.) are what the
grid has to discriminate between; the formula is the output, not the input.

Request shape (identical on both servers, recorded in every row):

  round 1 (prime):   [system: NONCE + "\\n\\n" + FILLER + "\\n\\n" + QUESTION,
                      user:   "Reply with the single word OK."]
  round 2 (measure): same + [assistant: "OK.", user: " the"*n]

  " the" is exactly 1 token on both tokenizers, so the payload is n tokens
  exactly; L_app = P2 - P1 also carries the constant template framing tokens T.

Instruments
  sglang : usage.prompt_tokens_details.cached_tokens  (null on a cold request;
           null is NOT zero -> cached_reported=false)
  vllm   : no per-request cache field on this build -> delta of the server
           counter vllm:prompt_tokens_cached_total across each serial request.

Hard rules: serial requests only, no /flush_cache, no restarts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(ROOT, "rows.jsonl")

QUESTION = ("Question: the ledger records shipment identifiers for a set of depots. "
            "Answer with one word.")

SERVERS = {
    "sglang": {
        "base": "http://192.168.2.168:8012",
        "model": "occamy-1.0",
        "tok_path": "/v1/tokenize",
        "instrument": "usage.prompt_tokens_details.cached_tokens",
        "hist_base": 8000,
        "ngrid": [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 40, 48, 56, 60, 62, 63, 64, 65, 80, 127, 128, 129],
        "max_model_len": 131072,
    },
    "vllm": {
        "base": "http://192.168.2.168:8014",
        "model": "qwen3.5-9b",
        "tok_path": "/tokenize",
        "instrument": "delta vllm:prompt_tokens_cached_total",
        "hist_base": 7000,
        "ngrid": [1, 2, 63, 64, 511, 512, 1055, 1056, 1057, 2112, 2113],
        "max_model_len": 32768,
    },
}

# 10 words that are each exactly one token when space-prefixed -> a permutation
# nonce has a CONSTANT token count, so P1 (hence H mod B) is stable across reps
# while the prefix is still unique (hence cold).
POOL = "the a and of to in is it on by".split()

SENTENCES = [
    "The quarterly inventory reconciliation ledger records shipment identifiers and depot codes. ",
    "Every depot keeps a roll-up of pallet counts that the audit team samples at quarter end. ",
    "Shipments tagged for manual review are re-scanned before the manifest is sealed. ",
    "A discrepancy note is filed whenever a scanned pallet count differs from the manifest. ",
    "Regional supervisors reconcile the exception queue against the nightly export. ",
    "Ledger rows carry a monotonic sequence number so replays can be detected cheaply. ",
    "Cold storage depots log temperature bands alongside every pallet movement. ",
    "The reconciliation window closes once all exception notes for the quarter are closed. ",
]

_TOK_CACHE: dict[str, int] = {}


def http_json(url: str, body: dict | None, timeout: int = 600):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def ntok(cfg: dict, text: str) -> int:
    """Exact token count from the server's own tokenizer."""
    key = f"{cfg['model']}|{hashlib.sha256(text.encode()).hexdigest()}"
    if key in _TOK_CACHE:
        return _TOK_CACHE[key]
    j = http_json(cfg["base"] + cfg["tok_path"], {"model": cfg["model"], "prompt": text})
    n = j.get("count")
    if n is None:
        n = len(j.get("tokens") or j.get("token_ids") or [])
    _TOK_CACHE[key] = int(n)
    return int(n)


def build_filler(target_tokens: int, cfg: dict) -> str:
    """Filler with EXACTLY `target_tokens` tokens: whole sentences, then ' the' padding."""
    parts: list[str] = []
    total = 0
    i = 0
    while True:
        s = SENTENCES[i % len(SENTENCES)]
        i += 1
        c = ntok(cfg, s)
        if total + c > target_tokens:
            break
        parts.append(s)
        total += c
        if i > 4000:
            break
    pad = target_tokens - total
    if pad > 0:
        parts.append(" the" * pad)
    text = "".join(parts)
    got = ntok(cfg, text)
    if got != target_tokens:  # repair by ±1-token nudges (rare)
        for _ in range(64):
            d = target_tokens - got
            if d == 0:
                break
            text = text + (" the" * d if d > 0 else "")
            if d < 0:
                # drop trailing ' the' units
                text = ("".join(parts[:-1])) if pad == 0 else ""
                text = text + " the" * max(0, target_tokens - ntok(cfg, text))
            got = ntok(cfg, text)
    return text


def make_nonce(cell: str, rep: int, used: set[str]) -> str:
    seed = hashlib.sha256(f"{cell}|{rep}".encode()).digest()
    words = POOL[:]
    rnd = int.from_bytes(seed[:8], "big")
    for i in range(len(words) - 1, 0, -1):
        rnd, j = divmod(rnd, i + 1)
        words[i], words[j] = words[j], words[i]
    cand = " ".join(words)
    salt = 0
    while cand in used:
        salt += 1
        w2 = words[:]
        a, b = 0, salt % len(w2)
        w2[a], w2[b] = w2[b], w2[a]
        cand = " ".join(w2)
        if salt > 200:
            cand = " ".join(words[:-1] + [f"{words[-1]}x{salt}"])  # last resort
            break
    used.add(cand)
    return " " + cand


# ------------------------------------------------------------------ metrics
def metrics_pull(cfg: dict) -> dict:
    try:
        with urllib.request.urlopen(cfg["base"] + "/metrics", timeout=30) as r:
            txt = r.read().decode()
    except Exception:
        return {}
    out = {}
    for line in txt.splitlines():
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([0-9eE+\-.]+)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(3)
        if "prompt_tokens_cached_total" in k or "prefix_cache_hits_total" in k:
            out[k] = float(v)
    return out


# ------------------------------------------------------------------ requests
def send(ctx, messages: list[dict]) -> dict:
    cfg = ctx["cfg"]
    body = {"model": cfg["model"], "messages": messages,
            "max_tokens": 4, "temperature": 0.0}
    url = cfg["base"] + "/v1/chat/completions"
    pre = metrics_pull(cfg) if ctx["name"] == "vllm" else None
    t0 = time.time()
    j, err = None, None
    for _attempt in range(2):
        try:
            j = http_json(url, body)
            err = None
            break
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:300]}"
            time.sleep(2)
    el = time.time() - t0
    post = metrics_pull(cfg) if ctx["name"] == "vllm" else None

    pt, cached, reported, extra = None, None, False, {}
    if j is not None:
        u = j.get("usage") or {}
        pt = u.get("prompt_tokens")
        if ctx["name"] == "sglang":
            d = u.get("prompt_tokens_details") or None
            cached = d.get("cached_tokens") if isinstance(d, dict) else None
            reported = cached is not None
        else:
            if pre and post and "vllm:prompt_tokens_cached_total" in post:
                cached = int(round(post["vllm:prompt_tokens_cached_total"]
                                   - pre.get("vllm:prompt_tokens_cached_total", 0.0)))
                reported = True
                extra["hits_delta"] = int(round(
                    post.get("vllm:prefix_cache_hits_total", 0.0)
                    - pre.get("vllm:prefix_cache_hits_total", 0.0)))
    return {"prompt_tokens": pt, "cached_tokens": cached,
            "cached_reported": reported, "elapsed_s": round(el, 3),
            "error": err, **extra}


def append_row(fd: int, row: dict) -> None:
    os.write(fd, (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode())
    os.fsync(fd)


# ------------------------------------------------------------------ cycle
def cycle(ctx, cell: str, filler_tokens: int, n: int, rep: int, phase: str,
          notes: str = "") -> None:
    """One prime -> append cycle. Skips a cell that is already on disk (resume)."""
    name, cfg = ctx["name"], ctx["cfg"]
    B = ctx["B"]
    k_prime = (name, cell, rep, "prime")
    k_meas = (name, cell, rep, "measure")
    if k_prime in ctx["done"] and k_meas in ctx["done"]:
        return

    nonce = ctx["nonce_of"].get((name, cell, rep))
    if nonce is None:
        nonce = make_nonce(cell, rep, ctx["used"])
        ctx["nonce_of"][(name, cell, rep)] = nonce

    hist = nonce + "\n\n" + build_filler(filler_tokens, cfg) + "\n\n" + QUESTION
    prime_msgs = [{"role": "system", "content": hist},
                  {"role": "user", "content": "Reply with the single word OK."}]

    if k_prime not in ctx["done"]:
        r = send(ctx, prime_msgs)
        P1 = r["prompt_tokens"]
        append_row(ctx["fd"], {
            "server": name, "model": cfg["model"], "phase": phase, "cell": cell,
            "rep": rep, "role": "prime", "nonce": nonce,
            "filler_tokens": filler_tokens, "n_payload": n,
            "prompt_tokens": P1, "cached_tokens": r["cached_tokens"],
            "cached_reported": r["cached_reported"],
            "uncached_tokens": (None if P1 is None else
                                P1 - (r["cached_tokens"] or 0)),
            "B_measured": B,
            "H_res": (None if (P1 is None or not B) else P1 % B),
            "elapsed_s": r["elapsed_s"], "error": r["error"],
            "shape": "prime", "notes": notes,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        ctx["done"].add(k_prime)
    else:
        P1 = ctx["p1_of"].get((name, cell, rep))

    if k_meas in ctx["done"]:
        return
    if P1 is None:
        return  # prime unknown (resume without P1) -> cannot attribute a delta

    meas_msgs = prime_msgs + [{"role": "assistant", "content": "OK."},
                              {"role": "user", "content": " the" * n}]
    r = send(ctx, meas_msgs)
    P2 = r["prompt_tokens"]
    L_app = None if (P2 is None or P1 is None) else P2 - P1
    append_row(ctx["fd"], {
        "server": name, "model": cfg["model"], "phase": phase, "cell": cell,
        "rep": rep, "role": "measure", "nonce": nonce,
        "filler_tokens": filler_tokens, "n_payload": n,
        "prev_prompt_tokens": P1, "prompt_tokens": P2,
        "cached_tokens": r["cached_tokens"],
        "cached_reported": r["cached_reported"],
        "uncached_tokens": (None if P2 is None else
                            P2 - (r["cached_tokens"] or 0)),
        "L_app": L_app, "B_measured": B,
        "H_res": (None if (P1 is None or not B) else P1 % B),
        "L_res": (None if (L_app is None or not B) else L_app % B),
        "generic_hit_theory": None,  # filled by analyze
        "elapsed_s": r["elapsed_s"], "error": r["error"], "hits_delta": r.get("hits_delta"),
        "shape": "measure", "notes": notes,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    ctx["done"].add(k_meas)


# ------------------------------------------------------------------ setup
def load_state(path: str):
    done, used, nonce_of, p1_of = set(), set(), {}, {}
    if not os.path.exists(path):
        return done, used, nonce_of, p1_of
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            done.add((r.get("server"), r.get("cell"), r.get("rep"), r.get("role")))
            if r.get("nonce"):
                used.add(r["nonce"].lstrip())
            if r.get("role") == "prime" and r.get("prompt_tokens") is not None:
                p1_of[(r.get("server"), r.get("cell"), r.get("rep"))] = r["prompt_tokens"]
                nonce_of[(r.get("server"), r.get("cell"), r.get("rep"))] = r.get("nonce")
    return done, used, nonce_of, p1_of


def gcd_all(vals):
    g = 0
    for v in vals:
        v = abs(int(v))
        while v:
            g, v = v, g % v
    return g


def probe_b(ctx, filler_tokens: int):
    """One cold cycle; returns (P1, cached) for B discovery."""
    cfg = ctx["cfg"]
    cell = f"Bprobe-{filler_tokens}"
    nonce = make_nonce(cell, 0, ctx["used"])
    hist = nonce + "\n\n" + build_filler(filler_tokens, cfg) + "\n\n" + QUESTION
    prime_msgs = [{"role": "system", "content": hist},
                  {"role": "user", "content": "Reply with the single word OK."}]
    r1 = send(ctx, prime_msgs)
    P1 = r1["prompt_tokens"]
    append_row(ctx["fd"], {
        "server": ctx["name"], "model": cfg["model"], "phase": "B", "cell": cell,
        "rep": 0, "role": "prime", "nonce": nonce, "filler_tokens": filler_tokens,
        "n_payload": 2, "prompt_tokens": P1, "cached_tokens": r1["cached_tokens"],
        "cached_reported": r1["cached_reported"],
        "uncached_tokens": (None if P1 is None else P1 - (r1["cached_tokens"] or 0)),
        "B_measured": None, "H_res": None, "elapsed_s": r1["elapsed_s"],
        "error": r1["error"], "shape": "prime", "notes": "B discovery",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    meas = prime_msgs + [{"role": "assistant", "content": "OK."},
                         {"role": "user", "content": " the" * 2}]
    r2 = send(ctx, meas)
    P2 = r2["prompt_tokens"]
    cached = r2["cached_tokens"]
    append_row(ctx["fd"], {
        "server": ctx["name"], "model": cfg["model"], "phase": "B", "cell": cell,
        "rep": 0, "role": "measure", "nonce": nonce, "filler_tokens": filler_tokens,
        "n_payload": 2, "prev_prompt_tokens": P1, "prompt_tokens": P2,
        "cached_tokens": cached, "cached_reported": r2["cached_reported"],
        "uncached_tokens": (None if P2 is None else P2 - (cached or 0)),
        "L_app": (None if (P1 is None or P2 is None) else P2 - P1),
        "B_measured": None, "H_res": None, "L_res": None,
        "elapsed_s": r2["elapsed_s"], "error": r2["error"],
        "shape": "measure", "notes": "B discovery", "hits_delta": r2.get("hits_delta"),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    return P1, cached


def calibrate_hist(ctx, name: str, target_res: int, base_tokens: int) -> tuple[int, int]:
    """Choose a filler token count so that P1 % B == target_res.

    Uses a canonical nonce; per-rep nonces are permutations with the same token
    count, so the residue carries over to every rep of this history."""
    cfg = ctx["cfg"]
    B = ctx["B"]
    canon = " " + " ".join(POOL)
    f = base_tokens
    P1 = None
    for _ in range(4):
        hist = canon + "\n\n" + build_filler(f, cfg) + "\n\n" + QUESTION
        r = send(ctx, [{"role": "system", "content": hist},
                       {"role": "user", "content": "Reply with the single word OK."}])
        P1 = r["prompt_tokens"]
        append_row(ctx["fd"], {
            "server": name, "model": cfg["model"], "phase": "calib", "cell": f"calib-{name}-{target_res}",
            "rep": 0, "role": "prime", "nonce": canon, "filler_tokens": f,
            "n_payload": 0, "prompt_tokens": P1,
            "cached_tokens": r["cached_tokens"], "cached_reported": r["cached_reported"],
            "uncached_tokens": (None if P1 is None else P1 - (r["cached_tokens"] or 0)),
            "B_measured": B, "H_res": (None if (P1 is None or not B) else P1 % B),
            "elapsed_s": r["elapsed_s"], "error": r["error"], "shape": "prime",
            "notes": f"calib target_res={target_res}", "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        if P1 is not None and B and P1 % B == target_res:
            return f, P1
        if P1 is None:
            break
        delta = (target_res - P1) % B
        if delta > B // 2:
            delta -= B
        f = max(64, f + delta)
    return f, P1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="all", choices=["all", "sglang", "vllm"])
    ap.add_argument("--stage", default="all", choices=["all", "b", "grid"])
    ap.add_argument("--max-seconds", type=float, default=900.0)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--b-override", type=int, default=0,
                    help="working value of B used only to record H_res/L_res; the "
                         "grid itself is what verifies B (the gcd estimate overshoots)")
    args = ap.parse_args()

    t_start = time.time()
    done, used, nonce_of, p1_of = load_state(ROWS)
    fd = os.open(ROWS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    names = list(SERVERS) if args.server == "all" else [args.server]

    try:
        for name in names:
            cfg = SERVERS[name]
            ctx = {"name": name, "cfg": cfg, "done": done, "used": used,
                   "nonce_of": nonce_of, "p1_of": p1_of, "fd": fd, "B": None}
            print(f"=== {name} ({cfg['model']}) ===", flush=True)

            # ---- phase B: measure the block size, do not assume it
            probe_cached = []
            if args.stage in ("all", "b"):
                for k in range(8):
                    ft = 400 + k * 900
                    P1, cached = probe_b(ctx, ft)
                    if cached:
                        probe_cached.append(cached)
                    print(f"  Bprobe filler={ft:5d} P1={P1} cached={cached}", flush=True)
            else:
                for k in range(8):
                    ft = 400 + k * 900
                    for row in []:
                        pass
            if not probe_cached:
                # recover from rows on disk
                with open(ROWS, encoding="utf-8") as f:
                    for line in f:
                        try:
                            r = json.loads(line)
                        except Exception:
                            continue
                        if r.get("server") == name and r.get("phase") == "B" \
                                and r.get("role") == "measure" and r.get("cached_tokens"):
                            probe_cached.append(r["cached_tokens"])
            B = gcd_all(probe_cached) if probe_cached else 0
            if B < 8:
                B = 0
            if args.b_override:
                B = args.b_override
            ctx["B"] = B
            print(f"  => B_measured={B} from cached={sorted(set(probe_cached))}", flush=True)

            if args.stage == "b":
                continue

            # ---- histories calibrated to H mod B in {0, 1, B//2}
            base = cfg["hist_base"]
            targets = [("h0", 0), ("h1", 1), ("hm", (B // 2) if B else 0)]
            hist_f: dict[str, int] = {}
            for hname, tres in targets:
                f, P1 = calibrate_hist(ctx, f"{name}-{hname}", tres, base)
                hist_f[hname] = f
                print(f"  calib {hname}: filler={f} P1={P1} res={None if not P1 or not B else P1 % B}", flush=True)

            # ---- controls
            cnonce_a = make_nonce("ctl-warm", 0, used)
            cnonce_b = make_nonce("ctl-cold", 0, used)
            if (name, "ctl-warm", 0, "measure") not in done:
                fa = build_filler(base, cfg)
                msg_a = [{"role": "system", "content": cnonce_a + "\n\n" + fa + "\n\n" + QUESTION},
                         {"role": "user", "content": "Reply with the single word OK."}]
                r1 = send(ctx, msg_a)
                r2 = send(ctx, msg_a)  # WARM: identical repeat -> must read high
                for tag, r in (("warm1", r1), ("warm2", r2)):
                    append_row(fd, {
                        "server": name, "model": cfg["model"], "phase": "control",
                        "cell": "ctl-warm", "rep": 0, "role": tag, "nonce": cnonce_a,
                        "filler_tokens": base, "n_payload": 0,
                        "prompt_tokens": r["prompt_tokens"],
                        "cached_tokens": r["cached_tokens"],
                        "cached_reported": r["cached_reported"],
                        "uncached_tokens": (None if r["prompt_tokens"] is None else
                                            r["prompt_tokens"] - (r["cached_tokens"] or 0)),
                        "B_measured": B,
                        "H_res": (None if (r["prompt_tokens"] is None or not B)
                                  else r["prompt_tokens"] % B),
                        "elapsed_s": r["elapsed_s"], "error": r["error"],
                        "shape": "control", "notes": "WARM control: identical repeat",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
                done.add((name, "ctl-warm", 0, "measure"))

            # COLD control: unique prefix, then a prefix differing mid-history -> must read ~0
            if (name, "ctl-cold", 0, "measure") not in done:
                fb = build_filler(base, cfg)
                mut = fb[:-1].replace("depot", "DEPOTX", 1) if "depot" in fb else fb[:-1] + "Z"
                m1 = [{"role": "system", "content": cnonce_b + "\n\n" + fb + "\n\n" + QUESTION},
                      {"role": "user", "content": "Reply with the single word OK."}]
                m2 = [{"role": "system", "content": cnonce_b + "\n\n" + mut + "\n\n" + QUESTION},
                      {"role": "user", "content": "Reply with the single word OK."}]
                r1 = send(ctx, m1)
                r2 = send(ctx, m2)  # COLD: prefix broken mid-history -> must read ~0
                for tag, r in (("cold1", r1), ("cold2", r2)):
                    append_row(fd, {
                        "server": name, "model": cfg["model"], "phase": "control",
                        "cell": "ctl-cold", "rep": 0, "role": tag, "nonce": cnonce_b,
                        "filler_tokens": base, "n_payload": 0,
                        "prompt_tokens": r["prompt_tokens"],
                        "cached_tokens": r["cached_tokens"],
                        "cached_reported": r["cached_reported"],
                        "uncached_tokens": (None if r["prompt_tokens"] is None else
                                            r["prompt_tokens"] - (r["cached_tokens"] or 0)),
                        "B_measured": B,
                        "H_res": (None if (r["prompt_tokens"] is None or not B)
                                  else r["prompt_tokens"] % B),
                        "elapsed_s": r["elapsed_s"], "error": r["error"],
                        "shape": "control", "notes": "COLD control: prefix broken mid-history",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
                done.add((name, "ctl-cold", 0, "measure"))

            # ---- main grid
            for hname, _t in targets:
                f = hist_f[hname]
                for n in cfg["ngrid"]:
                    if time.time() - t_start > args.max_seconds:
                        print(f"  [budget] stop after grid partial at {hname} n={n}", flush=True)
                        return 0
                    for rep in range(args.reps):
                        cycle(ctx, f"grid-{hname}-n{n}", f, n, rep, "grid")
                    print(f"  grid {hname} n={n:4d} done", flush=True)
            print(f"=== {name} complete ===", flush=True)
    finally:
        os.close(fd)
    print(f"total elapsed {time.time() - t_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
