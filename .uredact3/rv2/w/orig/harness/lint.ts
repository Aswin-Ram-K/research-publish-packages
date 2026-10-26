#!/usr/bin/env node
/**
 * lint.ts — EXP#12 contamination lint (F4), both directions, with its fired/silent control.
 *
 * Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §4, §6 (F4), §7.4.
 *
 *   F4: "the lint finds ANY >=2-shared-8-gram overlap between training rows and the fixture ->
 *        RUN VOID — the instrument was contaminated."
 *   §7.4: "The lint runs in both directions (training->fixture and fixture->training), and is shown
 *          to fire on a seeded copied row before it is trusted to be silent."
 *
 * PROVENANCE. The tokeniser, the per-field 8-gram index, the absolute >=2-shared-gram rule, the
 * bidirectional `lintSides` and the `demonstrateLint` two-sided control are ported VERBATIM from
 * EXP#11's `tools/frame-exp/lint.ts` (branch `EXP#11-per-model-option-revision`), so the rule is the
 * same rule that removed 0 rows in EXP#11 rather than a re-implementation that could differ. Two
 * things changed and only two:
 *
 *   1. The CLI's sides. EXP#11 linted revision vs H-A / H-B / the 190. EXP#12 lints the ACTUAL
 *      TRAINING SPLIT (600 revision + 200 H-A = the 800 rows the heads are fitted on) against the
 *      sealed 190, in both directions, and additionally reports train vs dev.
 *   2. `demonstrateLint` is adapted to the two sides' different field vocabularies. The corpus row
 *      has fields {state, instructions, criteria:*, option:*}; the fixture row has
 *      {question, option:*}. EXP#11's demo replaced a field NAMED "state" on the held-out row, which
 *      does not exist on a fixture row and would have made the control a silent no-op — a detector
 *      that cannot fire. The adaptation copies the corpus text INTO the fixture row's `question`
 *      field, and seeds a whole-row copy with the corpus row's own field names. The rule, the
 *      threshold and the direction are unchanged; only the field the text is written into is.
 *
 * RUN
 *   ./scripts/run.sh tools/typed-channel/lint.ts           # lint the split, write the report
 *   ./scripts/run.sh tools/typed-channel/lint.ts --demo    # + the fired/silent control
 */
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

/* ------------------------------------------------------------------ constants */

export const NGRAM_SIZE = 8;
export const SHARED_NGRAM_THRESHOLD = 2;

/** The 190-case instrument is FROZEN. The lint verifies it rather than assuming it. */
export const INSTRUMENT_190_SHA256 =
  "076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796";

/** The EXP#11 corpus this experiment trains on, from the pre-registration §4 (frozen). */
export const CORPUS_SHA256 =
  "c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66";

export const HERE = dirname(fileURLToPath(import.meta.url));
export const DATA_DIR = join(HERE, "data");
export const CORPUS_PATH = join(DATA_DIR, "corpus.json");
export const FIXTURE_JSON_PATH = join(DATA_DIR, "fixture-190.json");
export const REPORT_PATH = join(DATA_DIR, "lint-report.json");
export const FIXTURE_TS_PATH = join(HERE, "..", "..", "evals", "fixtures", "reflex-decisions.ts");

/* ------------------------------------------------------------------ tokenising */

/** Lowercase, map every non-alphanumeric to a space, drop empties, split. */
export function tokenize(text: string): string[] {
  const out: string[] = [];
  for (const piece of text.toLowerCase().replace(/[^a-z0-9]+/g, " ").split(" ")) {
    if (piece.length > 0) out.push(piece);
  }
  return out;
}

/** Every distinct 8-gram of one field's token stream. */
export function fieldGrams(text: string, size: number = NGRAM_SIZE): Set<string> {
  const toks = tokenize(text);
  const grams = new Set<string>();
  for (let i = 0; i + size <= toks.length; i++) {
    grams.add(toks.slice(i, i + size).join(" "));
  }
  return grams;
}

