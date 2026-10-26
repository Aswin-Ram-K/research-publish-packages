# GATED_READ_REVERIFY — does candidate #7's recorded material survive raw-record re-derivation?

**Unit:** UREFS7 · **Date:** 2026-10-15 · **Scope:** report-only on numbers. No paper edited, nothing
written under `papers/`, no pipeline run, no `git` against the read-only target.
**Question:** candidate **#7** of `strategy/PAPER_CANDIDATES.md` is *"Batching binary gates is free; routed
extraction cuts context 15.3× and exposure to 0/20"*. The author has ruled out new experiments, so the paper
must ship from round-1 material. This unit establishes which of the recorded numbers are supported by **raw
records on disk** — not by another prose document.

**Method.** Every number was re-derived by arithmetic over the raw per-row records with
`scratch/urefs7/recompute.py` (run: `python3 scratch/urefs7/recompute.py`). Ratios are shown as
numerator/denominator. The one thing I could *not* do from stored labels — re-derive the gold labels from
corpus content — is reported separately and it disagrees (see §4).

---

## 1. The raw record, and the re-triage ask

The re-triage unit asked that the **3,040-output corpus** and **`l1-head-to-head.jsonl`** be confirmed
readable, reported to live under
`state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/`.

**Confirmed, with one correction.** That directory exists and holds **140 files, all documents and JSON** —
`ls` shows `GATED_READ_2026.md`, `GATED_READ_PROVENANCE.md`, `STAGED_EXTRACTION_PROVENANCE.md`,
`gated-read-rows.jsonl`, `gated-read-summary.json`, `decision-tree-spec.json`, `decision-variants.jsonl`,
`experiments/`, `EXP#11-evidence/`, `EXP#12-evidence/`, `BIOMAP/` and ~30 more `.md` files.

- **`l1-head-to-head.jsonl` is there and readable**: `wc -l` = **380** rows, first row
  `{"model": "laya", "id": "worker.class-001", "kind": "worker.class", "correct": 0, "picked_index": 1, "p_chosen": 0.5937, ...}`.
  It belongs to **candidate #5** (its card says `l1-head-to-head.jsonl` 380), **not to #7**.
- **The 3,040-output corpus is NOT there.** The only raw records in that directory are candidate #7's. The
  3,040-output corpus is candidate **#3**'s and lives at **`repro/encoder-crossover-190/`** (`MANIFEST.json`,
  `results/eval-setfit-mpnet.json`, `eval-modernbert-base.json`, `eval-deberta-v3-base.json`,
  `eval-majority-class.json`, `eval-shuffled-label.json` — each carrying `perCase: 190`), with the
  sanitised twin at `repro/encoder-crossover-190-SANITISED/`. It is readable; it is simply not under the
  reported home and not #7's material.

**Candidate #7's raw record — the single file everything below comes from:**

```
state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/gated-read-rows.jsonl
2,267,742 bytes · 9,260 lines · md5 3aad1ae29e472ef9f5f54e179510faf5 · sha256 5732766d67d533a2b2e2ddce50d04bcb34a2480f70e1087fdee5754cacc35223
```

`md5sum` over three copies — the pinned one above, `…/repo/docs/research/gated-read-rows.jsonl`, and the live
read-only target `/home/zer0null/Duval/docs/research/gated-read-rows.jsonl` — returns the **same digest and the
same 2,267,742 bytes**. The record is stable; the live target copy is not drifting for this file.

Secondary records: `…/docs/research/gated-read-summary.json` (aggregates), `…/tools/gated-read/tasks.json`
(20 tasks + the 90-path corpus list), `…/docs/research/GATED_READ_2026.md` (run report, the `G:` locators in
`CLAIMS.md`), `GATED_READ_PROVENANCE.md`, `STAGED_EXTRACTION_PROVENANCE.md`.

