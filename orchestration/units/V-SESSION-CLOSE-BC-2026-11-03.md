# V-SESSION-CLOSE-BC-2026-11-03 — independent verification of the 2026-11-03 research close-out

**Status:** verdict **`pass`** (one minor documentation defect; no overclaim, no stale number, no live run).
**Date:** 2026-11-04. **Bound:** 30 tool calls (used 26, including this card and its handoff).
**Posture:** read-only on the seven close-out files; this unit wrote only this card and
`orchestration/handoffs/V-SESSION-CLOSE-BC-2026-11-03.json` (plus `/tmp/docred-vsess/`). No live request,
no `curl`, no `run_longrun`, no target-repo write, no build.

## Target and method

The seven paths declared by `SESSION-CLOSE-BC-2026-11-03`: `journal/2026-11-03.md`, `journal/INDEX.md`,
`docs/STATE.md`, `orchestration/STATUS.md`, `orchestration/VERDICTS.md`,
`orchestration/units/SESSION-CLOSE-BC-2026-11-03.md`,
`orchestration/handoffs/SESSION-CLOSE-BC-2026-11-03.json`.

Method: sha256 + mtime of all seven at start and at end; full read of the journal entry, the unit card, the
handoff, `docs/STATE.md` (all 302 lines), and the `orchestration/STATUS.md` /
`orchestration/VERDICTS.md` batch sections; `git diff` of the three tracked changed files to check history
was extended, not rewritten; every headline number cross-read against
`orchestration/handoffs/V-CONSONANCE-BC-REPORT-RECHECK.json` and `…-EVAL-RECHECK.json`; both gate
commands re-run; the doc guard's journal-row check exercised red→green in a `/tmp` copy.

## Checks

