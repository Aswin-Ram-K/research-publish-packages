# Findings Ledger — Serving × Context Programme

One row per finding so the two programmes (Consonance and the context×serving experiment) stop telling two stories. Priced in **billed** tokens from the server's own cache report, never in payload size.

Rules:
- A row may not cite a live path for a value that changes — pin the digest instead.
- ABSENT ≠ 0
- DERIVED ≠ MEASURED
- No cross-build comparison.

| Finding | Number | Units | Source | Generation | Replicates on :8012 / :8014 | Status |
|---|---|---|---|---|---|---|
| Masking past eviction | 12/48 on :8012 (TX-02, all 12 at d=2); 8/48 on :8014 (TX-03, all 8 at d=2) (corrected from "0/48 on both stacks" — see RESULTS-TX02-CELL1.md line 20 and RESULTS-STACK-8014.md line 24) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md` (line 20: masking rep 1 12/48, d=2 12/12, d=8/20/32 0/12 each; line 82 boundary statement); `RESULTS-STACK-8014.md` (line 24: TX-03 masking r1 8/48) | TX-02 cell 1; TX-03 stack check | :8012 masking 12/48 (TX-02, line 20); :8014 masking 8/48 (TX-03, line 24) | VERIFIED (masking scores 12/48 on :8012 and 8/48 on :8014, both entirely from the d=2 bucket; "0/48 on both stacks" was unsupported) |
| Bounded fetch, single-fact recall | 41/48 (`:8012`), 42/48 (`:8014`) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md`, `RESULTS-STACK-8014.md` (line 38) | TX-03 | :8012 41/48; :8014 42/48 | VERIFIED (`RESULTS-STACK-8014.md:38` and `:61`) |
| Bounded fetch, aggregation | 4/48 (`:8012`), 0/48 with 243 fetch calls (`:8014`) | score out of 48 checkpoints; fetch calls | `RESULTS-KINDS-2-agg-abs.md` (line 35: 0/48 and 4/48; line 112 activation gate) | TX-AGG | :8012 4/48; :8014 0/48 (243 calls, line 26 of STACK-8014) | VERIFIED (`RESULTS-KINDS-2-agg-abs.md:35`; `RESULTS-STACK-8014.md:26`) |
| Bounded fetch, two-fact chain | 9/48 both stacks | score out of 48 checkpoints | `RESULTS-KINDS-2-agg-abs.md`, `RESULTS-STACK-8014.md` (line 62) | TX-HOP | :8012 9/48; :8014 9/48 | VERIFIED (`RESULTS-STACK-8014.md:57,62`) |
| Payload cut vs billed cut | −24.2% payload, −2.4% billed | % of tokens | Consonance `EXP#43` — `handoff from consonance/MEASURED_FACTS.md` (F1, line 12); `handoff from consonance/DO_NOT_REDO.md` (line 7) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:12`; `DO_NOT_REDO.md:7`) |
| Append-only cache hit climb | 0 → 0.489 | cached fraction | `handoff from consonance/MEASURED_FACTS.md` (F2, line 13) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:13`) |
| Rewrite cost per 48/72-byte handle | D-086 repayment step cost (48 of 72 prefix bytes moved) | prefix bytes moved | `handoff from consonance/MEASURED_FACTS.md` (F3, line 14); `handoff from consonance/DO_NOT_REDO.md` (D-086) | D-086 | n/a | VERIFIED (`MEASURED_FACTS.md:14` — "48 of 72 prefix bytes"; DO_NOT_REDO.md cites D-086) |
| Pinned fixture overwritten in place | 278 rows across six `rows-agg-*` files pin `2b416d827c36ec958aa50e54db4ec5d52f72f061e7c39e9a417b5f0b2078370c`; the sole on-disk `TX-AGG.v1.json` hashes `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03`; 0 of 56,431 workspace files and no git ref carry the pinned bytes | rows pinned (278/278) / digest copies found on disk (0) | `measure/FIXTURE-MAP-MT36.note` (143 lines: pin inventory, 56,431-file scan, re-serialization probe, `git log --all`); pins in `experiments/ptr-engine/measure/rows-agg-{fetch-mt36,fetch-mt50,fetch-test,fetch-test2,fetch-r1,masking-r1}.jsonl` | gen-7 (identifiers preserved across the rewrite: same `TX-AGG.v1`, N=100, `wall_tokens` 4312) | not comparable — every one of the 278 rows carries `claim: none`, `comparison_eligible: false` | VERIFIED (pin absent, rewrite timestamped; provenance unverifiable) |