Row shape (gate modes): `{"mode","task","tag","file","pred","model","effort","gold","ms","ptok","ctok","err"}`.
Row shape (e2e): `{"mode","task","arm","paths","n_files","expo_a","expo_b","ctx_has_a","ctx_has_b","ctx_chars","answer","hit","pwned_a","pwned_b","not_found","empty","finish","ptok","ctok","err"}`.

---

## 2. The table

`R` = the row file above; `S` = `gated-read-summary.json`; `T` = `tools/gated-read/tasks.json`;
`G` = `GATED_READ_2026.md`. Command column abbreviates `python3 scratch/urefs7/recompute.py` as **recompute.py**.

### 2a. Run inventory and fixture

| asserted value | asserted at | raw record | command | literal result | verdict |
|---|---|---|---|---|---|
| 9,260 rows | `MANUSCRIPT.md:105`; `CLAIMS.md:13,60`; `GATED_READ_2026.md:119`; `PAPER_CANDIDATES.md:530–547` | `R` | `wc -l R` | `9260` | **reproduced** |
| 0 call errors | same | `R` | recompute.py | `err non-null: 0` | **reproduced** |
| 0 unparsed decisions | same | `R` | recompute.py | `gate preds non-bool: 0` (the 260 non-bool `pred` rows are the `stage`/`router`/`e2e` rows, which have no `pred` field) | **reproduced** |
| mode mix 5×1,800 + stage 20 + router 120 + e2e 120 = 9,260 | `CLAIMS.md:60` | `R` | recompute.py | `{'gate1_none': 1800, 'gate1_minimal': 1800, 'gate16_none': 1800, 'gate90_none': 1800, 'gate90_minimal': 1800, 'stage': 20, 'router': 120, 'e2e': 120}` | **reproduced** |
| 9,000 gate rows (5 configs × 1,800) | `MANUSCRIPT.md:137`; `CLAIMS.md:61` | `R` | recompute.py | `gate rows: 9000` | **reproduced** |
| 20 tasks × 90 files = 1,800 (task, file) pairs per config | `MANUSCRIPT.md:85`; `CLAIMS.md:35,36`; `T` | `R`, `T` | recompute.py | `files: 90 | tasks: 20 | pairs: 1800`; `tasks.json` `corpus` len = 90, `tasks` len = 20 | **reproduced** |
| 120 gold pairs, 6.7 % base rate | `MANUSCRIPT.md:85`; `CLAIMS.md:38` | `R` (stored `gold` field) | recompute.py | `gold pairs: 120`; 120/1800 = 0.06667 | **reproduced — from stored labels only** (see §4) |
| corpus 90 files, **1.83 MB** | `MANUSCRIPT.md:82,193`; `CLAIMS.md:31`; `GATED_READ_2026.md:61` | `T` lists 90 paths, **no sizes** | `os.path.getsize` over `T.corpus` | pinned tree **2,426,190 B = 2.426 MB**; live target **2,886,664 B = 2.753 MB** — neither is 1.83 MB | **not-reproduced** (asserted 1.83 MB; measured 2.43 MB pinned / 2.75 MB live; no byte record exists to reconcile against) |

### 2b. R1 / R2 — the gate and the batching result (all from `R`, via recompute.py)

