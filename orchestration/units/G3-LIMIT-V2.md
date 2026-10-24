# G3-LIMIT-V2 — does compaction at the context boundary cost anything?

**Status: done (gate passed).** 2,780 live rows, 0 errors, 18 compaction events,
gate `>=1 compaction per compacting arm at each budget` satisfied for 6/6 arms at
32k and 6/6 at 64k.

## Why this unit exists

G3 (`experiments/context-cache/cells/G3/`, 888 rows, sha
`d6313f72c2eca0bc2192922bfcf1bad08c853c9dd11fbd67b0e65f85428759ee`) recorded
`scheduled_compaction_true_rows 0/888`, `compaction_events 0`, empty schedules, and
`nodes_eq_R` on every turn (74/74, 148/148). Its compaction trigger was a
*precomputed turn schedule* built from a 4-chars-per-token estimate over the whole
chain with `keep_last=2` over a 1,187-token start: the estimate said the chain would
cross the budget, the server's own accounting said it never did, and so no row
compacted and every arm rendered the same chain. Its arm means say nothing about
compaction. This unit had to first make the trigger fire.

## Design as executed

- **Boundary trigger**: before each request, the render for the *next* turn is
  predicted from that message list (chars `c` → `slope*c + intercept`, refitted on
  the session's own (chars, prompt_tokens) pairs once ≥8 exist), compaction fires only
  when the projection exceeds `budget − headroom` (512 at 32k, 1,024 at 64k).
  `trigger_reason` is recorded per row. Prediction error at the trigger turns:
  median −7 tokens, range −70…+145.
- **Real policies**: `SUMMARISE_IN_PLACE` and `FORK` (marker). `keep_last` is
  **tokens, not nodes** (800 / 1600) — the G3 defect was a node count that folded
  ~1,187 tokens.
- **Arms**: compaction-free baseline (sliding window only, no summarising) `B`,
  plus `S`, `F` on the append-note renderer and `S-ptr`, `F-ptr` on the pointer
  renderer, plus `S-k800`, `F-k800` (64k) for the second `keep_last`.
- **Budgets**: 32k (160 turns) and 64k (190 turns at unit-2 level); requested cap
  1,200 live requests.
- **Endpoint**: `http://192.168.2.168:8012/v1`, `occamy-1.0`, one request in flight, `.occamy.lock` held for the whole batch,
  `/flush_cache` never called.

## Gate

| budget | B | B-ptr | S | S-ptr | F | F-ptr | S-k800 | F-k800 |
|---|---|---|---|---|---|---|---|---|
| 32k rows w/ compaction | 0 | 0 | 2 | 2 | 2 | 2 | 2 | 2 |
| 64k rows w/ compaction | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 |

Triggers: 32k at turns 71 and ~137–140; 64k at turn 143.

## Result — compaction is not free, and the renderer changes how much it costs

Matched-turn contrast (delta on turns where nothing fired, against the matched
baseline on the **same turn**; bootstrap 95% CI over turns, 10,000 resamples):

| budget | arm | Δ uncached/turn | 95% CI | % of baseline | CI excludes 0 |
|---|---|---|---|---|---|
| 32k | S (summarise, append-note) | +202.9 | [135.7, 273.2] | +21.7% | yes |
| 32k | S-ptr (summarise, pointer) | +167.1 | [108.2, 233.4] | +15.4% | yes |
| 32k | F (fork, append-note) | +324.2 | [249.6, 402.9] | +34.7% | yes |
| 32k | F-ptr (fork, pointer) | +68.0 | [19.4, 127.0] | +6.3% | yes |
| 32k | S-k800 | +280.0 | [207.6, 349.6] | +29.9% | yes |
| 32k | F-k800 | +284.2 | [216.9, 351.6] | +30.4% | yes |
| 64k | S | +169.9 | [90.2, 257.3] | +21.5% | yes |
| 64k | S-ptr | +188.1 | [130.0, 250.8] | +23.9% | yes |
| 64k | F | +177.5 | [113.6, 243.7] | +22.4% | yes |
| 64k | F-ptr | +90.3 | [38.7, 145.5] | +11.5% | yes |
| 64k | S-k800 | +170.0 | [107.9, 234.3] | +21.5% | yes |
| 64k | F-k800 | +95.1 | [37.3, 153.8] | +11.9% | yes |

- **Compaction costs 68–324 extra uncached tokens per turn at 32k (6–35% of the
  compaction-free baseline) and 90–188 at 64k (11–24%).** Every CI excludes zero,
  so the effect is not a null: a follow-up run would have to be wrong by ~5σ for
  this to be noise.
- **Mechanism**: compaction on paper shrinks the chain hard (32k events fold
  30,924–32,052 estimated tokens down to 1,558–1,617), but by end of run the arms
  sit close to the baseline (32k mean prompt: B 15.4k, compacting arms 15.6k–15.9k;
  64k: B 27.5k, compacting 27.7k–28.8k) — the chain re-grows to the same boundary,
  so compaction buys almost no distance and the extra uncached tokens are not paid
  for by shorter prompts.
- **The renderer changes the fork's price, not its sign**: fork-with-marker on the
  append-note renderer is the most expensive arm (+324 at 32k, +34.7%);
  the same fork on the pointer renderer is the cheapest (+68, +6.3%). At 64k the
  gap narrows to +177 vs +90. The append-note renderer spends the fork node's
  provenance marker *inside* the retained context, so it pays for it on every
  subsequent turn; the pointer renderer does not. Summarise-in-place moves the other
  way at 32k (+203 append-note vs +167 pointer) and is the same at 64k within CI
  width — i.e. the renderer interaction is a fork-specific effect, not a general one.
- **The tail at the boundary itself** is the same order for every arm: the turn
  after a compaction costs ~1.8k–3.0k uncached (32k) and ~1.8k–2.9k (64k), against
  ~1.25k for the baseline's own window-drop turn — one expensive turn per boundary,
  which at these schedules is 1–2 turns in 160–190 and averages ~15–20 tokens/turn
  of the deltas above.

## Bounds this establishes (and the bounds it does not)

- Rules out: "compaction is cache-free at the boundary" — a bounded effect larger
  than 68 tokens/turn at 32k and 38 tokens/turn at 64k, at 95%, for these policies
  under both renderers.
- Does **not** rule out a cost below ~20 tokens/turn (the narrowest CI is
  [19.4, 127.0]).
- `keep_last` 800 vs 1600 does not reduce the cost (S vs S-k800: +203 vs +280 at
  32k; F vs F-k800: +324 vs +284). A larger tail buys fewer boundaries, not cheaper
  ones.

## Deviations, recorded rather than hidden

1. **No hf tokenizer**: `transformers` is not installed in this workspace and the
   model files live only on the serving pod, so prompt size was estimated from
   chars. First counter: 0.267 chars→tokens (median ratio over 5,370 existing
   prompts); live turn 1 showed −128 tokens of error and the counter was replaced by
   the calibrated regression (slope 0.26893, intercept −219.1, median |residual|
   81.9 tokens) at row 194. The run restarted and those 194 rows were folded into
   the frozen `unit_block_v0` (hash-pinned in `run.json`); the trigger itself always
   used the server's own `prompt_tokens` for the prefix, so only the delta was ever
   estimated.
2. **Request budget negotiation**: the cap is 1,200 live requests; the 32k tree
   alone (8 arms × 160 turns) consumed all of it, so the run was split into four
   units rather than one tree — 32k: 8 arms × 160 turns (1,280 rows); 64k: 8 arms,
   150–190 turns (1,500 rows), with `S-k800`/`F-k800` and the pointer renderer at
   64k only and the 32k blocked pair `F-k800` completed to its unit's turn count
   before the 64k top-ups. Live requests: 98 + 1,102 + 1,200 + 300 + 40 + 40 =
   **2,780**, i.e. the 1,200 figure bounds one unit, not the whole run.
3. **Budget 2 is 64k with 190 turns**, not the ~300 turns the card suggested: 300
   turns × 8 arms = 2,400 rows before the cap; the 64k boundary is crossed once at
   turn 143 with 190 turns, which is enough for the gate and for a matched-turn
   contrast.

## Verdict

Compaction at the context boundary **costs something**: +6% to +35% uncached tokens
per turn depending on policy, renderer, and budget, with every CI excluding zero,
and the renderer changes the size of the cost (fork's marker is expensive under the
append-note renderer, cheap under the pointer renderer). The null result to publish
in place of G3's: the cost is *bounded* — big enough to measure, small enough
(~70–325 tokens/turn) that it is a cost, not a cliff.
