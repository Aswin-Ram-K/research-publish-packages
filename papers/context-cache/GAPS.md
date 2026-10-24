# GAPS.md — what this package cannot support

Each gap names what would close it. The first two are load-bearing: they change how the
record must be read, not just how far it generalises. G3's status changed on 2026-10-23:
G3-LIMIT-V2 measured compaction at a real 32k/64k boundary (C62), so what was an unmeasured
limit case is now a measured band with a named remainder — read the G3-FOLD statement first,
and treat the X-SYNTH / G3-CLOSE statements below it as history.

**Status ledger (GAP-TRIAGE, 2026-10-23).** `state/gap-ledger.json` derives a status for all
sixteen sections from evidence on disk: **2 closed** (G1, G5), **3 narrowed** (G3, G4, G11),
**10 open**, and **1 unverifiable** (the downgrade note). Of the ten open, eight are **stated
limitations** — the measurement that would close them has not been run, and no claim in
`CLAIMS.md` rests on the missing measurement — and two (G12, G14) carried **stale prose** that a
later cell had already outdated; both are corrected in place below, dated to this unit. The
per-gap decisions and their evidence are `state/gap-triage.json`. **`verify_package.py` printing
`UNVERIFIED: none` is not a statement about this list:** that gate checks that every claim value
in `CLAIMS.md` is mapped to a runner and a cell with rows, so a gap is a boundary of what was
measured, not an unverified claim. Reading `UNVERIFIED: none` as "no open gaps" reads the gate
for the property it does not test.

*(CACHE-AUDIT, 2026-10-23: **G16** is added below and is **not** in the tally above, which was
taken before it existed. Its decision is a **stated limitation** — the options it names were not
run, and no claim in `CLAIMS.md` rests on them; two rejections it re-checks (`PACKAGE.md` §4,
`docs/serving-options/LAUNCH-SGLANG.md`) are downgraded to unverified, which removes evidence
rather than adding it. **Superseded in part by FIX-G16-LEDGER, 2026-10-23:** the ledger and the
triage record now carry G16 (`state/gap-ledger.json`, `state/gap-triage.json`), so the test above
passes; the counts in the paragraph above (2 closed, 3 narrowed, 10 open, 1 unverifiable) still
predate G16 and now read **2 closed, 3 narrowed, 11 open, 1 unverifiable** — that tally is the
owner's text and was not edited.)*

## G1. The fork hypothesis is untested, not refuted — STATUS: CLOSED by G1 (C44)

**One-line verdict (G1):** NOT REFUTED — per-break cost in EDIT is not within 10 % of FORK across all 6 break events (2 of 6 within 10 %; mean gross E=1,728.0, F=1,664.0, ratio=1.0384615); U15's 1.700x does not survive decomposition (u15_1_700x_survives_decomposition=False): it is 92.2 % post-compaction window truncation, not break-event cost (264 rows, sha256 9242ad383281b360ec3c4be92bc59e7de7d5cd751eb7e15c0944f2261497ae66).

*Historical text (kept for followability; the gap is now closed by the measurement below):*

U4's comparison of fork against summarise-in-place measured one renderer against itself
(`cells/U4/u4_cell.py` never imported `POINTER_FORK`, and `render.py` emits `node.text`, not
`node.kind`), so its "identical break cost" result carries no information about forking
(MANUSCRIPT §5). U5's fork arm has the same defect and is a second summarise sample. U13 made
the policies genuinely distinct offline and U15 ran fork with the marker, but U15's fork arm
answered a different question: whether fork and summarise differ in *total uncached tokens
over 40 turns*, where they are within 8.7 % of each other. The question U4 posed — do the two
policies have different break cost at the event — has **zero** pairs under the fixed library.

*What would close it:* a re-run of U4's matched-pair design (three sessions x 44 turns, seven
compaction events) with the post-U13 library, reading the fork marker's effect on break cost.
The design and the analysis code already exist; only the rows are missing. Until then, any
sentence of the form "fork and summarise cost the same" is unsupported, and the correct
statement is "the break-cost comparison has not been made".

*Status check (GAPS-GSWEEP, 2026-10-23) — closed, and the historical text below is now
literally stale:* `cells/CX-V2/u4_recon.py` rebuilds all 12 units from `u4_sessions.json` under
the post-U13 library and the head digests reproduce the live rows 44/44 in both arms in all
three sessions (`reconstruction check (head digest == live row prefix_sha256): summarise 44/44,
fork 44/44`), while the body digests separate the arms from turn 12 (`body digest equal 11`,
bodies 19,998 vs 20,173 bytes at turn 12), so the fork marker is being rendered. The two
sentences immediately above ("`POINTER_FORK` never imported", "U5 is a second summarise sample")
describe the *pre-U13* build: they are superseded by C16, not contradicted, and should be read
as history. The gap itself stays closed; what the 44/44 does **not** cover is the live
break-cost pairs, which the G1 measurement at MANUSCRIPT §5 supplies independently.

## G2. U4's 438 rows cannot be salvaged — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

The rows record the uncached counts produced by three policy objects rendered by one
appender. Re-deriving policy-level quantities from them would repeat the confound. They are
retained in the package only as evidence *of* the confound (C11, C12, C13, C16) and are not
used to support any positive claim about edit policies. The card's 454-request figure also
exceeds the 451 requests recorded in files (438 batch + 13 probe); the extra three are smoke
sends recorded only in the unit card (C14).

