#!/usr/bin/env python3
"""Direct proof of the P2 accounting artifact: on the SAME turn, send the
padded prompt (attempt A), then the alignment correction (attempt B), and show
B.cached_tokens == A.prompt_tokens -- i.e. the row's 'cached' is the same turn's
own first attempt, whose prefill the row never records."""
import importlib.util, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rep", HERE / "prompt_o3_repeat.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
renderer = R.load_renderer(); setup = R.load_setup("O3"); url = R.BASE_URL["O3"]
rows = [json.loads(l) for l in (HERE / "rows.jsonl").read_text().splitlines() if l.strip()]
p1_tok = {int(r["turn"]): int(r["prompt_tokens"]) for r in rows if r["arm"] == "P1"}
out = {"salt": R.SALT, "endpoint": url, "turns": {}}
tot = {"p1_unc": 0, "p2_recorded": 0, "p2_true": 0}
for turn in (20, 35, 50, 60, 70, 71):
    st = {"slope": 0.25, "err": 0.0, "base_tokens": p1_tok}
    text, pad = R.p2_text(renderer, turn, 16, 0.25, st)
    a = R.post(url, setup["model"], [{"role": "user", "content": text}])
    pa, ca = a["prompt_tokens"], a["cached_tokens"]
    # the harness's own correction: add the residue to the filler, resend
    delta = (-pa) % 16
    text_b = text + R.FILLER * max(1, int((delta / 0.25) // len(R.FILLER)))
    b = R.post(url, setup["model"], [{"role": "user", "content": text_b}])
    pb, cb = b["prompt_tokens"], b["cached_tokens"]
    p1 = [r for r in rows if r["arm"] == "P1" and int(r["turn"]) == turn][0]
    rec = [r for r in rows if r["arm"] == "P2" and int(r["turn"]) == turn][0]
    out["turns"][str(turn)] = {
        "P1": {"prompt": p1["prompt_tokens"], "cached": p1["cached_tokens"],
               "recorded_unc": p1["uncached_tokens"]},
        "P2_attempt_A": {"prompt": pa, "cached": ca, "unc": pa - ca},
        "P2_attempt_B": {"prompt": pb, "cached": cb, "unc": pb - cb},
        "P2_recorded_row": {"prompt": rec["prompt_tokens"], "cached": rec["cached_tokens"],
                            "unc": rec["uncached_tokens"]},
        "B_cached_equals_A_prompt": cb == pa,
        "p2_true_unc_for_turn": (pa - ca) + (pb - cb),
    }
    tot["p1_unc"] += p1["uncached_tokens"]; tot["p2_recorded"] += rec["uncached_tokens"]
    tot["p2_true"] += (pa - ca) + (pb - cb)
out["means"] = {k: round(v / 6, 2) for k, v in tot.items()}
out["reading"] = ("p2_true_unc ~= p1_unc means the arm's recorded saving is the same-turn "
                  "self-hit; the first attempt's prefill is not in the row")
(HERE / "probe_p2_cost.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
