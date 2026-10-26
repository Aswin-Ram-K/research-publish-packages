# GAPS.md — what a reviewer would still want, and what this draft could not establish

**Purpose.** Things the manuscript does not claim, cannot claim from the source material, or claims only in a
weakened form. Nothing here is a number: where a wanted number does not exist, the gap is written down instead
of estimated. Gaps are grouped by who they block.

---

## 1. Gaps in the measurement itself

### G-01 · The "10×" completion-token sentence in the source is unit-sloppy
`GATED_READ_2026.md:160-162` says bs90 × `minimal` costs "1.69 M completion tokens (10× the total of
bs1-minimal)". Measured from the raw rows: bs90-minimal completion = **1,690,920**; bs1-minimal *completion*
= **190,699** (ratio 8.9×); bs1-minimal *total* = 821,909 (ratio 2.1×). Neither reading gives exactly 10×; the
sentence is approximately true of the completion-token comparison and false of the total. The manuscript
therefore says "8.9× the completion tokens" (corrected from "ten times" in a later correction pass) and carries the recomputed ratio here rather than repeating
the source's "10× the total". **A reviewer should not cite the source's sentence without this correction.**

### G-02 · The shipped summary cannot corroborate two of the three R2 token figures
`gated-read-summary.json` records `gate.gate1_none.prompt_tok_total = 631210` and
`gate.gate1_minimal.prompt_tok_total = 631210`, but leaves `prompt_tok_total = null` for `gate16_none` and
`gate90_none`. The bs16 (269,614) and bs90 (261,090) prompt-token totals in the manuscript were re-derived
from the raw per-row `ptok` values. They match the run report's rounded 270 K and 261 K, but **a reproducer
working from the summary alone finds two nulls where the paper quotes numbers.** This is a harness gap the
source run did not catch, and it is arguably the most important reproducibility wart in the package.

### G-03 · No significance test, and no pre-registered non-inferiority margin
The batching comparison has 1,800 pairs per configuration, which is enough for the differences reported to be
non-trivial, but **no null hypothesis is tested and no margin was pre-registered**. "Within ±0.01" is a
tolerance chosen by this draft, and the source's own later design notes propose a δ = 10-point
non-inferiority margin for a *different* (end-to-end) comparison (`GATED_READ_2026.md:312-317`). A reviewer
wanting "no measurable degradation" as a statistical statement would need a pre-registered margin, a
per-task or bootstrap CI, and a paired test. **None exists on disk.**

### G-04 · Batch-size granularity is coarse
Only bs ∈ {1, 16, 90} were run. There is no sweep, so the shape of the F1-vs-batch-size curve between 1 and 16,
or above 90, is unknown. The claim of "no measurable degradation at 16 and 90" cannot be extended to "flat
across batch sizes".

### G-05 · The exact batching template is not in the public material
The run report states that 16 or 90 decisions are packed into one request with indices and answered as
per-item JSON, and that unparsed verdicts are counted (`GATED_READ_2026.md:110-113`, `:154-158`). It does
**not** publish the prompt template, the delimiter/index scheme, or the parsing rules. Those are
implementation and are withheld by design (see G-09). A reproducer can reproduce the *protocol description*
but not the exact call.

### G-06 · Preview depth is a live variable, not a frozen design
The gate's input changed during design: a 500-character header rejected gold files whose answer sat at line
153, and the structure outline was added for that reason (`GATED_READ_2026.md:264-266`). So the R1 protocol as
finally run was not fully pre-registered before the first gate calls, and the measured F1 is a property of
this particular preview, not of "header and structure" in general.

### G-07 · Aggregate-only results
Every gate claim is aggregate over 1,800 pairs. There is **no per-task or per-file breakdown**, no analysis of
which task types the gate fails on, and no per-file false-negative analysis. A reviewer wanting to know
whether the gate fails on a *kind* of file (large files, code vs documentation, answers deep in the file) will
not find it here. The per-row data exists (`gated-read-rows.jsonl` carries `task`, `tag`, `pred`, `gold`,
`ptok`, `ctok`, `ms`), so this is a tractable extension, not a missing experiment.

