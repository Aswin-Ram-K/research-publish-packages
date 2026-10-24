// DECISION_CASE_SCHEMA.ts — extracted verbatim from
//   target: /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts (HEAD 907fa39)
//   lines 53-75 (the DecisionKind union and the DecisionCase interface).
// Nothing else in that file is referenced by these declarations: every field type is a
// TypeScript primitive or string[], so this snippet is the complete fixture schema.
// The body corpus (DECISION_CASES, 190 records) is copied in full at fixture/reflex-decisions.ts.

export type DecisionKind =
  | "worker.class"
  | "context.package"
  | "capability.family"
  | "memory.admission"
  | "escalation"
  | "topology"
  | "acquisition";

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
  /** Withheld in this sanitised release. */
  namespaces: string[];
}
