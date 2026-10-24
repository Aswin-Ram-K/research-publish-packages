# UFIX18 — repair the last live citation of the deleted denylist gate

**Purpose (one):** correct the present-tense prose in `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` that still
locates the gate at the removed HARD/REVIEW pattern lists.

**Bound:** 10 tool calls, one file. Stop and report `partial` if the correction cannot be made inside
`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`.

**Declared write paths:** `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`, `scratch/ufix18/**`,
`orchestration/units/UFIX18.md`, `orchestration/handoffs/UFIX18.json`.

**Defect (re-derived, not copied):** `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md:39-40` states in the present
tense that the 24 HARD patterns at `UBUILD1.build.sh:613–636` and the 6 REVIEW patterns at `:640–647` *are*
the gate ("a leak detector"); `:589` uses the same removed names as the gate's scanner markers. Both pattern
heredocs were deleted by ULICENCE3. Re-read identity of the script: sha256
`a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, 1019 lines (confirmed by
`sha256sum` + `wc -l` before any write).

**Real gate, re-derived by `grep -n`:** positive vocabulary checker written by the heredoc beginning
`cat > "$DEST/gate.sh" <<'GATE_EOF'` (opens `:771`, terminator `:896`, `chmod +x` at `:897`); word lists
`vocabulary/english.txt` created `:691`, `vocabulary/code.txt` heredoc `:695`–`:743`, `vocabulary/public.txt`
heredoc `:748`–`:769`; invocation `bash "$DEST/gate.sh"` at `:1005` (block `:1003`–`:1017`).

**Rule for every number written:** each line number is emitted with its anchor name (heredoc opening line /
marker name), never bare — the citation has gone stale three times for want of this.

**Scope:** fix `:39-40` and `:589`; sweep the whole file for `613`/`636`/`640`/`647`/`PATTERNS_HARD`/
`PATTERNS_REVIEW` used as a current location. Do not restructure, renumber, or touch neighbouring `strategy/`
files (UFIX17 owns them).

**Report-back:** `orchestration/units/UFIX18.md` + `orchestration/handoffs/UFIX18.json`, seven keys, verbatim
before/after of each edit, sha256 + line count as read, raw sweep output.
