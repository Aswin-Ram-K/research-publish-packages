# Replay reproduces the record, not the decision

**A short note.** One task family (a typed multiple-choice decision), one corpus of 190 cases, four
model configurations, four recorded variants. Everything below describes **already-recorded data**;
no model was run, re-trained, or re-evaluated for this note, and the reader is given the files that
carry every figure.

*Author block: the author-supplied name.* The byline is **Aswin Ram Kalugasala Moorthy** — the author's
own name, supplied verbatim, with the affiliation and corresponding-author contact shown on the byline. At
drafting, no byline had been decided and this note then described the author block as an unfilled slot
for the author to fill in before submission; that was accurate then, and the superseded wording is
retained in this package's build record rather than shipped. (Corrected 2026-10-16.) See §7.

---

## Abstract

Replaying a recorded decision trace reproduces the recorded output. It does not necessarily reproduce
the **decision** the trace encodes. On a corpus of 190 decision cases answered by four model
configurations under four recorded variants (3,040 rows total), we measure how often two
configurations reason over the same record, at the same variant, and pick a **different option**.
At the reference variant V0 that happens on **476 of 1,140** model-pair-by-case comparisons —
**41.7544 %**. The instrument has a real zero: the corpus's own replication arm re-issues the same
request and returns an **identical decision on 244 of 244** non-decomposable comparisons, across both
replication pairs, with **zero** divergent. Against that control the divergence is a property of the
binding, not of noise. The four variants give 41.75 %, 47.11 %, 40.00 % and 43.33 %, so the headline
is one arm, not a four-variant average. Relabelling the options alone moves **245 of 760** decisions
(**32.2368 %**), but that pool hides the shape: one configuration moves **119 of 190 (62.63 %)** while
the other three move 15.8–26.8 %. A second record file, `l1-head-to-head.jsonl`, is **not an
independent corpus**: it covers the same 190 cases and the same two models, and reproduces the same
`picked_index` on **190 of 190** rows per model. Its 51.5789 % divergence is the same 98 disagreements
already counted in the binding table. The stimuli — the questions and the options — are **not carried by
these record files**: the records release indices and latencies, not text. The same 190 cases release
with the **companion note** (`10.5281/zenodo.23463944`), under a different neutralised tagging. A reader
can recompute every arithmetic figure here, and — by recovering the tag correspondence from the per-kind
sequence of `correct` values (§7) — can check the questions, options and hand-authored labels for any
record; neither release states that mapping as a table.

---

## 1. Introduction

A deterministic log does not make a model deterministic. If a decision trace is replayed by a
different model, or under relabelled options, the *record* of the decision is reproduced exactly while
the *decision* it encodes may not be. The distinction matters wherever a system treats a replay as a
reconstruction of what happened: a trace that rebinds faithfully can still encode a different choice.

This note quantifies that distinction on one recorded corpus. It is deliberately narrow: one task
family, 190 cases, four model configurations, four variants, no new measurement. The claim is not that
replay is unreliable in general. The claim is that **on this corpus, replaying the record reproduces
the record and diverges from the decision at a measurable, controlled rate** — and that the corpus
supplies a zero it can report, which is what makes the rate admissible.

The antecedent this note adopts is the pre-registered experiment's own: it records that arXiv
2605.20173 names the phenomenon *replay divergence* — an LLM consumer of a deterministic event log
producing different outputs under model or prompt changes (`EXP#7-replay-divergence.md:16-17`). That
citation is quoted from the pre-registration and was **not** independently fetched for this note
(§6). No literature claim beyond it is made.

### 1.1 Related work

The sentence above was accurate at drafting: no literature claim beyond the antecedent was made then. This subsection, added for review, places the note in the literature it belongs to. It makes no claim about the measured rates, and it cites only work that was verified from a primary record — the verification is recorded in the reference notes shipped with this note.

