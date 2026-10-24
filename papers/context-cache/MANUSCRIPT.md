# Where the cache win lives: placement, truncation, and the silent cost of compaction

Findings from the Occamy context-cache experiment. Two models (`occamy-1.0`, a Qwen3.5-MoE
checkpoint; `qwen3.5-9b`, a dense one), two engines (SGLang; vLLM 0.27.1), one seed. Every
number below is re-derived from raw request rows by a single command named in `CLAIMS.md`;
the units, digests and pre-registered kill conditions are in `RUN.json`.

**Abstract.** We asked whether prompt caching in a production-style inference server can be
made to pay for structured agent workloads, and why earlier measurements said it could not.
Four results survive re-derivation from the raw rows. First, the renderer is not the lever: the
compaction experiment's tree appender emitted byte-identical prompts under both of its render
modes in all 760 cells — the pointer renderer and the naive appender returning the same bytes,
760/760, 0 bytes differing (C01) — so every between-arm difference there belongs to the
compaction policy and none to rendering, while the two compacted arms' prompts were themselves
identical (190/190 equal digests, C03). Second, whether fan-out reuses a
cache is decided by where the shared bytes sit: keeping the prefix byte-identical and placing the branch tag at
the end of the delta reduced uncached tokens 6.744x [4.045, 9.443] over a per-branch-history
layout (cell G5, race-free, 8 fan-outs x 8 branches — superseding the pre-G5 band 3.31 measured
/ 5.39 projected, which was not a bound in either direction), and
moving only the tag reproduced the full win (1.00x) with no pointer machinery at all — the
win is a placement discipline, not a property of pointers. Third, compaction that rewrites
the head of the context is silently lossy: a gold line planted mid-history survived 190/190
uncompacted cells and 0/190 cells in both compacted arms, while multiple-choice accuracy
moved by at most 2.6 points (McNemar p >= 0.38) — aggregate accuracy hides a total loss of a
specific fact. Fourth, over 40 turns with compaction at turns 18 and 35, append-a-note beat
summarise-in-place by **1.700x** on total uncached tokens, past the pre-registered 1.5x
threshold; fork and summarise-in-place stayed within 8.7 % of each other, so rewriting the
head at all matters far more than which rewrite is used. The decisive caveat is that only
**7.8 %** of summarise-in-place's 20,649-token excess over the no-compaction control is the
two break events: 92.2 % is a steady-state window cost, roughly 1,660 re-prefilled tokens per
turn against the control's 755. The cost of compaction is truncation *plus* the break, not
the break event alone, and a counterfactual arm paying only the break would score 1.07x, not
1.70x. G1 re-derives the break cost independently (per-break E/F = 1.038, within measurement
noise; only 2 of 6 break events within 10 %; 264 rows, sha256 9242ad383281b360ec3c4be92bc59e7de7d5cd751eb7e15c0944f2261497ae66), so
the 1.700x is a compaction-window-policy cost on this workload, not a fork/append cost
(u15_1_700x_survives_decomposition = False; C44). We also report two negative results that change how the record must be read: the
earlier "fork equals summarise-in-place" finding rests on a comparison that measured nothing
— both arms were rendered by the same appender — so the fork hypothesis is **untested at
n>0, not refuted**; and the 64-token cache grid is a law of byte-identical repeats, not of
context growth, breaking on every one of 372 warm appends. Cache hits are real but partial:
median time-to-first-token falls from 208.7 ms to 86.4 ms at a 1,024-token prompt and from
7,541.9 ms to 231.6 ms at 31,415 tokens, with a hit/miss ratio near L^-0.78 and a residual
cost of about 4.7 microseconds per token, so "zero prefill cost" is false.

