# HOST-SCOUT-1 — read-only scout for leftover paper-ready work

**Unit:** HOST-SCOUT-1 · **Started/completed:** 2026-10-23 23:02–23:26 (America/Chicago)
**Mode:** READ-ONLY. No writes outside `/home/zer0null/reserach extarctor`. No git run at all (no target
git verb, not even lock-free status — nothing needed it). No servers, no builds, no model/network requests.
**Budget:** ≤40 tool calls / 20 min → **25 bash calls used**, ~24 min wall.

## Scope

Three projects, the question being: *what is already measured, with real numbers, and not yet in any paper?*

1. `/home/zer0null/Duval` — `docs/research/` (89 entries, 7 `EXP#*-evidence/` dirs, `FINDINGS_REGISTER.md` 82 KB, `PAPER_DERIVATION.md` 46 KB, `experiments/` 50 docs).
2. `/home/zer0null/publish-present-compete` — `publish/` (5 audit docs + 2 drafts + repro), `data/`, `CLAIMS.tsv`/`SOURCES.tsv`, `STATUS.md`.
3. `/home/zer0null/TRUTH` — `opinion-publishing-outlets-2026.md`, `outlets.csv`, `out/`, `mailsweep/`, `PLATFORM-PLAYBOOK-2026-10-22.md`.

## Method

Directory listings first (cheap, no content); then the register/paper cross-check (`grep` for `EXP#11|EXP#43|
EXP#45|EXP#46|EXP#47|EXP#48` and for `speculat|max-num-seqs|MTP|selective|AUROC` across `papers/`);
then **raw-evidence verification** — every headline number below was re-read from the row file with
`python3 -c` JSON parsing (read-only), not taken from prose. Papers already extant and therefore *not*
leftover: `papers/replay-record-not-decision`, `papers/gated-read-batching`,
`papers/encoder-crossover-190`, `papers/context-cache` (the last is live: 726-line manuscript, 264-line
claims ledger, 572-line gaps file, mtimes 2026-10-23).

---

## Project 1 — Duval: LEFTOVER, and one candidate is strong

### A. EXP#11 option-set revision / self-refinement degradation — **best candidate on the machine**

*Docs:* `docs/research/experiments/EXP#11-per-model-option-revision.md`;
`docs/research/SELF_REFINEMENT_DEGRADATION_2026.md` (50 KB literature record, §1 measurements, §5.2 external
comparisons, §6 "no external match", §7 R1/R3, §8 unfetchable sources);
`docs/research/EXTERNAL_EVIDENCE_2026-10-07.md` (159 KB); 17 findings **F-EXP11-01…17** in
`docs/research/FINDINGS_REGISTER.md:30-70`.

**Verified from raw rows (my own parse, not the register):**
`docs/research/EXP#11-evidence/decider-dashboard.jsonl`, `…/imajev-dashboard.jsonl`
- `haAccuracy` (revised stratum, decider-4b): 0.665 → 0.630 over 7 rounds = **−3.5 points**; escalator's own
  accuracy 0.8974/0.90/0.85/1.0/0.925/0.8378.
- `haAccuracy` (imajev-4b): 0.645 → 0.580 over 6 rounds = **−6.5 points**, trough **0.570** at r4 (−7.5).
- `hbAccuracy` (never-revised control stratum): **0.6700 in all 13 dashboard rows** (7 decider + 6 imajev).
- Row files: `decider-rows.jsonl` = **4,090 lines**; imajev dashboard `rows` Σ = **3,690**.
- `ANSWER ∉ option set` = 0.00 % at every round (F-EXP11-11) — the defect that justified the design does
  not exist at baseline; option sets grew 2 → 8 (F-EXP11-03); `missing_option` was the only edit kind ever
  admitted (F-EXP11-05); AUROC(confidence→error) **0.708–0.715** vs published verbalised-confidence
  0.522–0.605 (F-EXP11-07); paired exact test **7/7 discordant, p = 0.0156** (F-EXP11-14, caveat: does not
  survive Bonferroni at 0.0125).

