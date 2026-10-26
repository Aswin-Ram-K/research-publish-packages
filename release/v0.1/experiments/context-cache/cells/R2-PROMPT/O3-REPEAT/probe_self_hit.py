#!/usr/bin/env python3
"""Cache-independent proof (fresh nonce => nothing of these bytes was cached):
does the alignment correction hit the SAME TURN's first attempt?"""
import importlib.util, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rep", HERE / "prompt_o3_repeat.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
renderer = R.load_renderer(); setup = R.load_setup("O3"); url = R.base_url = R.BASE_URL["O3"]
NONCE = "SELFHIT-PROBE-20261024T1118Z-b7"
def send(txt, label):
    r = R.post(url, setup["model"], [{"role": "user", "content": txt}])
    return {"label": label, "prompt": r["prompt_tokens"], "cached": r["cached_tokens"],
            "unc": (r["prompt_tokens"] - r["cached_tokens"]) if r["cached_tokens"] is not None else None}
base = R.p1_text(renderer, 71) + "\n" + NONCE + "\n"
out = {"nonce": NONCE, "endpoint": url, "steps": []}
a0 = send(base, "A0 fresh base (cold)")
out["steps"].append(a0)
padA = " PAD" * 20                       # unaligned first attempt
a1 = send(base + padA, "A1 base + 20 pad (first attempt)")
out["steps"].append(a1)
padB = " PAD" * 24                       # +4 tokens: the correction's extra filler
a2 = send(base + padB, "A2 base + 24 pad (corrected attempt)")
out["steps"].append(a2)
a3 = send(base + padB, "A3 resend identical")
out["steps"].append(a3)
out["self_hit"] = (a1["prompt"] is not None and a2["cached"] is not None
                   and abs(a2["cached"] - a1["prompt"]) <= 16)
out["p2_true_cost_two_attempts"] = (a1["prompt"] - a1["cached"]) + (a2["prompt"] - a2["cached"]) if a1["cached"] is not None and a2["cached"] is not None else None
out["p1_cost_single_attempt"] = a0["prompt"] - (a0["cached"] or 0)
out["reading"] = ("self_hit true => A2.cached is A1's prompt, so the row written for the "
                  "corrected attempt reports the same turn's earlier prefill as a cache hit; "
                  "the arm's recorded uncached tokens are only A2-A1.delta, not the turn's work")
(HERE / "probe_self_hit.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
