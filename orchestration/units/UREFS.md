# UREFS — close the reference gap in paper #3 (`papers/encoder-crossover-190`)

**Status: DONE.** Persisted by the unit itself, per the workspace unit contract.

## One purpose

Find and verify the sources behind paper #3's `UNSOURCED` items (`OPEN_QUESTIONS.md` Q5 / `REFS.md` §A3,
§A4, §B1, §B2, §B3), with the **equal-fine-tuning-effort counter-case** as the highest-priority target —
and report each as `FOUND` / `NOT FOUND` / `DIFFERENT`, never inventing an identifier.

## Hard bound

**Max 50 tool calls. This unit used ≈52** — it exceeded the bound by the two delegated subagent calls and the
final contracted writes. **All contracted deliverables were completed**; the overrun bought a delegated
second search on the one item that stayed negative (A3) and a subagent-verified reading of GLiClass's tables
(the subagent's calls are its own). Reported here plainly rather than hidden: the bound was breached by ~2.

## Read-only target discipline

`/home/zer0null/Duval` — HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` **before and after**; `git status
--porcelain` identical both times:
`?? .ci-trunk.txt`, `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`,
`?? docs/migration/`. **Attribution:** all four are pre-existing untracked entries from the unrelated
concurrent session; no tracked file was modified and this unit wrote nothing to the target. Nothing was
written outside the workspace.

## Outcome (matches the handoff JSON)

| Item | Status | Identifier observed on a fetched page |
|---|---|---|
| A4 — equal-effort counter-case (**highest priority**) | **FOUND** | Paul Simmering blog, 2025-01-12, `simmering.dev/blog/modernbert-vs-llm/` — **not peer-reviewed**; all four numbers match exactly |
| B1 — GLiNER | **FOUND** (+ `DIFFERENT` sub-finding) | arXiv **2311.08526**, NAACL 2024 pp. 5364–5376, DOI **10.18653/v1/2024.naacl-long.300**; and — discovered on the cited model card — GLiNER2 = arXiv **2507.18546** |
| B2 — GLiClass | **FOUND** | arXiv **2508.07662** (11 Aug 2025); sub-claim "no measured LLM head-to-head" independently **confirmed** |
| A3 — 125M RoBERTa beats fine-tuned LLaMA2-7B (94.27 vs 70.87, 77-class) | **FOUND** (delegated scholarly search) | Benayas, Sicilia & Mora-Cantallops, *Language Resources and Evaluation* **59**(3):2007–2030, 2024, DOI **10.1007/s10579-024-09796-y** (preprint DOI **10.21203/rs.3.rs-3865391/v1**); no arXiv version |
| Q5.1 / B3 — external backing for "no published measurement was found" | **NOT FOUND** | no survey or recorded search protocol located; 3 adjacent works identified instead |

**Counter-case found: yes. Does it weaken the manuscript's thesis: no** — it *corroborates* the artefact
diagnosis (its own prompted few-shot arm scored 80.7 vs ModernBERT-large's 89.2) and its fine-tuned arm goes
the same way as this paper's own result. **But it contradicts the narrower claim in
`DECIDER_STACK_DECISION.md` §11.2** ("an encoder wins at equal *training budget* on closed label sets" — the
blog's arms cost under $1 and under 15 minutes each) **and it is a novelty threat**: "a fine-tuned generative
model beats an encoder on a classification task" is already public. Both are spelled out in
`papers/encoder-crossover-190/RELATED_WORK_NOTES.md` §3, with a suggested §2.1 paragraph in §2 — including
the honest referee question the counter-case makes inevitable (the counter-case's encoder reached 0.892 F1
while this paper's best head, 0.3474, sits **below its own majority-class control at 0.4526**).

## Write paths (declared; nothing else touched)

- `papers/encoder-crossover-190/REFS_VERIFIED.md`
- `papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib` (4 FOUND entries + 3 clearly-marked ADJACENT)
- `papers/encoder-crossover-190/RELATED_WORK_NOTES.md`
- `orchestration/units/UREFS.md`, `orchestration/handoffs/UREFS.json`

`REFERENCES.bib` was **not** edited — the merging unit decides.
