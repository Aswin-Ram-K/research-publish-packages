#!/usr/bin/env python3
"""CX-V2 independent re-derivation of U9, U4b, U5, U10, U2 figures.

Offline only.  Reads the units' own row files; writes nothing.
Every number printed names the row file it came from.
"""
from __future__ import annotations

import json
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CELLS = REPO / "experiments" / "context-cache" / "cells"


def jl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def med(xs):
    return st.median(xs) if xs else float("nan")


def linfit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    icpt = my - slope * mx
    sst = sum((y - my) ** 2 for y in ys)
    ssr = sum((y - (icpt + slope * x)) ** 2 for x, y in zip(xs, ys))
    return slope, icpt, 1 - ssr / sst


def sign_p_one_sided(deltas):
    w = sum(1 for d in deltas if d > 0)
    nt = sum(1 for d in deltas if d == 0)
    n = len(deltas) - nt
    return sum(math.comb(n, k) for k in range(w, n + 1)) / 2 ** n


print("=" * 78)
print("U9  source:", (CELLS / "U9/u9_trials.jsonl").relative_to(REPO))
rows = jl(CELLS / "U9/u9_trials.jsonl")
print("rows:", len(rows), "roles:", dict(Counter(r["role"] for r in rows)))
lengths = sorted({int(r["length_target"]) for r in rows if r["role"] in ("miss", "hit")})
print(f"{'L':>7} {'n':>3} {'miss_med':>9} {'hit_med':>9} {'ratio':>7} {'delta':>8} {'p1s':>7} {'cached':>10}")
miss_pts, hit_pts, ratio_pts, alldeltas = [], [], [], []
allpos = True
for L in lengths:
    sub = [r for r in rows if int(r["length_target"]) == L]
    mb, hb = {}, {}
    for r in sub:
        if r["role"] == "miss":
            mb[int(r["rep"])] = r
        elif r["role"] == "hit":
            hb[int(r["rep"])] = r
    reps = sorted(set(mb) & set(hb))
    miss = [mb[r]["ttft_ms"] for r in reps]
    hit = [hb[r]["ttft_ms"] for r in reps]
    d = [m - h for m, h in zip(miss, hit)]
    alldeltas += d
    allpos &= all(x > 0 for x in d)
    miss_pts.append(med(miss))
    hit_pts.append(med(hit))
    ratio_pts.append(med(hit) / med(miss))
    print(f"{L:>7} {len(reps):>3} {med(miss):>9.1f} {med(hit):>9.1f} "
          f"{med(hit)/med(miss):>7.4f} {med(d):>8.1f} {sign_p_one_sided(d):>7.4f} "
          f"{sorted({hb[r]['cached_tokens'] for r in reps})}/{sorted({hb[r]['prompt_tokens'] for r in reps})}")
xs = [math.log(L) for L in lengths]
ms, mi, mr2 = linfit(xs, [math.log(v) for v in miss_pts])
hs, hi, hr2 = linfit(xs, [math.log(v) for v in hit_pts])
rs, ri, rr2 = linfit(xs, [math.log(v) for v in ratio_pts])
print(f"power fit miss: L^{ms:.4f} r2={mr2:.4f} | hit: L^{hs:.4f} r2={hr2:.4f} | ratio: L^{rs:.4f} r2={rr2:.4f}")
sm, _, r2m = linfit([float(L) for L in lengths], miss_pts)
sh, _, r2h = linfit([float(L) for L in lengths], hit_pts)
print(f"OLS miss {sm:.6f} ms/token r2={r2m:.4f} ({1000/sm:.0f} tok/s); hit {sh:.6f} ms/token r2={r2h:.4f} ({1000/sh:.0f} tok/s); ratio {sm/sh:.1f}x")
print(f"all {len(alldeltas)} paired deltas > 0: {allpos}; min one-sided p at n=7 = {2**-7:.4f}; two-sided = {2*2**-7:.4f}")