The nearest established literature is on nondeterminism in inference itself. Yuan et al. trace disagreement between repeated runs of the same model to numerical sources — the order in which floating-point reductions are accumulated and the scheduling of kernel launches — rather than to sampling, so a temperature of zero does not by itself make an execution reproducible [[CITE:yuanNondeterminism]]. That result is the mechanism behind this note's control: the corpus's own replication arm re-issues a recorded request and, on this record, returns an identical decision every time, which is what lets the divergence it does observe be attributed to the binding rather than to numerical jitter.

A parallel literature studies how much of a measured result survives a change of seed, batch or execution order. Henderson et al. show that reported gains in deep reinforcement learning can be explained by seed choice alone [[CITE:hendersonDeepRL]]; Bouthillier et al. formalise benchmark variance and recommend reporting it rather than a single point estimate [[CITE:bouthillierVariance]]. BatchPrompt makes the batch itself a treatment: packing many requests into one call changes the answers and interacts with the position of an item within the batch [[CITE:linBatchPrompt]]. This note's option-relabelling variant is in the same family — the record is fixed and only the surface form of the request moves — and its finding that one configuration is far more label-sensitive than the others is a split that the pooled rate hides.

For agents, reproducibility has largely been treated as a property of the environment and the scoring harness rather than of a single decision. AgentBench and the tool-agent-user benchmark of Yao et al. build controlled, replayable settings so that whole trajectories can be compared [[CITE:liuAgentBench]] [[CITE:yaoTauBench]]. This note is deliberately narrower and reports a per-decision rate: it measures single decisions, not trajectories, and says so.

Finally, the note is an exercise in evaluation-record integrity. Dodge et al. argue that a reported result should carry the variation behind it [[CITE:dodgeShowYourWork]]; Gebru et al. argue that the artifacts a result depends on should be documented well enough to be interpreted [[CITE:gebruDatasheets]]. This note follows both precepts in one direction and fails them in another: it releases the record files, the definitions and the analysis, and points to the companion note that releases the stimulus under a different neutralised tagging, so the arithmetic is reproducible and the meaning of a case is checkable by recovering the tag correspondence from the data (§7).

---

## 2. The records

Two JSONL files carry the evidence. Both are pinned here by size and digest; a third artifact, the
stimulus fixture is **not** in this release: the same 190 cases ship with the companion note (§7), under a different neutralised tagging.

| record | bytes | lines | sha256 (first 8) |
|---|---|---|---|
| `decision-variants.jsonl` | 1,197,797 | 3,040 | `c5ec44a7` |
| `l1-head-to-head.jsonl` | 63,238 | 380 | `6af0e0d8` |

**`decision-variants.jsonl` — the substrate.** 3,040 rows, 21 fields each. The rows are
**4 models × 190 cases × 4 variants** (V0–V3): the four configurations are `decider-0.8b`,
`decider-2b`, `decider-4b` and `laya`, and there are 190 distinct case `id`s spanning 7 `kind`
labels. The field set is stable across all rows. `variant` is the "four variants" of the title;
V1 is the option-relabelling arm, and V2/V3 are the re-issue control arm described in §3.

**`l1-head-to-head.jsonl` — a second execution, not a second corpus.** 380 rows, 8 fields each:
2 models (`laya`, `decider-0.8b`) × the same 190 cases. Its role is discussed — and limited — in §5.

### 2.1 The schema trap: `correct` is an index, not a flag

In **both** record files the column named `correct` holds the **option index** of the correct answer,
not a right/wrong boolean. Its value set is `{0, 1, 2, 3, 4}` in both files, and the first row of each
file makes this visible: `decision-variants.jsonl` line 1 carries `"correct": 1` and
`"picked_index": 1`; `l1-head-to-head.jsonl` line 1 carries `"correct": 0` with
`"picked_index": 1` — i.e. a *wrong* answer whose `correct` field is literally `0`.

The correctness axis must therefore be derived:

> **`picked_index == correct`** is the outcome boolean.