*What would close it:* nothing short of a re-run; the rows are a record of an instrument
error, not a dataset with a fixable defect.

## G3. Append-a-note is not usable beyond the context limit — STATUS: MEASURED at the 32k and 64k boundary by G3-LIMIT-V2 (2026-10-23, C62), NARROWED but not closed

**G3-FOLD statement (added 2026-10-23, after G3-LIMIT-V2 was analysed as C62):** the premise's
first half is now measured and the second half is not. Cell G3-LIMIT-V2 (`cells/G3-LIMIT-V2/`,
2,780 rows, sha256 `589662cef35cbdf6c54b3f75ff11dff9a86e618fc8c77fa3dbcc0d5a2d573382`, 18
compaction events) drove six compacting arms past a real 32k budget and six past a real 64k
budget, each against a compaction-free baseline rendered in the same bytes, and it contains
the rows the earlier cells lacked: `compacted_this_turn` true on 18 rows (and
`trigger_reason` a boundary reason, not `below_budget`, on each of them), with at least one
boundary per arm per budget (turn 71 at 32k, turn 143 at 64k). The control segment is flat —
before any arm compacted, the matched-turn delta between arm and baseline was −11.8 to +51.0 uncached
tokens per turn and **0 of 12** bootstrap intervals excluded zero — and after the boundary it
is not: **+134.6 to +747.2** uncached tokens per turn **on the arm means** (twelve means over
27–89 turns), 11 of 12 intervals excluding zero (the exception is the pointer fork at 32k,
+134.6 [−12.8, 285.9]). Those twelve means are not a per-turn range, and the difference is the
gap's own evidence rather than a technicality: **per turn** the segment runs **−927 to +5,473**,
and **all twelve arms carry at least one turn below their baseline** — the arms pay on average
and unevenly, so any statement that reads the band as a per-turn floor (or as "nothing before
it" applied per turn) is wrong for this cell. So "compaction at the limit
costs something" is now measured rather than inferred, and the rows say what it is: the
compacting arms rest at 11,009–13,546 tokens by their last 32k turn and 22,643–23,765 by
their last 64k turn, against the baselines' 9,896 and 22,063, so they carry *more* prompt
after the boundary as well as resting on a different window (MANUSCRIPT §6a). The mechanism
is that the boundary destroys the reusable prefix — `cached_tokens` 0 on the compaction row where the baseline's previous turn carried
31,552 — and what the arm rebuilds is a shorter prompt with a worse hit rate, not a longer
prompt: on its second 32k boundary arm S restarts at 2,812 tokens where the baseline stood on
30,717 the same turn, and still pays more uncached per turn thereafter.

*What is still not settled, and is now the gap's remainder:* (i) the **trigger**. All 18
compactions were requested on `projected_prompt_exceeds_budget_headroom` — the cell asked for a
compaction when the projected prompt came within a headroom of the budget — so the cost
measured is that of compacting at the limit's edge, not of a request that actually overran the
window. (ii) The **length of the post-boundary segment**: the arms fire once at 64k (47 turns
after the boundary, 27 for F-k800) and twice at 32k (89 turns after the first), one seed and
one corpus, so the +134.6…+747.2 band is an average over 27–89 turns and says nothing about a
long run — and, because it is an average, it is not a per-turn range either (−927…+5,473, as
above). (iii) The **separation**: the baseline's own window drops put it on a
different resting window from the compacting arms by construction, and the arms do not
separate by policy at 64k, so "the arm compacted", "therefore its window differs" and "which
rewrite it used" cannot be pulled apart with a cell that has no arm compacting to the
baseline's window. (iv) The second engine: G3-LIMIT-V2 is SGLang only.

*What would close it:* a trigger that lets the prompt overrun a budget by a known amount
before compacting, an arm that compacts to the baseline's window (isolating the truncation from
the resting-window difference), a 64k run longer than F-k800's 27 post-boundary turns, and the same three on vLLM.

*The earlier verdicts, kept for followability and superseded by the above:*

*X-SYNTH second-pass statement (added 2026-10-23, after the cross-stack cells and V-XSTACK2):*
the cross-stack window **did not** touch this gap and could not have. Cells WIN-SGL (1,800
rows, 32k/64k depths), WIN-VLLM (692 rows, `max_model_len` 32768), TUNED (289 rows, doc-push
pressure) and G3 (888 rows) all ran below the context limit; none scheduled a compaction and
none contains a row where an arm is inside its window while another is outside it. The
purpose of the second pass was grid granularity, and grid granularity is measured on prompts
that already hit — an eviction or limit study would have needed a different workload, not a
different page size. The gap therefore stays at the bound G3-CLOSE set (32k arms 721.9 / 723.4
/ 734.4 / 723.3 uncached per turn, spread 1.722 %; 64k 742.3 / 749.0 / 749.6 / 743.2, spread
0.976 %; `scheduled_compaction` false on 888/888 rows), and it is **not** upgraded by the two
new stacks. No number in this paragraph is new: C47 (G3 S0 rows) and the G3-CLOSE analysis
supply them.

