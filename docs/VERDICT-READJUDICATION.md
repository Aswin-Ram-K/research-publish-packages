# VERDICT-READJUDICATION — do the 29 delivered-but-unverdicted units still pass today?

**Unit** `VERDICT-READJUDICATE-27` · **date** 2026-10-26 · **head** `f17663d1fed0` · **machine-readable record** [`experiments/ptr-engine/measure/VERDICT-READJUDICATION.json`](../experiments/ptr-engine/measure/VERDICT-READJUDICATION.json)

## The honest frame

These executions closed **FAIL `no-verdict` `no-sha`**. That verdict was *correct under the rule* — nobody wrote a
verdict row — and it stays in the record. This document does not erase it and does not backdate anything. What was
unknown is whether the work they delivered still passes **today**; the only way to answer that is to run each
unit's own acceptance command against the current tree and record what happens.

**Input set is 29, not 27.** The 27 `delivered-unverdicted` rows of [FAILED-TRIAGE.md](FAILED-TRIAGE.md) plus
`FAILED-TRIAGE` (`5e7e5af7`) and `DEDUPE-ROOT-CAUSE` (`31e3b9a5`), which also delivered and also closed `FAIL no-verdict`.

## Result

| | all 29 | the 27 |
|---|---|---|
| **pass** | 10 | 9 |
| **fail** | 1 | 1 |
| **stale-tree** | 1 | 1 |
| **not-runnable** | 17 | 16 |

**10 of 29 delivered units (9 of the 27) still pass today** — measured by running their own command, not by
noticing that their artefacts exist. Of those 10 passes, **7 could be written as verdict rows**; the other 3 are
refused by the gate itself (`command-not-allowed`), which is a finding in its own right (see §3).

## 1. All 29, one row each

`exit` is the exit code measured today under `/bin/sh -c`; `row` says whether a verdict row could be recorded for
that execution. Full command strings and output tails are in the JSON.

