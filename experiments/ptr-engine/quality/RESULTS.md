# QUALITY-ARM — can a task finish when the answer lives in an old body?

**Unit:** QUALITY-ARM · **Server:** `occamy-1.0` on SGLang, `http://192.168.2.168:8012/v1`, `B = 64` ·
**sole writer** for the whole unit (no restart, no `/flush_cache`) · **Rows:** `quality/rows.jsonl` —
115 rows (48 request, 48 prediction, 12 rep, 4 corpus, 3 compaction), flushed **and fsynced** one row
at a time; a prediction row is written **before** each request · **Pre-registration:** `quality/PREREG.json`,
sha256 `ea717e9c737b6f3d5dc1f67df818bec72cc44c9730cbcb368feac7106cc02157`, written before the first request.

**Answer in one sentence.** Yes — the engine lets a task finish when the answer is in an old body,
because the model can pull the older body back through the index (arm A **3/3** on item `k01`, and so
does lossy destructive compaction, arm C **3/3**), while a cap-3 warm set cannot finish at all (arm B
**0/3**, every attempt refused by name with `PTR_STORE_MISS` — 33 of them — never a silent empty body);
and the cost difference between finishing by full retention and finishing after destructive compaction
is **not resolvable at 3 reps** — median **34,372 vs 34,374** billed tokens, i.e. the sign flips with the
model's own fetch choice rather than with the policy.

---

## 0. Discrimination check (non-negotiable, reported first)

Arm **D — no-body** is the same corpus, the same index, the same turn plan, the same question, with the
host never resolving a single body. It **fails 3/3**, and it fails the way a clean control fails:

| arm D, 3 reps | value |
|---|---|
| task success | **0/3** |
| bodies resolved | **0** (15 references *withheld*, none read) |
| answer, all three reps | `756741be` |
| what that string is | the first 8 hex of `@knowledge:k12@1`'s digest — echoed straight off the index line |

The offline proof was run *before* any request (`corpus.py`), and it agrees with the live control:

* index sha256 `e81ba025cfb484a8460022dedffa8cb8e7ffe09a53b365f9b84227eb105531d5`, **458 bytes**, 12 lines,
  each exactly `- @knowledge:kNN@1 <hash8> 9000`;
* the index contains no `AUD-` substring, no `lumen`, and no "audit code" phrase;
* `lumen` appears in exactly one body — `k01`; `AUD-4417` appears in exactly one body — `k01`.

**So the index is not leaking the fact, and every other arm is measuring something.** D answers *something*
(`756741be`) rather than refusing, which is itself worth recording: an index-only prompt makes the model
echo a digest rather than say "I cannot"; the fact is still absent, so the control is green.

---

## 1. The corpus and the question (fixed before the first request)

12 items, `@knowledge:k01 … k12`, 9,000 bytes each (108,000 body bytes → a 458-byte index, **r = 236×**).
Each body is deterministic institutional prose. `k01` carries the only calibration constant with a name —
`lumen` — and its audit code `AUD-4417`; the other 11 bodies carry eleven *different* codes and never the
word `lumen`.

> **Question (pre-registered, never edited).** "Each knowledge item records exactly one calibration
> constant and that constant's audit code. Naming a constant aloud is meaningful only if its own audit
> code accompanies it. Which audit code belongs to the constant named 'lumen'?"
>
> **Judgement:** exact case-sensitive match of `AUD-4417` in the final answer; raw text kept per row.

The question asks for the audit code **of the constant's own entry**, so the model cannot locate the
answer by keyword-matching a code it was handed. The fact lives at byte 162 of a 9,000-byte `k01`.

### 1.1 What the model can actually do to reach an old body

A one-shot test, recorded here because it decides whether the arms can even finish:

| probe | what was sent | result |
|---|---|---|
| **tool path (the rule state, pre-registered)** | index only + the `fetch(ref)` tool, 4 turns | **A and C finish 3/3** — see §3 |
| **inline path (exploratory; NOT used by any arm)** | the full `k01` body inline in the system message, 12-item question, one-shot | correct (`AUD-4417`) |

The inline probe exists for one reason: before trusting A's 3/3 as "the engine lets it finish", the
fact's *answerability* has to be separated from the engine. It is answerable (the model reads `AUD-4417`
out of the same bytes arm A serves). That probe used a resting-state question that was later reworded
(§6.1) and is **not** a rule state; no arm used the inline path, and its cost is not comparable to the
arms' because it sends the body as prompt instead of resolving it.

