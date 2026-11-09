# HARNESS-MAP v2 — the harness that exists

**Unit** `HARNESS-MAP-V2` · **Date** 2026-10-26 · **Mode** offline, zero inference requests, no network, no `git`
**Supersedes** [`docs/HARNESS-MAP.md`](docs/HARNESS-MAP.md) (42,410 B, 329 lines, unit `HARNESS-MAP` `500a9255`) — that file is the
**historical record and is not edited**; this one cites it. Machine form:
[`experiments/ptr-engine/measure/HARNESS-MAP-V2.json`](experiments/ptr-engine/measure/HARNESS-MAP-V2.json).

**Why v2 exists.** Since v1 was written this session added `HARNESS-GUARDS`, `DECIDABILITY-SEAM`, `MATRIX-DECLARED-SPACE`,
`RECORD-STOP-REASON`, `FROZEN-TREE`, `GRADE-V5-REPAIR`, `GRADE-V6-DERIVE`, `PREREG-ARM-RUN`, `REQUEST-LEDGER`,
`HANDOFF-RECOVERY`, `LINT-RECOVERED-STATUS`, `UNIT-JOURNAL`, `PROJECTION-CALIBRATION`, `PUBLISHED-NUMBER-AUDIT`,
`STOP-REASON-AUDIT`. v1 is therefore wrong about **which codes exist and what they mean** — and exit codes are how this
project reports. v2 re-derives every stage and every code **from the source line that raises it**, then measures this
batch from the journals and handoffs.

---

## 1. Stage table, re-derived from the code

Every row was read from source; nothing is carried over from v1. `exit` is the code that stage emits on refusal.

| # | Stage | File · function | Reads | Writes | Exit | Gate it enforces |
|---|---|---|---|---|---|---|
| 1 | preflight | `experiments/ptr-engine/longrun/cell.py:141` `stage_preflight` | fixture JSON (`cell.py:122` `_load_fixture`), runner arms (`cell.py:127` `_runner_arms`), `grade_v5` truth derivation | — | **2** | fixture parses; arm known; every checkpoint has an integer `turn`, a question, an `answer_spec` that derives truth; answer contract present in the system prompt |
| 2 | harness freeze | `cell.py:223` `stage_harness` | sha256 of `HARNESS_FILES` (`cell.py:60-72`) + the fixture | — | **2** | `--expect-harness` must equal the combined digest of `run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`, `tools/det_verify.py`, fixture |
| 3 | budget | `cell.py:248` `stage_budget` | the runner's own `--dry-run` `would_send_total`, rows on disk | — | **3** | `would_send_total × 1.10 ≤ --budget` |
| 4 | projection | `cell.py:356` `stage_projection` (`turn_walls_from_rows:304`, `_p90:291`) | measured latency rows | — | **8** | projected requests × p90 turn wall ≤ `--max-wall`; documented never to preempt a budget refusal (`cell.py:372`) |
| 5 | cell send loop | `cell.py:411` `stage_run` → `run_longrun.py:1455` `run_cell` | frozen manifest, fixture, messages | `experiments/ptr-engine/measure/rows-*.jsonl`, one row per request | **4** | budget (`run_longrun.py:1576`), resume lineage (`:1465`), runaway (`:1592`, `:1637`, `:1740`, `:1847` → **6**) |
| 6 | tool channel | `client.py:474` `collect_stream`, `client.py:139` `derive_stop_reason`, `client.py:175` `truncated_for` | response stream | row fields `stop_reason`, `truncated` | **6** | closed `stop_reason` vocabulary: a cap stop is `completion_tokens ≥ max_tokens`, never guessed |
| 7 | grading | `cell.py:440` `stage_grade` → `grade_v5.py` | rows + fixture | `measure/cell-<arm>-<stamp>.grade-v5.json` | **5** | verdict derived from content; integer-only `NUM` |
| 8 | analysis | `cell.py:463` `stage_analyse` → `analyze_stats.py` | rows + the grade JSON | `measure/cell-<arm>-<stamp>.analysis.json` | **6** | a number **or** an explicit refusal — never a silent substitution |
| 9 | consistency seam | `cell.py:539` `stage_consistency` | `grade.arms[*].decidable`, `analysis.populations[*].graded_n` | — | **9** | `grader decidable > 0 ⟺ analyser graded_n > 0`; `--allow-inconsistent` records the override |
| 10 | record | `cell.py:566` `stage_record` | frames, analysis, grade, budget, harness, run | `measure/cell-<arm>-<stamp>.json` + `.md` | **none** | **GAP** — declared `7` at `cell.py:22`, never raised; an `OSError` here surfaces as interpreter exit **1** |
| 11 | handoff emission | `cell.py:621` `write_handoff` | the record | `orchestration/handoffs/<UNIT>.json` | **none** | **GAP** — writes a handoff without invoking `tools/handoff_lint.py` |
| 12 | matrix audit | `experiments/ptr-engine/tools/matrix_audit.py:600-631` `main` | rows dir + fixture / manifests / registry | `--out` JSON | **11** | every row cell must lie in the declared cell space; `--strict` missing → **1** (`:630`) |
| 13 | journal | `tools/unit_journal.py:60-180` | card paths | `orchestration/journals/<UNIT>.jsonl` (append-only, fsync) | **2** (usage) / **1** (missing artifact, `:174`) | artifact existence |
| 14 | handoff lint | `tools/handoff_lint.py:163` `lint_doc` | `orchestration/handoffs/*.json` | — | **1** / **2** | unit or verifier shape, artifacts exist, evidence non-empty; `status:recovered` additionally requires a `recovery` block (`:209-232`) |
| 15 | frozen tree | `tools/frozen_tree.py:401-460` `main`, `:363` `verdict_exit_code` | snapshot JSON, live digests | snapshot JSON (`snapshot` subcommand only) | **2** | relpath+sha256 identity of every input unchanged (**3** usage, **1** command failed) |
| 16 | request ledger | `tools/request_ledger.py:322-380` `main` | row files | ledger JSON/text | **4** | one currency — requests; **5** unreadable rows (`:341`), **3** usage |

