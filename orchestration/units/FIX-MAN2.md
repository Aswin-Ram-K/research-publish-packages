# FIX-MAN2 — repair the abstract sentence, refresh RUN.json's stale block, re-run the two recon scripts

**Card.** Automated task-board execution, 2026-10-23. No human present.

## Objective

Three repairs the chain left open after V-FINAL:

1. **Abstract sentence.** MANUSCRIPT.md:10-11 said *"two independently implemented prompt
   renderers emitted byte-identical prompts"*. `u5_recon.py` compares `RenderPolicy.POINTER`
   against `RenderPolicy.NAIVE_APPEND` inside one library (`resextract.context`), reached
   through one `build_cell(..., policy=...)` call — that is one appender honouring two mode
   flags, not two independent implementations. The sentence overclaimed the evidence.
2. **RUN.json stale block.** `request_totals` was the U7 snapshot (4573 / 4349) and by now
   omitted G1 (264), G5 (192) and M4 (327) entirely; `synthesis_recompute` still carried
   `claims 52 / claims_matching 52 / script_sha256 6fd5bec1…`, while the script on disk
   reported 59 claims checked at sha256 `4845bd8d…`.
3. **The two recon scripts** named in `verification.external_commands` had never been
   re-executed (V-FINAL's own `unverified[0]`).

## Hard bound

≤30 tool calls; stop and report if the attribution guard could not be shown to behave on the
repaired sentence.

## Write paths

- `papers/context-cache/MANUSCRIPT.md`
- `papers/context-cache/CLAIMS.md` (guard-defect fix, see below)
- `papers/context-cache/RUN.json`
- `orchestration/units/FIX-MAN2.md`
- `orchestration/handoffs/FIX-MAN2.json`

No cell data, no `recompute.py`, no target repo touched.

## Findings beyond the card

- **verify_package.py was FAILING, not passing.** The bash fence in CLAIMS.md:11-17 carried
  `#`-comments, and both parsers treat an ATX heading (`re.match(r"#{1,6}\s", …)`) as a
  section change — inside a code fence. The source-key table therefore had no heading, and all
  25 of its rows were reported as "unrecognised row, invisible to the claim census",
  `exit=1`. Fixed on the CLAIMS.md side (bash `::` comments; an explicit
  `### Source rows and digests` heading) rather than by weakening either parser.
- **C63 is not a live claim.** A `COVERAGE GUARD FAIL no runner for 1 claim(s): C63` line
  appeared once mid-pass and did not reproduce across four later runs; V-FINAL2 records
  `C63`/planted rows as its own red tests, restored afterwards. Treated as a transient
  planted row, not a real defect.
- **The repaired sentence is not guarded.** Reverting MANUSCRIPT.md to the overclaim gives
  `11 passed` — the attribution guard pins the G5 and M4 sentences only. Recorded as a gap,
  not claimed as red→green.

## Result

`partial`: all three repairs landed and the gates are green, but no guard pins the renderer
sentence, so the correction can silently regress.