### G-08 · Operating point is not pinned, only F1
The three `effort=none` configurations admit very different numbers of pairs (73 / 268 / 146 out of 1,800)
at nearly equal F1 (0.218 / 0.227 / 0.211). The manuscript reports this (Section 4.1) but cannot say which
operating point a deployment should use, because the run has no downstream task-success measurement to price
a false negative against a false positive.

### G-09 · One decision model; the model-vs-task question is open
Only `deepseek-v4-flash` was used as the decision model. The source identifies a cross-model check as a
designed-but-unrun next step (`GATED_READ_2026.md:330-334`). **A 0.320 F1 may be a property of this model, not
of the task.** The manuscript says so explicitly in Sections 5 and 6; it cannot resolve it.

### G-10 · One corpus, one task family
90 files, one repository, one task shape (extract a specific value from a named file). The task family is
stated in the source (`GATED_READ_2026.md:184-185`, `:283`). Nothing here generalises to summarisation,
overview, or structure questions — and the source's own round-2 design proposes exactly those shapes as the
missing heterogeneity (`:282-291`).

### G-11 · Gold is byte-containment, which is sufficient but not necessary for relevance
`gold(t, f)` holds iff *f*'s bytes contain *t*'s answer, recomputed each run (`GATED_READ_2026.md:64-65`).
This removes label noise but means a genuinely useful file that does not contain the literal answer scores as
non-gold, understating precision and distorting recall. The manuscript flags this; it cannot correct it,
because no alternative label exists on disk.

### G-12 · Base-rate performance is not usable
At a 6.7 % gold rate, an always-`false` gate scores 0.933 accuracy (`GATED_READ_2026.md:134-135`). Any
reviewer-facing claim must use precision/recall/F1; accuracy is reported in the manuscript only because it is
in the source table, with the caveat attached. No balanced-sample or AUC-style evaluation exists.

### G-25 · The gold labels are **stored**, not reproducible from the shipped corpus

`MANUSCRIPT.md` §3.2 states that the harness "recomputes gold from the bytes on every run rather than
trusting a stored label". **The raw record does not support that.** Re-deriving the gold set from corpus
content under the rule the fixture states ("file contains the answer substring; harness dir excluded")
gives **127 gold pairs in the pinned snapshot tree and 130 in the live tree, against 120 stored** —
stored-only 12 (pinned) / 14 (live), recomputed-only 19 (pinned) / 24 (live). **10 of the 12 stored-only
pairs are a single file, `AGENTS.md`.** No harness or fixture script that reproduces the stored `gold`
field exists on disk, and `tasks.json` lists 90 paths with no hashes, so the fixture is not pinned by
digest.

**Consequence — a validity limitation, not a bookkeeping one.** The **120-pair gold count**, the
**6.67 % base rate** (120/1,800), and **every precision, recall, F1 and accuracy figure in this paper** are
obtained from *recorded verdicts*, not reproduced from the fixture. The batching comparison itself is not
endangered — all five configurations share the same stored labels — but a reader cannot rebuild the
labels, and the numbers describe label-consistent behaviour rather than an independently reproducible
fixture. Two readings are possible and neither can be separated from the shipped material: the harness
applied a labelling rule the note does not capture, or the corpus files drifted between the 2026-09-30 run
and the Oct-8 snapshot.

*Recorded 2026-10-15 by UFIXGR7 from the raw-record re-verification (`strategy/GATED_READ_REVERIFY.md`
§4); the re-derived counts and the `AGENTS.md` concentration are that unit's measurements.*

---

## 2. Scope that was dropped, and why (stated so it is not read as an omission)