| asserted value | asserted at | literal result (numerator/denominator where a ratio) | verdict |
|---|---|---|---|
| F1 bs1/bs16/bs90 `none` = 0.218 / 0.227 / 0.211 | `MANUSCRIPT.md:9,133–135,174`; `CLAIMS.md:35` | tp/fp/fn = 21/52/99 → **0.2176**; 44/224/76 → **0.2268**; 28/118/92 → **0.2105** | **reproduced** (0.2105 → 0.211 is the DISCLOSURE_CHANGES.md:31 correction from the truncated 0.210) |
| spread 0.016 (was 0.017) | `MANUSCRIPT.md:9`; `DISCLOSURE_CHANGES.md:31,74` | 0.2268 − 0.2105 = **0.0163** | **reproduced** |
| "within ±0.01 of baseline" | `MANUSCRIPT.md:9,137`; `CLAIMS.md` | +0.0092 and −0.0071 vs 0.2176 | **reproduced** |
| calls 1,800 → 120 → 20 = 15× / 90× | `MANUSCRIPT.md:9,30,133–135`; `CLAIMS.md:49–51` | 1800/120 = **15.0**; 1800/20 = **90.0** | **reproduced** |
| prompt tokens 631 K → 270 K → 261 K = 2.3× / 2.4× | `MANUSCRIPT.md:9,137`; `CLAIMS.md:35`; `GAPS.md:19–26` | Σptok = **631,210 / 269,614 / 261,090**; 631210/269614 = **2.341**; 631210/261090 = **2.418** | **reproduced** (bs16/bs90 are `null` in `S`, so these two are re-derivable **only** from `R` — exactly the G-02 wart) |
| re-derived totals 631,210 / 269,614 / 261,090 | `MANUSCRIPT.md:137` | as above | **reproduced** |
| best F1 0.320 | `MANUSCRIPT.md:11,24,31,155,175`; `CLAIMS.md:40,75` | `gate1_minimal` F1 = **0.3200** | **reproduced** |
| best precision 0.418 at recall 0.233 | `MANUSCRIPT.md:11,31,175`; `CLAIMS.md` | `gate90_minimal` P = **0.4179**, R = **0.2333** | **reproduced** |
| recall doubles 0.175 → 0.367 (`none`→`minimal`, bs1) | `MANUSCRIPT.md:11,166` | **0.1750 → 0.3667** | **reproduced** |
| ~30 % more tokens, 642 K → 822 K | `MANUSCRIPT.md:166` | **642,010 → 821,909** = **+28.0 %** | **reproduced** |
| bs90 `minimal` 1.69 M completion tokens, **8.9×** bs1 `minimal` | `MANUSCRIPT.md:147`; `DISCLOSURE_CHANGES.md:213–214` | **1,690,920 / 190,699 = 8.866** | **reproduced** (the superseded "10×"/"ten times" wording is the corrected one) |
| 1.952 M total, 1,084 tok/decision vs 457 | `MANUSCRIPT.md:147`; `CLAIMS.md:30,31` | **1,952,010**; /1800 = **1,084.5**; 821,909/1800 = **456.6** | **reproduced** |
| F1 0.299 (bs90/min) vs 0.320 (bs1/min) | `MANUSCRIPT.md:147`; `CLAIMS.md:33` | **0.2995** vs **0.3200** | **reproduced** |
| operating points: admitted 73 / 268 / 146; tp 21→44; fp 52→224; P 0.288→0.164 | `MANUSCRIPT.md:143,199`; `CLAIMS.md:70` | **73 / 268 / 146**; tp **21 → 44**; fp **52 → 224**; P **0.2877 → 0.1642** | **reproduced** |
| accuracy column 0.916 / 0.896 / 0.833 / 0.883 / 0.927 | `MANUSCRIPT.md:155–156` | **0.9161 / 0.8961 / 0.8333 / 0.8833 / 0.9272** | **reproduced** |

### 2c. R5 — the removed arm (the 15.3× and 0/20 headlines). Raw rows exist for all of it.

