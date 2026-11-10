/**
 * src/authority.ts — K0-10: the BINDING between a real-environment authority
 * change and the required authority decision.
 *
 * `src/invariants.ts` K0-10 states: *"No real-environment authority change
 * bypasses its required authority decision."* P1.4 provides the
 * AuthorityRequest / AuthorityDecision vocabulary and the promotion seam
 * records the outcome, but nothing asserted the BINDING. This module is that
 * binding, generalised out of `applyCriterionRedefinition`'s inline block.
 *
 * PURE. No I/O, no clock, no randomness, no filesystem, no network. The types
 * are imported from `./promotion.ts` — never redeclared — so the vocabulary
 * cannot drift between the seam and this check.
 */

import type { AuthorityState } from "./promotion.ts";

/** Where a change takes effect. A sandbox change is contained by the boundary; a real one is not. */
export type AuthorityScope = "sandbox" | "real_environment";

export interface ScopedChange {
  /** Deliberately wide: an UNKNOWN scope must be refusable. */
  readonly scope: AuthorityScope | string;
  /** What is being changed. */
  readonly subject: string;
  /** The new value or digest. */
  readonly proposed: string;
}

export type AuthorityBindingVerdict =
  | { readonly ok: true; readonly decision_id: string; readonly code: "authorised" | "not_required" }
  | { readonly ok: false; readonly code: "approval_missing" | "request_mismatch" | "unknown_scope"; readonly reason: string };

/**
 * Pure. Fail-closed. The rules, in order:
 *
 * 1. `sandbox` → `{ ok: true, code: "not_required" }`. The boundary is the
 *    control for a contained change, and saying so explicitly is the point —
 *    it is why the rule is not a blanket "every change needs approval".
 * 2. `real_environment` → an approval must exist, be APPROVED (a refusal is
 *    not an approval), and cover EXACTLY what was asked: same subject, same
 *    proposed value. The exact-coverage clause is the anti-replay clause — an
 *    approval covers what was asked and nothing adjacent to it.
 * 3. Any other scope → refuse `unknown_scope`. Unknown must never fall through
 *    to permitted: a future scope nobody classified fails closed.
 */
export function authorityBindingHolds(change: ScopedChange, approval: AuthorityState): AuthorityBindingVerdict {
  if (change.scope === "sandbox") {
    return { ok: true, code: "not_required", decision_id: "" };
  }
  if (change.scope === "real_environment") {
    if (approval.kind !== "approved") {
      // not_required / requested have no decision; rejected / deferred are a
      // refusal, and a refusal is not an approval.
      return {
        ok: false,
        code: "approval_missing",
        reason: `a real-environment change to ${JSON.stringify(change.subject)} requires an APPROVED AuthorityDecision; the authority state is ${JSON.stringify(approval.kind)}, which is not an approval`,
      };
    }
    if (approval.request.subject !== change.subject || approval.request.proposed !== change.proposed) {
      return {
        ok: false,
        code: "request_mismatch",
        reason:
          "the approval does not cover this change — the request was raised for subject/proposed values this change does not carry; approval covers exactly what was asked and nothing adjacent to it",
      };
    }
    return { ok: true, code: "authorised", decision_id: approval.decision.decision_id };
  }
  return {
    ok: false,
    code: "unknown_scope",
    reason: `scope ${JSON.stringify(change.scope)} is not a classified AuthorityScope — unknown must fail closed, never fall through to permitted`,
  };
}

/**
 * Does the binding refuse a real-environment change that carries no decision?
 * Always true if the mechanism works. Implemented by CALLING the binding —
 * never by restating it — so the predicate cannot drift from the mechanism.
 */
export function realChangeWithoutDecisionIsRefused(): boolean {
  const noDecision: AuthorityState = {
    kind: "not_required",
    outcome: "RETAIN_EXPERIMENTAL",
    reason: "no authority decision exists for this change — the control input to realChangeWithoutDecisionIsRefused",
  };
  const verdict = authorityBindingHolds(
    { scope: "real_environment", subject: "subject-under-binding", proposed: "proposed-under-binding" },
    noDecision,
  );
  return !verdict.ok;
}
