#!/usr/bin/env python3
"""Instrument probe: is cached_tokens a contiguous-prefix count, or an
alignment-padded count?  4-6 requests, same endpoint, same salt as the repeat."""
import importlib.util, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rep", HERE / "prompt_o3_repeat.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
renderer = R.load_renderer()
setup = R.load_setup("O3"); model = setup["model"]; url = R.BASE_URL["O3"]

def send(text):
    r = R.post(url, model, [{"role": "user", "content": text}])
    return {"prompt_tokens": r["prompt_tokens"], "cached_tokens": r["cached_tokens"],
            "text_sha256": R.sha256_text(text), "chars": len(text)}

base = R.p2_text(renderer, 71, 16, 0.25, {"slope": 0.25, "err": 0.0})[0]
out = {"salt": R.SALT, "endpoint": url}
r1 = send(base)
for _ in range(4):
    if isinstance(r1["prompt_tokens"], int) and r1["prompt_tokens"] % 16 == 0:
        break
    delta = (-int(r1["prompt_tokens"])) % 16
    pad = " PAD" * max(1, int(round(abs(delta) / 0.25)) // 2)
    base = R.p1_text(renderer, 71) + " PAD" * max(1, (len(base.split("PAD")) - 1) + int(delta / 0.25))
    r1 = send(base)
out["aligned"] = r1
out["aligned_repeat"] = send(base)
# same length, one sha8 swapped deep inside the pointer index (~60% in)
import re
m = list(re.finditer(r"\| [0-9a-f]{8} \|", base))
out["n_sha8_sites"] = len(m)
if m:
    site = m[int(len(m) * 0.6)]
    swapped = base[:site.start()] + "| deadbeef |" + base[site.end():]
    assert len(swapped) == len(base)
    out["midchange"] = send(swapped)
    out["midchange_byte_offset"] = site.start()
    out["midchange_char_fraction"] = round(site.start() / len(base), 4)
# control: a prompt that is genuinely new after the scaffold (diverges at ~scaffold end)
fresh = renderer.SCAFFOLD + "RUN-SALT: " + R.SALT + "\nFRESH RUN %s\n" % R.sha256_text(base)
out["fresh"] = send(fresh)
out["reading"] = ("prefix semantics: a mid-change deep in the prompt drops cached to the block "
                  "before the change; padding semantics: cached stays near prompt-16")
(HERE / "probe_midchange.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