**What is missing:** a manuscript — the register is an index, not a paper; no claims ledger, no recompute
script, no venue choice. Two *cheap* verification repairs before writing (0 provider requests):
1. F-EXP11-02 says "twelve measurements"; the dashboards carry **13** rows at 0.6700 (7 + 6).
2. F-EXP11-11 says **3,590** imajev rows; the dashboard `rows` fields sum to **3,690**.
Also F-EXP11-12's "recoverable headroom grew" figure is not in the dashboard and must be recomputed from
`live2-decider/rows.jsonl` before it is quoted.
**Readiness: one batch** (write-up + claims ledger + the two recounts). **Venue:** TMLR / a workshop on
self-refinement & evaluation methodology; the never-revised control stratum and the 2→8 option-count
range are both claimed *novel* (SELF_REFINEMENT §6–7) — that is the contribution, not "self-refinement
hurts", which is public (Huang et al. ICLR 2024, cited in doc §2.1).
**Risk:** the effect is small and the paper's honest core is a *correction* story (F-EXP11-08 falsifies an
earlier claim); a reviewer will read "no revision round improved either model, n = 2 models, one 4B size
class" as narrow. The control stratum is what makes it defensible.

### B. EXP#46 serving-config Pareto / MTP speculation — **measured, self-declared VOID as a Pareto claim**

*Docs:* `docs/research/experiments/EXP#46-serving-config-pareto.md`;
`FINDINGS_REGISTER.md` §EXP#46 (F-EXP46-01…06); evidence `docs/research/EXP#46-evidence/` (`sweep.jsonl`,
`analysis.json`, `RUN_LOG`, `prefix-cache-probe.json`, `metrics/`, `inspect/`, `clock-*.txt`).
**Verified from `sweep.jsonl` (16 rows = 4 arms × c∈{1,2,4,8}):**
- `tok_s_aggregate`, V-DEP (MTP on) vs V-S6 (spec off): **32.67/62.82/117.45/148.05** vs
  **22.16/45.28/85.12/108.49** → ratios **1.474 / 1.387 / 1.380 / 1.365**.
- `--max-num-seqs` 8 vs 4 at c=8: **148.16 vs 85.27 tok/s = 1.738×** (register: 1.74×).
- Non-determinism: 6 of 16 rows `deterministic=False`, **all** in speculation-off arms (V-DEP is True at
  every c).
- `resolution: "VOID"`, `pareto_claims: []`, `incomplete_comparisons: 16`; **12 SGLang points never ran**
  (Launcher `DockerCmd` TypeError), `--max-num-seqs` 4-vs-6 at c=4 never measured (F-EXP46-06 open), and
  the prefix-cache gauge was never shown able to report a non-zero hit (F-EXP46-03).
**Readiness: one batch** (the missing SGLang arms + the c=4 4-vs-6 cell + a calibrated cache gauge) or
ship now as a **measurement note** with the VOID status stated. **Venue:** systems workshop (MLSys/NSDI
workshop on serving), or an engineering report. **Risk:** "vendor advice to disable speculation is
contradicted" holds for one engine, one model, one quantisation, one greedy 64-token workload, one GB10
box — the doc already states that width, which is also the ceiling.

### C. EXP#45 selective-risk reformulation — closed, offline, negative/power result