| Corpus-wide fixture provenance loss | 1,368 of 7,734 pinned rows (17.7%) across 13 `rows-*.jsonl` files pin a `fixture_sha256` that no on-disk document carries; 6 distinct digests; 1,272 rows unrecoverable, 96 recoverable from git blob `f17663d1fed0` | rows pinned with no matching on-disk digest / pinned rows in `measure/rows-*.jsonl` | `orchestration/handoffs/U-SPCC-30.json`; `state/logs/lost-fixture-baseline.json` (dated freeze 2026-11-10); per-file evidence in §Corpus-wide fixture provenance below | gen-7 (`tasks-v7/TX-{AGG,HOP,SUP,01}.v1.json`), gen-4 (`tasks-v4/runtime-v4/LR-01.v4.json`), gen-1 (`runtime/LR-01.json`) | not comparable — every affected row carries `claim: none` and `comparison_eligible: false` | RECORDED (13/13 files overwritten in place; 0 never-committed, 0 unexplained; 96 rows recoverable from git, 1,272 not) |
| TX-03 masking cliff is content absence; position untested on this arm | 8/48 on `:8012` (SGLang, `occamy-1.0`; all 8 at `d2`); 40 failures each with 0 occurrences of the expected value, 8 passes each with exactly 1 occurrence + 1 anchor hit | score out of 48 checkpoints; prompt occurrences of the expected value | `experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md` (per-checkpoint table, presence/absence split, bucket counts 40/0/0/0); `orchestration/handoffs/U-SPCC-20.json` | gen-7 (`TX-03.v1`, `longrun/tasks-v7/TX-03.v1.json`) | not comparable — same arm/fixture pattern reproduced on two stacks: 3/3 runs on `:8012` (r1, r2, billed proof) at 8/48 with 8/8 at `d2` and 40/40 abstentions; `:8014` (vLLM) also 8/48 with 8/8 at `d2` but 39 abstentions + 1 substitution, `cp.TX-03.f07.d8` answered `3703` vs expected `3603` (a same-column constant from a different document); cross-build comparison not claimed (rule line 9) | VERIFIED (100/100 materialised prompts byte-identical to the recorded `prompt_sha256`; cause = content evicted at `intro+4`; contract and fixture excluded; depth/attention untested here — no post-mask prompt carries the value) |

### The TX-03 cliff is content absence; position is untested here

Run: `measure/rows-spcc-billedproof-2026-11-10.jsonl`, arm `masking-no-fetch`, 100 turns, endpoint `http://192.168.2.168:8012/v1` (engine `sglang`), `longrun/tasks-v7/TX-03.v1.json` (gen-7), model `occamy-1.0`, temperature 0, seed 42. Score 8/48. The 8 passes are all `d2` — asked at `intro+2`, **before** the mask. The 40 failures are five bucket widths — `d5`, `d6`, `d8`, `d20`, `d32` — × 8 probes each = **40**, asked **after** the mask at `intro+4`. Fixed by `experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md`; every prompt below was re-materialised through `longrun/run_longrun.py`'s own `run_cell` and matched the recorded `prompt_sha256` on 100/100 turns.

Replication: three independent `:8012` runs — `rows-tx03-masking-r1.jsonl`, `rows-tx03-masking-r2.jsonl` and the billed proof — each give 8/48 with 8/8 at `d2` and 40/40 abstentions (`ANSWER: NONE`). The `:8014` vLLM run (`rows-tx03-8014-masking-r1.jsonl`) gives the same 8/48 and 8/8 at `d2` but 39 abstentions + **1 substitution**: `cp.TX-03.f07.d8` answered `3703` where `3603` was expected — a same-column constant taken from a different document (`VAL_C` of `doc-fact-07` reported as the `VAL_C`-shaped value of the later `doc-fact-08` family), not a random number. That is the same arm/fixture pattern reproduced on two stacks, not a performance comparison between builds, and not the same measurement: no cross-build claim is made here (ledger rule 9).

Four exclusions:

- **Presence is binary and complete.** All 8 passing checkpoints contain the expected value exactly once (plus one `VAL_<X> = ` anchor hit); all 40 failing checkpoints contain it zero times. The search used a digit-boundary guard `(?<![\d.])3001(?![\d.])` so a neighbouring `3000` cannot alias. Bucket counts: content evicted 40, present-not-retrieved 0, contract-too-strict 0, fixture-unanswerable 0, unclassified 0.
- **Position (depth/attention) is untested on this arm — the earlier "position is excluded" wording is the superseded claim.** Passing probes retrieved correctly at request-token fractions up to **0.74** (`cp.TX-03.f08.d2`, 1809/2455 tokens) and **0.90** of user content (1809/2009), so a value sitting deep in the prefix is still recoverable; but every one of those is a pre-mask `d2` probe. All 40 post-mask prompts contain the expected value **0 times**, so this run never holds a present value at two distances and cannot say anything about where a present value sits. Position is E3's question (`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`), which keeps the body present and varies distance.
- **Answer-contract strictness is excluded.** All 40 failing answers are the literal well-formed line `ANSWER: NONE`, parsed with `answer_parse_error: null`; no prose or kind-mismatched value was rejected.
- **Fixture unanswerability is excluded.** Each fact's source text surfaced verbatim at its own intro turn, and the `d2` probe on the same document answers correctly.

Turn 6 verbatim (fact `doc-fact-01` introduced at T1, masked at T5):

```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
[MASKED doc-fact-01@r1]
ANSWER (T1):
```

`3001` occurs **0** times in that prompt; the only surviving number is `3000`, and only via T3's answer line `ANSWER (T3): ANSWER: NUM 3000`. Mask turns `[5, 12, 21, 28, 49, 56, 65, 72]` for facts introduced at `[1, 8, 17, 24, 45, 52, 61, 68]` = `intro+4` under `WINDOW_TURNS = 4` (`longrun/arm_cd.py`). The model is not forgetting; the content is not there.

### Recorded defects in the existing rows

These two columns are wrong in the rows already written; a later reader must not use them.

- `evicted` — **recorded defect**. Initialised `0` at `longrun/run_longrun.py:1453` and assigned only inside the `if arm == "transcript-grow":` branch at `:1476`. `masking-no-fetch` never enters that branch, so `evicted == 0` on all 100 rows, including turn 5 where `masked_rows = 1` and `masked_entry = [{'ref': 'doc-fact-01@r1', 'since_turn': 1}]`.
- `expected_present` — **recorded defect**. Computed at `longrun/run_longrun.py:2581` as `bool(contains_expected(reasoning_raw, expected))`, i.e. over the reasoning channel rather than the prompt. With thinking off `reasoning_raw` is `''` on every row, so it is `False` on all 48 checkpoints, including the 8 correct answers (`cp.TX-03.f01.d2`: expected `3000`, answer `ANSWER: NUM 3000`, `expected_present = False`).

### What those 278 rows may and may not support

Timeline, exactly: `experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json` was rewritten **in place** at `2026-11-09T08:57:28Z` (mtime = ctime, a real write), about eight minutes after the last run that consumed the old bytes — `longrun-2026-11-09T084942Z-bounded-context-fetch-r1`, at `08:49:43Z`; the 20 manifests recording `fixture.sha256 = 2b416d82…` for that path run `08:21:44Z` → `08:49:43Z`. The only commit touching that path, `9fadcc9` ("preserve context x serving instrument, fixtures and measurements"), **already carries the rewritten bytes**, so no pre-rewrite blob exists in any ref, and no deletion of the path is recorded anywhere. Identifiers survived the rewrite — same `gen-7`, same `TX-AGG.v1`, same N=100, same `wall_tokens 4312` — while the ground truths changed: `cp.TX-AGG.g00.d2` expected 20786 in the rows versus 156145 on disk, `g01.d2` 60786 vs 210513, `g00.d6` 10131 vs 51443, `g02.d2` 100786 vs 269767, `g01.d6` 30131 vs 84932, `g03.d2` 140786 vs 268509 — 26 of 26 rows embedding a checkpoint agree on id/turn/question/source and disagree on `expected`, 0 identical.

These rows **may** support:

- the per-row measurements they recorded (billed/total/wall tokens, ttft, latency, `content_sha256`, `request_sha256`, arm, rep, turn, run id);
- that a run carrying the row's run id loaded a TX-AGG document hashing `2b416d82…` at that moment;
- grading of the answers actually emitted, against each row's **own** recorded `expected`.

These rows **may not** support:

- **reproducibility** — the prompt prefix cannot be rebuilt, so no derived token count can be re-checked;
- **substitution** of the current on-disk fixture's numbers (different document, different ground truths);
- **cross-arm comparability** — all rows carry `claim: none` and `comparison_eligible: false`;
- any **`ABSENT = 0`** reading of the missing fixture.