A fifth result answers the question the first four leave open — what a compaction *at the
context boundary* costs, rather than a compaction scheduled at a fixed turn. With eight arms
driven past a real 32k and 64k budget (cell G3-LIMIT-V2, 2,780 live requests, 18 compactions),
every arm renders the same trajectory until its boundary fires, and from that turn on the
six compacting arms pay **+134.6 to +747.2 uncached tokens per turn on average** against the
compaction-free baseline — five of six at 32k and six of six at 64k with intervals excluding
zero; before the boundary the same arms are indistinguishable from it (-11.8 to +51.0,
every interval crossing zero). Those are twelve arm means over 27-89 turns each; per turn the
segment reaches **-927 to +5,473**, every one of the twelve arms has at least one turn below
its baseline (it pays on average, not on every turn), and the extremes are the turns around
the baseline's own window drops, where the baseline stands on `cached_tokens` 31,616-30,656
that the arm has just folded away. The bill is a reuse bill, not prompt volume: on the turn it
compacts, the arm's `cached_tokens` is 0 where the baseline's previous turn carried 31,552,
and what it rebuilds afterwards is a shorter prompt with a worse hit rate (last-turn prompts
13,325 / 13,542 at 32k and 23,632 / 23,762 at 64k against the baselines' 9,896 / 22,063).
The boundary turn itself costs 1,826-3,033 uncached tokens across all 18 compactions — not
1,826-2,972, which took only each arm's *first* compaction and so missed the second 32k
boundary at 2,808-3,033 — against the baseline's own window drop at 1,236-1,321 over six drop
rows (the 32k baseline drops twice), and the cheapest of the twelve arm-instances is the pointer renderer's
fork at 32k (+134.6 [-12.8, 285.9]) - the one interval that crosses zero. Truncation forced
by a limit therefore costs what §6 measured for truncation on a schedule; G3-LIMIT-V2 is
what turns that from an inference into a measurement (C62).

**A sixth result separates the engine from the model.** Filling the 2x2 — two checkpoints
(`occamy-1.0` MoE, `qwen3.5-9b` dense) x two engines (SGLang, vLLM 0.27.1) — on one
shared 32k schedule (4 arms x 71 turns = 284 rows per cell, 1,136 rows, with the same
prompt prefix digest and length on every cell pair: `prefix_sha256` 284/284, `chars` 284/284) shows that the **engine**, not the model, sets the
per-turn uncached bill: vLLM spends **+1,225.18** uncached tokens per turn more than SGLang
[1,132.2, 1,313.3], a **2.6738x** ratio, against a model main effect of **+275.83** [194.3,
357.6]. The model effect is **engine-conditional**: **+548.06** [384.7, 711.9] under vLLM
versus **+3.61** [0.0, 10.8] under SGLang (one of 71 paired turns positive), an interaction
of **+272.23** [190.1, 354.6] — the model effect is **152.00x** larger under vLLM. SGLang
pages both checkpoints on the same 64-token grid; under vLLM each checkpoint's resolved
block (1,088 dense, 2,096 MoE) sets its own bill (C63).

## 1. The question, and the answers we can defend

The motivating question is narrow: for a multi-turn agent workload, where does cache reuse
actually come from, and what does a compaction policy do to it? The core experiment
(Sections 2-8) was run against a single SGLang endpoint serving `occamy-1.0` (Qwen3.5-MoE,
NVFP4 weights) with the radix cache enabled, `chunked_prefill_size` 8192 and
`max_running_requests` 5; Section 9b adds a second checkpoint and a second engine. All prompts
are synthetic in-cell corpora built by one driver, all requests are serial, and cache hits
arrive as `usage.prompt_tokens_details.cached_tokens` (null, coerced to 0, on cold requests).

| Unit | Question | Live requests | Rows |
|---|---|---:|---|
| U2 | Does the prompt-length tax follow the 64-token grid? | 97 | `cells/U2/u2_cache_rows.jsonl` (88) |
| U4 | Do edit policies beat fork at compaction? | 454 incl. probes | `cells/U4/u4_rows.jsonl` (438) |
| U4b | Where must the shared prefix sit for fan-out reuse? | 24 | `cells/U4b/rows.jsonl` (24) |
| U5 | Does compaction preserve what the task depends on? | 760 | `cells/U5/u5_raw.jsonl` (760) |
| U9 | What does a hit buy in time-to-first-token? | 139 | `cells/U9/u9_trials.jsonl` (139) |
| U10 | When does an immediate repeat miss? | 159 | `cells/U10/u10_rows*.jsonl` (65 + 55) |
| U13, U14 | Can fork and append-note be made genuinely distinct? | offline | `cells/U13/*.json`, `cells/U14/*.json` |
| U15 | Append vs summarise vs fork over 40 turns | 160 | `cells/U15/rows.jsonl` (160) |
| G3-LIMIT-V2 | What does compaction cost when the limit, not a schedule, forces it? | 2,780 | `cells/G3-LIMIT-V2/rows.jsonl` (2,780) |

Four answers hold: the renderer contributes nothing (Section 2); placement decides fan-out
reuse (Section 3); head-rewriting compaction loses content silently (Section 4); and
append-a-note wins on uncached tokens largely because it never truncates (Section 6). Two
things must not be read the way the earlier cards read them: the U4 fork comparison
(Section 5) and the 64-grid law (Section 8). The invalid comparison is the first thing a
reviewer should check, so it is stated here and given its own section rather than a footnote
in the discussion.

## 2. No rendering-level advantage exists

`u5_recon.py` rebuilds every prompt from the row's stored tree and compares the pointer
renderer against `NAIVE_APPEND`: **760/760 cells byte-identical, 0 bytes differing** (C01).
That equality is a property of one library, not of two independent implementations: both
render modes are the `RenderPolicy` variants of `resextract.context` (`POINTER` and
`NAIVE_APPEND`), reached through the same `build_cell(..., policy=...)` call, so the
comparison shows the appender ignores `node.kind` — it does not show that two teams converged
on the same format, and it is the same identity that makes the U4 comparison in Section 5
measure nothing. The deep-condition prompts also show `summarise_in_place` and `fork` digests equal in
**190/190** cells, with 570 distinct digests over the 760 rows (C03), which is exactly what a
renderer that emits `node.text` and never `node.kind` must produce.

This is a negative result with a sharp consequence: the 760-cell compaction experiment is a
pure policy experiment. Any difference between its arms is caused by the compaction policy,
not by how the policy's tree was turned into tokens. It also means that the U5 "fork" arm was
a second summarise arm, which matters in Section 5.

Renderer identity does not generalise for free: U13's fix (a content-addressed `[fork]`
marker) is precisely the change that makes fork and summarise render differently, and after
it the two arms no longer share a prompt (C15). Identity was true of the build that ran U4
and U5, and it is that build's conclusions which must be reinterpreted.

## 3. Fan-out reuse is a placement discipline

Twenty-four requests, eight branches under one fan-out, three layouts of the same bytes
(C04, C05). Each arm sends a 15,400-token prompt; only the uncached share differs. This is the
single-fan-out cell U4b, whose ratio turned out to be an **understatement**: cell G5's
race-free 8x8 measurement reports B/A = 6.744, so the 3.3133 in row B below is the
**superseded** pre-G5 value, kept here only because the mechanism paragraph is read from these
24 rows.

| Arm | Layout | Uncached | Cached per branch | B/A (this cell) | B/A (live, G5) |
|---|---|---:|---|---:|---:|
| A | `P + [BRANCH-k]` + delta | 4,648 | 0, 0, 1792 x 6 | 1.0000 | 1.0000 |
| B | `[BRANCH-k]` + `P` + delta | 15,400 | all 0 | 3.3133 (superseded) | **6.744 [4.045, 9.443]** |
| C | `P` + delta + `[BRANCH-k]` | 4,648 | 0, 0, 1792 x 6 | 1.0000 | 1.105 |

The per-branch rows make the mechanism unambiguous: prompt is 1,925 tokens per branch,
uncached is 1,925 for the first two branches and 133 for each of the remaining six, and the
1,792-token shared prefix `P` is what every branch after the first reuses. In B the branch tag
sits *before* the shared prefix, so no branch shares a prefix with any other and every branch
pays the full 1,925. In C only the tag moves, to the end of the delta, and the win is
reproduced exactly — `C/A = 1.0000`.

So the win is two properties, neither of which is "use a pointer": keep the prefix bytes
identical across branches, and branch late, after the shared material. C has no pointer
machinery and matches A to the token. The pointer implementation is one way to get the
discipline; it is not the discipline.

