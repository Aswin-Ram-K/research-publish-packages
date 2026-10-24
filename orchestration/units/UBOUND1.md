# UBOUND1 — Boundary measurement: does per-case outcome data ship, and does the encoder-vs-decider gap vary with K?

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Type:** REPORT-ONLY measurement unit. No paper/manuscript/release file is edited. No model is trained or run.
**Bound:** 25 tool calls max; if no per-case outcome data found within the first 8 calls, STOP and report that as the primary finding.

## Purpose
The manuscript `papers/encoder-crossover-190/MANUSCRIPT.md` argues the published "small encoder beats a big LLM"
crossover is a prompted-baseline artefact: fine-tuned encoder head 0.3474 vs fine-tuned 4B decider 0.6789,
majority-class control 0.4526, shuffled-label 0.2316 (chance floor 0.2911), 190 sealed cases / 721 options.
The external counter-case (Benayas, Sicilia & Mora-Cantallops 2024, LRE 59(3):2007-2030, DOI
10.1007/s10579-024-09796-y) reports fine-tuned RoBERTa 94.27 macro-F1 > fine-tuned LLaMA2-7B 70.87 on
BANKING77 (77 classes), cited at `MANUSCRIPT.md:169-178` but not treated as a boundary case.
The paper's own §2.1 records an N-dependent table where the encoder wins at N=4 (AG News) and N=14 (DBPedia)
while losing/tying at N=2, and §2.2 records Weller et al. (ICLR'26) with a 400M encoder beating a 1B decoder
on 3-way MNLI under a matched recipe — so K alone does not separate the cases.

**Open question:** which variable separates the two outcomes — (a) data scale / training signal,
(b) per-case named-option decision vs fixed label space, (c) K / label-space size, (d) option-order/position effects?

## Tasks
1. Establish exactly what per-case data ships: file lists + byte sizes for `repro/encoder-crossover-190/results/`,
   `repro/encoder-crossover-190-SANITISED/results/`, `scratch/uneutral10/package/results/`,
   `scratch/urecut1/package/results/`; literal JSON schema for files carrying per-case data.
2. If per-case data exists: per-K (K=2:33, K=3:27, K=4:76, K=5:54 = 190 cases / 721 options) case counts,
   each fine-tuned encoder head's accuracy per K, the fine-tuned decider's accuracy per K if shipped,
   majority-class control per K, encoder-vs-decider gap per K. State whether gap grows/shrinks/flat with K,
   and whether encoders sit below majority-class at every K or only some.
3. What the released records can/cannot discriminate for candidates (a)-(d); what evidence would settle each,
   whether present, and if not what would have to be produced (re-analysis of stored labels vs re-training).
4. State what a short boundary paragraph could honestly assert — and what it could NOT. Conservative.
5. If a learning-curve/data-fraction experiment is the decisive test, report required infrastructure
   (harness files, GPU, checkpoints) and whether those exist locally — without running it.

## Hard constraints
- Report-only. Write only under declared paths. Never edit `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md`,
  `AVAILABILITY.md`, anything under `submission/`, or the build script.
- Do not retrain/fine-tune/run any model. Re-analysis of stored labels only.
- Do not attempt to refute the external paper.
- Quote literal command output for every number. Mark unverifiable items `UNVERIFIED`. Never upgrade
  "we were not able to locate" into "no such thing exists".
- `/home/zer0null/Duval` is STRICTLY READ-ONLY: no writes, no `git` state changes, no `git -C` at all.

## Write paths
- `strategy/BOUNDARY_ANALYSIS.md`
- `orchestration/units/UBOUND1.md`
- `orchestration/handoffs/UBOUND1.json`
- `scratch/ubound1/**`

## Status
IN PROGRESS — card persisted first, as required.
