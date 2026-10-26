#!/usr/bin/env python3
"""BILL-AUDIT: compare the append-cost LAW against the SERVER's own accounting.

Server: occamy-1.0, SGLang, http://192.168.2.168:8012  (sole writer for this unit)
No restart, no /flush_cache. One row per request, flush()+fsync() per row.

The law (experiments/miss-law/LAW.md):
    uncached = (P1 mod 64) + L                    if (P1 mod 64) not in {0, 1}
    uncached = P1 + L                             if (P1 mod 64) in {0, 1}   <- "the avalanche"

Server instrument (found by this unit, NOT used by QUALITY-ARM):
    POST /generate -> meta_info.cached_tokens  (+ cached_tokens_details.{device,host})
    POST /v1/chat/completions -> usage.prompt_tokens_details.cached_tokens
"""

import json
import os
import random
import sys
import time
import urllib.request

BASE = "http://192.168.2.168:8012"
B = 64
HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "rows.jsonl")
WORDS = "alpha bravo charlie delta echo foxtrot golf hotel india juliet".split()

_fh = None


def _open():
    global _fh
    if _fh is None:
        _fh = open(ROWS, "a", buffering=1)
    return _fh


def emit(row):
    """One row per line, flushed AND fsynced."""
    fh = _open()
    fh.write(json.dumps(row, sort_keys=True) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def post(path, payload, timeout=300.0):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read())
    return body, time.time() - t0


def gen_cached(meta):
    """Read the server's cached count from a /generate meta_info WITHOUT inferring it.

    Returns (cached, reported, keys_used).
    reported=False when the key is absent OR null -- null is NOT zero.
    """
    keys = []
    if "cached_tokens" in meta:
        keys.append("meta_info.cached_tokens")
    det = meta.get("cached_tokens_details")
    if isinstance(det, dict):
        keys.append("meta_info.cached_tokens_details")
    val = meta.get("cached_tokens", None)
    if val is None:
        return None, False, keys
    return int(val), True, keys


def predict(p1, L):
    """The law. Returns (uncached, residue, avalanche_flag)."""
    r = p1 % B
    if r in (0, 1):
        return p1 + L, r, True
    return r + L, r, False


def sid(nonce_val):
    return nonce_val * 1000 + random.randrange(1000)


def fresh_nonce(rng):
    return " ".join(rng.sample(WORDS, 10))


def aim_residue(rng, target, filler, min_blocks=6, max_try=70):
    """Find a filler padding whose MEASURED P1 lands on `target` residue.

    Every probe is a real /generate request and gets its own row.
    Returns (nonce, prompt_text, P1) or (None, None, None).
    """
    nonce = fresh_nonce(rng)
    for pad in range(0, max_try):
        text = nonce + "\n\n" + filler + (" the" * pad) + "\n\nReply with the single word OK."
        body, el = post("/generate", {"text": text, "sampling_params": {"max_new_tokens": 1, "temperature": 0}})
        meta = body.get("meta_info", {})
        p1 = int(meta["prompt_tokens"])
        cached, rep, keys = gen_cached(meta)
        emit({
            "row": "probe", "phase": "aim", "target_residue": target,
            "P1": p1, "residue": p1 % B, "pad": pad,
            "server_reported": {"cached_tokens": cached, "reported": rep, "keys": keys,
                                "prompt_tokens": p1,
                                "cached_tokens_details": meta.get("cached_tokens_details")},
            "elapsed_s": round(el, 4), "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        if p1 % B == target and p1 // B >= min_blocks:
            return nonce, text, p1
    return None, None, None


def measure_cell(rng, arm, target, filler, reps):
    """Prime (cold, aimed), then repeat verbatim (WARM) and read both numbers."""
    for rep in range(reps):
        nonce, text, p1 = aim_residue(rng, target, filler)
        if text is None:
            emit({"row": "measure", "arm": arm, "target_residue": target, "rep": rep,
                  "error": "aim_failed"})
            continue
        # The aiming request IS the prime -- it is cold because the nonce is fresh.
        # Now the WARM append: same conversation, one more user turn.
        warm_text = text + "\n\nReply with the single word OK."
        body, el = post("/generate", {"text": warm_text,
                                      "sampling_params": {"max_new_tokens": 8, "temperature": 0}})
        meta = body.get("meta_info", {})
        p2 = int(meta["prompt_tokens"])
        L = p2 - p1
        cached, rep_flag, keys = gen_cached(meta)
        law_unc, residue, avalanche = predict(p1, L)
        if not rep_flag:
            verdict = "server-null"
            delta = None
            server_unc = None
        else:
            server_unc = p2 - cached
            delta = server_unc - law_unc
            if delta == 0:
                verdict = "exact"
            elif avalanche:
                verdict = "exact" if delta == 0 else "off-by-k"
            else:
                verdict = "off-by-k"
        emit({
            "row": "measure", "arm": arm, "rep": rep,
            "target_residue": target,
            "residue": residue, "P1": p1, "P2": p2, "L": L,
            "avalanche_predicted": avalanche,
            "law_predicted": {"uncached": law_unc, "formula":
                              f"P1+L={p1}+{L}" if avalanche else f"(P1 mod 64)+L={residue}+{L}"},
            "server_reported": {"cached_tokens": cached, "reported": rep_flag,
                                "prompt_tokens": p2, "uncached": server_unc,
                                "keys": keys,
                                "cached_tokens_details": meta.get("cached_tokens_details"),
                                "finish_reason": meta.get("finish_reason"),
                                "e2e_latency": meta.get("e2e_latency"),
                                "queue_time": meta.get("queue_time")},
            "delta": delta, "agreement": verdict,
            "elapsed_s": round(el, 4),
            "ttft_s": None,
            "nonce": nonce,
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        print(f"  {arm} rep{rep} P1={p1} res={residue} L={L} "
              f"law={law_unc} server_unc={server_unc} delta={delta} {verdict}", flush=True)


def main():
    reps = int(os.environ.get("REPS", "3"))
    small = " ".join(["the quick brown fox jumps over the lazy dog."] * 40)    # ~420 tok
    big = " ".join(["the quick brown fox jumps over the lazy dog."] * 800)     # ~8000 tok
    print(f"BILL-AUDIT against {BASE}, B={B}, reps={reps}", flush=True)
    cells = [
        ("residue2-small", 2, small),
        ("residue0-small", 0, small),
        ("high-residue-small", 40, small),
        ("residue2-big", 2, big),
        ("residue0-big", 0, big),
        ("residue1-big", 1, big),
        ("high-residue-big", 63, big),
    ]
    for arm, target, filler in cells:
        print(f"[cell] {arm} target residue {target}", flush=True)
        rng = random.Random(hash(arm) & 0xFFFF)
        measure_cell(rng, arm, target, filler, reps)
    print("done", flush=True)


if __name__ == "__main__":
    main()
