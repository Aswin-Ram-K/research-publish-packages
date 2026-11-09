# ARM-RECONCILE - two impossible claims about `pointer-stable`, adjudicated from rows

**Unit** `V-ARM-RECONCILE` · **offline** (0 inference requests) · **no existing document edited**

**Verdict: `CLAIM_A_DEAD__CLAIM_B_SURVIVES`**

`prompt_tokens` is a **per-request** (cumulative-prefix) size. Summed over turn rows it reproduces Claim B's
104,468 exactly. Claim A's `217k` is a **column total of a different arm in a different grid**, and its
`1,867` matches no `pointer-stable` row anywhere. No arm in RUN-C-V2 exceeds **34,279** prompt tokens; the
corpus-wide maximum is **51,216**. Claim B is the surviving description of the same arm.

> **Correction (2026-10-26):** the `1,867` quoted above is register entry `WI-009`, **withdrawn**: `pointer-stable`
> G4 turn 1 measures **967** prompt tokens and no row on disk carries 1,867 (nearest 1,864 x1 / 1,870 x13, both
> G1 transcript-compact/transcript-grow turn 1). It is quoted here only to be refuted; the citable first value is
> **967** per `experiments/ptr-engine/measure/ARM-RECONCILE.json`.


## 1. Pinned files (`sha256` before and after; unchanged)

| file | bytes | sha256 | role |
|---|---|---|---|
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | 769,456 | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` | G4 / RUN-C-V2 rows (192 rows, 4 arms x 48) |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26.jsonl` | 202,251 | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` | G1 / stage1 rows (source of the `1,870` T1) |
| `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl` | 169,988 | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` | G7 / V4-TOOLS rows (source of the `216,951`) |
| `experiments/ptr-engine/measure/LATENCY-REPORT.json` | 123,851 | `2d84d71345745faf0e5e61e56b535aea674eddf1940c5d5286b412ebb9446171` | Claim B's host |
| `experiments/ptr-engine/longrun/run_longrun.py` | - | `939c225c052319b91ef7df0e69678b85ae855fc9bb3fbf293441b7bafb99b1c3` | Claim A's code citation |

All 14 `rows-*.jsonl` files in `experiments/ptr-engine/measure/` were enumerated. `LATENCY-REPORT.json`'s
`grids[]` map names the rows file per grid: G4 -> `rows-longrun-c-2026-10-26.jsonl`, whose sha matches the
`row_files` entry, so the grid->file attribution is pinned, not assumed.

## 2. Field semantics - where the 50x error lives

`pointer-stable`, G4, first six turn rows' `prompt_tokens`:

```
[967, 1752, 2194, 2215, 2200, 2195]
```
A cumulative prefix of ~0.97k growing to an asymptote ~2.2k. The per-turn **increment** is the diff, never the value.

