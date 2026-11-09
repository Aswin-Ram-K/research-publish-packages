# HANDOFF-RECOVERY — what the disk was actually holding

**Generated:** 2026-10-26T10:28:49 · **Source:** `experiments/ptr-engine/measure/HANDOFF-LINT-rerun.json` (948 files scanned, 0 skipped mid-write) · **Unit:** HANDOFF-RECOVERY

## Totals

| stubs enumerated | recoverable | unrecoverable | not-a-stub | recovered files written | artifact entries now walkable |
|---:|---:|---:|---:|---:|---:|
| **16** | **8** | **7** | **1** | **8** | **33** |

The linter named **16** `E_STUB` files — under the 20 cap, so nothing was truncated. It also named **75** `E_ARTIFACT_ABSENT` and **40** `done`/`pass` claims whose artifacts are incomplete; those are not stubs and are out of this unit's scope.

## The ledger — one row per stub

| unit | stub B | classification | artifacts found (size, mtime) | what is missing | recovered file |
|---|---:|---|---|---|---|
| `C8-SENTENCE-FIX` | 204 | **unrecoverable** | experiments/miss-law/FIT-GAP.md (5,450 B) exists, but its own header withdraws it — tombstoned 2026-10-25 by C8-PARTITION and attributed to C8-FIT-GAP, not to this unit | No unit card, no log, and no byte in FIT-GAP.md is attributable to this unit; the deliverable was rewritten by later units and then withdrawn | — |
| `FIX-BITE` | 190 | **unrecoverable** | none | The only disk change in its window (2026-10-25 02:40-02:52) is tests/test_orchestration_handoffs.py at 02:42:59, which predates this stub (02:43:43) and belongs to FIX-HANDOFF-CLASSIFIER | — |
| `FIX-GREEN` | 193 | **unrecoverable** | none | Same window as FIX-BITE: no file exists that postdates the stub (02:43:35) and belongs to this unit; no card, no log | — |
| `FIX-HANDOFF-CLASSIFIER` | 271 | **recoverable** | test_orchestration_handoffs.py (32463 B, 2026-10-25T02:42:59)<br>VERIFY-CLASSIFIER-FIX.json (2274 B, 2026-10-25T02:50:47) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/FIX-HANDOFF-CLASSIFIER.json` |
| `PAPER-FINAL-V2B` | 11353 | **recoverable** | VERDICTS.md (424582 B, 2026-10-25T02:39:18)<br>MANUSCRIPT.md (93021 B, 2026-10-24T21:39:10) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/PAPER-FINAL-V2B.json` |
| `R2-A2` | 13106 | **unrecoverable** | docs/serving-options/R2-DESIGN.md (14,103 B, 2026-10-23T20:38) — names R2-A2 forward as the future owner of row A6, it does not record R2-A2's findings | No artifact carries the unit's fetch log or its capacity-lever findings; its only declared write path was its own handoff | — |
| `U6.10` | 240 | **unrecoverable** | src/resextract/dashboard/api.py (72,850 B, 2026-10-08T09:36) and tests/test_dashboard.py (67,020 B, 11:07) — both after the stub (07:48) but shared with the later U6.11-U6.20 units | No orchestration/units/U6.10.md, no state/logs/U6.10*, and no way to split the api.py bytes between U6.10 and its successors | — |
| `U6.19` | 272 | **unrecoverable** | the same two shared files (api.py 09:36, test_dashboard.py 11:07) | state/logs/U6.19* does not exist, no card exists (RECORD_REPAIR s4c), and api.py is written by successor units — attribution impossible | — |
| `UDENAME1` | 339 | **recoverable** | UDENAME1.md (1053 B, 2026-10-19T01:13:39)<br>md2tex.py (48515 B, 2026-10-19T01:15:45)<br>MANUSCRIPT.md (26364 B, 2026-10-19T14:19:26)<br>main.tex (32766 B, 2026-10-19T14:19:40)<br>ABSTRACT.txt (1967 B, 2026-10-19T14:19:40)<br>ABSTRACT_METADATA.txt (1594 B, 2026-10-19T14:19:40)<br>replay-record-not-decision.tar.gz (11533 B, 2026-10-19T14:19:56) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/UDENAME1.json` |
| `V2-CURRENT` | 12692 | **recoverable** | V2-CURRENT.md (12171 B, 2026-10-24T22:48:51)<br>final.json (12143 B, 2026-10-24T22:48:13)<br>recompute.py (2371 B, 2026-10-24T23:36:24)<br>sabotage_registry.py (2452 B, 2026-10-24T23:36:55)<br>count2.py (716 B, 2026-10-24T22:46:14) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/V2-CURRENT.json` |
| `V2.11` | 9000 | **recoverable** | V2.11.md (2635 B, 2026-10-08T08:38:05)<br>census.txt (4902 B, 2026-10-08T08:34:53)<br>contexts.txt (10300 B, 2026-10-08T08:35:13)<br>containment_before.txt (2978 B, 2026-10-08T08:35:49)<br>containment_after.txt (711 B, 2026-10-08T08:36:22)<br>equiv.py (1233 B, 2026-10-08T08:35:48)<br>decompose.py.backup-U2.10-revert-hazard (30936 B, 2026-10-08T08:32:39) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/V2.11.json` |
| `V2T` | 3893 | **recoverable** | c2c3c4.py (15950 B, 2026-10-08T07:16:45)<br>followup.py (7923 B, 2026-10-08T07:17:46)<br>followup_result.json (2222 B, 2026-10-08T07:17:48)<br>store_v3_ref.py (54257 B, 2026-10-08T07:15:49)<br>v2t_empty_migrations.py (282 B, 2026-10-08T07:18:06) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/V2T.json` |
| `V5F` | 385 | **recoverable** | baseline.txt (1464 B, 2026-10-08T08:19:56) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/V5F.json` |
| `V6E` | 301 | **unrecoverable** | an empty directory state/verify/V6E/ created 2026-10-08T08:04 | No file inside it; V6F's own recovery block records that V6E died at the route census (C2), and no state/logs/V6E* or card exists | — |
| `V6F` | 811 | **not_a_stub** | none on disk (its only declared write path is its own handoff) | E_STUB is a structural false positive: the body is not a pre-run placeholder — it records three executed sha256 probes (app.py/cli.py/main.py all match:true) and a named recovery of V6E, but in a non-contracted `recovery` key, so the linter sees no artifacts/evidence/commands | — |
| `V8D` | 331 | **recoverable** | c2.py (2234 B, 2026-10-08T08:45:27)<br>c2_stage.py (1833 B, 2026-10-08T08:46:29)<br>dbg.py (1349 B, 2026-10-08T08:46:40)<br>testdiff.txt (38270 B, 2026-10-08T08:45:09) | nothing that the disk can supply; per-field gaps are listed in the recovered record's unverified[] | `orchestration/handoffs/recovered/V8D.json` |

## What was reconstructed, and on what basis

Every recovered file cites the size and mtime of each artifact as observed, quotes the evidence lines **read out of the file**, and sets `"status":"recovered"` with `recovery.from_stub_sha256` / `stub_bytes` / `evidence_basis`. Anything the disk cannot settle is in `unverified[]` — never in `evidence`.

The three recoveries that carry the most weight:

- **`V2-CURRENT`** — `.verify-scratch/final.json` (12,143 B) is the unit's own machine body: `status`, `overall`, `checks`, `not_reproduced`, `overstated`, `unverified`, `tool_calls`, `bound`. The verdict survives almost intact; only the qwen 30,000-char crossover stays unmeasured, exactly as the unit's card says.
- **`FIX-HANDOFF-CLASSIFIER`** — the stub (02:42:46) is followed 13 s later by `tests/test_orchestration_handoffs.py` (32,463 B), and `VERIFY-CLASSIFIER-FIX.json` (02:50) verifies that exact clause at `:208` with a red pre-fix baseline. Authorship of the bytes is inference-by-elimination, recorded as such.
- **`V8D`** — four probes survive under `state/debris/V8D/tree/` (`testdiff.txt` alone is 38,270 B), and `orchestration/VERDICTS.md:1728` names them as the artifacts V8D left. The recovered claim is the *measurement*, not the defect V8E later refuted.

## Constraints honoured

- **Zero inference requests** — every value here was read from disk with Python/grep; nothing was generated.
- **`orchestration/handoffs/*.json` is read-only** — the stubs are byte-for-byte unchanged (each recovered record carries the stub's sha256 precisely so that can be re-checked). All writes are under `orchestration/handoffs/recovered/`.
- **No invented numbers** — the only numbers in a recovered record are sizes, mtimes, exit codes and file-quoted text.

## Linter gap (reported, not fixed)

`experiments/ptr-engine/tools/handoff_lint.py:167-194` has no `recovered` status. `E_STUB` is only evaluated for `status in ('partial','stub')`, and the success gate (`E_DONE_NO_EVIDENCE` / `E_DONE_NO_ARTIFACTS`) only fires for `status:'done'`. So a `status:'recovered'` record passes clean **even if it were empty** — precisely the stub condition this unit exists to catch. All eight recovered files do pass with exit 0 (see below), but that pass does not by itself prove they carry evidence. A fresh card should teach the linter the `recovered` status; the linter was not edited here.

## Dogfood — linter exit codes

| recovered file | `handoff_lint.py` exit |
|---|---:|
| `orchestration/handoffs/recovered/FIX-HANDOFF-CLASSIFIER.json` | 0 |
| `orchestration/handoffs/recovered/PAPER-FINAL-V2B.json` | 0 |
| `orchestration/handoffs/recovered/UDENAME1.json` | 0 |
| `orchestration/handoffs/recovered/V2-CURRENT.json` | 0 |
| `orchestration/handoffs/recovered/V2.11.json` | 0 |
| `orchestration/handoffs/recovered/V2T.json` | 0 |
| `orchestration/handoffs/recovered/V5F.json` | 0 |
| `orchestration/handoffs/recovered/V8D.json` | 0 |

`python3 experiments/ptr-engine/tools/handoff_lint.py <file>` for all eight returned **exit 0** with no errors and no warnings.

## What the disk was holding

**8 of 16** stubs were not lost work: **33** artifact entries across 8 units were sitting on disk with real content and plausible mtimes — including a full verifier verdict body (`V2-CURRENT`), a 29-file fixture set (`V2T`), the packaging output of a de-naming fix (`UDENAME1`), and a 38 KB differential (`V8D`). The other 8 were genuinely empty: three (`FIX-BITE`, `FIX-GREEN`, `V6E`) left nothing at all, four (`C8-SENTENCE-FIX`, `R2-A2`, `U6.10`, `U6.19`) left only files shared with, or later overwritten by, other units, and one (`V6F`) was never a stub.