## 2. Exit codes — verified at the raise site

Complete set actually raised today: **0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11** (11 codes).

| Code | Meaning | Verified raise site(s) |
|---|---|---|
| 0 | ok | `cell.py:803`, `request_ledger.py:380`, `frozen_tree.py:427`, `matrix_audit.py:631` |
| 1 | **undeclared** tool failure: missing artifact / strict-missing cell / cmd failed / lint red | `unit_journal.py:174`, `frozen_tree.py:54`, `frozen_tree.py:364`, `matrix_audit.py:630`, `handoff_lint.py:381` |
| 2 | frozen-snapshot mutated — **and** preflight refusal, **and** usage | `frozen_tree.py:363`, `frozen_tree.py:451`, `cell.py:146`, `cell.py:238`, `handoff_lint.py:400`, `stop_reason_audit.py:478`, `run_longrun.py:1983`, `unit_journal.py:30` |
| 3 | usage/preflight — **and** in-cell budget, **and** manifest write | `request_ledger.py:322`, `frozen_tree.py:401`, `cell.py:251`, `cell.py:282`, `run_longrun.py:2009` |
| 4 | budget would be exceeded | `request_ledger.py:373`, `cell.py:434`, `run_longrun.py:1576` |
| 5 | unreadable row file — **and** resume-lineage mismatch, **and** grade-stage failure | `request_ledger.py:341`, `run_longrun.py:1465`, `cell.py:449` |
| 6 | runaway turn — **and** analyser refusal | `run_longrun.py:1592`, `:1637`, `:1740`, `:1847`, `cell.py:472` |
| 7 | consistency/record | `run_longrun.py:1874`, `run_longrun.py:1880` (smoke: `answer_source=none`, or a truncated row) |
| 8 | projection over `--max-wall` | `cell.py:402` — **single site** |
| 9 | grader/analyser disagreement | `cell.py:559` — **single site**, gate at `cell.py:534-563` |
| 11 | extraneous cell | `matrix_audit.py:627` — **single site** |

### Findings on the code set

- **`declared_but_unraised` = 1 → code `7`.** `cell.py:22` declares *record — one JSON + one markdown (exit 7)*, but
  `grep -c 'Abort(7' cell.py` = **0**. The record stage has no refusing path; a write failure escapes as exit **1**.
  Code `7` *is* raised, but only by the runner's smoke gate (`run_longrun.py:1874,1880`), i.e. a different stage than the
  one that declares it.