**One-line verdict (G3-CLOSE):** NOT SETTLED as a limit result — the 888-row cell G3 never
crossed its own budget (`scheduled_compaction` false on 888/888 rows; `events.jsonl`
`compaction_events` empty; the run log's own schedules are `schedule=[]` for both depths), so
R, A, C and H executed one identical no-compaction trajectory and differ only by their one-token
per-turn control token. The 4-arm spread at each depth (mean uncached per turn: 32k 721.9 /
723.4 / 734.4 / 723.3, spread 1.722 % of the minimum; 64k 742.3 / 749.0 / 749.6 / 743.2,
spread 0.976 %) is therefore a 1-token-per-turn difference, **not** a measurement that append-note
costs what summarise-in-place costs. What the rows do carry is that **no arm avoided the
limit**, and that the hybrid's own limit-handling branch never executed: `A_available False` at
both depths is a property of the shared trajectory, and because H switches policy only on a
scheduled compaction, its post-limit behaviour is the one piece of H that was never rendered.

*What would have to be true for the opposite conclusion (closed as refuted, "arms within 1.7 %
at 32k and 1.0 % at 64k; no arm avoids the limit; the differentiator is window policy"):* at
least one arm must have compacted while another did not. A refutation of G3's premise needs A to
be measured against an arm that is still inside its window — i.e. `scheduled_compaction` true on
some row, one A row that survives without compacting, and a live 2.5 %-of-budget boundary
(800/1,600-token `keep_last` budget starting at 1,187 prompt tokens, tracked by
`est_chain_tokens_before`). None of the three holds in these rows.

*What would close it now:* a boundary-triggered cell — request-side `prompt_tokens` > budget
(the 32k/64k labels are 32,768/65,536, not the 2.5 % sandbox), a real `keep_last` budget instead
of 2 nodes, and a compaction-free baseline arm, so that A's failure and H's first
post-limit compaction are both measured at the turn they occur. Prerequisite: a larger request
cap (G3 ran 888/900) and a turn count that reaches 65,536 given 1,187-token start plus ~505/turn.

*Second-pass note on the prerequisity (2026-10-23):* the second pass supplies a fourth
prerequisite, and only that: the vLLM stack now exists as a second engine (V1/V2/V3, C48–C56)
but ran at `max_model_len` 32768 with 71-turn batteries well below it, so "a limit-triggered
cell on a second engine" is *possible now* and still **not run**. Naming it is not evidence
that it was run.

*Historical text (kept for followability; superseded by the verdict above, since no row in
cell G3 draws a limit):*

X-SYNTH did not run append-note at the context limit and did not measure a hybrid
(append until limit, then compact). The gap is unchanged: the package establishes a result
for workloads whose histories fit, and says nothing about what to do when they do not.
Reason it was not settled: the cross-stack window exercised cache-hit granularity (page/block
size), not context-limit behaviour; no new bound exists beyond the original statement.
Arm A wins on uncached tokens (1.700x over R) precisely because it never shrinks: its window
grows from 1,186 to 19,583 tokens over 40 turns, 16.5x, and its final prompt is more than
four times arm R's (MANUSCRIPT §6). In a workload that reaches the context limit, append-note
is unavailable, and the choice collapses to summarise-in-place versus fork — which is the
untested comparison of G1. The package therefore establishes a result for workloads whose
histories fit, and says nothing about what to do when they do not.

*What would close it:* a run at 32k or 64k context where A must either fail or compact, and a
comparison of what a hybrid (append until the limit, then compact) costs against A and R.

## G4. Single model, single endpoint, one seed — STATUS: NARROWED by X-SYNTH (first pass); NARROWED further and bounded by measurement in the second pass, 2026-10-23

**The bound that replaced the unknown (second pass, C55–C60):** the grid is no longer an
SGLang-only observation. It is measured on **three engines** — SGLang (unit 64 at the
production page size and at 64, 128 at page size 128), vLLM 0.27.1 serving qwen3.5-9b (units
1088 / 1056 / 2096) and SGLang with SLRU eviction under 1.505083x pressure (unit 64) — and the
unit is identifiable rather than fitted for vLLM (0/264 V1 hot rows are multiples of 1056;
0/264 V2 hot rows are multiples of 1088, C56). **Five distinct units across seven stacks**
(C60). What is *not* replaced, and must not be read as replaced: the second engine is a
**different model** (`qwen3.5-9b`, served by vLLM 0.27.1 on `:8014`) as well as a different
engine, so this pass separates "grid vs. engine" — every engine tested exhibits a grid, and
the unit tracks the resolved block/page size rather than the engine name — but it does **not**
separate engine from model, and the two results most likely to be model-specific, the 64-grid
as a *token* boundary (§8, C37–C43) and the append deviation (§8, C38), remain SGLang-only on
this checkpoint. The one condition measured to move the grid moved it by exactly one block on
353 of 900 paired rows, with a paired median TTFT ratio of 1.005 (C58): granularity is a
measured lever on residency, not on hit cost in these rows.

Still single, unchanged by the second pass: one corpus seed (1729); the fan-out (G5, C53),
U15 head-rewrite (§6) and compaction (§4–§5) units were **not** re-run on vLLM; three of the
four stacks with a grid (S0, S1/S2, TUNED) have **no in-cell G0** (V-XSTACK2 check 6), so the
cross-engine contrast compares one gated engine with three ungated configurations.

*First-pass text (kept; it understates the count — the second pass measures the units over whole
cells and finds five across seven stacks, not three configurations):*

Cross-stack evidence now covers three configurations: SGLang occamy NVFP4 (page_size 1/64/128,
888+900+900 rows), vLLM qwen3.5-9b (block 1088/1056/2096, 692 rows) and TUNED occamy
NVFP4 SGLang (289 rows) (MANUSCRIPT §9a, C45–C52). The cache grid is therefore not an
artefact of one SGLang build: it appears on vLLM with a different unit (1088/1056/2096).
What remains single: one model family (occamy NVFP4 / qwen3.5-9b, both Qwen3.5-MoE
hybrid-attention), one corpus seed (1729), one endpoint per stack, and the fan-out/compaction
units were not re-run on the second stack. The 64-grid and append-deviation results are still
SGLang-only and may be model-specific.
Everything in the package comes from one SGLang endpoint serving `occamy-1.0`, a
Qwen3.5-MoE hybrid-attention checkpoint in NVFP4 whose stack is mostly linear attention (30
of 40 layers, per the model architecture). All corpora were generated by one driver with seed
1729. No result is replicated on a second model, a second serving stack, a second seed, or a
second endpoint, so none of the mechanisms can be separated from this model's hybrid
attention and this server's cache implementation. The two results most likely to be
model-specific are the 64-grid (Section 8) and the append deviation, both of which sit
against the mamba/linear-attention checkpoint machinery.

*What would close it:* the same units on at least one pure-attention model and one non-SGLang
stack, and a second seed for the corpus. The U15 design costs 160 requests, so replication is
cheap; the expensive part is a second endpoint.

**Narrowed again by the measured 2x2 (MATRIX-FOLD, 2026-10-23, C63).** The sentence above —
that the second pass "does **not** separate engine from model" — is superseded. MOE-VLLM
(occamy-1.0 on vLLM 0.27.1) and DENSE-SGL (qwen3.5-9b on SGLang) complete the 2x2, so both
checkpoints have now run on both engines, on the same shared 32k/71-turn schedule
(prompt prefix digest and length equal on all six cell pairs: `prefix_sha256` 284/284, `chars`
284/284; 4 arms x 71 turns = 284 rows per cell). At that
band the **engine** main effect is **+1,225.18** uncached tokens per turn [1,132.2, 1,313.3],
positive on 70/71 paired turns, and the **model** main effect is **+275.83** [194.3, 357.6],
positive on 53/71: the engine effect is **4.4418x** the model's and **91.2 %** of the 1,344.16
grand mean. The model effect is engine-conditional — **+548.06** [384.7, 711.9] under vLLM
(1.3257x) against **+3.61** [0.0, 10.8] under SGLang (1.0049x, 1/71 turns), an interaction of
**+272.23** — because SGLang pages both checkpoints on the same 64 grid while vLLM's resolved
block is a property of the checkpoint (2,096 MoE, 1,088 dense). What the 2x2 does **not** buy,
and what G4 still carries: one band (32k; vLLM ran no 64k), one seed, one GPU, two checkpoints
that differ in size and architecture as well as MoE-vs-dense, and per-model launch flags inside
the engine axis (vLLM block 1,088 vs 2,096; SGLang `--mem-fraction-static` 0.22 on the dense
cell). The 64-grid as a token boundary (§8, C37–C43) and the append deviation (C38) remain
SGLang-only on this checkpoint.

## G5. Fan-out ratio — STATUS: CLOSED by G5 (C53)

*Second-pass status (2026-10-23, X-SYNTH): still CLOSED, and the second pass adds nothing to
it — neither a measurement that narrows it nor a reason to reopen it.* The cross-stack cells
did not run a fan-out on any second engine; the one row-level fact they add is incidental —
TUNED's replay bands show the same placement logic from the other side (newest band 10/10
hits, middle 0/10, oldest 0/10, C59), which is eviction under pressure, not fan-out. The bound
stands at B/A = 6.744 [4.045, 9.443], C/A = 1.105, 192 rows, cell G5, single seed — and the
single-seed limitation in §11 is still the honest qualifier on it.

Race-free measurement: B/A = 6.744 [4.045, 9.443] (8 fan-outs x 8 branches), replacing the
3.31-5.39 band. Layout B has zero cache hit because per-branch histories never share a prefix;
Layout C costs 19,792 uncached (C/A = 1.105).

*Status check (GAPS-GSWEEP, 2026-10-23): no line in this gap is contradicted by the current
evidence; the bound is unaltered at B/A = 6.744 [4.045, 9.443], 192 rows, cell G5.*
*Closed where it is read:* the manuscript states the same bound in the abstract (MANUSCRIPT:14,
with the cell and its 8 x 8 condition in the same sentence), in the §3 arm table (MANUSCRIPT:100,
both arms against the superseded 3.3133) and in the §11 single-seed limitation (MANUSCRIPT:439-444,
which names the single cell as the replication limit). The guard
`tests/test_paper_attribution_guard.py::test_g5_fanout_attribution_is_present` pins the §3
figure-carrying sentence; it does not pin the abstract, so this line records the reader-facing
scope of the closure rather than a second check.

### Resident capacity (M4-EVICT) — measured bound, not a gap

Resident capacity is now a measured bound, not a gap: the state cache (max_mamba_cache_size 64)
binding constraint at 1.5017x pressure; only 30-31 documents (258,035-266,636 tokens,
0.1592-0.1645 of the 1,620,892 declared capacity) remain resident (M4-EVICT, C54); verdict
consistent_with_lru.

*Stated as the bound where the paper needs it:* MANUSCRIPT:424 carries all four numbers
(30-31 documents, 258,035-266,636 tokens, 0.1592-0.1645, 1,620,892 declared capacity) and the
verdict consistent_with_lru, with token-pool LRU (188.45 documents) excluded. It sits in the
"what changes an implementation's decision" list, not in §11's limitations, which is the correct
reading of a measured bound. Scope of the bound: 283 documents at 1.5017x pressure on this one
endpoint; it is not a prediction for a different `max_mamba_cache_size` or a pure-attention stack
(that stays G7).

## G6. The compaction decomposition is arithmetic, not instrumented — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

U15's central claim splits R's excess over the control into 7.8 % break and 92.2 % steady
state by subtracting the two break turns. That decomposition is exact for the totals. What it
does *not* explain is why R re-prefills about 1,660 tokens per turn between compactions when
its prompt is only 5,812 tokens on average and its summary node is constant: the rows show
768–1,920 cached tokens against 2,394–4,209-token prompts on turns 19–23, which is consistent
with the window's tail being re-rendered but was not instrumented. The same is true of F's
advantage over R in turns 36–40 (4,595 vs 9,011 uncached), which we report without a
mechanism.

*What would close it:* per-turn prefix-diff logging (which node ids change between turns) or
a server-side radix-tree dump, so that the re-prefilled span can be attributed to the sliding
window, the summary node, or cache chunking rather than inferred.

## G7. The append deviation from the 64-grid is an untested hypothesis — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

Every one of 372 warm appends deviates from the grid (residual 832–7,936, median 1,792), but
the cause is not established. The profile is consistent with checkpointed-state eviction in
the mamba/linear-attention path (the server exposes `max_mamba_cache_size` 64 and
`linear_replayssm_cache_len` 16), and that is where the hypothesis stops.

*What would close it:* sweep the residual against the number of live mamba checkpoints and
against `max_mamba_cache_size`, or run the same append pattern on a pure-attention model
where no such checkpoint economy exists. If the deviation disappears there, the hypothesis
becomes a finding; if it persists, it is a property of the radix cache instead.

*Status check (GAPS-GSWEEP, 2026-10-23) — still open, but for a narrower reason than stated
above.* The described sweep was **not** run (no row file sweeps live checkpoints against the
residual). What does now exist is a hostile, controlled comparison: M4-EVICT measures the
mamba state cache being the binding constraint and uses 1.5017x deliberate eviction pressure
(MANUSCRIPT:424, C54), and the cross-stack cells reach vLLM with a different cache unit
(1088/1056/2096, C49) and TUNED SGLang with SLRU (C52) — none of which tests the append
deviation directly. So the hypothesis is still untested *as a mechanism*; what changed is that
"the state cache can bind" is now measured elsewhere in the package. The remainder is exactly
the pure-attention control.

## G8. Latency covers six lengths and TTFT only — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

U9 resolved six lengths (1,024 to 31,415 tokens) from 42 paired observations, 139 of a
planned 200 requests. The power law is fitted to six medians; the OLS slopes to 42 rows. Only
time-to-first-token is measured — no inter-token latency, no end-to-end time, and `max_tokens`
was 4 so decode is absent by design. The 4.66 µs/token residual is a property of this
endpoint under this load (serial requests, 5-slot concurrency limit), not a constant.

*What would close it:* more lengths (at least a decade above 31k, which needs a larger
context), repeated runs under concurrent load, and inter-token latency. The residual is the
quantity a deployment budget needs, and one endpoint is not enough to fix it.

## G9. The boundary rule has five cells per length — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

U10's per-length counts are n=5 (`1,008/1,023/1,024/1,025/1,088`), which is why the pooled
35/35 versus 0/15 statement is carried alongside. The mechanism — why a length that is a
multiple of 64 misses exactly once — is not established, only the boundary condition and the
repairs (time does not help, a 63-token interleave does not, a second repeat does).

*What would close it:* n=20 per cell and lengths 960, 1,152, 2,048, 4,096 (planned but not
run), plus a server-side trace of the chunk insertion at the boundary.

## G10. The accuracy comparison sits on a noise floor — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

Two U5 arms with byte-identical prompts agree on only 174/190 cases (91.6 %), so the 86.8–87.9
% baseline-versus-compacted agreement is a small difference above a sampling floor, not a
large effect. The retention measure (190/190 vs 0/190) is not subject to that floor, and it is
the result the manuscript leans on. The retention check is a string test for the planted gold
line, not a semantic judgement, and the task's multiple-choice accuracy does not measure
whether the answer was *grounded*, only whether the letter was right.

*What would close it:* repeated sampling per case (the 91.6 % floor shrinks with reps) and a
graded, model-judged correctness measure rather than a letter match.

## G11. U15's recompute is independently verified, but its quality measure is not

*Partial closure by G1 (C44):* G1 independently re-derives the break-cost decomposition
(1.038) from 264 rows; it does not verify U15's total-uncached comparison or accuracy.

*CX-V3 closed 2026-10-21 (these lines re-checked by FIX-GAPS-RUN2, 2026-10-23, against
`orchestration/VERDICTS.md:12`):* an earlier revision of this gap read CX-V3 as pending.
`orchestration/VERDICTS.md:12` records `2026-10-21 05:22 | CX-V3 | context-cache | PASS` —
`recompute.py all` 41/41, u5_recon 760/760, 13/13 digests match, red→green 1/1 reproduced
(1.7002→1.6002 ⇒ `FAIL 4/5`; restored ⇒ `PASS 5/5`). The matching stale attribution in
EVIDENCE.md §5 (":240 until it rules, the 1.700x ... not verified by a different agent") was
fixed in that file by FIX-EVID-DOC on 2026-10-23, so EVIDENCE.md no longer contradicts this
gap; it is a sibling card's file and was not edited here.

U15's result is the package's headline, and its 1.700x figure has now been re-checked by a
different agent (CX-V3, 2026-10-21: `recompute.py all` 41/41, 13/13 digests matching,
red→green reproduced). What U15 measured is still tokens, not correctness — no accuracy or
retention is recorded for the four arms, so the package cannot say whether the cheaper arm is
also the better one. The stub summariser is deterministic (750 characters, about 188 tokens),
so the absolute numbers would move under a model-written summary. U15 covers one corpus, one
scenario, 40 turns.

*What would close it:* two measurements, not a verdict: a graded correctness measure on U15's
completions, and a re-run with a real summariser (the expensive one). Independence is **not**
an open condition — CX-V3's pass is on record, 2026-10-21 05:22 PASS (`recompute.py all` 41/41,
13/13 digests, red→green 1/1), so the earlier "until CX-V3 rules" closure condition is spent.