### G-13 · The end-to-end / staged-extraction arm (source R5) is entirely out of scope
The same run measured a six-arm end-to-end comparison (staged shortlist → routed extraction → reasoner) with
accuracy, context cost and injection-exposure columns, n = 20 per arm. **This manuscript reports none of
those numbers.** Two reasons, both load-bearing:

1. **Power.** With n = 20 per arm, the differences among the top four arms are not separable — the source
   records sign tests at p ≥ 0.219, i.e. coin flips (`GATED_READ_2026.md:313`).
2. **Disclosure.** The staged-extraction implementation is not part of the design this paper publishes, and
   deriving its numbers here would drag that implementation into a paper whose subject is the gate and its
   batching.

**Consequence:** this paper makes **no** claim about downstream task accuracy, context-cost reduction, or
prompt-injection exposure. A reader who wants those must wait for a separate, properly powered write-up.
`ULEAD1`'s lead package independently scoped this arm out as too weak to lead.

### G-14 · The staged-shortlist (source R3) and router (source R4) arms are out of scope
Both were measured in the same run (`GATED_READ_2026.md:165-190`; summary fields `stage.recall_at_5 = 0.2917`,
`stage.tasks_with_any_gold = 17`, `router.method_dist = {"grep": 120}`). They are cited nowhere in this
manuscript except as "measured but out of scope", because the paper's claim is about the *gate*, and the
router's collapse to one method is a separate finding about a different component.

### G-15 · Round-2 designs are designed and not run
`GATED_READ_2026.md:277-338` contains five round-2 experiments (heterogeneous workload, single-payload
injection, gate-input ablation, power, engineering the exposure result). **None was executed.** The
manuscript does not report them as results; where it mentions them it is as open work.

---

## 3. Disclosure abstractions applied to this package

The author's posture is *publish the design, keep the implementation*. The following source material was
**abstracted to the finding** or removed, and the abstraction is recorded here so a reviewer can see the seam.

| # | What the source carries | What the manuscript does | Why |
|---|---|---|---|
| G-16 | A named internal artefact and an internal decision identifier at `GATED_READ_2026.md:327`, describing conversion of the measurement into that artefact | Sentence **excised**. The architectural idea is not needed for either R1 or R2. | This is the single gate-hit line in the run report; the claim contains no reference to it. |
| G-17 | Internal decision IDs (`D-038`, `D-047`, `D-048`) and `M`-numbered mistake classes (`MISTAKES-A2`, `M10`, `M13`) | **Removed.** Where the underlying observation is needed, it is stated as an observation ("effort selects a different classifier, not a cheaper one"; "a check that cannot detect its own case"). | Internal taxonomy identifiers are not part of the published design and assume the internal corpus. |
| G-18 | The staged-extraction / ledger / replay mechanism (round-2 T5/T7: per-line provenance, state transitions, byte-identical replay) | **Removed**, along with the arm that measured it (G-13). | Implementation mechanism, not design; and the arm is underpowered. |
| G-19 | Corpus file paths (they appear in the row metadata and in the fixture) | **Not named.** The manuscript never names a corpus file; the one worked smoke-test example (`GATED_READ_2026.md:138-140`) is reported as behaviour without the path. | The measured claims are invariant under renaming; naming files would carry corpus inventory into the package for no analytical gain. |
| G-20 | The decision-model and reasoner model identifiers | **Retained** (`deepseek-v4-flash`; the reasoner is not central). | Model identity is part of the measured setup; without it the numbers are not interpretable. |

**Residual risk:** if the author considers the corpus *file inventory* itself sensitive rather than merely the
code, then G-19 is insufficient and the package needs the mechanical rename described in `ULEAD1`'s manifest
(`tag`/`file` → `f001…f0NN` with a withheld key) before release. The authors did not perform that rename — it
is a packaging step, and the source rows were not written to (target is read-only). **Flagged, not actioned.**

---

## 4. What a reviewer would ask for, ranked by how much it would change the paper