- **`undeclared_but_raised` = 1 → code `1`.** Four tools return it; no declared vocabulary contains it. A run that ends
  `1` is today ambiguous between "artifact missing", "strict audit", "command failed" and "uncaught Python".
- **Overloaded codes.** `2` covers snapshot mutation, preflight and usage; `3` covers budget, usage and manifest write;
  `5` covers rows, resume lineage and grade failure; `6` covers runaway and analyse refusal. `8`, `9`, `11` are clean —
  one site each.
- **Two tools disagree about usage:** `frozen_tree.py:56` / `request_ledger.py:70` use `3`; `unit_journal.py:30` and
  `handoff_lint.py:400` use `2`.

## 3. This batch's cost, measured

Scope: the 20 cards of this session (18 with a journal — including this one — plus `DECIDABILITY-SEAM` and
`HARNESS-GUARDS`, handoff-only). Sources: `orchestration/journals/*.jsonl`, `orchestration/handoffs/*.json`.

| Figure | Measured | Source / method |
|---|---|---|
| cards | **20** | union of `orchestration/journals/` and this batch's `orchestration/handoffs/*.json` |
| card rounds | **20** | one round per card |
| live requests | **0** | no handoff records a live send; every card carries `OFFLINE`; the ledger's 1101 requests are historical rows, not this batch |
| requests per card | **0** | as above |
| zero-request rounds | **20 / 20** (100 %) | as above |
| tool calls per card | **measured for 6, `not_measured` for 14** | `handoff.tool_calls`: ATTACK-GRADE-V5 17, FROZEN-TREE 22, MATRIX-DECLARED-SPACE 26, PUBLISHED-NUMBER-AUDIT 13, STOP-REASON-AUDIT 25, UNIT-JOURNAL 13 — total **116**; 14 handoffs carry no `tool_calls` key |
| bound utilisation | **116 / 166 = 69.9 %** (same 6 cards) | `handoff.bound` 32, 26, 28, 26, 28, 26 |
| wall time per card | **15 cards measurable**, 5 `not_measured`; sum of per-card spans **6 473 s**, median **317 s**, max **1 380 s** | journal timestamps; spans overlap, so the sum is not elapsed time |
| heaviest stage by calls | **audit / verification**, not the send loop | MATRIX-DECLARED-SPACE 26/28 and STOP-REASON-AUDIT 25/28 bind the audit stage; `cell.py:411` `stage_run` sent **0** requests — per-call stage attribution is not recorded anywhere, so this is card-level evidence, not call-level |

**Delta against v1** (`docs/HARNESS-MAP.md:1-8`, `:76-125`: *40 card rounds / 863 live requests / 31 zero-request rounds*):

| Figure | v1 | v2 (this batch) | Delta |
|---|---|---|---|
| card rounds | 40 | **20** | −20 — **different unit of work**: v1 costed *one trustworthy graded cell*; this batch built the gates |
| live requests | 863 | **0** | −863 |
| zero-request rounds | 31 (77.5 %) | **20** (100 %) | +22.5 pp |
| requests per round | 21.6 | **0** | the science spend is gone; the process spend is not |

The comparison is deliberately not flattering: v1's rounds bought measurements, this batch's rounds bought guards. The
like-for-like number is **requests per round: 21.6 → 0**, and the cost that replaced it is measured in §5.

## 4. The 14 inefficiencies, re-ranked

`closed` 6 · `narrowed` 5 · `open` 2 · `superseded` 1.

