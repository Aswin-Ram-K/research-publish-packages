# EXP#12 — what the Lead must wire, and what must NOT be wired

The build lane does not edit `package.json` or `.github/workflows/` (Lead-owned). These are the exact
lines, with the reason each is or is not recommended.

## Recommendation in one line

**Wire the OFFLINE lint only** (`exp12`). **Do NOT wire the training or evaluation** — they download
three checkpoints (~1.7 GB), need a Python/torch stack the repo does not manage, and need a GPU. CI is
offline by design (`ci.yml`: *"It must never require a model, a broker, or a credential"*).

---

## 1. `package.json` — two edits

### (a) add the script, after `"exp7": ...` in the `scripts` block

```json
    "exp12": "./scripts/run.sh tools/typed-channel/lint.ts --demo",
```

Place it next to the other `expN` entries so the experiment scripts stay together. Do **not** name it
with a colon (`exp12:lint`): the name is also a `.github/workflows/ci.yml` matrix entry, and a colon in
an unquoted YAML flow scalar is an avoidable parse risk.

### (b) add it to `suite`

Change this fragment:

```
"suite": "npm run ab && npm run adapter-conformance && npm run catalog-declarations && npm run commit-boundary && npm run commit-lineage && npm run dag && npm run dag-merge && npm run decision-record && npm run derivation-coverage && npm run disposal && npm run evals && npm run gates && ...
```

to:

```
"suite": "npm run ab && npm run adapter-conformance && npm run catalog-declarations && npm run commit-boundary && npm run commit-lineage && npm run dag && npm run dag-merge && npm run decision-record && npm run derivation-coverage && npm run disposal && npm run evals && npm run exp12 && npm run gates && ...
```

i.e. insert the five tokens `npm run exp12 &&` between `npm run evals &&` and `npm run gates &&`.

## 2. `.github/workflows/ci.yml` — one REQUIRED edit

The suite job is a matrix and **does not go through `npm run suite`**, and the file says so itself:

> *"Every new suite must therefore be added HERE as well as to `package.json`, or it runs locally and is
> silently unenforced in CI. … drift check 4 compares this list against `package.json` scripts.suite and
> FAILS if they disagree."*

So add `exp12` to the matrix, keeping the list sorted:

```yaml
        suite: [ab, adapter-conformance, catalog-declarations, commit-boundary, commit-lineage, dag, dag-merge, decision-record, derivation-coverage, disposal, evals, exp12, gates, hosted-layer, isolation, isolation-netns, lifecycle, loopback-relay, model-route, position-not-identity, sandbox, scope, state-entity, teardown]
```

That is the whole CI change. No new job, no new install step, no network.

### Why `exp12` is safe in CI

Measured on the build host, `./scripts/run.sh tools/typed-channel/lint.ts --demo` runs in a few seconds
and needs only Node ≥ 24 (which `actions/setup-node` already provides at `'24'`) plus the files already
in the tree:

* it reads `tools/typed-channel/data/corpus.json` and `data/fixture-190.json` (both committed);
* it hashes `evals/fixtures/reflex-decisions.ts` and fails if the digest is not
  `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`;
* it re-runs the ≥2-shared-8-gram rule in both directions over 152,000 pairs and fails if anything is
  flagged;
* it runs the seeded-copy control and fails if the detector does not fire on all three seeded copies
  **and** stay silent on the novel row;
* it rewrites `data/lint-report.json` (a tracked file, so the CI checkout becomes dirty — harmless, and
  the committed copy is regenerated only when the run is repeated locally).

It imports nothing from `evals/`, so it is not exposed to the TypeScript-strip-types loader.

## 3. What must NOT be wired, and why