Why 12 items and not fewer: with twelve entries each holding a *different* code, an answer of
`AUD-4417` can only come from reading `k01` — it cannot be inferred from the shape of the set or from the
index. The question never names a reference, so there is no cheap route to it either; the model either
fetches `k01` or it does not, which is what arm D measures.

## 2. The turn plan (identical in every arm)

| turn | host resolves | why |
|---|---|---|
| T1 (prime) | `@knowledge:k12@1` | realistic conversation; warm set = {k12} |
| T2 | `@knowledge:k10@1` | warm set = {k12, k10} |
| T3 | `@knowledge:k08@1`, `@knowledge:k02@1` | warm set = {k08, k02} after eviction; **k01 has never been read** |
| T4 (question) | `@knowledge:k02@1` + the model may call `fetch(ref)` | the question names **no reference**: the model must choose what to fetch from the 12-line index |

In T4 the model's first fetch is therefore the interesting event. In **A and C** it is usually `k01`
first — the index tells it nothing, so it fetches the first item — and the task finishes in that single
turn. In **B** every fetch after the first three is refused, so `k01` never arrives.

## 3. The arm table

One row per arm, 3 reps each, median over reps for the continuous columns.

| arm | policy | **task success** | resolutions (host + model) | refusal | **code raised** | **billed tokens** (3 reps) | turns | re-fetch? |
|---|---|---|---|---|---|---|---|---|
| **D** `no-body` (control) | no body path at all | **0/3** | 0 + 0 (15 withheld) | — | — | 3,386 / 3,386 / 3,386 | 4/4/4 | no |
| **A** `warmpool` | every body retained | **3/3** | 15 + 10 | 0 | — | 34,390 / 34,372 / 30,652 (**34,372**) | 4/4/4 | no |
| **B** `cap-3` | last 3 bodies only | **0/3** | 15 + 0 | **33** | **`PTR_STORE_MISS`** | 27,346 / 27,860 / 27,622 (**27,622**) | 4/4/4 | no |
| **C** `destructive-compaction` | older bodies → first 200 B + marker | **3/3** | 15 + 10 | 0 | — | 32,550 / 34,374 / 49,594 (**34,374**) | 4/4/4 | no |

**Raw answers (auditable, one per rep).**

* **A**: `"I found it in k01. The constant named 'lumen' has audit code AUD-4417.\n\nAUD-4417"` ×2, and
  `"AUD-4417"`. Every rep names `k01`.
* **B**: `"I've now attempted to read all 12 knowledge items…"` / `"All items are now returning retention
  policy errors…"` / `"I'm unable to access the body of any knowledge item due to the session's retention
  policy. The pointer index only provides reference names, digests…"` — **no code, and no guess.**
* **C**: `"I found the answer in k01. The constant named 'lumen' has audit code AUD-4417."` ×2 and
  `"AUD-4417"`.
* **D**: `756741be` ×3.

### 3.1 Arm B is an honest failure, not a bug

33 refusals, **11 per rep**, and the model reports them in its own words. The engine did not return an
empty body — it raised `PTR_STORE_MISS`, and the host handed that code back to the model verbatim in the
tool result (`ERROR PTR_STORE_MISS: this session's retention policy cannot open @knowledge:k01@1…`).
That is precisely the "say so with a code" requirement, and it is the finding: **cap-3 cannot finish this
task.** No fallback was added; the arm is not rescued anywhere in `runner.py`.

### 3.2 Arm C is destructive, and the destruction is on the record

Each rep has a `compaction` row: `@knowledge:k10@1` **9,000 B → 273 B** (`lost_fact: false` — the lossy
digest happened not to be the fact-bearing body). Compaction is applied at the *same* content locator, so
the reference still resolves and the model receives a 200-byte stub instead of the body. It did not stop
the task finishing, because the answer was fetched *after* the compaction point. That is the honest
result: at these read orders, a lossy-but-addressable view is indistinguishable from full retention, and
the first rep in which the model happened to fetch five items shows why (C rep2's bill is 44 % higher —
see §4).

## 4. Billed tokens, from the law