/* ------------------------------------------------------------------ rows and sides */

export interface LintField {
  field: string;
  text: string;
}

export interface LintRow {
  id: string;
  fields: readonly LintField[];
}

export interface LintSideSpec {
  name: string;
  rows: readonly LintRow[];
}

export interface IndexedRow {
  id: string;
  grams: Set<string>;
  provenance: Map<string, string[]>;
}

/** Index one row: per-field 8-grams, with provenance retained. */
export function indexRow(row: LintRow, size: number = NGRAM_SIZE): IndexedRow {
  const grams = new Set<string>();
  const provenance = new Map<string, string[]>();
  for (const f of row.fields) {
    for (const gram of fieldGrams(f.text, size)) {
      grams.add(gram);
      const seen = provenance.get(gram);
      if (seen === undefined) provenance.set(gram, [f.field]);
      else if (!seen.includes(f.field)) seen.push(f.field);
    }
  }
  return { id: row.id, grams, provenance };
}

export interface LintableCase {
  caseId: string;
  state: string;
  instructions: string;
  criteria: Readonly<Record<string, string | null>>;
  options: readonly string[];
}

export function caseToLintRow(c: LintableCase): LintRow {
  const fields: LintField[] = [
    { field: "state", text: c.state },
    { field: "instructions", text: c.instructions },
  ];
  for (const label of Object.keys(c.criteria).sort()) {
    const desc = c.criteria[label];
    if (desc !== null && desc !== undefined) fields.push({ field: `criteria:${label}`, text: desc });
  }
  c.options.forEach((opt, i) => fields.push({ field: `option:${i}`, text: opt }));
  return { id: c.caseId, fields };
}

export function casesToSide(name: string, cases: readonly LintableCase[]): LintSideSpec {
  return { name, rows: cases.map(caseToLintRow) };
}

/* ------------------------------------------------------------------ the detection */

export interface GramSample {
  gram: string;
  sourceFields: string[];
  targetFields: string[];
}

export interface ContaminationFlag {
  targetId: string;
  sourceId: string;
  sharedGramCount: number;
  sample: GramSample[];
}

export interface DirectionReport {
  direction: string;
  source: string;
  target: string;
  sourceRows: number;
  targetRows: number;
  pairsCompared: number;
  flagged: ContaminationFlag[];
  removedTargetIds: string[];
  removedCount: number;
}

/**
 * One direction of the absolute rule: walk `target` and drop every row that shares
 * >= `threshold` distinct 8-grams with any single row of `source`.
 */
export function lintDirection(
  source: LintSideSpec,
  target: LintSideSpec,
  threshold: number = SHARED_NGRAM_THRESHOLD,
  sampleLimit = 8,
  size: number = NGRAM_SIZE,
): DirectionReport {
  const src = source.rows.map((r) => indexRow(r, size));
  const tgt = target.rows.map((r) => indexRow(r, size));

  const inverted = new Map<string, number[]>();
  src.forEach((row, i) => {
    for (const gram of row.grams) {
      const list = inverted.get(gram);
      if (list === undefined) inverted.set(gram, [i]);
      else list.push(i);
    }
  });

  const flagged: ContaminationFlag[] = [];
  const removed = new Set<string>();

  for (const t of tgt) {
    const counts = new Map<number, number>();
    for (const gram of t.grams) {
      const list = inverted.get(gram);
      if (list === undefined) continue;
      for (const si of list) counts.set(si, (counts.get(si) ?? 0) + 1);
    }
    for (const [si, count] of counts) {
      if (count < threshold) continue;
      const s = src[si];
      if (s === undefined) continue;
      const shared: string[] = [];
      for (const gram of t.grams) if (s.grams.has(gram)) shared.push(gram);
      shared.sort();
      flagged.push({
        targetId: t.id,
        sourceId: s.id,
        sharedGramCount: count,
        sample: shared.slice(0, sampleLimit).map((gram) => ({
          gram,
          sourceFields: s.provenance.get(gram) ?? [],
          targetFields: t.provenance.get(gram) ?? [],
        })),
      });
      removed.add(t.id);
    }
  }

  flagged.sort((a, b) => a.targetId.localeCompare(b.targetId) || a.sourceId.localeCompare(b.sourceId));
  const removedTargetIds = [...removed].sort();

  return {
    direction: `${source.name} -> ${target.name}`,
    source: source.name,
    target: target.name,
    sourceRows: src.length,
    targetRows: tgt.length,
    pairsCompared: src.length * tgt.length,
    flagged,
    removedTargetIds,
    removedCount: removedTargetIds.length,
  };
}

