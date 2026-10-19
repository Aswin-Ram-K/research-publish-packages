// D14 — extracted verbatim from
//   target: the read-only target repository (HEAD 907fa39)
//   lines 53-75 (the S12 union and the S02 interface).
// Nothing else in that file is referenced by these declarations: every field type is a
// TypeScript primitive or string[], so this snippet is the complete fixture schema.
// The body corpus (S07, 190 records) is copied in full with the shipped fixture data.

export type S12 =
  | "K02"
  | "N10"
  | "K05"
  | "K07"
  | "K01"
  | "K04"
  | "K03";

export interface S02 {
  id: string;
  kind: S12;
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