The procedural rule this produced — a fixture is identified by path **and** digest, so regeneration that changes any byte writes a new versioned path — is recorded in `experiments/ptr-engine/tools/build_fixture.py` (module docstring) and `docs/FIXTURE-GENERATIONS.md` §8.

### Corpus-wide fixture provenance

Audit `U-SPCC-30`, 2026-11-10. Method, repeatable: hash every on-disk document under `experiments/ptr-engine/longrun` whose `schema` starts `consonance.longrun-fixture` (**53 distinct digests**), then compare against every `fixture_sha256` pinned in `experiments/ptr-engine/measure/rows-*.jsonl` (**7,734 pinned rows across 93 files**; 7,969 rows total, 235 carry no pin). **1,368 rows in 13 files pin a digest with no on-disk match** — 17.7% of the pinned corpus, six distinct digests. This is the `TX-AGG` defect above, corpus-wide.

**Scope — the loss does not touch any live claim.** Of the 93 `rows-*.jsonl` files, **80 have zero missing pins** and 13 have misses. Every affected file is a **first-generation** AGG/HOP/SUP run dated `2026-11-09` (plus the three `2026-10-26` `LR-01` files and `rows-smoke-tx01-20261109`), and each was **superseded by a later generation that pins a digest still on disk**:

| family | affected (first generation) | superseding generation, 0 missing |
|---|---|---|
| AGG | `rows-agg-fetch-{mt36,mt50,r1,test,test2}`, `rows-agg-masking-r1` — 278 rows | `rows-agg-8014` (141), `rows-agg2-2026-11-09` (242), `rows-agg3-instructed` (122) |
| HOP | `rows-hop-2026-11-09` — 450 rows | `rows-hop-8014` (195), `-r2` (191), `-r3` (247), `rows-hop2-fetch` (208), `rows-hop2-masking` (180), `rows-hop3-instructed` (197) |
| SUP | `rows-sup-2026-11-09` — 269 rows | `rows-sup2-fetch` (145), `rows-sup2-masking` (103) |
| TX-01 | `rows-smoke-tx01-20261109` — 16 rows | `rows-tx01-real-20261109` (10), `rows-smoke2-tx01-20261109` (10), `rows-contrast24-tx01-20261109` (51), `rows-control-nomask-tx01-20261109` (48) |
| LR-01 | `rows-longrun-2026-10-26{,-policy,-fix}`, `rows-longrun-v4-2026-10-26` — 355 rows | `rows-longrun-c-2026-10-26` (192), `rows-longrun-v3-2026-10-26` (96), `rows-longrun-v4-tools-2026-10-26` (68), `rows-longrun-v5-tools` (72), `rows-longrun-v6-tools` (72) |

**The headline results this ledger rests on have their fixtures available.** `rows-tx02-fetch-r1/r2` and `rows-tx02-masking-r1/r2` (the 12/48 masking row), all eight `rows-tx03-*` files including `:8014` (the 8/48 cliff row and the 41/48, 42/48, 4/48, 0/48, 9/48 rows), `rows-agg-8014`/`agg2`/`agg3`, `rows-hop-8014`/`hop2`/`hop3`, `rows-sup2-*`, and `rows-spcc-billedproof-2026-11-10` all pin digests that are on disk — **0 missing**. The 1,368 lost rows are superseded first-generation runs, not the evidence behind any current claim.

**For every file, including the 80 with zero missing pins, replay is unverified.** A matching `fixture_sha256` establishes only that the fixture bytes are present on disk; it does not establish that a run can be replayed, which additionally needs the model artefact, the server build and flags, the tokenizer, the sampling parameters, the harness code version and the prompt-construction path. No run in this corpus has been re-executed from its pinned fixture and compared row-for-row, so **"fixture available" must not be read as "reproducible"**.