## G12. The workload is synthetic and serial — STATUS: OPEN (stated limitation; stale prose corrected 2026-10-23)

Corpora are generated in-cell text, turns are roughly constant in size and requests are serial. The
append/summarise corpus never met eviction pressure: the declared capacity is **1,620,892 tokens**
(C54) and the longest U15 prompts are about 20k, so the append arm's advantage assumes a cache that
never evicts. Deliberate pressure exists elsewhere in the package — M4-EVICT at **1.5017x** on 283
documents (C54) and TUNED at **1.505083x** under SLRU (C59) — but neither cell replays a real agent
trace and neither re-runs the append arm under pressure, so the assumption the advice rests on is
still untested. Real agent traffic has variable turns, concurrency, retries and evictions; none of
those is in these rows.

*(GAP-TRIAGE 2026-10-23: this paragraph previously generalised the append-corpus condition to the
whole package and understated the declared capacity; C54 supersedes both, and the gap's closer is
unchanged.)*

*What would close it:* a replay of a real agent trace (the workspace has one, but it was not
used here), with concurrent sessions and a small KV budget to force eviction.

## G13. Cache accounting is the server's own report — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

`cached_tokens` is accepted as the server reports it; there is no token-level audit of which
prefix was actually reused. The 64-grid is an empirical regularity of this build, not a
documented contract, and the `(L-1)` boundary form was inferred from U9's two boundary
lengths and confirmed by U10. A server upgrade can change all of it without changing any
prompt.