| reading | value | reproduces 104,468? |
|---|---|---|
| (i) sum of `prompt_tokens` over turn rows | **104,468** | **yes, exactly** |
| (ii) last - first | 1,230 | no |
| (iii) mean per turn | **2,176.4167** | yes, = (i)/48 (Claim B's `2,176.4`) |

Claim B is reading (i). Claim A read a **sum** as an **endpoint**.

## 3. Claim A's trajectory, refuted number by number

| Claim A clause | rows say | verdict |
|---|---|---|
| starts at 1,867 tokens | `pointer-stable` T1 in G4 = **967**. No row anywhere has 1,867; nearest 1,864 (1 row) / 1,870 (13 rows), and 1,870 is `transcript-compact`/`transcript-grow` T1 in **G1** | refuted |
| reaches 217k at turn 48 | turn 48 = **2,197**. `216,951` is the **sum** over G7 V4-TOOLS `pointer-stable`'s **68** rows | refuted |
| slope 1.21x/turn | **1.017614x/turn** (4.4433 tok/turn). Also self-inconsistent: 1,867->217,000 implies 1.1065x/turn at n=48 and 1.2297x at n=24, so 1.21x only coheres at n~23 intervals | refuted |
| r = 0.9799 | OLS r = **0.3265**, log-linear r = **0.3113**. No tested cumulative-series reconstruction gives 0.9799 (best: G1 compact cumsum 0.9466) | refuted |
| `run_longrun.py:436` reset at 6,000 vs `:441` reset at 8,000 | `:436` is `value = int(raw)`, `:441` is a `CapUsageError` line, both inside `allocation_for()`. No 6,000 constant exists; the only 8000 is `TOOL_READ_CAP_CHARS` at `:209`. `wall_tokens` = 65536, from the fixture (`0a07db1b`) | refuted |
| `transcript-grow` 0.85x/turn, reaches ~620k | **1.061068x/turn** (676.9636 tok/turn), 2,114->34,279; the 901,109 is a 48-turn **sum** (mean 18,773.1), not a prompt size | refuted |
| p50 advantage = 98.7 % prefix cache | measured cached share = **0.871157** | unsupported |

**Where the two numbers came from.** `216,951` is G7's total. `1,867` is nobody's first value. The pair is a
concatenation across grids *and* across arms - a transcript arm's T1 from G1 stitched onto a pointer arm's
68-row cumulative total from G7 - so it describes no trajectory that exists on disk.

## 4. Recomputed per-arm table (G4 / RUN-C-V2, n=48 each, all `kind=="turn"`)

| arm | n | first | last | mean/turn | total | slope tok/turn | x/turn | r (OLS) | log-linear r | cached share | max prompt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `pointer-stable` | 48 | 967 | 2,197 | 2,176.42 | 104,468 | +4.4433 | 1.017614 | +0.3265 | +0.3113 | 0.871157 | 2,249 |
| `transcript-grow` | 48 | 2,114 | 34,279 | 18,773.10 | 901,109 | +676.9636 | 1.061068 | +0.9990 | +0.9383 | 0.947952 | 34,279 |
| `transcript-compact` | 48 | 2,114 | 5,640 | 3,867.02 | 185,617 | +74.9779 | 1.021098 | +0.9999 | +0.9923 | 0.953361 | 5,640 |
| `lease-reopen` | 48 | 433 | 422 | 429.75 | 20,628 | -0.0051 | 0.999453 | -0.0079 | -0.0096 | 0.874927 | 466 |

Turn-only fit is identical to the all-rows fit because every row in this grid is `kind=="turn"` (48/48).
`cached_tokens` is present on all rows (0 nulls; `cached_reported` true on 46-47 of 48 per arm).

**Largest observed value in the corpus:** 51,216 prompt tokens - `experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl`, arm `transcript-grow`, turn 14. **No arm reaches 200k** anywhere.

## 5. Cache share - Claim A's 98.7 % is not on any disk

| arm | cached tokens | prompt tokens | cached share |
|---|---|---|---|
| `pointer-stable` | 91,008 | 104,468 | **0.871157** |
| `transcript-grow` | 854,208 | 901,109 | **0.947952** |
| `transcript-compact` | 176,960 | 185,617 | **0.953361** |
| `lease-reopen` | 18,048 | 20,628 | **0.874927** |

`pointer-stable` is **0.8712**, the second-**lowest** share in the grid. The claim is also incoherent in its own
terms: 0.987 of a 2.1k prompt is 2,076 cached tokens; 0.987 of a 110k prompt is 108,570. The rows support
neither a 110k prompt nor a 0.987 share. **`98.7 %` is unverifiable from disk.**

## 6. Mechanism, per arm

- `pointer-stable` - **supported** as *stable*: 967->2,197, span 1,230 tokens, slope 4.4433 tok/turn. **Unsupported** as 'grows like a transcript'.
- `transcript-grow` - **supported**: 2,114->34,279, 16.2x span, slope 676.9636 tok/turn, r 0.99896.
- `transcript-compact` - **supported as sub-linear growth** (1.0211x/turn, 74.9779 tok/turn); **unsupported as a digest arm** - 0 `kind=="digest"` rows and no eviction, so the compact/digest mechanism is not exercised by these rows.
- `lease-reopen` - **unsupported** as *reopen*: `lease == 1` on 48/48 rows and `lease_reopen_turns` is absent from every fixture, so it never reopened. Supported only as flat (mean 429.75, slope -0.0051).

**The difference between the two fastest arms is prompt SIZE, not cache-hit rate.**
`pointer-stable` mean prompt 2,176.4 vs `transcript-compact` 3,867.0 (**1.78x smaller**), while its cached
share is 0.8712 vs 0.9534 (**8.2 points lower**). A lower cache fraction on a smaller prompt cannot produce
the advantage, so Claim A's cache explanation is not merely unmeasured - it points the wrong way.

## 7. Consequences - what must change (nothing edited here)

- **`board post #891 (ws:78cead56, round 77, ARM-INTEGRITY F0)`** - strike - retracted in #893 and its four numbers refuted here
- **`orchestration/handoffs/ARM-INTEGRITY.json`** - keep - its slopes (2.72-4.85 tok/turn) and max_prompt_tokens_any_grid 34,279 AGREE with this reconciliation; only the board post's numbers were wrong
- **`RUN-A* precondition 10`** - must change - a precondition assuming pointer-stable reaches 217k prompt tokens / grows 1.21x per turn is measured against an arm whose real span is 1,230 tokens (967->2197). (Precondition numbering is not in the files searched: experiments/ptr-engine/measure/PREREG-ARM-RUN.json carries no 'precondition' key.)
- **`PRICE-REPLICATION`** - must change - any price/latency replication modelling pointer-stable as a 217k-token trajectory is ~50x too high on prompt volume; correct per-turn volume is 2,176.4 tokens (104,468 over 48 turns)
- **`any doc/manuscript sentence asserting 'pointer-stable grows like a transcript' or 'p50 advantage is 98.7% prefix cache'`** - restate as: pointer-stable's prompt is stable at ~2.2k tokens, cached share 0.8712, and its advantage over transcript-compact is prompt size (2,176 vs 3,867 mean tokens), not cache rate `WI-011` is **retracted**: the measured cached share is **0.871157** (`experiments/ptr-engine/measure/ARM-RECONCILE.json`), not 0.987.
- **`LATENCY-REPORT.json G4 cells`** - no change - its four prompt_tokens totals re-derive exactly; it is the surviving claim

## 8. Integrity

- Pins taken **before** computing and re-checked **after**: `midrun_rewrite = False` (all five files byte-identical).
- No existing document was edited; the only writes are this file, `ARM-RECONCILE.json`, the unit card, the handoff and the journal.
- `0` inference requests.