| # | v1 item (abridged) | State | Closed / changed by | What remains |
|---|---|---|---|---|
| 1 | answer shape unconstrained, grader parses prose | narrowed | `GRADE-V6-DERIVE`, `GRADE-V5-REPAIR` (12/12 gradeable, integer-only `NUM`) | fixtures still ship prose prompts; the contract is derived after the fact, not enforced at send time |
| 2 | fixture re-authoring, 4 generations | **open** | — | no unit this batch versioned fixtures; the cell space is audited (`exit 11`) but generations remain unversioned inputs |
| 3 | answerless acceptance, 36/92 cells missing | superseded | `MATRIX-DECLARED-SPACE` | absences are now counted against a printed declaration (`matrix_audit.py:630` → 1), not discovered later |
| 4 | tool channel refuses silently, model never told why | narrowed | `RECORD-STOP-REASON`, `STOP-REASON-AUDIT` | the *reason* is recorded; the model still is never told |
| 5 | budgets counted in three currencies | **closed** | `REQUEST-LEDGER` (14 files / 1101 rows / 1101 requests / 232 `assumed_billed`; 16/16 tests, mutant run 6 failures) | — |
| 6 | mid-cell code-version mixing | **closed** | `FROZEN-TREE` (snapshot + `exit 2`; 7 tests red→green) + `cell.py:223` | — |
| 7 | no grader checks line-of-descent | narrowed | `run_longrun.py:1465` refuses `--resume` on a manifest digest mismatch (5); `cell.py:223` freezes the harness per cell | a grader invoked outside `cell.py` still accepts rows from any fixture |
| 8 | handoff stubs strand on restart | **closed** | `HANDOFF-RECOVERY` (16 `E_STUB` → 8 recovered, lint exit 0), `LINT-RECOVERED-STATUS` (20 tests) | — |
| 9 | acceptance gate undecidable for 5 of 13 checks | narrowed | `DECIDABILITY-SEAM` (9), `GRADE-V5-REPAIR` | undecidable checks still grade as `null`; the seam catches disagreement, it does not create decidability |
| 10 | verification guard red and not runnable | narrowed | `HARNESS-GUARDS`: `test_guards` 6/6 green (each case carries its red half), `test_cell` 7 OK, `test_client_ttft` 8/8, `test_wire_client` 18/18 — *and the PYTHONPATH half is fixed*, so the guard now runs: `PYTHONPATH=src python3 -m pytest tests/test_orchestration_handoffs.py -q` → 12 passed, 1 failed | `test_no_new_contract_key_gaps` still fails on the **same three** pre-existing verifier-shape handoffs v1 named: `V2-RUNTIME.json`, `V3-FIXTURE.json`, `V3-PILOT.json` missing `overall`,`checks` |
| 11 | reasoning spend dominates, truncates at the cap | **closed** | `HARNESS-GUARDS` (`max_tokens` default 4096, `run_longrun.py:1933-1937`; thinking off; `--turn-wall-cap`; `--runaway-turns` → 6) + `PROJECTION-CALIBRATION` (p50 129.1 s / p90 427.7 s thinking-auto vs p50 2.9 s pooled thinking-off) | the 4.5× p90 gap now *refuses* cells that would have blown the wall (`cell.py:402`, exit 8) |
| 12 | three graders disagree, none authoritative | **closed** | `DECIDABILITY-SEAM` (9) + `GRADE-V6-DERIVE` | — |
| 13 | cross-run regrade is prose, not a command | **open** | — | `experiments/ptr-engine/tools/` lists no `regrade*.py`; the loop still lives in `REGRADE-DET.json` prose |
| 14 | prereg prose re-authored per generation | **closed** | `PREREG-ARM-RUN` (frozen decision rule; `sha256(rule body) == rule_sha256` `21cb8551…`; 12 cp ids agree; 8 decision cells, 4 pending inputs) | — |

### New ranked top 5 — what is actually wasting work now

| Rank | Waste | Evidence | Why this rank |
|---|---|---|---|
| 1 | **verification overhead exceeds the change itself** | 54 of 71 recorded evidence commands are verification-shaped, **4** are change-shaped (76.1 % / 5.6 %) | it is now the single largest consumer; see §5 |
| 2 | **the row schema still cannot say why a turn ended, for 147 of 1101 rows** | `STOP-REASON-AUDIT`: causes `{unrecorded_empty_content: 147, no_answer_text_field: 27, zero_tokens_no_content: 12}`, 172 empty-with-tokens | the vocabulary is closed now, but the historical corpus stays unlabelled — every re-analysis pays for it |
| 3 | **the journal cannot report the cost it exists to report** | two schemas in one batch (`{t,step,kind}` in 4 units vs `{ts,event,…}` in 14); 5 of 20 cards have no wall time, 14 of 20 no `tool_calls` | this map's own §3 is 70 % `not_measured` because of it |
| 4 | **handoff completeness is not checked by the thing that writes handoffs** | `cell.py:621` `write_handoff` never calls `handoff_lint.py`; 14 of 20 batch handoffs omit `tool_calls` | cheap to fix, and it is the reason rank 3 exists |
| 5 | **a stage with a declared exit code and no code path** | `cell.py:22` declares 7; `Abort(7` count = 0 | a failure in the record stage reports `1`, which nothing documents |

