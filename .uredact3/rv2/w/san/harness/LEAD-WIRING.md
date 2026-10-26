# EXP#12 — wiring notes (sanitised)

> **WITHHELD BY POLICY (unit UREDACT1, 2026-10-15).** The as-audited copy of this file
> (`repro/encoder-crossover-190/harness/LEAD-WIRING.md`) carried the private repository's complete
> `npm run suite` script list, its CI job matrix, its repo-policy gate text and its internal
> decision numbers. That content is a map of the private tree, not of the measurement; it is
> withheld here. The original is preserved unchanged in the as-audited subset and described in
> `../REDACTION_REPORT.md` section 7. What remains is the whole wiring recommendation.

## 1. Wire the OFFLINE lint only

`lint.ts --demo` needs no model, no network and no credential: it hashes the sealed instrument,
re-runs the ≥2-shared-8-gram rule in both directions, and runs the seeded-copy control, failing if
the detector does not answer both ways. It is the only EXP#12 step safe to run in an offline CI job.

## 2. Do NOT wire training or evaluation

They download three **public** checkpoints (~1.7 GB), need a torch/transformers stack the repository
does not manage, and need a GPU. CI here is offline and has no GPU.

## 3. `export-fixture.ts` is subsumed by the lint

The lint already hashes the sealed instrument and fails on a mismatch, and `data/fixture-190.json`
is committed alongside it.

## 4. `analyze.py` and `collect.py` read `out/`

`out/` is not in the tree, so those two steps are run from `README.md`, not from CI.

## 5. The rendered split is byte-reproducible

Re-running `prepare.py` against the committed `data/corpus.json` and `data/manifest.json` regenerates
`data/train.jsonl` and `data/dev.jsonl` **byte-identically**; the digests are recorded in
`../INTEGRITY.md`, and the manifest records the split rule, the counts and the rendering spec.

## 6. Sanitised digest note

`lint.ts` and `export-fixture.ts` assert the **as-audited** instrument digest `076164ac…`. The
sanitised fixture legitimately hashes differently, because the `rationale` and `namespaces` *values*
were emptied. The scoring projection of the 190 cases (`id`, `kind`, `question`, `options`,
`correct`) is unchanged, and that projection's digest is the invariant a sanitised checkout should
assert. See `../REDACTION_REPORT.md` section 4.
