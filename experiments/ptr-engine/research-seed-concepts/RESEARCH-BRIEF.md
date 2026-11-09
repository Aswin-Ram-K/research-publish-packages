# Research brief — flagship paper

**Working title.** *The bill is set by the append, not the window: how prefix caches price long
agent context, and what a context engine should do about it.*

**Status of this brief.** A plan for a paper, written from evidence on disk. Nothing here is a
result that does not exist. Every quantitative statement names its source and its status
(`MEASURED` / `RECOMPUTED` / `RECORD` / `INFERENCE` / `PROPOSED-UNTESTED`); the full mapping is
[`EVIDENCE-DOSSIER.md`](EVIDENCE-DOSSIER.md). **No request has been sent for this paper.**

---

## 1. The problem

Agent systems spend most of their prompt budget on context they have already sent. The standard
remedies are all *window* remedies: keep less, summarise, truncate, or compress. Their cost model is
implicitly "cost ∝ how much history is retained", so a design that retains less is assumed to cost
less.

The measurements on this rig say the cost model is wrong at the level where the decisions are made.
What a prefix-cached server re-bills on each turn is a function of **where the append lands** and
**how many appends there are**, and only weakly of what the append contains:

- appending `L` tokens to a primed prefix of `P1` tokens on SGLang (B = 64) re-bills
  `(P1 mod 64) + L` — residual **0** on every non-avalanche row recomputed from the 774-row file
  (218 zero-residual of 301 SGLang fit rows; the remaining non-zero residuals are all avalanche rows)
  [`EVIDENCE-DOSSIER.md` §E-01];
- the payload does not interact with the residue at all: at `P1 mod 64 = 5`, payloads of 16/32/64/128
  tokens cost 33/49/81/145 — each exactly `r + L` [§E-04];
- vLLM (B = 1056) additionally leaves one whole block uncached: `(P1 mod 1056) + 1056 + L`, exact on
  **85/86** fit rows [§E-05];
- at `P1 mod 64 ∈ {0,1}` the behaviour changes class — the entry is absent, an identical repeat
  misses, and the same 13-token append is billed the whole prefix through one usage field and one
  block plus tail through another [§E-02];
- and the cheapest remedy is not a smaller window: two tokens of padding before the append converts
  the class change into a tail [§E-07].