*What would close it:* a server version pin in every row (the rows carry timestamps and the
config capture, but not a build hash) and a periodic re-run of U2's 44 repeats as a canary.

## G14. The hybrid policy (append to the limit, then compact) is unrun — STATUS: OPEN (stated limitation; stale prose corrected 2026-10-23)

MANUSCRIPT §10 recommends append-until-it-fits and, when it does not fit, attacking the
steady-state re-prefill rather than the break. The steady-state half is now measured at a real
32k/64k boundary: G3-LIMIT-V2 (C62) shows the bill is the lost prefix carried for the rest of the
run, not the boundary turn. What that cell does **not** test is the trigger the advice turns on —
all 18 compactions were requested at the budget's headroom, none after an actual overrun (G3's
remainder (i)) — and the **hybrid policy itself** (append until the limit, then summarise) has not
been run: G3-LIMIT-V2's arms are baseline, summarise and fork, plus pointer and `keep_last`
variants, with no append-then-compact arm.

*(GAP-TRIAGE 2026-10-23: the previous text said neither half had been tested at the limit; C62 and
MANUSCRIPT §10 rule 5 supersede that for the steady-state half. The hybrid arm remains the gap.)*

*What would close it:* the hybrid arm in the U15 harness with a context budget below the
final window size, and a measurement of what it costs against A and R.

