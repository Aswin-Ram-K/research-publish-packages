/**
 * reflex-decisions.ts — a hand-labelled decision set for the reflex tier.
 *
 * PURPOSE. A reflex model (Decider 0.8B/2B/4B, Kev-4B, Laya; see D-026/D-031) is a
 * non-autoregressive classifier: it picks one of 2-8 typed options in a single forward pass
 * and returns a confidence. This file is the measurement instrument for the question the
 * reflex tier exists to answer -- can the cheap model replace the expensive one? Accuracy
 * alone cannot answer it, because a reflex model's failure mode is a SILENT wrong routing
 * rather than a visible bad generation. So every case carries exactly one defensible label
 * plus the rationale for it, and calibration ("does 0.8 confidence mean 80 % correct?") is
 * scored against that same label rather than asserted.
 *
 * PROVENANCE. Hand-authored, reviewable, versioned with the code. Every case is written from
 * this system's own invariants (docs/STATE.md, docs/POLICY.md, docs/CLASSES.md,
 * docs/DECISION_LOG.md) and states the facts its answer follows from, so a reviewer can check
 * the label against a rule without reading the rest of the file. A case whose answer is not
 * derivable from a stated invariant is a broken case and is deleted or rewritten, never
 * softened -- the same rule the docs hold themselves to. Because the set is a plain source
 * file, a label change is a diff a reviewer can read and argue with, which is exactly what a
 * model-generated set can never give.
 *
 * HOW IT GROWS. These 190 cases are a seed, not the destination. Every real run already emits
 * a trace (docs/TRACES.md), and D-027 already names traces as the supervised training data
 * for deciders, compaction, retrieval and tool routing. The intended path: mine real
 * DecisionIR records from traces where the engine's deterministic outcome is known, promote a
 * case only when its label is derivable from a named invariant AND a second reviewer agrees,
 * and keep this hand-authored seed as the fixed control those mined cases are measured against. A mined case that cannot be justified in a rationale is not a case.
 *
 * ERRATA, 2026-10-01 -- three cases were corrected, and the corrections are named in place
 * rather than silently applied, because a corpus whose past labels are editable has no
 * provenance and is exactly the kind of instrument this file exists to be measured against.
 *   * `worker.class-019` and `capability.family-006` were written when scope narrowing was
 *     believed to be an OPERATIVE mechanism. EXP#9a (merged as 2b578ae) measured the opposite:
 *     `scope` was DECLARED-ONLY, with zero readers in `src/`, no emission from
 *     `materialiseGrants`, and no scope gate in `admit()` -- an out-of-scope read succeeded.
 *     The scope lane opened by D-059 then wired the reader (`src/scope.ts`, consulted at the
 *     broker boundary), so both cases now describe the mechanism as measured by
 *     `npm run scope` (tests/scope-enforcement.ts): the address space is the union of granted
 *     scopes and an address outside it has no entry, failing as ENOENT. **Labels unchanged** --
 *     an out-of-scope address is absent either way once the mechanism exists.
 *   * `capability.family-022` named the grant sort key as 'kind:ref'. Grant identity was
 *     unified to 'kind:ref:scope' (`grantKey`, src/state.ts:256), so the key text is corrected.
 *     **Label unchanged** -- the kind is still the leading segment, so the emitted order is the
 *     same.
 *
 * DIFFICULTY IS DELIBERATE. The set mixes easy and hard on purpose, because reflex error is
 * reported per band: a uniformly hard set overstates error, a uniformly easy set overstates
 * accuracy, and neither can be fixed after the fact. 28 cases have ESCALATE as the label, so
 * abstention is measured rather than assumed -- "it knows when it does not know" is exactly
 * the claim this set exists to be able to falsify.
 */

export type DecisionKind =
  | "worker.class" // which StateClass runs the next step
  | "context.package" // which refs make up the compiled state package for this step
  | "capability.family" // which capability family to surface to Needle 3
  | "memory.admission" // DROP | EPHEMERAL | EPISODIC | PROCEDURAL | PERSISTENT
  | "escalation" // ANSWER | ESCALATE
  | "topology" // SINGLE(x) | PARALLEL(x,y) | SEQUENCE(x,y) | RETURN
  | "acquisition"; // DISCARD | RETAIN_REF | EXPAND | CONTRADICTION_CHECK | ESCALATE

export interface DecisionCase {
  id: string;
  kind: DecisionKind;
  /** The question as it would be put to the model. Must be self-contained. */
  question: string;
  /** The 2-8 (never more) options, as short semantic labels. */
  options: string[];
  /** Index into options. Exactly one correct answer. */
  correct: number;
  /** Why the correct answer is correct — used in review, not fed to the model. */
  rationale: string;
  /** Namespace(s) the case draws on: task|evidence|execution|capability|policy|decision */
  namespaces: string[];
}