print()
print("=" * 78)
print("U4b source:", (CELLS / "U4b/rows.jsonl").relative_to(REPO))
r4b = jl(CELLS / "U4b/rows.jsonl")
print("rows:", len(r4b), "arms:", dict(Counter(r["arm"] for r in r4b)))
tot = {}
for arm in ("A", "B", "C"):
    arm_rows = [r for r in r4b if r["arm"] == arm]
    tot[arm] = sum(r["uncached_tokens"] for r in arm_rows)
    prompt = sum(r["prompt_tokens"] for r in arm_rows)
    by_branch = {r["branch"]: r["cached_tokens"] for r in arm_rows}
    warm = [r for r in arm_rows if r["branch"] > 1]
    hit = sum(1 for r in warm if r["cached_tokens"] > 0)
    print(f"  {arm}: n={len(arm_rows)} prompt={prompt} uncached={tot[arm]} "
          f"ratio_uncached={tot[arm]/prompt:.4f} cached_by_branch={[by_branch[b] for b in sorted(by_branch)]}")
    print(f"     warm branches hit {hit}/{len(warm)} at cached={sorted({r['cached_tokens'] for r in warm})}")
print(f"B/A = {tot['B']/tot['A']:.4f}  (claim 3.31)")
print(f"C/A = {tot['C']/tot['A']:.6f}  (claim 1.0000)")
print("prompt chars/arm:", {a: sorted({r["chars"] for r in r4b if r["arm"] == a}) for a in "ABC"})

print()
print("=" * 78)
print("U5 source:", (CELLS / "U5/u5_raw.jsonl").relative_to(REPO))
r5 = jl(CELLS / "U5/u5_raw.jsonl")
cond = Counter((r["depth"], r["condition"]) for r in r5)
print("rows:", len(r5), "cells:", dict(cond))
acc = {}
for (d, c), n in sorted(cond.items()):
    sub = [r for r in r5 if r["depth"] == d and r["condition"] == c]
    ok = sum(1 for r in sub if r["correct"])
    acc[(d, c)] = (ok, n)
    print(f"  {d:>6}/{c:<18} {ok}/{n} = {100*ok/n:.1f}%")
print(f"claim 66.3/72.1/70.5/69.5 -> got "
      f"{100*acc[('shallow','shared')][0]/190:.1f}/"
      f"{100*acc[('deep','baseline')][0]/190:.1f}/"
      f"{100*acc[('deep','summarise')][0]/190:.1f}/"
      f"{100*acc[('deep','fork')][0]/190:.1f}")
gold = {k: sum(1 for r in r5 if (r["depth"], r["condition"]) == k and r["retained"]["gold"])
        for k in cond}
print("gold retained:", gold)
# POINTER==NAIVE_APPEND: per-case prompt digest equality across the two arms
bycase = defaultdict(dict)
for r in r5:
    bycase[r["case_id"]][(r["depth"], r["condition"])] = r["prompt_sha256"]
same_sf = sum(1 for c in bycase if bycase[c][("deep", "summarise")] == bycase[c][("deep", "fork")])
print(f"deep summarise prompt_sha256 == fork prompt_sha256: {same_sf}/{len(bycase)} cases")
print("distinct prompt_sha256 overall:", len({r['prompt_sha256'] for r in r5}), "of", len(r5))
print("status/errors:", Counter(r["status"] for r in r5), "errors:", sum(1 for r in r5 if r["error"]))

print()
print("=" * 78)
print("U10 sources:", "cells/U10/u10_rows.jsonl + cells/U10/u10_rows_p23.jsonl")
r10 = jl(CELLS / "U10/u10_rows.jsonl") + jl(CELLS / "U10/u10_rows_p23.jsonl")
print("rows:", len(r10), "phases:", dict(Counter(r["phase"] for r in r10)))
by_len = defaultdict(list)
for r in r10:
    if r.get("length_target") is None:
        continue
    by_len[int(r["length_target"])].append(r)
print(f"{'L':>6} {'L%64':>5} {'n':>3} {'cold0':>7} {'rep1miss':>9} {'rep2_cached':>12} {'prompt_tokens':>16}")
for L in sorted(by_len):
    rs = by_len[L]
    cold = [r for r in rs if r["role"] == "cold"]
    r1 = [r for r in rs if r["role"] == "rep1"]
    r2 = [r for r in rs if r["role"] == "rep2"]
    print(f"{L:>6} {L%64:>5} {len(rs):>3} "
          f"{sum(1 for c in cold if c['cached_tokens']==0)}/{len(cold):<4} "
          f"{sum(1 for x in r1 if x['cached_tokens']==0)}/{len(r1):<7} "
          f"{str(sorted({x['cached_tokens'] for x in r2})):>12} "
          f"{str(sorted({x['prompt_tokens'] for x in cold})):>16}")
