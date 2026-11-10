/**
 * reference.ts — a typed pointer into the namespaced object graph.
 *
 * THE HAZARD THIS FILE EXISTS TO AVOID, STATED FIRST. `src/state.ts` already has
 * `ResourceRef`. Adding a second reference type to the kernel is the exact shape of
 * mistake D-007 recorded — one native vocabulary, extensibility on top — and
 * "two allowlists drift" is the project's own phrase for it. So the relationship
 * is fixed here, and it is not a choice downstream code gets to make:
 *
 *   `ResourceRef`  **content identity** — {scheme, locator, hash, pin}. Which
 *                  bytes, verified.
 *   `Reference`     **position** — {kind, id, pointer?, revision?, projection?}.
 *                  Which region of which namespace, at which revision, in which
 *                  view.
 *
 * A `Reference` is **not** an alternative to a `ResourceRef` and cannot be used
 * where one is required. Resolution is the only bridge, and it has one direction:
 * **a resolved `Reference` yields a `ResourceRef`**, because resolution ends at a
 * content hash. A `ResourceRef` cannot yield a `Reference`, because content does
 * not know which namespace it was reached through.
 *
 * WHAT THIS IS NOT. The text form `@kind:id[#pointer][@revision][?projection]` is
 * a **serialization**, not the primitive. It exists for prompts, logs, APIs and
 * user surfaces. Once parsed, everything downstream carries the object, so the
 * syntax can change without rewriting the resolver — the same reason D-007 keeps
 * specialisation in `StateClass` rather than in the envelope.
 *
 * PROMOTED, NOT BUILT. The vocabulary and the type are promoted by D-053. The
 * parser, the formatter and the resolver are EXP#4's method and stay in
 * `tools/refs/`, where the 98.6 % reduction was measured and where a resolver can
 * be tested against a moving corpus without the kernel depending on an experiment.
 */

import type { ResourceRef } from "./state.ts";
import type { ContentHash } from "./hash.ts";

/**
 * The kind table is derived from **D-024**, not from the handoff that proposed it.
 *
 * D-024 fixes six kernel namespaces (`task`, `evidence`, `execution`,
 * `capability`, `policy`, `decision`) and six module namespaces (`artifact`,
 * `memory`, `knowledge`, `meta`, `world`, `hypothesis`). The last four are
 * **layer-model L3 compositions, not namespaces** — `@lease` is now decided
 * (D-051: a projection of the states that issued it), `@agent` is D-008's class,
 * and `@run` is a composition. They are kinds here because they are what a caller
 * actually names, and they are marked so that a later reader does not promote them
 * to namespaces by accident.
 */
export const REF_KINDS = [
  // D-024 kernel namespaces
  "task",
  "evidence",
  "execution",
  "capability",
  "policy",
  "decision",
  // D-024 module namespaces
  "artifact",
  "memory",
  "knowledge",
  "meta",
  "world",
  "hypothesis",
  // layer-model L3 compositions — what a caller names, NOT namespaces
  "lease",
  "agent",
  "run",
  // the state itself, the L1 primitive
  "state",
] as const;

export type RefKind = (typeof REF_KINDS)[number];

export interface Reference {
  kind: RefKind;
  id: string;
  /** RFC 6901 JSON Pointer, e.g. `/goal` or `/tools/3/name`. */
  pointer?: string;
  /** Exact revision. Absent means head. */
  revision?: number;
  /** Enumerated view name. Absent means the kind's default. */
  projection?: string;
}

/**
 * A parse failure is a **value, not a throw**, and it is closed.
 *
 * Three reasons, and the third is the one that matters: an unparseable reference
 * must not be silently treated as an absent one, because `undefined` is what a
 * missing projection legitimately looks like. Collapsing the two would make a
 * malformed reference indistinguishable from "no view requested", which is the
 * same empty-success shape D-021's successor rules forbid.
 */
export type RefParseError = {
  kind: "syntax" | "unknown-kind" | "empty-id";
  detail: string;
  input: string;
};

/**
 * The one bridge between position and content, declared so it cannot be widened.
 *
 * Returning a `ResourceRef` rather than the selected content is deliberate: a
 * resolver that returned bytes would put selection inside the pointer type, and
 * selection is a **grant** decision. Returning the reference to the content keeps
 * the grant check where it is — at the boundary, over a resolved `ResourceRef` —
 * rather than inside a string parser.
 */
export type ResolvedReference = {
  ref: Reference;
  /** Absent when the reference names something not in this chain. */
  target?: ResourceRef;
  /** Content hash of what was selected, when it was selected. */
  hash?: ContentHash;
};