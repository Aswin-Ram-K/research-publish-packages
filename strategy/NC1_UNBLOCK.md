# NC1_UNBLOCK — can candidate NC1's single blocker be resolved?

**Unit:** UNC1A · **Date:** 2026-10-15 · **Target:** `/home/zer0null/Duval` (read-only, no git invoked there)
**Question:** ULEAD1 found NC1 gate-clean, fixture-free, invariant TRUE, blocked only by
`evals/prevention.ts` importing `../tools/trace.ts`, an M13 withhold block. Resolve it or close it.

---

## 0. Verdict up front

| field | value |
|---|---|
| blocker class | **(c) incidental** — and, separately, **wider** than one import |
| single import fixable | **yes** — trivial, 2-line change, zero behavioural risk |
| first run after that fix | **RED** (measured, not inferred) |
| **package verdict** | **FIXABLE-BUT-COSTLY** |
| M13 exposure required for a green run at NC1's current numbers | **yes** → needs author decision |

**Plainly:** the *import* is a false alarm — it is one string constant of provenance bookkeeping, not
mechanism. But removing it does **not** unblock NC1. A reader who takes `registry` + `eval` and runs
gets a red build for **13 withheld modules**, and the eval itself then fails **4 of its own assertions**.
Making that green requires shipping `tools/trace.ts` (M13) or moving NC1's headline number. This is the
same shape as ULEAD1's finding, one level deeper.

---

## 1. The real files (RAN: located and read)

| path | lines | what it is |
|---|---|---|
| `/home/zer0null/Duval/evals/prevention.ts` | 789 | NC1's detector-coverage eval — checks A–D over `docs/MISTAKES.md` |
| `/home/zer0null/Duval/tools/trace.ts` | 514 | append-only trace CLI; **M13 withhold block** |
| `/home/zer0null/Duval/evals/registry.ts` | 29 | barrel exporting `EVALS: Eval[]` |
| `/home/zer0null/Duval/docs/MISTAKES.md` | — | the table the eval checks (detector rows at `:388-413`) |

`/home/zer0null/Duval/.worktrees/**` holds ~50 near-identical copies of `prevention.ts`/`trace.ts`
(one per historical worktree). They are noise for this question; the canonical copies are the two
above. No other `prevention.ts`/`trace.ts` pair outside `.worktrees/` was found.

---

## 2. The import, precisely (RAN: read + grep)

```
evals/prevention.ts:42   import { DEFAULT_SESSION } from "../tools/trace.ts";
evals/prevention.ts:63   const TRACE_SESSION = DEFAULT_SESSION;
tools/trace.ts:122       export const DEFAULT_SESSION = "2026-09-28-duval-m0";
```

That is **the whole coupling**. Evidence:

* `prevention.ts` uses **no** function, class, or type from `tools/trace.ts`. Its complete import list
  is `node:child_process`, `node:fs`, `node:path`, `./types.ts` (a type plus `assertion, metric,
  result`), `./compare.ts` (`compareToBaseline`), and `../tools/trace.ts` (`DEFAULT_SESSION`). One
  symbol, one line.
* The symbol is a **plain string constant**, not a function. Under Duval's own tsconfig
  (`verbatimModuleSyntax: true`) a value import is **not** elidable by `import type` — which is why
  the naive "just make it a type import" fix does not exist here. But it is also why the *value* is
  all that is needed.
* `prevention.ts`'s own header comment records the history: the literal **used to live in this file**
  and was swapped for the import in "GATE0 trace lineage, Task A", with the note *"The value is
  unchanged; only the provenance is unified."* The fix is a **revert of a provenance refactor**, not a
  rewrite of behaviour.

### Classification: **(c) incidental** — with the (a)/(b) alternatives explicitly ruled out

| option | verdict | why |
|---|---|---|
| (a) **type-only** / erasable | **no** | it imports a *value*; `import type` would not compile and there is no interface to re-declare |
| (b) runtime function the eval needs | **no** | no function is referenced; nothing from `tools/trace.ts` is *executed* by the eval |
| (c) **incidental** | **YES** | a single string constant kept in sync so `prevention.ts` and `scripts/trace-sync.sh` cannot disagree about a session name. The eval needs the *value*; the *provenance* is what it imports |

It is incidental in the strongest sense: the eval works correctly with the literal inlined, because
the literal **is** the value. Nothing about M13's mechanism (the trace CLI's `append()` semantics,
session-match logic, or the derivation/kernel machinery) is used, needed, or revealed by it.