export interface RemovedRow {
  side: "left" | "right";
  id: string;
  matchedSourceIds: string[];
  maxSharedGramCount: number;
  sample: GramSample[];
}

export interface LintReport {
  rule: string;
  ngramSize: number;
  threshold: number;
  left: string;
  right: string;
  leftRows: number;
  rightRows: number;
  leftGramPopulation: number;
  rightGramPopulation: number;
  forward: DirectionReport;
  reverse: DirectionReport;
  removed: RemovedRow[];
  removedCount: number;
  removedLeftCount: number;
  removedRightCount: number;
  flaggedPairs: number;
  silent: boolean;
}

function collapsed(flags: readonly ContaminationFlag[], side: "left" | "right"): RemovedRow[] {
  const byTarget = new Map<string, RemovedRow>();
  for (const f of flags) {
    const existing = byTarget.get(f.targetId);
    if (existing === undefined) {
      byTarget.set(f.targetId, {
        side,
        id: f.targetId,
        matchedSourceIds: [f.sourceId],
        maxSharedGramCount: f.sharedGramCount,
        sample: f.sample,
      });
      continue;
    }
    existing.matchedSourceIds.push(f.sourceId);
    if (f.sharedGramCount > existing.maxSharedGramCount) {
      existing.maxSharedGramCount = f.sharedGramCount;
      existing.sample = f.sample;
    }
  }
  for (const row of byTarget.values()) row.matchedSourceIds.sort();
  return [...byTarget.values()].sort((a, b) => a.id.localeCompare(b.id));
}

function sideGramPopulation(side: LintSideSpec, size: number = NGRAM_SIZE): number {
  let n = 0;
  for (const row of side.rows) n += indexRow(row, size).grams.size;
  return n;
}

/** The absolute rule, both directions, with one audit record per dropped row. */
export function lintSides(
  left: LintSideSpec,
  right: LintSideSpec,
  threshold: number = SHARED_NGRAM_THRESHOLD,
  size: number = NGRAM_SIZE,
): LintReport {
  const forward = lintDirection(left, right, threshold, 8, size);
  const reverse = lintDirection(right, left, threshold, 8, size);
  const removedRight = collapsed(forward.flagged, "right");
  const removedLeft = collapsed(reverse.flagged, "left");
  const removed = [...removedLeft, ...removedRight].sort(
    (a, b) => a.side.localeCompare(b.side) || a.id.localeCompare(b.id),
  );

  return {
    rule: `drop when a row shares >= ${threshold} distinct ${size}-grams with any single row of the other side, applied in both directions`,
    ngramSize: size,
    threshold,
    left: left.name,
    right: right.name,
    leftRows: left.rows.length,
    rightRows: right.rows.length,
    leftGramPopulation: sideGramPopulation(left, size),
    rightGramPopulation: sideGramPopulation(right, size),
    forward,
    reverse,
    removed,
    removedCount: removed.length,
    removedLeftCount: removedLeft.length,
    removedRightCount: removedRight.length,
    flaggedPairs: forward.flagged.length + reverse.flagged.length,
    silent: removed.length === 0,
  };
}

/* ------------------------------------------------------------------ the instrument side */

