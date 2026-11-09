# The declared cell space — declared outside the rows (MATRIX-DECLARED-SPACE)

Audit: `experiments/ptr-engine/tools/matrix_audit.py` (the card named
`experiments/ptr-engine/longrun/matrix_audit.py`; no such file exists — the verifier's own
citation `:122` is the line `arms = sorted({r.get("arm") for r in rows if r.get("arm")})`, which
is `tools/matrix_audit.py:122`, so `tools/` is the file it measured and the one changed here).
Tests: `experiments/ptr-engine/longrun/tests/test_matrix_audit.py`.
Artifact: `experiments/ptr-engine/measure/MATRIX-HONESTY.json`. Zero inference requests.

## The defect this repairs

Pre-fix, the arm axis of the population was read from the rows it audits
(`tools/matrix_audit.py:122`). A cell invented in a rows file was therefore *learned as
declared*: the audit reported the injection as expected. Measured on a synthetic corpus
(`pointer-stable-2`, three turns, one manifest declaring only `pointer-stable`):

```
PRE-FIX: declared_cells=3, extraneous_cell=0 -> pointer-stable-2 ADMITTED as declared
PRE-FIX exit code: 0 (defect invisible)
```

## Where the declaration now comes from

| axis | declaration artefact | citation |
|---|---|---|
| arm name (legal population) | `run_longrun.py` `ARMS = (...)` | `experiments/ptr-engine/longrun/run_longrun.py:64` |
| arm legality, enforced | per-arm builder `raise ValueError(f"unknown arm {arm!r}")` | `experiments/ptr-engine/longrun/run_longrun.py:862` |
| which arm produced which rows file | run manifests `arm` + `rows_path` | `experiments/ptr-engine/longrun/manifests/*.json` (88 files; 23 admit the 9 grid batches) |
| checkpoint ids | fixture `checkpoints` / `repair.at_turn` | `experiments/ptr-engine/longrun/fixtures/LR-01.json:283` (`checkpoints`), `:303` (`repair`) |
| rep | the fixture's single-run contract: `1` | as above |

`run_longrun.py:64` is authoritative because it is the **only** driver that can emit a
long-run cell, and its builder refuses every name outside the tuple
(`run_longrun.py:862`) — an arm absent from that tuple cannot have been run honestly. The
manifests are authoritative for the arm↔file pairing because each is written *before* its run
and names both, so the pairing is never inferred from the output.

The card also cites `tasks-v5/runtime-v5/LR-01.v5.json` (checkpoints `:351`, repair `:465`).
`det_verify.FIXTURE` — the fixture the audit actually reads for AST truth — is
`fixtures/LR-01.json` (sha256 `2c07e461…9ba06a`, checkpoints at `:283`). It declares the same
four turn slots (12, 24, 46, repair at 30) but carries no explicit `id` fields, so the audit
synthesizes `cp.<i>.t<turn>`; the v5 runtime fixture (sha256 `967cef03…06ab567`) declares
explicitly `cp.0.t12`, `cp.1.t24`, `cp.2.t46`. The synthesized names coincide with the explicit
ones, so the choice moves no state — verified: 92 cells, same five figures.

If no manifest declares a rows file, the audit falls back to the full `ARMS` registry and
records the file in `declaration.manifest_declarations.gaps` (`declaration_gaps` in the
artifact) — never to the rows. On the real corpus there are **0** gaps and **0** manifest arms
outside the registry.

## The fifth state

`extraneous_cell` — a row whose (arm, checkpoint id) pair is not in the declared space, or
whose `rep` is not declared. It is counted in `states.extraneous_cell`, named individually
(`kind`, `arm`, `label`, `reason`, `rows_file`, `rows`) in `extraneous`, and makes the audit
**non-clean with exit code 11** — distinct from `1` (`--strict`, missing cells). The asymmetry
is exact:

* declared pair, no rows → `missing_turn_absent` / `missing_answer_empty` (an unrun arm is not a
  defect, so it must not exit 11);
* undeclared pair, rows present → `extraneous_cell` (exit 11).

`pass` / `fail` / the four `missing_*` states / `undecidable` keep their meanings, and
`extraneous_cell` never enters an accuracy denominator (it is not a declared cell).

## Real corpus, before / after

`measure/rows-longrun-*.jsonl`, 9 grid batches, 23 run/arm pairs × 4 checkpoint ids × 1 rep.

```
BEFORE (harvested arms, no extraneous state)
TOTAL   5 pass  38 fail  0 m_row  29 m_turn  7 m_ans  0 m_cp  13 undec  = 92
overall 5/43 (pass 5, fail 38, missing 36, undecidable 13) – PARTIAL GRID   exit 0

AFTER (declared externally)
TOTAL   5 pass  38 fail  0 m_row  29 m_turn  7 m_ans  0 m_cp  13 undec  = 92
overall 5/43 (pass 5, fail 38, missing 36, undecidable 13) – PARTIAL GRID   exit 0
extraneous_cell = 0   (92 (arm, checkpoint) pairs checked across 9 batches, 0 undeclared)
```

No existing cell is extraneous: the corpus contains no fabricated arm and no undeclared
checkpoint id. Config C (5/43 = 11.6 %) is unchanged.

## Tests (17 passed, offline)

(a) fabricated arm `pointer-stable-2` → `extraneous_cell`, named, exit 11;
(b) row with `cp.99.t99` → `extraneous_cell`, id named, exit 11;
(c) clean matrix (only declared pairs) → exit 0; (d) declared arm with no rows → still
`missing_turn_absent`, never extraneous, exit 0; (e) the real corpus: 92 cells,
5 / 38 / 29 / 7 / 13, `extraneous_cell` 0.
