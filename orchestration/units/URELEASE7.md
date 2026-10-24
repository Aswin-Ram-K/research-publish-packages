# URELEASE7 — smallest release portion that validates candidate #7's published claims

**Unit:** URELEASE7 · **Workspace:** `/home/zer0null/reserach extarctor` · **Date:** 2026-10-15
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Purpose
Find the **smallest possible portion** of candidate #7's material that still lets an independent
reader verify the paper's published claims, given that the raw record
(`gated-read-rows.jsonl`, 2,267,742 B / 9,260 lines / md5 `3aad1ae29e472ef9f5f54e179510faf5`) is on the
**withhold list** and cannot ship. Prove minimality by **cutting and running the verification path** at
each cut — record literal exit code and diagnostics — not by argument.

## Inputs (read first, binding)
- `strategy/GATED_READ_DISCLOSURE.md` — disclosure classification; **its withhold checklist is binding**.
- `strategy/GATED_READ_REVERIFY.md` — which numbers are reproducible and from which raw record.

## Deliverable
`strategy/GATED_READ_RELEASE_CUT.md`: claims table; cut ladder (cut N | files | bytes | exact command |
literal exit | diagnostics | verdict); first-breaking cut with literal error; minimal file list with
per-file reason + file kind (verification tool / result record / reduced-neutralised data record / prose);
neutralisation applied (element → tag kind, no map values); withheld list restated; residual risk.

## Hard constraints
- Target repo `/home/zer0null/Duval` STRICTLY READ-ONLY. **No `git` against it at all.**
- Write only: `strategy/GATED_READ_RELEASE_CUT.md`, `orchestration/units/URELEASE7.md`,
  `orchestration/handoffs/URELEASE7.json`, `scratch/urelease7/**`.
- Do NOT touch `papers/**`, `repro/**`, `orchestration/units/UBUILD1.build.sh`, other `scratch/**`.
- Must NOT ship: `tools/gated-read/bench.py`; `tasks.json`; unreduced row/summary files; any `src/**` path
  or module name; KeyRing surface (`GATED_URL`, `KEYRING_API_KEY`, `~/.dsh/.credentials.yaml`, `okr_`-shaped
  tokens); branch label; fixture answers; M10 gate/absence construction as construction detail; model ids;
  every `[CONST-*]` constant from UDISCLOSE7.
- Do not weaken the withhold checklist to make a cut work — report the trade instead.
- Do not draft/edit the paper; do not build the final package or touch a manifest.

## Bound
**30 tool calls.** Stop condition: if the minimal set cannot be established in 3 successive cuts, report
`partial` with the smallest set proved and the exact failure.

## Status log
- (start) Card persisted. Reading the two binding reports next.