An earlier draft called the measured 3.31 a **floor** and
the 5.3922 counterfactual an **upper bound**, and argued the ratio had to lie between them.
Both halves of that argument are wrong, and G5 shows it: branch 2 of arm A missed on an insert
race (its request was issued before the first branch's cache insert completed), so this cell
paid 1,925 tokens twice; but removing that race does not lower the ratio, it raises it. With all
seven warm branches hitting, this cell's counterfactual is 2,856 uncached and B/A = **5.3922**
(C06) — already above the 3.31 "floor", and only 1.5x below the 6.744 that an 8x8 race-free
measurement actually returns. So 5.3922 is a **lower** reference for a race-free ratio, not an
upper bound on it; the larger fan-out changes how many branches reuse the prefix and how many
times B re-pays it. The card for U4b projected 3.99 for the warm scenario; that figure does not
reproduce from the rows (15,400 / 2,856), and it is superseded in the same way. The only ratio
this paper reports as a result is 6.744 [4.045, 9.443] from cell G5; 3.3133 and 5.3922 are this
cell's measured and race-corrected values, and anything that quotes them as the effect
size is quoting superseded numbers. Second, this is one seed, and the insert race itself is a
finding about the runner, not about the cache — which is why G5 was run with the insert
serialised behind the shared prefix.

**The live fan-out figure (cell G5, race-free; 8 fan-outs x 8 branches, 192 rows, C53).** B/A = **6.744** [4.045, 9.443].
Layout A shares one prefix: 123,240 prompt tokens, 102,912 cached, 20,328 uncached. Layout B's per-branch
histories never share a prefix, so the cache hit is structurally 0 for B (0 of 123,256 cached; 123,256
uncached). Layout C serialises the insert behind the shared prefix and costs 19,792 uncached (C/A = 1.105).
This is the figure the paper stands on, and it supersedes the pre-G5 band 3.31 measured / 5.39 projected in
both directions: 6.744 is 1.25x above the 5.39 that the earlier text offered as an upper bound, so that
bound claim is withdrawn, not merely restated with a new number.

## 4. Compaction is silently lossy

U5 sends 760 requests (190 cases x 4 conditions), all HTTP 200, no request errors (C02). Accuracy on
the multiple-choice task barely moves; retention of a planted fact collapses (C07, C09, C10).

| Condition | Correct / 190 | Accuracy | Gold line survives | Agreement with baseline |
|---|---:|---:|---:|---:|
| shallow (no compaction) | 126 | 66.3 % | 0/190 | 87.9 % |
| deep baseline | 137 | 72.1 % | 190/190 | — |
| deep, summarise_in_place | 134 | 70.5 % | **0/190** | 87.9 % |
| deep, fork | 132 | 69.5 % | **0/190** | 86.8 % |

The compacted-arm deltas against the deep baseline are -1.6 (summarise) and -2.6 (fork) points,
and shallow, which discards the history entirely, is -5.8; none of the compacted-arm deltas is
significant (McNemar exact: summarise-vs-baseline 11/8 discordant, p = 0.648; fork-vs-baseline
13/8, p = 0.383; summarise-vs-fork 7/5, p = 0.774) and none exceeds the pre-registered 5-point
threshold (C08). A reviewer who read only the accuracy
table would conclude compaction is harmless. It is not: the gold line planted mid-history is
retained by every uncompacted cell and by **none** of the 380 compacted cells, in either
compacted arm (C09). The question and options survive 190/190 in every condition, so the
model still answers — it answers from a summary that no longer contains the fact. That is the
definition of a silent loss: the interface is intact, the grounding is gone.

The pre-registered 90 % agreement flag **fired**: baseline-vs-compacted agreement is 167/190
(87.9 %) and 165/190 (86.8 %), both below 90 % (C10). It should be read with its noise floor
attached. Agreement between the two compacted arms — whose prompts were byte-identical, as
Section 2 shows — is only 174/190 (91.6 %). Two arms fed the same bytes disagree on 8.4 % of
cases, so 86.8–87.9 % is a small but real difference, and the flag is measuring sampling
noise as much as effect. The retention result does not have this problem: 190/190 versus
0/190 is not a noise artefact.

Aggregate MCQ accuracy is therefore the wrong instrument for this question. A 21/190 two-way
flip rate nets out to a 1–3 point accuracy change while the quantity the
task depends on goes to zero. Any future claim that a compaction policy "preserves
behaviour" must report content retention alongside accuracy.

## 5. The U4 fork comparison is invalid and must not be cited as a refutation

This is the most important correction in the package, and it is a correction to the
experiment's own record.

**What U4 reported.** Three sessions x 44 turns, three rewriting policies plus a 42-row
control, compaction at turns 12, 17, 22, ..., 42 (seven events per session, 21 paired events
per policy). Break cost was identical for
`summarise_in_place` and `fork`: paired median delta 0, 18/21 pairs exactly 0, maximum
absolute delta 64, permutation p = 1.0 (C11). On that basis the U4 card concluded the
edit-vs-fork hypothesis was refuted and recorded a kill-condition trigger. **That conclusion
is void**: the paragraph below shows the pairs measured renderer identity, so the hypothesis
is not refuted but **untested at n>0** (C13, C16).

**Why that comparison measured nothing.** The cell driver that ran U4 renders every arm with
one renderer: `cells/U4/u4_cell.py` sets

    RENDER = RenderPolicy.NAIVE_APPEND  # the single renderer for every arm

and `POINTER_FORK` is never imported (C13). The renderer emits `node.text` and never
`node.kind`, so a summarise-in-place chain and a fork chain over the same nodes produce the
same bytes. `compact(FORK)` and `compact(SUMMARISE_IN_PLACE)` therefore emitted identical
text, and the "comparison" compared an arm with itself. The three nonzero deltas (-64, +64,
-64) are 64-grid rounding of a 2–3 token per-cell salt offset, not policy effects: the
prompts differ only by the salt, and the row pairs differ by exactly one 64-token chunk
(C12).

**Independent confirmation.** The verifier's offline replay
(`cells/CX-V2/u4_recon.py`) rebuilt both arms from the stored trees and, on the library as it
stood, found body digests identical **44/44** in every session, with prompts differing only
by the per-cell salt. Re-running the same script today (C16) reports only **11/44** body-byte
equality — because U13's `[fork]` marker now separates the arms from turn 12 onward, and the
replay prints the body byte counts at the boundary: equal at turn 1 (2,857 vs 2,857), unequal
from turn 12 (19,998 vs 20,173). Turn 12 is the first turn rendered after a compaction. That
is the cleanest possible proof of both halves: the historical 44/44 was an artefact of one
renderer, and the fixed library makes the arms differ exactly where compaction begins.

**The same defect in U5.** The U5 "fork" prompts have the same digest as the "summarise"
prompts in 190/190 cells (C03). U5's fork accuracy (69.5 %) is therefore a second summarise
number, and neither card's fork result carries information about forking.

**The fix.** U13 added a content-addressed marker to the fork root text
(`[fork] replaces head through <id>; forked_from <chain hash>` plus the summary). Fork now
digests to `b812c99d`, summarise to `dc591b7e`, the fork prompt is 7,966 characters against
7,791 (+175 characters, about 44 tokens) and the material after the marker is byte-identical
to the bare summary (C15). The arms are now genuinely distinct, which is the minimum
condition for a comparison.

**Consequence.** The hypothesis "an edit policy and a fork policy have the same break cost"
is **untested at n>0 under the fixed library**. U4's 438 rows cannot be salvaged: they record
what one renderer produced for three policy objects, not what the policies produce. The
correct statement in any citation is that U4 measured renderer identity, and that the fork
question remains open. Writing "refuted" would propagate a null experiment as a negative
result, which is the one error this package exists to prevent.

## 6. The decisive comparison: whether the head may be rewritten

U15 removes the renderer question entirely by making the policies produce different bytes
(C17–C26). Four arms, 40 turns each, one corpus (`endtoend.json`, scenario E1), compaction at
turns 18 and 35 derived once from the summarise arm so that all arms compact on the same
schedule:

| Arm | Policy | Prompt | Cached | Uncached | Hit rate | Breaks | Net break cost |
|---|---|---:|---:|---:|---:|---:|---:|
| R | summarise_in_place | 194,788 | 143,616 | 51,172 | 0.7373 | 2 | 1,620 |
| F | fork (with marker) | 198,376 | 151,296 | 47,080 | 0.7627 | 2 | 1,975 |
| A | append_note | 412,177 | 382,080 | 30,097 | 0.9270 | 0 | 0 |
| C | none (control) | 403,259 | 372,736 | 30,523 | 0.9243 | 0 | 0 |

Arm A beats arm R by **1.7002x** on total uncached tokens (C21), past the pre-registered
1.5x test. R and F are within 8.69 % of each other (R/F = 1.0869), and both are far behind A.
Whatever distinguishes fork from summarise, it is not the driver: the driver is that both
rewrite the head and A does not.

G1 re-attributes this result (C44): the 1.700x is a post-compaction window-truncation cost,
not a fork/append cost — the per-break cost ratio E/F is 1.038 (within measurement noise;
only 2 of 6 break events within 10 %). The observed 1.700x stands as a window-policy effect.

**The caveat that must travel with the headline.** R's excess over the control is 20,649
uncached tokens, but only 1,620 of it (7.85 %) is net break cost at turns 18 and 35 (C22).
The remaining 19,029 (92.15 %) is post-compaction steady state: on turns 19–34, R re-prefills
1,659.9 tokens per turn against the control's 754.9 (C23). R's window is 5,811.9 tokens on
average, the control's is 12,838.9, and the difference in the *reusable prefix* is what the
arm pays for. Counterfactually, an arm that paid R's break cost and nothing else would total
32,143 uncached tokens, and A/R would be **1.068x** (C24) — inside the pre-registered
threshold's noise. The pre-registered test passes, but what it measures is the cost of a
truncated window plus the break, and any deployment that must compact for context-limit
reasons buys the 92 % whether or not it ever sees a break event.
G1 corroborates the decomposition (C44): the net break cost is the smaller term and the
per-break fork/append cost is within measurement noise of the edit cost.

The segment split makes the asymmetry visible. R's excess over C is -30 tokens before the
first compaction, 15,901 on turns 18–34, and 4,778 on turns 35–40. F's advantage over R is
almost entirely in the last segment (F 4,595 vs R 9,011 uncached on turns 35–40); we report
that as an observed asymmetry without an instrumented explanation (see `GAPS.md`).

**What A costs.** A never shrinks. Its final prompt is 19,583 tokens against R's 4,134 (R's
mean window over turns 19–34 is 5,811.9), a growth of 18,397 tokens, 16.5x over the run
(C25). Its total prompt mass is 412,177 tokens against the control's 403,259 — the notes it
appends buy cache stability with 8,918 extra prompt tokens and an unbounded window (C25).
U14's mechanism is the analytic bridge: appending a note leaves the head digest identical
before and after compaction (`2a38a86f`), where summarising changes it (`b424ae2e`), at a
cost of 231 tokens per note against the summariser's 1,028-token reduction. Append buys its
hit rate by never compacting; that is exactly why its window is unbounded, and why it is
unusable beyond the context limit. The honest operational reading is: if the workload fits,
append and take the 0.927 hit rate; if it does not fit, compaction is unavoidable, and the
cost to attack is the steady-state re-prefill, not the break.

