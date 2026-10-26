#!/usr/bin/env node
/**
 * export-fixture.ts — EXP#12. Freeze the sealed instrument to JSON, once, with its digest.
 *
 * Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §4 (frozen).
 *
 * The instrument is `evals/fixtures/reflex-decisions.ts`, 190 cases, sha256
 * 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796. It is the SAME instrument the
 * 4B deciders scored on (docs/research/L1_HEAD_TO_HEAD.md), so the comparison in this experiment is
 * paired by construction. Nothing here interprets or filters a case: the projection is faithful and
 * the count is asserted.
 *
 * WHY AN EXPORT AT ALL. The training and evaluation code is Python (torch), and the fixture is
 * TypeScript. A regex parse of a TS source file is a second, informal parser that can silently
 * mis-split an option containing a comma — observed while building this experiment. This exporter is
 * the single faithful reader; the Python side never parses TypeScript.
 *
 * RUN
 *   ./scripts/run.sh tools/typed-channel/export-fixture.ts
 */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { DECISION_CASES } from "../../evals/fixtures/reflex-decisions.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(HERE, "..", "..", "evals", "fixtures", "reflex-decisions.ts");
const OUT = join(HERE, "data", "fixture-190.json");

export const INSTRUMENT_190_SHA256 =
  "076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796";

function sha256File(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

/** The digest is asserted BEFORE the read and AFTER the write, so a moved instrument is caught. */
function main(): void {
  const beforeHash = sha256File(SOURCE);
  console.log(`instrument ${resolve(SOURCE)}`);
  console.log(`  sha256 before ${beforeHash}`);
  console.log(`  expected      ${INSTRUMENT_190_SHA256}`);
  if (beforeHash !== INSTRUMENT_190_SHA256) {
    throw new Error(
      "SEALED INSTRUMENT CHANGED BEFORE EXPORT — refusing to export. " +
        `actual=${beforeHash} expected=${INSTRUMENT_190_SHA256}`,
    );
  }

  const cases = DECISION_CASES.map((c) => ({
    id: c.id,
    kind: c.kind,
    question: c.question,
    options: [...c.options],
    correct: c.correct,
    rationale: c.rationale,
    namespaces: [...c.namespaces],
  }));

  if (cases.length !== 190) throw new Error(`expected 190 cases, got ${cases.length}`);
  const ids = new Set<string>();
  const kinds = new Map<string, number>();
  for (const c of cases) {
    if (ids.has(c.id)) throw new Error(`duplicate id: ${c.id}`);
    ids.add(c.id);
    if (c.options.length < 2 || c.options.length > 8) {
      throw new Error(`${c.id}: ${c.options.length} options (must be 2-8)`);
    }
    if (c.correct < 0 || c.correct >= c.options.length) {
      throw new Error(`${c.id}: correct index ${c.correct} out of range`);
    }
    if (new Set(c.options).size !== c.options.length) {
      throw new Error(`${c.id}: duplicate option labels`);
    }
    kinds.set(c.kind, (kinds.get(c.kind) ?? 0) + 1);
  }

  writeFileSync(OUT, JSON.stringify(cases, null, 2) + "\n", "utf8");

  const afterHash = sha256File(SOURCE);
  console.log(`  sha256 after  ${afterHash}`);
  if (afterHash !== INSTRUMENT_190_SHA256) {
    throw new Error(
      "SEALED INSTRUMENT CHANGED DURING EXPORT — the run is void. " +
        `actual=${afterHash} expected=${INSTRUMENT_190_SHA256}`,
    );
  }
  console.log(`  MATCH before and after — the instrument is byte-identical`);

  console.log(`\nwrote ${resolve(OUT)}`);
  console.log(`cases: ${cases.length}`);
  for (const [k, n] of [...kinds].sort((a, b) => b[1] - a[1])) console.log(`  ${k}: ${n}`);
  const abstain = cases.filter((c) => c.options[c.correct] === "ESCALATE" || c.options[c.correct] === "DROP");
  console.log(`abstention-shaped correct labels: ${abstain.length}`);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
