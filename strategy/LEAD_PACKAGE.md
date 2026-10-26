# LEAD_PACKAGE — which package should lead `research-publish-packages`

**Unit:** ULEAD1 · **Date:** 2026-10-15 · **Purpose (one):** identify the single best package to publish first,
and say exactly what it would contain and what work it needs.
**Write scope:** this file, `orchestration/units/ULEAD1.md`, `orchestration/handoffs/ULEAD1.json`. Nothing else.
**Target `/home/zer0null/Duval`: read only.** Every command issued against it was `ls`, `find`, `wc`, `sed`,
`head`, `grep` — no writes, no `git`.

> **Method.** The candidate register ([`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G, §D, §E and
> [`PAPER_CANDIDATES_SUPPLEMENT.md`](PAPER_CANDIDATES_SUPPLEMENT.md)) was treated as a **hypothesis**, not as
> evidence. Every gate-hit number below was **measured** by running the exclusion pattern set over the actual
> files that would ship. Two register claims did not survive that check and are corrected in §6 and §8.

---

## 0. The decisive on-disk fact the register does not carry

`papers/` contains **exactly one manuscript** — `papers/encoder-crossover-190/` (18 files, `MANUSCRIPT.md`
66 KB) — and that is candidate **#3, the excluded one**.

```
find papers -type f | wc -l   → 18, all under papers/encoder-crossover-190/
ls papers/                    → encoder-crossover-190   (only entry)
```

**Consequence: for every candidate except the excluded #3, no manuscript exists.** What exists is
programme documentation in the target repo (`docs/research/*_2026.md`, run reports, pre-registrations,
evidence trees) and, in this workspace, one integrity harness (`repro/encoder-crossover-190-SANITISED/`)
that also belongs to #3.

So criterion 3 ("already written") cannot be satisfied by any viable lead in the strong sense. The real
question becomes: *which candidate's material is closest to a manuscript, and cleanest on criteria 1 and 2?*
The honest answer — recorded up front so the recommendation is not read as more ready than it is — is that
**no candidate is publishable today, and every lead requires a manuscript to be written.**
This is a "here is the smallest one to finish" result, not a "ship this" result.

---

## 1. Gate-hit measurement (the primary evidence)

Pattern set applied (the unit's list, `grep -E`): `/home/zer0null` · `duval` · `a5ef1b28` · `89003e70` ·
`publish-present-compete` · `Consonance` · `StateClass` · `grantPolicy` · `src/broker` · `src/scope` ·
`src/layer` · `CommitRecord` · `admit(` · `expanded[` · `EXCLUDED.md` · `REDACTION_REPORT` · `RESIDUALS.md` ·
`LICENCE_TODO` · `TRADE_SECRET` · `WITHHELD.md` · `DISCLOSURE_INVENTORY` · `EXPOSURE_CLOSURE` ·
`ARCHIVE_WINDOW` · `VERIFICATION_REPORT`. (`Consonance` run case-sensitively; the register's §G.1 #14 count
of 33 was reproduced exactly.)

| File (the artefact that would ship) | Lines | Gate hits | Where the hits are |
|---|---|---|---|
| `docs/research/GATED_READ_2026.md` | 340 | **1** | `:327`, prose: *"converts the measurement into a Consonance artefact"* |
| `docs/research/gated-read-rows.jsonl` | 9,260 rows | **432** | 4 `duval` + 212 `src/broker` + 216 `src/layer` — **all inside the `tag`/`file` metadata columns** |
| `docs/research/gated-read-summary.json` | 4.3 KB | **0** | — |
| `tools/gated-read/bench.py` | — | **0** | — |
| `tools/gated-read/tasks.json` | — | **3** | corpus filenames |
| `docs/MISTAKES.md` | 599 | **4** | `grantPolicy` `:47` (prose); `duval` `:480`, `:483`, `:484` (a pasted trace-append log line) |
| `evals/prevention.ts` | 789 | **0** | — |
| `docs/research/SELF_REFINEMENT_DEGRADATION_2026.md` | 605 | **0** | — |
| `docs/research/EXP#11-evidence/decider-rows.jsonl` | 4,090 rows | **7** | 3 `admit(` + 4 `expanded[` — **inside the option text the model chose between** |
| `docs/research/EXP#11-evidence/imajev-rows.jsonl` | 3,690 rows | **7** | same |
| `docs/research/EXP#11-evidence/*-manifest.jsonl` | — | 1 each | `/home/zer0null` |
| other `EXP#11-evidence/*` (17 files) | — | **0** | — |
| `docs/research/ESCALATION_LADDER_2026.md` | 154 | **0** | — |
| `docs/research/L1_HEAD_TO_HEAD.md` | 214 | **4** | not itemised |
| `docs/research/MODEL_ESTATE_AUDIT_2026.md` | 248 | **7** | not itemised |
| `docs/research/3MODEL_PILOT_RESULTS.md` | 168 | **0** | — |
| `docs/research/SM_PROJECTION_SHAPE.md` | 117 | **0** | — |
| `docs/research/ROUTING_ORNITH_2026.md` | 164 | **0** | — |
| `docs/research/LONG_HORIZON_EVALS_2026.md` (#13) | 1,529 | **1** | `:1343`, `StateClass`, inside §6 (the projection-A/B section, which a survey would excise anyway) |
| `docs/research/AGENT_HARNESSES_2026.md` (#14) | 823 | **36** | 33 `Consonance` + `StateClass`, incl. a dedicated §8 |

**The distinction that decides this unit.** A gate hit is not equally expensive to remove:

- **Lossless scrub** — the hit sits in a *metadata column* that is not load-bearing for the claim.
  `gated-read-rows.jsonl` is the clean case: the 432 hits are corpus **file paths** in `tag`/`file`, and the
  reported quantities (calls, prompt tokens, `pred`, `gold`, F1) are **invariant under renaming those
  paths** to `f001…f090`. The measured claim does not mention a single filename.
- **Lossy scrub** — the hit sits *inside the measured stimulus*. `EXP#11-evidence/*-rows.jsonl` is the clean
  case: the options are literally `"none -- admit() mints the state"` and `"the expanded[] ref list"`, i.e.
  kernel-internal vocabulary **is the thing the model was asked to choose between**. Renaming changes the
  stimulus; dropping those cases changes n and the fixture identity. **This is the same class of problem as
  the excluded #3's fixture, and the register's §G.1 has #4 marked `publish` without noticing it.**

That single distinction is what moves the recommendation away from #4 (and away from NC1, for a different
reason — see §6).

---

## 2. Ranked table of viable lead candidates

"Files on disk" counts only material that would plausibly ship or be cited. "Fixture?" asks whether the
package's *value* rests on released decision data (criterion 2). "Time to DOI" assumes the author works the
package and routes to arXiv (`10.48550/arXiv.*`) plus a workshop/short-paper.

| # | Candidate | What exists on disk (files) | Fixture? | Estimated gate hits | Work required | Time to DOI |
|---|---|---|---|---|---|---|
| **1** | **#7 batching note (R2)** — *batching 16–90 binary gate decisions at `effort=none` is free* | **7 files**: `GATED_READ_2026.md` (340 l), `gated-read-rows.jsonl` (9,260 rows), `gated-read-summary.json`, `tools/gated-read/{bench.py,tasks.json}`, `GATED_READ_PROVENANCE.md`, `STAGED_EXTRACTION_PROVENANCE.md`. Manuscript: **none** | **No** — claim is about the inference pattern; the 432 hits are file paths, scrubbed losslessly | 1 doc + 432 row-metadata + 3 tasks.json | Write manuscript (~3–4k words); scope to R2+R1; 2 lossless scrubs; neutral batcher check; licence/CITATION | **~1–2 weeks** |
| **2** | **NC1** — *detectors that cannot fail: 19 classes, machine-checked* | **~24 files**: `MISTAKES.md` (599 l), `evals/{prevention,types,compare,run,drift}.ts`, `scripts/` (17 entries, 6 named as detectors + `timer-guard-fixtures/`), `.githooks/{pre-commit,post-commit,commit-msg}`, `tools/trace.ts`, `EVALS.md`, `LEARNINGS.md` (M1–M14), `EXPERIMENT_SM_PILOT.md`, `evidence/gates-2026-10-11/RUN.md`, `WORKSTREAM_RECOVERY_PLAN.md`. Manuscript: **none** | **No** — no decision data at all | 4 (all prose/log) in `MISTAKES.md`; `evals/prevention.ts` **0**; `tools/trace.ts` **not measured** | Write manuscript; **rebuild the detector set** so the headline invariant is reproducible (§6); build M1–M14 ↔ 19-class cross-walk; 4-line scrub | **~3–6 weeks** |
| **3** | **#13 survey** — *long-horizon agent evaluation* | **1 file**: `LONG_HORIZON_EVALS_2026.md` (1,529 l, fully sourced §8). Manuscript-shaped *note*, not a paper | **No** — about the field | 1 (`StateClass` `:1343`, in the section a survey drops) | Reframe an A/B research note into a survey (abstract, scope, excise §6); survey ships **no code** | **~3–7 days to a DOI — but see §7** |
| **4** | **#5 escalation ladder** | **~10 files**: `ESCALATION_LADDER_2026.md` (154 l), `L1_HEAD_TO_HEAD.md` (214 l), `MODEL_ESTATE_AUDIT_2026.md` (248 l), `l1-head-to-head.jsonl`, `ornith-tier-rows.jsonl`, `routing-rows.jsonl`, `TIER2_*` (5). Manuscript: **none** | **Yes** — "measured on the same 190 cases"; row files not gate-scanned | ≥11 in the three docs, unscanned in the rows | Write manuscript; **resolve the fixture-vocabulary question**; the `DecisionKind` taxonomy (M11) must be kept out | **~2–4 weeks** |
| **5** | **#4 self-refinement degradation** | **~25 files**: `EXP#11-per-model-option-revision.md` (40 KB prereg), `SELF_REFINEMENT_DEGRADATION_2026.md` (605 l, 0 hits), `FINDINGS_REGISTER` F-EXP11-*, `EXP#11-evidence/` (20 files, 7,780 rows). Manuscript: **none** | **Yes — with vocab hits inside the stimulus** (§1) | 14 in the two rows files + 2 manifests + 0 in the 605-l related-work record | Write manuscript **and** settle the fixture-vocabulary problem (the class under separate test); plus the #4 power caveats: p=0.0156 fails Bonferroni | **~4–8 weeks** |
| **6** | **#2 replay divergence** | 1 doc + the corpus (`decision-variants.jsonl`, `decision-tree-spec.json`) | **Yes** (recorded decision data) | not measured | **The scorer does not exist** — `tools/replay/exp7.ts` is in the withhold block; a neutral divergence scorer must be written | ≥6 weeks |
| **7** | **#14 survey + position** | 1 file, 823 l | No | **36** | Excise 33 `Consonance` mentions + a dedicated §8; the position half restates the already-public W3 → **duplication** | ~2–3 weeks |
| 8 | **#6, #8, #9, #10, #11, #12** | — | #6/#8 fail limb (b) on the emitter/projection (M7/M1–M2); #10's demonstration **does not exist**; #9/#11/#12 are real but need packaging + a manuscript | — | Not leads | — |

---

## 3. Recommended lead — **#7, scoped to R2: batching binary gate decisions**

**Working title:** *Free batches: batching binary read-gate decisions 16–90-way at `effort=none`, and why a
purpose-conditioned gate on header and structure alone is not yet a classifier.*

**The measured content already on disk (no new run):**
`gated-read-rows.jsonl` is 9,260 rows, 0 call errors, 0 unparsed, run 2026-09-30 on branch
`measure/gated-read`. Per-configuration, **n = 1,800**:

| config | calls | prompt tokens | F1 |
|---|---|---|---|
| bs1 `none` | 1,800 | 631 K | 0.218 |
| bs16 `none` | 120 (**15×**) | 270 K (**2.3×**) | 0.227 |
| bs90 `none` | 20 (**90×**) | 261 K (**2.4×**) | 0.210 |

and the motivating negative — the best binary gate F1 is **0.320**, best precision 0.418 at recall 0.233, so
the most precise gate silently drops 3 of 4 gold files. Both are statements of *what was measured*; neither
needs a kernel mechanism (no M-number appears in either claim).

**Why it wins, criterion by criterion:**

1. **Gate-clean — the cheapest scrub of any candidate, and it is lossless.** One 12-word sentence
   (`GATED_READ_2026.md:327`) and a mechanical column rename over `tag`/`file` in the rows and in
   `tasks.json`. The claim contains no filename, so the rename cannot alter any reported number.
   `gated-read-summary.json` and `bench.py` are already at **0** hits.
2. **No fixture dependency.** The finding is a property of *batched binary decisions at `effort=none`* — an
   inference pattern, not a corpus. Nothing in the package asks a reader to accept released decision data as
   the thing of value. This is the criterion the excluded #3 fails and #4/#5/#2 also fail.
3. **Already written — partially, and I am not overstating it.** The pre-registration (the arm table G1/G2/E/X
   with what each measures), the run, the raw rows, the summary and the results tables all exist and are
   dated. **There is no manuscript**: no abstract, no introduction, no related-work section, no paper-form
   method, no discussion. That work is real and is the bulk of the remaining cost (§5).
4. **Small — the smallest of any viable candidate.** 5 existing files + 3 new plumbing files, versus ~24 for
   NC1 and ~25 for #4, and it needs **no** rebuilt harness: `bench.py` is 0-hit and self-contained.
5. **Fast to a DOI.** No new experiments, no new compute, a powered positive result, and a short-paper route
   that arXiv makes a DOI-in-days. This is the only candidate where nothing has to be *measured* first.

**Honest weakness.** It is **thin** as a standalone paper: one model, one corpus, three configurations. It
is a **short note or workshop paper, not a main-venue systems paper**, and a reviewer may call n=1 model
insufficient. Its interest comes from pairing the positive (batching is free) with the negative (the gate
itself is not accurate) and from the contrast with published batch-prompting losses (BatchPrompt: −17.8 pts
at bs≥64 on QA/NLI) — *binary gate decisions do not degrade here*. Said plainly: **this leads because it is
the fastest clean DOI, not because it is the most important paper in the corpus.** If the author's priority
is DOI speed and pipeline proof, it is the pick. If the priority is a substantive contribution,
the runner-up (§6) is the better paper and the worse package.

---

## 4. Exact contents manifest for the recommended lead

**New repo:** `research-publish-packages` (fresh history). Package name proposed: `gated-read-batching-190`.

| # | Path that ships | Sourced from | Change on the way in |
|---|---|---|---|
| 1 | `paper/MANUSCRIPT.md` | `/home/zer0null/Duval/docs/research/GATED_READ_2026.md` | **New paper form**: abstract, intro, related work, method, results (R2 + R1), limitations, reproducibility. Excise `:327`. Scope out R5. |
| 2 | `paper/preregistration.md` | §"experiment design" of the same file | Extracted verbatim so the pre-registration is separately citable |
| 3 | `data/gated-read-rows.jsonl` | `/home/zer0null/Duval/docs/research/gated-read-rows.jsonl` | `tag` and `file` → `f001…f0NN`; **all 432 gate hits removed** (measured); every other column byte-identical |
| 4 | `data/gated-read-summary.json` | `/home/zer0null/Duval/docs/research/gated-read-summary.json` | 0 hits measured; verify no absolute paths |
| 5 | `data/key.json` | **new** | The `f001…f0NN` ↔ original-path map, **withheld** from the public package (this is the one thing that must not travel) |
| 6 | `harness/bench.py` | `/home/zer0null/Duval/tools/gated-read/bench.py` | 0 hits measured; confirm it runs with no withheld import |
| 7 | `harness/tasks.json` | `/home/zer0null/Duval/tools/gated-read/tasks.json` | 3 hits → same anonymisation as #3, so the harness and rows agree |
| 8 | `harness/anonymise.py` | **new** | The rename must be reproducible, because the paper claims the labels are *mechanically* assigned |
| 9 | `LICENSE` | the author's rule | **PolyForm Noncommercial** (per `PAPER_CANDIDATES.md` §G and `CODE_LICENSING_STRATEGY.md`) |
| 10 | `README.md`, `CITATION.cff` | **new** | DOI plumbing + the exact reproduction commands |

**Explicitly not shipped:** the R5 staged extractor (its harness *is* the gate/absence machinery, M10, and
its numbers are n=20), `tools/gated-read/bench.py`'s imports if any reach the withheld tree, and `data/key.json`.

**Never written:** the target repo is read-only; every file above is *copied into* the new repo.

---

## 5. Work remaining to make the lead publishable (specific)

1. **Write the manuscript (the dominant cost — this is not editing, it is authoring).**
   `GATED_READ_2026.md` is a run report. There is no abstract, no introduction, no related-work section, no
   paper-form method, no discussion, no limitations section. Estimated **3,000–4,500 words** using the
   existing tables and numbers. **If the author does not want to write a manuscript, no candidate in this
   report is ready.**
2. **Fix the scope in writing.** Paper = R2 (batching is free, n=1,800/config) + R1 (the binary gate is not
   yet a classifier, best F1 0.320) + the BatchPrompt contrast. **Drop R5** (M10 exposure, n=20, cannot
   separate the top four arms).
3. **Do the two lossless scrubs and prove them lossless.** Rename `tag`/`file` in the rows and in
   `tasks.json` to `f001…f0NN`; land `data/key.json` as withheld; re-run the summary from the renamed rows and
   confirm every number in the paper is byte-identical. Excise `GATED_READ_2026.md:327`.
4. **Verify `bench.py` runs without the withheld tree** (`tools/**` is the M13 block; `bench.py` itself has 0
   gate hits but I did not execute it — see §9). If it imports anything withheld, write a ~1-file neutral
   batching driver; this is much smaller than the neutral re-implementations #2, #6 and #8 require.
5. **Add the reproduction commands** to the README: install, run `anonymise.py`, run `bench.py`, regenerate
   `gated-read-summary.json`, and the exact assertion that F1 stays within ±0.01.
6. **Choose the route and clear it:** arXiv (immediate `10.48550` DOI) + a workshop/short-paper track. Confirm
   **endorsement** is in place for the intended arXiv category before promising DOI timing.
7. **Licence + metadata:** PolyForm Noncommercial text, `CITATION.cff`, package name.
8. **Optional, improves acceptance odds:** one external replication of the batching arm (a second model at
   bs1/bs16/bs90). This is the only *new measurement* worth doing for the lead, and it is small.

---

## 6. Runner-up — **NC1, "Detectors that cannot fail"**, and why my hypothesis about it is only half right

The unit card proposed NC1 ("Detectors that cannot fail", from `MISTAKES.md`) as the likely best lead:
paper-only, no fixture, method contribution. **Tested rather than accepted, the hypothesis divides:**

**Half confirmed.**
- **Gate-clean enough.** `evals/prevention.ts` (789 l) measured **0 hits**; `docs/MISTAKES.md` has **4**, all
  scrub-able prose/log (`grantPolicy` `:47`; three `duval` trace-append lines `:480/483/484`).
- **Genuinely fixture-free.** Nothing in NC1 asks a reader to accept released decision data.
- **Its headline invariant is currently TRUE, and I verified it rather than trusting the count sentence.**
  Counting the detector-status table rows gives **19 rows — 12 automated, 3 partial, 4 manual**, which matches
  the sentence at `MISTAKES.md:386` exactly. The paper's central claim (a class with no detector is a visible
  gap, not a silent one) survives its own check.
- **The intellectual fit is the best in the corpus** for a "clean, simple, method" lead, and it is the only
  candidate whose contribution is a *method* rather than a measurement of the author's own stack.

**Half falsified — the package does not close.**
- **"Paper-only" is true for the paper and false for the package.** The machine-enforced invariant is the
  paper's selling point, and `evals/prevention.ts` check B requires **every `automated` row to name a detector
  that resolves**. The 12 automated rows name `scripts/check-timers.py`, `scripts/sync-issues.sh`,
  `scripts/guardrails.sh`, `scripts/write-scope-guard.mjs`, `evals/run.ts`, `evals/drift.ts`,
  `evals/prevention.ts` and **`tools/trace.ts`** — and `tools/trace.ts` is in the **M13 withhold block**.
  Shipping the registry + the eval **without** the detector set makes the package's own headline invariant go
  **RED on a reader's first run** — a detector that cannot fail, inside the paper about detectors that cannot
  fail. Either ship the ~17-file `scripts/` tree + `timer-guard-fixtures/` + 3 `.githooks/` files + a
  neutralised `tools/trace.ts`, or reformulate the eval so a declared "external detector set" mode is honest.
  Both are design work, not framing.
- **"1–2 weeks" is a paper estimate, not a package estimate.** It also omits the M1–M14 ↔ 19-class cross-walk
  that does not exist on disk (M11 and M12 have no class; 15 classes have no M-id).
- One register claim corrected: `docs/research/experiments/LEARNINGS.md` is **35,636 B**, and NC1's "19
  classes" is stable at 19 rows even though appended sections stale the prose — the drift is cosmetic, not
  structural.

**Verdict:** NC1 is the **better paper** and the **worse package**. It is the runner-up because the delivery
risk is a rebuild, not a scrub — while the lead's risk is only writing.

---

## 7. Is a survey a legitimate lead? (#13, #14) — **no, and here is precisely why**

- **#13 is the fastest DOI in the corpus and I am not disputing that.** `LONG_HORIZON_EVALS_2026.md` is
  1,529 lines, **1 gate hit** (a single `StateClass` at `:1343`, inside §6 — the projection-A/B section a
  survey would remove anyway), no fixture, and §8 lists every URL opened. A reframed survey could be on arXiv
  in **days**.
- **But a survey cannot lead `research-publish-packages`.** The repo's declared purpose is a **code + paper**
  store and the pipeline to prove is *data → package → DOI*. A survey ships **no artifact**, so it proves the
  paper half and none of the packaging half. The author's own rule (`PAPER_CANDIDATES.md` §G) is explicit:
  *"only small extracted projects that go public and the papers associated with it"*, and §G.1 states
  surveys *"are not extracted projects and are decided separately"*. A survey lead would ship a package whose
  contents manifest is one Markdown file.
- **A second, structural problem:** as it exists on disk the document is not a survey — it is an internal
  research note, headed *"Research note for the projection-memory A/B"*, with §6 answering *"what this implies
  for the projection-vs-full-transcript A/B"*. Publishing it as a survey requires reframing (title, abstract,
  scope, excise §6) and adding a survey's own apparatus. That is a real, if modest, authoring job.
- **Venue context:** TMLR no longer considers surveys (`§11.13` of the register), so the survey route is
  arXiv + a venue that takes surveys.
- **#14 is not a candidate at all.** 36 hits in 823 lines, including a dedicated §8 *"Implications for
  Consonance"*; its position half restates W3, which is **already public**, so the defect is **duplication**.
  Excising the exposure would remove the paper's argument.

**Recommendation on surveys:** keep #13 as an **optional fast-DOI side-channel** to run *in parallel* with
the lead — it is cheap, it is clean, and a DOI is a DOI — but **do not let it be the lead**, because it cannot
prove the pipeline the repo exists to prove.

---

## 8. What I could not determine

1. **Whether `tools/gated-read/bench.py` executes standalone.** It has 0 gate hits, but I did not run it; if
   it imports anything under `tools/**` it inherits the M13 withhold question. This is the lead's only
   technical unknown and it is checkable in one command.
2. **Whether `tools/trace.ts` is itself gate-clean** — not scanned, and it is NC1's blocking dependency.
3. **Whether the corpus file-path list is itself sensitive.** The recommendation assumes `src/broker/*` and
   `src/layer/*` **paths** are not secret once the code is not shipped; if the author considers the file
   *inventory* secret, the lead's scrub becomes a rebuild and NC1 becomes relatively stronger.
4. **Whether arXiv endorsement is in place** for the intended category. The "1–2 weeks to DOI" figure is
   contingent on it; without endorsement, timing is not mine to promise.
5. **Whether PolyForm Noncommercial is the settled licence** for this package specifically (the register
   says selected pieces are released under it; `LICENCE_TODO.md` exists in the #3 sanitised tree).
6. **The exact gate status of `EXP#11-per-model-option-revision.md`** (the #4 pre-registration) and of
   `GATED_READ_PROVENANCE.md` / `STAGED_EXTRACTION_PROVENANCE.md` — not scanned; this affects #4/#5's row in
   the table, not the lead's.
7. **The real venue appetite for a one-model, three-configuration note.** My "~1–2 weeks" is a production
   estimate, not an acceptance estimate.

---

## 9. UNVERIFIED

- `tools/gated-read/bench.py` runs without the withheld `tools/**` tree — **UNVERIFIED** (0 gate hits measured;
  execution not attempted).
- `tools/trace.ts` gate-hit count — **UNVERIFIED** (not scanned).
- `docs/research/EXP#11-per-model-option-revision.md`, `GATED_READ_PROVENANCE.md`,
  `STAGED_EXTRACTION_PROVENANCE.md`, `L1_HEAD_TO_HEAD.md`, `MODEL_ESTATE_AUDIT_2026.md`,
  `routing-rows.jsonl`, `ornith-tier-rows.jsonl`, `l1-head-to-head.jsonl` — **UNVERIFIED** (hit counts for
  the first two and the rows files not measured; L1/MODEL_ESTATE counts are measured but their hit *locations*
  are not itemised).
- `docs/research/LONG_HORIZON_EVALS_2026.md` is publishable as a survey after reframing — **UNVERIFIED**
  (the reframing is my judgement, not a measurement).
- That the #7 batching rows' 432 gate hits are **exclusively** in `tag`/`file` — **VERIFIED by inspection of
  the columns** (every hit is a corpus path); that no *other* column carries an unpatterned identifier is
  **UNVERIFIED**.
- Time-to-DOI figures — **estimates**, contingent on endorsement and on the author writing the manuscript.
- `#13`'s and `#14`'s status as "legitimate papers, illegitimate package leads" — that is this unit's
  judgement, not a measurement.

---

## 10. Commands run (evidence)

```
find papers -type f                                  # 18 files, all encoder-crossover-190
ls papers/                                           # one entry
wc -l strategy/PAPER_CANDIDATES.md                   # 1160
grep -n '^#\|^##\|^###' strategy/PAPER_CANDIDATES.md
grep -Eco "$PATS" docs/research/{SELF_REFINEMENT_DEGRADATION,ESCALATION_LADDER,GATED_READ,\
LONG_HORIZON_EVALS,AGENT_HARNESSES,L1_HEAD_TO_HEAD,MODEL_ESTATE_AUDIT,TEARDOWN_LIVE,\
TEARDOWN_TIMEOUT,3MODEL_PILOT_RESULTS,3MODEL_GATE,ROUTING_ORNITH,SM_PILOT_RESULTS,\
SM_PROJECTION_SHAPE}_2026.md                         # measured hit counts, §1
grep -Eno "$PATS" docs/MISTAKES.md                   # 47 grantPolicy; 480,483,484 duval
grep -Eco "$PATS" evals/prevention.ts                # 0
sed -n '1,60p' evals/prevention.ts                   # imports ../tools/trace.ts
grep -n "MISTAKES\|detector-coverage" evals/prevention.ts
sed -n '384,420p' docs/MISTAKES.md                   # detector table: 19 rows, 12/3/4 — matches :386
grep -Eco "$PATS" docs/research/EXP#11-evidence/*    # 7 + 7 in the two rows files; 1 + 1 manifests
grep -Eo "$PATS" docs/research/EXP#11-evidence/decider-rows.jsonl | sort | uniq -c   # admit( x3, expanded[ x4
grep -o '.\{70\}admit(.\{20\}' docs/research/EXP#11-evidence/decider-rows.jsonl       # inside option text
grep -Eo "$PATS" docs/research/gated-read-rows.jsonl | sort | uniq -c  # duval 4, src/broker 212, src/layer 216
head -c 600 docs/research/gated-read-rows.jsonl      # schema: hits in tag/file only
find tools/gated-read -type f                        # tasks.json, bench.py
grep -rEco "$PATS" tools/gated-read/                 # tasks.json 3, bench.py 0
sed -n '140,160p' docs/research/GATED_READ_2026.md   # the R2 table: 1800/120/20 calls
sed -n '200,215p' strategy/PAPER_CANDIDATES.md       # #2: 3,040 recorded outputs, 190 cases
ls scripts/ | wc -l ; ls .githooks ; ls tools/trace.ts   # NC1 detector-set inventory
```