## G15. Per-break cost variation is unexplained (residual of G1) — STATUS: OPEN (stated limitation, GAP-TRIAGE 2026-10-23)

G1 found the mean per-break cost ratio E/F = 1.038 (within measurement noise), but only 2 of the
6 break events fall within 10 % (ratios 0.80, 0.875, 0.9375, 0.9375, 1.4, 1.5), and the
post-compaction window is imbalanced between the arms (prompt delta E-F mean -165.1 tokens,
est delta mean -43.0, 81 of 81 post-compaction turns imbalanced). The mean is stable; the
per-event spread and the window imbalance are not explained by the rows.

*What would close it:* per-event prefix-diff logging or a server-side radix-tree dump, plus more
sessions to narrow the per-event variance (G1 ran 3 sessions x 2 events).

## Downgrade note — no in-cell G0 for S1/S2/TUNED (FIX-VXSTACK)

S1, S2, and TUNED contain no in-cell G0 gate. The only SGLang gate is `experiments/context-cache/cells/SGLang/u2_gate.py` (mtime 2026-10-20 18:05), which predates the protocol those cells measured. vLLM cells V1/V2/V3 do carry an in-cell battery gate. TUNED also has no in-cell G0; its result is downgraded accordingly. S1/S2/TUNED measurements therefore rest on a gate that predates their warm-retry-empty-sleep path and repeated box restarts, not on a gate run against the config they measured.

