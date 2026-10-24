# UFIXDEP3 — two documentation corrections in `strategy/DEPOSIT_ARCHIVE.md`

**Purpose (one):** correct a wrong documented input path and add a dated inline supersession note,
in a single file. Documentation only.

**Hard bound:** 8 tool calls. If the input guard cannot be exercised, STOP and report that rather
than asserting it works.

**Write paths (nothing else):** `strategy/DEPOSIT_ARCHIVE.md`, `scratch/ufixdep3/**`,
`orchestration/units/UFIXDEP3.md`, `orchestration/handoffs/UFIXDEP3.json`.

**Inputs read:** `strategy/DEPOSIT_ARCHIVE.md`, `strategy/VERIFICATION_REPORT_DEPOSIT_2.md`,
`scratch/ufixman1/build_archive.sh`.

## Defect (from VDEPOSIT2, `strategy/VERIFICATION_REPORT_DEPOSIT_2.md`)
- `strategy/DEPOSIT_ARCHIVE.md:17` names `scratch/uzenodo2/run2/README_DEPOSIT.md` (6,396 B,
  sha256 `baf13459…`) as the build's README input. That is the **superseded** copy. The build
  actually reads `papers/encoder-crossover-190/released/README_DEPOSIT.md` (10,477 B,
  sha256 `503751f1…`). A reader following the doc points the build at the wrong file and it fails
  its own input guard.
- `strategy/DEPOSIT_ARCHIVE.md:42` carries a present-tense sentence about a directory that no
  longer exists, with no inline supersession date.

## Tasks
1. Read the three inputs.
2. Fix `:17` to name the path the script actually reads; add a dated inline supersession note at
   `:42`; assert each before-string occurs exactly once before writing.
3. Prove the fix self-provingly: confirm the corrected path is the path
   `scratch/ufixman1/build_archive.sh` reads, and run the input guard both ways — accept the
   corrected path, reject the superseded one — reporting literal command + output.
4. Report before/after byte size and sha256 of `strategy/DEPOSIT_ARCHIVE.md`.
5. Confirm no other file changed; archive, package and papers byte-unchanged.

## Do NOT
Edit the build script, the archive, the package, any paper, or `strategy/DEPOSIT_METADATA.md`.
Do not rebuild the archive. No network API.

## Status
in_progress — card persisted; reading inputs next.