*Docs:* `docs/research/experiments/EXP#45-selective-risk-reformulation.md`,
`docs/research/EXP#45-evidence/{REPORT.md,analysis.json,rows.jsonl}`, register §EXP#45.
**Verified from `analysis.json`:** `pooled.raw_accuracy` **0.6316**; at the 97.5 % per-decision target the
cross-fitted isotonic gate covers **0.0158** (handled accuracy 1.000) and the raw-confidence gate **0.0**;
`arms.b_learned_gate.composed_accuracy` **0.6684** (escalation 0.9842) vs
`arms.c_fixed_rule_t075.composed_accuracy` **0.6789** (escalation 0.6737); `per_kind` has 7 types;
`types_reaching_registered_mde` vs `types_below…` split at n = 22–30.
**The interesting claim (input numbers, *not* re-derived by this lane):** same signal quality (AUROC
0.708–0.715 here vs 0.707 published) gives **11.5–16 %** handled under a per-decision 97.5 % target but
**41–49 %** under an aggregate tolerance — the *constraint formulation* is the lever. Those 41–49 % figures
come from `docs/DECIDER_TIER.md` and would have to be recomputed in-lane before they can be a paper claim.
**Readiness: one batch** (compute the aggregate-tolerance arm; otherwise the paper is "we could not
evaluate this at n = 22–30"). **Venue:** short note / workshop. **Risk:** as written it is a power
analysis and a negative result; defensible, low excitement.

### D. `PAPER_DERIVATION.md` — a complete 8-experiment working paper with no submission package

`docs/research/PAPER_DERIVATION.md` (46 KB) has Abstract, §1 Intro, §2 Related work, §3 Method, §4
Experiments (8 experiments), §5 Discussion, §6 Limitations, §7 Artefacts, §8 Reproducing — "eight
experiments complete, all emerged" (header + §4, lines 1–25 and 155–533). **No package exists** for it in
`papers/` (only the four named above). **Readiness:** one batch to split scope and package, but hand the
EXP#7 overlap (it is the replay paper's source) to whoever owns `papers/replay-record-not-decision`, and
note the file is stale (2026-10-04) against the register (2026-10-19). **Risk:** broad programme paper
whose individual results are now individually published — the split is the work.

### E. Everything else in Duval `docs/research/` — **checked, not candidates**

`SCOPE_ENFORCEMENT_2026.md` ("a promotion record, not an experiment"); `TEARDOWN_TIMEOUT_2026.md`
(research note ending in a recommendation, no numbers of its own); `LONG_HORIZON_EVALS_2026.md` (107 KB
literature record, deliberately `[UNVERIFIED]`-labelled); `TIER2_MODEL_SURVEY_2026-10-10.md` (SURVEY, "no
experiment"); `AGENT_HARNESSES_2026.md`, `GX10_COMPANION_SURFACE_2026.md`, `TIER2_SERVING_EVIDENCE_2026-10-10.md`
(design/evidence bases already feeding `docs/serving-options/` and `papers/context-cache`);
`BIOMAP/` (proposal + literature sweeps, "no decision"); `EXP#11-evidence`, `EXP#43/45/46/47/48-evidence` —
EXP#43/47/48 are already *inside* the live context-cache package (F-EXP47-05 explicitly corrects EXP#43
there), so they are **not** leftovers.

---

## Project 2 — publish-present-compete: two **finished drafts**, already marked publishable

### F. `D1-node-zstd-multiframe` — the corpus-census finding (strongest here)

*Paths:* `publish/drafts/D1-node-zstd-multiframe.md` (marked **PUBLISHABLE** in `publish/README.md`),
`publish/repro/zstd-multiframe.mjs`, `publish/repro/corpus-census.mjs`,
`publish/corpus-census-2026-10-07.json` (marked **INTERNAL** — carries an absolute home path in `root`;
strip before publishing).
**Numbers (read from the census JSON and the draft's version matrix):** 4,986 logs / 4,982 session dirs,
**3,086,067,541 bytes** compressed, **6,715,736 frames**, `records_first_frame_only` 4,985,
`silently_lost_records` **11,757,139**, `silent_loss_pct` **99.96**, one `frameParameter_windowTooLarge`
failure. Version matrix measured on released binaries: Node **v22.23.3 and v24.21.0** return `"ONE"` from a
3-frame stream (both sync and stream APIs); **v26.10.0** returns `"ONETWOTHREE"`; already fixed on `main`,
**not backported** (so the draft is correctly a comment on an existing issue, not a new report).
**What is missing:** essentially nothing for its own intended venue — it has a review checklist in the
draft, reproductions, and a re-scoping note. **Readiness: ready now** as an upstream comment + blog post.
**Venue:** engineering blog / upstream issue thread. **Not** a research venue: n = 1 machine, one
corpus, and the phenomenon is upstream's bug.
**Risk:** the census is agent-log-shaped and machine-specific; the 99.96 % figure is only credible
*with* the version matrix, which is why the two artifacts must ship together.

### G. `D2-failure-autopsy` — narrative method piece, ready now

*Path:* `publish/drafts/D2-failure-autopsy.md` ("The Decompressor Was Innocent: Five Claims One
Instrument Falsified"). Five of the project's own claims falsified by its own measurement passes; each
produced a confident number (0 % coverage, "285 distinct sessions", "1 distinct catalog value", **1.08 GB
RSS after 54,385 frames** — the last one measured false on Node v22.22.1 with forced GC between
checkpoints); the reusable residue is **four assertions made against real data**. **Readiness: ready now**
(blog/technical essay). **Venue:** engineering blog, not a paper. **Risk:** one project, one machine, a few
weeks — the draft says so itself.
*Also present:* `publish/01-findings-inventory.md` is a systematic **22-candidate** findings inventory
(`F-1…F-22`) with dispositions and a coverage check against `STATUS.md`'s 14 build findings; `03-disclosure-boundary.md`,
`04-venue-and-sequence.md`, `05-repo-readiness.md` are internal audits. `CLAIMS.tsv`/`SOURCES.tsv`:
**82 sources × 131 claims**, validated by `validate-ledgers.py` (exit 0) — a real ledger, but it is the
app's own provenance store, not a study.
**Verdict for this repo:** it is a research-ready *publishing pipeline*, not a research paper. Two
artifacts (F, G) are finished and unpublished; nothing else here is a paper.

---

## Project 3 — TRUTH: **operational, not research** (with one curated dataset)

*Checked:* `opinion-publishing-outlets-2026.md` (field guide, "Verified: 21 Oct 2026", ✅-marks on
re-checked entries), `outlets.csv` (83 lines ≈ 82 outlet rows; columns platform/category/reach/
free_to_post/api_write/auth/quota/gate/notes/verified; e.g. X "$0.015/post; $0.20/post with URL … 3M
reads/mo", Bluesky "1,666 posts/hr, 11,666/day"), `PLATFORM-PLAYBOOK-2026-10-22.md` (mail-history audit,
account inventory), `out/` (7 batch CSVs, 2,270 contact rows, `exec_journal.jsonl` **948 records**),
`mailsweep/` (plugin + `state/sweep.db`), `INBOX_DECLUTTER_REPORT.md`, `MAIL-TRIAGE-2026-10-21.md`,
`PUBLIC-PRESENCE-DASHBOARD-PLAN.md`.
**Response-rate data: none found.** A grep for `response rate|reply rate|reply_rate` over `*.md/*.csv/*.json`
returned **zero files**; the journal records batch *execution* (account, stage, batch, n, uids), not
outcomes. **Verdict: operational.** The only artifact with research-grade shape is the outlet guide/CSV —
a verified cross-platform costing of free write access (API, quota, approval gate, price) as of
2026-10-21. It is a **technical report / living dataset** at best; there is no study design, no outcome
measurement, no reproducible analysis script. Do not dress it as a paper.

---

## Ranked answer

| # | Candidate | Where | Established (verified) | Missing | Readiness |
|---|---|---|---|---|---|
| 1 | EXP#11 option-revision degradation | Duval | −3.5 / −6.5 pts, control 0.6700 ×13, p=0.0156, 4,090+3,690 rows | manuscript + 2 recounts + headroom recompute | **one batch** |
| 2 | D1 zstd multiframe + census | publish-present-compete | 99.96 % / 11,757,139 records, 4,986 files, version matrix | strip `root`, ship | **ready now** (blog/issue) |
| 3 | EXP#46 serving config | Duval | 1.474/1.387/1.380/1.365×, 1.738× at c=8, 16 rows | SGLang arms, c=4 4-vs-6, calibrated gauge | one batch |
| 4 | EXP#45 selective risk | Duval | 1.58 % coverage @97.5 %, 0.6684 vs 0.6789 | aggregate-tolerance arm computed | one batch |
| 5 | D2 failure autopsy | publish-present-compete | 5 falsified claims, 1.08 GB RSS refuted | none | **ready now** (blog) |
| 6 | PAPER_DERIVATION | Duval | 8 experiments, full structure | scope split vs replay paper, refresh | one batch+ |
| 7 | TRUTH outlet guide | TRUTH | 82 outlets verified 2026-10-21 | any outcome measurement | not a paper |

**Nothing in TRUTH is paper-ready. In publish-present-compete, two drafts are finished but belong to a
blog, not a venue. Duval is the only project with genuine leftover research value — EXP#11 first, and it
needs zero new experiments.**

## Discrepancies recorded (must be fixed before EXP#11 becomes a paper)

1. F-EXP11-02: "twelve measurements" for the 0.6700 control — `decider-dashboard.jsonl` (7 rows) +
   `imajev-dashboard.jsonl` (6 rows) = **13** rows, every one 0.6700.
2. F-EXP11-11: "3,590 imajev rows" — the dashboard `rows` fields sum to **3,690**.
3. `SELF_REFINEMENT_DEGRADATION_2026.md` §1 still prints imajev "**−7.50** (4 revisions)"; the register's
   errata says **−6.50 over six revisions** (verified: 0.645 → 0.580, week-4 trough 0.570). The literature
   record needs the errata carried into §1 or a paper will quote the stale figure.

## Hygiene

No write outside the workspace. No git command was executed anywhere (none was needed: every claim above
came from reading files or parsing JSON). No server, build, install, network or model request. Only reads
plus `python3 -c` JSON parsing and `wc -l`.
