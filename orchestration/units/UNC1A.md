# UNC1A — resolve candidate NC1's single blocker

**Unit:** UNC1A · **Date:** 2026-10-15 · **Tool calls:** 27 of 40 bound
**Target:** `/home/zer0null/Duval` — READ ONLY, no git invoked there, no writes
**Status:** `done`

## Purpose (one)

Determine whether publish-candidate **NC1**'s single blocker can be resolved — and if so, specify
exactly how. ULEAD1 found NC1 gate-clean, fixture-free, invariant TRUE, blocked only by
`evals/prevention.ts` importing `../tools/trace.ts` (an M13 withhold block).

## Write paths (declared, no clashes)

`strategy/NC1_UNBLOCK.md`, `strategy/NC1_FIX_PROPOSAL.md`, `orchestration/units/UNC1A.md`,
`orchestration/handoffs/UNC1A.json`. Running units own `repro/**` (UREDACT2),
`papers/gated-read-batching/**` (UFIX11), `orchestration/units/UBUILD1.build.sh` +
`strategy/PUBLISH_PACKAGE_MANIFEST.md` (UCURATE1) — none touched.

## Answer

**(c) incidental** is the precise class of the named import; the **package** blocker is **wider**.

```
evals/prevention.ts:42   import { DEFAULT_SESSION } from "../tools/trace.ts";
evals/prevention.ts:63   const TRACE_SESSION = DEFAULT_SESSION;
tools/trace.ts:122       export const DEFAULT_SESSION = "2026-09-28-duval-m0";
```

One plain string constant. No function, class, or type from `tools/trace.ts` is used or executed;
`prevention.ts`'s own header comment records that this literal *used to live in the file* and was
swapped for the import as a provenance refactor, value unchanged. So the fix is a revert, not a rewrite.
`import type` is not available (value import under `verbatimModuleSyntax`).

**But it does not unblock NC1:**

* transitive closure of `[evals/registry.ts, evals/run.ts, evals/prevention.ts]` = **42 modules**
  (13 evals / 21 src / 5 tools / 3 tests). `registry` + `eval` reds the reader's build on
  **13 distinct withheld modules** (19 × TS2307, measured).
* post-fix the eval **runs and fails 4 of its own assertions**: check B resolves only **6 of 12**
  automated detector rows; check C finds no traces; two git-graph reds were **simulation artifacts**
  (the sim sits inside the workspace's own git repo — Duval history was never read).
* a green B needs `scripts/{sync-issues,guardrails}.sh`, `scripts/write-scope-guard.mjs`,
  `examples/sandbox-test.ts`, `.githooks/*`, and **`tools/trace.ts`** (M13, itself gate-dirty: 4 hits).
* checks C/D need `traces/2026-09-28-duval-m0.jsonl` — pinned copy at **866,816 bytes / 573 records / 573 gated lines / 712 gate occurrences** (the recorded **1,570,243 bytes / 1031 gate hits** was the live path, and 1,031 is that blob's line count — no state reproduces it as a gate count) — plus a
  commit↔trace history a fresh-history publish repo cannot reproduce.

**Verdict: FIXABLE-BUT-COSTLY.** The 2-line import fix is real and riskless (RAN: `tsc` red→green);
unblocking the *package* requires either publishing M13 `tools/**` (**author decision**) or moving
NC1's headline number **12 → ≤11**. `m13_exposure_required: yes`.

Also closed ULEAD1's UNVERIFIED #2: `tools/trace.ts` is **not** gate-clean.

## Evidence (what I RAN vs READ)

* **RAN** `tsc` 5.9.3 (`/home/zer0null/Duval/node_modules/.bin/tsc`, no install) on a workspace copy:
  pre-fix exit 2 / `TS2307` at `(42,33)`; post-fix exit 0; `registry.ts` entry exit 2 / 19 errors;
  emitted JS then executed the eval → `passed=false`, 4 FAILs.
* **RAN** Python import-closure resolver over the real tree; `find` mtime sweep; `grep` gate scan.
* **READ** `evals/prevention.ts` (789 L), `tools/trace.ts` (514 L), `evals/registry.ts`,
  `docs/MISTAKES.md:388-413`, `AGENTS.md`.
* Sim lives at `scratch/unc1a/sim/` (scratch input, not a deliverable); the 0.83 MB pinned corpus was
  deliberately not copied into the workspace.

## Containment

No writes to Duval; no git in Duval. **Observation, not self-exculpation:** a 30-minute mtime sweep
of Duval shows writes that are not mine — `package.json` and `CONTRIBUTING.md` (both `18:26:07`),
large `rust/target/tests/trybuild/**` churn, and `traces/2026-09-28-duval-m0.jsonl` (`18:50:03`,
grew mid-session). Target sources older and untouched (`evals/prevention.ts` 10-14 20:03,
`tools/trace.ts` 10-12 04:22, `docs/MISTAKES.md` 10-06 23:43). No stray build artifacts in the root.
**Something else is writing in the read-only target — orchestrator should check containment.**

## Deliverables

* `strategy/NC1_UNBLOCK.md` — classification, withheld-import list, fix + risk, sim results, verdict
* `strategy/NC1_FIX_PROPOSAL.md` — diff-style spec, verification checklist, red→green guard (§A.4 V4)
* this card, and `orchestration/handoffs/UNC1A.json`

## Next unit hint

Route the scoping decision to the author (M13 `tools/trace.ts` vs a restated automated count), not to
an implementer — §A is safe to apply now, §B(i) is not ours to choose.