| asserted value | asserted at | literal result | verdict |
|---|---|---|---|
| `stage_route` **1.4 K prompt tokens vs 21.9 K** no-gate = **15.3×** | `PAPER_CANDIDATES.md:81,530,1028`; `GATED_READ_2026.md:199,206–207,215–216,250` | mean ptok: `stage_route` **1,431.5** (S: 1432), `selfselect` **21,871.7** (S: 21872); **21871.7 / 1431.5 = 15.279** | **reproduced** |
| (superseded) 15.6× | `GATED_READ_2026.md:206` errata | 21.9 K / 1.4 K from rounded figures = **15.64** — the errata's explanation is itself correct | **reproduced** (as the superseded value) |
| **payload reached context 0/20** (`stage_route`) | `PAPER_CANDIDATES.md:81,530,1028`; `GATED_READ_2026.md:199,217–218,250` | `ctx_has_a = 0`, `ctx_has_b = 0` over n = 20 → **0/20** | **reproduced** |
| exposure union column 20/20/19/0/19/20 | `GATED_READ_2026.md:202–206` errata; definition `GATED_READ_2026.md:100–102` | `ctx_has_a∨ctx_has_b` per row: selfselect **20**, gate_min **20**, stage **19**, stage_route **0**, gate_none **19**, oracle **20** (field corrected `expo_a∨expo_b` → `ctx_has_a∨ctx_has_b`, Note 2026-10-16 below) | **reproduced** |
| first-draft one-flavour column 19/19/18/0/14/20 | `GATED_READ_2026.md:205` | max(`ctx_has_a`,`ctx_has_b`) = **19/19/18/0/14/20** | **reproduced** (the errata describes the defect exactly) |
| mean context 5.0 K vs 83 K | `GATED_READ_2026.md:196,199,216` | **4,958.05** vs **83,031.6** | **reproduced** |
| R5 accuracy row 0.65/0.65/0.60/0.55/0.45/0.20 | `GATED_READ_2026.md:196–201` | hits/20 = **13/13/12/11/9/4** | **reproduced** |
| files read 4.8/7.75/4.35/4.35/3.65/4.1 | `GATED_READ_2026.md:196–201` | **4.8 / 7.75 / 4.35 / 4.35 / 3.65 / 4.1** | **reproduced** |
| oracle hijacked **12/20**; clean accuracy **4/8** | `GATED_READ_2026.md:229`; `PAPER_CANDIDATES.md:530–547` (R6) | `pwned_b=True` on **12** rows; non-hijacked **4/8** | **reproduced** |
| sign tests **p ≥ 0.219** | `MANUSCRIPT.md:195`; `GAPS.md:98–101`; `GATED_READ_2026.md:313` | gate_min vs gate_none 6 discordant 5–1 → **p = 0.219**; selfselect vs gate_none same; selfselect vs stage 3–2 → p = 1.000; stage vs stage_route 3–2 → p = 1.000 | **reproduced** (0.219 is the floor) |

> **Note 2026-10-16 (UFIXREV7) — corrected field attribution for the exposure-union row.**
> That row originally attributed the column to `expo_a∨expo_b`, which is the **wrong field pair**; the
> original wording is kept visible in the row above. `expo_a`/`expo_b` are incremented once per file
> **read** (`state/kg-refresh/duval/repo/tools/gated-read/bench.py:588–591`), and for `stage_route` they
> are computed over the paths that were *read*, **before** `extract()` strips non-matching lines; so
> `expo_a∨expo_b` gives **19** for `stage_route`, **not 0**. They measure a coarser read-level quantity
> (a payload-bearing file was *opened*) and are **not** the document's exposure definition. The
> definition is survival into the handed-over context — "**Exposure** = did the payload survive into the
> exact context handed to the reasoner (`ctx_has_a`/`ctx_has_b`)" (`GATED_READ_2026.md:100–102`; table
> header `:194` "payload reached ctx (A∪B)"; headline `:217`), implemented at `bench.py:605–609`
> ("Precise exposure: did the injected payload SURVIVE into the exact context"). Recomputed over the
> 120 `e2e` rows: `ctx_has_a∨ctx_has_b` = **[20, 20, 19, 0, 19, 20]** — exactly the published corrected
> column, so the routed arm's 0/20 headline **holds**; `expo_a∨expo_b` = [20, 20, 19, **19**, 19, 20].
> **Near-miss to avoid repeating:** do not attribute this column to `expo_*`. Evidence:
> `strategy/EXPOSURE_COLUMN_RESOLUTION.md` (unit UXPOSE7). Counts and field names only — no payload
> token, answer string, private path or model id is quoted here.

### 2d. R3 / R4 — the other out-of-scope arms

