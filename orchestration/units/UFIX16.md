# UFIX16 — close the stale-gate-citation class by sweep

**Status: done** (2026-10-15). Bound: 20 tool calls.

## Purpose
UVER15 (`strategy/VERIFICATION_REPORT_15.md`) showed UFIX15 had fixed only the citations it was handed,
then declared the class closed. UFIX16 re-derives the class by workspace-wide sweep, judges each hit
live-vs-frozen, and fixes only the live ones.

## Script identity (read, not copied)
`orchestration/units/UBUILD1.build.sh` = sha256
`a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`, **1019 lines** — matches the reported
identity. Not edited (another unit's path); sha256 re-read identical after all edits.

## Current gate anchors — re-derived from the script, anchor + number
- Positive vocabulary checker written by the heredoc beginning
  `cat > "$DEST/gate.sh" <<'GATE_EOF'` — opens **:771**, closes `GATE_EOF` **:896**,
  `chmod +x "$DEST/gate.sh"` **:897** (so :771–:897).
- Vocabulary word lists: `vocabulary/english.txt` created **:691**; `code.txt` heredoc `CODE_VOCAB_EOF`
  **:695**–**:743**; `public.txt` heredoc `PUBLIC_VOCAB_EOF` **:748**–**:769**.
- Invocation `bash "$DEST/gate.sh"` — **:1005**, inside the gate block **:1003–:1017**.

## Fixes (all six write-path files)
| file:line | class | action |
|---|---|---|
| `strategy/REGEN_ASSESSMENT.md:23` | LIVE DEFECT | present-tense "the gate's own heredoc …:612-637" replaced with past-tense denylist + current anchor |
| `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md:296` | FROZEN (dated measurement) | dead ranges removed from the prose; dated 2026-10-15 supersession pointer + current anchor added inline |
| `strategy/PUBLISH_PACKAGE_MANIFEST.md:131` | LIVE stale figure | inline marker: 152 is a superseded denylist measurement; current figure 95,606; points at :255, :258–:259, :292–:296 |
| `orchestration/units/UCURATE1.md:36-37` | FROZEN, annotation merely beside | dead range removed, past tense kept, anchor + `:771`–`:897` given |
| `orchestration/units/UTOK1.md:35-36` | FROZEN, annotation merely beside | same |
| `experiments/token-substitution-test/REPORT.md:167-169` | FROZEN, annotation merely beside | same |

Post-edit `grep -rnE '612[-–]637|640[-–]647|423[-–]458'` over the six files = **0 hits** (line counts
preserved where possible, so §-internal numbering is undisturbed).

## Live defect OUTSIDE my write paths (not edited)
`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md:39-40`: "The 24 HARD patterns in
`orchestration/units/UBUILD1.build.sh:613–636` and the 6 REVIEW patterns at `:640–647` are a **leak
detector, not an inventory**" — present tense, no superseded marker, both ranges now dead. Also
`:589` (a shell comment naming `PATTERNS_HARD|PATTERNS_REVIEW|HARD_FILE`). A unit owning `strategy/`
must fix it; original text is preserved verbatim in the handoff.

## Left frozen (no rewrite, no pointer)
`orchestration/units/UFIX12.md`, `UVER11.md` (unit/verifier records); `orchestration/handoffs/UFIX12.json`,
`UFIX15.json`, `UVER15.json`, `UVER11.json` (machine records); `strategy/VERIFICATION_REPORT_11.md`,
`VERIFICATION_REPORT_15.md` (verifier reports that quote the defects); `scratch/**` (other units' scratch,
36 hits total); `.ucurate1/pre/research-publish-packages/gate.sh:35,60,63,70` (built artifact whose real
`PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs are content, not citations);
`experiments/token-substitution-test/gate-scan.sh:5,30,31,38` (the scanner's own heredoc identifiers).

See `orchestration/handoffs/UFIX16.json` for raw sweep output, per-directory exclusion counts and the
verbatim before/after of every changed region.
