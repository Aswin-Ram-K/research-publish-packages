# UVER21 — independent verifier of UFIX24

**Status: complete (partial verdict).** Bound: 25 tool calls — used 25.

**Purpose.** Decide whether UFIX24 actually closed the cross-file citation-drift class over five
files, and say what is left. I wrote none of the work under verification.

**Write paths (only these):** `strategy/VERIFICATION_REPORT_21.md`,
`orchestration/units/UVER21.md`, `orchestration/handoffs/UVER21.json`, `scratch/uver21/**`.
No file under verification was edited; nothing was perturbed in place (the staled copy is a scratch copy).

**Result: `partial`.**
- Build-script derivation (12 anchors, 1,019 lines, sha256 `a2a1df17…`) — **CONFIRMED in full**, re-derived.
- Judgement call on `redact.py` `:204`–`:205` — **UFIX24 is RIGHT**; `:208 CASE_FIELDS`, `:206`–`:207` rationale, `:204` SAFE_KEYS tail, `:205 CASE_FIELD_RE`.
- Check (a) PUBLISH pointers outside the fence (`:333`–`:340`) — **PASS**.
- Check (b) no other MIT/5,662/`25aa637b…` assertion — **CONTRADICTED** (`VERIFICATION_REPORT_11.md:152,178,307`; `UCURATE1.md:128`–`:129`; stale tree `.ucurate1/pre/`).
- Check (c) residual `204-205` grep — **NOT REPRODUCED** (output polluted; see report §3c).
- The "Zero further stale citations" sentence — **0 occurrences in the five files**; 5 in `UFIX24.md:58,75,90,111,125`.
- RED→GREEN — **PASS** (green 21/21 rc=0; red 11/21, drifted=10, rc=1).

**Artifacts:** `scratch/uver21/check_citations.py`, `scratch/uver21/staled/…`.

**Blocker:** none. **Next hint:** add dated pointers at the three MIT sites; decide the fate of the
stale `.ucurate1/pre/` tree; re-run check (c) with `--include` scoping; reconcile UFIX24's per-file
counts against the `:N` census, especially `CODE_AGNOSTIC_RELEASE_POLICY.md` (773 tokens, 172-row table).