/** The fixture row, in the lint's shape. `question` carries the whole case text. */
export function fixtureSide(name: string, cases: readonly FixtureCase[]): LintSideSpec {
  return {
    name,
    rows: cases.map((c) => ({
      id: c.id,
      fields: [
        { field: "question", text: c.question },
        ...c.options.map((o, i) => ({ field: `option:${i}`, text: o })),
      ],
    })),
  };
}

/* ------------------------------------------------------------------ the two-sided control */

export interface DemoProbe {
  name: string;
  copied: string;
  expectFire: boolean;
  sharedWithSourceId: string;
  /**
   * Sum of the shared-gram counts over EVERY flagged source row. The corpus family boilerplate is
   * byte-identical across a family's sibling cases, so several source rows flag at once and this
   * number is a multiple of the pairwise overlap. Reported deliberately, next to the pairwise figure,
   * because an aggregate displayed beside a single source id invites over-reading (an independent
   * verifier read 220 as the overlap with the one named row; the pairwise figure is 44).
   */
  aggregateSharedGramCount: number;
  /** Alias of `aggregateSharedGramCount`, kept so downstream readers see the same field name. */
  sharedGramCount: number;
  /** The largest overlap with any ONE source row — the per-pair quantity. */
  maxPairSharedGramCount: number;
  flaggedSourceIds: string[];
  fieldsThatCarriedTheSharedGrams: string[];
  sampleGrams: string[];
  fired: boolean;
  ok: boolean;
}

export interface DemoResult {
  note: string;
  novelSharedGramCount: number;
  probes: DemoProbe[];
  ok: boolean;
}

function field(row: LintRow, name: string): string {
  return row.fields.find((f) => f.field === name)?.text ?? "";
}

/**
 * Show the detector both of its answers, in the direction F4 cares about (train -> fixture).
 *
 * EXP#11's `demonstrateLint` replaced a held-out field NAMED "state" with a revision row's state.
 * A fixture row has no field named "state" — only `question` and `option:*` — so that control would
 * have been a silent no-op on this instrument. The adaptation writes the copied corpus text into the
 * field that actually exists (`question`), and seeds a whole-row copy using the corpus row's own
 * field names. Three copies must fire; the unmodified fixture row must not.
 */
export function demonstrateLint(
  train: LintSideSpec,
  fixture: LintSideSpec,
  threshold: number = SHARED_NGRAM_THRESHOLD,
): DemoResult {
  const sourceId = train.rows[0]?.id ?? "";
  const source = train.rows.find((r) => r.id === sourceId);
  const novelRow = fixture.rows[0];
  if (source === undefined || novelRow === undefined) {
    throw new Error("demonstrateLint needs a non-empty train side and a non-empty fixture side");
  }

  const sourceBoilerplate = source.fields
    .filter((f) => f.field === "instructions" || f.field.startsWith("criteria:"))
    .map((f) => f.text)
    .join(" ");

  const withQuestion = (row: LintRow, text: string): LintRow => ({
    id: row.id,
    fields: row.fields.map((f) => (f.field === "question" ? { field: f.field, text } : f)),
  });

  const cases: { name: string; copied: string; expectFire: boolean; rows: LintRow[] }[] = [
    {
      name: "seeded.state-only-copy",
      copied: "a train row's `state` text written into a fixture row's `question`; options left novel",
      expectFire: true,
      rows: [withQuestion(novelRow, field(source, "state"))],
    },
    {
      name: "seeded.boilerplate-only-copy",
      copied:
        "a train row's `instructions` + every `criteria:` value written into a fixture row's `question`",
      expectFire: true,
      rows: [withQuestion(novelRow, sourceBoilerplate)],
    },
    {
      name: "seeded.whole-row-copy",
      copied: "every field of a train row copied verbatim (state, instructions, criteria:*, option:*)",
      expectFire: true,
      rows: [{ id: novelRow.id, fields: source.fields.map((f) => ({ field: f.field, text: f.text })) }],
    },
    {
      name: "control.novel-row",
      copied: "nothing copied — the unmodified fixture row",
      expectFire: false,
      rows: [novelRow],
    },
  ];

  const probes: DemoProbe[] = [];
  for (const c of cases) {
    const side: LintSideSpec = { name: c.name, rows: c.rows };
    const report = lintDirection(train, side, threshold);
    const flags = report.flagged;
    const total = flags.reduce((acc, f) => acc + f.sharedGramCount, 0);
    const carrying = new Set<string>();
    const grams: string[] = [];
    for (const f of flags) {
      for (const g of f.sample) {
        grams.push(g.gram);
        for (const fld of g.targetFields) carrying.add(fld);
        for (const fld of g.sourceFields) carrying.add(fld);
      }
    }
    probes.push({
      name: c.name,
      copied: c.copied,
      expectFire: c.expectFire,
      sharedWithSourceId: flags[0]?.sourceId ?? "",
      aggregateSharedGramCount: total,
      sharedGramCount: total,
      maxPairSharedGramCount: flags.reduce((acc, f) => Math.max(acc, f.sharedGramCount), 0),
      flaggedSourceIds: [...new Set(flags.map((f) => f.sourceId))].sort(),
      fieldsThatCarriedTheSharedGrams: [...carrying].sort(),
      sampleGrams: grams.slice(0, 4),
      fired: flags.length > 0,
      ok: flags.length > 0 === c.expectFire,
    });
  }

  const novel = probes.find((p) => p.name === "control.novel-row");
  return {
    note:
      "adapted from EXP#11 demonstrateLint: the copied text is written into the fixture row's `question` field, because a fixture row has no `state` field",
    novelSharedGramCount: novel?.sharedGramCount ?? 0,
    probes,
    ok: probes.every((p) => p.ok),
  };
}

