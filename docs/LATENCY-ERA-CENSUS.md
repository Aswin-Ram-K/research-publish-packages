# LATENCY-ERA-CENSUS — which TTFT era produced each rows file, and each published latency figure

**Unit:** `LATENCY-ERA-CENSUS` · **Generated:** 2026-10-26 · **Live requests: 0** · **Network: none** · **Inference requests: 0**
**Posture:** read-only on every rows file, grade file, `docs/LATENCY-REPORT.md`, `measure/LATENCY-REPORT.json`, `client.py`, `run_longrun.py`. This unit adds two documents and one JSON; it edits nothing it reads.
**Machine-readable twin:** [`measure/LATENCY-ERA-CENSUS.json`](../experiments/ptr-engine/measure/LATENCY-ERA-CENSUS.json)
**Generator:** §10 below — the fenced `python3` block *is* the whole generator. Running it rewrites the twin byte-identically, which is what the verdict command does.
**This document derives no quantile.** Every p50 / p95 quoted here is copied from `measure/LATENCY-REPORT.json`; `LATENCY-UNDER-DISPUTE` owns the floor policy and `P95-POWER-FROM-ROWS` owns the power question. This unit supplies the **era label** only.

---

## 0. The sentence the brief can quote

> **0 of 12 published p50 values is measured wholly on post-client rows — all 12 sit on pre-client rows — but the wall-substitution defect the fixed client removed is measured on 0 of 186 tool-call rows and 0 of 1,101 declared rows, so H1's headline p50s are pre-fix-era numbers with no measured contamination and an unmeasured, wall-bounded inflation risk.**

Three things travel with that sentence, and none of them can be dropped without changing it:

1. **Every published latency figure in this project predates `WIRE-CLIENT`.** Not most of them — all of them, p50 and p95 alike. There is no post-fix latency number on disk to compare them against.
2. **The specific defect the fix repaired did not leave a trace in the rows.** The fixed client latches TTFT on the first delta carrying `content`, `reasoning_content` **or** `tool_calls`; the old inline latch ignored `tool_calls`. The card's stated consequence was *a tool-call turn entering the tail as full `wall_ms` latency*. That never happened here: 0 of 186 tool-call rows are null, and 0 of 186 are within 1 % of their own wall clock (the worst is 0.391 × wall, the median 0.083 × wall).
3. **What cannot be proven is weaker but real.** The pre-client rows carry no `first_token_kind`, so for a tool-call row we cannot tell whether the first delta was the tool call or the text. A `tool_calls`-first turn would have latched **late** (at the first content delta) instead of at the true first token. That inflation is bounded by the row's own wall clock — at most 0.391 × wall on the worst of the 186 rows — and it is *not measured*, because the field that would measure it did not exist yet.

---

## 1. The discriminator, stated once

### 1.1 The rule

| label | test |
|---|---|
| `post-client` | **every** row carries `ttft_source` **and** `first_token_kind` |
| `pre-client` | **no** row carries either field, and the file carries a TTFT column (`ttft_ms` or `ttft_s`) |
| `mixed` | some rows carry them and some do not |
| `undatable` | no TTFT column on any row — there is no TTFT measurement to date |

Applied per rows file, on row-level field **presence with a non-null value** (not on key declaration: a key declared `None` is not provenance).

### 1.2 Why this discriminator and not a timestamp

Two independent axes agree, and the classification rests on both:

- **Field axis.** `ttft_source` / `first_token_kind` are written by `client.py` and passed through unchanged by `run_longrun.make_row` (`run_longrun.py:1592-1601`). The committed runner has no such field: `git show HEAD:experiments/ptr-engine/longrun/run_longrun.py` carries the inline latch at **:1077** (`if (piece_c or piece_r) and ttft is None: ttft = time.perf_counter() - t0`) and writes only `ttft_s` / `ttft_ms` at :1126-1127. The field cannot exist in a row written by that code.
- **Time axis.** `WIRE-CLIENT` landed at **2026-10-26T14:53:28Z** (handoff write). Exactly **one** rows file on disk postdates it: `rows-cell-pointer-stable-20261026T145758Z.jsonl`, last written 15:17:04Z. That is the same file the field axis selects. The two axes name the same file, and no file is selected by one and not the other.

### 1.3 The trap this discriminator avoids

`cached_source` **is not** a seam field. `rows-live-2026-10-26.jsonl` carries it on **25 of 27** rows — with an entirely different vocabulary (`'absent'`, `'usage.prompt_tokens_details'`, `'metrics.prompt_tokens_cached_total'`) and no `ttft_source`, no `ttft_ms`, and a legacy schema (`ttft_server_s`, `client_elapsed_s`, one-second `ts_utc`). A `cached_source`-based discriminator would have labelled that file post-client on 25 rows and been wrong. The card lists `cached_source` beside the other two; it is the one that does not discriminate.

### 1.4 What I could not classify, and why

**`experiments/ptr-engine/measure/rows.jsonl` (49 rows)** — `undatable` in the strongest sense: no timing column of any kind, no `kind`, no `arm`, no `run_id`, no `fixture_sha256`. It is the **2026-10-25 calibration / nonce corpus** (`cell`, `nonce`, `phase`, `prompt_tokens`), not a latency rows file, and it is **not** one of the 14 files `LATENCY-REPORT.md` §8.1 declares. Every figure in this document is computed over the **14 declared files and their 1,101 rows**; this file's 49 rows are censused and reported separately as out of scope.

The three legacy files (`rows-baseline` 105, `rows-equalinfo` 100, `rows-live` 27 = **232 rows**) are `undatable` **as TTFT sources** because none carries a TTFT column — but they are not mysterious: all three were written before the seam (`written_before_seam: true` in the JSON, mtimes 05:30–06:07Z). Their era is moot because they contribute **0 rows** to every latency figure in the report. `LATENCY-REPORT.md` §8.2 already excludes them from every cell.

---

## 2. Per rows file: era, field presence, sha256

`ttft_src / ftk` = rows carrying `ttft_source` / `first_token_kind`; `cached_src` = rows carrying the legacy-or-seam `cached_source`; `ttft_ms` = rows with a **non-null** `ttft_ms`; `tc` = rows with a non-empty `tool_calls`; `fu` = rows with `kind == "tool-followup"`.
`wall_ms` is carried on **6** rows in the whole corpus — all six in the one post-client file; every other row's wall clock is `round(latency_s*1000, 3)`, which §5 validates.

