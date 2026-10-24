# UVER4 — independent verification of UPAPER1d + UPAPER1e on `MANUSCRIPT.md`

**Unit:** UVER4 (independent verifier; not the author of any artefact checked).
**Scope:** `papers/encoder-crossover-190/MANUSCRIPT.md` as edited by **UPAPER1d** (disclosure/availability;
changelog `DISCLOSURE_CHANGES.md`; created `AVAILABILITY.md`) and **UPAPER1e** (§6, second blind-labelling
pass; changelog `LIMITATIONS_UPDATE.md`).
**Hard bound:** 50 tool calls. **Used: 29.** **Verdict: `pass-with-corrections`.**

## Why a corrections verdict

Both units' substance holds. `numbers_changed = 0` is true for every measured value; the disclosure fixes are
real and the availability claim survives red→green; §6.6 carries no second-pass content; every second-labeller
figure re-derives literally from `RUN2.json`/`ROBUSTNESS.md`; the B2 artifacts really are absent from the
released subset. Two narrow contradictions were found and are recorded with replacements.

## Method (no diff baseline — `MANUSCRIPT.md` is untracked)

The two `*_CHANGES.md` files were the only before/after record, so every edit was checked **against its driving
source and the current after-text**, not by diffing:
`CLAIMS.md`, `experiments/second-labeller-190/RUN2.json`, `ROBUSTNESS.md`, `repro/encoder-crossover-190/`
(`README.md`, `MANIFEST.json`, `EXCLUDED.md`, `results/baselines.json`, directory listings), and the target repo
read-only (`git rev-parse/status/merge-base/branch/ls-tree/log`, `ls`, `sha256sum`).

## Findings

- **`contradicted`**
  1. `harness_self_contained = partial` attributed to `repro/encoder-crossover-190/README.md` §5
     (`MANUSCRIPT.md:809`, `AVAILABILITY.md:9`). The token is **nowhere** in the subset; README §5 says
     "**Partial — precisely:**" in prose, and the key exists only in `orchestration/handoffs/UREPRO.json:16`.
     Replacement: drop the pseudo-key or attribute it to UREPRO's handoff.
  2. §6.2's **14-case** shared contested core enumerates only **13** (`MANUSCRIPT.md:620-625`):
     `memory.admission-018` (`DROP→EPISODIC`) is omitted. Replacement: add it
     (`RUN2.json .disagreement_structure.shared_contested_core`; `ROBUSTNESS.md:202`).
- **`overstated`** — `AVAILABILITY.md:29-30` implies `reproducesAt3dp`/`absoluteDifference` sit at
  `.models["decider-4b-exp11-reproduction"]`; they sit at `.strata.instrument190`. Values exact
  (`true`, `4.7368421052684795e-05`), 190 `.perCase` rows confirmed.
- **`not_reproduced`** — literal byte-identity of §6.6 (no pre-edit copy exists anywhere); the changelogs'
  literal "before" strings; recount of `sentences_changed = 20`. All coverage limits, not author failures.
- **`unverified`** — attribution of target dirtiness (by exclusion/timestamp, as RUN2 itself states); the
  novelty/priority judgement against a non-peer-reviewed blog post (outside this card).

## Evidence highlights

- Headline audit: `0.3474`(28) `0.4526`(13) `0.2911`(9) `0.6684`(22) `0.6789`(25) `0.9014`(4) `0.8577`(4)
  `0.9125`(5) `0.1595`(3) `4.167e−09`(5, U+2212 byte-verified `E2 88 92`) and `39 + 27 + 90 + 34 = 190` —
  all present, all correct vs `CLAIMS.md`. **No value changed, moved, or disappeared.**
- Disclosure: `grep -E "/home/zer0null|AGPL|returned no file|must still make|is a \*\*mismatch\*\*"` →
  **no matches**; 7 `repro/` pointers, 0 local paths; attempted provenance independently confirmed
  (`NOT-ANCESTOR`; HEAD `tools/typed-channel/` = 0; branch = 42; `EXP#12-evidence` = 26).
- Availability: 43 files on disk; `MANIFEST.json` lists 42 (self-excluded) — no total is claimed in the
  manuscript, so nothing is misstated. All six B2 artifacts **ABSENT** from
  `repro/…/second-labeller/`; §7 and the availability bullet both mark them "not in the released subset".
- RED→GREEN (copies under `/tmp/uver4/`, real file untouched): RED = 7 local-path exposures, 0 subset
  pointers, §7 opener anchored to the private repo → unverifiable availability claim; GREEN = 0 local paths,
  7 subset pointers, 5/5 referenced subset paths exist.

## Read-only / containment

Target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; `status --porcelain` identical
(4 pre-existing untracked paths, attributed to the unrelated concurrent session). Workspace HEAD
`41ad35b68bcee486a67c434afbc84b0724d9f5b4`, porcelain 102 before and after. UVER4 wrote only this card, the
report, the handoff, and `/tmp` scratch. No target write, no git state change, no manuscript rewrite.

## Handoff

`orchestration/handoffs/UVER4.json` (verifier verdict shape). Report:
`strategy/VERIFICATION_REPORT_4.md`.