| # | Check | Result |
|---|---|---|
| 1 | Seven files read; sha256/mtime at start = at end | **pass** — hashes identical before/after (below); no deliverable changed mid-verification |
| 2 | Accuracy vs the two recheck handoffs | **pass** — both rechecks `overall: pass` (`tool_calls` 16/20 and 25/20); journal says PASS, 0 live endpoint/model requests, no Rust/omp build, E2 `123` descriptive / `369` adjudicable / `450` with the 12-checkpoint fixture, comparative `7,560` vs `1,729` `UNFUNDED`, `BOUNDARY-PREREG` separate; stale `6,300`/`3.64×` appears only as the *corrected* pre-fix value in a `→` construction and in the "residual, recorded not edited" block |
| 3 | Pickup | **pass** — `docs/STATE.md` `Last updated: 2026-11-04` (= newest journal 2026-11-03, so doc_check's stale-page rule holds); §0, §2a (deliverables/verdicts table, established vs proposed, exact E1/E2 decision, four blockers), §4 row, §6 item 7, §8 all point at the two deliverables, the PASS verdicts, the decision and the owner decisions; `journal/INDEX.md` carries exactly one 2026-11-03 row anchored on both recheck handoffs; `orchestration/STATUS.md` and `orchestration/VERDICTS.md` agree with each other and with the journal (0 live calls, PASS/PASS, 123/369/450, 7,560/1,729 = 4.37× UNFUNDED); `git diff` shows insertions plus only the two lines that extend the journal-index title and the STATUS one-liner — no old verdict row altered |
| 4 | Gate | **pass** — see outputs below |
| 5 | Red→green on the new journal row | **pass** — exercised, not asserted: exit **0 → 1 → 0** |
| 6 | Containment | **pass** with one qualification — only the seven declared paths carry today's mtime in this workspace (sweep: 7 files + `.pytest_cache`); `REQUEST-LEDGER.json` still 2026-10-28, `BOUNDARY-PREREG.md` still 2026-10-26; the close-out handoff's `evidence.commands` are `doc_check`, `pytest`, `recompute.py C53`, `json.tool` — no `curl`, no live call, no `run_longrun` |
| 7 | Card + handoff | **pass** — `orchestration/handoffs/V-SESSION-CLOSE-BC-2026-11-03.json` |
| 8 | Report | this card |

## Gate outputs (re-run here, offline)

| Command | Actual output | Exit |
|---|---|---|
| `python3 tools/doc_check.py` | `OK docs clean under /home/zer0null/research extractor` | **0** |
| `.venv/bin/python -m pytest tests/test_agent_context.py tests/test_orchestration_handoffs.py -q` | `30 passed, 1 warning in 2.56s` | **0** |

The one warning is the pre-existing non-failing `HANDOFF-SHAPE REPORT` (11 both-shape handoffs, three of
them `UNDECIDED` role) — it reproduces on the close-out's own run (`1 warning in 2.73 s`) and is not
introduced by this batch.

## Red→green (doc guard, temp root, real workspace untouched)

```
R=/tmp/docred-vsess; mkdir -p "$R"; cp AGENTS.md STRUCTURE.md "$R/"      # root line rewritten to $R
cp -r docs journal "$R/"                                                # full copies
python3 tools/doc_check.py --root "$R"          -> OK docs clean        EXIT 0
grep -v '^| \[2026-11-03\]' journal/INDEX.md > "$R/journal/INDEX.md"    # row removed (37 -> 36 lines)
python3 tools/doc_check.py --root "$R"          -> FAIL journal entry journal/2026-11-03.md has no row or mention in journal/INDEX.md   EXIT 1
cp /tmp/docred-index.bak "$R/journal/INDEX.md"                          # restored
python3 tools/doc_check.py --root "$R"          -> OK docs clean        EXIT 0
```

The guard therefore fails on exactly the omission the close-out introduced, and the workspace copy of
`journal/INDEX.md` was never edited by this unit.

## Accuracy detail (numbers cross-checked, not re-derived)

- Deliverables on disk: report **356 lines / 53,979 B**, sha256 starts `aae035df`; protocol **517 lines /
  44,691 B**, sha256 starts `e53d8856` — both match the sizes and shas quoted in the journal, the STATE
  table and the VERDICTS batch table.
- E2 arithmetic `3 arms × 40 turns + 3 checkpoints = 123` for one rep, `3 × 123 = 369`, `450` with the
  12-checkpoint fixture: present and identically worded in the report recheck's `next_unit_hint`, in all
  four close-out prose sites, and never stated as ≤120 deciding anything.
- Comparative `5,040 + 2 × 420 × 3 = 7,560`, `7,560 / 1,729 = 4.37×`, `UNFUNDED`; `5,040 / 1,729 = 2.92×`
  kept as the "even if D were free" figure. No site carries the pre-fix `3.64×` as a live claim.
- `BOUNDARY-PREREG` (696 scheduled, ceiling 810, registered 2026-10-26T01:22-0500): described everywhere
  as a **separate, unexecuted, unapproved** candidate whose `E1`/`E2` names collide with the handoff's.
- "0 live calls / no build" is written as a **checked negative** ("not a proof") in the journal, and the
  handoff's command list contains no request-making command — consistent with the recheck's own evidence
  that only reads, greps and `/tmp` checker work ran.

## Defects

1. **Minor, documentation-only:** `docs/STATE.md` §8 says the STATUS record is at
   "`orchestration/STATUS.md` (§11)", but `orchestration/STATUS.md` has **no §11** — the batch section is
   named `## Batch: Consonance bounded-context research (2026-11-03)` precisely because the file already
   carries two `## 8` and two `## 9` headings. The stale cross-reference does not break pickup (§8 names
   the file, the journal entry and the two recheck handoffs in the same bullet), so it is recorded, not
   graded a failure. A later documentation unit may change `(§11)` to `(the 2026-11-03 batch section)`.

## Not reproduced / not verifiable here

- The research **evidence** itself was not re-run (out of scope by assignment): `recompute.py C53`, the G5
  row recomputation and the two `/tmp` progressive checkers are accepted on the recheck handoffs' PASS.
- The **absence of Duval writes** is inherited, not independently provable: `/home/zer0null/Duval` has
  concurrent unrelated activity (`.worktrees/SELFBUILD`, HEAD `d2832604` 2026-11-04 03:52, files at
  05:06), which is a different session's work; nothing ties any Duval path to this close-out, and its
  journal already labels the zero-write claim a checked negative. Recorded as `unverified`, not a defect.

## Next

`E1-CACHE-BOUNDARY-SWEEP` at ≤60 calls (reconcile `experiments/ptr-engine/measure/REQUEST-LEDGER.json`
first), then `E2-CHECKPOINT-COST` only at an owner-approved budget (123 descriptive / 369 adjudicable /
450 with the 12-checkpoint fixture). The 7,560-request comparative stays `UNFUNDED` against 1,729; the
**185-call instrument pilot** is the funded alternative; quality arms stay blocked on the fixture/grader
owner (`PATH-CANNOT-SAY-YES`, report row E-17). `BOUNDARY-PREREG` remains separate and unexecuted.

## Start/end hashes (identical, so no deliverable changed during verification)

```
fc106d2c… journal/2026-11-03.md        baf1073c… journal/INDEX.md
8379a3e3… docs/STATE.md                baadddf5… orchestration/STATUS.md
ff145720… orchestration/VERDICTS.md    ed295d7e… orchestration/units/SESSION-CLOSE-BC-2026-11-03.md
e3412713… orchestration/handoffs/SESSION-CLOSE-BC-2026-11-03.json
```
