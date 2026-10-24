# UP2 — material outside `docs/research/` (coverage-gap survey)

**Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a` · **Date:** 2026-10-14
**Purpose (one):** determine whether paper-worthy candidates or load-bearing evidence exist **outside `docs/research/`**, and what they add. No re-inventory of `docs/research/`.
**Hard bound:** 50 tool calls. **Used 36.** Status: **done**.

## Write paths (declared, and the only ones touched)
`strategy/PAPER_CANDIDATES_SUPPLEMENT.md`, `orchestration/units/UP2.md`, `orchestration/handoffs/UP2.json`.

## Read-only compliance
The target `/home/zer0null/Duval` was **read only** — `grep`, `sed`, `head`, `find`, `wc`,
`git status --porcelain`. No write, no state-changing git, no hooks. `git status --porcelain` at survey
time showed **8 pre-existing dirty/untracked paths** (`AGENTS.md`, `docs/COMPACTION_LOG.md`,
`guidance/codex/COMPACTION_LOG.md`, `.ci-trunk.txt`, `.lane-j-scratch/`, `.relay/`, `.run-dashboard/`,
`docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`). None is UP2's. `.worktrees/` excluded.

## Result in one paragraph
Nothing outside `docs/research/` holds a **new experimental** candidate, and no second labeller,
external benchmark or independent corpus exists anywhere in the surveyed trees — a real negative
result. `docs/DECISION_LOG.md` (454 KB, 127 decisions) is **substrate, not a paper**: it strengthens
candidate #1's method and substrate (D-001/D-002/D-009/D-039 confirmed and quoted; **D-058** supplies a
*measured* determinism proof; **D-072** records that no decision had ever been recorded) and weakens its
system-novelty claim (**D-098** the readiness ledger was true and the engine did not exist; **D-099**
the first run produced no candidate). `docs/consolidation/SOURCE_VERIFICATION.md` — named in
`PAPER_CANDIDATES.md:9–11` and then **used by no candidate** — is the corpus's novelty instrument, and
its strongest entry (**V13**, arXiv 2608.03836) is a **competing measurement published in August 2026**:
the resume-contract failure candidate #1 presents as a gap has already been measured on five shipping
frameworks. Novelty verdict **mixed**: supported for the construction, undercut for the observation.
**One candidate is promoted — NC1, "Detectors that cannot fail"** (method + empirical, ranks between #6
and #7), built from `docs/MISTAKES.md` (19 classes, 12/3/4 detector status, count enforced by
`evals/prevention.ts`), **D-096** (three measured defects in a green invariant wall, incl.
`18 assertions, 0 failure(s)` and exit 0), the recorded **pre-registered VOID** invoked against the
authors' own 53.8 % headline (`EXPERIMENT_SM_PILOT.md:251`), withdrawn `EXIT=0` claims replaced by
durable artifacts (`docs/evidence/gates-2026-10-11/RUN.md:1–5`), and a measured evidence that the same
commit is CI-green or CI-red depending on which `node` is on PATH
(`WORKSTREAM_RECOVERY_PLAN.md:28–37`). One further sketch (the append-only design record) was
**considered and declined** as inflation. **Seven corrections** to `PAPER_CANDIDATES.md` filed.

## Evidence lines
- `docs/DECISION_LOG.md`: 6,497 lines, **127** `D-###` headings, 24 errata headings, 146 "measured".
- **D-001** `:8`, **D-002** `:28`, **D-009** `:155`, **D-039** `:1123` — all exist, all quoted in the supplement.
- **D-023** `:567` *"The unit of propagation is the StateCommit … Affirms D-001/D-002"* — D-001 is **refined**, not merely held.
- **D-058** `:1993` — two states differing only in `epoch` hashed `ee2852ce…` vs `5d34ff6b…`.
- **D-096** `:4368` — a structural invariant nobody asserted printed *"18 assertions, 0 failure(s)"* and exited 0; K0-03's word list missed **7 of 9** forbidden-set shapes.
- **D-098** `:4553` / **D-099** `:4594` — greens that did not mean what their reader thought.
- `SOURCE_VERIFICATION.md` **142 lines read in full**; **V13** `:35`, **V14** `:36`, **V16** `:43`, **V19** `:46`, **V24** `:51`, §3 `:83–105`, §4 `:119–134`.
- `docs/MISTAKES.md:386–388` — *"19 classes — 12 automated, 3 partial, 4 manual"*, count checked against the table by `evals/prevention.ts`.
- `docs/EXPERIMENT_SM_PILOT.md:251–263` — *"The run is therefore VOID as a DR1-B result"*, applied against the author's own 53.8 %.
- `docs/BUILD_PLAN.md:123–186` — seventh consecutive refusal stop, second identical → *"a REPRODUCIBLE DEATH"*.
- `WORKSTREAM_RECOVERY_PLAN.md:28–37` — `node v24.21.0 → EXIT=0`, `node v22.23.1 → EXIT=1`, same commit.

## Artifacts
- `strategy/PAPER_CANDIDATES_SUPPLEMENT.md` (coverage statement; 6 answers; NC1 + declined NC2; novelty-risk section; 7 corrections; limits)
- `orchestration/units/UP2.md` (this card)
- `orchestration/handoffs/UP2.json`

## Blocker
None.

## Next unit hint
A verifier should (a) re-read `docs/consolidation/SOURCE_VERIFICATION.md` and independently confirm the
V13 prior-art conflict against `PAPER_CANDIDATES.md:62–64`, (b) check the seven corrections' line
citations, and (c) decide NC1's rank slot against the §D M1–M14 note. Separately, route
`guidance/and1-handoff/AND1_RECON_HANDOFF.md` §0 (two measured credential-boundary holes in the DSH
harness) — it is out of scope for this unit and for the corpus.
