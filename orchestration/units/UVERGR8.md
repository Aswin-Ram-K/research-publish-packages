# UVERGR8 — independent verifier for UFIXGR8 (paper #7 pointer/prose fix)

**Purpose.** Re-check UFIXGR8's claims; do not redo or improve its work. Did not author the files under review.

**Subject of review.** `papers/gated-read-batching/MANUSCRIPT.md`, `papers/gated-read-batching/submission/main.tex`,
tarball payload; author card `orchestration/units/UFIXGR8.md`, handoff `orchestration/handoffs/UFIXGR8.json`.

**Read-only.** `/home/zer0null/Duval` strictly read-only, NO git command against it.

**Write paths (only these).**
- strategy/VERIFICATION_REPORT_GR8.md
- orchestration/units/UVERGR8.md
- orchestration/handoffs/UVERGR8.json
- scratch/uvergr8/**

**Hard bound.** 12 tool calls. Findings written to the report as I go so a death is still readable from disk.

**Checks.**
1. Independent pointer sweep of MANUSCRIPT.md + main.tex (CLAIMS.md, GAPS.md, REFS.md, siblings, bare `scratch/`); open all 5 reported lines.
2. `MANUSCRIPT.md:3` neutral scope; no `draft|to be supplied|status:` anywhere; title/abstract intact.
3. Two UFIXGR7 markers (~MANUSCRIPT.md:82/:84) keep date + unit id + correction content.
4. Regeneration: copy live main.tex aside, run scratch/uprep7/md2tex.py, compare, restore byte-identically with digest proof; two runs identical; 13 bibitem / 14 cite / 13 distinct keys / 0 uncited / 0 unresolved / 1 author / 0 non-ASCII / balanced begin-end; tar member check; verify both reported digests.
5. Number invariance vs any pre-edit copy; else cross-check numbers in the 5 reworded sentences against CLAIMS.md and the manuscript.
6. Verdict on judgement call (a) converter rule S1 firing on the Scope line; (b) minimal rewording of GAPS.md inside the dated marker.
7. Red→green: on a `scratch/uvergr8/` copy, inject one bare-filename pointer; check fails on the copy, passes on the real file.

**Status: COMPLETE — overall verdict PASS.** All 7 checks ran; every UFIXGR8 claim reproduced
(0 not_reproduced, 0 overstated). Report: `strategy/VERIFICATION_REPORT_GR8.md`. Handoff:
`orchestration/handoffs/UVERGR8.json` (valid JSON, re-parsed). Two limits in `unverified`: no TeX
toolchain so no compile; no independent mtime sweep of UFIXGR8's declared write paths. Live
`main.tex` was rewritten by the converter during the regeneration check and restored byte-identically
(sha256 `a5d32dd7…` re-proven; all 6 `submission/` digests OK). `/home/zer0null/Duval` untouched; no git.
