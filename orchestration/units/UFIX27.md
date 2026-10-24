# UFIX27 - correct two record defects in UDTAG1's neutralisation record

**Status: done** (2026-10-16). Hard bound: 10 tool calls.

## Purpose
UVER24's verdict on UDTAG1 (content: pass-with-corrections) found two defects in UDTAG1's **record**:
(1) `counts.bytes_total` recorded as 3,009,198 where the manifest and disk say 3,008,830 (delta 368);
(2) `artifacts[]` names `scratch/udtag1/udtag1_facts.json`, which does not exist. Fix both under house
style - live statements corrected in place with the old value's context preserved; frozen records left
intact with a dated correction note appended - and enumerate every occurrence myself rather than trusting
the two named paths. The content verdict is NOT re-opened.

## Write paths (declared)
`strategy/DTAG_NEUTRALISATION.md`, `orchestration/handoffs/UDTAG1.json`,
`orchestration/units/UFIX27.md`, `orchestration/handoffs/UFIX27.json`, `scratch/ufix27/**`.
Read-only: everything else. `scratch/udtag1/tree-five` and `scratch/udtag1/tree-five-b` are NOT touched
(UVER24 verified those exact bytes). `/home/zer0null/Duval` never written, no git command run.

## Enumeration (whole workspace, my own grep)
Wrong total `3,009,198` occurs at exactly four distinct sites outside the read-only verifier records:
* `strategy/DTAG_NEUTRALISATION.md:8` - **live statement** (current emitted-tree summary in the strategy
  doc). Treatment: correct in place, old value preserved in a parenthetical.
* `orchestration/handoffs/UDTAG1.json:25` - **frozen record** (UDTAG1's dated historical handoff).
  Treatment: value left verbatim; dated correction note appended beside it.
* `orchestration/units/UVER24.md:37`, `orchestration/handoffs/UVER24.json:22,:30,:37`,
  `strategy/VERIFICATION_REPORT_23.md:151,:161,:214` - the verifier's own records, quoting the wrong
  value to identify the defect (correct in context) and on the do-not-touch list. No action.
* No occurrence anywhere under `scratch/udtag1/tree-five`, `scratch/udtag1/tree-five-b`, or any manifest.

Extra finding, same class, beyond the named defect: `strategy/DTAG_NEUTRALISATION.md:6` states the 44
payload files total **3,008,378** bytes. Disk: payload 2,986,505 in both base and emitted tree; 3,008,378
is the base *tree* total including its 21,873-byte manifest. Live statement -> corrected in place.

## Defect 2
`scratch/udtag1/` actually contains `dtag_one.py`, `regen_manifest.py`, `check_emitted.py`, `logs_build.txt`,
`logs/` (census before/after + seed0, census diffs, compare.diff, compileall.out, recompute before/after),
`base-copy/`, `run-base/`, `run-five/`, `run-b/`, `tree-five/`, `tree-five-b/`. No file anywhere in the
workspace is named `*facts*` (only `.venv` internals and `state/logs/U8.75_ledger_facts.txt`, both unrelated),
and `orchestration/units/UDTAG1.md` never mentions "facts" - so no real file of that name was meant.
`artifacts[]` entry replaced with the real fact-bearing output `scratch/udtag1/logs/`, per the brief's
preference for naming the real artifact over deleting the entry.

## Method / guards
Every in-place edit asserts the old string occurs exactly once immediately before writing. The handoff is
edited textually (not re-serialised) to keep the frozen bytes verbatim, then re-parsed with
`python3 -c 'import json;json.load(open(...))'`.