| rows file | rows | era | ttft_src / ftk | cached_src | ttft_ms | tc | fu | sha256 |
|---|---:|---|---:|---:|---:|---:|---:|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | **undatable** (no TTFT column) | 0 / 0 | 0 | 0 | 0 | 0 | `638c84942e3bcdba4b416cceda9214f3fdcc99c42171639bf5c52736f40e032d` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | **post-client** | **6 / 6** | 5 | 6 | 0 | 0 | `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800` |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | **undatable** (no TTFT column) | 0 / 0 | 0 | 0 | 0 | 0 | `c01c7b4a477fe24bc55370ceddf26d885a1fe827e7135023cdde48b271e8c934` |
| `rows-live-2026-10-26.jsonl` | 27 | **undatable** (no TTFT column) | 0 / 0 | 25 | 0 | 0 | 0 | `3d02b4d473304f0012b34024cc517c70d7f23b60de1103c1ca1b93a7e2752e5b` |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | pre-client | 0 / 0 | 0 | 29 | 0 | 0 | `9d4ad90ce34cb781c04e9f73fba50ffb47d5b35d6d1491389d22a49044516405` |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | pre-client | 0 / 0 | 0 | 40 | 0 | 0 | `9b1097234bf8d2464a4d24ec48cf0cccc1ecd64bd853815fc6643b1ad3da3368` |
| `rows-longrun-2026-10-26.jsonl` | 192 | pre-client | 0 / 0 | 0 | **0** | 0 | 0 | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | pre-client | 0 / 0 | 0 | 192 | 0 | 0 | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | pre-client | 0 / 0 | 0 | 96 | 0 | 0 | `80d85fe0e977af164a5ffeca8b2f95350c6614d2112455c3ace93765530ff921` |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | pre-client | 0 / 0 | 0 | 96 | 0 | 0 | `999f298dac8b83569c4059946e7789b76ec485b24a5c9a39d6c1616f0501c28e` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | pre-client | 0 / 0 | 0 | 68 | **51** | **20** | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` |
| `rows-longrun-v5-tools.jsonl` | 72 | pre-client | 0 / 0 | 0 | 72 | **68** | **24** | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| `rows-longrun-v6-tools.jsonl` | 72 | pre-client | 0 / 0 | 0 | 72 | **67** | **24** | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | pre-client | 0 / 0 | 0 | 6 | 0 | 0 | `6b81a6281ce0b266f45ab1b95fc3834e446bea5708e5466988b28e133a0e9e10` |
| `rows.jsonl` *(not declared)* | 49 | **undatable** (calibration corpus) | 0 / 0 | 0 | 0 | 0 | 0 | `29119ecd5e5c3beefcd3e91830cef148861eac6aeecbc6dd7d1ba8bc4fb8de7a` |

**Totals, 14 declared files / 1,101 rows:** 1 post-client file (**6 rows**) · 10 pre-client files (**863 rows**) · 3 undatable-no-TTFT files (**232 rows**) · 0 mixed · 0 unclassifiable-but-declared.
**Provenance check:** all **14** computed sha256 values equal the digests `LATENCY-REPORT.md` §8.1 publishes (`sha256_all_match_latency_report: true`). Nothing in `measure/` was modified — the digests prove it, not my assertion.

`rows-longrun-2026-10-26.jsonl` is `pre-client` **and additionally** carries **0 non-null `ttft_ms`** (its 93 `ttft_s` values were never converted — see `LATENCY-REPORT.md` §2/G1). Era and usability are different questions: that file's era is knowable, its TTFT is simply absent.

---

## 3. The exposed share — the rows the old latch could have mistimed

Two counts, because the card names one rule in two strengths and they do not agree:

- **row level** — a row whose `tool_calls` is non-empty. This is the row that carries the tool-call payload.
- **run level** — the card's literal rule: **every** row of a run that contains a `kind == "tool-followup"` row (`run_id` grouping).

| rows file | era | rows | tc rows (row level) | exposed rows (run level) | share (row / run) | ttft present on tc rows | tc rows ≈ wall |
|---|---|---:|---:|---:|---|---:|---:|
| `rows-longrun-v4-tools-2026-10-26.jsonl` | pre-client | 68 | 51 | **68** | 75.0 % / 100 % | 51 / 51 | **0** |
| `rows-longrun-v5-tools.jsonl` | pre-client | 72 | 68 | **72** | 94.4 % / 100 % | 68 / 68 | **0** |
| `rows-longrun-v6-tools.jsonl` | pre-client | 72 | 67 | **72** | 93.1 % / 100 % | 67 / 67 | **0** |
| other 11 declared files | pre-client / post / undatable | 889 | **0** | **0** | 0 % / 0 % | — | **0** |
| **total, 14 declared / 1,101 rows** | | 1,101 | **186 (16.89 %)** | **212 (19.26 %)** | | **186 / 186** | **0** |

Read the two columns as a range and quote the one you mean. The row-level set is **186 of 1,101 rows (16.89 %)**; the card's run-level rule makes it **212 of 1,101 (19.26 %)**. The difference is 26 rows that are neither tool-call rows nor follow-ups but sit inside a run that called a tool. Because all 68 follow-up rows also carry `tool_calls`, the row-level set is exactly the `tool_calls` set — no follow-up row escapes it.

**All 212 exposed rows are in three files, all pre-client, all tools-ON.** The other 11 declared files contain no `tool_calls` and no follow-up row at all, so the old latch's blind spot is **structurally unreachable** in them: there is no delta order that could have diverged.

---

## 4. Which published numbers are era-contaminated

Twelve cells carry a published p50; three carry a p95 (one withdrawn). All fifteen rows below copy their numbers from `measure/LATENCY-REPORT.json` unchanged — this table adds an era column, nothing else.

`era_label` per cell: `era-clean` = every row post-client · `era-pre` = every row pre-client · `era-mixed` = both within the cell · `undatable`. I add `era-pre` because the card's three labels have no name for "wholly pre-client", which is the state of **every** published cell; mapped onto the card's vocabulary all 12 are `era-mixed` (`card_vocabulary_label`), and none is mixed *within* itself.

| grid | arm | rows file | era | p50 ms | n | exposed rows | ≈ wall | era label |
|---|---|---|---:|---:|---:|---:|---:|---|
| G2 `smoke-rp` | `transcript-grow` | `rows-longrun-2026-10-26-policy.jsonl` | pre-client | 8800.748 | 31 | **0** | 0 | `era-pre` |
| G4 `RUN-C-V2` | `lease-reopen` | `rows-longrun-c-2026-10-26.jsonl` | pre-client | 134.9635 | 48 | **0** | 0 | `era-pre` |
| G4 `RUN-C-V2` | `pointer-stable` | `rows-longrun-c-2026-10-26.jsonl` | pre-client | 167.0200 | 48 | **0** | 0 | `era-pre` |
| G4 `RUN-C-V2` | `transcript-compact` | `rows-longrun-c-2026-10-26.jsonl` | pre-client | 202.4945 | 48 | **0** | 0 | `era-pre` |
| G4 `RUN-C-V2` | `transcript-grow` | `rows-longrun-c-2026-10-26.jsonl` | pre-client | 482.2425 | 48 | **0** | 0 | `era-pre` |
| G5 `V3` | `pointer-stable` | `rows-longrun-v3-2026-10-26.jsonl` | pre-client | 167.4930 | 48 | **0** | 0 | `era-pre` |
| G5 `V3` | `transcript-grow` | `rows-longrun-v3-2026-10-26.jsonl` | pre-client | 200.6530 | 48 | **0** | 0 | `era-pre` |
| G6 `V4` | `pointer-stable` | `rows-longrun-v4-2026-10-26.jsonl` | pre-client | 187.8980 | 48 | **0** | 0 | `era-pre` |
| G6 `V4` | `transcript-grow` | `rows-longrun-v4-2026-10-26.jsonl` | pre-client | 199.7940 | 48 | **0** | 0 | `era-pre` |
| G7 `V4-TOOLS` | `pointer-stable` | `rows-longrun-v4-tools-2026-10-26.jsonl` | pre-client | 198.7230 | 51 | **51 (100 %)** | 0 | `era-pre` |
| G8 `V5-TOOLS` | `pointer-stable` | `rows-longrun-v5-tools.jsonl` | pre-client | 143.9145 | 70 | **68 (94.4 %)** | 0 | `era-pre` |
| G9 `V6-TOOLS` | `pointer-stable` | `rows-longrun-v6-tools.jsonl` | pre-client | 147.5850 | 61 | **67 (93.1 %)** | 0 | `era-pre` |

**The p95s.** `G8` `397.411 [273.84, 659.70] n=70` — **published**, pre-client, 68 exposed rows, 0 ≈ wall. `G9` `429.696 [318.80, 477.06] n=61` — **published**, pre-client, 67 exposed rows, 0 ≈ wall. `G7` `318.14 [235.00, 526.41] n=68` — **withdrawn** (`LATENCY-UNDER-DISPUTE`'s floor policy, not this unit), pre-client, 51 exposed rows, 0 ≈ wall. All three p95s are pre-client, so the era label does **not** discriminate between the withdrawn one and the surviving two; the withdrawal stands on its own floor argument and nothing here revives or further damages it.

**The count the card asks for.** Of the 12 published p50 values:
- **0** are `era-clean` (no cell anywhere is measured wholly on post-client rows);
- **9** are era-inert in the strongest sense — their files carry **0** rows the old latch could touch, so the fix could not have moved them by any mechanism;
- **3** (G7, G8, G9) sit entirely inside the exposed set — every one of their rows is in a run that called a tool — so their era cannot be cleared by structure;
- **0** are `undatable` (every p50 cell's file carries a knowable era);
- and the **measured** wall-substitution count across all 15 figures is **0**.

That is why the honest one-line answer is neither "all of them predate the fix" nor "none of them is affected": **all fifteen predate the fix; nine are provably unaffected by the defect class the fix addressed; three are affected-in-principle but the measured signature is absent; none is contaminated by the mechanism the brief names.**

---

## 5. The empirical cross-check — the `ttft ≈ wall` signature, both eras

The card asks for counts both ways. The wall clock for a row is `wall_ms` when the row carries it and `round(latency_s*1000, 3)` otherwise — the exact expression `client.collect_stream()` uses to fill `wall_ms`. The proxy is **validated, not assumed**: on the one file carrying both, **6 of 6** rows satisfy `wall_ms == round(latency_s*1000, 3)` to within 0.01 ms. "≈ wall" = `|ttft_ms − wall| ≤ max(1 ms, 0.1 % of wall)`.

| era | tool-call rows | `ttft_ms` present | `ttft_ms` null | **≈ wall** | ttft/wall min · p50 · p95 · max |
|---|---:|---:|---:|---:|---|
| **pre-client** | **186** | 186 | **0** | **0** | 0.00122 · 0.08291 · 0.22169 · **0.39053** |
| **post-client** | **0** | — | — | — | not observable (file carries 6 `turn` rows, 0 tool-call rows) |
| all 1,101 declared rows, any kind | 186 | 186 | 0 | **0** | — |

**What this establishes.** No row anywhere in the corpus — tool-call or not — was timed as its own wall clock: **0 of 1,101**. No tool-call row was silently dropped either: **186 of 186 carry a `ttft_ms`**, so the old latch never failed to fire on a tools-ON row. Both failure modes the card names ("entered the tail as full latency", or a turn that "recorded no TTFT at all" per the `WIRE-CLIENT` comment) are absent from the measured corpus.

**What it does not establish, and why the post-client column is empty.** The fixed latch's tool-call path has **never written a row that any published cell used**: the only post-client file is a 6-row, tools-OFF probe. So the fix is proven by its own test suite, not by a row: `python3 -m pytest experiments/ptr-engine/longrun/tests/test_client_ttft.py -q` → **8 passed**, asserting `first_token_kind == "tool_call"` with `ttft_source == "first_delta"` (`experiments/ptr-engine/longrun/tests/test_client_ttft.py:226-227`) and an unavailable TTFT staying null (`:265-266`). That is code-level evidence, and it is labelled as such — it is **not** a measurement on rows.

**The residual, honestly bounded.** Delta order is not recoverable for a pre-client row (no `first_token_kind`). A `tool_calls`-first delta followed by content would have latched the old runner **late** — not at wall, but at the first content token. The size of that error is bounded by the row's own clock: at most **0.391 × wall** on the worst of the 186 rows, **0.083 × wall** at the median, and **0 of 186** exceed half of wall. So the maximum conceivable inflation on the worst published cell is bounded well below the between-arm gaps the report is built on — but it is a bound, not a measurement, and it should be quoted as one.

---

## 6. Three corrections to the brief as written

1. **The old latch did not fall back to `wall_ms`.** The committed runner (`git show HEAD:...run_longrun.py`, latch at **:1077**) computes `ttft_s` only on a non-empty `piece_c or piece_r` and otherwise leaves it **`None`**; `ttft_ms` is `round(ttft*1000, 3) if ttft is not None else None` (:1127). Both pre-edit snapshots under `experiments/ptr-engine/longrun/manifests/` carry the same shape (`v6-run-longrun-pre-edit.py:874`, `v4tools2-baseline-pre.py:762`). No version on disk or in `git HEAD` assigns latency to a `ttft` variable. **The failure mode was silent deletion from every quantile** (`analyze_stats.ttft_values` drops nulls), **not a wall-inflated tail** — and the measured corpus shows neither.
2. **`analyze_stats.py:470` warns about a wall-clock fallback that no row is in.** `ttft_source == "unavailable"` is never paired with a number on disk: `ttft_dropped_unavailable` is **0** in all 24 cells of `measure/LATENCY-REPORT.json`, and the post-client file's 6 rows are all `first_delta`.
3. **`cached_source` does not discriminate era** (§1.3). It is present on 25 legacy rows that carry no seam field at all.

None of these changes a published number. They change *what the numbers are worth*: the defect class is real in the code history, and its feared signature is measurably absent from the corpus — which is a different, and more useful, statement than "the numbers predate the fix".

---

## 7. What this licenses, and what it does not

| consumer | what this document gives it | what it still does not have |
|---|---|---|
| `OPERATOR-BRIEF-3` | the one sentence in §0, plus the per-cell era column: **all 15 published figures are pre-fix-era**, 9 of 12 p50s are provably defect-inert, 3 are exposed-in-principle with the signature measured absent | a single post-fix latency figure. Nothing measured after `WIRE-CLIENT` enters any published cell. |
| `LATENCY-UNDER-DISPUTE` (owns the floor policy) | an era column that is independent of the floor argument: G7's withdrawal and G8/G9's survival are **not** era-driven, so the era label neither revives G7 nor undermines G8/G9 | any change to the floor, the de-duplication rule, or a recomputed p50 — none is produced here |
| `P95-POWER-FROM-ROWS` (owns the power question) | the era of every p95 cell and the fact that the three p95 cells are also the only three with any exposure at all | the power question itself; this unit computes no interval |
| H1's thesis | the honest denominator for "is the latency evidence post-fix?" — **0 of 15 figures** | an arm-versus-arm latency comparison; that is still unproduced |

**The one thing a reader must not conclude:** that the p50s are wrong. They are era-labelled, not discredited. What is missing is not correctness but **provenance against the current client** — no published cell was measured with the code that ships now.

---

## 8. Pinned provenance and limits

**`run_longrun.py` was rewritten twice while this unit read it** (live ownership: `TURN-ROW-ATTRIBUTION`). The pin is therefore a **sequence**, recorded rather than resolved — and the era boundary in §1.2 does not depend on any of these bytes:

| file | observation | sha256 | bytes |
|---|---|---|---:|
| `experiments/ptr-engine/longrun/run_longrun.py` | first read (unit start) | `939c225c052319b91ef7df0e69678b85ae855fc9bb3fbf293441b7bafb99b1c3` | 133,065 |
| `experiments/ptr-engine/longrun/run_longrun.py` | at the first JSON write | `fff28df4860f16e5a4784abb4f77f8e79de757be7d46e9fe495e7b2a6120fa49` | 143,844 |
| `experiments/ptr-engine/longrun/run_longrun.py` | at the regeneration check | `32f8680e89d779463ba85c728b0a1075ba5be2626373af5255be1d5941d8511c` | 145,581 |
| `experiments/ptr-engine/longrun/client.py` | first read, unchanged through the regeneration check | `5aa23bb5470b7e0909992b3f0947867953ba39204e5d03eff0f95c30e57ca7bb` | 41,593 |

`client.py` is untracked (created by `WIRE-CLIENT`); `run_longrun.py` is modified vs `HEAD`, whose **committed copy is immutable** and still carries the inline latch at `:1077`. That committed copy — not any working-tree digest — is what the era boundary rests on, which is why the churn above changes no classification. The JSON stores these same observations as static constants: a live digest would make the twin non-deterministic and would describe a moving object.

**Limits, stated rather than papered over:**

- **The client revision that wrote the 6 post-client rows is not recoverable by digest.** `client.py`'s inode birth is 2026-10-26T16:13:55Z, *after* the rows file's last write at 15:17:04Z; the file was recreated by a later unit. The rows carry the seam fields, which proves seam v1 was live; they do not pin a sha.
- **Era is a property of the writer, and the writer is inferred.** Field presence and write time are two independent inferences that agree on one file; neither is a log line naming a commit. The classification is as strong as those two axes and no stronger.
- **`pre-client` does not mean "the same code"** — the 10 pre-client files span several runner growth steps (`LATENCY-REPORT.md` §2 records `pre-guard inline latch`, `old inline latch`, `pre-guard`, and a mid-cell version mix in G9). Within the era, the latch itself is the same code shape in every snapshot: `(piece_c or piece_r) and ttft is None`.
- **No inference request, no network call, no write** outside `docs/LATENCY-ERA-CENSUS.md`, `experiments/ptr-engine/measure/LATENCY-ERA-CENSUS.json`, `orchestration/units/LATENCY-ERA-CENSUS.md`, `orchestration/handoffs/LATENCY-ERA-CENSUS.json`, `orchestration/journals/LATENCY-ERA-CENSUS.jsonl`.

---

## 9. Reproduction

The generator is the `python3` fence in §10. It reads the corpus and rewrites the JSON twin; it is deterministic (no clock, no environment, no ordering nondeterminism: files sorted, dicts built in a fixed order).

```sh
cd "/home/zer0null/reserach extarctor" && python3 -c "import re;s=open('docs/LATENCY-ERA-CENSUS.md',encoding='utf-8').read();m=re.search(r'\`\`\`python\n(.*?)\n\`\`\`',s,re.S);open('/tmp/latency_era_census.py','w',encoding='utf-8').write(m.group(1))" && python3 /tmp/latency_era_census.py --out /tmp/census.json && diff -u /tmp/census.json experiments/ptr-engine/measure/LATENCY-ERA-CENSUS.json && echo REGEN-IDENTICAL
```

---

## 10. The generator (this fence is the unit's entire computation)

```python
#!/usr/bin/env python3
"""LATENCY-ERA-CENSUS generator. OFFLINE. Reads only; writes the measure/ JSON twin.

Discriminator (stated once, applied everywhere):
  A rows file is POST-CLIENT iff every row carries the WIRE-CLIENT seam v1 provenance
  fields ``ttft_source`` AND ``first_token_kind`` (present, not merely declared);
  PRE-CLIENT iff no row carries them; MIXED iff some do and some do not;
  UNDATABLE iff no row carries a TTFT column at all (nothing to date).

Exposure (the rows the old inline latch COULD have mistimed):
  a row whose ``tool_calls`` is non-empty (row level), and -- the card's literal
  "same run" rule -- every row of a run that contains a ``kind == "tool-followup"`` row
  (run level). Both are reported; neither is substituted for the other.

Realised signature (what the latch ACTUALLY did):
  |ttft_ms - wall| <= max(1 ms, 0.1 % of wall) with wall = latency_s * 1000.
  Pre-client files carry no ``wall_ms`` key, so latency_s*1000 is the wall proxy;
  it is validated against ``wall_ms`` on the one file that carries both.
"""
import argparse
import hashlib
import json
import os
import sys