`uncached = (P1 mod 64) + L`, avalanche (`uncached = P1 + L`) when `P1 mod 64 ∈ {0, 1}`;
`L = prompt_tokens + FRAMING` (`FRAMING = 12`), with `P1` the **measured** `prompt_tokens` of each
request (prediction row written before the request). One run bills the prime once, then the append of
each later turn. Residues and the avalanche flag are per row in `rows.jsonl`.

| arm | turn | `P1` | residue | avalanche | `L` | uncached |
|---|---|---:|---:|---|---:|---:|
| all arms | prime T1 | 2,252 (A/B/C) · 342 (D) | 10 · 20 | no · no | — | counted as the prime itself |
| A/B/C | T2 | 4,471 | 55 | no | 4,483 | 4,538 |
| A/B/C | T3 | 8,589 | 13 | no | 8,601 | 8,614 |
| A | T4 | 15,234–18,950 | 2, 6, 47 | no | +12 of `P1` | 15,248–18,986 |
| B | T4 | 11,917–12,398 | 13, 23, 46 | no | +12 of `P1` | 11,942–12,456 |
| C | T4 | 17,079–18,951 | 7, 55, **1** | **no** (request row) / **true** (rep row) | +12 of `P1` | 17,146–18,970 |
| D | T2–T4 | 652, 973, 1,319 | 12, 13, 39 | no | 664, 985, 1,331 | 676, 998, 1,370 |

**What the avalanche column actually says.** The rep rows are the record, and they are not empty: C
rep2's T4 `per_turn` entry carries `avalanche: true`, `residue: 1`, `uncached: 34,190` — that flagged turn
*is* that rep's **49,594** bill — **REFUTED as a cost, see Corrections** (`runner.py:490`/`:495`; RECORD.md C3). The request rows cannot corroborate it: their per-row `residue` column
computes `templated_prompt_tokens % 64`, which does not equal the measured `prompt_tokens % 64` in **48/48**
request rows, so `avalanche: false` there flags the templated prefix, not the billed one. Whether SGLang
avalanches at residue 1 therefore remains an extrapolation, not a confirmation (see §4.1). Had that prefix been one token
shorter it would have been a true avalanche, and a single turn would have billed `17,089 + 17,101` instead of 17,101 — near-doubling the whole rep's
**49,594** against 32,550 / 34,374 for the other two, and it would still finish. The residue tail, not the
policy, is what a quality arm has to budget for.

### 4.1 The residue-1 turn: the law's prediction is currently an extrapolation

`SPEC.md` §13 records the avalanche at residue **1** as measured only on the *vLLM* profile
(`B = 1056`); on SGLang it was measured at residue **0** (83/83 null-cache rows, and `measure/RESULTS.md`
cell C on a 384-token prefix). No SGLang request in this unit landed on residue 0, so **no avalanche is
observed here** — only predicted, for the one turn at residue 1. That turn's billing is therefore the
law applied, not the law confirmed; it is recorded as a limit rather than folded into the arm's result.

**The gap between finishing by retention and finishing by compaction:** medians **34,372 (A) vs 34,374
(C)** — a two-token difference that is noise, and whose *sign* flips between adjacent reps. The spread
inside each arm (A: 3,738 tokens; C: 17,044 tokens) is driven by how many items the model chose to fetch
and by one avalanche, not by the policy. **At 3 reps this unit cannot rank A and C on cost.** Two things
must be stated plainly:

1. A and C **both finish**; the "token gap between them" is therefore not a policy number, it is a
   fetch-choice number.
2. The bill is **arithmetic on measured `prompt_tokens`, not a server-reported cache hit.** The
   telescoping identity `sum(prompt_tokens) + 12·(R−1)` does **not** hold exactly: the measured residuals
   are A +151/+110/+106, B +117/+150/+127, C +159/+111/+17,193, D +100×3, and the identity's own next
   clause already showed it (A: 34,275 ≠ 34,390). Nor is the gap the completion of T1 + T2 + T3 carrying
   into the prefix: those completions total **6** tokens against a **17,193**-token gap for C rep2, whose
   raw prefix measures **32,401** (not 34,201) against a 49,594 bill. Nothing in this run shows the server
   actually re-billed those tokens; the law is the measured law of `LAW.md` applied to measured prefixes,
   and reconciling the bill against the endpoint is the live re-run described below.