## 6a. The measured cost of compaction at the boundary

Section 6's comparison is bounded in a way that matters: it schedules compaction and the
histories stay far below the limit in every row (cell G3, 888 rows, `scheduled_compaction`
false on all of them; `GAPS.md` G3). So the package knew the cost of a *scheduled* truncation
and, until cell G3-LIMIT-V2, nothing about the truncation a context limit forces — and
nothing about it could be inferred from the scheduled case, because there append-a-note never
compact and so is not available to compare. G3-LIMIT-V2 measured the boundary live: 2,780
requests, 18 compactions, 12 arm-instances — six compacting arms at each of two budgets (32k
and 64k), each against a compaction-free baseline rendered in the same bytes, so the arms
share a trajectory until the boundary and differ only in what happens after it (C62). Each arm fired once at 32k (turn 71) and again at turn 137-140, and once at
64k (turn 143), out of 160 and 190 turns respectively. The trigger is a projection of the
next turn's render made from the server's own `prompt_tokens` for the current one, so only
the appended delta is estimated; it fires when that projection exceeds the budget less a
headroom of 512 tokens at 32k and 1,024 at 64k.

**The control segment is flat.** Before any arm compacted, every arm is the same workload, and
the matched-turn contrast says so: -11.8 to +51.0 uncached tokens per turn across the twelve
arm-instances, and **0 of 12** bootstrap intervals excludes zero. That is the pre-registration
of this cell passing — the arms may only differ where compaction begins.

**After the boundary the arms pay, and mostly at rest.** Against the same-turn baseline,
the post-boundary delta runs **+134.6 to +747.2 uncached tokens per turn** — but that range is
twelve *arm means*, each averaged over 27-89 turns, and it is not the spread of what a single
turn costs. **Per turn the segment runs -927 to +5,473 uncached tokens** against the
baseline, and **all twelve arms** contain at least one turn that comes in *below* its
baseline: the arms pay on average and unevenly, not on every turn. Both ends of the per-turn
range are the turns around the baseline's own window drop. They are why the arm means differ
from the turn range by more than the point estimates suggest: the 32k arms' worst turns
(+1,335 to +2,203) fall on the turn after the baseline's window drop, where the baseline
stands on 30,656-31,616 cached tokens the arm has already folded away: all 12 of those
transition turns (six arms x two baseline drops) exceed their baseline. Re-weighting the
segment to exclude the turns that follow a baseline drop changes no arm's significance and no arm's range, but it does move one arm's
mean the most: the pointer fork at 32k falls from +134.6 to **+112.5** on resting turns,
where its interval [−33.7, 264.3] crosses zero — the one interval that was already the
exception becomes the one arm whose resting cost this cell cannot resolve. 11 of 12 intervals
exclude zero with those turns included (the exception is the pointer fork at 32k, +134.6
[−12.8, 285.9]). The replicated structure in the means is that the cheap arms are the
pointer renderer's and the 800-token `keep_last` variants, and the expensive ones are the
1,600-token `keep_last` append-note arms — and a ranking of *means* should not be read as a
ranking of single turns:

| Budget | Baseline (last prompt) | Arm | Last prompt | Post-boundary Δ [95 % CI] | Pre-boundary Δ |
|---|---:|---|---:|---:|---:|
| 32k | B 9,896 | S | 13,325 | +390.2 [239.4, 542.1] | −10.7 |
| 32k | B 9,896 | F | 13,542 | +578.1 [451.4, 709.6] | +27.3 |
| 32k | B 9,896 | S-k800 | 11,009 | +522.0 [410.3, 632.0] | −11.7 |
| 32k | B 9,896 | F-k800 | 11,717 | +526.6 [412.3, 641.0] | -11.8 |
| 32k | B-ptr 9,897 | S-ptr | 13,321 | +278.1 [161.9, 401.7] | +51.0 |
| 32k | B-ptr 9,897 | F-ptr | 13,546 | +134.6 [−12.8, 285.9] | +13.0 |
| 64k | B 22,063 | S | 23,632 | +700.2 [475.2, 997.7] | −5.6 |
| 64k | B 22,063 | F | 23,762 | +747.2 [598.7, 900.2] | −11.1 |
| 64k | B 22,063 | S-k800 | 22,643 | +697.1 [571.6, 824.7] | −4.5 |
| 64k | B 22,063 | F-k800 | 14,197 | +653.5 [482.0, 822.0] | −11.1 |
| 64k | B-ptr 22,061 | S-ptr | 23,634 | +739.6 [595.7, 889.7] | +5.6 |
| 64k | B-ptr 22,061 | F-ptr | 23,765 | +346.4 [141.2, 559.6] | +5.6 |

The mechanism the rows carry is the one Section 6 named, now measured after a limit rather
than after a schedule: the boundary destroys the reusable prefix, and the arm never rebuilds
the reuse the baseline keeps. The 32k boundary row says so directly — the arm's
`cached_tokens` is 0 on the turn it compacts, where the baseline's preceding turn carried
31,552 — and the resting windows show what follows: at 32k the baseline rests at 9,896
tokens by its last turn and the compacting arms at 11,009-13,546; at 64k, 22,063 against
22,643-23,765. On its second boundary at 32k, arm S restarts at 2,812 tokens where the
baseline stood at 30,717 on the same turn, and it still pays more uncached per turn from
there on — so the excess is not prompt volume, it is a shorter prompt with a worse hit rate.
In this workload the boundary *is* the window cost, and it is not free.

**Two limits on that reading.** First, the arms do not separate by policy the way Section 6's
scheduled comparison did: at 32k S/F are +390.2/+578.1 and S-k800/F-k800 are +522.0/+526.6,
and whether an interval pair is disjoint is not uniform (S vs F at 32k does not overlap;
S-k800 vs F-k800 does). At 64k the four append-note arms are 700.2/747.2/697.1/653.5 and every
interval overlaps the next except F-k800's lower bound clearing S's upper bound. What does
separate cleanly is the renderer at 32k — both pointer arms are cheaper than both append-note
arms — but with 6 arms per budget and one seed, a ranking is reported as observed, not
tested. Second, the boundary trigger was `projected_prompt_exceeds_budget_headroom` on 18/18
compactions: the cell compacted when the projected prompt came within a headroom of the
budget rather than after an overrun, so what is measured is the cost of compacting *before*
the limit. The trigger fires with 512 tokens of headroom at 32k and 1,024 at 64k, and the
compaction turn's prompt lands at 2.8-8.7 % of the budget against the baseline's own window
drop at 1.9-3.8 %. Measuring compaction *after* an overrun needs a cell that lets the prompt
exceed a budget by a known amount. Both limits are recorded in `GAPS.md` G3.

## 7. What a cache hit buys, and what it does not

139 usable requests, six prompt lengths, seven repetitions (C36). Median time-to-first-token
on hit and miss, and their ratio (C27–C32):

| Prompt tokens | Miss (ms) | Hit (ms) | Ratio | Delta (ms) |
|---:|---:|---:|---:|---:|
| 1,024 | 208.7 | 86.4 | 0.414 | 122.1 |
| 2,028 | 349.2 | 87.2 | 0.250 | 259.8 |
| 3,955 | 674.6 | 105.2 | 0.156 | 559.8 |
| 7,863 | 1,431.6 | 114.3 | 0.080 | 1,311.7 |
| 15,701 | 3,039.5 | 139.2 | 0.046 | 2,892.1 |
| 31,415 | 7,541.9 | 231.6 | 0.031 | 7,251.0 |

The ratio falls as a power of length: L^-0.7837 with r2 = 0.9962 (C33). Fitted separately,
the miss term grows at L^1.052 (r2 = 0.9934) and the hit term at L^0.268 (r2 = 0.8631), and
the ordinary least squares slopes are 0.240736 and 0.004659 ms/token — a **51.67x** smaller
length term on hits (C34). All 42 paired deltas are positive; the sign test gives p = 0.0078
one-sided and p = 0.0156 two-sided (C35). Both are reported because the one-sided test is the
natural one (hits cannot be slower) but was not pre-registered as such in the card.

The residual is what matters for honesty. A hit still costs about **4.66 microseconds per
token** (0.004659 ms/token), so the correct claim is "prefill cost falls by a factor of 52",
not "prefill becomes free". At 31,415 tokens the hit still spends 231.6 ms, and at 1,024
tokens the saved time is 122 ms — the absolute saving is what an agent loop experiences, and
it scales with length.

## 8. The 64-token grid is a hit law, not a memory law

For byte-identical repeats the grid holds exactly. U2 sends 44 warm repeats at 314–1,550
tokens; every one satisfies `cached = 64 * floor((L - 1) / 64)` and every one has an uncached
residual of 0 (C37). The `(L-1)` form is the corrected boundary form — 1,024 and 1,088 miss
on the repeat (Section 9) while 1,023 and 1,025 hit, so a full 1,024 tokens are reusable, not
the naive `64 * floor(L / 64)`.

For appends the grid fails, and it fails universally. U4's 372 warm appends deviate from the
grid on **372/372** rows, with a true residual range of 832–7,936 tokens and median 1,792
(C38). The U4 handoff's "0.9–2.7k" figure is wrong: it is 832–7,936. The two datasets are not
the same data and are not in tension — U2 repeats 314–1,550-token prompts; U4's histories run
931–12,393 tokens, and the two share **zero** rows on `(case_id, salt)` (C39). The
earlier "contradiction" between U2 and U4 was a scope error, and the corrected statement is
that the grid is a property of *repeating the same bytes*, not of extending them.

