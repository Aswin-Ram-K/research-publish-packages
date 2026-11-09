# ROW-PROVENANCE — every row says what produced it

**Unit:** `ROW-PROVENANCE` · **Card:** `25c15347-4045-4941-a07b-0171c6b66349` · **Date:** 2026-10-26
**Cost of this unit:** **zero inference requests** — no network, no lock, no live measurement.
Every number below was produced by reading files already on disk.

## 1. Why this exists

`HARNESS-MAP-V2` (`experiments/ptr-engine/measure/HARNESS-MAP-V2.json`) had to infer a
"harness era" axis from **file mtimes**, because a row carried no harness, fixture generation,
model or thinking field. That inference then gated the only arm comparison the project has:
`LATENCY-REPORT` marked every pair whose era is load-bearing **NOT COMPARABLE**, and
`docs/OPERATOR-BRIEF.md` reports H1 as not adjudicable partly for that reason.

Four revisions of the same fixture (`LR-01.v2 → v4 → v5 → v6/v7`) each changed the task while
the rows stayed anonymous — so a grid measured under v2 could not be told apart from one
measured under v7 except by **guessing at filenames**. §5 shows that guess was wrong in at
least two places.

## 2. The fields

Nine provenance fields, written on **every row** and published once on the **run manifest**.
(The card's prose calls this "the eight fields" while its field list names nine; the list is
authoritative here and all nine are written.)

| field | what it names | where the runner gets it |
|---|---|---|
| `arm` | the arm under test | `make_row`'s `arm` argument |
| `model` | model name | `cfg.model` (`--model`) |
| `endpoint` | serving base URL, trailing slash stripped | `cfg.base_url` |
| `fixture_id` | `<task_id>.<fixture_version>` — e.g. `LR-01.v5-answer-contract` | `client.fixture_label(fixture)` |
| `fixture_sha256` | sha256 of the exact tasks file used | `fixture["_sha256"]` (the loaded file) |
| `harness_sha256` | digest over the five harness files **plus** the fixture, combined exactly as `cell.py:stage_harness` combines them | `run_longrun.harness_sha256_now()`, which **reads** `cell.HARNESS_FILES` |
| `max_tokens` | the completion ceiling as configured | `cfg.max_tokens` |
| `thinking` | the literal mode string `"off"` / `"on"` / `"auto"` | `client.thinking_setting(cfg)` — the same call the row's own `thinking` field already used, so the two can never disagree |
| `tools_mode` | `"off"`, or `"on:<csv>"` naming the tools sent | `client.tools_mode_label(tool_names(cfg))` |

Plus two companion keys on every row:

* `provenance_complete` (bool) — `true` only when all nine are known;
* `provenance_missing` (list) — the names that are not, so nobody re-derives them.

### The "unknown" rule

An unknown provenance value is the **string `"unknown"`** and the row carries
`provenance_complete: false`. It is never `null`, and no field is ever filled by a plausible
guess: a wrong value is worse than an admitted gap.

### Where it is stamped

| site | file:line |
|---|---|
| field set + helpers + `same_provenance` (canonical) | `experiments/ptr-engine/longrun/client.py:799` (`PROVENANCE_FIELDS`), `:816` (`PROVENANCE_LOAD_BEARING`), `:854` (`provenance_block`), `:880` (`fixture_label`), `:896` (`same_provenance`) |
| harness digest, read-only against `cell.HARNESS_FILES` | `experiments/ptr-engine/longrun/run_longrun.py:1431` |
| the run's provenance block | `experiments/ptr-engine/longrun/run_longrun.py:1464` (`provenance_for`) |
| **every row** | `experiments/ptr-engine/longrun/run_longrun.py:1647` — `row.update(provenance_for(cfg, fixture, arm))` |
| **the manifest** | `experiments/ptr-engine/longrun/run_longrun.py:1199` — `"provenance": provenance_for(cfg, fixture, arm)` |

**Recorded correction to the card:** the card says the row writer is `make_row` *in
`client.py`*. There is no `make_row` in `client.py`; the row writer is
`run_longrun.make_row` (`run_longrun.py:1484`). The field set and the pure helpers live in
`client.py` (so the tool and the runner share one definition); the stamping happens in
`run_longrun.py`. Both files were in this unit's write paths.

`harness_sha256` is the one field the runner does **not** already hold: it was only ever
computed inside `cell.py`. Rather than copy that algorithm (drift) or guess, the runner now
computes it from `cell.HARNESS_FILES`, **read, never edited**, and falls back to `"unknown"`
if `cell` cannot be imported or a harness file is missing.

