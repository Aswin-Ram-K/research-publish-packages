# SYSTEM ITEM INVENTORY — standalone-paper candidates inside `/home/zer0null/Duval` (Consonance)

**Unit:** USYS1 · **Kind:** report-only inventory · **Bound:** 30 tool calls (used 12 incl. this write's predecessors)
**Target:** `/home/zer0null/Duval`, read-only (no writes, no git invoked at any point).
**Purpose of this unit:** name and describe every mechanism / subsystem / protocol / instrument / method in
the target that could plausibly be *described and evaluated on its own*, with paths, sizes, line counts,
doc anchors, on-disk evidence, coupling and public-disclosure status. **No literature/prior-art assessment
is done here** — that is the next unit's job.

## How to read the entries

- **byte sizes and line counts** were measured with `find -printf '%s'` and `wc -l` (read-only). Sizes are
  exact as of this sweep.
- **`doc anchor`** is `path:line` into a file I opened or into header lines I read with `grep -n`.
- **`UNVERIFIED`** marks anything I did not personally open (all of `src/**` and `tools/**` bodies are in
  this class: I have their path, byte size and line count from the filesystem, and their purpose from the
  design records, but I did not read the code).
- **Evidence** entries name a file that exists on disk. I did not execute anything against the target.

## Two structural notes that change the item list

1. The unit card named `consonance/src/**` and `tools/typed-channel/**`. **Neither exists in this tree.**
   The kernel sources are at `/home/zer0null/Duval/src/**` (39 files), and there is no `typed-channel`
   directory anywhere outside `node_modules` (checked `find . -maxdepth 3 -name "*typed-channel*"` → no
   hit). The typed-channel work exists as `docs/research/experiments/EXP#12-typed-channel-comparison.md`,
   `docs/DECIDER_STACK_DECISION.md` §11, and `.worktrees/lane-exp12-typed-channel` (a separate checkout,
   **not swept**). All items below therefore cite `src/**` and `tools/**` as found.
2. `docs/research/PAPER_DERIVATION.md` (46636 bytes / 719 lines) is a **working paper** that is
   byte-identical to a formerly-public MIT file (per the unit card). Its subject — the derivation loop
   *observation stream → derived state → projection, with typed references as connective tissue* — is
   therefore **already disclosed as a whole**. Its per-experiment sub-mechanisms are listed below as
   items **with that fact stated**, because a standalone paper about, say, the consume-once gate would
   overlap a document that has already been public. This is the single largest disclosure caveat in the
   inventory.

---

# A. Kernel mechanisms (`src/**`, promoted code)

## A1 — Content-addressed commit DAG with first-class merge edges

- **One-line function:** Append-only commit graph in which a state transition is a content-addressed node,
  and a merge edge is a real edge rather than an extra `parent_id`.
- **Implementation:** `src/dag.ts` — 44468 bytes / **1104 lines**; `src/commit.ts` 7610 B / 156 lines
  (the `StateCommit` record whose absence EXP#1 measured and EXP#2 built).
- **Doc anchors:** `docs/DECISION_LOG.md:567` (D-023 — "the unit of propagation is the StateCommit"),
  `docs/DECISION_LOG.md:1216` (D-042 — transition typed by a content-addressed declaration),
  `docs/DECISION_LOG.md:1262` (D-043 — "one `parent_id` column was dropping lineages"),
  `docs/research/PAPER_DERIVATION.md:249-252`, `docs/research/PAPER_DERIVATION.md:177-193` (the
  `StateCommit` absence finding).
- **Mechanism:** A state kernel needs a unit of propagation that carries lineage, not just a row. The DAG
  stores generic rows addressed by content hash; D-023 makes the node the `StateCommit`; D-043 records the
  measured defect that a single `parent_id` column silently dropped merge lineages, so merge edges became
  first-class. D-042 makes the transition itself a content-addressed declaration rather than a mutable
  field, and *position* is derived from the declaration + the DAG rather than stored (`docs/DECISION_LOG.md:1216`).
  Distinctive: the graph is the source of truth for lineage, and identity is a class at a position in a
  chain rather than a row (`docs/research/PAPER_DERIVATION.md:609-611`).
- **Evidence:** `tests/dag-merge-traversal.ts` 6357 B; `tests/commit-lineage.ts` 14688 B;
  `tests/commit-boundary.ts` 17191 B; `tests/position-not-identity.ts` 7869 B; npm scripts `dag`,
  `dag-merge`, `commit-lineage`, `commit-boundary`, `position-not-identity`.
- **Coupling:** **tightly coupled** — depends on `state.ts`, `hash.ts`, `catalog.ts`, `transitions.ts`.
- **Already public:** `partially public` — the *idea* is recorded in `PAPER_DERIVATION.md:60-68`
  (formerly-public MIT file) and D-023/D-043 are private records, but `src/dag.ts` itself was inside the
  `src/**` tree that was public under AGPL-3.0 for ~27.5 h in Oct 2026 (per the unit card). UNVERIFIED:
  whether `src/dag.ts` existed at the moment of that window.

## A2 — Observation stream → derived state (projector)

- **One-line function:** A stream of typed observations is the source; the state is a deterministic
  projection of that stream, not a narration the model writes.
- **Implementation:** `src/observation.ts` 6517 B / 142 lines; `src/commit.ts` 7610 B / 156 lines;
  `tools/derivation/stream.ts` 3742 B / 93 lines, `tools/derivation/projector.ts` 8049 B / 206 lines,
  `tools/derivation/types.ts` 3364 B / 61 lines, `tools/derivation/kernel.ts` 1048 B / 31 lines,
  `tools/derivation/exp2.ts` 12671 B / 283 lines.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:216-252` (§4.2 — the experiment and its bound);
  `docs/research/PAPER_DERIVATION.md:29-33` (the claim under test); `docs/PAUSE_STATE.md:63` (types
  promoted, engines stay in `tools/`); `docs/DECISION_LOG.md:1792` (D-053 — the promotion of types).
- **Mechanism:** The fixture authors a state the kernel's way, emits the same transition as twelve typed
  observations, and a projector reading nothing but the stream folds them back into an envelope; addresses
  are compared with the kernel's own `stateId`/`canonical`/hasher. Result recorded: `projected.id ===
  authored.id`, all twelve identity-bearing regions identical (`docs/research/PAPER_DERIVATION.md:224`).
  Two type defects were found before anything reached `src/`: the hasher is async, and `Observation` had to
  be a discriminated union over `kind` or a projector can read one kind's payload as another's
  (`docs/research/PAPER_DERIVATION.md:236-240`). The recorded bound is explicit: the fixture emits
  observations **from** the authored state, so the experiment proves the decomposition is **lossless**, not
  that the stream is independent of what it reconstructs (`:242-247`).
- **Evidence:** `docs/research/experiments/EXP#2-observation-stream-derived-state.md` 13489 B;
  npm script `exp2`; `tests/derivation-coverage.ts` 10636 B; the 16-field envelope coverage check
  (`docs/PAUSE_STATE.md:63`).
- **Coupling:** **moderate** — the engines are self-contained under `tools/derivation/` but built against
  the kernel's real `stateId`/hasher types.
- **Already public:** `already public (idea)` — this is the subject of `PAPER_DERIVATION.md` §4.2, held to
  be byte-identical to a formerly-public MIT file. A new standalone paper would need a different cut.

## A3 — First-class uncertain-effect state and the resume contract

- **One-line function:** An agent-native journal with a third value between "we did it" and "we know
  nothing": the effect is *in doubt*, and a crashed run resumes exactly once.
- **Implementation:** `tools/resume/engine.ts` 11033 B / 296 lines; `tools/resume/exp3.ts` 9406 B /
  196 lines; `tools/resume/exp3b.ts` 5423 B / 121 lines; `src/journal.ts` 46450 B / 1225 lines
  (the K0 promotion).
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:254-299` (§4.3 — measurement and the three-line
  result at `:278-282`); `docs/research/PAPER_DERIVATION.md:301-334` (§4.3b — concurrent resumption);
  `docs/research/PAPER_DERIVATION.md:556-559` ("an outcomes-only journal cannot represent ambiguity");
  `docs/DECISION_LOG.md:3997` (D-092 — the K0 redirection's six decisions).
- **Mechanism:** The journal write-ahead-records the *intent* before the side effect; `classify()` returns
  `settled` / `uncertain` / `not-dispatched` / `unknown-key`. Measured: naive retry against a
  non-idempotent effect double-executes (`occurrences=2`), a reconciling resumer gives exactly one
  occurrence, and an outcomes-only journal makes the ambiguity **invisible** rather than ambiguous
  (`journal keys=0, effect occurred 1×`) — write-ahead ordering is the load-bearing property
  (`docs/research/PAPER_DERIVATION.md:262-292`). The recorded bound: journal is in-memory, the world is
  simulated, and concurrency is excluded (which EXP#3b then supplies).
- **Evidence:** `docs/research/experiments/EXP#3-uncertain-effects-resume-contract.md` 10802 B;
  `docs/research/experiments/EXP#3b-concurrent-resumption.md` 8773 B; npm scripts `exp3`, `exp3b`,
  `journal`; `tests/journal.ts` 41719 B.
- **Coupling:** **moderate** — `tools/resume/` is a model of the kernel; `src/journal.ts` is the promoted
  kernel form.
- **Already public:** `already public (idea)` — `PAPER_DERIVATION.md` §4.3/§4.3b is the formerly-public
  MIT file's content, and `PAPER_DERIVATION.md:613-619` states the occupation explicitly.

## A4 — Consume-once atomic gate before reconcile ("a read is not a gate")

- **One-line function:** Under concurrent resumption, take a consume-once claim before the query; because
  a reconciliation is a read and a read is not a gate, only an atomic write can gate.
- **Implementation:** the claim/gate logic in `tools/resume/engine.ts` (296 lines) exercised by
  `tools/resume/exp3b.ts` (121 lines).
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:316-325` (§4.3b: "a read is not a gate", the repair,
  and F4 — a claim with an `await` between check and set is *not* a gate); `:548-554` (§5.2, the same
  finding stated as generalising beyond the project); `:329-331` (a `Map` models the requirement but a real
  gate needs atomicity in the shared store).
- **Mechanism:** Two reconciling resumers both ask "did it happen?" before either acts, are both told no,
  and both act — measured at `occurrences=2`, scaling with k (k=5 → 5). A consume-once claim taken
  *before* the query gives exactly one occurrence at k=5 and k=20. The identified load-bearing property is
  **atomicity, not earliness**: moving the `await` inside the claim relocates the race rather than closing
  it. Absence discipline extends to concurrency — a losing racer holds **nothing** rather than being told
  no. This is the mechanism behind the literature's saturation figure, identified rather than observed.
- **Evidence:** `docs/research/experiments/EXP#3b-concurrent-resumption.md` 8773 B; `tools/resume/exp3b.ts`
  (read via the experiment record only — body UNVERIFIED); npm script `exp3b`.
- **Coupling:** **moderate** — depends on `tools/resume/engine.ts` only.
- **Already public:** `already public (idea)` — `PAPER_DERIVATION.md` §4.3b/§5.2 (formerly-public MIT file).
  **This is the strongest single "standalone result" in the tree**, and it is also the most disclosed.

## A5 — Absence-only authority: `plan()` as allowlist, and indistinguishability of ungranted from nonexistent

- **One-line function:** Prohibition is the absence of a grant from `plan()`, never a check against a
  forbidden value; an ungranted reference and a nonexistent one return the same error, so the system cannot
  be probed for what the caller may not see.
- **Implementation:** `src/policy.ts` 9766 B / 262 lines; `src/state.ts` 20603 B / 543 lines;
  `src/scope.ts` 10878 B / 233 lines; `src/authority.ts` 4361 B / 94 lines; `src/catalog.ts` 15402 B /
  364 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:155` (D-009 — allowlist, no denylist);
  `docs/DECISION_LOG.md:908` (D-033 — capability discovery may only narrow);
  `docs/DECISION_LOG.md:3298` (D-085 — read-scope expands and collapses, capability growth is a new lease);
  `docs/research/PAPER_DERIVATION.md:63-64`; `docs/research/PAPER_DERIVATION.md:350-356` (the resolver
  property); `docs/BOARD.md:171-193` (the host allowlist at `src/broker.ts:362-375`).
- **Mechanism:** Two states with identical data but different grants are different states, so the diff
  answers "what did this state permit that the last did not?". Enforcement is by absence: an uncovered host
  fails as absence (`code:"upstream"`, no request, no budget spent — `docs/BOARD.md:174-178`), and the
  typed-reference resolver returns the same generic error for ungranted and nonexistent ids, which makes
  the resolver unusable as a discovery oracle. Distinctive: the security property is *unrepresentability*
  rather than a refusal path, and it survives across layers (resolver, broker, sandbox mount).
- **Evidence:** `tests/scope-enforcement.ts` 26033 B (scoped-away host → `ENETUNREACH`, 0 arrivals;
  allowed host → 1 arrival); `tests/envelope.ts` 17606 B; `tests/authority.ts` 11900 B;
  `docs/BOARD.md:176-180`.
- **Coupling:** **tightly coupled** — this is the kernel's policy core.
- **Already public:** `partially public` — the `plan()` allowlist idea is stated in `PAPER_DERIVATION.md`
  §1.3 (formerly-public file); the resolver-side indistinguishability property is stated at
  `PAPER_DERIVATION.md:350-356`. `src/policy.ts` fell in the AGPL-public `src/**` window (UNVERIFIED that
  this exact file existed then).

## A6 — Typed reference token and a five-responsibility resolver with a closed projection vocabulary

- **One-line function:** A compact reference token `@<kind>:<id>[#<pointer>][@<revision>][?<projection>]`
  that a resolver expands under lookup, authorization, revision selection, projection and budget.
- **Implementation:** `src/reference.ts` 4703 B / 114 lines (promoted type);
  `tools/refs/reference.ts` 3404 B / 97 lines, `tools/refs/resolver.ts` 7459 B / 184 lines,
  `tools/refs/exp4.ts` 10028 B / 192 lines.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:336-368` (§4.4 — seven refused controls,
  "absence is indistinguishable from non-existence" at `:350-356`, the closed vocabulary at `:354-356`);
  `docs/DECISION_LOG.md:662` (D-026 — context is a paging interface over the object graph);
  `docs/DECISION_LOG.md:1792` (D-053 — the type is promoted, the engine is not).
- **Mechanism:** The token is parsed into a `Reference` and resolved by a resolver that owns all five
  responsibilities; namespaces are derived from D-024 and the layer model rather than invented. Seven
  controls were checked first and each refused by name (malformed token, unknown kind, unknown id,
  ungranted id, unenumerated projection, bad pointer, over-budget). Result: 7/7 token forms round-trip;
  a named revision resolves to *that* revision and not head; RFC 6901 array pointers work; budgets **refuse
  rather than truncate**. The stated reason the projection vocabulary is closed: an open projection language
  is an arbitrary read primitive wearing a query string.
- **Evidence:** `docs/research/experiments/EXP#4-reference-token-methods.md` 9441 B; npm script `exp4`;
  `tests/commit-boundary.ts` and the `exp4` re-run are the only on-disk runs I found.
- **Coupling:** **standalone** to **moderate** — the resolver's mechanics were proved against a synthetic
  in-memory array, not the kernel DAG (`docs/research/PAPER_DERIVATION.md:364-365`).
- **Already public:** `already public (idea)` — `PAPER_DERIVATION.md` §4.4.

## A7 — Context engine: paging over the object graph, and the break-even as the result

- **One-line function:** Compile a step's context by paging object-graph refs instead of inlining them,
  with non-destructive re-expansion and a measured break-even.
- **Implementation:** `tools/context/compiler.ts` 31707 B / 714 lines; `tools/context/exp5.ts` 8587 B;
  `tools/context/exp13.ts` 25948 B / 553 lines; `tools/context/exp14.ts` 45327 B / 879 lines.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:370-405` (§4.5 — the control at `:376-378`, the
  table at `:381-387`, "the break-even is the result" at `:389-391`); `docs/DECISION_LOG.md:662` (D-026);
  `docs/DECISION_LOG.md:3652` (D-089 — EXP#14: the third rung is cache-free, cheaper at equal sufficiency);
  `docs/DECISION_LOG.md:3727` (D-090 — `compile()` rebuilt on `ContextWindow`).
- **Mechanism:** With 30 objects of ~2418 chars: k=0 pages 4549 vs full 73879; k=3 of 30 saves 83.9 %;
  the **break-even is k=29 of 30**, and at k=30 paging **loses** (78429 vs 73879) — the instrument can show
  paging losing. Non-destructive re-expansion holds: a ref bootstrapped at `brief` but never expanded is
  recoverable byte-identically afterwards. Over-budget expansions are dropped and named, never truncated.
  The recorded bound is that characters and not tokens are measured, the corpus is uniform, and the
  break-even is a function of the brief:full ratio (~16:1 here), not a constant.
- **Evidence:** `docs/research/experiments/EXP#5-context-engine-paging.md` 8615 B;
  `docs/research/experiments/EXP#13-collapse-depth-shadow.md` 23996 B;
  `docs/research/experiments/EXP#14-graded-depth.md` 46085 B; npm scripts `exp5`, `exp13`.
- **Coupling:** **moderate** — the engine is in `tools/`, built against kernel types and the object graph.
- **Already public:** `already public (idea)` for §4.5 of `PAPER_DERIVATION.md`; the later EXP#13/#14 rungs
  are recorded only in private docs → `partially public` for the depth-knob extension.

## A8 — Composition → lease → view ("the head is the certificate")

- **One-line function:** Derive a read-only, deterministic user-facing view from a composition of derived
  states, via a lease, without losing the grant-diff.
- **Implementation:** `src/lease.ts` 29410 B / 659 lines; `src/layer.ts` 15078 B / 382 lines;
  `tools/abstraction/compose.ts` 5424 B / 143 lines; `tools/abstraction/exp6.ts` 10547 B / 222 lines.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:407-444` (§4.6, incl. the errata at `:433-438` and
  the bound at `:440-444`); `docs/research/PAPER_DERIVATION.md:588-598` (§5.4 — two errata found by
  building); `docs/DECISION_LOG.md:1648` (D-051 — authority stays in the state, a lease is the narrow
  scope of authority for one task); `docs/DECISION_LOG.md:1720` (D-052).
- **Mechanism:** `stream → state → commit → composition → view`, every level derived from the one below.
  The measured test that mattered: two runs differing in exactly one capability produce leases whose diff
  names exactly that capability (`added=["tool:fs.read:"]`), so the abstraction does not destroy the
  grant-diff. Composition is a pure function (byte-identical recomposition); grants are within the **union**
  of the composed states' grants and are the **head's**, not an intersection — the errata that corrected
  the layer model's intersection claim. Liveness is epoch-bound: an expired grant is *unrepresentable*, not
  flagged, and no clock is read.
- **Evidence:** `docs/research/experiments/EXP#6-user-abstraction-composition.md` 8920 B; npm scripts
  `exp6`, `lease`; `tests/lease.ts` 43912 B (112 PASS / 0 FAIL per `docs/BOARD.md:382`).
- **Coupling:** **moderate** (engines in `tools/`) / **tightly coupled** for `src/lease.ts`.
- **Already public:** `already public (idea)` for `PAPER_DERIVATION.md` §4.6; `src/lease.ts` was a K0
  promotion (D-092) — UNVERIFIED whether it existed inside the public window.

## A9 — Content-addressed objects with Merkle manifests, and the body-aliasing defect

- **One-line function:** Store state payloads as content-addressed objects with Merkle manifests and
  structural sharing; `ObjectRegistry.get()` was measured returning the stored body by reference.
- **Implementation:** `src/objects.ts` 11625 B / 289 lines; `tools/objects/aliasing-probe.ts` 9847 B /
  198 lines.
- **Doc anchors:** `docs/PAUSE_STATE.md:63` (content-addressed objects, Merkle manifests with structural
  sharing, the O(n²) lineage copy stopped); `docs/research/experiments/EXP#23-object-registry-body-aliasing.md`
  17519 B (status "FROZEN at commit time"), npm script `exp23-objects`.
- **Mechanism:** Payload bodies are stored once and referenced by hash, with a Merkle manifest giving
  structural sharing, so re-deriving lineage does not copy O(n²). The exposure frozen into EXP#23 is that
  `ObjectRegistry.get()` returns the stored body **by reference**, so a caller can mutate the registry's
  copy; the pre-registered probe measures the aliasing and inspects every caller. Distinctive: the defect
  record (with controls written before the probe ran) is itself a publishable artefact about snapshot
  semantics in content-addressed stores.
- **Evidence:** `docs/research/experiments/EXP#23-object-registry-body-aliasing.md` 17519 B;
  `tools/objects/aliasing-probe.ts` 9847 B; npm script `exp23-objects`.
- **Coupling:** **tightly coupled** — `src/objects.ts` is kernel.
- **Already public:** `not public` for EXP#23 (dated `2026-10-11`, after the Oct-2026 public window as
  described in the card — UNVERIFIED as to exact dates).

## A10 — Lifecycle / teardown: load-dispose tree walk with abort-and-continue and measured budgets

- **One-line function:** A load/dispose state machine over the scope tree, where a release that hangs is
  aborted and the walk continues, with recorded budgets and a live measurement of the abort path.
- **Implementation:** `src/lifecycle.ts` 33431 B / 759 lines; `src/loop.ts` 41047 B / 946 lines;
  `tools/teardown/cases.ts` 5665 B / 146 lines, `deterministic.ts` 5666 B / 136 lines,
  `live.ts` 28487 B / 619 lines, `measure.ts` 11142 B / 219 lines, `probe.ts` 5437 B / 105 lines,
  `sink.ts` 7701 B / 230 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:2315` (D-066 — teardown promoted into `src/`, "rule 10 required
  this decision"); `docs/BOARD.md:133-151` (lane 1 item 1 and its honest limit);
  `docs/BOARD.md:197-226` (findings S1, S2, S4, S5, S7, S9, S14, S15 with line cites);
  `docs/research/TEARDOWN_LIVE_2026.md` 23718 B; `docs/research/TEARDOWN_TIMEOUT_2026.md` 40100 B;
  `docs/BOARD.md:454` (the 2000 ms step budget vs the 85 s close budget derived from systemd).
- **Mechanism:** `Loop.step()` **is** a scope; teardown walks the scope tree, and a release that does not
  settle within its budget is aborted (`unsettled`/`aborted`) and the walk continues, so one hung release
  cannot block disposal of the rest. The live falsifier fired twice at **1 ms** against a pre-registered
  **500 ms** threshold, closing falsifier A in both directions; the loud-skip path is stated to be
  *theoretical at the measured scale* — no workload is shown where the skip fires. The close budget is
  derived rather than invented: `defaultCloseDisposeTimeoutMs()` = `SYSTEMD_DEFAULT_TIMEOUT_STOP_MS` 90000
  − `CLOSE_REPORT_MARGIN_MS` 5000, overridable by `CONSONANCE_CLOSE_GRACE_MS`
  (`docs/BOARD.md:454`). Distinctive: an *externally derived* timer budget and an append-only record of the
  instrument's own defects.
- **Evidence:** `docs/research/TEARDOWN_LIVE_2026.md` 23718 B, §7.3 (instrument checks V1–V6 at
  `tools/teardown/live.ts:460-515`); `docs/research/teardown-live-manifest.json` 4508 B;
  `docs/research/teardown-live-rows.jsonl` 7940 B; `tests/lifecycle.ts` 63605 B;
  `tests/disposal-observed.ts` 12755 B; `docs/BOARD.md:135`.
- **Coupling:** **tightly coupled** — `src/lifecycle.ts` + `src/loop.ts` are the kernel runtime.
- **Already public:** `partially public` — the teardown contract is a kernel decision (D-066, private log);
  `src/lifecycle.ts` fell in the AGPL `src/**` window (UNVERIFIED whether at that revision).

## A11 — Code-pinned constitution with two independent recomputations of its root

- **One-line function:** Meta-rules materialised as data files plus code, pinned by a root hash that the
  loader must recompute; the pin is verified by two independent implementations.
- **Implementation:** `src/constitution.ts` 14579 B / 344 lines; `constitution/root.json` 999 B,
  `invariants.json` 3089 B, `mutation-classes.json` 5479 B, `permissions.json` 2395 B,
  `protected.json` 4844 B; `scripts/guardrails.sh` 42615 B.
- **Doc anchors:** `docs/DECISION_LOG.md:722` (D-028 — the constitution is code-pinned meta-rules and
  nothing else); `docs/DECISION_LOG.md:2473` (D-070 — the constitution is materialised, its root is
  pinned); `docs/DECISION_LOG.md:4099` (D-093 — root re-pin `672fa939…` → `56aa8ea3…` verified by two
  independent recomputations, `scripts/guardrails.sh` Python and `src/constitution.ts` TypeScript);
  `docs/DECISION_LOG.md:1060` (D-038 — the M0–M6 mutation budget is the constitution's initial content).
- **Mechanism:** `loadConstitution()` **refuses to start** when the recomputed root does not match the pin,
  and the re-pin procedure requires two independent recomputations — the stated reason is that a re-pin
  checked only by the code it re-pins reproduces the project's recorded A1 defect. Distinctive: governance
  data is content-addressed, and the guard is a boot-time refusal rather than a lint.
- **Evidence:** `docs/BOARD.md:351-361` (the Actions-removal re-pin); `tests/kernel.ts` 73771 B;
  `tests/invariants.ts` 27416 B; `tests/wall-immovability.ts` 9550 B; npm scripts `gates`, `invariants`.
- **Coupling:** **tightly coupled** — boot-time kernel concern.
- **Already public:** `not public` as a mechanism (the design lives in private records); `src/constitution.ts`
  and `constitution/*.json` were inside the `src/**` window only if that window post-dated P0 (UNVERIFIED).

## A12 — Typed decision declarations with epoch-bound verdicts and identity-hazard findings

- **One-line function:** A decision is a typed, content-addressed declaration; a verdict carries an epoch,
  and clock reads are kept out of the hashed payload.
- **Implementation:** `src/decisions.ts` 54156 B / 1121 lines; `src/transitions.ts` 11406 B / 280 lines;
  `src/generation.ts` 15710 B / 369 lines; `src/experiment.ts` 14789 B / 380 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:1216` (D-042); `docs/DECISION_LOG.md:2544` (D-072 — the decision
  recorder promoted into `src/`); `docs/DECISION_LOG.md:3004` (D-079 — `verdict.at` stays the carried
  epoch); `docs/research/FINDINGS_REGISTER.md:99` (F-IDENT-01 — `Verdict.at` is a clock read inside the
  hashed `State`), `:122` (F-IDENT-02 — `dag.appendCommit`'s idempotency check contains a wall clock),
  `:271` (F-IDENT-03 — `EvidenceRef.confidence` bound documented but enforced nowhere), `:294`
  (F-IDENT-04 — the broker counter leaves the hashed payload), `:144/:187/:281` (their resolutions).
- **Mechanism:** The state is content-addressed and hashed, so any clock read inside it makes identity
  unstable; the project measures this class (four identity-hazard findings, each verified by a second lane
  on a different model), resolves it by moving time to the log side (`docs/DECISION_LOG.md:1993`, D-058 —
  `epoch` leaves the state's identity) and by an epoch-bound verdict. Distinctive: the *hazard class* is
  named and a resolution protocol (refusal-only verification, log-side epoch) exists.
- **Evidence:** `tests/decision-record.ts` 74836 B (145/0 per `docs/BOARD.md:385` — 99 assertions, 0
  failures per `docs/PAUSE_STATE.md:127`); `tests/decisions-validation.ts` 12185 B; `tests/generation.ts`
  43293 B; `tests/verdict-at-epoch.ts` 29817 B; `tests/evidence-confidence.ts` 16999 B;
  `docs/research/FINDINGS_REGISTER.md:30-70` (EXP#11 findings F-EXP11-01…17).
- **Coupling:** **tightly coupled** — hashing, catalog, state.
- **Already public:** `partially public` — EXP#11's negative result is written up in
  `PAPER_DERIVATION.md:487-529` (formerly-public MIT file); the recorder promotion (D-072) is private.

## A13 — Mediated model boundary: the broker as the only egress

- **One-line function:** The model is a mediated capability rather than ambient network; every hosted
  provider request goes through a broker bound to loopback, and the host allowlist is enforced by absence.
- **Implementation:** `src/broker.ts` 24340 B / 606 lines; `src/proxy.ts` 12359 B / 359 lines;
  `src/adapters/stub-agent.ts` 24081 B / 590 lines; `src/adapter.ts` 26983 B / 609 lines;
  `src/mcp.ts` 18518 B / 454 lines; `src/mcp-stdio.ts` 13710 B / 299 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:325` (D-017 — the model is a mediated capability, not ambient
  network); `docs/DECISION_LOG.md:850` (D-032 — hosted providers reach the gateway over loopback);
  `docs/DECISION_LOG.md:936` (D-034 — per-provider credential honesty, no egress); `docs/DECISION_LOG.md:2508`
  (D-071 — the tool is the only egress); `docs/BOARD.md:171-180` (host allowlist at `src/broker.ts:362-375`,
  scope enforcement `tests/scope-enforcement.ts:371-455`).
- **Mechanism:** A granted `model` scope is checked against the upstream host before any request; an
  uncovered host fails as absence (`code:"upstream"`, no request, no budget spent). Credentials and egress
  are handled per provider with recorded honesty about what the proxy does and does not do. Distinctive:
  no network capability is granted to the worker at all; the broker is the single mediated path, and the
  host check is enforced at the boundary rather than at the policy layer (D-011, `docs/DECISION_LOG.md:187`).
- **Evidence:** `tests/broker-counter-identity.ts` 20300 B; `tests/scope-enforcement.ts` 26033 B;
  `tests/mediated-channel.ts` 14313 B; `tests/loopback-relay.ts` 11074 B; `tests/hosted-layer.ts` 28166 B;
  `tests/model-route.ts` 29172 B; `tests/mcp-bridge.ts` 62495 B; `examples/ab-demo.ts`, `real-ab.ts`.
- **Coupling:** **tightly coupled** — the broker is the kernel's egress.
- **Already public:** `partially public` — `src/broker.ts` in the AGPL window (UNVERIFIED revision);
  design rationale private (D-017/D-032/D-034/D-071).

## A14 — Sandbox/worker isolation and scope-aware mount

- **One-line function:** The worker runs inside a bubblewrap sandbox; the write mount is derived from the
  write grant's `scope`, and the tool list is *not* (a recorded open defect).
- **Implementation:** `src/sandbox.ts` 22832 B / 533 lines; `src/worker-sandboxed.ts` 14781 B / 357 lines;
  `kernel/sandbox.sh` 19771 B; `examples/sandbox-test.ts` 33809 B; `examples/isolation-test.ts` 12122 B.
- **Doc anchors:** `docs/DECISION_LOG.md:274` (D-016 — bubblewrap); `docs/DECISION_LOG.md:377` (D-019 —
  Anthropic `sandbox-runtime` evaluated, not adopted as primary); `docs/DECISION_LOG.md:484` (D-021 — the
  worker runs inside the sandbox, two bugs found by doing so);
  `docs/DECISION_LOG.md:4475` (D-097 — userns granted to `/usr/bin/bwrap` alone);
  `docs/BOARD.md:187-193` (Lane 1 item 3: scope narrows the mount, not the tool list — open).
- **Mechanism:** Isolation is validated at the boundary, not at the policy layer (D-011). The sandboxed
  worker's writable mount is computed by `workspaceWritePlan` reading the write grant's `scope`
  (`src/worker-sandboxed.ts:58-81`, called at `:136`), while its `tools` list is still
  `grants.filter(kind === "tool").map(g => g.ref)` (`:125`) — the remaining open question is whether that
  is sufficient. Distinctive: the mount decision is a *plan* derived from the state's grants, and the
  residual gap is recorded rather than closed silently.
- **Evidence:** `docs/research/EXPERIMENT_PROGRAMME.md` 13368 B; `docs/evidence/gates-2026-10-11/sandbox.out`
  13325 B and `isolation.out` 6571 B (a recorded CI gate run with `41 PASSED · 0 FAILED · 0 SKIPPED` per
  `docs/BOARD.md:55`); `tests/isolation-netns.ts` 14714 B; `tests/socket-containment.ts` 12157 B;
  `evals/FLAKE_HISTORY.md` 17117 B.
- **Coupling:** **tightly coupled**.
- **Already public:** `partially public` (`src/sandbox.ts` in the AGPL window, UNVERIFIED revision).

## A15 — Promotion seam: moving a mechanism from `tools/` into `src/` only against a measurement

- **One-line function:** A recorded promotion seam that takes an experimental artefact and admits it into
  the kernel only when a measurement justifies it, as a decision rather than a by-product.
- **Implementation:** `src/promotion.ts` 51016 B / 1076 lines; `tools/selfbuild/pilot-verdict.ts` 34657 B
  / 471 lines; `tools/selfbuild/criteria.ts` 9740 B; `src/experiment.ts` 14789 B / 380 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:3997` (D-092 — six decisions recorded together);
  `docs/DECISION_LOG.md:2315` (D-066 — rule 10 required a decision, not a by-product);
  `docs/research/PAPER_DERIVATION.md:669-672` ("nothing was promoted into `src/`; every artefact lives in
  `tools/`") and `:702-705` (promotion filed as its own open experiment);
  `docs/research/experiments/EXP#18-self-build-first-cycle.md` 30344 B.
- **Mechanism:** Experiments live in `tools/`; promotion into `src/` requires a `D-0NN` decision backed by a
  measurement, and the seam encodes what may be promoted (a type) vs what may not (an engine) —
  `src/index.ts:22-23` states "promotion of a type is not promotion of a mechanism". Distinctive: the
  repository treats promotion as a gated operation with its own tests, and the promotion of `lease`,
  `journal`, `generation`, `experiment` and `promotion` itself happened as K0 alongside the seam.
- **Evidence:** `tests/promotion.ts` 54374 B (80 assertions / 0 failures per `docs/BOARD.md:385`);
  npm scripts `promotion`, `lease`, `journal`, `generation`.
- **Coupling:** **tightly coupled**.
- **Already public:** `not public` (D-092 dated 2026-10-07+, after the Oct public window as described —
  UNVERIFIED exact dates).

## A16 — Docs gate, write-scope guard and the self-check discipline

- **One-line function:** Merge gates that verify documentation impact and that every write stays inside a
  declared write scope — with their own bypasses measured and fixed, and their self-tests run in CI.
- **Implementation:** `scripts/docs-gate.mjs` 50561 B; `scripts/docs-gate-selftest.mjs` 77561 B;
  `scripts/write-scope-guard.mjs` 11836 B; `scripts/write-scope-guard-selftest.mjs` 9993 B;
  `scripts/check-timers.py` 24578 B; `evals/prevention.ts` 38640 B; `evals/drift.ts` 60687 B.
- **Doc anchors:** `docs/DECISION_LOG.md:3133` (D-082 — the write-scope declaration, the docs gate's
  off-by-one bypass, check D's fail-closed gap); `docs/DECISION_LOG.md:3399` (D-086 — the gate's bypass
  leaks across a whole branch range); `docs/DECISION_LOG.md:3485` (D-087); `docs/DECISION_LOG.md:3813`
  (D-091); `docs/research/FINDINGS_REGISTER.md:374` (F-GATE-01 — the `Docs-Impact` bypass is evaluated one
  commit behind); `docs/research/experiments/EXP#34-selftest-in-ci.md` 16556 B;
  `docs/research/experiments/EXP#36-selftest-impl.md` 26810 B.
- **Mechanism:** Two independent guards (documentation impact; write scope) run on every commit, each with
  a paired self-test that must be able to fail. The recorded defects are the publishable part: a bypass
  evaluated one commit behind, an off-by-one that leaked across a branch range, and a check that failed
  open rather than closed. Distinctive: the guard's own bypasses are measured and recorded in the findings
  register rather than quietly patched.
- **Evidence:** `scripts/docs-gate.frozen.json` 7005 B; `scripts/docs-gate.map.json` 17729 B;
  `docs/evidence/gates-2026-10-11/RUN.md` 12155 B; `docs/evidence/gates-2026-10-11/ci-final-*.out`
  309242 B; `evals/FLAKE_HISTORY.md` 17117 B.
- **Coupling:** **standalone** as a method/instrument contribution.
- **Already public:** `not public` (D-082…D-091 all dated 2026-10-04…10-11, private log).

## A17 — Issue-tracker synchronisation with an addressable ledger

- **One-line function:** A tracker mechanism that addresses every issue for an ID and re-verifies after
  writing, after a parser defect silently dropped a row and still reported agreement.
- **Implementation:** `src/ledger-tools.ts` 34715 B / 779 lines; `scripts/sync-issues.sh` 89816 B.
- **Doc anchors:** `docs/research/FINDINGS_REGISTER.md:397` (F-ISSUE-01…03 — the tracker mechanism's named
  defects), `:420` (F-ISSUE-04 — the parser silently dropped a narrow item row, and the run still called it
  AGREE), `:539` (F-ISSUE-01…03 FIXED — the write path addresses every issue for an ID and re-verifies
  after writing); `docs/DECISION_LOG.md:3280` (D-084 — a row that bears an item ID is never dropped in
  silence; the parser's silence was the defect).
- **Mechanism:** The tool writes issue state and then **re-reads** to verify the write landed, and the
  parser's silent-drop behaviour was localised as the defect rather than the backlog. Distinctive: the
  "a run that reported AGREE while dropping a row" defect is a first-class finding about *verification
  tooling*, not about issues.
- **Evidence:** `tests/ledger-tools.ts` 51400 B; `tests/off-funnel-count.ts` / `tools/migration/off-funnel-count.ts`
  19245 B; npm scripts `issues:check`, `issues:selftest`, `issues:sync`.
- **Coupling:** **standalone** (a tool + its tests).
- **Already public:** `not public`.

---

# B. Instrument-family items (`tools/**`, `docs/research/**`)

## B1 — The absence probe and its discrimination self-test

- **One-line function:** A mechanical detector that decides PRESENT/ABSENT for each capability, with a
  self-test proving each detector can discriminate before its verdicts are believed.
- **Implementation:** `tools/absence-probe.ts` 19122 B / 444 lines.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:157-214` (§4.1 and §4.1.1 — the three runs, the four
  vacuous detectors, the positive control that returned ABSENT); `:569-586` (§5.3 — seven ways a
  self-check fails); `docs/research/experiments/EXP#1-absence-probe.md` 10805 B;
  `docs/research/experiments/LEARNINGS.md:15` (M1), `:29` (M2), `:43` (M3), `:53` (M4), `:64` (M5), `:90` (M6).
- **Mechanism:** Run 1 was INVALID because 4 of 14 detectors were vacuous — the self-test routed through
  the scope filter, so scoped detectors saw an empty corpus and returned ABSENT twice; two further
  detectors were false positives (a local variable named `observations`; the comment "Idempotent by
  construction"). Run 3 was valid with 15/15 detectors discriminating. A positive control ("the commit DAG
  exists") correctly returned ABSENT because `StateCommit` does not exist as a type in `src/` — which found
  a wrong dependency *one level up* and reordered the programme. Distinctive: the probe's failure record is
  the contribution — "Had the discrimination self-test not existed, run 1 would have produced a table that
  looked authoritative and rested on four detectors that could not discriminate."
- **Evidence:** `docs/research/experiments/EXP#1-absence-probe.md` 10805 B; npm script `absence-probe`;
  `tests/derivation-coverage.ts` 10636 B; `tests/selfbuild-boundary-absence.ts` 13438 B;
  `docs/research/experiments/LEARNINGS.md` M1–M6 at the lines above.
- **Coupling:** **standalone** — a static symbol/syntax probe over a tree.
- **Already public:** `already public (idea)` — `PAPER_DERIVATION.md` §4.1/§5.3 (formerly-public MIT file).

## B2 — Replay divergence instrument with a real zero

- **One-line function:** Measures how much a model's decision diverges when the *record* is replayed under
  a new binding or new prompt labels, against a replication arm that can report zero.
- **Implementation:** `tools/replay/exp7.ts` 8856 B / 199 lines; corpora `docs/research/l1-head-to-head.jsonl`
  63238 B, `docs/research/decision-variants.jsonl` 1197797 B, `docs/research/decision-tree-spec.json`
  178403 B.
- **Doc anchors:** `docs/research/PAPER_DERIVATION.md:446-483` (§4.7 — the table at `:454-459`, the
  control that caught two bugs at `:467-472`, the bound at `:478-483`); `docs/DECISION_LOG.md:1333`
  (D-045); `docs/research/experiments/EXP#7-replay-divergence.md` 9347 B;
  `docs/research/experiments/LEARNINGS.md:124` (M7).
- **Mechanism:** Over 4 models × 190 cases × 4 variants: REPLICATION (same request, re-issued) diverges
  **0 %** (244/244), BINDING (same record, new model) **41.8 %**, PROMPT (same record, new labels) **32.2 %**,
  STABLE (all bindings agree) **31.6 %** of cases (60/190). The instrument has a real zero because the
  corpus contains a replication arm its authors did not build for this. §4.7.1 records the control catching
  a predicate inversion that would have been published as "51 % replication divergence" and a misread field
  that reported 0 % for every pair. Distinctive: "replay reproduces the record, not the decision" is stated
  as a bounded number rather than a caveat.
- **Evidence:** repo files above; npm script `exp7`; `docs/research/l1-ladder.jsonl` 66925 B;
  `docs/research/DECISION_DECOMPOSITION_2026.md` 46819 B.
- **Coupling:** **standalone** (offline analysis of an existing corpus).
- **Already public:** `already public (idea)` — `PAPER_DERIVATION.md` §4.7.

## B3 — Judge-boundary detector: catching a self-re-pinned weakened judge

- **One-line function:** A mechanical detector for the case where a judge re-pins its own boundary and is
  thereby weakened.
- **Implementation:** `tools/judge-boundary/detect.mjs` 15736 B / 383 lines, `oracle.mjs` 18604 B /
  502 lines, `parse.mjs` 14964 B / 458 lines, `controls.mjs` 19035 B / 386 lines, `freeze.mjs` 10424 B /
  251 lines, `repin.mjs` 5512 B / 130 lines, `README.md` 8307 B.
- **Doc anchors:** `docs/research/experiments/EXP#19-judge-boundary-detector.md` 14062 B (PRE-REGISTERED
  2026-10-11); `docs/research/experiments/EXP#20-whole-source-judge-freeze.md` 25566 B (EXP#19 is CLOSED —
  its falsifier fired; EXP#19 "not edited and not deleted"); `docs/research/experiments/EXP-M4-judge-boundary-detector.md`
  14869 B; `docs/JUDGE_INTEGRITY_STATUS.md` 49980 B.
- **Mechanism:** The instrument parses a judge's freeze/pin records, detects a re-pin that weakens the
  boundary, and provides an independent semantic oracle. EXP#19's falsifier fired and it is closed; EXP#20
  is the successor experiment with whole-source freeze. Distinctive: the defect is *changed pin under a
  stable name*, and the detector is separated into parse/detect/oracle/controls roles.
- **Evidence:** the experiment files above; `docs/research/experiments/LEARNINGS.md:124` (M7, the control
  discipline) and `:152` (M8); npm scripts do not list judge-boundary (run ad hoc) — **UNVERIFIED** how it
  is executed.
- **Coupling:** **moderate** — operates on repository records.
- **Already public:** `not public` (2026-10-11 records).

## B4 — Gated-read instrument: a measured decision/router stack in front of a file-reading agent

- **One-line function:** Measures whether a gate plus a staged shortlist can cut the context a reading
  agent consumes without losing accuracy, and probes prompt-injection exposure.
- **Implementation:** `tools/gated-read/bench.py` 32186 B / 762 lines; `tools/gated-read/tasks.json` 6343 B;
  corpora `docs/research/gated-read-rows.jsonl` 2267742 B, `docs/research/gated-read-summary.json` 4278 B.
- **Doc anchors:** `docs/research/GATED_READ_2026.md` 23591 B (headings: `:11` §1 what is being tested,
  `:124` R1 the binary read gate is a weak classifier, `:165` R3 the staged shortlist stages the answer
  17/20 at 29 % file recall, `:172` R4 the router collapsed to a single method, `:192` R5 end-to-end at
  1/14 the context and zero injection exposure, `:226` R6 the injection probe contaminated its own ceiling,
  `:277` ROUND 2 designed, NOT yet run); `docs/research/GATED_READ_PROVENANCE.md` 31679 B;
  `docs/research/STAGED_EXTRACTION_PROVENANCE.md` 43738 B.
- **Mechanism:** A binary read gate decides whether to read each file; a staged shortlist chooses among
  candidates; metrics cover answer correctness, file recall, context consumed and injection exposure. The
  recorded results include a **negative**: the binary gate is a weak classifier at every setting tested, the
  router collapsed to a single method, and the injection probe contaminated its own ceiling — the
  contamination is itself reported as a result. Round 2 is designed but not run. Distinctive: a security
  claim (context reduction reduces injection exposure) measured with its own probe's contamination named.
- **Evidence:** the rows/summary/manifest JSON files above; `docs/research/EXPERIMENT_PROGRAMME_2.md`
  9207 B; `docs/research/GATED_READ_2026.md` §R7–R8.
- **Coupling:** **standalone** (a benchmark harness over a task file).
- **Already public:** `not public`.

## B5 — Three-model gate pilot and the SM state-machine/trajectory pilots

- **One-line function:** Two experimental harnesses measuring where gate decisions and state-machine
  projections hold or plateau across models and horizons.
- **Implementation:** `tools/three-model/runner.ts` 27683 B / 688 lines, `score.ts` 28299 B,
  `fixture.ts` 16640 B, `gates.ts` 5471 B, `mediation.ts` 9426 B, `types.ts` 10352 B, `world.ts` 5618 B,
  `scenarios.json` 85934 B; `tools/sm-pilot/runner.ts` 44815 B / 1077 lines, `score.ts` 28190 B,
  `baseline.ts` 20644 B, `compare.ts` 7901 B, `feasibility.ts` 11026 B, `sm-tasks.json` 31588 B,
  `sm-tasks-long.json` 243544 B, `sm-tasks-horizon.json` 367254 B.
- **Doc anchors:** `docs/research/3MODEL_PILOT_RESULTS.md` 10760 B; `docs/research/3MODEL_GATE_2026.md`
  17313 B; `docs/research/SM_PILOT_RESULTS.md` 28916 B; `docs/research/SM_PROJECTION_SHAPE.md` 6666 B;
  `docs/research/three-model-summary.json` 9078 B; `docs/research/sm-summary.json` 23479 B;
  `docs/research/sm-summary-horizon.json` 37027 B; `docs/research/sm-comparison.json` 1373 B;
  `docs/research/prem_summary.json` 392 B.
- **Mechanism:** The three-model pilot runs a gate decision through three models with mediation, and its
  ASR stayed unresolved because the base rate never materialised (`docs/research/FINDINGS_REGISTER.md:71-95`
  index). The SM pilot projects state-machine trajectories and records a **horizon plateau at ~62–65 %**.
  Distinctive: both report the shape they fail to resolve, with summary/manifest JSON and raw rows on disk.
- **Evidence:** raw row files `docs/research/three-model-rows.jsonl` 1766015 B,
  `sm-rows-long.jsonl` 2663929 B, `sm-rows-horizon.jsonl` 3134190 B, `sm-rows-baseline.jsonl` 949806 B;
  `tools/sm-pilot/sm-manifest*.json`; npm scripts `3model`, `sm:long`, `sm:horizon`, `sm:baseline`,
  `sm:compare`.
- **Coupling:** **moderate** — harnesses over task fixtures.
- **Already public:** `not public` for the pilot records; the `PAPER_DERIVATION.md`/`FINDINGS_REGISTER.md`
  index treats them as their own corpus (`docs/research/FINDINGS_REGISTER.md:82-84`).

## B6 — Typed-channel / decision-channel comparison (the missing `tools/typed-channel/`)

- **One-line function:** Tests whether constraining a *decision* field helps while constraining a
  *reasoning* field destroys it, and whether a fine-tuned encoder head beats the 4B deciders.
- **Implementation:** **no `tools/typed-channel/` directory exists** (checked: `ls tools/typed-channel` →
  `No such file or directory`; `find . -maxdepth 3 -name "*typed-channel*"` → no hit outside the docs).
  The nearest code is `src/decisions.ts` (54156 B / 1121 lines) and the `.worktrees/lane-exp12-typed-channel`
  checkout, **not swept**.
- **Doc anchors:** `docs/research/experiments/EXP#12-typed-channel-comparison.md` 13403 B;
  `docs/DECIDER_STACK_DECISION.md:356` (§11 the typed-channel lane — D-5 changes), `:358` §11.1
  constraining a decision field helps, constraining a reasoning field destroys it, `:389` §11.2 the
  crossover is N-dependent, `:411` §11.3 generative per-option probabilities are contaminated, `:436`
  §11.4 training a head is minutes, `:463` §11.6 ERRATA the encoder recommendation is weaker than written;
  `docs/research/experiments/LEARNINGS.md:434` (H2 — EXP#12-typed-channel-comparison harvest).
- **Mechanism:** The lane's own errata are the contribution: a recommendation was weakened after review, and
  the crossover was found to be N-dependent so the project's 2–8 option range straddles it. It is recorded
  as **superseded by EXP#12** in `docs/research/PAPER_DERIVATION.md:528-529` (a changed hypothesis got a
  new number, as the discipline requires).
- **Evidence:** `docs/research/decision-variants.jsonl` 1197797 B; `docs/research/l1-head-to-head.jsonl`;
  `docs/research/L1_HEAD_TO_HEAD.md` 11574 B; `docs/research/ESCALATION_LADDER_2026.md` 8243 B;
  `docs/research/TYPED_STATE_PROGRESSION_2026.md` 17479 B (headings `:11` typestate, `:133` the matrix,
  `:151` recommended primitive).
- **Coupling:** **moderate**.
- **Already public:** `not public` (private docs only).

## B7 — Replay/rollback/reversibility primitives (repeat-guard, rollback, reversibility)

- **One-line function:** Small kernel-level checks that an operation is repeatable, reversible, or
  rollback-safe, each promoted with its own conformance test.
- **Implementation:** `src/reversibility.ts` 10900 B / 223 lines; `src/rollback.ts` 7458 B / 167 lines;
  `src/replay.ts` 11386 B / 269 lines.
- **Doc anchors:** `docs/DECISION_LOG.md:3133` and D-086/D-087 (the `replay.ts` vacuous-predicate fix is
  cited at `docs/BOARD.md:383`); `docs/DECISION_LOG.md:3997` (D-092).
- **Mechanism:** `replay.ts` originally contained a vacuous predicate — `replay()` could not fail — and the
  K0 lane repaired it so that deleting an event changes the projection and `replay()` can now FAIL
  (`docs/BOARD.md:383`). Distinctive: the *vacuous predicate* is the finding: a replay function that
  cannot report a failure is the instrument-defect class of M1/M3 applied to kernel code.
- **Evidence:** `tests/replay` coverage via `tests/journal.ts` 41719 B; `tests/reversibility.ts` 13535 B;
  `tests/rollback.ts` 6325 B; `tests/repeat-guard.ts` 14515 B; npm scripts `replay` (via `suite`),
  `reversibility`, `rollback`, `repeat-guard`.
- **Coupling:** **tightly coupled**.
- **Already public:** `partially public` (kernel files in the AGPL window, UNVERIFIED revision).

---

# C. Self-build programme items (`tools/selfbuild/**`, `docs/research/selfbuild/**`)

This is the largest single body of recent work (EXP#18–#41, 30+ `tools/selfbuild/*.ts` files, 25
`docs/research/selfbuild/*` files, 20 `tests/selfbuild-*.ts` files). It is a *programme* with a custody
chain; I list the mechanisms that read as separable, and treat the programme as one item with sub-items.

## C1 — The self-build custody chain (sealed criterion → trusted source → custody writer → custody sink → evaluator-only custody)

- **One-line function:** A chain of mechanisms that makes a self-modifying build's acceptance evidence
  authentic: the criterion is sealed, the source is hash-pinned, the evaluator reads verified bytes or
  refuses, and custody of the artefacts is durable and access-controlled.
- **Implementation:** `tools/selfbuild/closure-seal.ts` 15841 B / 345 lines;
  `tools/selfbuild/live-repair-trusted-source.ts` 45880 B / 719 lines;
  `tools/selfbuild/custody-writer.ts` 19592 B / 459 lines;
  `tools/selfbuild/custody-sink.ts` 39138 B / 902 lines;
  `tools/selfbuild/evaluator-custody.ts` 41505 B / 967 lines;
  `tools/selfbuild/grant.ts` 37822 B / 834 lines;
  `tools/selfbuild/accounting.ts` 40235 B / 864 lines;
  `tools/selfbuild/admission.ts` 32797 B / 818 lines;
  `tools/selfbuild/pilot-verdict.ts` 34657 B / 471 lines;
  plus `controller.ts` 32272 B, `dispatch.ts` 38659 B, `propose.ts` 34512 B, `wire.ts` 41994 B,
  `boot.ts` 24366 B, `components/{context-selector.ts 19580 B, edit-compiler.ts 26543 B}`.
- **Doc anchors:** `docs/research/experiments/EXP#22-trusted-evidence-authenticity.md` 15099 B;
  `EXP#26-custody-writer.md` 18300 B; `EXP#27-custody-sink.md` 34255 B;
  `EXP#29-evaluator-custody.md` 28864 B; `EXP#30-kernel-custody.md` 22134 B;
  `EXP#31-pin-to-use.md` 11266 B; `EXP#32-sealed-bytes.md` 28804 B;
  `EXP#38-live-repair-resolver.md` 28159 B; `EXP#39-independent-verification.md` 11800 B;
  `docs/research/selfbuild/ARCHITECTURE_MINIMAL_KERNEL.md` 100209 B;
  `docs/research/selfbuild/BOOTSTRAP_ACCOUNTING.md` 53893 B;
  `docs/research/selfbuild/BOOTSTRAP_GRANT.md` 37459 B;
  `docs/research/selfbuild/LIVE_REPAIR_PACKET_PROPOSAL.md` 128529 B;
  `docs/DECISION_LOG.md:4285` (D-095 — the self-build's authorisation envelope: eight decisions, and the
  criterion that was refused), `:4553` (D-098 — the readiness ledger was true, and the engine did not
  exist), `:4594` (D-099 — the first run produced no candidate, the promotion seam cannot be satisfied
  mechanically); `docs/research/selfbuild/APPROVAL_RECEIPT.md` 6610 B.
- **Mechanism:** EXP#22's premise is "acceptance must be earned from a runtime-verified pinned source, or
  not at all". Each experiment is FROZEN (hypothesis, method, falsifier, budget written before the code
  runs and never edited) and each names its own defect: EXP#26 builds a production writer for a sealed
  freeze record with integrity and publication controls and *no pins*; EXP#27 adds durable publication and
  recovery; EXP#29 restricts custody access to the evaluator; EXP#31 measures what `--ro-bind-fd` actually
  guarantees; EXP#32 makes the consuming evaluator read VERIFIED bytes or REFUSE before evaluation. D-098
  and D-099 record the honest negatives: the readiness ledger was true but the engine did not exist, and
  the first run produced no candidate. Distinctive: an acceptance chain where the evaluator's own access is
  the restricted resource and where the authorisation envelope (D-095) includes a criterion that was
  **refused**.
- **Evidence:** `docs/evidence/selfbuild/` carries the CI evidence, including
  `ci-exact-head-1479a1e.txt` 463312 B, `ci-exact-head-174a901.txt` 484017 B,
  `ci-exact-head-40c1df8.txt` 526540 B, `ci-after-bootstrap-2026-10-12.txt` 312110 B,
  `baseline-ci-2026-10-12.txt` 104526 B, `baseline-ci-independent-2.txt` 105213 B,
  `baseline-ci-independent-PARTIAL.txt` 3807 B, and `APPROVAL_PACKET.v2.md.txt` 31869 B;
  tests `tests/selfbuild-accounting.ts` 42857 B, `selfbuild-grant.ts` 56790 B,
  `selfbuild-custody-sink.ts` 43724 B, `selfbuild-custody-writer.ts` 23751 B,
  `selfbuild-evaluator-custody.ts` 50257 B, `selfbuild-pilot-verdict.ts` 43415 B,
  `selfbuild-live-repair-trusted-source.ts` 36111 B, `selfbuild-wiring.ts` 63394 B,
  `selfbuild-admission.ts` 32162 B, `selfbuild-boot-matrix.ts` 44659 B, plus 10 more;
  npm scripts `selfbuild` and 25 `selfbuild:*` subcommands.
- **Coupling:** **moderate** to **tightly coupled** — the chain is built against kernel types and the
  repository's own gate, but each link has its own pre-registration and test.
- **Already public:** `not public` (all records dated 2026-10-11/12, after the Oct public window as
  described in the card — UNVERIFIED exact dates). Note `docs/research/experiments/LEARNINGS.md:790`
  references branch `release/sanitised-for-public` (H15): a *sanitised* release branch exists; whether it
  was ever published is **UNVERIFIED** and should be checked by the next unit before any "not public"
  claim is published.

## C2 — Independent verification as a separate artefact (EXP#39) and the identity-conformance run (EXP#41)

- **One-line function:** A delivered artefact is re-verified by an independent run, and the Rust state
  digest is made to reproduce the TypeScript contract.
- **Implementation:** `tools/exp41-identity-conformance/run.ts` 16803 B / 485 lines;
  `tools/exp41-identity-conformance/src/main.rs` 7717 B; `digest-table.json` 6871 B;
  `run-output.txt` 2547 B; `Cargo.toml`/`Cargo.lock`. Rust crates: `rust/crates/core-journal`,
  `core-state`, `core-protocol` (**no `*.rs` found at maxdepth 2 — UNVERIFIED as source tree**;
  `rust/` is 4609 files / 658515836 B, mostly `rust/target/`).
- **Doc anchors:** `docs/research/experiments/EXP#41-identity-conformance.md` 15598 B;
  `docs/research/experiments/EXP#39-independent-verification.md` 11800 B;
  `docs/research/experiments/LEARNINGS.md:823` (M15 — an identity contract implemented twice is a
  convention, not a contract: name the digest, the exclusions and the absent/null split).
- **Mechanism:** A second implementation (Rust) must reproduce the TypeScript state digest exactly; the
  digest table and run output are on disk. M15 is the generalised lesson: without naming the digest, the
  exclusions and the absent/null split, two implementations diverge while both passing. Distinctive: cross-
  language identity conformance as a *measured* experiment with a frozen pre-registration.
- **Evidence:** `tools/exp41-identity-conformance/run-output.txt` 2547 B and `digest-table.json` 6871 B;
  npm script `rust:test`; `docs/research/experiments/EXP#41-identity-conformance.md`.
- **Coupling:** **moderate**.
- **Already public:** `not public`.

## C3 — Accounting reservation binding driven through the dispatch seam (EXP#24)

- **One-line function:** The accounting's exact request binding is driven through the dispatch seam rather
  than inferred.
- **Implementation:** `tools/selfbuild/accounting.ts` 40235 B / 864 lines; `tests/selfbuild-accounting.ts`
  42857 B.
- **Doc anchors:** `docs/research/experiments/EXP#24-accounting-reservation-binding.md` 12856 B (status
  "FROZEN at commit time… the question, and what inspection found before anything ran").
- **Mechanism:** A budget/accounting mechanism must bind a reservation to the exact request that will spend
  it; the experiment drives it through the dispatch seam (the real call path) instead of asserting the
  binding from inspection. Distinctive: "the accounting's exact request binding" as a falsifiable
  pre-registered claim, with the inspection findings written down *before* the controls ran.
- **Evidence:** the experiment file and test above; npm script `selfbuild:accounting`.
- **Coupling:** **moderate**.
- **Already public:** `not public`.

## C4 — The closure-seal / sealed-bytes pair (pin-to-use)

- **One-line function:** Seal the bytes that a self-build will consume, and make the consumer read only
  verified bytes or refuse.
- **Implementation:** `tools/selfbuild/closure-seal.ts` 15841 B / 345 lines;
  `tools/selfbuild/product-worker.ts` 13766 B; `tools/selfbuild/custody-writer.ts` 19592 B / 459 lines.
- **Doc anchors:** `docs/research/experiments/EXP#31-pin-to-use.md` 11266 B (what `--ro-bind-fd` actually
  guarantees); `docs/research/experiments/EXP#32-sealed-bytes.md` 28804 B (make the consuming evaluator
  read VERIFIED bytes or REFUSE before evaluation); `docs/research/experiments/LEARNINGS.md:530` (H6 —
  EXP#31-pin-to-use harvest).
- **Mechanism:** The kernel launches the sandbox with a read-only bind of a *file descriptor* rather than a
  path, and the experiment asks what that actually guarantees (the answer is recorded rather than assumed);
  the successor experiment makes the evaluator's read fail closed on unverified bytes. Distinctive: the
  threat model is *the evaluator is the adversary's target*, and the repair is a refusal before evaluation
  rather than a check inside it.
- **Evidence:** both experiment files; `tools/selfbuild/kernel-custody-probe.sh` 11325 B;
  `docs/research/experiments/EXP#30-kernel-custody.md` 22134 B.
- **Coupling:** **moderate**.
- **Already public:** `not public`.

---

# D. Method contributions (the repository's own research discipline)

## D1 — Instrument-validation-before-measurement discipline and the M1–M15 learnings ledger

- **One-line function:** Every measurement instrument must demonstrate it can report the opposite of what it
  reports, and each failure of that rule is harvested as a numbered learning.
- **Implementation:** `docs/research/experiments/LEARNINGS.md` 72332 B / **864 lines** (append-only);
  `docs/research/PAPER_DERIVATION.md:146-151` and `:569-586`;
  `docs/research/FINDINGS_REGISTER.md` 53144 B / 642 lines.
- **Doc anchors:** `docs/research/experiments/LEARNINGS.md:15` M1 through `:823` M15 — the headings I read:
  `:15` M1 self-test sharing the detector's selection logic; `:29` M2 loose pattern false positive;
  `:43` M3 a no-op edit that breaks the file and a piped check masking it; `:53` M4 a control wrong about
  the system; `:64` M5 static-corpus validation has unknown false-positive rate; `:90` M6 a presence-only
  probe cannot express WHERE; `:124` M7 a control catches a predicate inversion; `:152` M8 an answerable
  prompt makes the router answer; `:197` M9 a mechanism promoted with falsifiers unrun is built not
  verified; `:214` M10 an admitted fix with no bound on its size is a question-hardening machine;
  `:236` M11 an effect smaller than the MDE is unresolved not absent; `:260` M12 a published crossover can
  be an artefact of what the losing side was allowed to be; `:297` M13 a shadow arm is named for the
  operation it must perform; `:341` M14 a check's INPUTS must come from the subject; `:823` M15 an identity
  contract implemented twice is a convention not a contract. Branch harvests H1–H15 follow at `:401-822`.
- **Mechanism:** The ledger is append-only and each entry names the failure, the instance and the rule. The
  unifying statement is M7's: a control designed to be able to report **zero** is falsifiable in a way a
  positive result is not. The repository repeatedly records that the same failure class recurs after being
  written up — "it arrived a fourth time, in a probe written by someone who had just written up the
  previous three" (`docs/research/PAPER_DERIVATION.md:173-175`). Distinctive: a *method* paper is available
  here without any of the kernel, and the negative results are as complete as the positive ones.
- **Evidence:** `docs/research/experiments/LEARNINGS.md` (864 lines, M1–M15 + H1–H15);
  `docs/research/FINDINGS_REGISTER.md` (F-IDENT-01…04 at `:99/:122/:271/:294`, F-TOOL-01 at `:348`,
  F-GATE-01 at `:374`, F-ISSUE-01…04 at `:397/:420`); `docs/MISTAKES.md` 46367 B;
  `evals/FLAKE_HISTORY.md` 17117 B; `docs/research/experiments/EXP#19`, `#20`, `#M4`.
- **Coupling:** **standalone** — readable without the kernel.
- **Already public:** `partially public` — M1–M7 and the "seven ways a self-check fails" table are in
  `PAPER_DERIVATION.md:569-586` (formerly-public MIT file); M8–M15 and the H-harvests are private-only.

---

# E. Cross-cutting items on the boundary of "mechanism"

- **E1 — The trace corpus and hash-chained evidence ledger.** `traces/2026-09-28-duval-m0.jsonl`
  1840886 B (live path); `tools/trace.ts` 20837 B; `scripts/trace-sync.sh` 8155 B;
  `docs/TRACES.md` 9503 B. Recorded state: coverage is verified by the evals but **integrity is not
  gate-verified** — `trace verify` fails at line 536 (seq 527 twice) per `docs/BOARD.md:481`; the pinned
  copy elsewhere is 866816 B / 573 records. Evidence: `evals/prevention.ts` (`traces.commits.untraced = 0`),
  `docs/research/experiments/LEARNINGS.md:559` (H7 — EXP#37-trace-sync-selftest). Coupling: **moderate**.
  Already public: `not public`.
- **E2 — Naming/identity consolidation and the publication pass.** `docs/DECISION_LOG.md:1553` (D-049 —
  one name on every live surface, an archive for the old one), `:1602` (D-050), `:2687` (D-075 — the
  documentation transport rule and the publication pass), `:1835` (D-054 — "the repository stays private").
  `docs/consolidation/*` (6 files, 84382 B total) is the consolidation record.
  `LEARNINGS.md:790` H15 names branch `release/sanitised-for-public`. Coupling: **standalone** as a
  release-engineering account. Already public: **UNVERIFIED** — this is the item that most needs checking
  against the actual public window before any disclosure claim is made.
- **E3 — The kernel as a whole (`kernel/`).** `kernel/loop.ts` 46944 B / 839 lines, `kernel/tools.ts`
  36070 B / 739 lines, `kernel/sandbox.sh` 19771 B, `kernel/model.ts` 8711 B / 191 lines,
  `kernel/main.ts` 4942 B / 116 lines, `kernel/status.ts` 9510 B / 166 lines,
  `kernel/backlog.ts` 6025 B / 124 lines, `kernel/ledger.json` 12357 B,
  `kernel/seed/goal.md` 35355 B, `kernel/README.md` 6522 B. A separate agent-loop/scaffold around the
  library — likely a "second implementation" item, but I did **not** open it and cannot describe its
  mechanism. Coupling: **UNVERIFIED**. Already public: **UNVERIFIED**.
- **E4 — `src/invariants.ts` (47384 B / 964 lines) and `src/dag.ts`'s neighbourhood.** Named as part of the
  "invariant wall" in `docs/DECISION_LOG.md:4368` (D-096 — the invariant wall's three measured defects: a
  structural gap, a tautology, and a word list) and `docs/MISTAKES.md`. I did not open the file: the
  mechanism is **UNVERIFIED**, but D-096's three-defect framing is a ready-made standalone result.
  Evidence: `tests/invariants.ts` 27416 B, `tests/wall-immovability.ts` 9550 B, npm script
  `wall-immovability`. Already public: `not public`.

---

# Coverage statement

**What I actually swept.** All counts are from read-only `find`/`du`/`wc`; no file in the target was
written and no git command was run at any point.

- **Enumerated, exhaustively by name/size/line count:** the top level of `/home/zer0null/Duval` (34
  entries), `src/` (39 files, 754461 B), `tools/` (116 files, 2638021 B — all 116 listed), `kernel/`
  (10 files), `constitution/` (5 files), `guidance/` (12 files), `evals/` (18 files), `tests/` (63 files,
  all listed), `scripts/` (20 files, all listed), `examples/` (4 files), `runs/` (13 files),
  `docs/` top level (58 files, all listed), `docs/research/` top level (86 files, all listed),
  `docs/research/experiments/` (40 files, all listed), `docs/research/selfbuild/` (25 files, all listed),
  `docs/consolidation/` (6 files, all listed), `docs/evidence/` (listed to depth 2),
  `package.json` script names (all 130+).
- **Read in full (3 files):** `docs/research/PAPER_DERIVATION.md` (46636 B / 719 lines),
  `docs/BOARD.md` (42902 B / 497 lines), `docs/PAUSE_STATE.md` (12400 B / 144 lines). Plus
  `src/index.ts` (35 lines, via `cat -n`) and `docs/PLAN.md` / `AGENTS.md` for the workspace contract.
- **Read partially, by heading or line range:** `docs/research/FINDINGS_REGISTER.md` (headings + lines
  71-95), `docs/research/experiments/LEARNINGS.md` (headings only, M1–M15 + H1–H15),
  `docs/DECISION_LOG.md` (all `## D-0NN` heading lines with their line numbers, D-001…D-099; **no entry
  body read**), `docs/DECIDER_STACK_DECISION.md` (headings only), `docs/research/TYPED_STATE_PROGRESSION_2026.md`
  and `docs/research/GATED_READ_2026.md` (headings only), the first ~14 lines of all 40
  `docs/research/experiments/EXP*.md`.
- **Listed but NOT opened:** every file in `src/**` (39), `tools/**` (116), `tests/**` (63), `evals/**`
  (16), `scripts/**` (20), `kernel/**` (10), `constitution/**` (5), `guidance/**` (12), `examples/**` (4),
  and all of `docs/` except the three full reads above. Their purpose is inferred from the design records
  and filenames; **their internal mechanism is `UNVERIFIED`**.
- **Not reached at all:** `.worktrees/**` (ten separate checkouts: CORPUS, D128129, DENT, DLRP, GATE,
  INTEG, MAINT, P3-CLIENT, P3-CORE, P3-DAEMON) — this is where several lanes' live work sits, including
  `lane-exp12-typed-channel` per `docs/BOARD.md:338`; `rust/target/**` (build output) and effectively
  `rust/crates/**` (no `.rs` found at depth 2 — the Rust sources are **UNVERIFIED**, which weakens item C2);
  `node_modules/**`; `tmp/**` (147 files / 15860990 B); `scratch/**` (74 files / 3068299 B);
  `source-material/**` (53 files / 2337884 B); `archive/**` (3 files); `docs/evidence/**` beyond depth 2
  (the `ci-exact-head-*.txt` family was listed by size only); `docs/research/EXP#11-evidence/**` (20 files /
  10828388 B) and `docs/research/EXP#12-evidence/**` (26 files / 698746 B), `docs/research/BIOMAP/**`
  (9 files / 259645 B), `docs/migration/**`, `docs/evidence/gates-2026-10-11/**` bodies.
- **No completeness is claimed.** The tree is large (docs alone 47079295 B across 339 files) and the bound
  was 30 tool calls. Sampling rule actually used: enumerate everything by path/size, open the three
  narrative/design records in full, and take headings for the rest. Items E3 (`kernel/`) and E4
  (`src/invariants.ts`) are named precisely because a reader would otherwise think they were covered.
- **One scope caveat that must travel with this inventory:** the ROUND-2 gated read, EXP#2b, and several
  round-2 designs exist as *designed-not-run* records. `docs/research/GATED_READ_2026.md:277` says ROUND 2
  is "designed, NOT yet run"; `docs/research/PAPER_DERIVATION.md:702-705` says EXP#2b is filed and unbuilt.
  Any claim built on those must say "designed, not run".

---

# The items I would put forward first (12)

1. **A4 — consume-once atomic gate ("a read is not a gate").** A one-sentence, load-bearing result with
   controls that reproduce the literature's failure; the mechanism is process-independent. *Reason to lead
   with it:* it is the sharpest standalone claim in the tree, with a named repair and a named bound.
2. **D1 — the instrument-validation discipline and M1–M15 ledger.** A method paper needing none of the
   kernel; already has a unifying rule (a control that can report zero) and 15 numbered instances.
3. **A3 — the uncertain-effect third state and the resume contract.** Names a *missing state* rather than a
   simplification, with a measured three-line result; the bound (in-memory journal, simulated world) is
   fully stated.
4. **A1+A2 — content-addressed projection: observation stream → derived state.** The kernel's distinctive
   move (state as projection, identity by address) with a 16/16 result and a written bound about what a
   round-trip does not prove.
5. **B1 — the absence probe and its discrimination self-test.** A publishable *instrument* whose failure
   history (4/14 vacuous detectors, a correct ABSENT that reordered the programme) is the evidence.
6. **A6 — typed reference token + five-responsibility resolver with a closed projection vocabulary.** The
   crispest "absence is indistinguishable from non-existence" property in the repo, with 7/7 controls.
7. **A7 — context paging and the break-even result.** "The break-even is the result, not the saving" is a
   quotable methodological point, and the instrument can show paging *losing*.
8. **B2 — replay divergence with a real zero.** 41.8 % / 32.2 % against a 244/244 replication control and a
   31.6 % stable set; the control-catches-two-bugs story is included.
9. **A10 — teardown: abort-and-continue with an externally derived close budget.** An operational mechanism
   with a live falsifier that fired at 1 ms against 500 ms, plus S1–S15 defect findings already itemised.
10. **C1 — the self-build custody chain.** The largest coherent recent programme; acceptance earned from a
    runtime-verified pinned source, with an authorisation envelope that refused one criterion (D-095).
11. **A8 — composition → lease → view, and the head-is-the-certificate errata.** Directly answers whether a
    user-facing abstraction costs the grant-diff; the errata line is a standalone finding.
12. **C2 — cross-language identity conformance (Rust digest vs TypeScript contract), with M15.** A small,
    self-contained, *measured* conformance result whose lesson ("an identity contract implemented twice is a
    convention") travels beyond this project.

**Runner-up worth naming because it is ready-made and cheap:** **E4** (`src/invariants.ts`, D-096's
structural gap + tautology + word list) — three enumerated defects in an invariant wall, needing only the
file and its tests.

**Disclosure ranking that should gate sequencing:** A1–A8 and B1–B2 are covered *in idea* by the
formerly-public MIT file; C1–C4, B4, B6 and most of D1's M8–M15 are not covered by anything I could verify
as public. If the objective is a genuinely new standalone paper, the C-series and the M8–M15 material are
the least-disclosed; if the objective is to republish the derivation programme as separate short papers, the
A/B series is the material, and the prior disclosure must be stated.