MEASURE = "experiments/ptr-engine/measure"
REPORT = os.path.join(MEASURE, "LATENCY-REPORT.json")
LONGRUN = "experiments/ptr-engine/longrun"
OWNED = ["run_longrun.py", "client.py"]
SEAM_FIELDS = ("ttft_source", "first_token_kind")
ERA_BOUNDARY_UTC = "2026-10-26T14:53:28Z"
TOL_ABS = 1.0
TOL_REL = 0.001


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def wall_ms(row):
    """The wall clock for a row, in ms, as the row itself records it.

    ``wall_ms`` when present (client era); otherwise round(latency_s*1000, 3) -- the
    exact expression client.collect_stream() uses to fill ``wall_ms``.
    """
    w = row.get("wall_ms")
    if isinstance(w, (int, float)):
        return float(w)
    l = row.get("latency_s")
    if isinstance(l, (int, float)):
        return round(float(l) * 1000.0, 3)
    return None


def near_wall(ttft, wall):
    if ttft is None or wall is None:
        return False
    return abs(float(ttft) - float(wall)) <= max(TOL_ABS, TOL_REL * abs(float(wall)))


def classify(rows):
    with_src = sum(1 for r in rows if r.get("ttft_source") is not None)
    with_kind = sum(1 for r in rows if r.get("first_token_kind") is not None)
    has_ttft_col = any(("ttft_ms" in r) or ("ttft_s" in r) for r in rows)
    n = len(rows)
    if n == 0:
        return "undatable", "empty file", with_src, with_kind
    if with_src == n and with_kind == n:
        return ("post-client", "every row carries ttft_source and first_token_kind",
                with_src, with_kind)
    if with_src == 0 and with_kind == 0 and has_ttft_col:
        return ("pre-client", "no row carries ttft_source or first_token_kind",
                with_src, with_kind)
    if 0 < with_src < n or 0 < with_kind < n:
        return ("mixed", "some rows carry the seam fields and some do not",
                with_src, with_kind)
    return ("undatable", "no TTFT column on any row: nothing to date", with_src, with_kind)