## Triage ledger (GAP-TRIAGE, 2026-10-23)

The ten sections above whose derived status is `open` were triaged against the rows and claims on
disk, not against their own prose. **Eight are stated limitations**, and they stay open because the
measurement named in "What would close it" has not been run while no claim depends on it:

- **G2** — the 438 U4 rows record an instrument error; a re-run is the only close, and none is planned.
- **G6** — no per-turn prefix-diff or radix-tree dump exists, so the re-prefill is described, not explained.
- **G7** — the append deviation's mamba-checkpoint account still lacks the pure-attention control.
- **G8** — six lengths, TTFT only, 139 of a planned 200 requests; no inter-token or end-to-end latency.
- **G9** — n = 5 per length; the n = 20 cells and the chunk-insertion trace were not run.
- **G10** — the 91.6 % identical-prompt floor is measured; repeated sampling and a graded measure were not.
- **G13** — no per-row build pin and no U2 44-repeat canary; `cached_tokens` is the server's own report.
- **G15** — the per-event spread and the 81/81 window imbalance are unexplained; more sessions were not run.

**Two carried stale prose** and are corrected in place with a dated note: **G12** (a blanket "no
eviction pressure" sentence and an understated capacity, both superseded by C54/C59) and **G14** (a
"neither half has been tested at the limit" sentence superseded by G3-LIMIT-V2/C62; the hybrid arm
itself is still unrun, which is why the gap remains open). The decisions, with the evidence ref each
one rests on, are `state/gap-triage.json`; `tests/test_gap_triage.py` re-checks that the ten ids each
carry a decision and that the corrected assertions do not return.

## G16. The cache-option search was narrow, and two rejections cite a source that does not say what they claim — STATUS: OPEN (stated limitation, FIX-G16-LEDGER 2026-10-23; raised by CACHE-AUDIT)

**Why this gap exists.** Every cache statement in this package is a statement about the options
that were *tried*, and CACHE-AUDIT asked whether those are the options the engines document as
best. They are not, and two of the package's negative results rest on a source that does not
carry the claim attributed to it. No live request was made by this unit; everything below is a
document quotation plus a count over the rows and launch records already on disk.

**What was tried (tally over `experiments/context-cache/cells/`, launch records and variant
`server_info`).** SGLang: `--page-size` (S1 = 64, S2 = 128, both against production page 1) and
`--radix-eviction-policy slru` (TUNED, one flag). vLLM: `--block-size`, `--max-model-len`,
`--gpu-memory-utilization`, `--kv-cache-dtype`, prefix caching on. Nothing else. Every vLLM
variant ran with **no** offload tier: the captured `/metrics` line in
`cells/WIN-VLLM/logs/V1-restore.json` reads `kv_offloading_backend="native",kv_offloading_size="None"`,
and the same `kv_offloading_size="None"` appears in all four captures.

**What the engines document, quoted (pinned copies under `scratch/cache-audit/docs/`).**

- SGLang eviction policies. The pin is
  `https://raw.githubusercontent.com/sgl-project/sglang/main/docs/docs/advanced_features/radix_eviction_policy.mdx`
  (6,243 bytes, sha256 `4ba2e6210d27ed1d…`). It lists **five** command-line policies — `lru`
  (default), `lfu`, `slru`, `priority`, `tlru` — and says: *"`lfu` — The prefix with the fewest
  cache hits, then the least recent. | A small set of prompts is reused far more than the rest, and
  you want those to survive bursts of one-off traffic"*; *"`tlru` — The tail of a conversation
  beyond what its next prefill needs to meet the TTFT budget ("TEL-safe" tokens) … Agentic /
  multi-turn workloads where tail TTFT matters more than raw hit rate."* `tlru` also takes the
  paper's parameters ([arXiv:2510.15152](https://arxiv.org/abs/2510.15152)) via
  `--radix-eviction-policy-config`, and `slru` takes `protected_threshold` (default 2). **The
  package measured exactly one of the five, `slru`, with its default parameter, and generalised
  to "the eviction policy":** `SERVING-BRIEF.md`'s "The SLRU eviction policy … the measurement gives no
  reason to think the policy, rather than the pressure, explains the loss" is a statement about
  *slru at default*, not about eviction policy.