1. **A second decision model** at bs1/bs16/bs90, `effort=none` (source's T6). This separates "the task is
   hard for header+structure gating" from "this model is bad at it", and it is the single largest open
   question. *(Cheap; designed but not run.)*
2. **A gate-input ablation** — header vs header+outline vs header+outline+grep-snippets (source's T3). This
   would test the source's own hypothesis that recall is preview-bound, and would decide whether the veto
   survives as a component at all. *(Source estimates ~10,800 cheap calls; not run.)*
3. **A pre-registered non-inferiority test** with a margin and a paired per-task analysis for the batching
   delta (closes G-03).
4. **Per-task / per-file breakdown** of the gate's errors from the existing rows (closes G-07; no new
   measurement needed).
5. **A batch-size sweep** to establish the shape of the curve rather than two points (closes G-04).
6. **A second request shape** (overview/summarise) to test whether the batching result is specific to
   value-extraction (source's T2); this is also what would give the *router* a real choice, but that is a
   different paper.

---

## 5. What this draft explicitly does NOT establish

- That batching is free in general. Only that it did not measurably degrade decision quality **on this task,
  this corpus, this model, at `effort=none`**.
- That the gate is useful. Best F1 0.320; best precision 0.418 at recall 0.233.
- That the gate's weakness is intrinsic to the design rather than to the model or the preview.
- That any downstream task accuracy is preserved, reduced, or improved by gating (arm dropped, G-13).
- That the gate reduces prompt-injection exposure (arm dropped, G-13).
- Any cost or latency claim about a full agent, as opposed to the decision layer measured here. The paper's
  cost claims are about **gate calls and gate prompt tokens**, nothing else.
- Novelty in the strong sense. The "no prior art for per-read relevance gating" statement is a **searched
  absence** over a 13-scaffold taxonomy, expressly `[INFERENCE]` in the source
  (`GATED_READ_PROVENANCE.md:250`), not a systematic review.

---

## 6. Gaps the authors hit in producing this package

| # | Gap | Effect on the deliverable |
|---|---|---|
| G-21 | `papers/gated-read-batching/` was created by the authors; there was no prior manuscript to review, only the run report. | Sections 1, 2, 5, 6 and 7 are newly authored reasoning, not edited source text. They contain no new numbers, but their framing is the authors', and a verifier should test the framing separately from the numbers. |
| G-22 | No web-search API key was available (`web_search` failed); verification used `local_web_search` (SearXNG) only. | Two load-bearing references were re-verified (Tier A in `REFS.md`); the remaining eleven rest on the source provenance's recorded fetches. Re-fetching all eleven is the obvious verifier action. |
| G-23 | `data/key.json` / the anonymising rename described in `ULEAD1`'s manifest was **not** performed. *(Original wording kept as dated history — this gap is now **CLOSED**.)* | **Closed 2026-10-19 (pass 3).** The rename the release needed was performed, at equal length. The manuscript named no corpus file and was already clean on its own; the row-level package was not. Every occurrence of the target project's own name in `data/gated-read-rows.jsonl` — 436 occurrences on 224 lines, the two corpus paths it records in `tag`, `file`, `staged[]`, `hit[]` and `paths[]` — and the single prose occurrence at `results/GATED_READ_2026.md:327` are replaced by a neutral token of the same length (10 characters), so byte and line counts are unchanged (2,267,742 B / 9,260 lines; report 23,591 B / 340 lines), the shipped checker still reports 49/49 with `VERDICT PASS`, and the literal name appears **zero** times in any case form across the package, the archive extraction and this paper directory. The replacement token is not reproduced in this gap entry, for the same reason. Digests and the superseded values: `CLAIMS.md` claim R. |
| G-24 | The handoff's `sections_complete` is counted against the eight prose units (Abstract + §1–§7). | Title, references and back matter are not counted as "sections" in that figure. |