Why appends deviate is not established. The profile looks like checkpointed state eviction in
the mamba/linear-attention path (the server exposes `max_mamba_cache_size` 64 and a
`linear_replayssm_cache_len` of 16), but we did not instrument that path and the hypothesis is
untested; `buckets` in the rows are observed cached values, not a model. What is safe to say
is that a context that grows will not get the byte-identical repeat's reuse, and any
cost model that assumes `64 * floor((L-1)/64)` for growing contexts will under-predict
uncached tokens by hundreds to thousands per turn.

## 9. A boundary rule at L = 0 mod 64

The immediate-repeat miss is not random. Only lengths with `L mod 64 == 0` miss on the
immediate repeat: 1,024 and 1,088 miss 5/5 then hit 5/5, while 1,008, 1,023 and 1,025 miss
0/5 (C40). Pooled, 10/10 against 0/15 on the immediate repeat, Fisher exact two-sided
p = 3.06e-07 (C41). The same isolation holds at the wider pool (35/35 vs 0/15,
p = 4.44e-13).

The miss is not repaired by time or by traffic shape. Waiting 0.25, 0.5, 1.0 or 2.0 seconds
between the two identical requests still misses, 20/20 (C42). Sending an intervening
63-token request does not repair it either, 5/5. A second identical repeat does: 10/10 at
`64 * floor((L-1)/64)` (C40). Cold requests are fully cold, 55/55 with zero cached tokens
(C43), so the boundary effect is not a warm-up artefact.

The operational warning is concrete: a workload whose prompt length happens to be a multiple
of 64 pays one full prefill before its prefix becomes reusable, and the cost is a full
re-prefill of an L-token prompt — 268.4 ms median TTFT at 1,024 tokens in these rows (C40),
and materially more at production lengths. Since prompt lengths drift with every appended turn, this is a
per-turn lottery rather than a one-off; a runner that can pad the prompt off the boundary
buys a cache hit for a handful of tokens.

## 9a. Cache-hit granularity across serving stacks

The 64-token grid (Section 8) was measured on one engine. This section states, for each stack
the batch actually ran, the grid it exhibited, the measured condition under which that grid
moves — or an explicit statement that no condition in these rows moved it — and the
cross-engine comparison. Every number below is a claim id in `CLAIMS.md` with one
`recompute.py` command, and the per-stack metadata (version, flags, gate verdict, cell ids) is
`RUN.json` `stacks[]`. **Pre-registered kill condition (stated before these numbers were
computed):** the cross-stack section is withdrawn if any stack's hot rows are not all exact
multiples of a single unit — i.e. if the gcd of `cached_tokens` over the rows with a non-zero
cached count does not divide every one of them. It holds on all seven stacks (C55, C61).

**What the grid is, measured over the whole cell.** The unit is the gcd of `cached_tokens`
over every row of the cell with a non-zero cached count, and "the unit holds" means every one
of those rows is an exact multiple of it. SGLang at the production default (`page_size 1`,
cell G3 S0) returns multiples of 64 on 880/880 hot rows, gcd 64 (C55, C57). SGLang with
`--page-size 64` (S1) gives the same 64 on 888/888 and, row by row against S0, is the same
value on 887 of 888 paired rows (C57): in these cells `--page-size 64` does not move the grid.
SGLang with `--page-size 128` (S2) gives 128 on 888/888, gcd 128 (C55, C57). vLLM 0.27.1 on
qwen3.5-9b returns multiples of 1088 on 300/300 hot rows for V1, 1056 on 268/268 for V2 and
2096 on 16/16 for V3 (C55).

**The vLLM unit is identified, not fitted.** A fit would be satisfied by any divisor of the
observed values; V1's rows contain **no** multiple of 1056 and V2's contain **no** multiple of
1088, while all 264 hot V1 rows are multiples of 1088 and all 264 hot V2 rows multiples of
1056, and the successive cached deltas have gcd 1088 and 1056 respectively (C56). The
requested `--block-size 64` (V1) and `--block-size 16` (V2) therefore do not determine the
unit: the resolved block size does, and it differs from both requests. V3 launched without a
`--block-size` flag and resolved 2096, with no hot row a multiple of 1088 (C56). The unit is
a property of the resolved configuration, not of the number the operator typed.

**The condition that moves it.** Between two SGLang page sizes the grid moved exactly once,
and by exactly one 64-block per row. S1 and S2 are the same workload, the same engine image
and a 900-row cell each; paired row by row, 534 rows are identical, 353 are lower by exactly
64 under `--page-size 128`, 13 are higher (by 832 or 896) and the paired delta set is
`{-64, 0, 832, 896}` (C58). The move is therefore a per-row arithmetic consequence of the
larger unit, not a regime change: the median time-to-first-token ratio between the pair is
1.005 (range 0.435 to 45.798), so **no measurable latency effect accompanies the grid move in
these rows** (C58). The per-turn uncached cost does rise slightly, 740.4 at 64 to 752.58 at
128, which is the same 64-token ceiling showing up in tokens rather than in milliseconds
(C58). Where the grid did *not* move: `--radix-eviction-policy slru` under deliberate eviction
pressure (TUNED, `--disable-chunked-prefix-cache` true, 259 documents pushed to a 1.505083
pressure ratio) still delivered multiples of 64 on 10/10 hot rows (C59), and `--page-size 64`
(S1) left it at 64 (C57). No row in this batch moves the grid below 64 on SGLang, and no
SGLang row in this batch produces a unit above 128.

**Cross-engine: the unit is not the cost.** The three engines do not share a unit — SGLang
and the TUNED variant deliver 64, vLLM delivers 1088/1056/2096 (C55) — but two SGLang
configurations that *do* share the unit 64 do not share a per-turn cost: TUNED spends 8,305.0
uncached tokens per turn at a 0.034474 hit fraction against S0's 739.25 at 0.974242, a
TUNED/S0 ratio of 11.2344, where vLLM V1 sits at 3.0176x S0 (C60). That gap is not a grid
effect: TUNED's 259-document push at 1.505083x pressure evicts the history the TUNED rows
would have reused, and its replay bands show it — 10/10 hits in the newest band and 0/10 in
each of the middle and oldest bands (C59). The three-engine comparison is therefore: grid unit
moves with the engine (five distinct units across seven stacks, C60), per-turn uncached cost
moves with *eviction pressure and hit fraction* independently of the unit, and the unit alone
predicts neither.