A replicator who reads `correct` as a flag will compute a meaningless accuracy — summing the field as
if it were 0/1 yields `404/380` over the whole second record file, and `202/190` on each of the two
models' own lines (`sum(r["correct"] for r in rows)`, whole-file and then inside a per-model loop). This is not a hypothetical:
the pre-registered experiment's own record says the first analysis run made exactly this misreading and
reported 0 % outcome divergence for every pair until it was corrected
(`EXP#7-replay-divergence.md:148-150`). We state the trap explicitly here because a reader who trips
over it will not be able to reproduce anything.

### 2.2 No missing rows

`error` is `null` on all 3,040 rows of `decision-variants.jsonl`, and `error_stage` is `null` on all
3,040. No row is excluded and there is no missing-data correction anywhere in the figures below.

---

## 3. What is measured

The definitions are those the pre-registered experiment fixed before its analysis ran
(`EXP#7-replay-divergence.md:48-55`), implemented literally:

1. **Control / replication.** `V0`↔`V2` and `V1`↔`V3` on non-decomposable cases; divergence means
   `picked_index` differs. A working instrument must report **zero** here.
2. **Binding divergence.** Every unordered pair of the four models, compared at the **same** variant
   V0; divergence means `picked_index` differs. Six pairs × 190 cases = **1,140 comparisons**.
3. **Prompt divergence.** Every model, `V0` vs `V1` (options relabelled, same model, same case);
   4 × 190 = **760 comparisons**.
4. **Decision stability.** The fraction of the 190 cases on which all four models pick the same option
   at V0.
5. **Outcome divergence.** `(picked_index == correct)` differs between the two rows — a separate axis,
   because two configurations can pick different options and be equally right.

**Denominators are load-bearing.** The 41.7544 % headline is out of **1,140** comparisons — six model
pairs at one variant — not out of the 3,040-row corpus. It is **not** "41.8 % across four variants";
it is one arm. The four variants' binding rates appear separately in §4.5.

Every figure in §4 was re-derived from the raw records with a script that reads only the two `.jsonl`
files (`scratch/urever2/verify_divergence.py`); the full mapping from claim to field is in
`CLAIMS.md`.

---

## 4. Results

### 4.1 Binding divergence at V0

| model pair (at V0) | comparisons | decision divergent | decision % | outcome divergent | outcome % |
|---|---|---|---|---|---|
| decider-0.8b vs decider-2b | 190 | 51 | 26.84 | 30 | 15.79 |
| decider-0.8b vs decider-4b | 190 | 69 | 36.32 | 47 | 24.74 |
| decider-0.8b vs laya | 190 | 98 | 51.58 | 61 | 32.11 |
| decider-2b vs decider-4b | 190 | 50 | 26.32 | 35 | 18.42 |
| decider-2b vs laya | 190 | 100 | 52.63 | 67 | 35.26 |
| decider-4b vs laya | 190 | 108 | 56.84 | 84 | 44.21 |
| **pooled** | **1,140** | **476** | **41.7544** | **324** | **28.4211** |

Two models reasoning over the same record choose a different option on **41.7544 %** of
model-pair-by-case comparisons. The decision axis diverges more than the outcome axis
(**41.75 %** vs **28.42 %** pooled): two configurations can pick different options and still be
equally correct, which is exactly why the two axes are reported separately rather than collapsed.
Divergence also grows as the configurations get further apart (26.3–26.8 % between the decider
siblings; 51.6–56.8 % against `laya`).

### 4.2 Prompt divergence, and the split the pool hides

| model (V0 vs V1) | comparisons | divergent | % |
|---|---|---|---|
| decider-0.8b | 190 | 51 | 26.84 |
| decider-2b | 190 | 30 | 15.79 |
| decider-4b | 190 | 45 | 23.68 |
| laya | 190 | 119 | **62.63** |
| **pooled** | **760** | **245** | **32.2368** |

Relabelling the options moves **32.2368 %** of decisions pooled. That single number overstates the
robustness of the three decider configurations: **one model moves 119 of 190 decisions (62.63 %)**
from a label change alone, while the deciders move 15.8–26.8 %. The honest statement is the split,
not the pool. Any claim that "option labels barely matter" is true of three configurations and false
of the fourth.