mult = [r for r in r10 if r.get("length_target") and int(r["length_target"]) % 64 == 0 and r["role"] == "rep1"]
non = [r for r in r10 if r.get("length_target") and int(r["length_target"]) % 64 != 0 and r["role"] == "rep1"]
a = sum(1 for r in mult if r["cached_tokens"] == 0)
d = sum(1 for r in non if r["cached_tokens"] == 0)
print(f"multiples: {a}/{len(mult)} full misses; non-multiples: {d}/{len(non)}")
try:
    from scipy.stats import fisher_exact
    t = [[a, len(mult) - a], [d, len(non) - d]]
    p2 = fisher_exact(t, alternative="two-sided")[1]
    p1 = fisher_exact(t, alternative="greater")[1]
    print(f"table {t} fisher two-sided p = {p2:.6e} (one-sided {p1:.6e})")
except Exception as exc:
    print("scipy unavailable:", exc)
delays = Counter((r["delay_s"], r["role"]) for r in r10 if r["phase"] == "p2" and r["role"] == "rep1")
print("p2 delay repeats cached profile:", {k: v for k, v in delays.items()})
p2rep = [r for r in r10 if r["phase"] == "p2" and r["role"] == "rep1"]
print("p2 rep1 rows cached!=0:", sum(1 for r in p2rep if r["cached_tokens"] != 0), "of", len(p2rep))
p3rep = [r for r in r10 if r["phase"] == "p3" and r["role"] == "rep1"]
print("p3 rep1 (after unrelated insert) cached!=0:", sum(1 for r in p3rep if r["cached_tokens"] != 0), "of", len(p3rep))
print("every cold role cached==0:", all(r["cached_tokens"] == 0 for r in r10 if r["role"] == "cold"),
      "n_cold =", sum(1 for r in r10 if r["role"] == "cold"))
bad = [r for r in r10 if r["role"] == "rep2" and r["cached_tokens"] != 64 * ((r["prompt_tokens"] - 1) // 64)]
print("rep2 hits violating 64*((L-1)//64):", len(bad), [(r["prompt_tokens"], r["cached_tokens"]) for r in bad])

print()
print("=" * 78)
print("U2 source:", (CELLS / "U2/u2_cache_rows.jsonl").relative_to(REPO))
r2 = jl(CELLS / "U2/u2_cache_rows.jsonl")
print("rows:", len(r2), "arms:", dict(Counter(r["arm"] for r in r2)))
warm = [r for r in r2 if r["arm"] == "warm" and r["cached_tokens"] > 0]
cold = [r for r in r2 if r["arm"] == "cold"]
print(f"warm-with-cache rows: {len(warm)}, distinct lengths: {len({r['prompt_tokens'] for r in warm})}")
res_old, res_new, agree = [], [], 0
for r in warm:
    L = r["prompt_tokens"]
    c = r["cached_tokens"]
    old = c - 64 * (L // 64)
    new = c - 64 * ((L - 1) // 64)
    res_old.append(old)
    res_new.append(new)
    if old == new:
        agree += 1
print(f"residual vs 64*floor(L/64): max_abs={max(abs(v) for v in res_old)} histogram={dict(Counter(res_old))}")
print(f"residual vs 64*floor((L-1)/64): max_abs={max(abs(v) for v in res_new)} histogram={dict(Counter(res_new))}")
print(f"lengths where the two formulas agree: {agree}/{len(warm)}")
print("L mod 64 values seen:", sorted({r["prompt_tokens"] % 64 for r in warm}))
print("any L%64==0 among warm:", any(r["prompt_tokens"] % 64 == 0 for r in warm))
print(f"cold rows cached!=0: {sum(1 for r in cold if r['cached_tokens'] != 0)} of {len(cold)}")
print("lengths min/max:", min(r["prompt_tokens"] for r in warm), max(r["prompt_tokens"] for r in warm))