**G0 caveat, in the same breath as the cross-engine numbers.** No in-cell gate (G0) exists for
S1, S2, TUNED or S0; the only SGLang gate (`cells/SGLang/u2_gate.py`, mtime 2026-10-20 18:05)
predates the protocol these cells measured, so those four stacks' numbers are downgraded per
V-XSTACK2 and their restore check (`config_ok`) is a launch check, not a protocol gate
(`RUN.json` `stacks[]`). vLLM V1–V3 do carry an in-cell gate (`weighted_score` 0.975,
`config_ok` true, `all_compared_ok` true on restore, per V-XSTACK2 check 5), so the
cross-engine contrast in C60 compares a gated stack against three ungated ones. This caveat
does not change any recomputed value — it bounds what "the grid exists on engine X" licenses:
a regularity observed, not a contract verified.

**What does not travel.** The boundary rule (Section 9) is verified on SGLang only (C40–C43).
The append deviation (Section 8, C38) is SGLang-only. The 1.700x head-rewrite number (§6) and
the compaction findings (§4, §5) are SGLang-only and were not re-run on the second stack. The
vLLM unit 1088 is not a page size an operator can request — V1 asked for 64 and V2 for 16 —
so nothing here licenses choosing a vLLM block size to control the unit, and the vLLM battery
is 4 arms x 71 turns on one served model. TUNED reports `page_size 1` in `/get_server_info`
while its delivered rows follow the 64 grid; V-XSTACK2 reconciled this against
`_mamba_cache_chunk_size` 64, and the reconciliation — not a claim that TUNED has no grid — is
what C59 registers.

## 9b. The four-cell matrix: the engine sets the bill, the model sets it only under vLLM

Section 9a compares engines that served different models, so it cannot separate an engine
effect from a model effect. The 2x2 closes that (C63): two checkpoints (occamy-1.0, a Qwen3.5-MoE
hybrid-attention model in NVFP4; qwen3.5-9b, a dense hybrid-attention model in NVFP4) on two
engines (SGLang at its production `page_size 1`; vLLM 0.27.1), every cell on the same
32k/71-turn schedule — 4 arms x 71 turns = 284 rows per cell, 1,136 rows in all — with
the same prompt prefix digest and length on all six cell pairs (`prefix_sha256` 284/284,
`chars` 284/284 rows; the chat template moves
`prompt_tokens` by at most 4 on 140 of the 284 rows in the SGLang cells). No compaction fires
at this band, so the four arms are salt-separated replicates, not four policies.

| model | engine | hit | uncached/turn | cache unit (hot gcd) |
|---|---|---:|---:|---:|
| occamy-1.0 (MoE) | vLLM 0.27.1 | 0.901212 | 1,682.72 | 2,096 |
| occamy-1.0 (MoE) | SGLang | 0.957153 | 729.76 | 64 |
| qwen3.5-9b (dense) | vLLM 0.27.1 | 0.869037 | 2,230.78 | 1,088 |
| qwen3.5-9b (dense) | SGLang | 0.956941 | 733.37 | 64 |

**The engine is the lever.** Averaged over the two models, vLLM spends **+1,225.18** more
uncached tokens per turn than SGLang — 95 % percentile bootstrap over the 71 turns
[1,132.2, 1,313.3], 70 of 71 turns positive — a **2.6738x** ratio (2.3058x on the MoE,
3.0418x on the dense weights). That is **0.9115** of the 1,344.16-token grand mean. The
**model** main effect, averaged over the two engines, is **+275.83** [194.3, 357.6] — the
engine effect is **4.4418x** larger. The four salt-separated arms agree: recomputed per arm, the
engine effect is 1,216.2-1,229.7 and the model effect 274.0-281.2 across R/A/C/H.

**The model effect is engine-conditional, and that is the interaction.** Within vLLM the
dense checkpoint pays **+548.06** [384.7, 711.9] more uncached per turn than the MoE
(1.3257x); within SGLang the two models differ by **+3.61** [0.0, 10.8] uncached per turn
(1.0049x), positive on **1 of 71** paired turns. The interaction is **+272.23** [190.1,
354.6]: the model effect is **152.00x** larger under vLLM than under SGLang. The mechanism is
the one Section 9a measured: SGLang delivers the 64 grid to both checkpoints (hot gcd 64 in
both cells), while under vLLM the resolved block is a property of the checkpoint — 2,096 for
the MoE, 1,088 for the dense hybrid — and the dense hybrid forfeits one block per turn rather
than losing one at block completions (Section 9a; the pilot-level contrast is in `CAPTURE`,
not a claim here). The engine that pages at 64 also hides the model's per-turn cost.

**What this licenses, and what it does not.** At this band, an engine main effect predicts
each model's engine ratio to within 14 % (2.6738x against 2.3058x and 3.0418x), and a model
main effect predicts each engine's model ratio to within 14 % as well (1.1653x against
1.3257x and 1.0049x) — the residual is the interaction, and it says a per-turn bill cannot
be read off either factor alone. It is one schedule at one band (32k, 71 turns), one seed,
one GPU; the two checkpoints differ in size and architecture as well as MoE-vs-dense, and
the engine axis also carries each cell's launch flags (vLLM resolved blocks 1,088 / 2,096;
SGLang `--mem-fraction-static` 0.22 on the dense cell). The 64k band was run on SGLang only;
the matrix is a measured 2x2, not a law over models or engines (`GAPS.md` G4).

## 10. What a designer should take away

Five rules follow from the measurements, in descending order of confidence.

1. **Keep shared bytes identical and branch late.** Fan-out reuse is bought by byte layout,
   not by pointer bookkeeping (Section 3). Any serializer that prefixes per-branch metadata
   before shared content will pay the full prompt per branch.
2. **Prefer append over rewrite when the window allows it.** Append-a-note reached a 0.927
   hit rate against summarise-in-place's 0.737, at the cost of an unbounded window (Section
   6). The win is 1.70x on uncached tokens, and 92 % of the competing arm's penalty is
   steady-state truncation, so an implementation that shortens its window to save tokens per
   turn is optimising the smaller term. G1 decomposes the break cost (E/F = 1.038, within
   measurement noise; only 2/6 break events within 10 %), so the 1.70x is a compaction-window
   cost, not a fork/append cost (C44).
3. **Never evaluate a compaction policy on aggregate accuracy alone.** A planted fact can go
   from 190/190 to 0/190 with a 2-point accuracy move (Section 4). Content retention is the
   instrument; accuracy is not.
4. **Do not assume the 64-grid for growing contexts.** It holds for repeats (44/44) and
   fails for appends (372/372), and lengths on the boundary pay a full re-prefill (§9).
   Budget the observed residual, not the law.