### 4.3 The control, and why the rate is admissible

```
V0 <-> V2, non-decomposable: 244 comparisons, 244 identical, 0 divergent
V1 <-> V3, non-decomposable: 244 comparisons, 244 identical, 0 divergent
```

The corpus contains a replication arm its authors did not build for this experiment: on
non-decomposable cases, V2 re-issues the V0 request and V3 re-issues V1. **Every one of the 244
re-issued comparisons returned an identical decision, in both pairs.** The instrument can report
zero, so the divergence rates are a property of the bindings rather than of jitter, comparison error,
or a broken instrument. This control is not decoration: the pre-registered record says its first
analysis run inverted the case filter and reported "51 % replication divergence" — a would-be finding
that the zero control caught (`EXP#7-replay-divergence.md:139-154`).

### 4.4 How much replay actually guarantees

Across the 190 cases at V0, all four configurations agree on the same option in **60 cases =
31.5789 %**. That stable set is the size of what replay promises at the decision level on this corpus.
For the other 68.4 % (130/190) of cases, at least one binding picks something different from at least one other.

### 4.5 Sensitivity across variants

The headline is one arm. Binding divergence across V0–V3, each over 1,140 comparisons:

| variant | binding divergence | outcome divergence |
|---|---|---|
| V0 | 476/1140 = 41.7544 % | 324/1140 = 28.4211 % |
| V1 | 537/1140 = 47.1053 % | 371/1140 = 32.5439 % |
| V2 | 456/1140 = 40.0000 % | 358/1140 = 31.4035 % |
| V3 | 494/1140 = 43.3333 % | 383/1140 = 33.5965 % |

The spread is **40.00–47.11 %**, a 7.11-point range (V0 sits near the low end). The direction of every
claim in this note is invariant across the four arms; the *magnitude* is definitional — it depends on
which variant is called the reference. We report the per-variant column rather than a single number so
that a reviewer can see the sensitivity instead of having to discover it.

---

## 5. The timing file is not a second corpus

`l1-head-to-head.jsonl` was proposed elsewhere as an independent cross-check
(`strategy/PAPER2_REVERIFICATION.md:149`). It is not one, and this note does not claim corroboration
from it.

| property of `l1-head-to-head.jsonl` | measured |
|---|---|
| cases | the **same 190** case `id`s as `decision-variants.jsonl` |
| models | the **same two** (`laya`, `decider-0.8b`) |
| `picked_index` vs `decision-variants.jsonl` V0 | **identical on 190/190 rows for each model** |
| disagreement pattern vs the V0 decider-0.8b-vs-laya pair | **same on 190/190 cases** |
| `ms` (timing) vs `decision-variants.jsonl` V0 | **differs on 380/380 rows** |
| `p_chosen` vs `decision-variants.jsonl` V0 | **identical on 380/380 rows** (`conf` is not a field of `l1-head-to-head.jsonl`; it exists only in `decision-variants.jsonl`) |

Its 98/190 = **51.5789 %** divergence is arithmetically the same 98 disagreements already counted as
the decider-0.8b-vs-laya pair in §4.1 — not an independent estimate of the rate. What it *is* is a
second **execution** of the same two models over the same 190 cases: the choices are byte-identical
and the timings differ on every row. That is evidence about the **instruments' repeatability**, not
evidence that the 41.75 % figure holds on a second corpus. We therefore either drop the cross-check or
report it as a timing comparison on the same disagreements; we do the latter, and nothing in §4 relies
on it.

*Correction to the re-verification record:* `strategy/PAPER2_REVERIFICATION.md:152` states that `ms`,
`p_chosen` and `conf` all differ on every row. Measured directly, **`p_chosen` is identical
on all 380 rows** and **`ms` differs on all 380 rows**; `conf` is not a field of `l1-head-to-head.jsonl` at
all, so no claim about it can be evaluated on the L1 side (it exists only in `decision-variants.jsonl`). The correction does not change the conclusion — the
file is still not independent — but the record's sentence is wrong as written.