| # | unit | class | command (as run today) | exit | row | evidence |
|---|---|---|---|---|---|---|
| 1 | `ARMS-PARITY-WITHDRAW` | pass | `python3 tools/audit/arms_parity_status.py` | 0 | yes | C1_record: ok / C2_corpus: ok / C5_surfaces: ok; recorded form is the unit's own script re-invoked through allow-listed `python3` (its `.venv/bin/python` form is refused `command-not-allowed`) |
| 2 | `AVALANCHE-INSERT` | not-runnable | `python3 experiments/miss-law/avalanche/probe.py all 3` | — | no | not run: live. probe.py opens `http://192.168.2.168:8014/metrics` and an HTTPConnection to the same vLLM host; every stage is a live generation against a server that must be up |
| 3 | `C63-CELL` | pass | `python3 papers/context-cache/verify_package.py` | 0 | yes | verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none |
| 4 | `C8-ADDENDUM2` | not-runnable | `test -s experiments/ptr-engine/RECORD.md` | — | no | evidence-only: the only recorded acceptance is an existence check; RECORD.md exists (55006 B) but the file was rewritten 10-26 01:19, after this unit's 10-25 13:07 handoff |
| 5 | `C8-CENSUS` | not-runnable | `test -s experiments/miss-law/FIT-GAP.md` | — | no | evidence-only: existence check only |
| 6 | `CONTAINMENT-RULING` | not-runnable | `test -s orchestration/units/CONTAINMENT-RULING.md` | — | no | evidence-only: existence check only |
| 7 | `DET-VERIFY-FIX` | pass | `python3 experiments/ptr-engine/tools/det_verify.py` | 0 | yes | wrote experiments/ptr-engine/measure/det-verify-matrix.json; self-writing command — it rewrote its own measure output at 11:34, `git status` reports no content change for that path |
| 8 | `GRADE-FIT-CONTROL` | pass | `python3 experiments/ptr-engine/tools/grader_fitness.py` | 0 | yes | wrote experiments/ptr-engine/measure/grader-fitness.json; self-writing, same caveat as DET-VERIFY-FIX |
| 9 | `LATENCY-DERIVE` | not-runnable | `.venv/bin/python state/logs/lat_derive.py > state/logs/lat_derive.out` | — | no | not run: mutating — the command redirects into `state/logs/lat_derive.out`, a measurement output; re-running it would overwrite a measurement file this card must not edit |
| 10 | `LAZY-LOAD-CROSSOVER` | not-runnable | `python3 cx_corpus.py` | — | no | not run: no cwd recorded and the command mutates. A bare `python3 cx_corpus.py` fails at the workspace root (`cx_corpus.py` does not exist there); the file lives at experiments/agentic-lazy/crossover/cx_corpus.py and writes the 3000/30000-char corpora |
| 11 | `LAZY-LOAD-CROSSOVER-2` | not-runnable | `(none)` | — | no | no command in the record: orchestration/handoffs/LAZY-LOAD-CROSSOVER-2.json does not exist, so this unit has no recorded acceptance command at all (its DNA is only the FAILED-TRIAGE settle field, the same line as its predecessor) |
| 12 | `PAPER-FINAL-V2C` | not-runnable | `test -s orchestration/handoffs/PAPER-FINAL-V2C.json` | — | no | evidence-only: the acceptance names the unit's own handoff as its artefact |
| 13 | `PROBE-CP3-V5` | not-runnable | `python3 experiments/ptr-engine/longrun/run_longrun.py --fixture …LR-01.v4.tools2.json -…` | — | no | not run: live — run_longrun.py is the live inference driver (48 turns + up to 24 fetch rounds against the endpoint) |
| 14 | `PROBE-CP3-V6` | fail | `python3 experiments/ptr-engine/longrun/tests/test_tool_channel2.py` | 1 | yes | AssertionError: ({'before': '9624cb3e8b80ae6caf828d26e289831bdacfc9d31302dbca5cd11d5be39ff493', 'after': '4e0949f50b8b61e721a981d0209e19161a0bac38dc087b924980f84eaeba2a86'}, 'tools-off output drifted'). Not repaired here. Candidate cause, not a conclusion: experiments/ptr-engine/longrun/run_longrun. |
| 15 | `PROMPT-O2C` | not-runnable | `docker stop gx10-qwen9b` | — | no | not run: mutating — it stops a live inference container; the rest of the recorded evidence is docker run / serve lines |
| 16 | `PROMPT-O4` | not-runnable | `.venv/bin/python experiments/context-cache/cells/PROMPT-O4/prompt_o4_cell.py` | — | no | not run: live — the cell drives five prompt arms against 9B/vLLM on :8016 |
| 17 | `Q0-ANSWER-DEGENERACY` | pass | `python3 -c "import json;d=json.load(open('experiments/ptr-engine/longrun/tasks-v2/runti…` | 0 | **refused** | resolve.py #L66-L110 1680 False 0 / errors.py #L114-L126 331 False 3 / test_scope.py #L16-L80 2598 False 0 / test_negative_controls.py #L80-L117 1412 False 0. Row refused: the gate splits the command on ';' and judges the `[print(...)]` fragment, so a `python3 -c` with semicolons can never be record |
| 18 | `R2-OPT-SIM` | pass | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q` | 0 | **refused** | 23 passed in 0.07s. Row refused because the command starts with `.venv/bin/python`; the allow-listed substitute `python3 -m pytest` cannot stand in — system python3 fails at tests/conftest.py:19 `ModuleNotFoundError: No module named 'resextract'`, so the venv is the only interpreter that can run thi |
| 19 | `R2-OPT-SIM2` | not-runnable | `test -s strategy/R2_OPT_SIM2.md` | — | no | evidence-only: existence check only |
| 20 | `R2-P1-O1` | not-runnable | `wc -l experiments/context-cache/cells/R2-P1-O1/rows.jsonl` | — | no | evidence-only: `wc -l` cannot fail (it exits 0 whenever the file exists, and 1 when it does not); it prints a count, it does not judge the work |
| 21 | `R2-VLLM` | pass | `python3 experiments/context-cache/cells/R2-VLLM/selftest_offline.py` | 0 | yes | SUMMARY pass=16 fail=0 red_green=True (offline, 0 requests); recorded form is the same script through allow-listed `python3` |
| 22 | `R2.1-TIGHTEN` | pass | `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` | 0 | yes | OK |
| 23 | `RECORD-C8-APPEND` | stale-tree | `head -n 128 experiments/ptr-engine/RECORD.md \| sha256sum` | — | no | stale-tree: changed paths — experiments/ptr-engine/RECORD.md (rewritten 10-26 01:19, after this unit's 10-25 11:35 handoff and its 10-26 01:19 successors). The unit's own evidence pins the pre-append prefix at 42ce9fb0649f71…; today `head -n 128 RECORD.md \| sha256sum` gives 2efbf4c2c3c8eb… so its b |
| 24 | `RECORD-C8-PARAGRAPH` | not-runnable | `test -s experiments/ptr-engine/RECORD.md` | — | no | evidence-only: existence check only; the file it names has been rewritten since (10-26 01:19) |
| 25 | `SIM-PROMOTE` | pass | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q -p no:cacheprovider` | 0 | **refused** | 23 passed in 0.07s. Row refused for the same `.venv/bin/python` reason as R2-OPT-SIM |
| 26 | `V-XSTACK2` | not-runnable | `test -s orchestration/handoffs/V-XSTACK2.json` | — | no | evidence-only: existence check only |
| 27 | `VERIFY-CLASSIFIER-FIX` | not-runnable | `(none)` | — | no | no command in the record: the settle field is a result sentence — `EXIT=0: 13 passed in 2.48s (pre-fix baseline was 1 failed, 12 passed)` — and no handoff carries an executable command for it |
| 28 | `FAILED-TRIAGE` | not-runnable | `(none)` | — | no | no executable command in the record: its own evidence line is prose — `python3 (ledger-v2 + handoffs + verdict.jsonl + stat) -> experiments/ptr-engine/measure/FAILED-TRIAGE.json` — with no argv, no script path and no reproducible form. Its artefact exists and is valid today (104 rows, 27/11/66 class |
| 29 | `DEDUPE-ROOT-CAUSE` | pass | `python3 experiments/ptr-engine/longrun/tests/test_request_identity.py` | 0 | yes | ALL GREEN (and both RED assertions failed as designed) |

## 2. What the classes mean here

- **pass / fail** — the unit's own command ran now and exited 0 / non-zero, against head `f17663d1fed0`.
- **stale-tree** — the command targets a file that has since been rewritten, so its PASS (or its check) would not mean
  what it meant when it was written. `RECORD-C8-APPEND` is the only one: `experiments/ptr-engine/RECORD.md` was
  rewritten at 10-26 01:19, three hours after that unit's handoff, and its pinned prefix hash
  `42ce9fb0649f71…` is now `2efbf4c2c3c8eb…`.
- **not-runnable** — no acceptance command exists in the record, or it cannot honestly be run today. Four reasons:
  * *live* (4): `AVALANCHE-INSERT` (vLLM `192.168.2.168:8014`), `PROBE-CP3-V5` (the live driver), `PROMPT-O4`
    (5 prompt arms on `:8016`), and the docker half of `PROMPT-O2C`.
  * *mutating* (3): `LATENCY-DERIVE` redirects into `state/logs/lat_derive.out`, `PROMPT-O2C` stops a live
    container, `LAZY-LOAD-CROSSOVER` regenerates its corpora (and its recorded command names a bare `cx_corpus.py`
    that does not exist at the workspace root — the file lives at `experiments/agentic-lazy/crossover/cx_corpus.py`).
  * *evidence-only* (7): the recorded acceptance is `test -s`, a hash print, or `wc -l` — it cannot judge the work.
    A PASS on one of those would be a PASS on the strength of artifacts existing, which this card forbids.
  * *no command at all* (3): `LAZY-LOAD-CROSSOVER-2` has no handoff, `VERIFY-CLASSIFIER-FIX` recorded a result
    sentence instead of a command, and `FAILED-TRIAGE` recorded prose `python3 (ledger-v2 + handoffs + …)`.

## 3. The command that cannot be recorded — a structural cause of the no-verdict closures

`orchestration_verdict` accepts only allow-listed runners. Two of the workspace's normal invocation forms are not
allow-listed, and both appear throughout the handoffs:

- **`.venv/bin/python …` is refused `command-not-allowed`.** Measured over the `commands` arrays of
  `orchestration/handoffs/*.json`: **354 of 4255 recorded command strings (8.3%) start with `.venv/bin/python`**, and
  every one of them is unrecordable as a verdict row — whatever it measures.
- **`python3 -c "…; …; …"` is refused**, because the gate splits the string on `;` and judges the fragment after it
  (`Q0-ANSWER-DEGENERACY`'s row was refused on `[print(...)]`).

The substitute is not always available: `R2-OPT-SIM` and `SIM-PROMOTE` pass only under the venv interpreter, because
system `python3` fails at `tests/conftest.py:19` with `ModuleNotFoundError: No module named 'resextract'`. So the two
suites that do pass today can never carry a PASS. `ARMS-PARITY-WITHDRAW` and `R2-VLLM` could be re-recorded through
`python3` because their scripts are dependency-free; those rows say so in their `output` field, and the substitution
is disclosed rather than hidden.

This is worth fixing at the rule level, not at the card level: a unit whose acceptance command runs through the
project venv will close `no-verdict` no matter how green it is.

## 4. Artefact present, command gone

Three units delivered files that still exist today with **no re-runnable acceptance command** in the record:
`LAZY-LOAD-CROSSOVER-2` (no handoff at all; `experiments/agentic-lazy/crossover/RESULTS.md` and `cells.json` exist),
`VERIFY-CLASSIFIER-FIX` (card, handoff and `tests/test_orchestration_handoffs.py` exist; the record holds the result
`13 passed in 2.48s`, not the command), and `FAILED-TRIAGE` (its own JSON exists and is valid; its command is prose).
No command was invented for them.

## 5. Is re-adjudication of the remaining 66 retriable units worth doing?

**No.** The 66 `retriable` rows in `FAILED-TRIAGE.json` carry no delivered artefact — their settle field is literally
`none — no artefact exists to settle it; the card must be re-run`. Re-adjudication measures *delivered work*; there
is nothing there to measure, so the ritual would produce 66 rows of `not-runnable` and no information. The remedy for
those is a re-run, not a re-adjudication.

Re-adjudication *was* worth doing for these 29, and it paid twice: it proved 10 units still green (so the decay rate
of delivered work here is low — 10 of the 13 units that had any verifiable command still pass, which is the
interesting number), and it found the `command-not-allowed` gap that explains why good work kept closing FAIL.

## 6. Bounds, side effects, and what was not touched

- Two of the acceptance commands are self-writing: `det_verify.py` and `grader_fitness.py` rewrite
  `experiments/ptr-engine/measure/det-verify-matrix.json` and `experiments/ptr-engine/measure/grader-fitness.json`.
  Running them as their own units did updated those files' mtimes (11:34); `git status --porcelain` reports **no
  content change** for either path, so the regeneration was byte-identical. Disclosed, not hidden.
- No unit handoff, unit card, journal or other unit's measurement file was edited. No live request was made; no
  mutating command was run. `PROBE-CP3-V6` was **not repaired** — its FAIL is reported as measured.

## Appendix — the generator that produced the JSON

The JSON's numbers come from one script; its table of 29 rows is the `R` list below, and the only computed value is
the current head sha and the existence checks. Reproduce by pasting this into `gen_readjudication.py`:

```
rows = [(unit, execution, taskId, class, command_as_run, exitCode, recorded, evidence), …]   # 29 entries, in the JSON
sha = git --no-optional-locks rev-parse HEAD
totals[class] += 1 ; of_the_27 excludes FAILED-TRIAGE and DEDUPE-ROOT-CAUSE
```

Integrity check (the card's own verdict command, no semicolons so the runner allow-list accepts it):

```
python3 -c "import json\nd=json.load(open('experiments/ptr-engine/measure/VERDICT-READJUDICATION.json'))\nassert d['total']==29 and len(d['units'])==29\nassert sum(d['totals'].values())==29\nprint(d['totals'])"
```
