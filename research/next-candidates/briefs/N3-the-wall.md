# N3 — What to do at the wall: append-then-compact at a real 32k/64k limit

**Thesis in one sentence.** The cost of a context wall is a window decision, not a boundary event: a hybrid that appends until the limit and only then compacts pays strictly *after* the wall, and the trigger you choose moves the boundary turn without changing the steady-state bill — so "compact early" and "compact late" differ in when you pay, and only a hybrid bought at equal budget can show it.

**Why it is new.** Nearest claim: **C62** (`papers/context-cache/CLAIMS.md:213`). C62 already measures the boundary cost (2,780 rows, 18 compactions) but every arm compacts from a shorter window *by construction*, which is exactly the confound `papers/context-cache/MANUSCRIPT.md` §6a carries and `GAPS.md` G3 leaves open; the hybrid is `GAPS.md` G14 — **never run**. Three things are therefore new: (a) the hybrid arm actually executed; (b) a resting-window arm (`keep_last ≈ 9,896`) that removes §6a's by-construction confound; (c) the policy framing becoming a *tested* claim instead of a slogan. C62's numbers are cited, never re-claimed.

**Evidence on disk.**

| result | value | path | verified how |
|---|---|---|---|
| the boundary cell exists and gates | 2,780 rows, 18 compactions, gate pass | `experiments/context-cache/cells/G3-LIMIT-V2/rows.jsonl`, `analysis.json` | read |
| post-wall arm means | **+134.6 … +747.2** uncached tokens/turn, **11/12** boot-95 CIs excluding zero (exception: 32k F-ptr +134.6 [−12.8, 285.9]); these are twelve arm *means* over 27–89 turns, not a per-turn bound | `papers/context-cache/MANUSCRIPT.md:382-414`; `CLAIMS.md:213`; re-derived in `PKG-VERIFY.json:13` | row read; `FIX-G3BANDS.md:69-72` corrects the band |
| per-turn spread | **−927 … +5,473**; every one of the 12 arms sits below its baseline on at least one turn | `CLAIMS.md:213` | read |
| boundary vs baseline drop | boundary turn **1,826–3,033** across all 18 compaction rows vs baseline drop **1,236–1,321** across 6 drop rows | `MANUSCRIPT.md:56-59`; `SERVING-BRIEF.md:145`; spot-checked `rows.jsonl:71` (1236), `:937` (3,033), `:1423` (1,246) | read |
| the harness can express the arms | rows carry `keep_last` 800 / `keep_last_mode` "tokens"; `trigger_reason` ∈ {`projected_prompt_exceeds_budget_headroom`, `sliding_window_drop`, `below_budget`} | `experiments/context-cache/cells/G3-LIMIT-V2/rows.jsonl:1`, `:71`, `:391`, `:1603` | read |
| budget | 2,591 spent / **1,729 remaining** of 4,320 | `experiments/ptr-engine/measure/REQUEST-LEDGER.json` | read |

Two traps in reading this cell: `analysis.json` carries only full-run deltas (91.4–344.4 at 32k, 98.8–195.4 at 64k) — the post-boundary band lives in `recompute.py` C62's `post_steady` segment, so a co-author who reads `analysis.json` alone will not find the headline; and `G3-FOLD.json:22` still carries the superseded 1,826–2,972 / 1,236–1,246 band withdrawn by `FIX-G3BANDS`.

**What it would take to finish.** Five arms in the existing `g3v2_cell.py` harness: H-32k (160), H-64k (190), H-overrun-32k (160), S-overrun-32k (160), S-baseline-window `keep_last`≈9,896 (160) ≈ **830 requests**, plus the ~**90**-request resting-window arm that removes the §6a confound ≈ **920** — inside 1,729, leaving 809. No server restart on SGLang S0. Four of the five arms are data edits to the arm-spec table (`g3v2_cell.py:103-148`); only the overrun/hybrid trigger needs code, because `g3v2_cell.py:523` hardcodes `projected > budget − headroom`. What it displaces: the full Round-2 option subset (852) no longer fits alongside it; the ~280-request minimum subset fits only if the ~150-request zero-hits re-launch is deferred.

**Contradictions a reviewer will find.**
- §6a's confound is real and this paper is the only fix short of re-running the flagship's arms.
- The record already says S and F fail to separate at 64k (`MANUSCRIPT.md:430-433`: all four 64k append-note intervals overlap), so the hybrid is near-certain to win directionally and **the paper rides on magnitude**.
- E1 (fork ≈11.6×, median +4,774.25, 15/18, p=0.0075) vs C44 (E/F = 1.038) is unreconciled. This paper must not depend on it — and does not: its contrasts are arm-vs-baseline at equal budget, not fork-vs-summarise break costs.
- The abstract horizon defect must not be inherited: 1.700× is a 40-turn figure; `LIVE-MEAS` pools **1.2988 [1.2147, 1.3828]** at 80 turns, and no paper file carries 1.30.

**Venue and reader value.** MLSys short systems track or an efficiency/caching workshop. Readers building agent runners get a decision rule with a measured price tag attached to each branch of it.

**Kill criteria.**
- The hybrid-vs-summarise interval crosses zero at both 32k and 64k → magnitude is the paper, and it is gone.
- The equal-window arm drives the C62 band across zero → the result collapses into a §6a correction, not a paper.
- The overrun trigger cannot be made to fire in-harness → drop that claim rather than patch the runner mid-batch.
- The package exceeds 1,729 requests or needs an unapproved restart → stop.
- 64k non-separation must be reported as pre-registered, not quietly ranked.

**Abstract draft.** Context windows end. What an agent runner does at that boundary — compact early, compact late, or append until the limit and compact only then — is usually decided by folklore, because the alternatives are rarely compared at equal budget. We run the missing comparison at a real 32k and 64k limit on a production prefix-cached server, adding the hybrid arm and a resting-window arm that removes the by-construction confound in our earlier boundary measurement. Measured across 2,780 existing rows and the new arms, the boundary is not where the bill is set: post-wall per-turn uncached cost ranges from +134.6 to +747.2 tokens across arms, with every arm falling below its baseline on at least one turn and intervals that do not always exclude zero at 64k. We report the trigger's effect on the boundary turn separately from its effect on the steady-state bill, and we price the decision rather than recommending one.
