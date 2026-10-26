# NC1_FIX_PROPOSAL — the exact change, and what must be re-verified

**Unit:** UNC1A · **Applies to:** `/home/zer0null/Duval` (**read-only — this is a specification, not a
patch applied by me**) · **Status:** proposed, unapplied, unverified-by-a-second-unit
**Companion:** `strategy/NC1_UNBLOCK.md` (classification, evidence, verdict)

This is written so a **separate implementer** can apply it without reading UNC1A's transcript.
It has **two parts**: §A the import fix (trivial, safe, does *not* unblock the package) and §B the
scoping decision (the thing that actually decides whether NC1 ships green).

---

## §A — The import fix (recommended regardless of §B)

### A.1 Preconditions

* Target repo clean; **do not** apply this to `/home/zer0null/Duval` under this unit's authority.
  Apply it in the publish-package working tree, or on a Duval branch owned by another unit.
* Baseline: `evals/prevention.ts` is 789 lines; `evals/registry.ts` 29 lines; `tools/trace.ts` 514 lines.
* Confirm the literal has not drifted first —
  `grep -n 'DEFAULT_SESSION *=' /home/zer0null/Duval/tools/trace.ts`
  must still read `export const DEFAULT_SESSION = "2026-09-28-duval-m0";` at `:122`.
  **If it differs, use the value you find; do not use the value printed here.**

### A.2 The change — `evals/prevention.ts`, two hunks

**Hunk 1 — delete the import.** Line 42 currently reads (verbatim):

```ts
import { DEFAULT_SESSION } from "../tools/trace.ts";
```

Delete that line. Do not add a replacement import. (`prevention.ts` needs nothing else from
`tools/`; its other imports — `node:child_process`, `node:fs`, `node:path`, `./types.ts`,
`./compare.ts` — stay exactly as they are.)

**Hunk 2 — inline the constant.** Line 63 currently reads (verbatim):

```ts
const TRACE_SESSION = DEFAULT_SESSION;
```

Replace it with:

```ts
const TRACE_SESSION = "2026-09-28-duval-m0";
```

**Hunk 3 — update the explanatory comment above it (optional but required for honesty).**
The comment block immediately above `TRACE_SESSION` references `tools/trace.ts:105` as the source of
the literal. That reference becomes stale. Amend that one clause to state that this package declares
the literal locally and that it must stay equal to the `traces/<session>.jsonl` filename and to the
upstream `scripts/trace-sync.sh` literal. **Change no other sentence** — the surrounding comment
documents why the three historic session literals were unified, which is still true of the upstream
repository.

### A.3 What must NOT be done

* Do **not** convert this to `import type { … }` — the symbol is a **value** (`verbatimModuleSyntax`
  is on, and there is no type to import). It will not compile.
* Do **not** copy any part of `tools/trace.ts` into the package to "make the import resolvable".
  That is the M13 widening this unit exists to *avoid*; see §B.
* Do **not** add a `tools/trace.ts` stub/shim that re-declares the constant. It would satisfy `tsc`
  while leaving `tools/` in the package's expected layout and confusing every later reader about what
  ships. The inline is strictly better and is what the original code did.

### A.4 Verification after §A (do these in order; each has an expected exact result)

```bash
# V1 — the import is gone
grep -n 'tools/trace' evals/prevention.ts        # expect: no output
# V2 — nothing else in the file referenced trace.ts
grep -n 'DEFAULT_SESSION' evals/prevention.ts    # expect: no output
# V3 — the constant is present and correct
grep -n 'TRACE_SESSION *=' evals/prevention.ts   # expect: 1 hit, the inlined literal
# V4 — the eval's own module graph typechecks (this is the red→green of the named blocker)
npx tsc --noEmit -p <tsconfig including evals/prevention.ts>
#   expected BEFORE: evals/prevention.ts(42,33): error TS2307: Cannot find module '../tools/trace.ts'
#   expected AFTER:  exit 0
# V5 — the value did not move
node --experimental-strip-types -e '1' 2>/dev/null || true   # (system node has no TS support; use the emit harness)
#   run the eval and confirm: prevention.classes=19, prevention.automated=12,
#   prevention.manual=4, and every non-check-B/C/D assertion still PASSes.
```

**Red→green requirement (AGENTS.md):** V4 is the red→green guard. Reverting hunk 1 must restore the
exact TS2307 at column 33. If it does not, the environment is not the one described here.

### A.5 Risk

| | |
|---|---|
| behaviour | **unchanged** — same constant, same checks, same budgets |
| numbers NC1 claims | **unchanged** by this patch alone (19 / 12 / 4 and all check outcomes) |
| residual defect | re-creates the literal duplication the upstream comment says caused a prior failure; harmless **only** if the package ships neither `scripts/trace-sync.sh` nor a trace corpus — which §B(ii) does not guarantee |
| new gate hit | **+1** — the inlined literal contains `duval`; `evals/prevention.ts` was gate-clean (0 hits). Scrubbing requires renaming the session **and** the `traces/*.jsonl` file that names it — a §B job |

---

## §B — The scoping decision (this is what decides green vs red)

