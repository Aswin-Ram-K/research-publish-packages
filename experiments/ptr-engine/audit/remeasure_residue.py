#!/usr/bin/env python3
"""BILL-REPAIR: confirm on THIS server, through /generate, that residue 0 is ONE BLOCK
and residue 1 is NORMAL -- and settle whether ENGINE-R1's `cached=null` at residue 0
was the chat endpoint's field being absent rather than a cache behaviour.

Shape, per ENGINE-R1 (measure/run_cells.py) and LAW.md §2: the NONCE is a permutation
of ten one-token words placed at the HEAD of the system message, so every prime is
cold while P1 stays fixed; then the SAME prompt is re-sent with a 1-token append.

Two endpoints are exercised on the identical rendered token stream:
  * `/generate` with `input_ids`  -> meta_info.cached_tokens  (the RICH instrument)
  * `/v1/chat/completions`        -> usage.prompt_tokens_details (the QUALITY-ARM one)
so the null question is answered by construction, not by inference.
"""
import json, os, random, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import BASE, B, emit as _emit0, post, gen_cached  # noqa: E402

ROWS = HERE / "rows-remeasure.jsonl"
WORDS = "alpha bravo charlie delta echo foxtrot golf hotel india juliet".split()
MODEL = "occamy-1.0"
REPS = 3
CELLS = [("residue0", 0), ("residue1", 1), ("residue2", 2), ("residue40", 40)]

_fh = None
def emit(row):
    global _fh
    if _fh is None:
        _fh = open(ROWS, "a", buffering=1)
    row.setdefault("observed_at", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    _fh.write(json.dumps(row, sort_keys=True) + "\n"); _fh.flush(); os.fsync(_fh.fileno())

BASE_TEXT = ("The quarterly calibration record for the lumen instrument is filed under "
             "schedule K. " * 120)

def tokenize(msgs):
    r = post("/v1/tokenize", {"model": MODEL, "messages": msgs,
                              "add_generation_prompt": False})
    return r[0]["tokens"], r[0]["count"]

def build(target):
    """A cold prefix whose server-measured P1 lands on `target` residue."""
    for attempt in range(40):
        perm = random.sample(WORDS, len(WORDS))
        head = perm[0].upper() + " " + " ".join(perm) + " :: " + BASE_TEXT
        msgs = [{"role": "system", "content": head},
                {"role": "user", "content": "Reply with the single word OK."}]
        ids, n = tokenize(msgs)
        r = n % B
        if r == target:
            return msgs, ids, n, attempt
        # pad by ASCII words until the residue matches
        keep = " ".join(perm)
        for pad in range(1, 200):
            head2 = keep + " :: " + ("pad " * pad) + BASE_TEXT
            msgs2 = [{"role": "system", "content": head2},
                     {"role": "user", "content": "Reply with the single word OK."}]
            ids2, n2 = tokenize(msgs2)
            if n2 % B == target:
                return msgs2, ids2, n2, attempt + pad
    raise SystemExit(f"could not aim residue {target}")

def main():
    if ROWS.exists():
        ROWS.unlink()
    for cell, target in CELLS:
        for rep in range(REPS):
            msgs, ids, p1, tries = build(target)
            # PRIME: fresh nonce -> cold.  Read both endpoints' report for the prime.
            g = post("/generate", {"input_ids": ids,
                                   "sampling_params": {"max_new_tokens": 4, "temperature": 0}})[0]
            m = g["meta_info"]
            prime_cached, prime_rep, keys = gen_cached(m)
            # MEASURE: identical text with a 1-token append, through /generate.
            g2 = post("/generate", {"input_ids": ids + [198],
                                    "sampling_params": {"max_new_tokens": 4, "temperature": 0}})[0]
            m2 = g2["meta_info"]
            cached, reported, keys2 = gen_cached(m2)
            p2 = int(m2["prompt_tokens"]); L = p2 - p1
            unc = (p2 - cached) if reported else None
            # The SAME measured prompt through the chat endpoint QUALITY-ARM used.
            c = post("/v1/chat/completions", {"model": MODEL, "messages": msgs + [
                        {"role": "assistant", "content": "OK."},
                        {"role": "user", "content": " the"}],
                     "max_tokens": 4, "temperature": 0.0,
                     "chat_template_kwargs": {"enable_thinking": False}})[0]
            cu = c.get("usage") or {}
            cdet = cu.get("prompt_tokens_details")
            chat_rep = isinstance(cdet, dict) and cdet.get("cached_tokens") is not None
            chat_cached = cdet.get("cached_tokens") if chat_rep else None
            cp2 = cu.get("prompt_tokens")
            expected = (B if target == 0 else target) + L
            emit({"row": "measure", "cell": cell, "target_residue": target, "rep": rep,
                  "aim_tries": tries,
                  "prime": {"P1": m["prompt_tokens"], "cached_tokens": prime_cached,
                            "cached_reported": prime_rep,
                            "cached_tokens_details": m.get("cached_tokens_details"),
                            "keys": keys},
                  "generate": {"P1": p1, "P2": p2, "residue": p1 % B, "L": L,
                               "prompt_tokens": m2["prompt_tokens"],
                               "cached_tokens": cached, "cached_reported": reported,
                               "cached_tokens_details": m2.get("cached_tokens_details"),
                               "uncached": unc, "keys": keys2,
                               "e2e_latency": m2.get("e2e_latency")},
                  "chat": {"P2": cp2, "cached_tokens": chat_cached,
                           "cached_reported": chat_rep,
                           "prompt_tokens_details_raw": cdet},
                  "predicted_one_block": expected,
                  "delta": (unc - expected) if unc is not None else None,
                  "agreement": ("server-null" if unc is None else
                                ("exact" if unc == expected else "off-by-k"))})
            print(f"{cell} rep{rep} P1={p1} res={p1%B} L={L} gen_cached={cached} "
                  f"gen_unc={unc} pred={expected} chat_cached={chat_cached} "
                  f"prime_cached={prime_cached}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