## 5. What the gate chain itself costs

Every card now carries a bound, a write-path list, a journal-first rule and red→green evidence. Measured over this
batch's handoff `evidence.commands` (71 commands from 20 handoffs):

| Bucket | Commands | Share |
|---|---|---|
| verification-shaped (`pytest`/`test_`/`sha256`/`grep`/`diff`/`verify`/`audit`/`lint`/`frozen_tree`) | **54** | **76.1 %** |
| change-shaped (`edit`/`write`/`apply`/`patch`/`create`) | **4** | 5.6 % |
| both | 2 | 2.8 % |
| neither (probes, `ls`, `wc`) | 11 | 15.5 % |

**The overhead is above half: 76 % of recorded commands re-check work rather than produce it.** That is a finding about
the process, and it is the one the operator asked for. Two limits on the number, stated rather than glossed: commands are
*summaries* — a handoff lists the commands that prove its claim, not every call — and per-call stage attribution is not
recorded anywhere, so the 116 recorded tool calls cannot be split by stage. The direction is unambiguous even so: six
cards report 116 calls against 4 mutating commands.

## 6. New inefficiencies this session discovered (not in v1)

| # | Defect | Artefact | Fix / status |
|---|---|---|---|
| N1 | a verifier that reads live files serialises every author — the author cannot edit while the verifier reads, so verification and change queue behind each other | [`docs/FROZEN-TREE.md`](docs/FROZEN-TREE.md) | **fixed**: `frozen_tree.py` snapshots relpath+sha256, `verify` exits **2** on a moved input; 7 tests red→green, demo mutation run exit 2 |
| N2 | a linter status assumed exempt from every check | [`docs/HANDOFF-LINT.md`](docs/HANDOFF-LINT.md) | **claim corrected**: `handoff_lint.py:209-232` *does* check `status:recovered` — it requires non-empty evidence **and** a `recovery` provenance block, and treats it as a stub candidate. The exemption is narrative, not code. Remaining gap: `tests/test_orchestration_handoffs.py` baselines exercise no `recovered` record |
| N3 | a published accuracy over the wrong denominator | [`docs/PUBLISHED-NUMBERS.md`](docs/PUBLISHED-NUMBERS.md) | **partly fixed**: integer-only `NUM` + gradeable-count derivation (`GRADE-V5-REPAIR`), declared-space denominator (`matrix_audit`). `not_measured`: `PUBLISHED-NUMBER-AUDIT`'s handoff carries no `command_or_count` |
| N4 | an audit whose declared space came from its own data | [`docs/MATRIX-DECLARED-SPACE.md`](docs/MATRIX-DECLARED-SPACE.md) | **fixed**: the declared space is printed as a formula, and a row cell outside it is `extraneous_cell` → **11** (`matrix_audit.py:627`) |
| N5 | a row schema that cannot distinguish a cap stop from a refusal | [`docs/STOP-REASON.md`](docs/STOP-REASON.md) | **fixed going forward**: `client.py:139` `derive_stop_reason` (precedence: error code → server `finish_reason` → `completion_tokens ≥ max_tokens` → `empty_response` → `unknown`); the 147 historical `unrecorded_empty_content` rows stay unlabelled |

## 7. The pipeline, one page