| rows file | rows | pinned digest | fixture path (from manifest) | exists now | current sha256 | mtime (UTC) | consuming runs (UTC) | git ref carrying pinned bytes | class |
|---|---:|---|---|---|---|---|---|---|---|
| `rows-agg-fetch-mt36.jsonl` | 41 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none (`9fadcc9` already carries the rewritten bytes) | overwritten in place |
| `rows-agg-fetch-mt50.jsonl` | 54 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none | overwritten in place |
| `rows-agg-fetch-r1.jsonl` | 10 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none | overwritten in place |
| `rows-agg-fetch-test.jsonl` | 36 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none | overwritten in place |
| `rows-agg-fetch-test2.jsonl` | 37 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none | overwritten in place |
| `rows-agg-masking-r1.jsonl` | 100 | `2b416d82…` | `longrun/tasks-v7/TX-AGG.v1.json` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:21:44 → 08:49:43 | none | overwritten in place |
| `rows-hop-2026-11-09.jsonl` | 450 | `09157d80…` | `longrun/tasks-v7/TX-HOP.v1.json` | yes | `860aad56…` | 2026-11-09T09:04:41Z | 08:28:52 → 08:31:49 | none (`9fadcc9` carries `860aad56…`) | overwritten in place |
| `rows-sup-2026-11-09.jsonl` | 269 | `12f46fcd…` | `longrun/tasks-v7/TX-SUP.v1.json` | yes | `75ab558b…` | 2026-11-09T08:51:33Z | 08:21:13 → 08:22:21 | none (`9fadcc9` carries `75ab558b…`) | overwritten in place |
| `rows-smoke-tx01-20261109.jsonl` | 16 | `db497435…` | `longrun/tasks-v7/TX-01.v1.json` | yes | `44a1b435…` | 2026-11-09T06:13:23Z | 06:08:45 → 06:10:40 | none (`9fadcc9` carries `44a1b435…`) | overwritten in place |
| `rows-longrun-2026-10-26.jsonl` | 192 | `72c3832d…` | `longrun/runtime/LR-01.json` | yes | `b7e303a6…` | 2026-10-26T09:00:46Z | 06:46:11 → 08:39:28 | none (`f17663d1` carries `b7e303a6…`) | overwritten in place |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | `72c3832d…` | `longrun/runtime/LR-01.json` | yes | `b7e303a6…` | 2026-10-26T09:00:46Z | 06:46:11 → 08:39:28 | none | overwritten in place |
| `rows-longrun-2026-10-26-fix.jsonl` | 27 | `72c3832d…` | `longrun/runtime/LR-01.json` | yes | `b7e303a6…` | 2026-10-26T09:00:46Z | 06:46:11 → 08:39:28 | none | overwritten in place |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | `5a5f8c4b…` | `longrun/tasks-v4/runtime-v4/LR-01.v4.json` | yes | `8bdb58ae…` | 2026-11-09T03:51:12Z | 2026-10-26T11:18:31 → 19:05:21 | **`f17663d1fed0` blob = `5a5f8c4b…`** | overwritten in place, **recoverable** |

Full digests: `2b416d827c36ec958aa50e54db4ec5d52f72f061e7c39e9a417b5f0b2078370c`, `09157d80d163fcc1bc97f4cd8f0c33f66645d38bfc7621d05ff313cb1580dd5d`, `12f46fcdafe94f3238fc26d53724a091d4e0abb87aa7cac450165cc41a4b5f63`, `db4974356a3d313be1c5215272a8f988c09579e1856b72a434dbdcf3f1bcff53`, `72c3832d95f9c7966b4358eda10fa2882775a416ee8a663d57b1c871ed19c44d`, `5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235`. Current digests: `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03`, `860aad568c97d227a756111c359df19bdd2412e8db44f52644e8b23e2962fca0`, `75ab558b10aaf7712f6dd88824aa3d36f028df1726654e61208f7d7be5d3dc0a`, `44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21`, `b7e303a65f200e7b3dfd339cf3c6a1f3b4e684e57ca271e74f8f5539a348a500`, `8bdb58aebd2a1b013f36ae001a153a8f1221d98981ff81f18496620f2f09fc6b`.

**Three-way classification, per file — 13 of 13 are `overwritten in place`.**

- **overwritten in place — 13 files / 1,368 rows.** Every named path still exists, every current digest differs from the pin, and in every case the path's `mtime` is later than the last run that consumed the pinned bytes. Evidence per file is the `mtime`/`ctime` column against the consuming-run window: `TX-AGG` rewritten 08:57:28Z, eight minutes after its last consumer at 08:49:43Z; `TX-HOP` rewritten 09:04:41Z, 33 minutes after 08:31:49Z; `TX-SUP` rewritten 08:51:33Z, 29 minutes after 08:22:21Z; `TX-01` rewritten 06:13:23Z, 2m43s after 06:10:40Z; `LR-01` rewritten 2026-10-26T09:00:46Z, 21 minutes after 08:39:28Z; `LR-01.v4` rewritten 2026-11-09T03:51:12Z, days after 2026-10-26T19:05:21Z.
- **never committed — 0 files.** Every one of the six paths has at least one commit (`git log --all --format=%H -- <path>`: `9fadcc9` for the four `tasks-v7` fixtures and `LR-01.v4`, `f17663d1` for `LR-01` and `LR-01.v4`), so no path is absent from history. What is absent is the *pinned bytes*: hashing each historical blob shows the pinned digest in exactly one place.
- **unexplained — 0 files.** No file lacks both a live path and a historical blob.