def file_census(path, rel, declared, report_sha):
    rows = read_rows(path)
    era, basis, with_src, with_kind = classify(rows)
    digest = sha256_file(path)

    runs = {}
    for r in rows:
        runs.setdefault(r.get("run_id", "__no_run_id__"), []).append(r)
    followup_rids = {rid for rid, rs in runs.items()
                     if any(r.get("kind") == "tool-followup" for r in rs)}

    tc_rows = [r for r in rows if r.get("tool_calls")]
    fu_rows = [r for r in rows if r.get("kind") == "tool-followup"]
    runlevel = [r for r in rows if r.get("run_id", "__no_run_id__") in followup_rids]

    def sig(subset):
        nn = [r for r in subset if r.get("ttft_ms") is not None]
        eq = sum(1 for r in nn if near_wall(r.get("ttft_ms"), wall_ms(r)))
        ratios = [float(r["ttft_ms"]) / wall_ms(r)
                  for r in nn if wall_ms(r)]
        return {
            "rows": len(subset),
            "ttft_present": len(nn),
            "ttft_null": len(subset) - len(nn),
            "ttft_eq_wall": eq,
            "ttft_gt_wall": sum(1 for r in nn if wall_ms(r) and float(r["ttft_ms"]) > wall_ms(r)),
            "ratio_min": round(min(ratios), 6) if ratios else None,
            "ratio_max": round(max(ratios), 6) if ratios else None,
            "_ratios": ratios,
        }

    both_cols = [r for r in rows if "wall_ms" in r and isinstance(r.get("latency_s"), (int, float))]
    proxy_ok = sum(1 for r in both_cols
                   if abs(float(r["wall_ms"]) - round(float(r["latency_s"]) * 1000.0, 3)) <= 0.01)

    mtime = os.path.getmtime(path)
    import datetime
    mtime_utc = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
    mtime_iso = mtime_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    boundary = datetime.datetime.strptime(ERA_BOUNDARY_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)
    published = (report_sha or {}).get(os.path.basename(rel))

    return {
        "path": rel,
        "sha256": digest,
        "sha256_matches_latency_report": (None if published is None else published == digest),
        "declared_in_latency_report": os.path.basename(rel) in declared,
        "bytes": os.path.getsize(path),
        "rows": len(rows),
        "mtime_utc": mtime_iso,
        "written_before_seam": bool(mtime_utc < boundary),
        "era": era,
        "era_basis": basis,
        "field_presence": {
            "ttft_source": with_src,
            "first_token_kind": with_kind,
            "cached_source": sum(1 for r in rows if r.get("cached_source") is not None),
            "ttft_ms": sum(1 for r in rows if r.get("ttft_ms") is not None),
            "ttft_s": sum(1 for r in rows if r.get("ttft_s") is not None),
            "latency_s": sum(1 for r in rows if r.get("latency_s") is not None),
            "wall_ms": sum(1 for r in rows if r.get("wall_ms") is not None),
            "tool_calls": len(tc_rows),
            "kind_tool_followup": len(fu_rows),
            "run_id": sum(1 for r in rows if r.get("run_id") is not None),
        },
        "exposure": {
            "rowlevel_tool_calls": sig(tc_rows),
            "runlevel_has_followup": sig(runlevel),
            "rowlevel_rows": len(tc_rows),
            "runlevel_rows": len(runlevel),
        },
        "all_rows_ttft_eq_wall": sig(rows)["ttft_eq_wall"],
        "wall_proxy_validated_rows": proxy_ok if both_cols else None,
        "wall_proxy_rows_checked": len(both_cols) if both_cols else None,
        "ttft_present_total": sum(1 for r in rows if r.get("ttft_ms") is not None),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(MEASURE, "LATENCY-ERA-CENSUS.json"))
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    names = sorted(f for f in os.listdir(MEASURE) if f.endswith(".jsonl"))
    report = json.load(open(REPORT, encoding="utf-8"))
    declared = set((report.get("row_files") or {}).get("files") or {})
    report_sha = (report.get("row_files") or {}).get("sha256") or {}
    files = [file_census(os.path.join(MEASURE, n), os.path.join(MEASURE, n),
                         declared, report_sha) for n in names]
    by_path = {f["path"]: f for f in files}

    cells = []
    for g in report["grids"]:
        rf = os.path.join(MEASURE, g["rows_file"])
        fc = by_path.get(rf)
        for c in g["arm_cells"]:
            p50 = c.get("p50") or {}
            p95 = c.get("p95") or {}
            if p50.get("point") is None and p95.get("point") is None:
                continue
            era = fc["era"] if fc else "undatable"
            cells.append({
                "grid_id": g["grid_id"],
                "label": g["label"],
                "arm": c["arm"],
                "rows_file": rf,
                "rows_file_era": era,
                "rows_file_sha256": fc["sha256"] if fc else None,
                "harness_label_in_report": g.get("harness"),
                "tools": g["tools"],
                "n_published": p50.get("n") if p50.get("point") is not None else p95.get("n"),
                "p50_ms": p50.get("point"),
                "p50_ci": [p50.get("lo"), p50.get("hi")] if p50.get("point") is not None else None,
                "p95_ms": p95.get("point"),
                "p95_status": ("published" if p95.get("point") is not None
                               else ("withdrawn" if g["grid_id"] == "G7" else "not published")),
                "era_label": ("era-clean" if era == "post-client"
                              else "era-pre" if era == "pre-client"
                              else "era-mixed" if era == "mixed"
                              else "undatable"),
                "card_vocabulary_label": ("era-clean" if era == "post-client"
                                          else "undatable" if era == "undatable"
                                          else "era-mixed"),
                "exposed_rows_runlevel": fc["exposure"]["runlevel_rows"] if fc else 0,
                "exposed_rows_rowlevel": fc["exposure"]["rowlevel_rows"] if fc else 0,
                "exposed_share_of_rows_file": (round(fc["exposure"]["rowlevel_rows"] / fc["rows"], 6)
                                               if fc and fc["rows"] else None),
                "exposed_share_runlevel_of_rows_file": (round(fc["exposure"]["runlevel_rows"] / fc["rows"], 6)
                                                        if fc and fc["rows"] else None),
                "realised_wall_signature_rows": (fc["exposure"]["rowlevel_tool_calls"]["ttft_eq_wall"]
                                                 if fc else 0),
                "exposure_kind": ("none: 0 rows of this file carry tool_calls"
                                  if not fc or fc["exposure"]["rowlevel_rows"] == 0 else
                                  "unprovable-by-field: pre-client rows carry no "
                                  "first_token_kind, so delta order is not recoverable"),
                "exposure_residual_bound_ttft_over_wall_max": (
                    fc["exposure"]["rowlevel_tool_calls"]["ratio_max"]
                    if fc and fc["exposure"]["rowlevel_rows"] else None),
            })

    totals = {
        "rows_files_censused": len(files),
        "rows_total": sum(f["rows"] for f in files),
        "files_post_client": sum(1 for f in files if f["era"] == "post-client"),
        "files_pre_client": sum(1 for f in files if f["era"] == "pre-client"),
        "files_mixed": sum(1 for f in files if f["era"] == "mixed"),
        "files_undatable": sum(1 for f in files if f["era"] == "undatable"),
        "rows_post_client": sum(f["rows"] for f in files if f["era"] == "post-client"),
        "rows_pre_client": sum(f["rows"] for f in files if f["era"] == "pre-client"),
        "rows_undatable": sum(f["rows"] for f in files if f["era"] == "undatable"),
        "toolcalls_rows_total": sum(f["field_presence"]["tool_calls"] for f in files),
        "tool_followup_rows_total": sum(f["field_presence"]["kind_tool_followup"] for f in files),
        "tool_calls_rows_pre_client": sum(f["exposure"]["rowlevel_rows"] for f in files
                                          if f["era"] == "pre-client"),
        "runlevel_exposed_rows_pre_client": sum(f["exposure"]["runlevel_rows"] for f in files
                                                if f["era"] == "pre-client"),
        "realised_wall_signature_rows_total": sum(f["exposure"]["rowlevel_tool_calls"]["ttft_eq_wall"]
                                                  for f in files),
        "toolcall_rows_ttft_present_total": sum(f["exposure"]["rowlevel_tool_calls"]["ttft_present"]
                                                for f in files),
        "toolcall_rows_ttft_null_total": sum(f["exposure"]["rowlevel_tool_calls"]["ttft_null"]
                                             for f in files),
        "any_rows_ttft_eq_wall_total": sum(f["all_rows_ttft_eq_wall"] for f in files),
        "cells_with_published_p50": sum(1 for c in cells if c["p50_ms"] is not None),
        "cells_with_p95_in_census": sum(1 for c in cells if c["p95_ms"] is not None),
        "cells_era_clean": sum(1 for c in cells if c["era_label"] == "era-clean"),
        "cells_era_pre": sum(1 for c in cells if c["era_label"] == "era-pre"),
        "cells_era_mixed_within_cell": sum(1 for c in cells if c["era_label"] == "era-mixed"),
        "cells_undatable": sum(1 for c in cells if c["era_label"] == "undatable"),
        "cells_card_vocabulary_era_mixed": sum(1 for c in cells
                                              if c["card_vocabulary_label"] == "era-mixed"),
        "cells_with_zero_possible_exposure": sum(1 for c in cells if c["exposed_rows_rowlevel"] == 0),
        "cells_with_realised_wall_signature": sum(1 for c in cells
                                                  if c["realised_wall_signature_rows"] > 0),
    }
    totals["toolcall_share_of_all_rows"] = round(
        totals["toolcalls_rows_total"] / totals["rows_total"], 6)
    totals["runlevel_exposed_share_of_all_rows"] = round(
        totals["runlevel_exposed_rows_pre_client"] / totals["rows_total"], 6)

    # The 14 declared latency rows files (LATENCY-REPORT.md 8.1) are the corpus the
    # card's "1,101 rows" refers to; measure/rows.jsonl is censused but not one of them.
    decl = [f for f in files if f["declared_in_latency_report"]]
    undecl = [f for f in files if not f["declared_in_latency_report"]]
    totals["declared_corpus"] = {
        "files": len(decl),
        "rows": sum(f["rows"] for f in decl),
        "rows_pre_client": sum(f["rows"] for f in decl if f["era"] == "pre-client"),
        "rows_post_client": sum(f["rows"] for f in decl if f["era"] == "post-client"),
        "rows_undatable_no_ttft_column": sum(f["rows"] for f in decl if f["era"] == "undatable"),
        "toolcalls_rows": sum(f["field_presence"]["tool_calls"] for f in decl),
        "toolcalls_rows_ttft_eq_wall": sum(f["exposure"]["rowlevel_tool_calls"]["ttft_eq_wall"]
                                          for f in decl),
        "runlevel_exposed_rows": sum(f["exposure"]["runlevel_rows"] for f in decl
                                     if f["era"] == "pre-client"),
        "all_rows_ttft_eq_wall": sum(f["all_rows_ttft_eq_wall"] for f in decl),
        "sha256_all_match_latency_report": all(f["sha256_matches_latency_report"] is not False
                                               for f in decl),
    }
    c = totals["declared_corpus"]
    c["toolcall_share_of_declared_rows"] = (round(c["toolcalls_rows"] / c["rows"], 6)
                                            if c["rows"] else None)
    c["runlevel_exposed_share_of_declared_rows"] = (round(c["runlevel_exposed_rows"] / c["rows"], 6)
                                                    if c["rows"] else None)
    totals["non_declared_files"] = [
        {"path": f["path"], "rows": f["rows"], "era": f["era"],
         "why_not_a_latency_cell": f["era_basis"]} for f in undecl]

    # Static, timestamped observations. run_longrun.py is under live ownership
    # (TURN-ROW-ATTRIBUTION) and was rewritten twice while this unit read it, so a
    # live digest would make this JSON non-deterministic and would describe a moving
    # object. The sequence is the record; the byte-identical regeneration is the proof.
    owner_pins = {
        "run_longrun.py": {
            "path": os.path.join(LONGRUN, "run_longrun.py"),
            "live_ownership": "TURN-ROW-ATTRIBUTION",
            "observations": [
                {"when": "first read (unit start)", "sha256":
                 "939c225c052319b91ef7df0e69678b85ae855fc9bb3fbf293441b7bafb99b1c3",
                 "bytes": 133065},
                {"when": "at the first JSON write", "sha256":
                 "fff28df4860f16e5a4784abb4f77f8e79de757be7d46e9fe495e7b2a6120fa49",
                 "bytes": 143844},
                {"when": "at the regeneration check", "sha256":
                 "32f8680e89d779463ba85c728b0a1075ba5be2626373af5255be1d5941d8511c",
                 "bytes": 145581},
            ],
            "note": ("the file changed twice under this unit; HEAD's committed copy is "
                     "immutable and still carries the inline latch at :1077, which is what "
                     "the era boundary rests on -- not the working-tree digest"),
        },
        "client.py": {
            "path": os.path.join(LONGRUN, "client.py"),
            "live_ownership": "TURN-ROW-ATTRIBUTION",
            "observations": [
                {"when": "first read (unit start), unchanged through the regeneration check",
                 "sha256": "5aa23bb5470b7e0909992b3f0947867953ba39204e5d03eff0f95c30e57ca7bb",
                 "bytes": 41593},
            ],
        },
    }

    d = totals["declared_corpus"]
    all_ratios = []
    for f in files:
        if f["era"] != "pre-client":
            f["exposure"]["rowlevel_tool_calls"].pop("_ratios", None)
            f["exposure"]["runlevel_has_followup"].pop("_ratios", None)
            continue
        all_ratios.extend(f["exposure"]["rowlevel_tool_calls"].pop("_ratios", []) or [])
        f["exposure"]["runlevel_has_followup"].pop("_ratios", None)
    all_ratios.sort()
    n_r = len(all_ratios)
    residual = {
        "toolcall_rows_with_no_first_token_kind_field": sum(
            f["exposure"]["rowlevel_rows"] for f in files if f["era"] == "pre-client"),
        "wall_substitution_rows": d["toolcalls_rows_ttft_eq_wall"],
        "ttft_over_wall_min": round(all_ratios[0], 6) if n_r else None,
        "ttft_over_wall_p50": round(all_ratios[n_r // 2], 6) if n_r else None,
        "ttft_over_wall_p95": round(all_ratios[min(n_r - 1, int(n_r * 0.95))], 6) if n_r else None,
        "ttft_over_wall_max": round(all_ratios[-1], 6) if n_r else None,
        "rows_above_half_of_wall": sum(1 for x in all_ratios if x > 0.5),
        "rows_within_one_percent_of_wall": sum(1 for x in all_ratios if x > 0.99),
        "what_is_proven": ("wall substitution did not occur on any of the %d tool-call rows: "
                           "0 of them are null and 0 of them are within 1%% of wall"
                           % d["toolcalls_rows"]),
        "what_is_not_proven": ("that the pre-client latch fired on the SAME delta the fixed "
                               "client would have: those rows carry no first_token_kind, so a "
                               "tool_calls-first delta followed by content would have latched "
                               "late. The inflation is bounded by the row's own wall clock: the "
                               "worst tool-call row's ttft is %.3f x wall, the median %.3f x wall."
                               % (all_ratios[-1] if n_r else 0.0,
                                  all_ratios[n_r // 2] if n_r else 0.0)),
    }

    headline = {
        "cells_with_a_published_p50": totals["cells_with_published_p50"],
        "p50_cells_era_clean": totals["cells_era_clean"],
        "p50_cells_measured_on_pre_client_rows": totals["cells_era_pre"],
        "p50_cells_undatable": totals["cells_undatable"],
        "p50_cells_with_zero_possible_exposure": totals["cells_with_zero_possible_exposure"],
        "p50_cells_with_a_realised_wall_signature": totals["cells_with_realised_wall_signature"],
        "declared_rows": d["rows"],
        "toolcall_rows": d["toolcalls_rows"],
        "toolcall_rows_timed_as_wall": d["toolcalls_rows_ttft_eq_wall"],
        "runlevel_exposed_rows": d["runlevel_exposed_rows"],
        "all_declared_rows_timed_as_wall": d["all_rows_ttft_eq_wall"],
    }
    headline["quotable_sentence"] = (
        "%d of %d published p50 values is measured wholly on post-client rows -- all %d sit on "
        "pre-client rows -- but the wall-substitution defect the fixed client removed is measured "
        "on %d of %d tool-call rows and %d of %d declared rows, so H1's headline p50s are "
        "pre-fix-era numbers with no measured contamination and an unmeasured, wall-bounded "
        "inflation risk."
        % (headline["p50_cells_era_clean"], headline["cells_with_a_published_p50"],
           headline["p50_cells_measured_on_pre_client_rows"],
           headline["toolcall_rows_timed_as_wall"], headline["toolcall_rows"],
           headline["all_declared_rows_timed_as_wall"], headline["declared_rows"]))

    out = {
        "unit": "LATENCY-ERA-CENSUS",
        "live_requests": 0,
        "headline": headline,
        "inference_requests": 0,
        "scope": {
            "rows_files": "every *.jsonl under " + MEASURE,
            "note": ("14 of the 15 are the declared latency row files of LATENCY-REPORT.md 8.1; "
                     "measure/rows.jsonl is the 2026-10-25 calibration/nonce corpus, censused "
                     "separately as undatable (no timing column, no kind, no arm, no run_id)"),
        },
        "discriminator": {
            "rule": ("POST-CLIENT iff every row carries BOTH WIRE-CLIENT seam v1 fields "
                     "ttft_source and first_token_kind; PRE-CLIENT iff no row carries either; "
                     "MIXED iff some do and some do not; UNDATABLE iff no row carries a TTFT "
                     "column at all"),
            "fields": list(SEAM_FIELDS),
            "era_boundary_utc": ERA_BOUNDARY_UTC,
            "era_boundary_basis": ("orchestration/handoffs/WIRE-CLIENT.json write time; the "
                                   "committed run_longrun.py still carries the inline latch at "
                                   ":1077 and the working tree replaces it with a one-line "
                                   "delegation to client.send_chat"),
            "second_independent_axis": ("rows-file mtime vs the seam landing: only "
                                        "rows-cell-pointer-stable-20261026T145758Z.jsonl "
                                        "(2026-10-26T15:17:04Z) postdates " + ERA_BOUNDARY_UTC),
            "discriminator_trap": ("cached_source is NOT a seam field: rows-live-2026-10-26.jsonl "
                                   "carries cached_source on 25 of 27 rows with a different "
                                   "vocabulary and no ttft_source/ttft_ms (legacy schema, "
                                   "ttft_server_s + client_elapsed_s); a cached_source-only "
                                   "discriminator would misclassify it as post-client"),
        },
        "writer_pins_at_read_time": owner_pins,
        "asymmetry_reference": {
            "quality_side": "QUALITY-ERA-TABLE (50 grade files)",
            "this_card": "the latency side had no era census before this unit",
        },
        "residual_risk": residual,
        "files": files,
        "totals": totals,
        "published_cells": cells,
        "cross_check": {
            "question": "does the old latch's signature (ttft_ms == wall) appear on tool-call rows?",
            "wall_proxy": "wall = wall_ms when present, else round(latency_s*1000, 3)",
            "wall_proxy_validation": {
                "rows_checked": sum(f["wall_proxy_rows_checked"] or 0 for f in files),
                "rows_matching_wall_ms": sum(f["wall_proxy_validated_rows"] or 0 for f in files),
            },
            "pre_client_era": {
                "toolcall_rows": totals["tool_calls_rows_pre_client"],
                "ttft_present": totals["toolcall_rows_ttft_present_total"],
                "ttft_null": totals["toolcall_rows_ttft_null_total"],
                "ttft_eq_wall": totals["realised_wall_signature_rows_total"],
                "verdict": "signature ABSENT: no tool-call row was timed as wall",
            },
            "post_client_era": {
                "toolcall_rows": sum(f["exposure"]["rowlevel_rows"] for f in files
                                     if f["era"] == "post-client"),
                "ttft_eq_wall": sum(f["exposure"]["rowlevel_tool_calls"]["ttft_eq_wall"]
                                    for f in files if f["era"] == "post-client"),
                "verdict": ("UNOBSERVABLE on disk: the only post-client file carries 6 turn rows "
                            "and 0 tool-call rows, so the fixed latch's tool-call path has never "
                            "written a row that any published cell used"),
            },
            "code_level_evidence_post_era": {
                "command": "python3 -m pytest experiments/ptr-engine/longrun/tests/test_client_ttft.py -q",
                "result": "8 passed",
                "asserts": ("experiments/ptr-engine/longrun/tests/test_client_ttft.py:226-227 first_token_kind == 'tool_call' with "
                            "ttft_source == 'first_delta'; :265-266 an unavailable TTFT stays null"),
            },
        },
        "corrections": [
            ("The brief's mechanism is not what the code does. The inline latch (committed "
             "run_longrun.py:1077 `if (piece_c or piece_r) and ttft is None`) leaves ttft_s NULL "
             "when the first delta carries only tool_calls; it never substitutes wall_ms. No "
             "version on disk or in git HEAD assigns latency to a ttft variable. The old latch's "
             "failure mode is SILENT DELETION of the row from every quantile (analyze_stats."
             "ttft_values drops nulls), not a wall-inflated tail. Measured: 0 of 186 tool-call "
             "rows are null, so in this corpus the deletion never happened either."),
            ("analyze_stats.py:470 warns that a row flagged ttft_source == 'unavailable' may "
             "carry a number that is 'a wall-clock fallback rather than a first-delta "
             "measurement'. No row on disk is in that state: ttft_dropped_unavailable is 0 in all "
             "24 cells of LATENCY-REPORT.json, and the post-client file's 6 rows are all "
             "first_delta."),
            ("client.py's inode birth (2026-10-26T16:13:55Z) postdates the only post-client rows "
             "file (2026-10-26T15:17:04Z), so the exact client revision that wrote those 6 rows is "
             "not recoverable by digest; the pin is the read-time sha only."),
        ],
        "assumptions": [
            ("'tool-call turn' = a row whose tool_calls list is non-empty. In the three tool files "
             "every follow-up row also carries tool_calls, so the row-level set is exactly the "
             "tool_calls set."),
            ("The card's run-level rule ('kind == tool-followup present in the same run') is "
             "applied on run_id; each of the three tool files holds exactly one run, so the "
             "run-level set is the whole file."),
        ],
    }

    text = json.dumps(out, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if args.stdout:
        sys.stdout.write(text)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s (%d bytes)" % (args.out, len(text.encode())))


if __name__ == "__main__":
    main()
```