| Step | Wire it? | Why not |
|---|---|---|
| `train.py` | **No** | downloads `answerdotai/ModernBERT-base`, `microsoft/deberta-v3-base`, `sentence-transformers/all-mpnet-base-v2`; needs torch + transformers + scikit-learn; ~12 min on a GB10. CI is offline and has no GPU. |
| `evaluate.py` | **No** | needs torch and the trained checkpoints from `out/`, which are gitignored. |
| `export-fixture.ts` | **No** | it is subsumed by `exp12`: `lint.ts` already hashes the sealed instrument and fails on a mismatch, and `data/fixture-190.json` is committed. |
| `analyze.py`, `collect.py` | **No** | they read `out/`, which is not in the tree. |

The Python half is reproduced from the README, not from CI. If the Lead wants them recorded as npm
scripts anyway, they would be documentation scripts only and must **not** enter `suite` or the matrix:

```json
    "exp12:train":  "python3 tools/typed-channel/train.py --epochs 3",
    "exp12:eval":   "python3 tools/typed-channel/evaluate.py",
    "exp12:analyze": "python3 tools/typed-channel/analyze.py",
```

(`exp12:analyze` is dependency-free and could in principle run in CI if `out/analysis.json` and
`out/eval-*.json` were committed — they are in `tools/typed-channel/results/`. It is **not** recommended:
`results/` is a copy, and a CI check that reads a copy instead of the run is a check that can pass while
the run is wrong.)

## 4. Two repo-policy items the Lead must also satisfy

1. **AGENTS.md rule 11 / D-074 (the docs correspondence gate).** `tools/` is in `code_roots`, so adding
   `tools/typed-channel/**` is a code write and requires a documentation write in the same change set —
   any file under `docs/`, or a root-level `*.md` — or the commit trailer
   `Docs-Impact: none — <reason ≥ 12 chars>`. The natural doc write is the experiment's own results:
   append `tools/typed-channel/results/REPORT.md` to §10 of
   `docs/research/experiments/EXP#12-typed-channel-comparison.md` (**after** the Results heading, so the
   frozen bytes above it are untouched — the gate freezes everything above the first
   `Results` heading). Note the gate lives on `docs/publication-polish` (D-074/D-075), not yet on this
   branch; if it merges first, this applies.
2. **The frozen pre-registration.** Do not edit anything above `## 10. Results`. Append only.
   `tools/typed-channel/README.md` is under `tools/`, so it is not subject to the `docs/` index check.
3. **The rendered split is gitignored and must not be believed committed.** The repository's root
   `.gitignore` carries a blanket `*.jsonl` rule, which matches `tools/typed-channel/data/train.jsonl`
   (2.2 MB, the 800 rows actually fitted) and `data/dev.jsonl` (485 KB, the 200 H-B rows). This is the
   same failure the `.gitignore` comment already records for `traces/` and `docs/research/*.jsonl`.
   Two options, and the Lead picks:

   *Preferred — do not commit them.* They are byte-reproducible: re-running
   `python3 tools/typed-channel/prepare.py` with the committed `data/corpus.json` and the committed
   `data/manifest.json` regenerates both files byte-identically (verified in the run: sha256
   `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` for `train.jsonl` and
   `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` for `dev.jsonl`, unchanged
   across a re-run). The manifest records the split rule, the counts and the rendering spec.

   *Or commit them*, by adding these two negations to the root `.gitignore` next to the existing
   `!docs/research/**/*.jsonl`:

   ```gitignore
   !tools/typed-channel/data/*.jsonl
   ```

   Either way: do **not** leave them uncommitted *and* believed to be in the tree.

4. **Trace record.** `tools/typed-channel/results/trace-records.jsonl` holds a ready-to-append
   `eval.run` record. The build lane did **not** call `tools/trace.ts append` — the trace store
   `traces/2026-09-28-duval-m0.jsonl` already had an uncommitted change from another lane when this
   experiment ran, and `append()` requires a dense successor `seq`; two concurrent appends would write
   the same `seq` and `verify()` would then fail. Append it after the other lanes settle.
   The same applies to the visit-log line in `tools/typed-channel/results/visit-log-line.txt`.
   (`results/trace-records.jsonl` is itself matched by the blanket `*.jsonl` rule — add a negation for
   `tools/typed-channel/results/*.jsonl` if it is to be committed as evidence.)