## 3. The retrofit: read, never rewrite

`experiments/ptr-engine/tools/row_provenance.py` derives provenance for the **14 rows files**
the request ledger already enumerates (`measure/REQUEST-LEDGER.json` → `per_file`). It opens
every one of them **read-only** and writes nothing back; a rows file is a measurement.

Per field, the first rung that actually has the value wins:

1. **`row`** — the row itself carries the field. Strongest: stamped at write time by the
   process that made the measurement.
2. **`manifest`** — a sibling run manifest under `longrun/manifests/` whose `rows_path` is
   this file and whose `arm`/`rep` match, narrowed further by `fixture.sha256` when the row
   carries one. Nothing is inferred from a filename.
3. **`cell`** — a cell report under `measure/cell-*.json` whose `run.rows_path` is this file
   and whose `arm` matches. This is the **only** place on disk holding a
   `harness.harness_sha256` bound to a rows file.
4. **`"unknown"`** — nothing says.

`fixture_id` is resolved by **content address**: the fixture sha is looked up among the
fixture files under `longrun/tasks-*/` and `longrun/runtime/`, and the matching file's own
`task_id`/`fixture_version` name it. When the sha matches no fixture on disk, the file was
mutated in place (`longrun/runtime/LR-01.json` was, four times), so only the manifest's
`task_id` survives and the version stays unresolved — recorded as such, not invented.

A file-level field on which the rows of that file disagree is reported `"mixed"`: the file
then genuinely has no single provenance for it. A field that only *some* rows carry is
reported with the value those rows agree on, and the gap is counted in `partial_rows`.

Where several manifests could describe one file, `manifest_candidate_values` records the
distinct load-bearing values they would have supplied, so a pick is never mistaken for a
consensus. Thirteen of the fourteen files have at most one candidate after narrowing; the one
that does not is named in §4.

### The retrofit table

```
file                                            · arm             · fixture_id               · fixture_sha256 · harness_sha256 · model            · thinking · tools_mode   · source_of_truth  
----------------------------------------------- · --------------- · ------------------------ · -------------- · -------------- · ---------------- · -------- · ------------ · -----------------
rows-baseline-2026-10-26.jsonl                  · mixed           · unknown                  · unknown        · unknown        · mixed            · unknown  · unknown      · row              
rows-cell-pointer-stable-20261026T145758Z.jsonl · pointer-stable  · LR-01.v5-answer-contract · 967cef03c362   · unknown        · occamy-1.0-NVFP4 · auto     · off          · manifest+row     
rows-equalinfo-2026-10-26.jsonl                 · mixed           · unknown                  · unknown        · unknown        · mixed            · unknown  · unknown      · row              
rows-live-2026-10-26.jsonl                      · unknown         · unknown                  · unknown        · unknown        · mixed            · unknown  · unknown      · row              
rows-longrun-2026-10-26-fix.jsonl               · mixed           · LR-01                    · mixed          · unknown        · occamy-1.0-NVFP4 · auto     · off          · manifest+row     
rows-longrun-2026-10-26-policy.jsonl            · mixed           · LR-01                    · 72c3832d95f9   · unknown        · occamy-1.0-NVFP4 · unknown  · off          · manifest+row     
rows-longrun-2026-10-26.jsonl                   · mixed           · LR-01                    · 72c3832d95f9   · unknown        · occamy-1.0-NVFP4 · unknown  · off          · manifest+row     
rows-longrun-c-2026-10-26.jsonl                 · mixed           · LR-01.v2-bounded         · 0a07db1b14f3   · unknown        · occamy-1.0-NVFP4 · off      · off          · manifest+row     
rows-longrun-v3-2026-10-26.jsonl                · mixed           · LR-01.v3-answer-marker   · 07abab0bd902   · unknown        · occamy-1.0-NVFP4 · off      · off          · manifest+row     
rows-longrun-v4-2026-10-26.jsonl                · mixed           · LR-01.v4-slice-widened   · 5a5f8c4be202   · unknown        · occamy-1.0-NVFP4 · off      · off          · manifest+row     
rows-longrun-v4-tools-2026-10-26.jsonl          · pointer-stable  · LR-01.v4-slice-widened   · a592a48ff3e5   · unknown        · occamy-1.0-NVFP4 · off      · on:read_file · manifest+row     
rows-longrun-v5-tools.jsonl                     · pointer-stable  · LR-01.v4-slice-widened   · 5bf5f6393946   · unknown        · occamy-1.0-NVFP4 · off      · on:read_file · manifest+row     
rows-longrun-v6-tools.jsonl                     · pointer-stable  · LR-01.v4-slice-widened   · 5bf5f6393946   · 231b0ae11477   · occamy-1.0-NVFP4 · off      · on:read_file · cell+manifest+row
rows-pilot-thinking-2026-10-26.jsonl            · transcript-grow · LR-01                    · b7e303a65f20   · unknown        · occamy-1.0-NVFP4 · mixed    · off          · manifest+row     
```