```
 fixture ─┐
          ▼
 [1] preflight ──2── fixture gradable? truth derivable? contract in prompt?
          ▼
 [2] harness freeze ──2── sha256(run_longrun, client, grade_v5, analyze_stats, det_verify, fixture)
          ▼                                    ▲ --expect-harness must match
 [3] budget ──3── would_send_total×1.10 ≤ --budget
          ▼
 [3b] projection ──8── projected_requests × p90(wall) ≤ --max-wall
          ▼
 [4] RUN  run_longrun.py ──4── budget abort
          │              ──5── resume refused (manifest digest ≠ rows)
          │              ──6── RUNAWAY ABORT (wall cap, or turn ate the ceiling)
          │              ──7── smoke: answer_source=none / truncated row
          ▼ rows-*.jsonl (1 row = 1 request, stop_reason closed vocabulary)
 [5] GRADE  grade_v5.py ──5── grader refused
          ▼ grade-v5.json
 [6] ANALYSE analyze_stats.py ──6── refusal printed, never a number
          ▼ analysis.json
 [6b] CONSISTENCY ──9── grader decidable>0  ⟺  analyser graded_n>0
          ▼
 [7] RECORD ──(none: declared 7, unraised)──► measure/cell-*.{json,md}
          ▼
 HANDOFF ──(none: not linted)──► orchestration/handoffs/<UNIT>.json ──1/2── handoff_lint.py
          ▼
 JOURNAL ──1/2── orchestration/journals/<UNIT>.jsonl
          ▼
 AUDIT ──11── extraneous cell · ──1── --strict missing · ──4── ledger over budget · ──5── ledger rows unreadable
```

### Where to look when a run fails

| Exit | Read this first |
|---|---|
| 0 | `measure/cell-<arm>-<stamp>.json` — `stages[]` and `consistency` |
| 1 | `handoff_lint.py` output, then the missing artifact path — **undocumented code**; also what an uncaught `OSError` in `stage_record` looks like |
| 2 | `docs/FROZEN-TREE.md`, then `cell.py:223` `stage_harness` — a measurement input moved; `frozen_tree.py verify` names the file |
| 3 | `cell.py:248` `stage_budget` / `request_ledger.py` usage — the dry-run's `would_send_total` vs `--budget` |
| 4 | `request_ledger.py` output and `run_longrun.py:1576` — requests already sent vs the card's budget |
| 5 | `request_ledger.py:341` or `run_longrun.py:1465` — the row file, or the manifest digest the rows were written under |
| 6 | `docs/STOP-REASON.md`, then the row's `stop_reason`/`truncated` — runaway turns, or an analysis that refused |
| 7 | `run_longrun.py:1874,1880` — the smoke row with `answer_source=none` or a truncated row |
| 8 | `cell.py:356` `stage_projection` and the `--projected-from` row file — p90 turn wall × projected requests |
| 9 | `cell.py:539` `stage_consistency` — `grader decidable` vs `analyser graded_n`, both printed in `consistency.line` |
| 11 | `docs/MATRIX-DECLARED-SPACE.md`, then `matrix_audit.py` — the printed declared-space formula vs the extraneous cell list |

## 8. Gaps — a stage with no gate that should have one

- `stage_record` (`cell.py:566`): no gate and no exit code; declared `7` is unraised. Give it `Abort(7, "7/7 record", …)` on `OSError`.
- `write_handoff` (`cell.py:621`): writes a handoff without linting it, so an incomplete handoff is only caught later — call `handoff_lint.lint_doc` before write.
- `unit_journal.py:30`: `EXIT_USAGE = 2` collides with `2 = frozen-snapshot mutated`; usage should be `3`, as in `frozen_tree.py:56`.
- Exit `1` has four meanings across four tools and appears in no declared set; either declare it or give each tool a distinct code.

## 9. Provenance of this document

- Stages and exit codes: read from source (`experiments/ptr-engine/longrun/cell.py`, `run_longrun.py`, `client.py`,
  `experiments/ptr-engine/tools/{frozen_tree,request_ledger,unit_journal,handoff_lint,matrix_audit,stop_reason_audit}.py`).
- Batch figures: `orchestration/journals/*.jsonl` (18 files), `orchestration/handoffs/*.json` (973 files, 20 in this batch).
- v1 figures quoted from [`docs/HARNESS-MAP.md`](docs/HARNESS-MAP.md) and never overwritten: where v1 and v2 differ, both are shown (§3).
- Zero inference requests; no network; no `git`; `docs/HARNESS-MAP.md` and every source/row/grade/fixture/handoff file untouched except this unit's five declared write paths.