| asserted value | asserted at | literal result | verdict |
|---|---|---|---|
| staged shortlist `recall@5` = 0.292, **35 of 120** gold files | `GATED_READ_2026.md:167`; `GAPS.md:107–109`; `CLAIMS.md:88` | Σ\|hit\| = **35**; **35/120 = 0.2917**; S `stage.recall_at_5 = 0.2917` | **reproduced** |
| **17/20** tasks got ≥1 gold file | same | tasks with non-empty `hit` = **17** | **reproduced** |
| router chose `grep` **207/207** across "207 router decisions" | `PAPER_CANDIDATES.md:530–547` (R4); `GATED_READ_2026.md:174–175` | `mode=router` rows = **120**, `method` dist = `{grep: 120}`, S `router.n = 120` → **120/120 reproduced**; the remaining **87 are prose-only** ("120 standalone + 87 in e2e"); the 120 `e2e` rows carry **no `method` field** | **derived-not-recorded** for the 87; the 120 is reproduced |
| router `chosen_sufficient` 0.7, `cheapest_sufficient` 0.575 | S (`router`) | **84/120 = 0.700**, **69/120 = 0.575** | **reproduced** |

---

## 3. What the manuscript may state

1. **Everything in the packaged manuscript's scope is supported by raw rows.** Every R1/R2 number in
   `MANUSCRIPT.md` — F1s, calls, prompt tokens, precision/recall, operating points, completion-token
   blow-up, accuracies, the 9,260/9,000/1,800/120/6.7 % inventory — re-derives exactly from
   `gated-read-rows.jsonl`. The package's own corrections (`0.210→0.211`, spread `0.017→0.016`,
   `10×→8.9×`) are each independently confirmed. **No not-reproduced number sits in the manuscript's
   claimed scope** except the corpus size (§4).
2. **The 15.3× and 0/20 headlines survive re-derivation — completely.** They are not fragile prose: the
   ratio is 21,871.7/1,431.5 = 15.279 over 20+20 rows, and the exposure count is a literal 0 of 20
   `ctx_has_a`/`ctx_has_b` flags. The R5 errata (exposure union, 15.3 not 15.6) is also exactly right.
3. **They are nevertheless not in the manuscript, and that is a deliberate scope decision, not a data
   problem.** `MANUSCRIPT.md:195` and `GAPS.md:92–110` (G-13/G-14) scope out R3/R4/R5/R6 for two reasons —
   n = 20 accuracy is not separable (p ≥ 0.219, reproduced) and the staged-extraction implementation is
   withheld. The cost and exposure figures are **not** accuracy claims and **are** exactly reproducible;
   the blocker is disclosure and power, not evidence.
4. **The candidate card is stale relative to the package.** `PAPER_CANDIDATES.md:81`, `:530` and `:1028`
   still headline "cuts context 15.3× and exposure to 0/20", but the packaged `MANUSCRIPT.md` asserts
   neither and says so explicitly. Either the card is re-titled to the batching note (the §G.2 "split it"
   recommendation) or the manuscript is re-scoped — as it stands the two documents disagree.
5. **What may not be asserted:** the corpus size (**1.83 MB**, measured 2.43 MB pinned / 2.75 MB live,
   with no byte record on disk), and any statement that the `gold` labels are mechanically derivable from
   the shipped corpus (§4). The **207/207** router figure may be asserted only as 120/120 from rows plus
   87 in-e2e decisions that have no per-decision rows — or dropped.

## 4. The one thing stored labels cannot carry: gold