5. **If the workload will not fit, budget the boundary as a window cost, not a one-off —
   and budget it per turn, not on the average.** Compacted at a real 32k/64k limit, the
   compacting arms pay +134.6 to +747.2 uncached tokens per turn *on average* (twelve arm
   means) for the rest of the run, against a compaction-free baseline they were
   indistinguishable from before it; a single turn of that segment runs -927 to +5,473 and
   every arm has turns below its baseline, so a per-turn budget must not be set from the
   mean (§6a, C62). The bill is a lost prefix, not a boundary
   event: the arm rebuilds a shorter prompt at a worse hit rate for every turn that follows,
   so the lever is how long the run continues after the boundary and what the resting window
   is set to — not how cheap the boundary turn itself is (the boundary turn costs 1,826-3,033
   uncached tokens over all 18 compactions, against the baseline's own window drop at
   1,236-1,321 over six drop rows).

Resident capacity (cell M4-EVICT, 283 documents at 1.5017x pressure). The binding constraint is the state cache (max_mamba_cache_size 64), not KV token capacity: only 30-31 documents (258,035-266,636 tokens, 0.1592-0.1645 of the 1,620,892 declared token capacity) remain resident; verdict consistent_with_lru, with token-pool LRU (188.45 documents) excluded.

## 11. Limitations

**Two models, two engines, one seed.** The core batch (Sections 2-8) comes from a single
SGLang endpoint (`http://192.168.2.168:8012`) serving `occamy-1.0` — a Qwen3.5-MoE hybrid-attention model
(`Qwen3_5MoeForConditionalGeneration`, `model_type: qwen3_5_moe`) with NVFP4 weights, whose
stack is mostly linear attention (30 of 40 layers, per the model architecture). That hybrid
stack is exactly where the 64-grid and the append deviation are least likely to transfer: the
mamba/linear-attention path has its own checkpoint economy (`max_mamba_cache_size` 64,
`linear_replayssm_cache_len` 16), and a pure-attention model with a plain radix cache may
show neither the boundary rule nor the append deviation. The matrix in Section 9b adds a second
checkpoint (`qwen3.5-9b`, dense) and a second engine (vLLM 0.27.1) on the same 32k schedule,
which separates the engine effect from the model effect at that band (C63); it adds neither a
second seed nor a second GPU, and the two checkpoints differ in size and architecture as well
as MoE-vs-dense. Nothing here establishes behaviour for other endpoints, other model
families, or other serving stacks, and the corpora are synthetic in-cell texts generated by
one driver with seed 1729.

**The boundary result is one cell, one seed, and one trigger.** The compaction cost at the
limit (Section 6a, C62) rests on a single cell in which each compacting arm fired once at 64k
(47, or 27 for F-k800, turns after the boundary) and twice at 32k, all in one seed and one
corpus, with the compaction requested at the budget's edge rather than after an actual
overrun. The arms are compared turn for turn with a baseline rendered in the same bytes, which
is what makes the pre-boundary flatness a control rather than a coincidence, but the post-
boundary averages cover 47 to 89 turns and a long run would move them; the baseline's own
window drops put it on a different resting window from the compacting arms by construction,
and separating "the arm compacted" from "the arm therefore rests shorter" would need an arm
that compacts to the same window, which this cell does not have.

**The post-boundary segment is bimodal, so "the cheap arms" is a mean effect, not a
per-turn one.** The median matched-turn difference after the boundary is **10 / 5 / 7** for
32k `S` / `S-ptr` / `F-ptr` — that is, those arms sit *at* their baseline on a typical turn —
against **836–900** for the other nine arm-instances (32k `F`, `S-k800`, `F-k800`; every 64k
arm). Their means are larger than their medians because a minority of turns, the ones around
the baseline's own window drops, carry the whole excess: 32k `F-ptr` has a mean of +134.6 but
a median of +7, and 11 of 12 arms contain at least one turn below their baseline. A reader
must therefore not read the arm ranking (pointer renderer and `keep_last` 800 "cheap") as a
claim about a typical turn — under it is a mix of near-zero turns and a few very expensive
ones, and only the mean orders the arms.

**One 64k arm carries a third fewer post-boundary turns.** 64k `F-k800` covers **n = 27**
turns against **n = 47** for the other four 64k arms (and 89 at 32k), because its second
compaction left it fewer turns before the run ended. Its mean (+653.5) and median (+836) are
computed over a different window of the run than its siblings', so it should be compared with
them with that narrower base in mind rather than as an equal-n arm.

**Single seed and narrow replication.** The fan-out result (Section 3) rests on **one seed and
one race-free cell**: the bound we report is B/A = 6.744 [4.045, 9.443] from a single
race-free cell (G5, 8 fan-outs x 8 branches, 192 rows), and that cell — not a second seed — is
what lifts the effect above the earlier 3.31 measured / 5.39 projected band, both of which are
superseded pre-G5 values. The 5.39 figure was a counterfactual projection from the same 24
rows of the single-fan-out cell, not a second run, and G5 shows it was not an upper bound.
U9 resolved six lengths with seven
repetitions each (139 of a planned 200 requests); U10's boundary cells are n = 5 per length,
on 159 requests, and its wider pool came from a second phase rather than a replication of the
first. U15 ran one corpus, one scenario and 40 turns per arm.

**Mechanism is thinner than the measurements.** We can decompose R's penalty arithmetically
(Section 6) but we did not instrument the server, so the per-turn re-prefill is described, not
explained; the mamba-checkpoint account of the append deviation (Section 8) is an untested
hypothesis; and F's late-run advantage is observed without a mechanism. The compaction
policies themselves use a deterministic offline stub summariser (750 characters, about 188
tokens), not a model-generated summary, so the absolute numbers would move under a real
summariser even if the ordering held.

**Generality of the workload.** Turns are synthetic and roughly constant in size; `max_tokens`
was 4 and thinking was disabled, so decode time is negligible and TTFT dominates. A workload
with long generations, concurrent batches (the server allowed 5 running requests, but
requests were sent serially), or interleaved sessions could change both the cache-hit
economics and the latency ratios.

## 12. Provenance and how to recompute

Every value in this manuscript is listed in `CLAIMS.md` with one command per claim: the
recompute harness `papers/context-cache/recompute.py` for values derived from rows, and the
two verifier replay scripts (`cells/CX-V2/u5_recon.py`, `cells/CX-V2/u4_recon.py`) for the
renderer-identity and fixed-library results. `RUN.json` carries the unit table, request
counts, corpus digests, row digests, and the pre-registered kill conditions with their
outcomes. The independent verification of the source units is `orchestration/handoffs/CX-V2.json`
(overall verdict: fail — it refuted a mid-run-rewrite premise and resolved two
contradictions); this package is written against that verdict rather than against the
original unit cards, and where the two disagree the verifier's version is used and the
correction is named in `EVIDENCE.md`.