export const DECISION_CASES: readonly DecisionCase[] = [
  /* ==================================================================== */
  /* worker.class -- which StateClass runs the next step                  */
  /* Native classes: reasoner (output-only, grantPolicy 'none',           */
  /* canRequestEscalation false) and editor (attached, fs.read+fs.write).  */
  /* Catalogued classes used below declare their grant sets in the         */
  /* question, so each label follows from the stated policy.               */
  /* ==================================================================== */

  {
    id: "worker.class-001",
    kind: "worker.class",
    question:
      "Step 3 must emit a written critique of the diff already recorded under the execution namespace. It reads nothing from the workspace and writes nothing; its entire output is the proposal payload. The catalogue holds exactly the two native classes: reasoner (layer output-only, grantPolicy kind 'none') and editor (layer attached, grantPolicy kind 'declared' with tools fs.read and fs.write). Which StateClass runs this step?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 0,
    rationale:
      "plan() constructs the permitted set. For a grantPolicy of 'none' the construction emits model + context and nothing else, which is exactly what a pure-proposal step needs. Choosing editor would materialise two tool grants the step has no postcondition for.",
    namespaces: ["execution", "capability"],
  },
  {
    id: "worker.class-002",
    kind: "worker.class",
    question:
      "Step 2 must apply an already-admitted patch to module.ts inside the granted workspace so the on-disk digest changes before the verifier runs. No reading and no reasoning beyond applying the patch is required. Which StateClass runs this step?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 1,
    rationale:
      "editor is the only native class whose grantPolicy declares fs.write, so a step whose postcondition is an on-disk change is only satisfiable under editor. reasoner's grant set contains no write capability at all.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-003",
    kind: "worker.class",
    question:
      "Step 4 must report whether the A3_budget gate in src/policy.ts delegates on pass, by reading that file's current contents out of the workspace. The step changes no file and its whole output is a report. The catalogue holds reasoner (output-only, grantPolicy 'none') and code-review (output-only, grantPolicy 'none'). Which StateClass runs this step?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "code-review (output-only judge)"],
    correct: 1,
    rationale:
      "Hard case, and the trap is 'it does not mutate'. reasoner and code-review are both output-only, so their materialised set is model + context and fs.read is not in their vocabulary -- the read is unreachable for them, not merely unnecessary. Only editor declares fs.read. Non-mutating is not the discriminator; the grant set is.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "worker.class-004",
    kind: "worker.class",
    question:
      "One step must apply a write patch and a following step must run the unit suite. No single catalogued class declares both fs.write and test.run. The planner's rule is one class per step, and the step boundary is where capability changes. Which StateClass runs the first of the two steps?",
    options: ["editor (attached, writes)", "verifier (detached, test.run)", "no class fits"],
    correct: 0,
    rationale:
      "Identity is a property of position in the state chain, so a class is a role for exactly one step. The write half is editor; verifier's declared set has no write. Deciding which half to run first is the planner's job, not a reason to fuse two classes.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-005",
    kind: "worker.class",
    question:
      "Step 5 must append exactly one record to the memory module through a memory.write tool and must not touch any workspace file. editor's declared tools are exactly fs.read and fs.write. The catalogue also holds memory-curator (layer detached, grantPolicy declared with tool memory.write). Which StateClass runs this step?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "memory-curator (detached, memory.write)"],
    correct: 2,
    rationale:
      "'It mutates' is not the discriminator -- editor mutates too. The discriminator is the constructed grant set: memory.write is not in editor's declared tools, so the tool is not in its vocabulary, while memory-curator's policy constructs exactly that grant. The narrowest sufficient class is memory-curator.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-006",
    kind: "worker.class",
    question:
      "A proposal has arrived whose declared spend would exceed the state's budget envelope, so the A3_budget gate refuses it. The refusal must be recorded as a new state carrying the reason and the offending gate. Which StateClass runs the step that records it?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "none -- admit() mints the state"],
    correct: 2,
    rationale:
      "The gate chain is deterministic code containing no model, and only the engine mints a state. A layer may propose; it may never author. A refusal is a first-class state produced by the engine, so no class is planned for that step at all.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "worker.class-007",
    kind: "worker.class",
    question:
      "Two versions of editor are registered: 1.0.0 and 1.1.0. The head state references editor@1.0.0 by content hash, and replay from that state must reproduce the recorded path exactly. Which StateClass runs the next step?",
    options: ["editor@1.0.0 (the referenced hash)", "editor@1.1.0 (the newest)", "editor@1.1.0 (patch compatible)"],
    correct: 0,
    rationale:
      "A state references its class by hash, and that is what makes the grant set re-derivable. Switching to 1.1.0 changes the materialised grants and therefore the recorded path, so 'latest' is not a rule -- it is a silent change to history.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-008",
    kind: "worker.class",
    question:
      "A step must read workspace/src/loop.ts and return a verdict on it, and the postcondition explicitly forbids writing. The planner's rule is to select the class whose declared grant set is the smallest set that can satisfy the postconditions. The catalogue holds code-inspector (detached, declared tools ['fs.read']), reasoner (output-only, no tools) and editor (attached, declared tools ['fs.read','fs.write']). Which StateClass runs it?",
    options: ["code-inspector (detached, fs.read)", "reasoner (propose only)", "editor (attached, writes)"],
    correct: 0,
    rationale:
      "Under the stated smallest-sufficient rule the answer is code-inspector. reasoner cannot read the file at all, and editor's set is strictly larger than the postconditions require -- a wider grant than needed is a grant nobody asked for, and the grant diff is the distinctive operation of the system.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-009",
    kind: "worker.class",
    question:
      "A step must run the test suite and record its exit code, and no file may change. The catalogue holds verifier (detached, declared tools ['test.run']) and editor (attached, declared tools ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["verifier (detached, test.run)", "editor (attached, writes)", "no class reaches it"],
    correct: 0,
    rationale:
      "editor does not declare test.run, so it cannot run the suite under any narrowing; verifier's single grant is exactly the postcondition. Recording the exit code needs no second capability because the code is evidence, not a write.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-010",
    kind: "worker.class",
    question:
      "Step 1 of a task must emit a three-item plan naming the classes that should follow, and must not touch the workspace or produce any artifact. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "no class -- engine only"],
    correct: 0,
    rationale:
      "A plan that names future classes is a proposal, not an assignment: only the engine assigns a class. reasoner is the pure-proposal class and its materialised set is exactly model + context, which is all a plan needs.",
    namespaces: ["decision", "capability"],
  },
  {
    id: "worker.class-011",
    kind: "worker.class",
    question:
      "A step must write one file into the granted workspace and then stop; the postcondition is the file's existence and content hash, and nothing else is required. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 1,
    rationale:
      "The only native class that materialises a write grant is editor. A step whose postcondition is an on-disk artefact cannot be satisfied by a grant set with no write capability in it.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-012",
    kind: "worker.class",
    question:
      "A step must restate the task in one sentence using only what the current projection already carries, and must read and write nothing. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 0,
    rationale:
      "The projection is what the state shows its consumer, so the input is already materialised as a context grant. reasoner needs model + context and nothing else; editor would add two tool grants with no postcondition behind them.",
    namespaces: ["capability", "task"],
  },
  {
    id: "worker.class-013",
    kind: "worker.class",
    question:
      "A step must update one PROCEDURAL record in the memory module to reflect a method that has just proved reliable, and must touch neither the workspace nor the knowledge module. memory-curator is the catalogued class that declares memory.write; editor declares only fs.read and fs.write. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "memory-curator (detached, memory.write)"],
    correct: 2,
    rationale:
      "The postcondition names the memory module, so the class that constructs a memory.write grant is the only one whose postconditions can be satisfied. The planner selects the class; it never widens one to reach a store it does not declare.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-014",
    kind: "worker.class",
    question:
      "A step must read workspace/src/broker.ts and write a sibling file workspace/src/broker-test.ts that exercises it. Both halves are required. The catalogue holds reasoner (output-only, no tools), code-inspector (detached, ['fs.read']) and editor (attached, ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["editor (attached, writes)", "code-inspector (detached, fs.read)", "two steps, one class each"],
    correct: 0,
    rationale:
      "code-inspector satisfies half the postcondition and not the other half, so under smallest-sufficient it loses to editor. A class cannot be selected on the grounds that half of its work would fit a smaller class; the step is the unit.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-015",
    kind: "worker.class",
    question:
      "A step must write a file through an attachment point inside the sandbox, and the only class that declares a write grant for it is declared layer 'detached'. Which StateClass runs it?",
    options: ["the detached class as declared", "editor (attached, writes)", "none -- no attachment point"],
    correct: 2,
    rationale:
      "A detached layer holds no ambient capability and is materialised with no attachment point, so there is nowhere for a sandboxed write to land. The step is structurally unsatisfiable and must be refused rather than planned under a class that cannot carry it.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "worker.class-016",
    kind: "worker.class",
    question:
      "A step must run the test suite and then read the file the failing test names, in the same step, and both are required. The catalogue holds verifier (detached, ['test.run']), code-inspector (detached, ['fs.read']) and editor (attached, ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["verifier (detached, test.run)", "no class declares both", "editor (attached, writes)"],
    correct: 1,
    rationale:
      "Neither verifier nor code-inspector declares the other's tool, and editor does not declare test.run, so no class in the catalogue satisfies both postconditions. The planner must split the step at the capability boundary rather than select the closest class.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-017",
    kind: "worker.class",
    question:
      "A step must label the refusal reason already recorded on the head state so the refusal-rate metric can count refusals by stage. All inputs are present in the state; the step reads and writes nothing. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 0,
    rationale:
      "Labelling a value that is already in the projection is a pure transformation over materialised context. A refusal rate measured on preconditions and a refusal rate measured on postconditions are different diseases, so the label matters -- but the step itself needs no capability.",
    namespaces: ["decision", "policy"],
  },
  {
    id: "worker.class-018",
    kind: "worker.class",
    question:
      "A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for reasoner. Which StateClass can a reasoner step transition to in order to obtain a tool it lacks?",
    options: ["editor (attached, writes)", "reasoner (propose only)", "none -- no path exists"],
    correct: 2,
    rationale:
      "output-only is a hard ceiling, not a policy default: the escalation path is structurally absent, so no class is reachable by escalation from reasoner. A newer version of the same class is not a class transition and would not carry the write grant.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-019",
    kind: "worker.class",
    question:
      "A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker matches a scope against the address exactly as given. Which StateClass runs the step?",
    options: ["editor (attached, writes)", "reasoner (propose only)", "none -- outside every grant's scope"],
    correct: 2,
    rationale:
      "Scope narrowing is one of the four constructions of the permitted set, and it is enforced at the broker boundary — src/scope.ts, consulted by src/layer.ts's invoke() — so the root listing has no entry to resolve and the call fails as ENOENT: absence, not a refusal, and not a gate in admit(). The prohibition is structural: no class holds a grant whose scope denotes the root listing, so no class is planned for this step. ERRATA 2026-10-01: this case previously rested on narrowing being operative without naming where it is enforced; EXP#9a (2b578ae) then measured `scope` as declared-only with zero readers in src/, and the scope lane wired after it is that reader. The label is unchanged — an out-of-scope address is absent, which is the consequence the case tests.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "worker.class-020",
    kind: "worker.class",
    question:
      "A step must write the accepted summary to a file so the next state can pin it by content hash. Only one native class declares a write grant. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)"],
    correct: 1,
    rationale:
      "Producing a pinnable artefact means producing bytes at a path, and exactly one native class constructs a write grant. Storing the summary in the projection would not be pinnable by an artefact content hash.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-021",
    kind: "worker.class",
    question:
      "A state carries a class ref whose declared name and version do not match the registered class at that content hash. Which StateClass runs the next step?",
    options: ["the class registered at that hash", "the class with the matching name", "none -- the ref is forged"],
    correct: 2,
    rationale:
      "A ref whose name or version disagrees with the registered body is a forged ref and the catalogue lookup returns null for it. A state that points at nothing verifiable cannot be planned, so no class is selected and the transition is refused rather than guessed.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "worker.class-022",
    kind: "worker.class",
    question:
      "The head state's budget envelope is reasonerCalls 1, semanticCalls 0, tools 0. The remaining work is one pure judgement over the projection with no tool use. Which StateClass runs the step?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "none -- no call left"],
    correct: 0,
    rationale:
      "Budget is a second enforcement mechanism on top of the grant set, not a substitute for it. reasoner materialises model + context, which is precisely the single call the envelope permits; editor would materialise two tool grants the envelope can never pay for.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "worker.class-023",
    kind: "worker.class",
    question:
      "The head state's class is reasoner, and a transition is proposed that keeps the class and adds an fs.write grant to it. Which StateClass runs the next step?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "reasoner with an added grant"],
    correct: 1,
    rationale:
      "The grant set is constructed from the class's grantPolicy, so no transition can widen a role in place. A role change is a state transition with a different class, which is exactly what makes escalation a new state rather than a mutation of the current step's grants.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-024",
    kind: "worker.class",
    question:
      "A step must fetch a page and summarise it. The catalogue holds researcher (detached, declared tools ['web.fetch']), reasoner (output-only, no tools) and editor (attached, ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["researcher (detached, web.fetch)", "reasoner (propose only)", "editor (attached, writes)"],
    correct: 0,
    rationale:
      "web.fetch is in exactly one declared set. reasoner holds no tools and editor does not name web.fetch, so neither can reach the network; the postcondition is unsatisfiable for both. researcher's single grant is the smallest sufficient construction.",
    namespaces: ["capability", "evidence"],
  },
  {
    id: "worker.class-025",
    kind: "worker.class",
    question:
      "A step must compare two candidate patches that are both already carried in the state's resources by content hash, and emit the better one as a proposal summary. It must not touch the workspace. The catalogue holds critic (output-only, grantPolicy 'none') and editor (attached, ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["critic (output-only, no tools)", "editor (attached, writes)", "no class -- needs a read"],
    correct: 0,
    rationale:
      "Both candidates arrive as pinned resource refs, so the read has already happened and what remains is a transformation over materialised context. critic's model + context set is sufficient; editor's write grant is not asked for by any postcondition.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-026",
    kind: "worker.class",
    question:
      "The first of two steps must run the test suite so the engine can decide whether the second step's fix is needed. The class running the first step must observe the suite output before the decision is taken, and the deciding logic is the engine's. Which StateClass runs the first step?",
    options: ["verifier (detached, test.run)", "editor (attached, writes)", "no class -- engine decides"],
    correct: 0,
    rationale:
      "The suite has to actually run, and only a class that declares test.run can run it; no model can substitute for the observation. The decision between the two steps is taken afterwards by deterministic code, not by the step that observed the output.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "worker.class-027",
    kind: "worker.class",
    question:
      "A step must name which capability the next step will need, as part of its proposal payload, without requesting or receiving it. Which StateClass runs it?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "no class -- engine grants"],
    correct: 0,
    rationale:
      "Naming a need is a proposal; a role may propose capability and may never grant it to itself. reasoner is the pure-proposal class, and its set contains no tool grant to be confused with the named need.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-028",
    kind: "worker.class",
    question:
      "A layer has returned a proposal asserting that the test suite passed. Which StateClass runs the step whose outcome decides whether the commit is accepted?",
    options: ["reasoner (propose only)", "editor (attached, writes)", "none -- only a deterministic check"],
    correct: 2,
    rationale:
      "A model can never make a verdict accepted. Postconditions are checked against the world by deterministic checks; the model's assertion is stored in verification[] with its provenance and explicitly marked unverified, which makes it evidence and not a verdict.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "worker.class-029",
    kind: "worker.class",
    question:
      "Two candidate states are byte-identical except that one carries a tool grant and the other does not. Which StateClass is responsible for the difference being real rather than an artefact of comparison?",
    options: ["editor (attached, writes)", "no class -- not identity", "the granting class"],
    correct: 2,
    rationale:
      "Two states with identical data but different grants are different states, and that difference is produced by the class whose grantPolicy constructed the set. The class is therefore the thing that made the distinction real, not a label applied afterwards.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "worker.class-030",
    kind: "worker.class",
    question:
      "A step must read workspace/package.json to find the typecheck command and then write a one-line change adding a script entry. Both the read and the write are required in this one step. The catalogue holds code-inspector (detached, ['fs.read']) and editor (attached, ['fs.read','fs.write']); the planner's rule is the smallest declared grant set that satisfies the postconditions. Which StateClass runs it?",
    options: ["editor (attached, writes)", "code-inspector (detached, fs.read)", "two steps, read then write"],
    correct: 0,
    rationale:
      "code-inspector cannot satisfy the write postcondition, so the smallest-sufficient rule selects editor and keeps the read in the same step because editor declares fs.read. Splitting the step would be a planning choice, not a capability consequence.",
    namespaces: ["capability", "execution"],
  },
  /* ==================================================================== */
  /* context.package -- which refs make up the compiled package for a step  */
  /* Invariants used: the projection is derived per step and never          */
  /* accumulated; the reflex stack selects the package before the model      */
  /* sees it and may only SUBTRACT; the commit records expanded[];           */
  /* compaction is non-destructive and preserves a fixed set.                 */
  /* ==================================================================== */

  {
    id: "context.package-001",
    kind: "context.package",
    question:
      "The current step's class has its own projection spec. The parent state carries a projection computed for the previous class. Which construction produces the context for this step?",
    options: ["recompute it from the state", "carry the parent body forward", "concatenate both projections", "relist every ancestor"],
    correct: 0,
    rationale:
      "Context is a projection computed from the state for this specific step and class: not history, not a rolling window, not 'everything relevant'. Carrying the parent body forward is accumulation, which is the mechanism the projection rule exists to prevent.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-002",
    kind: "context.package",
    question:
      "The parent state's projection has a summary and a content-hashed body. This step's class names no part of that body. Structural sharing is automatic. Which parts of the parent projection may the compiler reuse?",
    options: ["the summary only", "the body, on matching hash", "both, unconditionally", "neither, ever"],
    correct: 1,
    rationale:
      "Reuse is by content, not by field: identical sub-projections share one hash, and a body the class does not name can still be carried at zero cost when its hash matches. Field-level reuse would be a policy the hashing rule does not have.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-003",
    kind: "context.package",
    question:
      "The package as compiled is 210,000 tokens and this step's explicit context budget is 80,000. The raw history is retained and re-queryable behind EXPAND and SEARCH. Which package does the step run with?",
    options: ["the full 210k package", "the compacted preserve set", "the newest 80k tokens", "nothing, and re-query later"],
    correct: 1,
    rationale:
      "Compaction is non-destructive and preserves failures, decisions, unresolved items, artifact refs and provenance; the raw history stays retrievable. A newest-N cut is the summarisation approach the design rejected as lossy by construction.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-004",
    kind: "context.package",
    question:
      "A knowledge ref in the candidate set is pinned to version v1, and the knowledge module's current head for that claim is v2. Which of the two does the compiled package carry?",
    options: ["v2, the current head", "v1, the candidate", "both, side by side", "neither, cite the locator"],
    correct: 0,
    rationale:
      "Knowledge merges by supersede, so the gate always reads the current head's label. Carrying v1 would put a claim in front of the model that the store has already retired, and a claim resting on superseded evidence is what A2 refuses.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "context.package-005",
    kind: "context.package",
    question:
      "The head state stores a tool grant with expiresAtEpoch 40, and the step being planned runs at epoch 41. Which capability families does the package carry for that grant?",
    options: ["the tool family, reissued", "model + context only", "the tool family, narrowed", "no families at all"],
    correct: 1,
    rationale:
      "Grants do not outlive the state that issued them. plan() constructs grants afresh for the step's epoch, so a grant recorded against epoch 40 contributes nothing at 41 -- the family is simply not emitted.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "context.package-006",
    kind: "context.package",
    question:
      "Two consecutive steps use the same class, the same provider family and the same schema version, and the step's state fields are byte-identical to the previous step's. Which construction of the compiled package preserves the byte-identical prefix?",
    options: ["recompute the whole prompt", "the deterministic bootstrap manifest", "a model-written summary", "the last trace lines"],
    correct: 1,
    rationale:
      "Prefix reuse is the largest measured serving win but requires a byte-identical prefix, so prompt stability is a cost property rather than tidiness. A deterministic bootstrap manifest is what makes the prefix reproducible; a model-written summary is not.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-007",
    kind: "context.package",
    question:
      "Two candidate refs have the same scheme, locator prefix and content hash but different pins. The step's package budget has ample room. How many entries does the manifest carry?",
    options: ["one, deduplicated by hash", "two, one per pin", "two, plus a merge record", "none, the pins disagree"],
    correct: 0,
    rationale:
      "Structural sharing is automatic: identical content shares one content-addressed blob, so a second pin of the same bytes adds no information to the model. Re-listing it would make the step's package grow with ref count rather than content.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-008",
    kind: "context.package",
    question:
      "The step's manifest names a ref whose summary is a pointer to another ref, and this step's postcondition does not depend on the target. The step's context budget has room for a manifest entry but not for the target's body. Which does the package carry?",
    options: ["the target's full body", "the manifest entry only", "neither, the pointer is noise", "both, plus a summary line"],
    correct: 1,
    rationale:
      "The commit records a manifest/tree ref plus expanded[] recording exactly which refs were paged in. A ref no postcondition depends on stays in the manifest and out of the page; that is what lets a later step chase the lead with EXPAND without having paid for it here.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-009",
    kind: "context.package",
    question:
      "The previous step's raw tool-result bodies total 400,000 tokens. This step's context budget is 80,000 and the step's postcondition names only the digests of those results. Which refs does the package carry?",
    options: ["the raw bodies, truncated", "the digests, by reference", "the newest 80k of bodies", "the full bodies, over budget"],
    correct: 1,
    rationale:
      "Resources are by reference plus content hash, never by value, and the content hash is what makes the state complete without being large. The postcondition asks for digests, so the digests are the whole of what the step needs.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-010",
    kind: "context.package",
    question:
      "The head state is a refusal produced by the A2_provenance gate. The next step must decide whether to re-propose the same claim. Which does the compiled package carry?",
    options: ["the refusal state and its gate", "the refused proposal only", "nothing, refusals are noise", "the evidence, not the refusal"],
    correct: 0,
    rationale:
      "A refusal is a first-class state carrying its reason and its offending gate, and the sequence must never lie about what happened. Dropping the gate makes 'which gate refused' unanswerable, which is exactly the metric the refusal-rate requirement needs.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-011",
    kind: "context.package",
    question:
      "A third party who trusts neither the engine nor the live policy must be able to confirm the grant was legitimately produced. Which field must the package carry to make that possible?",
    options: ["the policyHash provenance", "the engine's signature", "the live policy document", "the class source file"],
    correct: 0,
    rationale:
      "The grant is stored AND provenanced: policyHash lets a third party independently re-derive the grant and confirm legitimacy without trusting the writer. Storing the live policy would break the 'state plus the policy at that hash' verification model.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "context.package-012",
    kind: "context.package",
    question:
      "The step's class is reasoner (output-only, grantPolicy 'none'). The compiler's candidate list still contains a description of the fs.write tool, taken from the class documentation. What does the package do with it?",
    options: ["include it as context", "omit it entirely", "include it, redacted", "include it, read-only"],
    correct: 1,
    rationale:
      "The forbidden thing is not present in the vocabulary. An output-only class has no tool grants at all, ever, so a tool the plan never emitted must not reappear as prose -- describing a capability is how a denylist-shaped system starts.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "context.package-013",
    kind: "context.package",
    question:
      "The deterministic bootstrap manifest for this step is fixed. The reflex stack selects the package before the model sees it and is permitted to subtract from it, never to add. Which describes the resulting package?",
    options: ["the manifest, unmodified", "the manifest minus a subset", "the manifest plus a lead", "the model's chosen subset"],
    correct: 1,
    rationale:
      "Selection happens before the model sees the context, and the only operation available is subtraction. A model-chosen subset would make context selection a generation task, which is the deliberative plane's job, not the reflex plane's.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-014",
    kind: "context.package",
    question:
      "The commit for this step must let a reader determine exactly which refs were paged into it, using only the commit and the raw history. Which record makes that possible?",
    options: ["the expanded[] ref list", "the token count alone", "the model's own account", "the manifest's mtime"],
    correct: 0,
    rationale:
      "The commit carries a manifest/tree ref plus expanded[] recording exactly which refs were paged into that step. That is the difference between a package that is reconstructible and one that is merely described.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "context.package-015",
    kind: "context.package",
    question:
      "A candidate ref's pin resolves to epoch 43, while the head state is at epoch 41. A write carrying an epoch above the head cannot be ordered against the lineage. What does the compiler do with the ref?",
    options: ["include it, newer is better", "exclude it, unorderable", "include it, pinned to head", "escalate the whole step"],
    correct: 1,
    rationale:
      "Epoch is monotonic per lineage and exists to make distributed resumption safe. A ref the step cannot order against the head is not evidence about this state, and including it would let a future write masquerade as a past fact.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "context.package-016",
    kind: "context.package",
    question:
      "The state is rebuilt from its commit for a new step, and the task statement in the task namespace is unchanged. Which does the rebuilt package carry?",
    options: ["the task statement", "the task statement's digest only", "the previous step's prompt", "nothing, it is implicit"],
    correct: 0,
    rationale:
      "The task is one of the six kernel namespaces -- what the task is -- and it is in-scope for every consumer of the state. Carrying only its digest would make the state complete but unreadable, and the digest exists for verification, not for presentation.",
    namespaces: ["task", "policy"],
  },
  {
    id: "context.package-017",
    kind: "context.package",
    question:
      "Compaction is applied to fit the context budget, and it must not lose anything a later gate will read. Which set does the compacted package preserve?",
    options: ["failures, decisions, unresolved, refs", "the most recent 20 turns", "the model's summary lines", "whatever fits the budget"],
    correct: 0,
    rationale:
      "COMPACT preserves failures, decisions, unresolved items, artifact refs and provenance, and the raw history is retained and re-queryable. A recency cut is exactly the lossy reset the design refuses, because it drops failures first.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "context.package-018",
    kind: "context.package",
    question:
      "A claim in the candidate set cites an evidence ref that the execution store has already superseded with a newer hash for the same measurement. Which does the package carry?",
    options: ["the newer evidence ref", "the cited, superseded ref", "both, as a conflict", "neither, drop the claim"],
    correct: 0,
    rationale:
      "A2 refuses a claim that rests on evidence that has been superseded, so carrying the cited ref would build a package whose central claim cannot be admitted. The gate always reads the current head's label, which is the newer ref.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "context.package-019",
    kind: "context.package",
    question:
      "The candidate set contains a resource ref whose content hash already appears in the head state's resources, with the same scheme and locator. How is it represented in the package?",
    options: ["one entry, shared by hash", "two entries, one per commit", "one entry, no locator", "dropped, already seen"],
    correct: 0,
    rationale:
      "Identical resources share one content-addressed blob, so the dedupe is at the blob level and the entry is still carried -- the ref is evidence of provenance, not just content. Dropping it entirely would lose the fact that this step consulted it.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-020",
    kind: "context.package",
    question:
      "The step must diff the current workspace against the last committed artifact. The postcondition names the digest, not the bytes. Which does the package carry?",
    options: ["the artifact ref, by hash", "the artifact body inline", "the workspace listing", "neither, diff it live"],
    correct: 0,
    rationale:
      "The content hash is what makes the state complete without being large, and the postcondition asks for the digest. A live diff would be a second authority for the same fact, computed by something that was not recorded in the commit.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "context.package-021",
    kind: "context.package",
    question:
      "The parent class's projection payload holds a domain-specific field. This step's class projection spec does not name that field, and the field is not in the envelope. Which does the package carry?",
    options: ["keep it, it is in the state", "omit the field entirely", "include it as opaque text", "include it, redacted"],
    correct: 1,
    rationale:
      "A class refines the envelope's payload and may never extend it, and a projection is what this class shows its consumer. A field the spec does not name is not part of this step's context, carrying or not.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-022",
    kind: "context.package",
    question:
      "The head state carries a projection with a summary and a content-hashed body, and this step is planned from that head. Which summary reaches the package?",
    options: ["the head's own summary", "the root state's summary", "a concatenation of all", "the model's paraphrase"],
    correct: 0,
    rationale:
      "The projection is derived per step and never accumulated, so the head's summary is the one that describes the state this step continues. A paraphrase would make the summary a model output, and the summary is the state's own field.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "context.package-023",
    kind: "context.package",
    question:
      "The trace store holds 4,000 records of this run, including the model's raw completions. The commit semantics say trace events go to a separate store and never into the state. Which does the package carry?",
    options: ["no trace records at all", "the last 100 records", "the completion that was accepted", "records matching the digest"],
    correct: 0,
    rationale:
      "Commit per transition, never per event: trace events are a separate store. Inlining even a slice of the trace into the package would put events into the state and make the state grow with event count rather than transition count.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "context.package-024",
    kind: "context.package",
    question:
      "A candidate resource ref has scheme 'env' and its locator names a credential the sandbox must never hold. The state records the ref with a content hash. Which does the package carry?",
    options: ["the ref and its hash only", "the ref with the value", "the value, redacted", "nothing at all"],
    correct: 0,
    rationale:
      "Resources are by reference plus content hash, never by value, and the absence of a credential inside the boundary is the property under test. Carrying the ref and its hash records that the environment was consulted without carrying the secret.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "context.package-025",
    kind: "context.package",
    question:
      "The step must compare two candidate patches and emit the better one, and both are already pinned in the state's resources. Which does the package carry?",
    options: ["both refs, bodies by hash", "the larger patch only", "whichever the model prefers", "neither, the engine compares"],
    correct: 0,
    rationale:
      "The comparison needs both candidates, and both are already content-pinned, so the package carries two refs and reads the bodies through the hash. Choosing one before the model runs would make the step's premise a guess.",
    namespaces: ["decision", "execution"],
  },
  {
    id: "context.package-026",
    kind: "context.package",
    question:
      "Compaction is required to fit the budget, and one of the items in the preserve set is a refusal that the next step's gate decision reads directly. Which package does the step run with?",
    options: ["the compacted set, refusal dropped", "the compacted set, refusal kept", "the uncompacted package", "no package, defer the step"],
    correct: 1,
    rationale:
      "Failures and unresolved items are in the preserve set precisely because later gates read them, so the refusal survives compaction. A compacted set that omits a preserve item is not a compaction, it is a silent lossy reset.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "context.package-027",
    kind: "context.package",
    question:
      "The head state has two parents. Which does the compiled package carry about its lineage?",
    options: ["both parent refs", "the first parent only", "the count alone", "neither, lineage is metadata"],
    correct: 0,
    rationale:
      "parents is part of identity and is included in the body digest, and a merge commit is the record of reconciliation. Carrying only the count would let two different merges hash the same, defeating replay from the state alone.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "context.package-028",
    kind: "context.package",
    question:
      "The projection body is content-hashed, and a projection that embeds the wall-clock time changes its hash on every run. plan() is pure: no clock, no randomness, no I/O. Which construction keeps replay deterministic?",
    options: ["embed the step's timestamp", "cache the first run's body", "derive it from state fields", "let the model write it"],
    correct: 2,
    rationale:
      "All environment facts come from the state, never from the process. A clock reading in a hashed field is a cross-run divergence that would make replay of the same state produce a different hash, which is the property replay exists to guarantee.",
    namespaces: ["policy", "decision"],
  },
  /* ==================================================================== */
  /* capability.family -- which grant families the planner constructs.      */
  /* The kinds are model, tool, skill, resource and context. Every class    */
  /* gets model + context; grantPolicy adds the rest. Requests never add,   */
  /* denylists never subtract, and a family is not trimmed per step.        */
  /* ==================================================================== */

  {
    id: "capability.family-001",
    kind: "capability.family",
    question:
      "The step's class is reasoner, whose grantPolicy is { kind: 'none' }. The grant kinds available are model, tool, skill, resource and context, and every class always receives a model grant and a context grant. Which family set does the planner construct?",
    options: ["model + context", "model + context + tool", "model + tool", "model + context + resource"],
    correct: 0,
    rationale:
      "A grantPolicy of 'none' yields the two always-emitted grants and nothing else. The absence of a tool grant is not a check that forbade one -- it is the construction never emitting one, which is the whole point of an allowlist.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-002",
    kind: "capability.family",
    question:
      "The step's class is editor, whose grantPolicy is { kind: 'declared', tools: ['fs.read','fs.write'] }. Which family set does the planner construct?",
    options: ["model + context + tool", "model + context", "model + tool", "model + context + skill"],
    correct: 0,
    rationale:
      "grantPolicy kind 'declared' emits one tool grant per listed tool, on top of the model and context grants every class receives. The two tools are one family with two entries, not two families.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-003",
    kind: "capability.family",
    question:
      "The step's class is reasoner (grantPolicy 'none'). Its returned proposal carries requestedCapabilities: [{ kind: 'tool', ref: 'fs.write' }]. Which family set does the planner construct for this step?",
    options: ["model + context", "model + context + tool", "tool, replacing context", "model + context + tool, narrowed"],
    correct: 0,
    rationale:
      "A role may propose capability and may never grant it to itself; the request enters admit() like any other proposal. A class that could widen its own grant set from its own output would make the model the control surface, which is the design this repository exists to prevent.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "capability.family-004",
    kind: "capability.family",
    question:
      "A catalogued class declares grantPolicy { kind: 'declared', tools: ['fs.read','fs.write'] } and also declares two skills in its role spec. Which family set does the planner construct?",
    options: ["model + context + tool", "model + context + tool + skill", "model + context + skill", "model + context + tool + skill + resource"],
    correct: 0,
    rationale:
      "The construction reads grantPolicy.tools. A skill named in the role description is not a grant unless the policy emits one, so it stays in the vocabulary of the class and out of the materialised set. A wider set than the policy constructs is exactly what an allowlist forbids.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-005",
    kind: "capability.family",
    question:
      "A catalogued class declares grantPolicy { kind: 'declared', tools: [] } and one resource grant pinning a read-only artefact by content hash. No skill is declared. Which family set does the planner construct?",
    options: ["model + context", "model + context + tool", "model + context + resource", "model + context + tool + resource"],
    correct: 2,
    rationale:
      "An empty tools array contributes no tool grant, but the declared resource grant does contribute its family. A resource grant scopes what the step may see; it is a construction of the permitted set, not a capability to read anything.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-006",
    kind: "capability.family",
    question:
      "The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it declares. Which family set does the tool plane see?",
    options: ["model + context", "model + context + tool", "model + context + resource", "model + context + tool, unscoped"],
    correct: 1,
    rationale:
      "The family set is derived from a grant's presence and kind, never from its scope: src/policy.ts's materialiseGrants emits {kind:'tool', ref, scope?, expiresAtEpoch}, and the family is 'tool' whether or not a scope is attached. Scope narrows which ADDRESSES exist at the broker boundary (src/scope.ts) — how much of the tool is reachable — and it travels with the grant, so it cannot remove the family. ERRATA 2026-10-01: the previous wording asserted that narrowing 'operates inside a grant' with no enforcement point named; the mechanism above is the measured one (npm run scope). Label unchanged.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-007",
    kind: "capability.family",
    question:
      "The state being resumed from stores a tool grant with expiresAtEpoch 40, and the step being planned runs at epoch 41. Which family set does the package for this step carry?",
    options: ["model + context + tool", "model + context", "model + context + tool, reissued", "model + context + resource"],
    correct: 1,
    rationale:
      "Grants do not outlive the state that issued them, so a grant bound to epoch 40 contributes nothing at 41. Reissuing it would make expiry decorative, and the epoch binding is the property that makes a stored grant safe to resume from.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-008",
    kind: "capability.family",
    question:
      "The same class is run once with an in-process Broker and once behind a hosted MCP server. The MCP server's tools/list is derived mechanically from the grants and is never curated. How do the two family sets relate?",
    options: ["identical, the transport differs", "hosted adds a transport family", "hosted drops the skill family", "native adds the model family"],
    correct: 0,
    rationale:
      "materialise() picks the transport; it does not pick the permission set. A tool not granted is not in the Broker and not in the advertisement, so absence is literally the same property in both transports and there is no second allowlist to drift.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-009",
    kind: "capability.family",
    question:
      "The tool plane is about to compile a ToolCallIR for a network fetch. The step's class declares only ['fs.read','fs.write']. Which family set should reach the tool plane?",
    options: ["model + context + tool", "model + context", "model + context + tool + resource", "model + context + skill"],
    correct: 1,
    rationale:
      "The class does not declare a fetch tool, so no grant names it and it is not in the vocabulary of this step. A tool plane handed a family it may not use is a wider envelope than the plan authorised, and widening the envelope is a schema event, not a feature.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-010",
    kind: "capability.family",
    question:
      "The state's budget envelope has tools 0 remaining. The step's class is editor with declared tools ['fs.read','fs.write']. Which family set does the planner construct?",
    options: ["model + context", "model + context + tool", "model + context + tool, empty", "model + tool"],
    correct: 0,
    rationale:
      "Budget is a second mechanism layered on the grant set, so a class with declared tools still constructs its tool grants and the budget makes them unspendable at materialisation. The construction and the ceiling are separate facts and neither substitutes for the other.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-011",
    kind: "capability.family",
    question:
      "A change is proposed that adds one extra tool to the hosted MCP server's advertisement 'for convenience', with no corresponding grant. Which family set does the advertisement serve?",
    options: ["the same families as the grants", "grants plus the extra tool", "the extra tool only", "no tools at all"],
    correct: 0,
    rationale:
      "The advertised set is derived mechanically from the grants and never curated. A curated superset turns the layer boundary-based again and is precisely the failure the two-way subset check exists to catch, so the advertisement is the grant set by construction.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-012",
    kind: "capability.family",
    question:
      "A worker requests a model by name that differs from the one its class declared. Which grant family's absence makes that request unsatisfiable?",
    options: ["model", "context", "tool", "resource"],
    correct: 0,
    rationale:
      "The worker reads the model from the materialised model grant rather than from its own config, so the model grant is the single source of that fact. With no model grant for the requested name, the request has nothing to be satisfied against.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-013",
    kind: "capability.family",
    question:
      "The compiled prompt contract is keyed by class, provider family and schema version, and the context grant's ref is the string 'name@version'. Which family carries the class identity into the contract?",
    options: ["model", "context", "tool", "skill"],
    correct: 1,
    rationale:
      "The context grant is the one whose ref is name@version, so it is what makes the prompt contract keyable by class. A class change therefore changes the context ref, which is how two otherwise identical plans stop hashing alike.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-014",
    kind: "capability.family",
    question:
      "A proposal requesting a new capability has been admitted, and the resulting state has a different class. The current step's families were model + context. What is the next step's family set?",
    options: ["the current step's families", "the new class's declared families", "the union of both sets", "model + context + tool"],
    correct: 1,
    rationale:
      "Escalation is a class transition recorded as a new state, and each class's grants are constructed from its own grantPolicy. The grant set does not accumulate across the transition; the new state is a new continuation with its own construction.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "capability.family-015",
    kind: "capability.family",
    question:
      "A change is proposed that gives a class a denylist field, so certain tools can be listed as forbidden. Which family set results?",
    options: ["a new denial family", "the permitted families only", "an empty family set", "model + context + tool"],
    correct: 1,
    rationale:
      "A denylist says 'anything except X' and leaves the agent holding X-shaped capability with something trying to stop it. Prohibition is the absence of a grant from plan(), so the construction is unchanged and the forbidden value never enters the vocabulary.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-016",
    kind: "capability.family",
    question:
      "A class's role description reads 'applies changes with fs.write', but its grantPolicy is { kind: 'none' } and its layer is output-only. Which family set does the planner construct?",
    options: ["model + context + tool", "model + context", "model + tool", "model + context + skill"],
    correct: 1,
    rationale:
      "Prose is not a grant. The construction reads grantPolicy, so a description promising a write changes nothing about what is materialised -- which is what lets a role be rewritten without any change to the authority it holds.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-017",
    kind: "capability.family",
    question:
      "The step's class is editor with declared tools ['fs.read','fs.write'], and this particular step's postconditions require only a read. The planner has already selected the class. May it drop the fs.write family from the materialised set for this step alone?",
    options: ["yes, per-step families", "no, families emit in full", "yes, and narrow the read", "no, and split the step"],
    correct: 1,
    rationale:
      "Per-step narrowness is handled by class selection, not by trimming a class's families after selection; scope narrows within a grant, it does not delete a family. A family set that varied per step would make the plan's grant diff unable to answer what the class was allowed to hold.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "capability.family-018",
    kind: "capability.family",
    question:
      "The compiled prompt contract is content-addressed per (class, provider family, schema version). Which family does the schema version belong to, given that the context grant's ref is 'name@version' and no other grant carries a schema field?",
    options: ["model", "context", "tool", "resource"],
    correct: 1,
    rationale:
      "The context grant is the family's contract carrier, so the schema version that keys the prompt contract belongs with it. A schema version carried on a tool grant would bind the envelope's contract to one operation's scope.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-019",
    kind: "capability.family",
    question:
      "The tool plane is implemented by Needle 3, a grammar-constrained generator that compiles ActionIR into a schema-valid ToolCallIR. Which family is it given, and why is that not a modelling preference?",
    options: ["tool, grammar-constrained", "skill, it is a named capability", "resource, it resolves a ref", "model, it picks the model"],
    correct: 0,
    rationale:
      "A byte-level grammar compiled from the schemas constrains every token, so a ToolCallIR is valid by construction rather than by retry. That property is only useful for the tool plane, which is why routing it anywhere else would discard the guarantee that replaced retries.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "capability.family-020",
    kind: "capability.family",
    question:
      "A worker asks the broker for a model the transition did not materialise. The worker's own config names that model and the class's role.model names a different one. Which family's absence is the reason the request fails?",
    options: ["model", "context", "tool", "resource"],
    correct: 0,
    rationale:
      "The model grant is the only carrier of model identity, and the worker reads it from the layer rather than from its own config precisely so the grant chain stays closed. A config-named model that no grant names is not reachable, and the failure is an absence, not a message.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-021",
    kind: "capability.family",
    question:
      "The step's class is editor with declared tools ['fs.read','fs.write'], and the budget envelope has tools 1 remaining. Which family set does the planner construct?",
    options: ["model + context", "model + context + tool", "tool, one entry only", "model + tool"],
    correct: 1,
    rationale:
      "The budget bounds spend; it does not narrow the allowlist. A plan that trimmed its own grants to fit the remaining budget would make the grant a function of how much happens to be left, and the stored grant would no longer be re-derivable from the class and the policy.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-022",
    kind: "capability.family",
    question:
      "materialiseGrants() sorts the constructed grants by the string 'kind:ref:scope' — an absent scope being the empty final segment — so the policy hash is stable. Given kinds context, model and tool, which family appears first in the emitted array?",
    options: ["context", "model", "tool", "the family with the most grants"],
    correct: 0,
    rationale:
      "The sort is lexicographic on grantKey (src/state.ts:256), whose first segment is the kind, so 'context:…' precedes 'model:…' precedes 'tool:…' regardless of which class declared them. ERRATA 2026-10-01: this read 'kind:ref' and was stale — grant identity was unified to kind:ref:scope so that two grants differing only in scope are distinct capabilities. The label is unchanged: the kind is still the leading segment, so the order is still a function of the names, which is what makes the policy hash stable across runs.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-023",
    kind: "capability.family",
    question:
      "A hosted MCP server is proposed for an output-only class whose grantPolicy is 'none'. What does its tools/list contain?",
    options: ["model + context", "nothing at all", "model + tool", "the class's described tools"],
    correct: 1,
    rationale:
      "tools/list is derived from the grants, and an output-only class constructs no tool grant, so the advertisement is empty. model and context are capabilities the step holds but not things it calls, so they are not entries in a tool list.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-024",
    kind: "capability.family",
    question:
      "One class is run with an in-process Broker and another with a hosted MCP server, and both declare the same grantPolicy. Does the second run's family set differ from the first's?",
    options: ["yes, hosted is broader", "no, they are identical", "yes, native is broader", "only if a skill is declared"],
    correct: 1,
    rationale:
      "The two transports funnel through the same mediation, so the grant set is identical either way and the family sets match. Any divergence between them would be a second allowlist, which is the failure mode this refactor exists to remove.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-025",
    kind: "capability.family",
    question:
      "What makes a grant not outlive the state that issued it? The envelope defines expiresAtEpoch on CapabilityGrant and no other field carries the issuing epoch.",
    options: ["the model family", "the tool family", "every family", "no family carries it"],
    correct: 2,
    rationale:
      "The epoch binding is a property of the grant type rather than of a family, so it applies to model, context, tool, skill and resource alike. A family-specific expiry rule would make some capabilities outlive the state and the boundary would depend on the kind.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "capability.family-026",
    kind: "capability.family",
    question:
      "Two states are byte-identical except that one carries a tool grant and the other does not, and their content hashes differ. Which family's presence accounts for the difference?",
    options: ["the tool family", "the model family", "the context family", "no family; only fields matter"],
    correct: 0,
    rationale:
      "Two states with identical data but different grants are different states, and here the differing grant is the tool grant. The model and context grants are emitted for both classes identically, so they cannot be the source of the difference.",
    namespaces: ["capability", "decision"],
  },
  /* ==================================================================== */
  /* memory.admission -- which tier a candidate takes in the memory module. */
  /* EPHEMERAL: this step only. EPISODIC: this task run. PROCEDURAL: a     */
  /* repeatable method that generalises. PERSISTENT: a durable fact that is */
  /* not a method. DROP: it is not memory -- the knowledge, execution and    */
  /* meta stores own it, or it is duplicate, superseded, or already a state.*/
  /* ==================================================================== */

  {
    id: "memory.admission-001",
    kind: "memory.admission",
    question:
      "A candidate record holds a scratch list of file paths the running step considered. No later step in this task will read it and the step finishes in one call. Which tier does the memory module admit it at?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "The discriminator is the lifetime named in the record: needed by the step that is running now and by no later step. That is EPHEMERAL by definition, and admitting it at any wider tier would retain a value nothing will ever ask for.",
    namespaces: ["decision", "task"],
  },
  {
    id: "memory.admission-002",
    kind: "memory.admission",
    question:
      "A candidate record lists the classes visited so far during this task run. It is needed for the remaining steps of this run and for nothing in any later run. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 2,
    rationale:
      "Its scope is the run, not the step: several later steps will read it. EPISODIC is exactly that scope, and promoting it to PROCEDURAL or PERSISTENT would carry one run's route into a run that never walked it.",
    namespaces: ["task", "decision"],
  },
  {
    id: "memory.admission-003",
    kind: "memory.admission",
    question:
      "A candidate record is the command that regenerates the client in this repository, together with the flag that keeps the output stable. It is a method, and it applies to any future task against this repository. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 3,
    rationale:
      "A repeatable method is PROCEDURAL, and the test is whether the next task against this repository would be served by it. Note it is not PERSISTENT: PERSISTENT is for facts that are not methods, and collapsing the two would lose the distinction that makes procedures retrievable by task type.",
    namespaces: ["decision", "task"],
  },
  {
    id: "memory.admission-004",
    kind: "memory.admission",
    question:
      "A candidate record states that this repository pins its package manager in package.json. It is a fact about the project, not a method, and it will still be true next year. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 4,
    rationale:
      "A durable fact about the project that is not a procedure is PERSISTENT. Nothing about it is scoped to a step or a run, and it will be asked about by tasks that have nothing to do with the run that learned it.",
    namespaces: ["task", "decision"],
  },
  {
    id: "memory.admission-005",
    kind: "memory.admission",
    question:
      "A candidate record restates a claim the knowledge module already holds: that the gateway returns 200 on an empty body. The claim, its source and its confidence are all identical to the stored version. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "It is a claim about what is true, so the knowledge module owns it, and it is byte-identical to what that store holds. Admitting it to memory would create a second record of one fact in two stores, which is the kind of thing that later reads as a disagreement.",
    namespaces: ["evidence", "decision"],
  },
  {
    id: "memory.admission-006",
    kind: "memory.admission",
    question:
      "A candidate record is the refusal produced by the A3_budget gate on the previous step, together with its reason and its gate. The head state already carries it. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "A refusal is a first-class state, so this is already recorded where the system records it. Copying it into memory would make the same refusal countable twice and would put a state in a store whose readers do not know to re-check it against the chain.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "memory.admission-007",
    kind: "memory.admission",
    question:
      "A candidate record is a route-and-outcome table: task class X routed to path Y, 78 % success over 40 samples. The meta module owns route-and-outcome records. Which tier does the memory module admit it at?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "It is memory-shaped and it is durable, which is what makes it a trap. It belongs to the meta module because it is a statistic over runs rather than a thing a task recalls; a copy in memory would be read as a single run's outcome.",
    namespaces: ["decision", "execution"],
  },
  {
    id: "memory.admission-008",
    kind: "memory.admission",
    question:
      "A candidate record notes that the verifier's digest check for generated clients is unreliable, learned across three separate tasks in three separate runs. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 3,
    rationale:
      "Three separate tasks is the test: what generalised past the run that learned it is a method-level fact about how verification behaves here, which is PROCEDURAL. Admitted as EPISODIC it would expire with the run that discovered it, losing the very thing that generalised.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "memory.admission-009",
    kind: "memory.admission",
    question:
      "A candidate record lists the class names this step considered and rejected. It is discarded the moment the plan is made and no later step will read it. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "Its lifetime ends with the step. EPHEMERAL is the only tier whose scope is the step, and using a wider one would retain a dead exploration and make the package grow with discarded branches.",
    namespaces: ["decision", "policy"],
  },
  {
    id: "memory.admission-010",
    kind: "memory.admission",
    question:
      "A candidate record has the same content hash as a PROCEDURAL record already admitted to the memory module. The records differ in nothing but their pin. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "Identical content is already present, so the store is deduplicating rather than learning. Re-admitting the same bytes at a wider tier would silently promote a method to a fact without anyone deciding to, which is how a tier boundary erodes.",
    namespaces: ["decision", "policy"],
  },
  {
    id: "memory.admission-011",
    kind: "memory.admission",
    question:
      "A candidate record's only support is an evidence ref that the execution store has already superseded with a newer hash for the same measurement. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "A claim resting on superseded evidence is what A2 refuses, so admitting it would put a record in the store that the gate would reject if it were re-proposed. It is dropped rather than admitted at a narrower tier, because the defect is its support, not its scope.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "memory.admission-012",
    kind: "memory.admission",
    question:
      "A candidate record holds the absolute path of the workspace root for this task. The remaining steps of this run need it; no later run will, because every run gets a fresh workspace. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 2,
    rationale:
      "Later steps of the same run will read it, so it outlives the step that wrote it, which puts it at EPISODIC. The fact that the path is unique per run is exactly why it must not be PERSISTENT: a stored absolute path from a finished run is worse than no path.",
    namespaces: ["task", "execution"],
  },
  {
    id: "memory.admission-013",
    kind: "memory.admission",
    question:
      "A candidate record states that the user prefers metric units in every answer. It is a fact about a standing preference, not a method, and it holds for every future task. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 4,
    rationale:
      "A standing preference is a durable fact rather than a method, and it is scoped to no particular run. PERSISTENT is the tier whose defining property is that a future task with no relationship to this one would still want it.",
    namespaces: ["task", "decision"],
  },
  {
    id: "memory.admission-014",
    kind: "memory.admission",
    question:
      "A candidate record is the command that runs only the gate-delegation suite, discovered by reading package.json. It is a method for reproducing one specific check. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 3,
    rationale:
      "It is a method and it generalises past the run that found it, which is the PROCEDURAL test. It is not a durable fact about the project: nothing in package.json is a proposition the system should remember as true.",
    namespaces: ["policy", "task"],
  },
  {
    id: "memory.admission-015",
    kind: "memory.admission",
    question:
      "A candidate record holds the filesystem path of the broker socket this step is using. The socket is created at materialisation and removed when the step's epoch ends. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "Its lifetime is bound to the epoch that created it, so it is EPHEMERAL. Retaining a socket path past its epoch would be worse than retaining a stale grant: the next run would find a path that resolves to nothing and read that as a broken broker.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "memory.admission-016",
    kind: "memory.admission",
    question:
      "A candidate record restates a knowledge claim whose current version in the knowledge module is a different claim about the same subject. The knowledge module merges by supersede. Which tier does the memory module admit it at?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "A claim about what is true is the knowledge module's, and the store's merge rule is supersede, so this record is a retired version rather than a memory. Keeping it anywhere else would create a claim the system holds in two states at once.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "memory.admission-017",
    kind: "memory.admission",
    question:
      "A candidate record states that the upstream registry stopped publishing 32-bit images in March and will not resume. It is a fact about the world, not a method, and it outlives this project. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 4,
    rationale:
      "A durable fact that is not a method and is not scoped to a run is PERSISTENT. Its value is exactly that a task months from now, in a different repository, would still be served correctly by it.",
    namespaces: ["evidence", "decision"],
  },
  {
    id: "memory.admission-018",
    kind: "memory.admission",
    question:
      "A candidate record is the verbatim text a model returned on the previous step. It makes no claim, states no method, and its value is that it is what was returned. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "What ran and what it returned is the execution store's, and the proposal is already recorded in the state. A record with neither a claim nor a method has nothing to recall it for, so no memory tier applies to it.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "memory.admission-019",
    kind: "memory.admission",
    question:
      "A candidate record is a cached copy of the compiled prompt package, kept so the next call can reuse a byte-identical prefix. It is derived from one step's state and is rebuilt per step. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "It is derived per step and scoped to that step's prefix, so it is EPHEMERAL. The cache is a serving optimisation; storing it as memory would put a large derived artefact into a store whose readers treat contents as learned facts.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "memory.admission-020",
    kind: "memory.admission",
    question:
      "A candidate record duplicates, field for field, something the head state's resources already pin by content hash. It adds no provenance the state does not already hold. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "The state is the record of what was consulted; a memory copy adds no provenance and no retrieval value. Admitting it would put a resource in a store whose readers cannot tell a resource from a fact, which is how the two get confused later.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "memory.admission-021",
    kind: "memory.admission",
    question:
      "A candidate record holds the exact bwrap flag list used to materialise one step. The next step derives its own spec from the class and the epoch, so these flags are not reusable. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "It is a record of one step's construction, scoped to that step. If the flags were reusable across steps they would be a method and the tier would be PROCEDURAL, so the question's own condition -- that the next spec is derived afresh -- is what forces EPHEMERAL.",
    namespaces: ["capability", "execution"],
  },
  {
    id: "memory.admission-022",
    kind: "memory.admission",
    question:
      "A candidate record is a refusal reason the user asked about in this session. The identical refusal is already committed as a state carrying gate A2_provenance. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "It is already a state, with its gate attached, and states are the system's record of what happened. A memory copy would be readable without the gate, so a reader could not tell which gate refused, and the refusal-rate-by-stage metric would split.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "memory.admission-023",
    kind: "memory.admission",
    question:
      "A candidate record names the two tests that failed during this run, with their exit codes. The rest of this run will consult them; the next run will have its own failures. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 2,
    rationale:
      "It is scoped to this run and outlives the step that produced it, which is EPISODIC. Promoting it to PROCEDURAL would assert a pattern from a single run, and one run's two failures is not a method.",
    namespaces: ["execution", "task"],
  },
  {
    id: "memory.admission-024",
    kind: "memory.admission",
    question:
      "A candidate record states a general rule this run confirmed: a class may refine the envelope's payload but may never extend it, so a new envelope field is a schema version bump. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 3,
    rationale:
      "It is a rule that changes how any future work is done here, which is a method rather than a fact about the world. PROCEDURAL is the tier a future task retrieves it from; a run that confirmed a rule did not discover a new one, but confirmation does not make it narrower.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "memory.admission-025",
    kind: "memory.admission",
    question:
      "A candidate record is the exact sequence that reproduces a failed step deterministically, worked out across three separate failures in three separate runs. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 3,
    rationale:
      "A reproduction sequence generalised over three failures is a method: the next failure of this kind is served by it directly. The three-run span is what rules out EPISODIC, and the fact that it is a procedure is what rules out PERSISTENT.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "memory.admission-026",
    kind: "memory.admission",
    question:
      "A candidate record states a fact the user gave about an external billing system: invoices are issued monthly on the first. It is a fact, not a method, and it is still true next year. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 4,
    rationale:
      "A durable fact about the world that is not a procedure is PERSISTENT, and its durability is what the record asserts. Anything narrower would expire it while it is still true, which is the failure mode that makes a memory store untrustworthy.",
    namespaces: ["evidence", "task"],
  },
  {
    id: "memory.admission-027",
    kind: "memory.admission",
    question:
      "A candidate record is a scratch buffer of results from a search this step ran, together with the query. The step has already used the results and will not repeat the search. Which tier?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 1,
    rationale:
      "The buffer's consumer was the step that made it and the consumer is finished, so its lifetime is the step's. EPHEMERAL is the tier for exactly this, and retaining the buffer would trade serving cost for nothing at all.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "memory.admission-028",
    kind: "memory.admission",
    question:
      "A candidate record is an outcome record for one step: the command that ran, and exit code 1. The proposal that carries it is already committed on the state. Which tier does the memory module admit it at?",
    options: ["DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT"],
    correct: 0,
    rationale:
      "What ran and what it returned belongs to the execution store, and the state's proposal is the canonical record. It makes no claim and states no method, so no memory tier describes it; EPHEMERAL would be the answer only if a step still had to read it.",
    namespaces: ["execution", "decision"],
  },
  /* ==================================================================== */
  /* escalation -- ANSWER or ESCALATE.                                     */
  /* 22 of these 30 have ESCALATE as the label, on purpose: abstention is   */
  /* the property most likely to be claimed and least likely to be tested,  */
  /* and a set that only rewards an answer measures the wrong thing.         */
  /* ==================================================================== */

  {
    id: "escalation-001",
    kind: "escalation",
    question:
      "Verification of this step's postcondition has already failed twice, both times on the same deterministic check, both times under this same class. A third attempt under the same class would run the same check against the same expectation. Should this step answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "Two identical failures mean the plan is wrong, not that the execution was unlucky, and only a model can make a verdict accepted -- so a third answer would be asserting something the deterministic check has twice contradicted. The state is telling the loop to change class, not to try again.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-002",
    kind: "escalation",
    question:
      "The question requires a judgement the state does not record, and the budget envelope has reasonerCalls 0 remaining. A class that could produce that judgement would need a model call. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The answer is not in the state and the envelope has no call left to produce it, so any answer is a guess dressed as a fact. The budget is a promise, not a trend; exceeding it to avoid escalating is the trade this system exists not to make.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-003",
    kind: "escalation",
    question:
      "The state this step would read is at epoch 39, while the lineage head is at epoch 41. Any proposal built from it carries a stale epoch and is refused by the A5_epoch gate. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The epoch gate exists to make distributed resumption safe, and a write behind the head is exactly the write it refuses. The correct move is a new state planned from the head, which is an escalation to the engine, not an answer.",
    namespaces: ["policy", "capability"],
  },
  {
    id: "escalation-004",
    kind: "escalation",
    question:
      "The only evidence supporting the claim is a ref that the evidence store has already superseded with a newer hash for the same measurement. The claim cannot be re-grounded from anything else in the state. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "A2 refuses a claim that rests on superseded evidence, so an answer built on this ref would be refused at admission and the work would be lost twice. Escalating surfaces that the claim needs a current source rather than returning a verdict nobody can admit.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "escalation-005",
    kind: "escalation",
    question:
      "The question is 'which of the two candidate states was written first', and nothing in the state records the two timestamps. The step's grants name no SEARCH tool and no clock is available, since plan() takes environment facts from the state and never from the process. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "ts is excluded from the body digest as derived metadata, and with no SEARCH grant the ref cannot be paged in to recover it. The information is absent rather than hard, and an answer would be a fabrication with a confidence attached to it.",
    namespaces: ["decision", "capability"],
  },
  {
    id: "escalation-006",
    kind: "escalation",
    question:
      "The question asks about a repository that appears nowhere in the task namespace, the evidence namespace or the execution namespace of this state. Nothing in the state is about it. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The six kernel namespaces are the authority path, and a question about something outside all of them has no evidence path in this state. Answering would require importing outside knowledge into a state that claims to be self-contained and independently verifiable.",
    namespaces: ["task", "policy"],
  },
  {
    id: "escalation-007",
    kind: "escalation",
    question:
      "The question can only be answered by reading a file, and the step's class is reasoner, whose grantPolicy is 'none' and whose canRequestEscalation is false. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The step holds no read capability and has no escalation path, so the read is structurally out of reach. Abstaining is the only honest label here, and it is the case that separates a calibrated reflex model from a fluent one: the constraint is knowable from the state alone.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "escalation-008",
    kind: "escalation",
    question:
      "Two evidence refs in the state make the same measurement with opposite results, and neither ref's pin is later than the other's. The store's merge for evidence is an OR-Set, which unions rather than resolves. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The namespace's merge algebra unions the two, so the contradiction survives the merge intact and nothing downstream resolves it. Picking the one that reads better is a reflex model silently becoming the adjudicator of a conflict the engine's algebra deliberately left open.",
    namespaces: ["evidence", "decision"],
  },
  {
    id: "escalation-009",
    kind: "escalation",
    question:
      "The proposal this step would return does not conform to its class's payload schema, and the A1_schema gate would refuse it. Nothing in the state says what the correct payload shape is for this class version. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "Re-answering with the same class would produce the same malformed proposal and the same refusal. The missing thing is the schema for that class version, which is an artefact outside the state, so the honest label is that this step cannot be completed from what it holds.",
    namespaces: ["policy", "capability"],
  },
  {
    id: "escalation-010",
    kind: "escalation",
    question:
      "The declared spend for this transition is tools 6 against a remaining envelope of tools 2, and the tool calls cannot be made smaller without failing the postcondition. The A3_budget gate would refuse the proposal. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "A refusal at A3 is a state, but the useful thing is to report that this work does not fit the envelope rather than to return a proposal certain to be refused. Escalation is how a system says the plan is wrong; answering says the answer is wrong.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-011",
    kind: "escalation",
    question:
      "The question is 'which version of the editor class is better'. The state references editor@1.0.0 by hash and holds no criteria, no comparison and no record of any other version's use. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "'Better' is not a fact the state records, and 'latest' is not a rule -- a state references its class by hash precisely so this question is not answerable from the chain. A preference stated as a fact here would be indistinguishable, later, from a real one.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "escalation-012",
    kind: "escalation",
    question:
      "The answer depends on a tool-result ref whose content hash does not resolve in any store the state names, and the proposal's only provenance pointer is to that ref. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "A2 requires a claim's sources to resolve, and this one does not, so any answer is unbacked at the gate. The failure is in the substrate rather than in the reasoning, and reporting that is the only output that tells anyone where to look.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "escalation-013",
    kind: "escalation",
    question:
      "The request is 'give the reasoner class an fs.write grant so it can finish this task'. A role may propose capability and may never grant it to itself. Answer or escalate?",
    options: ["ANSWER", "ESCALATE", "AMEND THE GRANT IN PLACE"],
    correct: 1,
    rationale:
      "Escalation is a class transition recorded as a new state, never a mutation of the current step's grant set, so the in-place option is unavailable by construction rather than by policy. What the step can do is ask, and the engine records the answer either way.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "escalation-014",
    kind: "escalation",
    question:
      "A MutationProposal is on the table whose proposer identity is the same identity that would be recorded as its evaluator. The rule is that a proposal's proposer and its evaluators must be disjoint identity refs. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "No self-approval is structural: the two identities must be disjoint, and no self-approval is possible here because the proposal is self-evaluated. Escalation is the only path that can produce a valid evaluation, and it is the path that keeps the promotion out of the proposer's hands.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-015",
    kind: "escalation",
    question:
      "The answer requires a capability that appears in no grant on this state, and the class is attached, so an escalation path does exist. The state does not record which class would hold that capability. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "Prohibition is the absence of a grant, so the step can state confidently that it cannot do this -- but the question asked is what the answer is, not whether the step is permitted. Attached means escalation is available, and this is the case where using it is correct.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "escalation-016",
    kind: "escalation",
    question:
      "Two branches of the lineage disagree about the order of two planned steps, and the merge algebra for ordered plans is a sequence CRDT plus an explicit typed conflict record. The state records both orders and no tie-break. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The namespace's own algebra declares this a conflict rather than a merge, and the conflict record is a typed output the Reducer produces. A reflex model picking an order would be resolving a conflict its tier has no authority over, and the resolution would leave no record of the disagreement.",
    namespaces: ["decision", "execution"],
  },
  {
    id: "escalation-017",
    kind: "escalation",
    question:
      "The answer is in a resource whose scheme is 'memory', and the step's grants name no memory resource, so the ref cannot be paged into this package. Nothing else in the state contains the same fact. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The ref exists and is unreachable under this step's grant set; the reflex stack may only subtract, so it cannot bring it in. That is a statement about this step's authority rather than about the question, and escalating is how it gets said.",
    namespaces: ["capability", "evidence"],
  },
  {
    id: "escalation-018",
    kind: "escalation",
    question:
      "The question asks which grant set is currently effective, and the head state's stored capabilities disagree with what its policyHash re-derives. Either the stored grant or the policy is wrong, and the state does not say which. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "The grant is stored AND provenanced precisely so a third party can re-derive it without trusting the writer; a disagreement is the signal that one of them is corrupt. Picking either would destroy the only evidence that a corruption happened.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "escalation-019",
    kind: "escalation",
    question:
      "The only thing asserting that the postcondition holds is a layer's own claim, recorded in verification[] and marked unverified. No deterministic check exists for this postcondition. Answer or escalate?",
    options: ["ANSWER", "ESCALATE", "DROP THE CLAIM AND CONTINUE"],
    correct: 1,
    rationale:
      "A model can never make a verdict accepted, and its assertion is evidence, not a verdict. Dropping the claim would make the failure invisible and answer would launder an unverified assertion into a decision, which is the specific error D-029 exists to prevent.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-020",
    kind: "escalation",
    question:
      "The state presented to this step was authored by a layer rather than minted by the engine, and it carries a proposal and a verdict the engine never produced. Answer or escalate?",
    options: ["ANSWER", "ESCALATE", "REPLAY THE STEP AND CONTINUE"],
    correct: 1,
    rationale:
      "Engine-only authorship means a layer may propose and may never author, so this state is not a continuation the system recognises. Replaying it would treat the forgery as history, and answering would be worse; the only correct action is to report it.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "escalation-021",
    kind: "escalation",
    question:
      "The head state's class ref does not resolve in the catalogue: the name and version recorded on the ref disagree with the registered class at that content hash. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "A ref that does not resolve is a forged ref and the lookup returns null, so the state cannot be planned from and its materialised grants cannot be derived. The condition is fully determinable from the state, which is why this is an abstention rather than an uncertain answer.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "escalation-022",
    kind: "escalation",
    question:
      "The step's context budget cannot be met: compaction has already been applied once, and the artifact refs alone exceed what remains. The question cannot be answered from what fits. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 1,
    rationale:
      "Compaction is non-destructive but not infinitely repeatable, and the preserve set is not optional. When the budget cannot hold what must be held, the step has no honest input, and answering anyway is how a lossy context becomes a confident wrong answer.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-023",
    kind: "escalation",
    question:
      "The question is 'what is this state's task statement', and the state carries the task in the task namespace with its exact recorded text. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "The task is a kernel namespace and the answer is the recorded text, so answering is a lookup, not a judgement. Abstaining here would train the model to hedge on things it is certain about, which costs calibration just as surely as over-answering does.",
    namespaces: ["task", "decision"],
  },
  {
    id: "escalation-024",
    kind: "escalation",
    question:
      "The question is 'which gate refused the last proposal', and the head state is a refusal carrying both its reason and the gate that produced it. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "A refusal is a first-class state carrying the offending gate, so the question is answerable from the state alone. This is the control case for the 22 above: an abstention label that appears here would be as wrong as an answer label there.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "escalation-025",
    kind: "escalation",
    question:
      "The question is 'what tools does this step hold', and the class's grantPolicy and the step's epoch are both recorded on the state, so the set is exactly re-derivable by construction. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "The grant is stored and the policy that produced it is provenanced, so a third party can re-derive the answer without trusting the engine. That re-derivability is the property the stored-grant design exists for, and using it here is the intended behaviour.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "escalation-026",
    kind: "escalation",
    question:
      "The question is 'how many parents does the head commit have', and the parents array is on the state and included in the body digest. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "It is a count of a recorded field, and the field is identity-bearing, so the answer is as verifiable as the state itself. Nothing here requires judgement, retrieval or a capability the step does not hold.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "escalation-027",
    kind: "escalation",
    question:
      "The question is 'is fs.write permitted for this step', and this step's capabilities contain a model grant, a context grant and no tool grant. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "Prohibition is the absence of a grant, so the absence in the stored set is itself the answer -- and it is a complete one, because the set is the complete set. Abstaining here would be the model declining to state a fact the envelope is designed to make stateable.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "escalation-028",
    kind: "escalation",
    question:
      "The question is 'which capability families does this step hold', and the class is reasoner with grantPolicy 'none' at a recorded epoch, so the constructed set is fully determined. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "Every class receives a model and a context grant and a 'none' policy adds nothing, so the set follows from the recorded class and epoch alone. This is a construction, not an estimate, which is what makes it answerable rather than a matter of confidence.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "escalation-029",
    kind: "escalation",
    question:
      "The question is 'is this commit a merge', and the head state's parents array has exactly one entry. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "Lineage is defined by the parent count: 0 is root, 1 is progression, 2 or more is merge. One entry is progression by definition, so the question needs no inference beyond reading a field the state exists to carry.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "escalation-030",
    kind: "escalation",
    question:
      "The question is 'which class runs the next step', the step's postconditions require an on-disk write, and exactly one catalogued class declares a write grant. Answer or escalate?",
    options: ["ANSWER", "ESCALATE"],
    correct: 0,
    rationale:
      "The selection follows from the smallest-sufficient rule and the recorded grant policies, with exactly one candidate satisfying them, so there is no residual judgement to escalate. A model that abstains on a forced choice spends its abstention budget on nothing.",
    namespaces: ["capability", "decision"],
  },
  /* ==================================================================== */
  /* topology -- SINGLE(x) | PARALLEL(x,y) | SEQUENCE(x,y) | RETURN.        */
  /* One class per step and the Reducer alone mints a merge commit, so a    */
  /* step's shape follows from what consumes what, not from what is cheap.   */
  /* ==================================================================== */

  {
    id: "topology-001",
    kind: "topology",
    question:
      "Two candidates are on the table: (A) read workspace/src/loop.ts, (B) write the fix to that file. B's content is determined by what A returns, and both are admissible. Which topology runs this step?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "B consumes A's output, so there is a data dependency and the two cannot be in flight together. The rule is what consumes what, not wall-clock: running them in parallel would mean writing a file nobody has read yet.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "topology-002",
    kind: "topology",
    question:
      "Two candidates: (A) read workspace/tsconfig.json, (B) read workspace/package.json. Neither reads what the other produces, both are pure reads, and the step compares them afterwards. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 1,
    rationale:
      "Two independent, non-mutating candidates with no ordering constraint. Sequencing them would buy nothing but latency, and there is no merge to author because the postcondition is a comparison rather than a reconciliation.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "topology-003",
    kind: "topology",
    question:
      "Two candidates: (A) run the test suite, (B) write the fix. The fix's content is the correction the suite's failure output names, so B cannot be written before A has run. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The write is derived from the run's output, so the dependency is real and the ordering is forced. Running them together would commit a fix guessed before the failure that motivates it was known.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "topology-004",
    kind: "topology",
    question:
      "Two candidates: (A) write to /etc/hosts, (B) run a shell command through a tool that appears in no grant on this state. Neither is reachable, and both were proposed by the same layer that proposed them. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 3,
    rationale:
      "There is no admissible candidate set, and the failure mode is absence rather than an error: neither capability exists under this step's plan. RETURN is the shape that yields a continuation without executing, and the refusal is a first-class state.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "topology-005",
    kind: "topology",
    question:
      "Two candidates: (A) write workspace/src/a.ts, (B) write workspace/src/b.ts. B's content is computed from the exported symbol list A produces. Both are admissible and neither path is read by the other. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "Separate paths tempt a parallel answer, but B's bytes do not exist until A has run, and a content dependency outranks a path-independence one. A parallel plan here would be committing a file whose contents are undefined at plan time.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "topology-006",
    kind: "topology",
    question:
      "Two candidates: (A) fetch a URL through a web tool that this state's grants do not name, (B) read the local fixture that already contains the same payload. Only B is admissible. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 0,
    rationale:
      "The topology is taken over the admissible set. A is not a candidate because its capability was never granted, so including it would mean executing something the plan does not authorise in order to then discover it cannot run.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "topology-007",
    kind: "topology",
    question:
      "Two candidates, both of which require one tool call, and the budget envelope has tools 0 remaining. The postconditions cannot be met by any other means. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 3,
    rationale:
      "Parallelism cannot create budget, and a single call would still exceed the envelope. The step has no admissible plan, so it returns rather than executing something the A3 gate would refuse after the side effect had already happened.",
    namespaces: ["policy", "capability"],
  },
  {
    id: "topology-008",
    kind: "topology",
    question:
      "Two candidates: (A) verify the artefact digest, (B) run the test suite. A deterministic check already recorded on the head state has satisfied both, with their results, and re-running either would produce a state byte-identical to the head. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 3,
    rationale:
      "The postconditions are already recorded as met by a deterministic check, so the step's correct output is the existing continuation. Re-running would add latency and zero information, and a commit identical to the head is a no-op with a price.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "topology-009",
    kind: "topology",
    question:
      "Two candidates: (A) verify the content hash of the pinned artefact, (B) run the test suite. Both are pure, neither consumes the other, and the step's postcondition requires both to be recorded. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 1,
    rationale:
      "Two independent non-mutating checks with a combined postcondition. No merge is needed because the commit records both results in one transition, so nothing about this shape requires the Reducer's multi-parent path.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "topology-010",
    kind: "topology",
    question:
      "Two candidates: (A) propose a transition to a class that declares fs.write, (B) perform the write under that new class. Both are described in the same plan, and the engine admits (A) before (B) may run. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The write runs under a class that does not exist until the proposal is admitted, so the ordering is not merely advisable -- (B) has no grant to run under until (A) has produced a new state. Escalation is a transition, and a transition precedes the thing it authorises.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "topology-011",
    kind: "topology",
    question:
      "Two candidates: (A) read the knowledge claim pinned at hash k1, (B) read the knowledge claim pinned at hash k1 under a different locator. Both resolve to the same content hash, and the step's package is at its cap. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 0,
    rationale:
      "The two candidates are the same content under two names, and identical content shares one blob. Running both would spend a second read and a second package slot to obtain bytes already in hand, which is the duplicate this dedupe exists to prevent.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "topology-012",
    kind: "topology",
    question:
      "Two candidates: (A) read the head state's projection, (B) read the pinned evidence ref the proposal will cite. Both are pure reads of already-materialised content, and neither depends on the other. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 1,
    rationale:
      "Independent reads with a combined postcondition. The evidence ref is already pinned, so there is no expansion to wait for and no content that B produces which A would consume.",
    namespaces: ["evidence", "decision"],
  },
  {
    id: "topology-013",
    kind: "topology",
    question:
      "Two candidates: (A) EXPAND a manifest ref and read its body, (B) cite that ref in the proposal. The proposal's provenance must resolve to content the step has actually seen, and the budget has room for the body. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The citation's content comes from the expansion, so B depends on A's result. This is also why expanded[] exists: the commit records which refs were paged in, and a citation to a body that was never paged would make the provenance unfalsifiable.",
    namespaces: ["evidence", "execution"],
  },
  {
    id: "topology-014",
    kind: "topology",
    question:
      "Two candidates: (A) read a file from the workspace, (B) run the test suite. The step's class is reasoner, whose grantPolicy is 'none', so it holds no tool grants. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 3,
    rationale:
      "Both candidates require a capability the class does not hold, so the admissible set is empty and parallelism is not the question. The step returns a refusal state naming the class that would be needed -- a class transition, not a wider grant.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "topology-015",
    kind: "topology",
    question:
      "One candidate is on the table: (A) emit the proposal naming the class that should follow. The planner recorded no second candidate, the package for (A) is fully compiled, and its postcondition is satisfiable. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 0,
    rationale:
      "The easy anchor for this kind. A single candidate with no ordering constraint and no unmet postcondition is the trivial topology, and mislabelling it as anything else is an error of the same class as inventing a second candidate.",
    namespaces: ["decision", "execution"],
  },
  {
    id: "topology-016",
    kind: "topology",
    question:
      "Two candidates: (A) write workspace/docs/RESULTS.md, (B) pin that file's content hash into the next state so it can be verified later. B's value is the digest of what A wrote. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The hash does not exist until the bytes are written, so the dependency is on a value, not on a file. This is the general case that ordering rules are easy to miss: a derived fact sequences just as a derived body does.",
    namespaces: ["execution", "capability"],
  },
  {
    id: "topology-017",
    kind: "topology",
    question:
      "Two candidates: (A) read the parent state, (B) read the grandparent state. The step must produce the semantic diff across the last two transitions, and neither read depends on the other. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 1,
    rationale:
      "The diff needs both inputs and neither is derived from the other, so the postcondition is a function of two independent reads. Sequencing would be the shape for a chain; this is a fan-in with no fan-out.",
    namespaces: ["execution", "decision"],
  },
  {
    id: "topology-018",
    kind: "topology",
    question:
      "Two candidates: (A) write workspace/src/x.ts, (B) write workspace/src/y.ts. The paths are disjoint, neither consumes the other, and both writes are required. The class is attached, so both grants materialise. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The hard version of the disjoint-paths trap. Two independent writes look parallel, but two-parent commits may only be minted by the Reducer, and the reflex tier does not author commits -- so a plan that fans out writes has no author for its own result.",
    namespaces: ["execution", "capability"],
  },
  {
    id: "topology-019",
    kind: "topology",
    question:
      "Two candidates, (A) and (B), are both admissible pure reads, but this step's compiled package is already at its context cap and the postcondition names only (A)'s content. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 0,
    rationale:
      "Only one of the two can be paged, and the postcondition decides which: (A). Choosing (B) instead would be answering a question nobody asked, and the budget is a promise that the step does not get to reinterpret because it found a second option.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "topology-020",
    kind: "topology",
    question:
      "Two candidates: (A) read a ref pinned at epoch 43, (B) read a ref pinned at epoch 44. The head state is at epoch 41, and a ref above the head cannot be ordered against this lineage. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 3,
    rationale:
      "Neither candidate is trustworthy this step, and sequencing them would not make either so. The step returns rather than reading refs it cannot place, because a fact from the future is not a weaker fact -- it is a different kind of object.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "topology-021",
    kind: "topology",
    question:
      "Two candidates: (A) run the typecheck, (B) apply the type fix. B's content is the correction named by A's exit output, and neither can start before the other has finished. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 2,
    rationale:
      "The fix is determined by the diagnostic, so the dependency is total and the order is fixed. The concrete case generalises the rule: a candidate whose content is named by another's output is never a parallel candidate, whatever the paths look like.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "topology-022",
    kind: "topology",
    question:
      "Two candidates: (A) read docs/POLICY.md, (B) read src/policy.ts. The step's output is a report of where the document and the code disagree, and neither read depends on the other. Which topology?",
    options: ["SINGLE(A)", "PARALLEL(A,B)", "SEQUENCE(A,B)", "RETURN"],
    correct: 1,
    rationale:
      "The disagreement is computed after both reads, so the postcondition is a function of two independent inputs. This is the drift check's own shape, and it is the everyday case: two independent reads, one comparison afterwards.",
    namespaces: ["policy", "evidence"],
  },
  /* ==================================================================== */
  /* acquisition -- what the context compiler does with a candidate ref.    */
  /* The stack selects the package before the model sees it and may only    */
  /* subtract; the commit records expanded[]. A conflict in a namespace     */
  /* whose algebra declares one is surfaced, never silently resolved.       */
  /* ==================================================================== */

  {
    id: "acquisition-001",
    kind: "acquisition",
    question:
      "A candidate tool-result ref is cited by the proposal the current step is about to make, and A2_provenance requires a cited source to resolve. The claim's verdict does not depend on the ref's body, and this step's context budget has ample room for a manifest entry. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "The proposal depends on the ref existing and resolves to nothing else, so it cannot be discarded; and nothing in the verdict needs the bytes, so paging them would be spending context for no reader. RETAIN_REF is the only action that satisfies both halves of the question.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "acquisition-002",
    kind: "acquisition",
    question:
      "A candidate evidence ref records a measurement that the evidence store has already superseded with a newer hash. No proposal cites it and no postcondition names it. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "This is the hard case the acquisition tier exists for. The ref is real and resolvable, which is exactly what makes retaining it tempting, but it is retired evidence with nothing depending on it, and A2 would refuse any claim that used it.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "acquisition-003",
    kind: "acquisition",
    question:
      "A candidate ref has the same scheme, locator and content hash as an entry already in this step's manifest, differing only in its pin string. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "Identical content shares one blob, so the manifest already carries these bytes and a second entry is a duplicate rather than a second fact. Retaining it would make the manifest grow with ref count instead of with content.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-004",
    kind: "acquisition",
    question:
      "A manifest ref's summary mentions a configuration detail this step's postcondition turns on, and the summary does not state what the detail is. The step holds a SEARCH grant bounded to the ref's namespace, and the ref's body fits the step's remaining context budget. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 2,
    rationale:
      "The postcondition depends on content only the body carries, the grant permits fetching it, and the budget can hold it. Those three conditions together are the definition of expanding rather than retaining: the ref is not merely worth keeping, it is worth reading now.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-005",
    kind: "acquisition",
    question:
      "A candidate knowledge claim contradicts the current head of the knowledge store for the same subject, and its pin is not demonstrably later than the head's. The knowledge store's merge is supersede. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 3,
    rationale:
      "Adopting a contradicting claim would silently replace a verified one, because the store's merge rule resolves conflicts by supersession rather than by argument. CONTRADICTION_CHECK surfaces the conflict so a human or an explicit check decides it; discarding would lose the claim, and retaining would make it invisible.",
    namespaces: ["evidence", "decision"],
  },
  {
    id: "acquisition-006",
    kind: "acquisition",
    question:
      "A candidate ref is a MutationProposal object. The state carries no evaluation record for it, and the identity that would evaluate it is the same identity that proposed it. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "A proposal's proposer and its evaluators must be disjoint identity refs, and only the mutation controller may promote. Neither this step nor the compiler can complete that pairing, so the ref is handed to the authority that can rather than being quietly retained for a later reader to mistake for a decision.",
    namespaces: ["policy", "decision"],
  },
  {
    id: "acquisition-007",
    kind: "acquisition",
    question:
      "A candidate ref's pin resolves to epoch 43 while the head state is at epoch 41, and nothing in the state records how that ref relates to this lineage. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "The ref cannot be ordered against the head, so the compiler cannot tell whether it predates or postdates what the state says. Discarding would be a silent judgement about currency, and retaining it would carry an unplaceable claim -- this is a case where the honest answer is that the ref needs an authority, not a compiler decision.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "acquisition-008",
    kind: "acquisition",
    question:
      "A candidate artefact ref is the one the next step's postcondition names, and this step's postcondition does not. The body is far larger than this step's remaining context budget. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "A later step needs it and this one cannot hold it, which is exactly what a manifest entry is for: the ref travels in the commit's tree and the body is paged only by the step that needs it. Expanding now would exceed the budget for a reader that does not exist yet.",
    namespaces: ["execution", "policy"],
  },
  {
    id: "acquisition-009",
    kind: "acquisition",
    question:
      "A candidate ref's scheme is 'memory', the step's grants name no memory resource, and no postcondition and no proposal cites it. The step holds no SEARCH grant. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "Nothing depends on it and the step cannot reach it, so there is no reader for it under this plan. The compiler's operation is subtraction, and a ref with no reader and no reachable path is the simplest thing in the set to drop.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "acquisition-010",
    kind: "acquisition",
    question:
      "Two candidate evidence refs make the same claim with different sources and different confidences, and the proposal cites both. The evidence namespace's merge is an OR-Set, which unions. What does the compiler do with them?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "A contradicting pair is the trap here: disagreement is not the same as contradiction. The evidence algebra unions, so both refs are members of the store and neither is a conflict requiring adjudication; the contradiction check belongs to namespaces whose merge declares conflicts.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "acquisition-011",
    kind: "acquisition",
    question:
      "A manifest ref is itself a pointer to a third ref, and this step's postcondition requires the third ref's content. The step's grant covers the target namespace and the target body fits the remaining budget. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 2,
    rationale:
      "Following the pointer is what the postcondition asks for, the grant permits it and the budget holds it. Retaining the pointer alone would satisfy nothing; the point of a pointer being a manifest entry is that a step may chase it, and this step is the one that must.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-012",
    kind: "acquisition",
    question:
      "A candidate ref offers a raw body that is already present, in full, inside the package this step has compiled. The manifest records it separately. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "The body is already here and the manifest already records the ref, so neither half of this candidate adds anything. The rule is by reference plus content hash: a ref earns its place by naming something the state does not already carry.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-013",
    kind: "acquisition",
    question:
      "This step's postcondition cannot be satisfied without a ref's contents, and no class in this lineage declares the capability needed to read it. The state does not record which class would. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "The ref is needed and unreachable, so neither dropping it nor keeping it helps; what the step is reporting is that its own class is wrong for this postcondition. That is a class transition, and the compiler answers it by escalating rather than by quietly returning an unsatisfiable step.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "acquisition-014",
    kind: "acquisition",
    question:
      "A candidate knowledge ref is small, already cited by the proposal, in scope for this step's knowledge grant, and its body is 400 tokens against a step with 20,000 tokens of headroom. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "The easy anchor. Nothing forces the body in and nothing makes the ref droppable, and at 400 tokens the expansion question is not close enough to matter. A classifier that reaches for EXPAND by default is pattern-matching on 'useful' rather than on whether a reader needs the bytes.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "acquisition-015",
    kind: "acquisition",
    question:
      "A candidate ref is an EPHEMERAL memory record written at epoch 40, and this step runs at epoch 41. Nothing in the step's postconditions or proposal names it. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "Grants do not outlive their state, and an ephemeral record has exactly the same binding: it is scoped to the step at the epoch that wrote it. Carrying it forward would be the memory tier's version of resurrecting a stale grant.",
    namespaces: ["capability", "decision"],
  },
  {
    id: "acquisition-016",
    kind: "acquisition",
    question:
      "A candidate ref is currently carried as a manifest entry only, and this step's postcondition turns on a figure that appears in its body and nowhere in the summary. The step holds the grant and has 9,000 tokens of headroom against a 6,000-token body. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 2,
    rationale:
      "The arithmetic is the question: the body fits, the grant covers it, and a required figure lives only in there. All three of those are conditions on expanding rather than retaining, and a model that checks only the first two will systematically under-expand.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-017",
    kind: "acquisition",
    question:
      "A candidate knowledge claim carries a higher pin than the current head for its subject, so it looks newer, and the knowledge store's merge is supersede rather than compare. No verification record exists for either version. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 3,
    rationale:
      "Because the merge is supersede, adopting on pin alone would silently replace a verified claim with an unverified one and leave no trace that a replacement happened. The check is what distinguishes a genuine supersession from a newer-looking claim, and skipping it is how a knowledge store loses a fact quietly.",
    namespaces: ["evidence", "policy"],
  },
  {
    id: "acquisition-018",
    kind: "acquisition",
    question:
      "Two candidate tool-result refs record the same command with exit code 0 and exit code 1 respectively, and neither ref's pin is later than the other's. The execution namespace records a typed conflict for exactly this case. What does the compiler do with them?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 3,
    rationale:
      "The execution namespace's algebra has no order to break the tie, so it produces a typed conflict record rather than a winner. The compiler's job is to surface that the two disagree; picking the zero is choosing a result, and a result is not what this namespace can express.",
    namespaces: ["execution", "evidence"],
  },
  {
    id: "acquisition-019",
    kind: "acquisition",
    question:
      "A candidate ref's locator resolves to a path that matches no scheme the state declares -- it is not artifact, memory, knowledge, tool-result or env. Its hash is well-formed. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "A well-formed hash on an unclassifiable locator is not evidence of anything: the compiler cannot tell which store owns it or which merge algebra applies, and every one of those decisions depends on the answer. Guessing a scheme is precisely the sort of widening the envelope that a feature request looks like.",
    namespaces: ["policy", "capability"],
  },
  {
    id: "acquisition-020",
    kind: "acquisition",
    question:
      "A candidate ref came from a portion of the previous package that compaction removed. This step's budget has no room for its body, nothing cites it, and no postcondition names it. The raw history is still retrievable behind EXPAND. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "Compaction is non-destructive, so the ref is not lost -- it is deferred, and a step that needs it can reach it through EXPAND. Carrying it here would spend a manifest slot and a budget on a reader that does not exist in this step.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-021",
    kind: "acquisition",
    question:
      "A candidate ref is a tool-result whose verification record says the result was a model assertion rather than a deterministic check. It is the only source offered for the claim the current step wants to make. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "A model's assertion is evidence and never a verdict, so this cannot ground a claim on its own -- and the compiler is not the place to decide that it can. Escalating puts the question to the authority that can, and silently retaining it would make an unverified claim look like a sourced one.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "acquisition-022",
    kind: "acquisition",
    question:
      "A manifest ref's summary names a lead that this step would like to follow, but the step's knowledge grant is scoped to a different subject and does not cover the ref's subject. The ref itself is in scope and the manifest has room. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "The ref is reachable but its contents are not, under this step's grant. That is a different situation from acquisition-013, where nothing was reachable at all: here the correct action is to keep the ref in the manifest so a step with the right scope can expand it, and not to expand it now.",
    namespaces: ["capability", "policy"],
  },
  {
    id: "acquisition-023",
    kind: "acquisition",
    question:
      "Two candidate refs both claim to be the current head of the same knowledge claim, and the store's head pointer for that subject is absent from the state. The two refs have different pins. What does the compiler do with them?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 4,
    rationale:
      "The merge rule is supersede, and supersession needs a head to supersede from; with the pointer missing, the store cannot say which claim is current. This is not a contradiction between two claims about the world but a damaged pointer in the store, and only an authority can repair it.",
    namespaces: ["policy", "evidence"],
  },
  {
    id: "acquisition-024",
    kind: "acquisition",
    question:
      "A candidate ref has scheme 'tool-result', its content hash resolves in no store the state names, and no proposal cites it and no postcondition names it. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 0,
    rationale:
      "Unresolvable and uncited together is the easy DISCARD, and the contrast with acquisition-021 is the point: the same unresolvable condition is an escalation when a claim depends on the ref and a discard when nothing does. Deciding between them is knowing what the ref is for.",
    namespaces: ["policy", "execution"],
  },
  {
    id: "acquisition-025",
    kind: "acquisition",
    question:
      "A knowledge claim in the store states that the sandbox mounts /home read-only, and a new candidate ref states it mounts read-write. Both are current claims in the knowledge module and neither has a recorded evaluation. What does the compiler do with the new ref?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 3,
    rationale:
      "Two current claims that cannot both be true is a contradiction, and the knowledge module's algebra has no way to choose between them, so the compiler surfaces it. This one matters operationally: acting on either version without a check means a sandbox whose isolation claim is wrong in one direction or the other.",
    namespaces: ["policy", "capability"],
  },
  {
    id: "acquisition-026",
    kind: "acquisition",
    question:
      "A candidate ref is the only record that a prior step's fs.write actually happened, and the current step must be able to say what changed without holding any tool. The ref's body is already paged into this step's package. What does the compiler do with it?",
    options: ["DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "ESCALATE"],
    correct: 1,
    rationale:
      "A past write leaves no trace on the filesystem once the sandbox is gone, so this ref is the only provenance the step has, and a step with no tools cannot go and check. It is retained for that reason alone -- not because it is interesting, but because it is irreplaceable.",
    namespaces: ["execution", "capability"],
  },
];