---

## 6. Limitations

**The stimuli are not in the record files, and this remains the largest gap — now closeable by reference.** Neither record file carries a question or an
option label: the columns are model names, case `id`s, `kind` labels, small indices, probabilities,
latencies and booleans. The questions, the option texts and the hand-authored correctness labels lived only
in the fixture `evals/fixtures/reflex-decisions.ts` (145,031 bytes; 190 cases), which is not part of
either `.jsonl`; since 2026-10-19 that fixture is **not withheld**, and the companion note releases
those **same 190 cases**, with the same per-kind counts, as a neutralised fixture (`fixture-190.json`, 76897 bytes, 190 cases, sha256 `a15224ba…`) under a
different tagging (§7). A reader with the two record files and that companion fixture can
**recompute every arithmetic figure in this note**, verify the control, and — after recovering the tag
correspondence from the per-kind sequence of `correct` values (§7) — check that a case's `id` or
`kind` means what this note says it means, that the option indices refer to the options the fixture
holds, and that the `correct` index agrees with the fixture's own hand-authored label. A reader still
**cannot** read the tag mapping off any released table, and the fixture's labels remain unaudited for
defensibility (§6). Every divergence number here is still reproducible arithmetic over a
**stimulus-blind** record; what has changed is that the blindness is now liftable by the reader.
*(Superseded 2026-10-19: this bullet previously stated the stimuli were withheld outright and that the
three checks "are taken on trust unless the fixture ships"; that superseded wording is retained in §7's
dated history.)*

**The case set has no recorded sampling frame.** The 190 cases are what the fixture contains; nothing
on disk establishes that they are representative of any broader task distribution, so nothing here
generalises beyond them.

**The `correct` labels were not audited.** We verified the *schema* of `correct` (it is an index) and
used it to derive the outcome axis; we did not verify that any individual label is the defensible one.

**The analysis script named by the pre-registration was not executed.** `tools/replay/exp7.ts` exists
(8,856 bytes) but was neither read nor run for this note; every figure here comes from our own script
over the raw records. Whether `exp7.ts` implements the definition it documents is unknown to us.

**This measures a per-decision rate, not a trajectory rate.** The corpus is single-decision tasks with
2–5 options. A longer agent trajectory compounds these per-decision rates rather than averaging them,
so 41.75 % should not be read as a trajectory-level reliability figure. No trajectory was measured.

**No live re-run was performed.** The records are a measurement of the recorded record; a live re-run
would measure today's endpoint, which may differ from the recorded one. This is by design, but it means
the note reports what the record shows, not what the models do now.

**The antecedent citation was not independently fetched.** arXiv 2605.20173 is quoted from the
pre-registration's §1 and is not verified here. No literature claim rests on it beyond naming the
phenomenon.

---

## 7. Data availability

**Released.** The two record files (`decision-variants.jsonl`, 1,197,797 B / 3,040 lines /
sha256 `c5ec44a7…`; `l1-head-to-head.jsonl`, 63,238 B / 380 lines / sha256 `6af0e0d8…`), the
definitional section of the pre-registration that fixes the five measurements, and the analysis script
that re-derives every number in §4. Total released size of the two records: **1,261,035 bytes**.

**Persistent identifier: concept DOI `10.5281/zenodo.23482511`.** The released record files and the
verification tooling are published on Zenodo under that DOI, so the released artifacts carry a
persistent identifier as well as a licence statement. The **concept** DOI is cited deliberately: it
always resolves to the latest version of this deposit, whereas a version DOI dies at the next version.