- SGLang host tier (HiCache). The pin is
  `https://raw.githubusercontent.com/sgl-project/sglang/main/docs/docs/advanced_features/hicache_design.mdx`
  (22,005 bytes, sha256 `6e6d0d845539b1d6…`), which states: *"HiCache organizes GPU memory as L1,
  host memory as L2, and distributed storage as L3"* and *"Growing `--hicache-ratio` or
  `--hicache-size` only makes each instance's own private L2 larger."* `PACKAGE.md` §4 records
  "HiCache is a no-go for hybrid checkpoints … rejected on configuration, not measured to a
  number", and `SERVING-BRIEF.md` turns that into *"No unmeasured feature is recommended
  against. LMCache, HiCache and friends are absent because no cell tests them, not because they
  were measured to fail."* **Those two sentences cannot both stand:** §4 does recommend against
  it, on a source that does not settle it (see the next point).
- SGLang session protection. `session_radix_cache.mdx` (2,820 bytes, sha256
  `0b50a3e5b8b5e97d…`): *"It registers reusable KV to a session and evicts unreferenced KV before
  KV still referenced by an active session … This feature is implemented only by
  `UnifiedRadixCache`."* The live server's `metrics_cache_type` is `UnifiedRadixCache`
  (`orchestration/handoffs/M1-R.json` `evidence.live_config`), so the feature is applicable to
  this build and was never run.
- vLLM offload. **v0.27.1, the tag the box runs, does carry it**:
  `https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/config/cache.py` (sha256
  `0b603decec748713…`) defines `kv_offloading_size` — *"Size of the KV cache offloading buffer in
  GiB … When set, vLLM will enable KV cache offloading to CPU using the kv_offloading_backend"* —
  and `vllm/engine/arg_utils.py@v0.27.1` (sha256 `165f9ec6e3b067bb…`) registers
  `cache_group.add_argument("--kv-offloading-size", …)`. The 27.1 source is authoritative over
  the `latest`-branch docs for the binary on this box.

**Two rejections do not survive that check.**

1. **HiCache.** `docs/serving-options/LAUNCH-SGLANG.md:107-150` rejects HiCache for hybrid
   checkpoints with the text `ValueError: HiRadixCache only supports MHA and MLA yet`, described
   there as *"exact text from issue comments"* at `https://github.com/sgl-project/sglang/issues/12826`.
   The quoted sentence carries **no source URL of its own**, and the issue thread it cites does
   not contain the string "MHA and MLA" for the build this box runs
   (`0.0.0.dev1+g4ccff141d`, `state/config/live-server-config.json`). What *is* pinned is that the
   same server already runs `metrics_cache_type = "UnifiedRadixCache"` — the Mamba-aware tree —
   while `enable_hierarchical_cache` is `false`. So the rejection is **unverified for this
   build**, and the honest status is "not attempted", not "does not support".
2. **vLLM `--enable-mamba-shared-prefix-checkpoint`.** `docs/serving-options/LAUNCH-VLLM.md:87-93`
   records: *"Exact command: N/A — this flag does not exist in vLLM 0.27.1 … verified absent."*
   The `latest`-branch page quoted at `https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/`
   documents it as off-by-default and requiring `--prefix-match-unit` with EAGLE/MTP on the Mamba
   group, which is exactly this box's configuration. The absence was verified against the wrong
   version, and the R-VLLM survey had already read the flag on `main` — the contradiction was
   recorded and not followed up.
3. **Chunked prefix.** S3 used `--enable-chunked-prefix-cache`, but the live default is already
   `disable_chunked_prefix_cache = false`, i.e. the enabled path. A cell that sets a flag to a
   value it already has tests nothing, and `PACKAGE.md` §4's "Chunked-prefix cannot start" is a
   null result from a no-op configuration. Not re-derived here beyond the flag and default
   (which are in `state/config/live-server-config.json` and
   `experiments/context-cache/cells/WIN-SGL/logs/S3-config.json`).

**The lever the documents name for the capacity bound is the one never pulled.** G5's resident
capacity bound is `max_mamba_cache_size 64` (C54), and HiCache's L2 and the session cache both
address exactly that (capacity and eviction), which G3's remainder (iv), G12 and G14 all name as
the open need. The measured stack has `hicache_ratio 2.0`, `hicache_write_policy write_through`,
`hicache_io_backend kernel`, `hicache_mem_layout page_first`, `hicache_storage_prefetch_policy
timeout` present-but-off and `enable_lmcache false` — the whole L2/L3 tier set was never
enabled on a hybrid checkpoint, and no vLLM cell ever set `--kv-offloading-size`.

*What would close it:* (a) re-verify the HiCache hybrid rejection against the pinned build
(`0.0.0.dev1+g4ccff141d`) with a startup attempt or the build's own source, and if it starts,
one arm at `--hicache-ratio 2` on the G5 replay; (b) one `lfu` and one `tlru` arm on the M4/TUNED
pressure protocol, since TUNED's `slru` result covers one of five policies at one parameter
value; (c) one vLLM arm at `--kv-offloading-size` ≥ the GPU KV size (the docs' own condition:
*"set `cpu_bytes_to_use` larger than the aggregate GPU KV cache"*); (d) a genuinely different
chunked-prefix configuration, since S3 restated the default.

**Reading rule this gap imposes on the package:** "the pager does not change the grid" (C57/C58,
`page-size` 64 vs production 1) and "slru is indistinguishable from lru" (C59) are statements
about **one flag at a time**, and neither licenses "cache knobs do not matter". The brief's
"No measured reason to change any of it" (S19) is true only of the knobs that were turned.