---

## 3. But the blocker is WIDER than one import (RAN: closure computation + `tsc`)

### 3a. The reader-facing surface is `registry`, and `registry` is a barrel

`evals/registry.ts` re-exports eight evals. Importing it pulls the whole eval tree. I computed the
**transitive import closure** of seeds `[evals/registry.ts, evals/run.ts, evals/prevention.ts]` across
the real Duval tree (RAN, Python resolver over relative specifiers):

**42 modules — 13 `evals/`, 21 `src/`, 5 `tools/`, 3 `tests/`.**

Modules **outside** the eval surface that would not ship (29 files):

```
src/   adapter.ts  broker.ts  catalog.ts  commit.ts  dag.ts  decisions.ts  hash.ts
       layer.ts  ledger-tools.ts  lifecycle.ts  mcp-stdio.ts  mcp.ts  policy.ts
       probe.ts  proxy.ts  replay.ts  sandbox.ts  scope.ts  state.ts  store.ts
       transitions.ts
tools/ context/compiler.ts  derivation/kernel.ts  refs/reference.ts
       refs/resolver.ts  trace.ts
tests/ adapter-conformance.ts  ledger-tools.ts  mcp-bridge.ts
```

Three of those (`src/broker.ts`, `src/layer.ts`, `src/scope.ts`) are themselves gate-pattern-sensitive
names, and `tools/derivation/kernel.ts` is **explicitly in the M13 withhold inventory**.

### 3b. Measured: `registry` + `eval` does not even typecheck

RAN — `tsc` against a copy of `evals/*.ts` + `docs/MISTAKES.md` only, with `evals/registry.ts` as the
entry, exits **2** with **19 × TS2307** module-resolution errors across 8 evals. The distinct missing
specifiers: `../src/adapter.ts`, `../src/mcp.ts`, `../src/state.ts` (×5 evals), `../src/sandbox.ts`
(×2), `../src/catalog.ts` (×2), `../src/policy.ts`, `../src/store.ts`, `../src/dag.ts`,
`../src/hash.ts`, `../tools/context/compiler.ts` (×4), `../tools/refs/resolver.ts`,
`../tools/refs/reference.ts`, `../tools/trace.ts`, `../tests/adapter-conformance.ts`.

So the claim "a reader who takes registry + eval gets a red build" is **confirmed and understated**: it
is not the one import that reds their build, it is **13 withheld modules** (plus, one level down, the
21-source closure). Fixing `prevention.ts`'s import **does not change this at all**.

---

## 4. And a second, larger wall: the eval binds to the author's private development history

RAN — after the import fix, the eval *compiles and executes*, then fails **4 of its own assertions**
(`EVAL prevention.detector-coverage passed=false`):

**Intrinsic failures (not artifacts):**

1. **check B — "every `automated` claim names a detector that exists": 6 of 12 rows resolve to
   nothing** — B1/B2/B4 (`scripts/sync-issues.sh`), E1 (`scripts/guardrails.sh`),
   E4 (`scripts/write-scope-guard.mjs`), E5 (`tools/trace.ts`). Check B passes a row if *any* named
   path exists (`paths.some(...existsSync...)` over a `\.(ts|sh|md|json|mjs|py)` regex), so these are
   precisely the rows whose *only* detector is a non-eval file.
2. **check C — "no mistake traces found — the trace file or session name changed"** — checks C and D
   read `traces/${TRACE_SESSION}.jsonl` (`prevention.ts:290`) and require it to be **git-tracked**
   (`git ls-files --error-unmatch`, `prevention.ts:546`). That corpus's **pinned** copy is
   `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` (sha256 `431605e6…`):
   **866,816 bytes / 573 records / 573 gated lines / 712 gate occurrences** — still the most
   disclosure-dirty artifact in the package. *(Superseded figure: the live file at 18:50:03 was 1,570,243 bytes
   and **1,031** is its line count; no state reproduces 1,031 as a gate count —
   `strategy/TRACE_PIN_REVERIFICATION.md` §3 T2.)*

**Simulation artifacts (must not be read as NC1 failures):** the two git-graph reds
("trace file is NOT in git", "un-settled frontier holds at most one non-merge commit") measured the
**workspace** git repo, because the sim directory sits inside it (`traces.commits.total=5`, i.e. the
workspace's 5 commits — not Duval's history). Check D's real assertions are *every non-tip commit has a
trace, holes = 0*. In a **fresh-history publish repo** those assertions cannot be satisfied by
construction: the package's own commits have no trace records. Reproducing them means shipping the
author's commit↔trace correspondence — i.e. the private repo map.