**Released with the companion note.** The stimulus fixture (`evals/fixtures/reflex-decisions.ts`) —
the questions, the option texts and the
hand-authored labels — releases with the **companion note** on Zenodo, concept DOI
**`10.5281/zenodo.23463944`**; it is not copied into this package. The companion fixture is **not an
independent corpus and not a differently-sampled one**: it carries the **same 190 cases** as the
records, with the **same per-kind counts** (30/30/26/22/26/28/28), under a **different neutralised
tagging** (the companion tags its kinds `K01 K02 K03 K04 K05 K07 N10`; the records use their own kind
names). The case order within a kind is the same on both sides, and the correspondence between the two
tag sets is recoverable from the data itself: ordering each kind's cases by numeric suffix, the per-kind
sequence of `correct` values determines the mapping **uniquely** — exactly one bijection of the seven
kinds matches all seven sequences (`K01=escalation`, `K02=worker.class`, `K03=acquisition`,
`K04=topology`, `K05=capability.family`, `K07=memory.admission`, `N10=context.package`). What a
reader can therefore check, with the two record files and the companion fixture: the questions, the
options and the hand-authored labels of any record. What a reader still cannot: read the tag mapping
off any released table — neither release states it, so it must be recovered by the rule above — and
audit the fixture's labels for defensibility (§6).

**Withheld.** The definitional section ships; and the analysis script `tools/replay/exp7.ts`, which was
not executed for this note, is what remains withheld — it is not released here (8,856 bytes in the
source repository). Whether it implements the definition it documents is unknown to us (§6).

**Superseded (dated history).** Until 2026-10-19 this section described the stimulus fixture as
**Withheld**, calling that omission "the largest gap", and the section's withheld item was "the
stimulus fixture ...; and the analysis script". That wording is retained here
rather than deleted: it was accurate while no fixture was released, and the change is that the fixture
now releases with the companion note by **reference**, not by copy into this package. The item that
remains withheld is the analysis script.

**Licence.** The paper's own text is **CC BY 4.0**. The released subset's content is covered by
**CC BY 4.0**; the released artifacts are **source-available under PolyForm Noncommercial 1.0.0**, with
an **author-offered paid commercial licence** for commercial use. **The main repository stays fully
proprietary and closed**; its own `LICENSE` governs it and is not restated, copied, or resolved here.

**Author block: the author-supplied name.** The byline is the author's own name, **Aswin Ram
Kalugasala Moorthy**, supplied verbatim and name only; no affiliation, institution or contact is
invented or stated. (Corrected 2026-10-16: at drafting, no byline had been decided and this note then
described the author block as an unfilled slot for the author to complete before submission; that was
accurate then, and the superseded wording is retained in this package's build record. The author has
since supplied the name verbatim, and the record is kept.)

Full claim-by-claim sourcing is in `CLAIMS.md`; the unestablished items and what would close them are
in `GAPS.md`; the release subset and its boundary are described in `AVAILABILITY.md`.

---

## Compute and resources

**Compute and resources.** The figures reported here were re-derived from the two already-recorded data files by the analysis script; no model was trained, served or re-run for this note, and no accelerator, training wall-clock or energy measurement is claimed.

## Author contributions

**Author contributions.** This manuscript is by a single author, **Aswin Ram Kalugasala Moorthy**. The research question and the direction of the work are the author's; the author carried out and directed the work and wrote the paper, and takes responsibility for its content. No further contribution record exists and no CRediT roles are stated.

## Funding

**Funding.** This research received no external funding. No funding body, grant number or institutional support
is recorded anywhere in this workspace, and none is claimed.

## Use of AI tools

**Use of AI tools.** In October, I used large language models through DeepSeek Harness (chiefly
`deepseek-v4.1-flash`, with `step-5-preview-free` and `mimo-v2.6-flash` as subagent routes) in two ways: to
help design and implement the analysis and the experiment, and to help draft and edit this manuscript. The
research idea, the experimental design, and all editorial decisions are my own. I checked and verified all
AI-assisted output, and I take full responsibility for the entire content of this paper. The AI systems are
not authors and are not credited as contributors.

## Conflicts of Interest

**Conflicts of Interest.** The author declares no competing interests.