**The load-bearing limitation, in plain words.** Per-turn `usage.prompt_tokens_details.cached_tokens` is
read at `runner.py:585-596` but never written to `rows.jsonl`, so `billed_tokens_measured` is a
recomputation at `runner.py:688`. The bill is arithmetic on measured `prompt_tokens`, not a server-reported
cache hit, and reconciling it needs a live re-run that persists that field — a parked operator decision,
not this unit's to run.

### 4.2 The law's scope, and the regime this unit applied it to (2026-10-26)

The append-cost law is not a law about conversations. `experiments/miss-law/LAW.md:206` states its scope in
one sentence: "It is a law about **one append onto an already-primed prefix**. Multi-append runs were not
swept end to end; §6.3 extrapolates." A four-turn conversation is exactly the excluded regime, and
`runner.py:23-24` — the runner's own transcription of the law — repeats that it "applies per turn, with
``P1`` the measured ``prompt_tokens`` of the turn and ``L`` the measured ``prompt_tokens + 12`` of the turn".

`PREREG.json:30` billed the whole run with it anyway:

```
"billing_law": "uncached = (P1 mod 64) + L ; avalanche if residue in {0,1}; L = prompt_tokens + 12",
```

`L` there is a single turn's prompt, and §3 of this file spends that number across the 4 turns fixed by
`PREREG.json:28-29` (`"turns_per_rep": 4,`). Two independent defects therefore void the token column. The
instrument defect: `runner.py:490` describes `L = prompt_tokens + FRAMING` as "the whole prefix passed off as
the append", and `runner.py:495` computes it exactly so — `L` is the entire resident prefix, not the appended
turn. The scope defect: even a correct `L` would price one append, under a law whose §8 refuses multi-append
runs. The billed-token figures in §3 and §4 of this file are, for that reason, neither the law's prediction
nor a measurement of it, and neither defect is repaired by re-running: a re-run reproduces the same
out-of-scope arithmetic. The instrument half is implemented only in `runner_v2.py` in this directory, which
computes a per-append `L` and has never been run against a server.

Pricing a 4-turn conversation correctly is different arithmetic, not a better `L`: a cost per append, summed
over the appends the conversation actually made, each term reconciled against the per-turn
`usage.prompt_tokens_details.cached_tokens` the server reports — the field `runner.py:585-596` reads and never
persists (see §4.1). This contradiction carries the label **C7**; `experiments/ptr-engine/RECORD.md` is the
record in which its status is tracked.

## 5. Turns, re-fetch, and what "needed a re-fetch" means here

Every arm finished its 4 turns in all 3 reps; **no arm needed a re-fetch** (no turn in which the host had
to re-resolve a body because the model could not reach one). Arm B's failure is not a re-fetch failure;
it is a terminal one — the body does not exist in that policy's warm set, and the model is told so
eleven times. The distinction matters for the paper: "the engine lets you finish" is supported by A and
C; "the engine tells you when it cannot" is supported by B's 33 codes and B's abstention.

### 5.1 Arm B's own count is lower than A's, and that is not a win

B bills 27,622 against A's 34,372 because it **fetched less and read less** — it read 4 bodies, not 5+,
and never got to the answer. A quality arm that is cheap because it fails is not cheap. The comparison a
host should make is **cost per finished task**: A and C finish at ~34.4 k billed; B has no denominator.

## 6. Deviations, disclosed

1. **A dry run predates the pre-registration as written.** The question subject (`lumen` → `AUD-4417`),
   the corpus, the arms, the judgement rule and the turn plan in `PREREG.json` were **never changed**.
   What *was* changed after a dry run: the question's preface (from "Naming one constant is meaningful
   only if its own audit code is known" to "…and that constant's audit code"), because in that state the
   model rejected the premise and **refused for the wrong reason** in every arm — a false negative that
   would have made D's control look green for the wrong cause. D was re-run after the wording fix and is
   still 0/3 with `756741be`. The pre-registration was never rewritten to say otherwise.
2. **A turn-3 distractor body** (`@knowledge:k02@1`) was added: without it, T4's host fetch of `k02`
   left `k01` still inside cap-3's 3-body window and arm B would have passed. It is a corpus/turn-plan
   detail, recorded here rather than silently absorbed, and it does not touch the question or the fact.
3. **Retention applies to the model's in-turn fetches too** (B and C evict/compact every body older than
   the last 3, including ones fetched inside T4). The laxer reading — "a body the model fetched this very
   turn survives" — was rejected because it is a rescue, and this unit's card forbids rescuing B.