§A fixes a 2-line import. It does **not** make the package green. Measured (see `NC1_UNBLOCK.md` §6):
after §A, `tsc` on `evals/registry.ts` still fails with **19 errors over 13 distinct withheld
modules**, and the eval still fails **4 of its own assertions**. Pick one:

### B(i) — Ship the detectors → **requires an author decision (M13 exposure)**

Add to the package:

| path | needed by |
|---|---|
| `scripts/sync-issues.sh` | check B rows B1, B2, B3, B4 |
| `scripts/guardrails.sh` | check B row E1 |
| `scripts/write-scope-guard.mjs` | check B row E4 |
| `examples/sandbox-test.ts` | check B row B3 (alternate) |
| `.githooks/pre-commit`, `.githooks/post-commit`, `.githooks/commit-msg` | rows E4, A5 |
| **`tools/trace.ts`** | check B row E5 ← **the M13 withhold block, and itself gate-dirty (4 hits)** |
| `traces/2026-09-28-duval-m0.jsonl` | checks C and D — **pinned at 866,816 bytes / 573 gated lines / 712 gate occurrences** (`dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`, sha256 `431605e6…`); the recorded "1,570,243 bytes / 1031 gate hits" was the live path, and 1,031 is that blob's line count, not a gate count |
| the commit↔trace history | check D's "every non-tip commit has a trace" |

Also required: a package-local runner that does not import `registry.ts`, **or** shipping the whole
21-file `src/` closure that `registry.ts` drags in (`src/state.ts`, `src/adapter.ts`, `src/mcp.ts`,
`src/sandbox.ts`, `src/catalog.ts`, `src/policy.ts`, `src/store.ts`, `src/dag.ts`, `src/hash.ts`, …).

**Cost:** this publishes M13 material. Per the unit rules this route is **NOT FIXABLE without an
explicit author call** — it must not be chosen by an implementer.

### B(ii) — Re-scope the claim → **moves NC1's headline number**

1. Ship only the eval surface: `evals/{prevention,types,compare,run,drift,registry,…}.ts` **as the
   author re-scopes it**, plus `docs/MISTAKES.md`.
2. Provide a package-local runner that runs `evals/prevention.ts` **without** importing
   `evals/registry.ts` — this removes the 13-module `tsc` red without publishing `src/`.
3. Reformulate the `docs/MISTAKES.md:388-413` detector table so that rows whose only detector is
   withheld name something the package actually ships. Concretely, check B's predicate passes a row if
   **any** named path exists, so a row can be kept green by *adding* a shipped path — but **only if the
   added path is a real detector**, otherwise the table lies and check B is worthless.
4. Honest consequence: **`prevention.automated` drops from 12.** Six of twelve rows currently resolve
   to nothing in the package. Depending on how many are demoted to `partial`/`manual`,
   **12 → 11 at best, 12 → 6 at worst**. The paper's central figure and every claim resting on it must
   be re-derived from the table, not asserted.
5. Additionally decide what to do about checks **C and D**: they need the pinned 0.83 MB corpus and a
   git-history↔trace correspondence. Options: (a) mark them package-local "controls, not applicable
   outside the source repository" and have the runner skip them with an explicit N/A line — this
   **changes what "green" means** and must be stated in the paper; (b) ship the corpus (gate-dirty,
   private history) — that is B(i) by another name.

**Cost:** no new disclosure; but the invariant is weakened, the headline number moves, and the paper
must be amended. **This is the only route an implementer may take unilaterally, and only with the
number change pre-agreed.**

---

## §C — Re-verification checklist after either route

An **independent** verifier (not the implementer, per AGENTS.md) must confirm:

1. `grep -n 'tools/trace' evals/prevention.ts` → empty; `tsc` on `prevention.ts` → exit 0 (red→green
   shown by reverting the hunk first).
2. `tsc` on the package's declared entry point → exit 0, and the declared entry point is the one the
   README tells a reader to run.
3. The eval **executes** (not just compiles) and its emitted metrics match the table in
   `docs/MISTAKES.md`: `prevention.classes=19`, `prevention.automated=<?>`, `prevention.manual=<?>`.
4. For route B(ii): the *new* automated count is recorded wherever the old 12 was (paper, README,
   manifest, `MISTAKES.md:388`) — grep the whole package for the string `12 automated` and for
   `12` in detector contexts to prove no stale figure survives.
5. Gate scan of every shipped file: the package's own gate is clean — in particular `evals/prevention.ts`
   must be re-measured after the inline (expect ≥1 `duval` hit unless the session was renamed).
6. Containment: **no write by this workspace's units** (git status + mtime sweep), nothing written outside the
   workspace. The root checkout was **not** untouched — five root files and the trace were rewritten by a
   foreign actor (`strategy/CONTAINMENT_CHECK.md` §2/§7).

## §D — What I did and did not do

* I did **not** apply either route anywhere. `/home/zer0null/Duval` was never written to and no git
  command was run in it.
* Route A was **RAN and verified** on a workspace copy: pre-fix `tsc` exit 2 with the single TS2307;
  post-fix `tsc` exit 0. That is the strongest claim in this document.
* Route B is a **specification**, not a measurement. Its numbers (19 / 6 / 12 → ≤11) follow from the
  measured check-B failure list and the measured closure, but no B-compliant package was built.