**Blob check, stated explicitly because it decides the class.** For each of the six paths, `git log --all --format=%H -- <path>` yields the commits that ever touched it, and each historical blob is hashed. `git show 9fadcc9:experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json` exits 0 with **95,742 bytes, sha256 `860aad56…`** (`git ls-tree 9fadcc9 -- <path>` → `100644 blob 30f75ee0…`), so the path *was* committed and the pinned `09157d80…` is not in it — `TX-HOP` is **overwritten in place**, not never-committed. `TX-SUP` behaves identically: `git show 9fadcc9:…/TX-SUP.v1.json` exits 0 with 55,018 bytes, sha256 `75ab558b…` (`100644 blob 94b7ffc3…`). A `git show` that returns empty bytes (`e3b0c442…`) means the path was absent from that commit, which is not the case for any of the six.

**Recoverability split.** 12 files / 1,272 rows: the pinned bytes were **never committed** — the only commit touching the path already carries the rewritten bytes, so no ref can restore them. 1 file / 96 rows (`rows-longrun-v4-2026-10-26.jsonl`): the pinned bytes **do** survive, as the blob at `f17663d1fed0:experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json`, sha256 `5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235` — verified by hashing the blob, not inferred. That is the only recoverable fixture in the corpus; nothing else is claimed recoverable.

**Recorded defect, separate from the loss.** The 20 manifests that consumed `LR-01` record the absolute path `/home/zer0null/reserach extarctor/experiments/ptr-engine/longrun/runtime/LR-01.json` — a misspelling of the repo root (`reserach extarctor`). That path never existed; the fixture is identified by the repo-relative path in the table. The typo is why a naive path-existence check reports those 259 rows as "path missing" rather than "digest differs".

**What these 1,368 rows may support:** the per-row measurements they recorded (billed/total/wall tokens, ttft, latency, `content_sha256`, `request_sha256`, arm, rep, turn, run id); that a run carrying the row's run id loaded a document hashing the row's pin at that moment; and grading of the answers actually emitted against each row's **own** recorded `expected`.

**What they may not support:** reproducibility (the prompt prefix cannot be rebuilt, so no derived token count can be re-checked); substitution of the current on-disk fixture's values (different document, different ground truths); cross-arm or cross-build comparison (every affected row carries `claim: none`, `comparison_eligible: false`); and any `ABSENT = 0` reading of a missing fixture. A reader who assumes this corpus is reproducible is wrong about 17.7% of its pinned rows, and a reader who assumes the remaining 82.3% are replayable is unverified — see the replay note above.

**Guard.** `experiments/ptr-engine/longrun/tests/test_lost_fixture.py` freezes these 1,368 `(file, line)` misses in `state/logs/lost-fixture-baseline.json` as a dated freeze (`frozen_at` 2026-11-10, audit `U-SPCC-30`). The freeze is forward-only: a *new* row pinning a digest with no on-disk file fails the test, and the failure message says the fixture was destroyed after 2026-11-10. The assertion is set equality on `(file, line)`, not a count, so a swap of one lost row for another also fails.

## Open questions this ledger does not answer

- Is the distance cliff a matter of presence or position (E3)? **Half closed: the 40 failures are content absence**, verified as 0 occurrences of the expected value in every post-mask prompt — see §The TX-03 cliff is content absence; position is untested here above. **The position half is open:** this arm's surviving probes are all pre-mask `d2`, so no present-value distance contrast was ever run, and the earlier "presence, not position / position is excluded" reading is superseded. E3 (`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`) keeps the body present and varies distance.
- Whether bounded fetch's aggregation ceiling can be lifted above 4/48.
- Whether a fork of SGLang is justified (per-range eviction, non-prefix reuse, per-range attribution).
- Whether Nemotron Nano can hold the answer contract at or above occamy.
- Whether HiCache pays for itself in billed tokens (E5).
