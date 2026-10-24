#!/usr/bin/env python3
"""CX-V2: re-derive U4's head-line numbers from cells/U4/u4_rows.jsonl +
u4_events.jsonl + u4_runlog.json (the unit's own files; nothing re-run live)."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent / "U4"
REPO = HERE.parents[3]

rows = [json.loads(l) for l in (CELL / "u4_rows.jsonl").read_text().splitlines() if l.strip()]
events = [json.loads(l) for l in (CELL / "u4_events.jsonl").read_text().splitlines() if l.strip()]
runlog = json.loads((CELL / "u4_runlog.json").read_text())

print("rows", len(rows), "events", len(events))
print("policies:", dict(Counter(r["cell"].split("/")[2] for r in rows)))

# ---- 1. the 372/372 warm-append claim --------------------------------------
break_turns = {(e["cell"], int(e["turn"])) for e in events}
warm = [r for r in rows if r["rep"] == 1 and r["turn"] >= 2 and (r["cell"], r["turn"]) not in break_turns]
res = [r["uncached"] - (r["prompt_tokens"] % 64) for r in warm]
nonzero = [x for x in res if x != 0]
print(f"\nwarm append rows: {len(warm)}; residual(uncached - L%64) != 0: {len(nonzero)}/{len(warm)}")
print("  residual histogram:", dict(sorted(Counter(res).items())))
print(f"  residual range: {min(res)}..{max(res)} tokens; median {sorted(res)[len(res)//2]}")
print("  cached_tokens vs 64*floor(L/64): rows where cached < law:",
      sum(1 for r in warm if r["cached_tokens"] < 64 * (r["prompt_tokens"] // 64)), "/", len(warm))
maxprompt = max(r["prompt_tokens"] for r in rows)
tot_prompt = sum(r["prompt_tokens"] for r in rows)
print(f"  max prompt_tokens in file: {maxprompt}; sum over all rows: {tot_prompt}")

# which cells
percell = Counter(r["cell"] for r in warm)
print("  warm rows per cell:", dict(percell))

# ---- 2. paired fork - summarise deltas on break_cost ------------------------
def index(rows):
    out = defaultdict(dict)
    for r in rows:
        out[r["cell"]][r["turn"]] = r
    return out

idx = index(rows)
def break_cost(row):
    return row["uncached"] - (row["prompt_tokens"] % 64)

pairs = []
for e in events:
    if e["compaction"] != "fork":
        continue
    s = e["cell"].replace("/fork/", "/summarise_in_place/")
    fr, sr = idx[e["cell"]].get(int(e["turn"])), idx[s].get(int(e["turn"]))
    if fr is None or sr is None:
        continue
    pairs.append({
        "session": e["session"], "turn": int(e["turn"]),
        "fork": break_cost(fr), "summ": break_cost(sr),
        "delta": break_cost(fr) - break_cost(sr),
        "d_prompt": fr["prompt_tokens"] - sr["prompt_tokens"],
    })
d = [p["delta"] for p in pairs]
print(f"\nfork-vs-summarise event pairs: {len(pairs)}; zero: {sum(1 for x in d if x==0)}; "
      f"median {sorted(d)[len(d)//2]}; max|d| {max(abs(x) for x in d)}")
print("  deltas:", d)
print("  prompt-token offsets (fork - summarise) at those turns:",
      sorted({p["d_prompt"] for p in pairs}))
print("  deltas explained by the salt-induced token offset + 64-grid rounding:",
      all(p["delta"] in (-128, -64, 0, 64, 128) for p in pairs))
for p in pairs:
    if p["delta"]:
        print(f"   nonzero: {p['session']} turn {p['turn']} delta {p['delta']:+d} "
              f"(prompt offset {p['d_prompt']:+d})")

# ---- 3. first post-event turn cached=0 -------------------------------------
first = []
for e in events:
    r = idx[e["cell"]].get(int(e["turn"]))
    if r is not None:
        first.append(r)
print(f"\nfirst post-event rows: {len(first)}; cached==0: {sum(1 for r in first if r['cached_tokens']==0)}")
print("  session totals per policy:")
for pol in ("summarise_in_place", "fork", "sliding_window", "none"):
    sel = [r for r in rows if r["cell"].split("/")[2] == pol]
    print(f"   {pol:<18} rows={len(sel)} prompt={sum(r['prompt_tokens'] for r in sel)} "
          f"uncached={sum(r['uncached'] for r in sel)} "
          f"hit_rate={1-sum(r['uncached'] for r in sel)/sum(r['prompt_tokens'] for r in sel):.4f}")

# ---- 4. the renderer digest U4 actually ran -------------------------------
b = runlog["source_pins_before"]["render.py"]
a = runlog["source_pins_after"]["render.py"]
print(f"\nrender.py pinned before {b['sha256']} ({b['mtime']}) / after {a['sha256']} ({a['mtime']})")
print("source_changed_during_batch:", runlog["source_changed_during_batch"])
print("mode:", runlog["mode"], "renderer:", runlog["renderer"], "wall_started:", runlog["wall_started"])
cur = REPO / "src/resextract/context/render.py"
import hashlib
print("current render.py sha256:", hashlib.sha256(cur.read_bytes()).hexdigest())
print("rows policy values:", dict(Counter(r["policy"] for r in rows)))