If that is the cost structure, then the interesting design question is not "how much context should
I keep" but "**how should I append**". A bounded, recoverable context view is an append-shaping
design: it replaces a growing transcript with a stable prefix, a bounded recent window, and
content-addressed bodies resolved on demand — which changes *when* appends happen, *how many* there
are, and *at what residue* they land. That is a testable claim, and it has never been tested here:
the one comparative that would test it is `UNFUNDED`, and the one equal-information measurement that
exists points the **other way** (pointer arm 1.8441× the equal-information baseline, because "each
resolve appends a body, so the prefix changes and does not cache") [§E-12].

**So the paper's problem is twofold, and both halves are real:** practitioners optimise the window
while the bill is set by the append; and the obvious append-shaping design, built naively, is
*more* expensive. The contribution is the cost model, the design discipline it implies, and the
evidence that separates a naive from an alignment-aware implementation.

---

## 2. The research question

**Primary (RQ).** On a live prefix-cached serving stack, is the billed cost of multi-turn agent
context determined by the amount of history retained or by the alignment and shape of each append —
and does a bounded, recoverable context design that respects that arithmetic deliver non-inferior
verified answers at lower uncached prefill work than an append-only transcript?

**Operational sub-questions** (each independently falsifiable, each with the measurement that
decides it in §7):

- **RQ1 (model).** Is the per-append cost a closed-form function of `P1 mod B`, `L`, and the engine's
  block accounting, with an exact residual, on more than one engine? *Decided by: the existing law
  (already answered for one append on two engines) plus the multi-append extension.*
- **RQ2 (class change).** Is the residue-{0,1} discontinuity real, residue-based rather than
  positional, and avoidable by a 2-token intervention whose cost is smaller than what it prevents?
  *Decided by: the existing sweep (real, residue-based) plus one intervention cell read on both
  instruments.*
- **RQ3 (design).** Does an alignment-aware bounded context view — stable prefix, bounded verbatim
  window, content-addressed bodies fetched on demand in batched, aligned appends, with explicit
  retrieval outcomes — match an append-only transcript on independently verified success while
  spending fewer uncached tokens and less time-to-verified-success at a 60-turn horizon?
  *Decided by: the five-arm comparative; **not yet measured**.*
- **RQ4 (mechanism).** When the bounded view wins or loses, is the difference attributable to the
  append arithmetic (tail, block tax, class change) rather than to prompt length? *Decided by:
  per-turn decomposition on the comparative's own rows, in the style of the manuscript's E2 identity
  (`1,268.9 = 456.2 + 34.3 + 778.4`, residual 0).*

**Non-goals.** Model quality or benchmark scores; production integration; a Rust kernel; any claim
about summariser quality (the manuscript's compaction arms run an offline stub and say so); any
wire-API design.

---

## 3. Contribution

Four contributions, in the order a reader needs them. Each is annotated with what already exists.

**C1 — A closed-form per-append cost law with an exact residual, on two engines, plus a
class change.**
`uncached = (P1 mod B) + L` (SGLang, B = 64, residual 0) and `(P1 mod B) + B + L` (vLLM, B = 1056,
residual exactly +1056 on the `+0` model); at residues 0/1 the entry is absent; the discontinuity is
residue-based, not positional (11/11 misses across six block indices, `P1 − 64` preserving the
residue). *Status: MEASURED and recomputed from the rows; not in the manuscript.* The honest
qualification is part of the contribution: the **billed magnitude** of the class change is
instrument-dependent and the record marks the 5.2× between two read fields **UNDECIDABLE** — the
paper prints the class change and the field semantics, not a magnitude.

**C2 — The design consequence: the append is the unit, and it is quantised per engine.**
Never let the primed length land on residue 0/1; otherwise accept `P1 mod B` as an unavoidable
per-append tax and **batch** fetches (K appends ≈ `K·B/2`; merging two saves ~32 tokens on SGLang,
~1,584 on vLLM); size payloads by body tokens, not by append count (one 4,000-token fetch beats
eight 500-token fetches by ≈`7·B/2`). *Status: `INFERENCE` from C1 — arithmetic, not an independently
measured intervention.* The paper states it as a rule with its derivation and prices it honestly; the
one measured padding result on the record (§8a/C64a: a 64-token page-recovery pad **costs** +20.8429
uncached tokens/turn) is a *different pad* and the paper draws that boundary explicitly.

**C3 — A reproducible research prototype with a measured capability and refusal profile.**
An index-plus-bodies engine: a 12-line, 447 B index in front of 30,000 B of bodies (67.1141× **body
bytes over index bytes** — not tokens, not cost); deterministic (index sha256 `e08700c9…9bd2`
across 2 processes and 2 roots); seven named negative-control codes; and a pre-registered quality
arm in which a model finishes an exact-fact lookup through one `fetch` (**3/3**), a retention cap
that deletes the bytes yields **33/33 named refusals and zero silent wrong answers** (`PTR_STORE_MISS`),
destructive compaction of a non-fact body does not stop the task (**3/3**), and a **no-body control
scores 0/3** while echoing an index digest — proof the index carries structure and not the fact.
*Status: MEASURED.* The arm's token column is **refuted** and is not used [§E-11].

**C4 — The measurement discipline that makes C1–C3 checkable, and the reason the comparative is
still open.**
A red-before-green control regime (identical-repeat control reads 99.3 %; cold control reads null on
both requests; 8/8 fresh nonces miss), a stamp-computed exclusion rule, replicate identity, activation
gating, and a non-results vocabulary (`UNDEFINED`, `UNAVAILABLE`, `NOT_OBSERVED`, `INVALID-INSTRUMENT`,
`UNFUNDED`). *Status: MEASURED as practice; the case series itself belongs to the companion methods
paper* ([`SECOND-PAPER-BRIEF.md`](SECOND-PAPER-BRIEF.md)) — C4 here is the discipline, not the
taxonomy.

**The unifying contribution, in one sentence a reviewer can test:** context cost in a cached serving
stack is a function of append arithmetic (residue, block tax, append count), so the correct object of
context design is the append schedule, and a bounded recoverable view is worth building only insofar
as it improves that schedule rather than merely shortening the prompt.

---

## 4. What this paper must not claim (boundaries against published and in-progress work)

| Material | Owner | Rule for this paper |
|---|---|---|
| Renderer equivalence, fan-out placement (C53/C55–C57), compaction lossiness, the 2×2 engine/model result (C63), boundary compaction (C62), padding costs (C64a), repeat-hit grid (C40/C41) | `papers/context-cache/` (in progress, package-verified today: 69 claims mapped 1:1) | cite; never re-derive; never present as new |
| encoder-crossover-190 / replay-record-not-decision / gated-read-batching | filed 2026-10-19 (Zenodo + TMLR ids in `strategy/SUBMISSION_RECORD.md`) | related work only; no filing may assert this work was never published |
| BRCV design and its protocol | `research/next-candidates/consonance-bounded-context-{report,evaluation}.md` (both PASS, 0 live calls) | F uses the protocol's arms and void conditions; F may not describe BRCV as validated |
| Instrument-failure case series | `SECOND-PAPER-BRIEF.md` | F may state that its measurements were gated by that regime; F may not carry the taxonomy as a contribution |

**Naming.** F's own vocabulary: *append arithmetic*, *residue*, *block tax*, *class change*,
*alignment-aware append planner*, *bounded recoverable view*. Avoid "pointer engine" as a headline
term: the record shows the fan-out win is a placement discipline with no pointer machinery at all
(manuscript abstract), so pointer-ness is not the contribution.

---

## 5. Baselines and the prototype

### 5.1 Arms (adopted from the prospective protocol, §6 — design given, not invented here)

| arm | definition | requests/turn | role |
|---|---|---:|---|
| **A** `full-transcript` | append-only, FIFO at the declared wall | 1 | baseline (cannot falsify itself) |
| **B** `transcript-compact` | digest at cap, recent 4 turns raw | 1 + digests | the incumbent remedy |
| **C** `masking-no-fetch` | old tool outputs replaced by pointer markers, no external fetch | 1 | isolates masking from fetching |
| **D** `bounded-recoverable` | stable prefix, bounded verbatim window, pointer table, on-demand `fetch`, checkpoint only on forecast | **2** (fetch + answer) | the proposed design |
| **E** `oracle-evidence` | same prompt budget as D, needed evidence injected | 1 | upper-bound diagnostic, not deployable |
| **C0F** | equal-information control: the same evidence, laid out without pointers | 1 | **the adversarial baseline that already beat the pointer form 1.8441×** |

D's per-turn request shape is the only place that shape is grounded: `BOUNDARY-PREREG.md`'s
`R-pointer` arm prices "2 requests/turn (fetch + answer)". Any arm that changes that shape changes
the request arithmetic and must be re-priced before it is run.

### 5.2 The prototype (what is built, what is extended)

**Exists and is reproducible today** (`experiments/ptr-engine/`): a Python package (no third-party
dependency) that compiles a turn's material into a 12-line index plus bodies in a content-addressed
store; one `fetch` tool for resolution; a hit ledger that freezes the law's conclusion per turn;
7 named negative-control codes; a warmpool placement refusal (`PTR_WARMPOOL_INSIDE_REPO`); a
pre-registered quality arm. Size, dated: **10 modules / 3,653 lines**, **13 test files / 2,248 lines**
(measured 2026-10-26; the older 1,896/1,222 figure is frozen prose and must not be quoted as current).
Test counts are per branch (95 → 100 one tree; 153, 171, 108 concurrent branches) — quote the branch,
never "the engine's tests".

**Extension for this paper — minimal, offline first, no wire API:**

1. **Alignment-aware append planner.** Before each append, compute `P1 mod B`; if it is 0 or 1, insert
   a 2-token pad (1 if residue 1) *before* the append; else leave it alone. Pure function, unit-tested
   offline against the law, deterministic.
2. **Fetch batching by body tokens.** Coalesce pending resolutions into one append until a body-token
   budget is reached; record `appends_planned`, `appends_emitted`, `residue_at_append`,
   `predicted_uncached`, `observed_uncached` per turn.
3. **Retrieval outcome vocabulary** on the run row: `OK` / `NOT_FOUND` / `STALE_OR_REVOKED` /
   `SCOPE_UNGRANTED`, plus `masked_entry{ref, since_turn}` — so abstention is expressible.
4. **Deterministic resume**: the index is a pure function of (bodies, order, pad policy); a resume
   from disk must reproduce the digest, or the run is `INVALID-INSTRUMENT`.

**Not in scope:** production integration, a Rust kernel, an omp build, a new wire schema, a
summariser model (the manuscript's arms use an offline stub and this paper inherits that disclosure).

---

## 6. Evidence already available

| # | evidence | value | status | where |
|---|---|---|---|---|
| 1 | tail law, SGLang | residual 0 on every non-avalanche row (218/301 fit rows zero; 186/186 in the residue sweep) | MEASURED + RECOMPUTED | `experiments/miss-law/LAW.md` §3; `rows.jsonl` |
| 2 | class change | 6/6 misses at residues 0/1; 22/22 null `cached_tokens` recomputed; identical repeat also misses | MEASURED | §E-02 |
| 3 | residue not position | 11/11 across six block indices; `P1 − 64` keeps the residue | MEASURED | §E-03 |
| 4 | payload independence | 33/49/81/145 at `r = 5`; 8,140 / 8,204 at `r = 0` | MEASURED | §E-04 |
| 5 | vLLM `+B` | 85/86 exact; one known −1056 row; block 1056 identified against 1,088 / 2,096 | MEASURED | §E-05 |
| 6 | controls both ways | 99.3 % on a warm repeat; null on a broken prefix; 8/8 fresh nonces | MEASURED | §E-06 |
| 7 | rival explanation refuted | boundary ≤ 378 tokens = ≤ 3.7 % of a 10,244-token swing; warm 57/60 rows | MEASURED | §E-08 |
| 8 | prototype capability | 3/3 exact-fact retrieval through one `fetch`; index leak-proof (no `AUD-`, no `lumen`) | MEASURED | §E-10 |
| 9 | refusal discipline | 33/33 `PTR_STORE_MISS`, 0 silent empties; no-body control 0/3 echoing a digest | MEASURED | §E-10 |
| 10 | equal-information baseline | C0F 1,911 vs R 3,524 ⇒ 1.8441× — **against** the naive design | MEASURED | §E-12 |
| 11 | multi-turn cost facts (cited) | E1 +4,774.25 [193.5, 4,868.25]; E2 1,268.9 = 456.2 + 34.3 + 778.4; C62 +134.6…+747.2; C64a +20.8429 | MEASURED, owned by the manuscript | §E-13 |
| 12 | the comparative is unmeasured | grid `not_adjudicable` (n_eff 26.1356 < 60; p95 refused at n = 48; 288 rows → 96) | MEASURED (failure) | §E-14 |

---

## 7. Claims that require new validation

Each row names the claim, the measurement that decides it, and the arm/cell that produces it. None
of these may appear in a submission as a finding until its measurement exists.

| # | claim to be tested | measurement | where it comes from | est. requests |
|---:|---|---|---|---:|
| V1 | the class change is avoidable by a 2-token pad, priced on both instruments | prime `P1 = 8000` → identical resend → three appends, read on `usage.prompt_tokens_details` **and** `/generate meta_info.cached_tokens` | the decisive cell named in `N1-residue-law.md` "What it would take to finish" | **≈9** |
| V2 | the law extends from one append to a short multi-append run | 2–3 point multi-append sweep at fixed residues | `LAW.md` §8 scope limit | tens (unscheduled) |
| V3 | `+B` on vLLM is not a counter artefact | independent re-derivation from a second server-side quantity or a timing instrument | kill criterion (c) in `N1-residue-law.md` | 0 (offline from existing rows) or a small re-probe |
| V4 | the quality path can say yes and no | grader/fixture fix passing a red→green control: known-good log passes; wrong-value fails on value; missing-fact fails distinguishably; same log scores identically twice; tampered fixture exits 2 | protocol §3.1; `QUALITY-POSITIVE-CONTROL.md` | **0** (offline) |
| V5 | ≥12 decidable checkpoints exist and all are gradeable | fixture audit + `grade_v5` coverage of 8/12 → 12/12 | `docs/CHECKPOINT-COVERAGE.md` | **0** |
| V6 | the bounded view is non-inferior on verified success **and** cheaper in uncached work / time-to-verified-success at 60 turns | five paired arms, 3 reps, paired task-level differences | protocol §6 | **7,560** (⇒ `UNFUNDED` at 1,729) |
| V7 | the append arithmetic explains the comparative's per-turn difference | per-turn decomposition on the comparative's rows (tail / block tax / class change / re-prefill), residual 0 | manuscript E2 method | 0 (analysis of V6's rows) |
| V8 | an instrument pilot can prove activation before a comparative is funded | 5 arms × 30 turns × 1 task × 1 rep; controls fire red; treatments activate | protocol §6.3 pilot | **≈185** |

**Ledger arithmetic, labelled as arithmetic.** Remaining at the recorded snapshot: **1,729** of
4,320 (2026-10-28). V1+V4+V5 are ≈9 requests and mostly offline; V8 is ≈185; V6 is 7,560 = **4.37×**
the remaining ledger. Any figure here is protocol arithmetic, not a quote for a run, and the ledger
must be reconciled before the first call.

---

## 8. Limitations (each one belongs in the paper's own text)

1. **One endpoint pair, one model pair, one seed.** SGLang `occamy-1.0` (`:8012`) and vLLM
   `qwen3.5-9b` (`:8014`); the manuscript's results are likewise one seed.
2. **The law's scope is one append onto a primed prefix.** Multi-append runs were never swept end to
   end; §6.3 of `LAW.md` extrapolates. The paper must say so wherever it applies the law to a
   conversation.
3. **The class change's mechanism is unexplained.** It is reported as measured. Do not invent a
   radix-tree or page-table account.
4. **The class change's billed magnitude is instrument-dependent** and the 5.2× between two read
   fields is undecidable on the rows.
5. **vLLM's numbers rest on one server-side counter** (both cache counters count tokens on this
   build), so `+B` wants independent re-derivation.
6. **The prototype's quality evidence is capability, not non-inferiority.** 12 items, 4 turns, one
   model; no multi-hop class; no stale/revoked class; the fact-bearing body was never the compacted one.
7. **The comparative is unmeasured, and the one equal-information measurement points against the
   naive design.** A paper that omits this is misrepresenting its own evidence.
8. **Tail statistics are unavailable at the current n.** `min_n_for(0.95) = 60`; p95 was refused at
   n = 48; gen-6's n_eff was 26.1356. No latency-tail claim without a separately budgeted run.
9. **The engine's own size and test counts are branch-specific and dated.** Quote with date and branch.
10. **The quality arm's token column is refuted**; the corrected runner aborted on its own alignment
    guard (`quality/rerun-corrected.log:16`), leaving 9 rows of arm A rep 0 and no corrected results.

---

## 9. Failure conditions (kill criteria, stated before the work)

| # | condition | consequence |
|---|---|---|
| K1 | the class change does not reproduce on a second build or a freshly started server | the law survives as a tail-cost model; the headline goes; reframe as a note |
| K2 | both instruments turn out to read the same counter with different null handling | the C1 dispute becomes a field-semantics footnote; the paper shrinks materially |
| K3 | `+B` fails independent re-derivation | drop the 33× ratio rather than report it second-hand |
| K4 | the paper cannot be written without asserting a mechanism for the class change | do not write it |
| K5 | V4/V5 fail — the grader cannot be made to pass a contract-following log, or fewer than 12 decidable checkpoints exist | **every quality arm, including D's, is void before its first call**; the paper is a measurement + design paper with the comparative named as future work |
| K6 | V6 fires its falsifier — D is not non-inferior on verified success, or not lower in uncached work / time-to-verified-success at 60 turns | the bounded view is **not supported**; publish the negative result, do not narrow the claim |
| K7 | D answers from parametric memory without a retrieval event, or an abstention is scored as success | the cell is `INVALID-INSTRUMENT`; no result from that arm |
| K8 | the bounded view "wins" only by making the prompt shorter (the gain vanishes when measured as uncached work) | "bounded working memory" is not an economic win at these lengths; restate the premise |
| K9 | the ledger cannot be reconciled and the arithmetic shown | budget is **unknown**; zero requests are sent |

---

## 10. Positioning and venue

**Nearest neighbours the paper must place itself against:** prefix-caching systems work in the
serving engines this paper runs (SGLang, vLLM) and their block/radix accounting; agent context
management (compaction, summarisation, truncation); retrieval-structured or pointer-based context;
KV-eviction and memory-bound long-context serving. The manuscript's §10a already maps these four
areas; F reuses that map and adds the append-arithmetic framing rather than re-surveying.

**Venue.** MLSys, NSDI, or a serving/systems measurement track; strong as a full paper **only with
V6**; without V6 it is a strong short paper (law + prototype capability + design rule) whose central
comparative is explicitly open.

**Reader value.** Every inference-engine team and agent-runner author is one padding statement away
from the class change, and one batching decision away from paying `K·B/2` instead of `B/2`. The
design rule is a few lines in a request builder.

---

## 11. Abstract draft (nothing in it is a claim about unmeasured behaviour)

> Prefix caching is sold as reuse, but what a multi-turn agent actually re-pays is set by arithmetic
> nobody instruments. Sweeping the primed length of a live SGLang endpoint across a full 64-token
> block at fixed prompt content, we measure `uncached = (P1 mod 64) + L` with residual exactly zero on
> every non-avalanche row, and payload independence at every residue: what an append contains is
> nearly free, where it lands is not. At `P1 mod 64 ∈ {0,1}` the behaviour changes class — an append
> that adds 13 tokens is charged the whole prefix through one usage field and one block plus tail
> through another, and the identical repeat misses, so this is not rounding. The discontinuity is
> residue-based rather than positional: 11 of 11 misses across six block indices, and a prefix 64
> tokens shorter misses identically. The same append on vLLM, whose resolved block is 1,056, pays one
> extra block on 85 of 86 rows — a per-engine quantisation, not a universal tax. We then ask what a
> context engine should do about it. A bounded, recoverable context view — a stable prefix, a bounded
> verbatim window, and content-addressed bodies resolved on demand — is an append-shaping design, and
> built naively it is *more* expensive at equal information (1.8441× the equal-information baseline,
> because each resolution appends a body). We report the prototype's measured capability (a model
> finishing an exact-fact lookup through one fetch, 3/3), its refusal discipline (33/33 named store
> misses, zero silent wrong answers) and its discrimination control (a no-body arm scores 0/3), and we
> state precisely which comparative remains unmeasured, why the instrument could not adjudicate it,
> and what it would cost to settle.

**Word budget note.** The abstract's last clause is deliberate: a paper that hides the unmeasured
comparative will be caught in the first review round.
