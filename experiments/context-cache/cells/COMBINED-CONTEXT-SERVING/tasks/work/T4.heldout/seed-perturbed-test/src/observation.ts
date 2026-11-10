/**
 * observation.ts — the append-only observation stream: what happened, per event.
 *
 * THIS IS THE SOURCE, NOT A COMMIT AND NOT A STATE. D-023 says commit per
 * transition and never per event, and `tests/commit-boundary.ts` measures it.
 * The observation stream is the non-propagating evidence store beside the commit
 * DAG: it records more than it propagates, which is what makes it useful and what
 * would make it expensive if it were the unit of propagation. `docs/STATE.md`
 * already permits exactly this separation — *"Trace events go to a separate store
 * and never into the state"* — and D-053 records the promotion.
 *
 * WHY THE DECOMPOSITION IS TYPED. A projector that folds arbitrary JSON into an
 * envelope can always "reconstruct" something. For the reconstruction to be
 * checkable, each kind must be responsible for exactly one region of the envelope
 * and the mapping must be **enumerable**. That is the property EXP#2 measured
 * (16/16), and it is the reason this is a discriminated union rather than an
 * interface with a generic payload.
 *
 * WHAT IS PROMOTED AND WHAT IS NOT. The **types** are promoted. The chain
 * verification, the projector and the round-trip test are not: they are EXP#2's
 * method and they stay in `tools/derivation/`, where they can be measured against
 * a moving envelope without the kernel depending on an experiment.
 */

import type {
  Budget,
  CapabilityGrant,
  EvidenceRef,
  Proposal,
  ProjectionRef,
  ResourceRef,
  StateClassRef,
  Verdict,
} from "./state.ts";
import type { ContentHash } from "./hash.ts";

/**
 * The ten kinds, and what they do and do not cover. **This comment is a corrected
 * claim; the earlier version said the kinds covered the envelope exactly, and under
 * envelope 2.0 that is false.**
 *
 * `src/state.ts`'s `State` has **16** fields (envelope 2.0, D-052/P1). The ten kinds
 * produce the **12** regions enumerated by `DERIVED_FIELDS` in
 * `tools/derivation/projector.ts` — `transition.open` carries `epoch`, `parents` and
 * `schema`; `capability.granted`, `resource.attached` and `evidence.recorded` each
 * repeat, which is why twelve fields need ten kinds.
 *
 * **Four fields are outside the derivation surface, for two different reasons, and
 * each is named rather than implied** (`tools/derivation/projector.ts`):
 *
 *   - `COMPUTED_FIELDS` — `id` (the content address of the draft) and `ts` (supplied
 *     by the caller: time is log-side and derived, D-058). Written by the projection
 *     itself; no observation could carry them without becoming a second source of
 *     truth for what they are.
 *   - `NOT_OBSERVED_FIELDS` — `transition` (the `TransitionRef` declaration the
 *     engine used, D-042) and `expanded` (P4's paging record, recorded and not
 *     interpreted). No `ObservationKind` carries either and **no producer emits
 *     either**, so a kind would have to fabricate the observation it claims to
 *     replay.
 *
 * These are NOT `VOLATILE`. That set (`src/state.ts`) means "in the envelope,
 * excluded from the body digest", and these two are **inside** the digest: changing
 * `transition` or `expanded` changes the state's address, which is what D-042
 * requires. The two axes are independent — `epoch` is derived here *and* volatile
 * there.
 *
 * **And the coverage is CHECKED, not asserted**: `tests/derivation-coverage.ts`
 * fails when `State` grows a field that is in neither `DERIVED_FIELDS` nor
 * `OUTSIDE_DERIVATION`. Its absence is why this gap survived a schema bump with
 * every suite green; the prose being right is not what keeps it right.
 */
export type ObservationKind =
  | "transition.open" // epoch, parents, schema
  | "class.assigned" // the role
  | "policy.resolved" // policyHash
  | "budget.set" // budget
  | "capability.granted" // one grant; repeats
  | "projection.compiled" // projection
  | "resource.attached" // one resource; repeats
  | "evidence.recorded" // one evidence; repeats
  | "proposal.made" // what the layer asked for
  | "verdict.rendered"; // what the engine ratified

/** Payload for each kind. A union, so a projector cannot silently mis-read one. */
export interface ObservationData {
  "transition.open": { epoch: number; parents: ContentHash[]; schema: string };
  "class.assigned": StateClassRef;
  "policy.resolved": { policyHash: ContentHash };
  "budget.set": Budget;
  "capability.granted": CapabilityGrant;
  "projection.compiled": ProjectionRef;
  "resource.attached": ResourceRef;
  "evidence.recorded": EvidenceRef;
  "proposal.made": Proposal;
  "verdict.rendered": Verdict;
}

/**
 * An observation is a **discriminated union over `kind`**, not an interface with a
 * generic parameter.
 *
 * That is deliberate, and EXP#2 §7.3 records the defect it was written to prevent:
 * with `kind` and `data` as independent properties, switching on `o.kind` does
 * not narrow `o.data`, and a projector can read one kind's payload as another's
 * with the compiler objecting to nothing. Distributing the union over the kind
 * makes the pairing a type error instead of a runtime surprise.
 */
export type ObservationOf<K extends ObservationKind> = {
  /** Strict successor: seq n+1 requires seq n. */
  seq: number;
  kind: K;
  data: ObservationData[K];
  /** The previous observation's hash, or null for the first. */
  prev: ContentHash | null;
  /** Hash over {seq, kind, data, prev} — the chain link. */
  hash: ContentHash;
};

export type Observation = { [K in ObservationKind]: ObservationOf<K> }[ObservationKind];

/* ------------------------------------------------------------------ */
/* Stream integrity — the shape a verifier reports                        */
/* ------------------------------------------------------------------ */

/**
 * The three ways a chain can be broken, plus the empty case.
 *
 * These four are the entire failure vocabulary of `tools/derivation/stream.ts`, and
 * they are a type in `src/` rather than a string in a tool because **"did the
 * effect happen?" must have a closed vocabulary**. An open one is how a truncated
 * log and a corrupted log and a log that was never written become the same
 * "unknown", and `unknown` is what a caller cannot distinguish from "no".
 */
export type ChainProblem =
  | { kind: "seq"; at: number; detail: string }
  | { kind: "link"; at: number; detail: string }
  | { kind: "hash"; at: number; detail: string }
  | { kind: "empty" };

export interface ChainCheck {
  ok: boolean;
  problem?: ChainProblem;
}