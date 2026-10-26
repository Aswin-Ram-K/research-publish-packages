# GROUND-TRUTH-PROMPT

**Purpose.** Decide which of 583.14 (PROMPT-O1 original) / 391.48 (after OFFLINE-REPAIR) is the
true mean `uncached_tokens`/turn of arm **R** on production O1, by re-running the R arm as a fresh
71-turn cell with a NEW salt. GROUND-TRUTH-R had shown that repeated `cached_tokens` are real server
behaviour, so "duplicates ⇒ corrupt" cannot justify the repair on its own.

**Live only.** `http://192.168.2.168:8012/v1`, model `occamy-1.0`, HTTP only, no restart, no variant,
nothing stopped or removed on the GX10. Held `experiments/context-cache/.occamy.lock`.

**Method.** Arm R body taken from the same renderer the two candidate cells used
(`cells/VLLM-CELL/vllm_cell.py`, `render("R", turn)[0]["content"]`), same `fit_budget(., 32768)`,
same non-streaming call carrying `usage.prompt_tokens_details.cached_tokens`. Only the salt preamble
differs: seed `GROUND-TRUTH-PROMPT|R|2026-10-25T08:05Z|fresh-salt-1` →
`occamy-prompt-o1 salt:63564242b54d8609` (the candidate cells used `PROMPT-O2|R|2026-10-24`).

**Result.** 71 rows, 0 non-200, mean uncached/turn **589.20** (n=69 measured). vs 583.14 **+1.04 %**;
vs 391.48 **+50.51 %**; vs 390.80 **+50.77 %**. Cached series matches the pre-correction cell
turn-for-turn on 60/71 turns (65/71 of its values occur in the pre-correction series at all) and
R2-P1-O1 on only 31/71. The repaired cell's `cached_tokens` are **off the 64-token grid** on 40/71
turns (gcd = 1: 1409, 1793, 2433, 2753, 3777 …) — impossible on this stack (fresh, pre-correction and
R2-P1-O1 all have gcd = 64, 0 off-grid).

**Verdict.** 583.14 is genuine; the repair destroyed real data in PROMPT-O1. A−R = **−53.85**.

**Artifacts.** `experiments/context-cache/cells/GROUND-TRUTH-PROMPT/{rows.jsonl,summary.json,comparison.json,warmup.json,launch.json,run_r_only.py,resume_r.py}`.

**Caveat.** The harness restarted mid-run and killed the process at turn 58; turns 59–71 were appended
by `resume_r.py`. That interruption perturbed turns 58–60 (unc 421/376/395 instead of the 3-cycle's
~738/757/392); excluding them the mean is 597.82 (+2.5 % vs 583.14).
