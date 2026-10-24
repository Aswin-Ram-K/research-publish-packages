# UBIJ1 — coherent bijection: is one vocabulary achievable?

**Status: done.** Deliverable: `strategy/COHERENT_BIJECTION_MEASUREMENT.md`.

## Purpose

Measure whether the *coherent* release shape is achievable — i.e. rename the tooling in lockstep with the
data so no script looks a name up by a spelling the data no longer uses — and report it as a money number.
`tree-bij` was rejected for two-vocabulary incoherence (308 tooling occurrences; `bij.py` skips
`.py`/`.sh`/`.bash` and `verify/**`), not for leakage.

## Hard bounds (as given)

- ≤40 tool calls (used 38).
- Writes only: `scratch/ubij1/**`, `strategy/COHERENT_BIJECTION_MEASUREMENT.md`,
  `orchestration/units/UBIJ1.md`, `orchestration/handoffs/UBIJ1.json`.
- Never modified `repro/encoder-crossover-190-SANITISED/`, `scratch/uneutral3/**`, `scratch/uneutral4/**`,
  `scratch/uver13/**`, `papers/**`; never touched `/home/zer0null/Duval`; never ran `UBUILD1.build.sh`.
- Tag↔original map derived in memory only — never written to disk or logged.
- `ALL CLAIM NUMBERS PRESERVED: True` deliberately **not** cited as route-A evidence; route A re-run via
  `parse_fixture.py` + `compare.py`.

## Method

`scratch/ubij1/bij_one.py` — re-implements `bij.py`'s rename (10 taxonomy names discovered from the live
corpus, `sha256("BIJ/v1\0"+name)` ordering → `N01…N10`, word-bounded substitution, JSON/JSONL prose
masking so route A's stimulus is never rewritten) **without** the skip list: tooling renamed in the same
pass as the data. 1,639 pinned prose values → 1,774 mask needles; **prose-integrity failures: none**;
`map_shipped: false`.

```
python3 scratch/ubij1/bij_one.py scratch/ubij1/tree-one
  -> kinds discovered: 10 -> N01..N10
  -> files changed by class: {'ts': 3, 'tooling': 2, 'data': 15, 'prose': 4}
  -> exit 0
```

Compared artefact = **`scratch/ubij1/tree-one-r2`** (pristine second build). The working copy
`scratch/ubij1/tree-one` was later instrumented by `run_diags.sh` (10 extra files, and it **regenerated**
two of the 44: `second-labeller/disagreements.jsonl` 14,661 → 10,807 B, `second-labeller/metrics.json`
7,346 → 5,278 B), which inflates a naive census to 6,433 — not the release artefact.

## Result

| metric | value |
|---|---|
| bytes (44-file set) | **3,057,815** (bij 3,057,949; stripped 3,096,483) → **−134 B vs bij** |
| census (frozen 184-id decoded walk) | **5,364** (bij 5,384; stripped 9,247) → **−20** |
| inside stimulus (irreducible) | **2,171 / 30 ids**, unchanged |
| tooling class | 290 (bij 308); ts 600 → 598 |
| short code layer `K01…K10` (absent from the census's id list) | **3,676, 0 inside stimulus** — identical in all three shapes |
| complete decoded total (census + code layer) | **9,040** (bij 9,060; stripped 12,923) |
| idempotence | two builds byte-identical, manifest hash `b5527acb679c50d6bfb80dd090600daa6a4e1a840c7fb802723f2511ab9dea92` |

Every published number reproduced exactly: routeA ties 120 / agreement 0.34210526315789475 / kappa
0.32520740993294694 / exact 65 / zero 41; routeB 0.9052631578947369 / 0.9013584840356494 / 172 / 18;
AB 0.3526315789473684; arms 0.347368 / 0.347368 / 0.263158 / 0.452632 / 0.231579 / 0.678947;
closed 0.8837023738280471; roster 0.9139973672663448; 2×2 39 / 27 / 90 / 34.
`cases.json` sha256 and the scoring projection sha256
(`620e4a07f8add8c5c8073017d4148d1fa542bea1c711a02f9f98fd9193e8e50b`) are **identical** between
`tree-bij` and `tree-one`.

Tools run inside the emitted tree: `compileall` 0; JSON parse (800/200/18 records, 0 bad) 0;
`second-labeller/parse_fixture.py` 0; `compare.py` 0; `verify/recompute-claims.py` 0;
`harness/prepare.py` **2** (pre-existing corpus-digest pin, exits 2 in every shape — not caused by the
rename).

## Verdict

**Ship-able: yes.** One vocabulary for the renamed (project-identifier) vocabulary, tooling runs, every
number bit-intact, bytes and residual both below `tree-bij`. Accepted residual: **5,364** method-relative
/ **9,040** complete decode, of which the 2,171 inside the stimulus are irreducible.

## Findings for the parent

1. **The census method has a blind spot:** `scratch/uagnostic1/census.tsv` contains no `K01…K10` codes
   (`grep -c` → 0), so 16,813 / 9,247 / 5,384 never counted 3,676 code-layer occurrences present in
   **every** shape, none of them inside the stimulus. Any headline residual should say which figure it is.
2. **The coherent rename is cheap and safe:** it removes 20 occurrences (18 tooling + 2 `.ts`), 134 bytes,
   and nothing else — `cases.json`, the projection and all metrics are bit-identical.
3. **Instrumented vs pristine trees:** `run_diags.sh` mutates two of the 44 files and adds 10; measure the
   pristine twin or the fixed 44-file set.
4. **Unverified:** no `tsc` type-check (no TS toolchain in tree/workspace); no model training; 4
   compound-name leftovers (`context.package` inside longer identifiers) left by the word-boundary rule
   that protects the 23 in-stimulus questions.

## Evidence

See `strategy/COHERENT_BIJECTION_MEASUREMENT.md` (§2 command/exit-code table, §3 metric table, §4 census,
§5/§7 idempotence and bytes, §6 residual accounting). `strategy/` is untracked in this repo, so the
evidence is carried verbatim in `orchestration/handoffs/UBIJ1.json`.