4. **`chat_template_kwargs: {"enable_thinking": false}`** is sent on every request. It is a request-shape
   choice, not a content one; thinking was left on in the first pass and is not what any arm depends on.
5. **The bill excludes generating the answer itself** (the law bills appends). Stated, not hidden.

## 7. What this unit establishes, and what it does not

**Establishes.** (a) The index carries structure, not facts — proven offline and by a live control.
(b) A model *can* reach a body it never saw, through a 12-line index and one `fetch` tool, and finish the
task with the exact expected string — 3/3. (c) A retention cap that removes the bytes produces a
**named, honest refusal** (`PTR_STORE_MISS`, 33/33 attempts) and a correct abstention, never a silent
wrong answer. (d) Destructive compaction of the non-fact body does not stop the task finishing.

**Does not establish.** (a) Any ranking of A against C on cost — 3 reps, sign-unstable, dominated by
fetch choice and one avalanche. (b) That the server actually billed the modelled tokens; that needs
`/generate` reconciliation per turn. (c) Anything about a corpus where the *fact-bearing* body is the one
compacted — here it never was, and that case is exactly the one where C would be expected to fail. (d)
Anything about a policy that *drops the index line* rather than the body; this engine never did.

**Next unit.** Fix the fetch script per arm (same refs, same order) so the token column measures the
policy, and compact the fact-bearing body on purpose so C's failure mode is on the record; reconcile each
turn's bill against `/generate`'s `cached_tokens_prompt`.

---

## Corrections (2026-10-25)

Independent re-check: `orchestration/handoffs/V-QUALITY-ARM.json` (overall **partial**). Three sentences in
§4 were refuted by the rows and are corrected above. **No measured number was changed and no new figure was
introduced**; the one numeric edit is a transcription fix (34,201 → 32,401, C rep2's raw prefix).

1. `RESULTS.md:150` — "the avalanche column is empty / 48 requests, 0 avalanches" read as a measurement and
   was false as written. The rep rows record `avalanche: true`, `residue: 1`, `uncached: 34,190` for C rep2
   T4; the request rows' residue column computes `templated_prompt_tokens % 64`, which differs from the
   measured `prompt_tokens % 64` in 48/48 request rows, so those rows cannot settle an avalanche either way.
2. `RESULTS.md:174` — `sum(prompt_tokens) + 12·(R−1)` does not hold exactly: residuals A +151/+110/+106,
   B +117/+150/+127, C +159/+111/+17,193, D +100×3 — as the sentence's own `34,275 ≠ 34,390` showed.
3. `RESULTS.md:175-176` — "the difference is the completion of T1 + T2 + T3 carrying into the prefix" is
   refuted: those completions total 6 tokens against a 17,193-token gap.

**Repair trail, undisclosed at handoff (01:07-01:10).** Five files here post-date the 00:39 handoff — `probe_instrument.py`, the corrected `runner.py`, `rerun_corrected.py`, `rows-corrected.jsonl` (9 rows, arm A rep 0 only, 47-key schema) and `rerun-corrected.log` — and are the remains of the crashed BILL-REPAIR attempt: its own alignment guard stopped it (`AssertionError: per_turn[%d] bills P1=18794 but the row's own tokenizer count was 10902`, `rerun-corrected.log:16`), no arm completed, and no aggregate was written, so C4 stays OPEN and nothing may cite these files as a measurement.

4. `RESULTS.md:147` — the C/T4 avalanche cell now shows both records: `no` (request row, computed on
   the templated prefix) / `true` (rep row). A flag, not a measured number.

**Code-level defect behind the limitation.** Per-turn `usage.prompt_tokens_details.cached_tokens` is read at
`runner.py:585-596` but never written to `rows.jsonl`, so `billed_tokens_measured` is a recomputation at
`runner.py:688`. The bill is arithmetic on measured `prompt_tokens`, not a server-reported cache hit;
reconciling it requires a live re-run that persists that field — a parked operator decision, not this
unit's.

**Unchanged, and must stay so.** The discrimination result stands exactly as reported: A 3/3, B 0/3,
C 3/3, D 0/3; arm D resolves 0 of 5 withheld bodies per rep; answer `756741be`; index 458 B with its hash
taken over the in-row `index_text`.