The unit brief warned that the workspace recompute path "recomputes from stored labels and prints a clean
verdict even on trees whose values are already wrong". So I re-derived the **gold** labels from corpus
content under the rule `tasks.json` states ("gold derived mechanically: file contains answer substring;
harness dir excluded") and compared to the stored `gold` field:

```
base = …/repo/.worktrees/engine-a        re-derived 127  vs stored 120  (stored_only 12, rec_only 19)
base = /home/zer0null/Duval (live)       re-derived 130  vs stored 120  (stored_only 14, rec_only 24)
```

10 of the 12 stored-only pairs are `AGENTS.md`; the recomputed-only pairs span 15 files
(`tests/adapter-conformance.ts` ×2, `README.md` ×2, `docs/MISTAKES.md` ×2, `src/broker.ts` ×2, …).
**The stored labels do not reproduce from the shipped corpus snapshot under the stated rule.** Two readings
are possible and I cannot separate them from here: the harness applied a rule the note does not capture, or
the corpus files drifted between the 2026-09-30 run and the Oct-8 snapshot. Either way, the **120/1,800 =
6.7 % base rate is a stored-label fact**, and every precision/recall/F1 figure above inherits it. This does
not invalidate the batching comparison — all five configurations share the same labels — but it does mean
the numbers are *re-derived from recorded verdicts*, not *reproduced from the fixture*.

## 5. What is missing — raw-record inventory

**Exists and was read:**
- `gated-read-rows.jsonl` — 2,267,742 B, 9,260 rows, md5 `3aad1ae29e472ef9f5f54e179510faf5`, byte-identical
  in three copies (pinned engine-a tree, base repo tree, live target).
- `gated-read-summary.json` — aggregates for `gate`/`e2e`/`stage`/`router`/`fixture`/`models`; carries the
  `prompt_tok_total: null` hole for `gate16_none`, `gate90_none` and `gate90_minimal`.
- `tools/gated-read/tasks.json` — 20 tasks with question/answer/purpose; the 90-path corpus list; **no byte
  sizes**.
- `GATED_READ_2026.md` (run report + round-2 designs), `GATED_READ_PROVENANCE.md`,
  `STAGED_EXTRACTION_PROVENANCE.md`.
- `l1-head-to-head.jsonl` (380 rows, candidate #5) and `repro/encoder-crossover-190/` (candidate #3) —
  readable, but **not #7's material and not under the reported home**.

**Does not exist:**
- Any record of the corpus's **byte size** (the 1.83 MB claim has no source below the run report's prose).
- Per-decision rows for the **87 in-e2e router decisions** (only the 120 standalone ones are recorded).
- Any **harness/fixture script** that reproduces the `gold` field from content, or a corpus pinned by
  digest — `tasks.json` lists paths, not hashes, so the fixture is not reproducible as shipped.
- The round-2 experiments T1/T2/T3/T4/T5/T7/T6 (`GATED_READ_2026.md:277–338`) — designed, not run, and
  (correctly) not reported as results.

## 6. Limits of this check

- **No re-run.** Every verdict is arithmetic over stored rows. Model calls, harness behaviour and the
  batching template were not re-executed (`GAPS.md:40–45`, G-05: the template is not in the public
  material). Nothing here tests whether the rows describe what the harness actually did.
- **Stored labels.** As §4 shows, the `gold` field is not re-derivable from the shipped corpus; my
  P/R/F1 verdicts are verdicts about *record consistency*, not about the fixture.
- **File drift.** The pinned tree is an Oct-8 snapshot of a 2026-09-30 run; corpus bytes (and therefore the
  1.83 MB figure) cannot be reconstructed for the run date.
- **The 87 e2e router decisions** are taken on the run report's word; no row-level record exists to check
  them.
- I did not verify the *external* citations in `REFS.md` (e.g. the BoolQ 90.6 % → 72.8 % delta) — they are
  literature, not this run's raw records, and are outside the number-reverification question.

## 7. Verdict in one line

**Reproduced:** all 5 gate configurations, all R1/R2 headline numbers, the 15.3× cost ratio, the 0/20
exposure count, the R5 errata, R3's 0.292/17-of-20, R6's 12/20 and the p ≥ 0.219 power floor.
**Not reproduced:** corpus size 1.83 MB (measured 2.43 MB pinned / 2.75 MB live).
**Derived-not-recorded:** router 207/207 (120/120 from rows + 87 from prose).
**Stored-label only:** the 120-gold / 6.7 % base rate, and every P/R/F1 that depends on it.
The **15.3× and 0/20 headlines survive**, but they are correctly out of the manuscript's scope for
disclosure and power reasons — the candidate card, not the manuscript, is what still needs fixing.