**What still passed** (worth recording — the invariant backbone is real):
table parses non-empty; every class declares a known status; every class section has a row and every
row a section; **stated counts agree with the table (19 / 12 / 4)**; all 10 planted-control assertions;
holes = 0. Metrics emitted: `prevention.classes=19`, `prevention.automated=12`, `prevention.manual=4`,
`prevention.mistake.traces=0`.

---

## 5. The proposed fix (verbatim, minimal) and its risk

Full diff-style specification: `strategy/NC1_FIX_PROPOSAL.md`. Core change:

```diff
--- a/evals/prevention.ts
+++ b/evals/prevention.ts
@@ -39,10 +39,6 @@
-import { DEFAULT_SESSION } from "../tools/trace.ts";
-
@@ -60,7 +56,11 @@
-const TRACE_SESSION = DEFAULT_SESSION;
+// Declared here rather than imported: this package does not ship `tools/`.
+// Must stay equal to the session filename under `traces/` and to
+// `scripts/trace-sync.sh`'s literal in the upstream repository.
+const TRACE_SESSION = "2026-09-28-duval-m0";
```

**Risk assessment — honest, all three axes:**

| axis | answer |
|---|---|
| does it alter behaviour? | **No.** Same compile-time constant, same checks, same budgets, same output. |
| does it move any number NC1 claims? | **Not by itself** — 19/12/4 and every check-B/C/D outcome are unchanged. |
| does it have a *cost*? | **Yes, two.** (i) It re-introduces the exact literal-duplication the upstream comment at `prevention.ts:52-55` says caused a previous failure (green against an unswept corpus) — acceptable inside a package that ships neither `scripts/` nor a trace corpus, but a divergence hazard on republish. (ii) The inlined literal contains the token `duval`, so it **injects 1 gate hit into `evals/prevention.ts`**, which ULEAD1 measured at 0. That hit must be scrubbed by renaming the session **and the trace file it names** — which is the wider job, not this patch. |

**And the fix does not unblock the package.** It closes `prevention.ts`'s module graph (RAN: `tsc`
exit 0 for `prevention.ts` + `types.ts` + `compare.ts`) and turns the single-import red into a
*different* red. That is why the verdict is not FIXABLE.

### The two real unblocking routes, and what each costs

**Route 1 — ship the detector set (≈ 8 more files), including the M13 block.**
Green check B needs `scripts/sync-issues.sh`, `scripts/guardrails.sh`, `scripts/write-scope-guard.mjs`,
`examples/sandbox-test.ts`, `.githooks/{pre-commit,post-commit,commit-msg}` (3 files) — and
**`tools/trace.ts`** for row E5, which **is** the M13 withhold block (`tools/**`), itself gate-dirty
(RAN: 4 hits — `:5`, `:60`, `:122`, `:380`). Plus check C/D need the pinned 0.83 MB (866,816 B / 712-occurrence) trace corpus and
the commit↔trace history. **This widens disclosure → author decision, not mine.** Per the unit card,
this route is `NOT_FIXABLE` without an explicit author call.

**Route 2 — re-scope NC1's claim so it does not rest on withheld material.**
Ship only the eval surface (`evals/*.ts` + `docs/MISTAKES.md`) behind a package-local runner that does
**not** import `registry.ts` (kills the 13-module tsc red); then either (i) ship the detectors, or
(ii) reformulate the `MISTAKES.md` table so the rows currently naming `tools/trace.ts` / `scripts/*`
name something the package ships. Option (ii) **moves NC1's headline number: 12 automated → 11** (and
possibly 12 → 8 if all six unresolvable rows are demoted to partial/manual). The paper's central
figure would change, and the change would have to be re-derived from the table rather than asserted.

---

## 6. First-run simulation — RAN, with results

Run on a copy **inside the workspace** (`scratch/unc1a/sim/`), never in Duval. The 0.83 MB pinned trace corpus
was deliberately **not** copied in. Tooling: `/home/zer0null/Duval/node_modules/.bin/tsc` 5.9.3
(read-only use, no install). System `node` v22.22.1 has no TS support, hence the emit-then-run harness.

