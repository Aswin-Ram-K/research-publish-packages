# VARIANT B — the `DecisionKind` union REMOVED (a labelled alternative, **not** the default)

**The default subset is VARIANT A (`repro/encoder-crossover-190-SANITISED/`), which KEEPS the union.** UTS1 §5.2
flags the union as a genuine author trade, so both are produced. `REDACTION_REPORT.md` §6 assesses it; this file
is only the operator's view.

## What this variant changes

`files/fixture/reflex-decisions.ts` and `files/fixture/DECISION_CASE_SCHEMA.ts` replace the enumerated union

```ts
export type DecisionKind =
  | "worker.class"   // …
  | … | "acquisition";
```

with `export type DecisionKind = string;`, keeping the type name so both files still type-check, and **keeping the
line count** (the removed lines are replaced by explanatory comment lines) so `_line` provenance and every
`disagreements.jsonl` line citation stay valid.

## Apply it

```bash
cd repro/encoder-crossover-190-SANITISED
cp variants/no-union/files/fixture/reflex-decisions.ts      fixture/reflex-decisions.ts
cp variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts  fixture/DECISION_CASE_SCHEMA.ts
python3 verify/run-verification.sh          # re-proves the numbers on the variant you actually ship
python3 verify/recompute-claims.py          # every CLAIMS number must still print OK
```

**Re-run the verification after applying it.** The variant changes two declaration blocks and no field value, so
the scoring projection must stay `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` and every
number must hold — but "must" is not evidence; run it. Note the digest of the variant fixture differs from both
the as-audited and the VARIANT A digest, so `INTEGRITY.md` §1 does not describe this file.

## What it buys, measured

- **Removed:** the enumerated union *declaration* — 7 member lines, and the closed-set typing.
- **Not removed:** the seven kind **names**. They are the `kind` **values** of all 190 records, in
  `harness/data/fixture-190.json`, and in `results/*.json` / `metrics.json` (which stratify kappa by kind).
  Measured strict-mechanism lines: this variant's fixture **57** vs VARIANT A's **52**, and its schema **9** vs
  VARIANT A's **3** — higher, because the explanatory banner names the type it removed. **The taxonomy is
  disclosed either way.**
- **Cost:** the paper's "typed single-label" claim loses its declared closed set.
