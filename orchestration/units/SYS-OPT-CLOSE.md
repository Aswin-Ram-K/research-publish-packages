# Unit card — SYS-OPT-CLOSE (close SYS-OPT at the ceiling, publish the paired release)

**Unit:** `SYS-OPT-CLOSE` · **Parent:** `SYS-OPT` (`733058c8`) · **Predecessor:** `SYS-OPT-R1B` (`ad0c4cf8`,
execution `0de19ab2`)
**Permission:** danger-full-access · **Automated:** yes — `[automated]` `[no-questions]`, never ask.
**Live requests:** 0. Offline only. No container started, stopped or restarted. No lock acquired.

## Objective

Record the **consequence** of the pre-registered ceiling rule, not renegotiate it: SYS-OPT's round 1
returned `no_signal` (`state/sys-opt-v1.json`), §4 of `docs/prompt-system/VERSIONS.md` declares the ceiling,
and the best version is V0. Close the lineage and publish the paired release that V0 defines.

`SYS-OPT-R1B.json`'s `next_unit_hint` names this unit's job explicitly: *"Closing card (SYS-OPT close):
write state/sys-opt-verdict.json = {best_version: V0, closed_at_ceiling: true, ceiling_round: 1, per_model
from state/sys-opt-v1.json, paired_release: …}; then FINAL-GOAL close-out."*

## Hard bound

- **Live requests: 0.** Numbers are read from `state/sys-opt-v1.json` and
  `orchestration/handoffs/SYS-OPT-R1B.json`; nothing is re-measured.
- **Tool calls: 30.** **No source code, no logs, no debugging.**
- Nothing outside this workspace. No target repo touched. No `git` verb.
- Stop condition: if a required value is not derivable from the two named files plus `VERSIONS.md` /
  `RELEASE-v1.json` provenance, record it as a carried gap and continue — never invent it.

## Method (what was actually done)

| step | action |
|---|---|
| 1 | Read the two named sources; cross-checked every per-model figure in the handoff against `state/sys-opt-v1.json` — 0 discrepancies. |
| 2 | Read `VERSIONS.md` §§2, 4, 5, 6, 8, 9 + A1 + A2 and `SYS-OPT-R1B-RESULTS.md` to fix the rule's exact requirements for a ceiling. |
| 3 | Wrote `state/sys-opt-verdict.json`: `no_signal`, `best_version V0`, `closed_at_ceiling true`, `ceiling_round 1`, per-model block, quality-guard and headroom sections, reopening rule. |
| 4 | Wrote `docs/prompt-system/SYS-OPT-RESULTS.md`: the §4 "record the ceiling line" requirement — no such file existed (R1B wrote a round-level `SYS-OPT-R1B-RESULTS.md` instead). |
| 5 | Wrote `docs/prompt-system/RELEASE-v1.json`: the paired release — one prompt artefact + per-model serving. |
| 6 | Re-derived both `config_sha256` values from `state/config/best-config.json` `argv` (recipe `tools/best_config_build.py:84-88`) — **match**. |
| 7 | Computed the release's `prompt_stream_digest` offline from the frozen renderer + `sysopt_r1.py` overrides — 0 requests, labelled with its verification limit. |
| 8 | Appended the verdict row to `orchestration/VERDICTS.md` and the close-out to `orchestration/STATUS.md` (§7), both additively below their existing content. |

## Write paths (declared before work, no overlap with any concurrent unit)

`state/sys-opt-verdict.json` · `docs/prompt-system/SYS-OPT-RESULTS.md` · `docs/prompt-system/RELEASE-v1.json` ·
`orchestration/units/SYS-OPT-CLOSE.md` · `orchestration/handoffs/SYS-OPT-CLOSE.json` ·
`orchestration/VERDICTS.md` (append) · `orchestration/STATUS.md` (append)

**Not written:** any measurement, any row file, `state/sys-opt-v1.json`, `docs/prompt-system/VERSIONS.md`
(§11 freezes it and no amendment is warranted), `experiments/**`, `papers/**`, `RUN.json`, tests.

## Kill condition

If `state/sys-opt-v1.json` and the R1B handoff contradict each other, or the round is not a `no_signal`,
STOP and report `partial` — the close-out may not manufacture a ceiling the measurement did not produce.