### What it cost, honestly

```
RETROFIT COST (14 files declared, 14 present)
  full provenance   : 1
  partial           : 13
  'unknown' only    : 0
  missing harness_sha256  : 13/14 files
  missing arm             : 9/14 files
  missing thinking        : 6/14 files
  missing fixture_sha256  : 4/14 files
  missing max_tokens      : 4/14 files
  missing endpoint        : 3/14 files
  missing fixture_id      : 3/14 files
  missing model           : 3/14 files
  missing tools_mode      : 3/14 files
```

* **1 of 14 files** get **full** nine-field provenance
  (`rows-longrun-v6-tools.jsonl`) — and it takes all three rungs at once: the row, its
  manifest, and a cell report for the harness digest.
* **13 of 14** are **partial**: at least one field is
  `"unknown"` while the rest resolve.
* **0** resolve to `"unknown"` only — no file is entirely dark, because
  every one of the fourteen carries *something* readable.
* The field that is missing most often is **`harness_sha256` — 13 of
  14 files.** Only two cell reports ever recorded a harness digest, and only one of
  them names a rows file that is in the ledger; the runner itself never wrote one. This is
  precisely the field `HARNESS-MAP-V2` was inferring from mtimes.
* Next: **`arm` missing on 9 files** — three of the oldest files
  (`rows-baseline-2026-10-26.jsonl`, `rows-equalinfo-2026-10-26.jsonl`,
  `rows-live-2026-10-26.jsonl`) predate the arm field and have **no manifest at all**, so their
  arm cannot be recovered from anything on disk.
* Then `thinking` (6), and a cluster of four files
  missing `fixture_sha256` (4) and `max_tokens`. The oldest
  manifests carry no `renderer.thinking` key, so the thinking switch genuinely is not on
  record for them — `run_longrun` began stamping `thinking` on rows only later.
* `rows-pilot-thinking-2026-10-26.jsonl` is the one file whose **two** matching manifests
  disagree (thinking `off` vs `on` — `manifest_candidate_values`), which is why its thinking
  is `mixed`: two pilot runs were written into one rows file. No tie-break may be allowed to
  pick one of them.

## 4. `same_provenance` — the comparison that refuses

```python
same_provenance(cell_a, cell_b) -> (bool, [differing_fields])
```

Comparing only the **load-bearing set** `{fixture_sha256, model, thinking, tools_mode}`:

| case | result |
|---|---|
| identical load-bearing provenance | `(True, [])` |
| fixture sha differs | `(False, ["fixture_sha256"])` |
| differ only in `arm` | `(True, [])` — the arm **is** the comparison, not a confounder |
| `thinking` `"off"` vs `"auto"` | `(False, ["thinking"])` |
| tools on vs off | `(False, ["tools_mode"])` |
| either side `"unknown"` (or a file-level `"mixed"`) | `(False, [...])` — two unknowns are not evidence of agreement, and an unknown may not be asserted equal to a known value |

It is defined once, in `client.py:896`, and re-exported by the tool (`tools/row_provenance.py:78`)
so the writer and the tool can never disagree about what "same provenance" means.

**Not wired into `analyze_stats.py`** — another card owns that file. Making the analyser call
`same_provenance` before it pools two cells is the next step; this unit exposes the function
and stops there.

## 5. What the retrofit can now PROVE

20 pairs of files disagree on a load-bearing field with BOTH sides resolved — a proven difference, not an inference:

| a | b | differing fields | same declared fixture_id |
|---|---|---|---|
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-c-2026-10-26.jsonl` | `fixture_sha256, thinking` | no |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-v3-2026-10-26.jsonl` | `fixture_sha256, thinking` | no |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-v4-2026-10-26.jsonl` | `fixture_sha256, thinking` | no |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-v4-tools-2026-10-26.jsonl` | `fixture_sha256, thinking, tools_mode` | no |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-v5-tools.jsonl` | `fixture_sha256, thinking, tools_mode` | no |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | `rows-longrun-v6-tools.jsonl` | `fixture_sha256, thinking, tools_mode` | no |
| `rows-longrun-c-2026-10-26.jsonl` | `rows-longrun-v3-2026-10-26.jsonl` | `fixture_sha256` | no |
| `rows-longrun-c-2026-10-26.jsonl` | `rows-longrun-v4-2026-10-26.jsonl` | `fixture_sha256` | no |
| `rows-longrun-c-2026-10-26.jsonl` | `rows-longrun-v4-tools-2026-10-26.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-c-2026-10-26.jsonl` | `rows-longrun-v5-tools.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-c-2026-10-26.jsonl` | `rows-longrun-v6-tools.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-v3-2026-10-26.jsonl` | `rows-longrun-v4-2026-10-26.jsonl` | `fixture_sha256` | no |
| `rows-longrun-v3-2026-10-26.jsonl` | `rows-longrun-v4-tools-2026-10-26.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-v3-2026-10-26.jsonl` | `rows-longrun-v5-tools.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-v3-2026-10-26.jsonl` | `rows-longrun-v6-tools.jsonl` | `fixture_sha256, tools_mode` | no |
| `rows-longrun-v4-2026-10-26.jsonl` | `rows-longrun-v4-tools-2026-10-26.jsonl` | `fixture_sha256, tools_mode` | yes |
| `rows-longrun-v4-2026-10-26.jsonl` | `rows-longrun-v5-tools.jsonl` | `fixture_sha256, tools_mode` | yes |
| `rows-longrun-v4-2026-10-26.jsonl` | `rows-longrun-v6-tools.jsonl` | `fixture_sha256, tools_mode` | yes |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `rows-longrun-v5-tools.jsonl` | `fixture_sha256` | yes |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `rows-longrun-v6-tools.jsonl` | `fixture_sha256` | yes |

70 further pairs differ only because at least one side is `"unknown"`; those are gaps in the record, not proven differences, and they are listed in `measure/ROW-PROVENANCE.json` under `unresolved_deltas` with `"kind": "unknown-involved"`.

The three findings that change how a historical grid must be read:

1. **`rows-cell-pointer-stable-20261026T145758Z.jsonl` is not poolable with anything else.**
   It is the only live cell run with `thinking="auto"`; every other grid ran `thinking="off"`.
   Its rows differ from every other file on `thinking`, and from the tools grids on
   `tools_mode` too. Before this unit that difference was invisible on the row.
2. **A shared declared `fixture_id` does not mean a shared fixture.**
   `LR-01.v4-slice-widened` names three different fixture contents —
   `5a5f8c4be202…` (`rows-longrun-v4-…`), `a592a48ff3e5…` (`rows-longrun-v4-tools-…`) and
   `5bf5f6393946…` (`rows-longrun-v5-tools.jsonl`, and `rows-longrun-v6-tools.jsonl`). The
   v4/v4-tools pair also differs in `tools_mode`, so the v4 head-to-head was never
   like-for-like. **The sha is the comparison key; the fixture_id is not.**
3. **The v6 tools grid ran a v4 fixture.** `rows-longrun-v6-tools.jsonl` resolves to
   `LR-01.v4-slice-widened` / `5bf5f6393946…` — the same fixture bytes as
   `rows-longrun-v5-tools.jsonl`. "v6" there names the probe, not the fixture generation.

## 6. Machine-readable table

`experiments/ptr-engine/measure/ROW-PROVENANCE.json` carries, per file: the nine fields, the
per-field `sources` (which rung supplied each one), `missing_fields`, `partial_rows`,
`provenance_complete`, the matched manifest/cell, `manifest_candidates` +
`manifest_candidate_values` (how much the manifest pick mattered), `rows_sha256` (the file is
identified by content, not by mtime), the `cost` block, and every `unresolved_deltas` pair
with its `kind`.

## 7. Tests

`experiments/ptr-engine/longrun/tests/test_row_provenance.py` — 12 tests, all green:
(a) a written row carries all nine fields and the manifest publishes the same block;
(b) differing fixture sha ⇒ `(False, ["fixture_sha256"])`;
(c) differing only in `arm` ⇒ `(True, [])`;
(d) `thinking` off/auto/on ⇒ `(False, ["thinking"])`, and tools on/off ⇒ `(False, ["tools_mode"])`;
(e) a missing value is `"unknown"` + `provenance_complete: false`, never `null`, including
from a bare cfg that predates the fields; an unknown never compares equal;
(f) **red→green**: deleting the stamping line from `make_row` makes (f) fail — shown in
§"red→green" of the handoff.

No rows file, grade file, `TVS.json`, `LATENCY-REPORT.json`, `REQUEST-LEDGER.json`, `cell.py`
or anything under `longrun/tasks*/` was modified by this unit.