/* ------------------------------------------------------------------ inputs */

export interface CorpusCase extends LintableCase {
  stratum: string;
  familyId: string;
  clanId: string;
  kind: string;
  gold: string;
}

interface CorpusShape {
  seed: number;
  cases: CorpusCase[];
}

export interface FixtureCase {
  id: string;
  kind: string;
  question: string;
  options: string[];
  correct: number;
  rationale: string;
  namespaces: string[];
}

export function sha256File(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function readCorpus(path: string = CORPUS_PATH): CorpusShape {
  return JSON.parse(readFileSync(path, "utf8")) as CorpusShape;
}

export function readFixture(path: string = FIXTURE_JSON_PATH): FixtureCase[] {
  return JSON.parse(readFileSync(path, "utf8")) as FixtureCase[];
}

/** The training split the heads are actually fitted on: the pre-registration's 600 revision + 200 H-A. */
export function trainingSplit(corpus: CorpusShape): CorpusCase[] {
  return corpus.cases.filter((c) => c.stratum === "revision" || c.stratum === "H-A");
}

export function devSplit(corpus: CorpusShape): CorpusCase[] {
  return corpus.cases.filter((c) => c.stratum === "H-B");
}

/* ------------------------------------------------------------------ CLI */

function main(): void {
  const argv = process.argv.slice(2);
  const demo = argv.includes("--demo");
  const threshold = SHARED_NGRAM_THRESHOLD;
  let failed = false;

  const fixtureTsHash = sha256File(FIXTURE_TS_PATH);
  console.log(`sealed instrument ${resolve(FIXTURE_TS_PATH)}`);
  console.log(`  sha256 ${fixtureTsHash}`);
  console.log(
    `  expected ${INSTRUMENT_190_SHA256} — ${fixtureTsHash === INSTRUMENT_190_SHA256 ? "MATCH" : "MISMATCH"}`,
  );
  if (fixtureTsHash !== INSTRUMENT_190_SHA256) failed = true;

  const corpusHash = sha256File(CORPUS_PATH);
  console.log(`corpus ${resolve(CORPUS_PATH)}`);
  console.log(`  sha256 ${corpusHash}`);
  console.log(`  expected ${CORPUS_SHA256} — ${corpusHash === CORPUS_SHA256 ? "MATCH" : "MISMATCH"}`);
  if (corpusHash !== CORPUS_SHA256) failed = true;

  const corpus = readCorpus();
  const fixture = readFixture();
  const train = casesToSide("train800(600rev+200H-A)", trainingSplit(corpus));
  const dev = casesToSide("dev200(H-B)", devSplit(corpus));
  const inst = fixtureSide("sealed190", fixture);
  console.log(
    `\ncorpus seed ${corpus.seed}: ${corpus.cases.length} cases; train ${train.rows.length} rows, dev ${dev.rows.length}, fixture ${inst.rows.length}`,
  );

  const reports: LintReport[] = [lintSides(train, inst, threshold)];
  const devReport = lintSides(train, dev, threshold);
  const instSelf = lintSides(inst, inst, threshold);

  for (const r of [...reports, devReport]) {
    console.log(
      `\n${r.left} vs ${r.right}: ${r.removedCount} rows removed ` +
        `(left ${r.removedLeftCount}, right ${r.removedRightCount}; ${r.flaggedPairs} flagged pairs) ` +
        `pairs ${r.forward.pairsCompared} grams L${r.leftGramPopulation}/R${r.rightGramPopulation} ` +
        `${r.silent ? "SILENT" : "FIRED"}`,
    );
    for (const row of r.removed.slice(0, 20)) {
      console.log(
        `  removed[${row.side}] ${row.id} <- ${row.matchedSourceIds.slice(0, 5).join(",")} shared=${row.maxSharedGramCount}`,
      );
    }
  }

  let demoResult: DemoResult | null = null;
  if (demo) {
    demoResult = demonstrateLint(train, inst, threshold);
    console.log("\n-- lint demonstration (two-sided control, train -> fixture) --");
    for (const p of demoResult.probes) {
      console.log(
        `  ${p.ok ? "ok  " : "FAIL"} ${p.name} fired=${p.fired} expectFire=${p.expectFire} ` +
          `max-pairwise-shared=${p.maxPairSharedGramCount} aggregate-shared=${p.aggregateSharedGramCount} ` +
          `flagged-sources=${p.flaggedSourceIds.length} fields=[${p.fieldsThatCarriedTheSharedGrams.join(",")}]`,
      );
      if (p.sampleGrams[0]) console.log(`        e.g. "${p.sampleGrams[0]}"`);
    }
    if (!demoResult.ok) {
      console.log("  CONTROL FAILED: the lint did not answer both ways — it may not be trusted.");
      failed = true;
    }
  }

  const f4 = {
    falsifier: "F4",
    fires: !reports[0]!.silent,
    verdict: reports[0]!.silent
      ? "F4 did not fire — no >=2-shared-8-gram overlap between the 800 training rows and the sealed 190, in either direction"
      : "F4 FIRED — RUN VOID: the instrument was contaminated",
    trainVsFixture: reports[0],
    trainVsDev: devReport,
    fixtureSelfOverlap: {
      note:
        "the fixture against itself — a sanity check that the lint can fire at all on this side. " +
        "`lintSides` returns one audit record per side, so for two identical sides `removedCount` is " +
        "twice the number of distinct flagged rows. Both figures are given explicitly here.",
      distinctFlaggedRowsPerDirection: instSelf.forward.removedCount,
      rowsRemovedAcrossBothSides: instSelf.removedCount,
      flaggedPairs: instSelf.flaggedPairs,
      silent: instSelf.silent,
    },
    demo: demoResult,
    digests: {
      instrument190Expected: INSTRUMENT_190_SHA256,
      instrument190Actual: fixtureTsHash,
      corpusExpected: CORPUS_SHA256,
      corpusActual: corpusHash,
    },
  };

  mkdirSync(DATA_DIR, { recursive: true });
  writeFileSync(REPORT_PATH, JSON.stringify(f4, null, 2) + "\n");
  console.log(`\nF4: ${f4.verdict}`);
  console.log(`wrote ${resolve(REPORT_PATH)}`);
  if (failed) process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) main();
