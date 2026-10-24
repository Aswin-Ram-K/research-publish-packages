# UVER17 — independent verification of `strategy/AUTHOR_DECISIONS.md`

**Unit:** UVER17 · **Date:** 2026-10-15 · **Replaces:** UVER16 (died ~1 min in; skeleton + `scratch/uver16/pc_copy.md`, no report).
**Purpose (one purpose):** re-check the 166-line, 7-decision brief UDECIDE1 produced and report where a human acting on it would be misled.
**Bound:** ≤20 tool calls. **Used: 11.** No extension of UVER16's work — its artifacts were read-only/ignored except as orientation.
**Independence:** did not write `strategy/AUTHOR_DECISIONS.md`; read the cited files directly and re-counted independently rather than trusting UDECIDE1 or UVER16.

## Write paths (declared)
`strategy/VERIFICATION_REPORT_17.md`, `orchestration/units/UVER17.md`, `orchestration/handoffs/UVER17.json`, `scratch/uver17/**`.

## Containment
- `/home/zer0null/Duval` read-only: **no git command run against it** (not even `--no-optional-locks`); file reads only.
- `scratch/uver16/**` untouched; nothing edited under `repro/`, `orchestration/units/UBUILD1.build.sh` or `AGENTS.md`.
- Nothing written outside the workspace; all writes inside declared paths.

## Checks and method
- A: ≈55 citation targets opened across 7 source files (≥18/≥4 required): `PAPER_CANDIDATES.md`, `LEAD_PACKAGE.md`, `NC1_FIX_PROPOSAL.md`, `NC1_UNBLOCK.md` (both NC1 docs read in full), `PUBLISH_PACKAGE_MANIFEST.md`, `REFS.md`, `VERIFICATION_REPORT_13.md`.
- B: re-did the D6 arithmetic from the raw enumeration; 12 − 6 = 6, supporting `NC1_FIX_PROPOSAL.md:140`, exposing `NC1_UNBLOCK.md:198` as internally inconsistent.
- C: settled licence/registration/release posture not re-opened.
- D: all seven blocked-lines name dependent work.
- E: both flagged disagreements real (`NC1_UNBLOCK.md:198` vs `NC1_FIX_PROPOSAL.md:140`; `LEAD_PACKAGE.md:296` vs `NC1_UNBLOCK.md:189`).
- F: 166 lines, 10 headings, 7 decision headings.
- Red→green: `scratch/uver17/cite_check.py` GREEN on a copy of `NC1_FIX_PROPOSAL.md:140`, RED after the scratch line was altered.

## Verdict
`partial` — one `contradicted` D7 detail (`REFS.md:66` uses `P:246`; `G:` is at `REFS.md:68`) and one `overstated` D6 wording ("enumerates" vs "states the count"). D6's disputed number resolves in the brief's favour.

Full evidence: `strategy/VERIFICATION_REPORT_17.md`.