| test | what it covers | result |
|---|---|---|
| **A** `tsc` on `prevention.ts` + `types.ts` + `compare.ts`, **pre-fix** | the reader's literal first run if they take the eval | **RED** — exit 2, exactly 1 error: `evals/prevention.ts(42,33): error TS2307: Cannot find module '../tools/trace.ts' or its corresponding type declarations.` |
| **B** same set, **post-fix** | does the proposed patch close the import? | **GREEN** — `tsc exit=0` |
| **C** `tsc` on `registry.ts` (registry + eval) | the reader's first run if they take the registry | **RED** — exit 2, 19 × TS2307 over 13 distinct withheld modules |
| **D** post-fix **eval actually executed** on the emitted JS | does the check pass? | **RED** — `passed=false`, 4 FAILs (2 intrinsic: check B 6/12 rows unresolvable, check C no traces; 2 simulation artifacts from the workspace's own git repo) |

**ULEAD1's first-run claim is PROVEN, not refuted.** Two corrections to it: the red build is *wider*
than the one import (test C), and a green build is *not* sufficient — the eval still fails 4 assertions
(test D).

---

## 7. Withheld-import list for NC1's reader surface (the deliverable list)

If NC1 ships as "registry + eval", these do **not** ship and must:

```
# directly required by the eval tree (tsc-confirmed, 13 distinct)
src/adapter.ts  src/mcp.ts  src/state.ts  src/sandbox.ts  src/catalog.ts  src/policy.ts
src/store.ts  src/dag.ts  src/hash.ts
tools/context/compiler.ts  tools/refs/resolver.ts  tools/refs/reference.ts  ../tools/trace.ts
tests/adapter-conformance.ts

# one level down (closure computation, 16 more)
src/broker.ts  src/commit.ts  src/decisions.ts  src/layer.ts  src/ledger-tools.ts
src/lifecycle.ts  src/mcp-stdio.ts  src/probe.ts  src/proxy.ts  src/replay.ts  src/scope.ts
src/transitions.ts  tools/derivation/kernel.ts  tests/ledger-tools.ts  tests/mcp-bridge.ts
```

**M13 members in that set:** `tools/trace.ts`, `tools/context/compiler.ts`,
`tools/refs/resolver.ts`, `tools/refs/reference.ts`, `tools/derivation/kernel.ts`.
(Note: the exact direct-vs-transitive split above is from my two measurements; the union is the
authoritative list.)

---

## 8. Containment

I did not write to `/home/zer0null/Duval` and ran **no git command there** — the `git ls-files` /
`git log` calls came from the emitted eval executing with cwd inside the workspace sim, which is what
made the two git-graph assertions measure the workspace repo instead of Duval.

Observation to pass on, **not** a claim about my own behaviour: a Duval mtime sweep
(`find -newermt '-30 minutes'`, excluding `node_modules/.git/.worktrees`) shows recent writes that are
not mine — `/home/zer0null/Duval/package.json` and `/home/zer0null/Duval/CONTRIBUTING.md`, both
`2026-10-15 18:26:07`, plus a large `rust/target/tests/trybuild/**/.fingerprint/**` build-artifact
churn; and `/home/zer0null/Duval/traces/2026-09-28-duval-m0.jsonl` at `18:50:03` (it grew during my
session). Target sources of interest are older and **unmodified by this workspace's units** (the root files
and the trace *were* rewritten, by the foreign actor — `strategy/CONTAINMENT_CHECK.md` §2/§7):
`evals/prevention.ts` 2026-10-14 20:03,
`tools/trace.ts` 2026-10-12 04:22, `docs/MISTAKES.md` 2026-10-06 23:43. No stray `.tsbuildinfo`,
`out/`, or `*.json.tmp` in the Duval root. **Something other than this unit is writing in the
read-only target** — worth a containment check by the orchestrator.

---

## 9. Bottom line for the gate

* The named blocker is **not** on the critical path. Fix it anyway — it is 2 lines, no risk — but do
  not score NC1 as unblocked because of it.
* NC1 as currently scoped cannot deliver a green first run without either **publishing M13's `tools/`**
  (author decision; route 1) or **restating its automated-detector count** (route 2, 12 → ≤11).
* If the author declines both, NC1 should be re-cast as a **method/format** contribution (how to
  machine-check a mistake-class table; the check-A/B/C/D shape and the planted-control design) rather
  than a shippable green package. The design is genuinely good; the *data* it binds to is private.
