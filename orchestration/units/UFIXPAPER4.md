# UFIXPAPER4 — De-leak internal working names from papers/encoder-crossover-190

**Purpose.** A project-internal working name (`UEXP`, `UEXP2` — names for two passes of the
second-labeller process in the author's build) ships in prose in `papers/encoder-crossover-190/MANUSCRIPT.md:605`
and in the generated `submission/main.tex:323`. Rewrite only the identification of those passes
using the paper's own existing vocabulary; keep the claim and every number identical.

**Declared write paths.**
- `papers/encoder-crossover-190/**`
- `orchestration/units/UFIXPAPER4.md`
- `orchestration/handoffs/UFIXPAPER4.json`
- `scratch/ufixpaper4/**`

**Hard bound:** 20 tool calls.

**Not to touch:** `tools/**` (except running `tools/package/md2tex.py` read-only), `scratch/uneutral10/**`,
any other paper, `/home/zer0null/Duval` (read-only, never git).

**Constraints.** No number may change. `main.tex` regenerated via converter, never hand-edited.
Citation bookkeeping invariant: same `\bibitem` count, same `\cite` distinct keys, 0 uncited, 0 unresolved.
Converter run twice must be byte-identical.

## Outcome (measured 2026-10-16)

**Label substitution applied** (systematic, not paraphrase): `UEXP` x7 -> `B`, `UEXP2` x1 -> `B2`,
`UREFS` x1 -> `our`, in `papers/encoder-crossover-190/MANUSCRIPT.md`; `B`/`B2` are the paper's own
reader labels (`MANUSCRIPT.md:578-581`: Reader B = `routeB-blind-model`, Reader B2 = `mimo-v2.6-flash`).
Load-bearing sentence `MANUSCRIPT.md:604-605` now: "... (**4/4** replicated). B / first reported this
convention and B2 shows it is not one model's quirk." Claim preserved exactly (two independent readers
agreed; not one model's quirk); no figure touched.

- `main.tex`: 83832 B / sha256 `90db2cd4e7fa6a63d4b91e2c0636c3879de54fc2a4e7f55fcbf2cce4197c9b86`
  -> 83804 B / sha256 `05bc111e1fe3d6cacd819e1faa3a3d75b68a51dd0dbdd995456a3ff9fb7858e4` (28 B = the
  exact length of the 9 substitutions). Converter run twice: `cmp` byte-identical.
- `diff` baseline->new `main.tex`: exactly two hunks, `322,325c322,325` and `345c345`; every other
  byte identical (so every digest, incl. the fixture-correctness projection, is unchanged).
- Citation guard: bibitems 13, `\cite` occurrences 23, distinct keys 13, uncited [] , unresolved []
  — identical before/after. Numeric multiset: 1320 tokens, sha256
  `7a406a4d9449240606686d94b376cf97cdf26090fc0e59c06d6aad1cfdb3f045`, identical before/after.
- `guard: R18 FAILED` is a static guard *label* (`tools/package/md2tex.py:115`, printed at
  `:577-578`), NOT a failure: `guard_citations` (`:443-456`) never raised. Reproduced on the pre-edit
  source, so pre-existing and untouched.
- Tarball rebuilt (converter does not build it): `tar -czf ... -C submission main.tex`,
  sha256 `f2e1e2913648934267927e01313ab0aadc2d260560729efb028e5c510a9abb31`, 28553 B, 1 member,
  extracted bytes == source == converter run 1.

## Internal-marker sweep (shipping path = `submission/main.tex`)

**Fixed (shipped unit names):** `UEXP` x8 (MANUSCRIPT.md `:597,604,605,609,612,615,619` /
main.tex `:322`x2, `:323`, `:324`x2, `:325`x2); `UEXP2` x1 (MANUSCRIPT.md `:605` / main.tex `:323`);
`UREFS` x1 (MANUSCRIPT.md `:667` / main.tex `:345`).

**Still ships, NOT rewritten (reported):**
- `UNSOURCED_RETAINED.md` — MANUSCRIPT.md `:725`, main.tex `:367`. **Naive-regex miss:** `_` is a word
  char, so `\bU[A-Z]+\b` fails. Not present in `repro/encoder-crossover-190` (43 files), so a reader
  cannot obtain it. Left as-is because de-identifying it would invent a label; it is a
  companion-record cross-reference, not a build identifier.
- `OPEN_QUESTIONS.md` main.tex `:351`; `CLAIMS.md`/`EVIDENCE_NOTES.md` main.tex `:373`;
  `docs/DECIDER_STACK_DECISION.md` main.tex `:345`; also REPORT.md, DECISION.md, QUESTIONS.md, REFS.md,
  CHECKLIST.md, CANDIDATES.md, EVIDENCE.md, PREREGISTRATION.md, ROBUSTNESS.md, NOTES.md, README.md,
  `experiments/LEARNINGS.md`, `strategy/PAPER_CANDIDATES.md`. All companion-record cross-references.
- **No `scratch/` or `orchestration/` path reaches `main.tex`.**

**Not in the shipping path (reported, not edited):** `UEXP`/`UEXP2` in `LIMITATIONS_UPDATE.md` and
`VERIFIER_CORRECTIONS.md`; `UREFS`, `UPAPER1c`, `UBIB1`, `UMERGE1`, `UFIX*`, `ULIC`, `UBEN1`,
`UREPRO`, `UTS1`, `UVER4` in `MANUSCRIPT_CHANGES.md`, `UNSOURCED_RETAINED.md`, `REFERENCES.bib`
comments, `CHECKLIST.md`, `CLAIMS.md`, `BUILD_NOTES.md`, `LICENSE_ANALYSIS.md`, `REFS_VERIFIED.md` —
historical records only.

**Not markers (ordinary text):** `UP` main.tex `:234`; `Use` main.tex `:443`; `Urchade`
main.tex `:457-458` (cited author's first name). No `B`/`B2` collision exists elsewhere in the paper.
