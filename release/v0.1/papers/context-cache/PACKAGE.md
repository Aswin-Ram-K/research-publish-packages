# PACKAGE.md — context-cache findings, publishable package

**Open this first.** Everything below is re-derivable from committed rows by the commands in
[Reproduction](#7-reproduction). Nothing here is re-measured or re-argued: the manuscript is
`MANUSCRIPT.md`, the claim ledger is `CLAIMS.md`, the caveats are `GAPS.md`.

- Manuscript (revised): [`MANUSCRIPT.md`](MANUSCRIPT.md) — owned by unit X-SYNTH, referenced not edited here.
- Claim ledger: [`CLAIMS.md`](CLAIMS.md) — one row per claim, every value with a recompute command
  (the total is printed by `COVERAGE GUARD` / `verify_package.py`, never typed here).
- Evidence index: [`EVIDENCE.md`](EVIDENCE.md) · Run manifest: [`RUN.json`](RUN.json).
- Claim → function → cell → config: [`READER-MAP.md`](READER-MAP.md).
- Integrity gate: [`verify_package.py`](verify_package.py) (exit 0 required) — a **structural**
  census of `CLAIMS.md`, not a re-derivation of its values (see §9).

---

## 1. What was asked

Can a coding agent's context be **moved and compacted** — forked, summarised, appended to —
without silently changing what the model sees, and what does each move cost on a real
prefix-cache stack? The question decomposes into three: **(i)** does the renderer reproduce the
parent context byte for byte, **(ii)** what does a cache hit actually save, and **(iii)** when a
context is rewritten, what is the true bill.

## 2. What was measured

| Cell | What it measures | Scale |
|---|---|---|
| U5 | pointer-fork vs naive-append byte identity, retention, gold-line retention | 760 rebuilt cells, 190 cases, 4 conditions |
| U4 | summarise vs "fork" chains under U4's driver | 438 rows, 54 events, 44-turn chains |
| U4b | fan-out placement (branch late vs branch early) | 24 requests |
| U9 | hit vs miss latency across six lengths | 139 requests, 42 paired deltas |
| U2 / U4 / U10 | the 64-token cache grid: repeats, appends, the boundary rule | 88 + 438 + 120 rows |
| U15 | decisive four-arm comparison R/F/A/C | 160 rows |
| G1 | decomposition of the 1.700× ratio | 264 rows, 6 break events |
| G3 / WIN-SGL | SGLang grid and pager at `page_size` 1/64/128 | 888 + 1,800 rows |
| WIN-VLLM | vLLM grid and battery, same weights | 692 rows, 3 configs |
| MOE-VLLM | occamy-1.0 on vLLM 0.27.1, the MoE cell of the 2x2 | 306 rows, one config (V3) |
| DENSE-SGL | qwen3.5-9b (dense) on SGLang, the dense cell of the 2x2 | 894 rows, 32k + 64k battery, one config (P1) |
| TUNED | grid under `--disable-chunked-prefix-cache` + SLRU | 289 rows |
| G3-LIMIT-V2 | compaction forced by a real 32k/64k budget | 2,780 rows, 18 compactions |
| G5 | race-free fan-out | 8 fan-outs × 8 branches |
| M4 | resident capacity under eviction pressure | 327 rows, 1.5017× pressure |

All rows under `experiments/context-cache/cells/**`; digests in `CLAIMS.md` "Source rows and digests".

## 3. What the answer is

1. **A pointer fork can be free at the renderer.** POINTER and NAIVE_APPEND render
   **760/760 byte-identically, 0 bytes differing** (C01). Renderer identity is not the
   bottleneck.
2. **A cache hit is worth 30–100× at scale.** At 31,415-token prefixes, prefill falls
   **7,541.9 ms → 231.6 ms** (C32); the hit/miss ratio falls as **L^-0.7837** (C33), so hits are
   not free — they still cost **4.66 µs/token** (C34).
3. **The grid is quantised per stack, and the quantum differs per engine:** SGLang 64,
   vLLM 1088/1056/2096, TUNED 64 — **5 distinct units across 7 stacks** (C55, C56, C57). The
   grid holds exactly for byte-identical repeats (44/44, C37) and **fails on every append**
   (372/372, C38).
4. **Compaction is not free, and its cost is mostly steady state, not the break.** Only
   **7.8 %** of the excess is break cost; **92.2 %** is the cost of carrying a shorter and
   shorter cached prefix (C22). Compaction forced by a real budget costs
   **+134.6 to +747.2 uncached tokens per turn on average** after the boundary — twelve arm
   means over 27-89 turns, **-927 to +5,473 on a single turn**, with every one of the twelve
   arms below its baseline on at least one turn — and nothing before it (C62).
5. **Per-turn uncached cost is not predicted by the grid unit** (C60) — the unit says where
   boundaries fall, not what a turn costs.
6. **The engine sets the bill; the model sets it only under vLLM.** With the full 2x2 measured —
   two checkpoints (occamy-1.0 MoE, qwen3.5-9b dense) on two engines (SGLang, vLLM 0.27.1), one
   shared 32k/71-turn schedule (prompt prefix digests and lengths equal on every cell pair) —
   the engine main effect is **+549.33** uncached tokens per turn, 95 % CI [462.4, 631.9],
   **1.7523x** the mean (2.3058x on the MoE, 1.1987x on the dense) and **54.6 %** of the
   1,006.2306 grand mean, while the model main effect is **-400.02** [-474.2, -326.5] (8 of 71
   turns positive). The model effect is engine-conditional: **-803.65** under vLLM (0.5224x)
   against **+3.61** under SGLang (1.0049x, 1 of 71 paired turns positive), an interaction of
   **-403.63** — under SGLang both checkpoints are paged on the same 64-token grid, while under
   vLLM each checkpoint's resolved block (1,088 / 2,096) sets its own bill (C63, §9b).
   **Supersession:** the pre-MTP figures that used to stand here — engine **+1,225.18**
   [1,132.2, 1,313.3], model **+275.83**, model-within-vLLM **+548.06**, interaction **+272.23**,
   **2.6738x** / **91.2 %** — are superseded, not live: the Round-1 vLLM dense cell ran with
   `--speculative-config mtp`, and removing it re-measured that cell 2,230.7782 -> 879.0669
   uncached tokens/turn (a 2.54x drop). The model effect is therefore no longer a small positive
   quantity; it is negative under vLLM and near zero under SGLang.

## 4. What did not work — negative results, stated as results

These are results. A package that hides them is worthless.

- **The pager does not change the grid.** `--page-size 64` is **byte-identical to production**:
  900 paired rows, **887/888 identical** to S0, gcd stays **64**, odd-unit rows stay **351**
  (C57, C58). Changing the page size moves the grid by exactly one block in the one condition
  that moved it at all, with paired TTFT ratio median **1.005** — no measurable latency effect,
  and no gain. The pager knob is a no-op for this workload.
- **HiCache is unverified for hybrid checkpoints — not tested.** The earlier wording ("a no-go
  … does not support the HiCache path") is **withdrawn** (CACHE-AUDIT, 2026-10-23): it rested on
  a GitHub-issue error string that carries no source URL and that the cited thread does not
  carry for this build (`0.0.0.dev1+g4ccff141d`), while the same server runs the Mamba-aware tree
  (`metrics_cache_type UnifiedRadixCache`) and the SGLang docs pin L2 capacity as its lever
  (`GAPS.md` G16). No claim in `CLAIMS.md` rests on it either way. The correct status is **not
  attempted**, not "measured to fail" — treat it as an open option, not a dead end.
- **Chunked-prefix cannot start.** The S3/chunked-prefix path did not start at all. Every grid
  claim in §9a is therefore measured under `--disable-chunked-prefix-cache` or a stack where it
  is off (C59), and **no claim in this package depends on chunked-prefix behaviour it could not
  obtain.** An unstartable configuration is a missing experiment, not a null result.
- **vLLM costs ~3.1× per turn on the same weights.** S0 (SGLang, 32k) **725.74** uncached/turn
  at hit 0.974242 vs V1 (vLLM) **2230.8** at hit 0.869037 — ratio **3.074×** (C51), and
  **3.0176×** on V1/S0 in C60. Same model weights, different scheduler and cache granularity.
- **slru is indistinguishable from lru.** With the radix policy at `slru` under 1.505083×
  pressure, the TUNED grid is **10 hot rows, all multiples of 64, gcd 64, 3 odd-unit** (C59) —
  the same shape as the `lru` baseline. The eviction policy change did not move the observable.
- **The 1.700× fan-out ratio did not survive decomposition.** U15 observed A/R = **1.7002359**
  (C21), but G1's per-break decomposition gives E/F = **1.0384615** with only **2 of 6** break
  events within 10 % (C44), and `u15_1_700x_survives_decomposition=False`. The ratio is real as
  an observation and **wrong as a causal claim**: it is post-compaction **window truncation**,
  not break-event cost. The break-only counterfactual would score **1.068×**, not 1.700× (C24).
- **The "fork" arms never forked.** In U5/U4 the fork prompts are **byte-identical to the
  summarise prompts** (C03, 190/190), and U4's driver rendered every arm through one renderer
  and never imported the pointer fork (C13). The edit-vs-fork hypothesis is **untested at n>0**,
  not refuted; the "REFUTED" in U4's handoff is superseded (C13, C16, `CLAIMS.md` correction 3).
- **Compaction buys accuracy nothing.** MCQ accuracy moves at most **2.632 points** and no
  difference is significant (C08); the compacted arms lose the planted gold line **190/190 →
  0/190** (C09) while baseline keeps it **190/190**. Compaction costs content and saves nothing
  measurable.

## 5. Where every number lives

| You want | Open |
|---|---|
| A number's value and its command | [`CLAIMS.md`](CLAIMS.md) |
| Which function recomputes claim Cxx, from which cell, under which config | [`READER-MAP.md`](READER-MAP.md) |
| The code that recomputes | [`recompute.py`](recompute.py) (C02–C60, C62, C63; `grid_guard` = C61) |
| C01 and C16, computed by the independent verifier's own scripts | `experiments/context-cache/cells/CX-V2/u5_recon.py`, `…/u4_recon.py` |
| Raw rows and their digests | `experiments/context-cache/cells/**` |
| What the paper claims in prose | [`MANUSCRIPT.md`](MANUSCRIPT.md) |
| What is *not* claimed and why | [`GAPS.md`](GAPS.md) |
| How to check the package itself | [`verify_package.py`](verify_package.py) |

Claims that were corrected against their source cards (7 of them) are tabled at the end of
`CLAIMS.md` under "Corrections to the source cards" — the rows won, and each correction names the
section it lands in.

## 6. Live-required status

**No claim in `CLAIMS.md` is live-required.** Every claim recomputes from files already on disk.
The reproduction makes **0 live requests** and does not need the GX10 endpoint.

Substitutes for the live endpoint: for C01/C02/C03/C07–C10 (`u5_recon.py` rebuilds the 760 cells
from `cells/U5/u5_raw.jsonl`); for C16 (`u4_recon.py` rebuilds the chains from
`cells/U4/u4_rows.jsonl`). Collection originally used the endpoint; nothing in the package does.

## 7. Reproduction

```bash
cd "<workspace>"

# 1. every stored-value claim (C02..C60, C62, C63) + the C61 grid guard — reads only cells/**/rows
.venv/bin/python papers/context-cache/recompute.py all

# 2. the two claims the independent verifier owns (C01, C16)
.venv/bin/python experiments/context-cache/cells/CX-V2/u5_recon.py
.venv/bin/python experiments/context-cache/cells/CX-V2/u4_recon.py

# 3. the package's own integrity gate (must exit 0)
.venv/bin/python papers/context-cache/verify_package.py

# 4. one claim on its own
.venv/bin/python papers/context-cache/recompute.py C62
```

Use `.venv/bin/python`, not bare `python3`: the runner-side scripts import `resextract`.

Verified tails (2026-10-23, exit codes checked):

```text
# 1
GRID GUARD ok    TUNED: 289 rows in TUNED
GRID GUARD PASS  7/7 configs

60 claims checked, all match
COVERAGE GUARD ok    every CLAIMS.md table row is a claim row or a declared source key (nothing invisible to the census)
COVERAGE GUARD ok    every documented claim has a runner: 63/63 (61 in recompute.py, 2 script-backed)
COVERAGE GUARD ok    claim ids are contiguous C01..C63 (no row lost above the maximum)
COVERAGE GUARD ok    every runner has a claim row: 61/61
COVERAGE GUARD ok    census matches runner set: 63 ids
COVERAGE GUARD PASS  63 claims documented, 61 runnable here + 2 script-backed
```

```text
# 2a
POINTER == NAIVE_APPEND byte-identical: 760/760
retention flags reproduce: 2280/2280
gold-line retained (rebuilt): {('shallow','shared'):0, ('deep','baseline'):190, ('deep','summarise'):0, ('deep','fork'):0}
# 2b
reconstruction check (head digest == live row prefix_sha256): summarise 44/44, fork 44/44
turn-by-turn: full-prompt digest equal 0/44; head equal 0; body digest equal 11; body bytes equal 11
u4_cell.RENDER = naive_append ; POINTER_FORK never imported: True
```

```text
# 3
verify_package: PASS — 63 claims in CLAIMS.md, 63 mapped 1:1, 2 script-backed + 61
recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none
```

`60 claims checked` is the count of *stored-value* claims held in `recompute.py`; C01 and C16 are
the two external scripts, and C61 is the guard that prints its own line. 60 + 2 + 1 = **63**,
the number of claims in `CLAIMS.md`. The earlier "58"/"52" figures in this file were wrong and
are superseded by the run above.

That accounting is **no longer prose**. `recompute.py all` now ends with `COVERAGE GUARD`, which
derives all three numbers — claim ids from `CLAIMS.md`, runners from `recompute.py`, script-backed
claims from each claim's own command cell — and fails the run on any disagreement (a claim with no
runner, a runner with no claim row, a duplicate row, a missing script, or a table row it cannot
parse at all). This closes the hole recorded in `orchestration/handoffs/V-CLAIMAUD2.json`: a stale
count typed here passed every guard, which is how the "58" figure survived four new claims.

## 8. Claims status

**Every claim in the ledger is re-derived. None is UNVERIFIED.** `verify_package.py` prints
`UNVERIFIED: none` and fails if any row here or in the map carries an UNVERIFIED mark that
`PACKAGE.md` does not also state.

That sentence is about **claim values**, not about scope. Ten sections of `GAPS.md` are open
limitations (2 closed, 3 narrowed, 10 open, 1 unverifiable — `state/gap-ledger.json`, with the
`GAP-TRIAGE` decisions and evidence in `state/gap-triage.json`). `UNVERIFIED: none` means every
claim has a runner and a cell with rows; it does not mean the unmeasured regimes named in
`GAPS.md` were measured.

Ten claims carry a scope restriction rather than an unverified value — C21, C22, C24 (causal
reading superseded by G1/C44), C06 (value 5.3922 replaces the card's 3.99), C13/C16
(untested-at-n>0 hypothesis), C44 (2/6 within noise), C53 (G5 replaces the 3.31/5.39 band), C62
(one cell, one trigger policy), C63 (one 32k band, one seed, two checkpoints). See `CLAIMS.md`
"Supersessions by G1" and "What is not claimed here", and `GAPS.md`.

## 9. Package integrity

- `verify_package.py` fails if a claim id in `CLAIMS.md` is missing from `READER-MAP.md`,
  duplicated, or unknown; if a named recompute function/script does not exist; if a referenced
  cell is absent or has zero rows; or if an UNVERIFIED claim is not stated here.
- `verify_package.py` is a **structural** gate: it checks that every claim in `CLAIMS.md` is
  mapped, backed and backed by a cell with rows. It does **not** recompute a single value —
  `recompute.py all` does that, and the two are separate commands on purpose. Exit 0 from this
  gate therefore means "the ledger is complete and every claim is answerable", not "every value
  is right". The value check is §7 step 1.
- **Every `CLAIMS.md` table row is counted or refused.** Both guards derive their counts from row
  shape, so a row they could not parse used to be invisible to both (recorded in
  `orchestration/handoffs/V-FINAL2.json`): a planted `| Not a claim at all, … |` row left this
  gate at exit 0.
  Each guard now refuses any table row that is neither a `C\d\d` claim row, a header or
  separator, a row of the declared source-key table, nor a row of the numbered corrections
  table. Red→green, verified this pass: the planted row → `verify_package: FAIL` with
  `CLAIMS.md:202: unrecognised row, invisible to the claim census` (exit 1) **and**
  `COVERAGE GUARD FAIL  1 CLAIMS.md row(s) invisible to the census` (exit 1); with the row
  removed, both exit 0.
- **Red→green, verified this pass:** a copy of `READER-MAP.md` with `C52` removed →
  `verify_package: FAIL / - missing claim ids in READER-MAP: C52`, **exit 1**; the real map →
  `verify_package: PASS … 63 mapped 1:1`, **exit 0**. Also red on a nonexistent function
  (`C62: recompute function not in recompute.py: c62_does_not_exist`, exit 1) and on a
  zero-row cell (exit 1).
