# TURN-DEDUP — 48 / 46 / 43 are three different questions

Status: reconciled against the rows files on disk, 2026-10-26. Offline; no network.
No analyser, row, grade, threshold or published page was edited. Test: `tests/test_turn_dedup.py`.

## 1. What each count is, with the code that makes it

| count | meaning | code |
|---|---|---|
| **48** | turn rows for one cell: rows whose `kind` is a turn row | `analyze_stats.turn_latency_rows`, `TURN_ROW_KINDS = ("turn-initial", "turn")` at `experiments/ptr-engine/longrun/analyze_stats.py:608`; selector at `:805-908` |
| **46** | that set after the report tool's rule R, which is applied to the whole file *before* the analyser runs | `latency_report.dedupe` at `experiments/ptr-engine/tools/latency_report.py:202-214`, called from `dedupe_rows` `:230-245`, applied at `:310` and `:324` |
| **43** | distinct `content_sha256` (assistant response text) among the turn rows | response hash, not a turn identity: `latency_report.py:17` documents it as `sha256(assistant content)` |

The selector's own de-duplication is a different rule again: `_turn_key` is
`(arm, rep, turn_index|turn)` (`analyze_stats.py:797-802`), and
`meta["dropped_duplicate"]` (`:871`, `:878`) counts rows that share a turn key.
For every cell measured here that count is **0** — one row per turn — so the
selector is not the source of the 48→46 step.

Rule R's key is `(ts, content_sha256, prompt_tokens, completion_tokens)` and it
**keeps the first occurrence** (`latency_report.py:206-212`). Nothing in the key
identifies a turn: `ts` is a millisecond timestamp, and the content hash is a
response hash. This is the whole defect.

Row writers for one turn (the current model, one row per send):

- `run_longrun.py:2501-2508` — `turn-initial` row when a tool follow-up hit the wall cap;
- `run_longrun.py:2526-2533` — `turn-initial` row when the follow-up request failed;
- `run_longrun.py:2575-2576` — the `turn` row (this row is the **last** send of the turn, `send_index = len(followup_rows)`, `:2549`);
- `run_longrun.py:2598-2601` — the `turn-initial` row for a normal attributed turn;
- `run_longrun.py:2603-2604` — `tool-followup` rows for follow-ups `1..k-1`.

Before ROW-ATTRIBUTION the last follow-up was written **twice** — once as a
`tool-followup` row, once mirrored as the `turn` row — documented at
`analyze_stats.py:583-601` ("in the legacy files it double-counts the last send
... which is how a 48-turn cell produced a published p95 at n=70"). The rows
files that carry the 48/46/43 discrepancy are exactly those legacy files.

## 2. Recomputed counts from raw rows

`a` = rows with `kind ∈ {turn-initial, turn}`; `b` = `turn_latency_rows` after
`dedupe_rows`; `c` = distinct `content_sha256`; `d` = distinct `prompt_sha256`
(the request hash present in these files — there is no `request_sha256` column).

| cell | rows | a | b | c | d | rule R excess |
|---|---|---|---|---|---|---|
| `rows-longrun-c-2026-10-26.jsonl` / pointer-stable | 192 | 48 | 48 | 48 | 48 | 0 |
| `…-c…` / lease-reopen | 192 | 48 | 48 | 46 | 48 | 0 |
| `…-c…` / transcript-compact | 192 | 48 | 48 | **9** | 48 | 0 |
| `…-c…` / transcript-grow | 192 | 48 | 48 | 33 | 48 | 0 |
| `rows-longrun-v5-tools.jsonl` (G8) | 72 | 48 | **46** | 43 | 48 | 2 |
| `rows-longrun-v6-tools.jsonl` (G9) | 72 | 48 | **37** | 43 | 48 | 11 |

So the quoted 48/46/43 triple is **G8** (`rows-longrun-v5-tools.jsonl`), not v6:
`48` turn rows, `46` after R, `43` distinct response bodies. v6 carries the same
defect twice as badly: **48 → 37 → 43**. The `c` column on the `c` grid shows
why it cannot be a turn count at all: `transcript-compact` has 48 turns and only
**9** distinct responses.

## 3. Which rows R drops, and whether they are genuine duplicates

Every dropped row is a `turn` row whose key matches a row already kept, and the
kept row is the `tool-followup` **mirror of the same send**. Quoted from
`rows-longrun-v6-tools.jsonl` (arm `pointer-stable`, rep 1):

```
drop  idx=1  turn=1  kind=turn           ts=2026-10-26T13:16:13.529Z  content_sha256=eb8791454799…  prompt_tokens=3520  completion_tokens=288  ttft_ms=192.567  latency_s=8.057474  prompt_sha256=ff82c059835d…
keep  idx=0  turn=1  kind=tool-followup  ts=2026-10-26T13:16:13.529Z  content_sha256=eb8791454799…  prompt_tokens=3520  completion_tokens=288  ttft_ms=192.567  latency_s=8.057474  prompt_sha256=3ffd73d90220…
```

Identical for all 11 (v6) and 2 (v5) drops: same `ts`, same `content_sha256`,
same `prompt_tokens`, same `completion_tokens`, same `ttft_ms`, same
`latency_s`, same `run_id`, same `turn`, same `rep`. The only fields that differ
are `kind` and `prompt_sha256` — the legacy `turn` row stamps the turn's
*initial* prompt hash onto the *last send's* measurement, which is the mirroring
defect `analyze_stats.py:583-601` describes.

**Are they genuine duplicates?** Yes as measurements — one send, one TTFT,
recorded twice. They are not "distinct turns that happen to share a response
body": the `d` column (distinct request hashes) is 48, and the drops are
same-turn, same-`ts` pairs. R's *diagnosis* is right.

**Is R's action right?** No. R keeps the first occurrence, which is the wire-order
`tool-followup`; the row it deletes is the only row the frozen per-turn
definition can select for that turn (`turn_latency_rows` takes
`turn-initial` and never takes a `tool-followup`, `analyze_stats.py:848-852`,
`:867`). So R removes a duplicate measurement **and** removes the turn from the
turn-level sample. 48 turns become 46 (G8) and 37 (G9) — a 23% loss on G9.
Measured: `turn_latency_rows(raw)` selects 48, `turn_latency_rows(dedupe(raw))`
selects 46 / 37. That is data loss relative to the metric being reported, even
though each individual pair is a true duplicate.

Smallest fix (not applied here — the analyser and the report tool are frozen for
this card): in `latency_report.dedupe`, when a key collides, prefer the row whose
`kind` is in `TURN_ROW_KINDS` over a `tool-followup` row, i.e. replace the kept
entry in place instead of dropping the arrival. The measurement count is
unchanged (`excess` stays 2 / 11); the turn count returns to 48.

## 4. The true per-cell n, and the pooled n at 3 reps

The frozen definition is `turn_latency_rows` — one row per turn identity
`(arm, rep, turn)`. By that definition each of these cells has **n = 48**:
48 distinct `(arm, rep, turn)` identities, 48 distinct `prompt_sha256`, and the
selector's own duplicate count is 0. `46` and `37` are rule-R artefacts applied
to the wrong unit (a send-level measurement hash used to decide a turn-level
count); `43` is response-text diversity and is not a count of turns at all.

Pooled over 3 reps at **48 turns per cell**: `n = 3 × 48 = 144` per arm.

Admissibility arithmetic (`TAIL_MIN = 3`, `analyze_stats.py:111`;
`min_n_for(q) = max(MIN_N, ceil(TAIL_MIN / (1 - q)))`, `:330-335`):

```
floor:  min_n_for(0.95) = ceil(3 / 0.05) = 60
n = 144: n*(1-q) = 144*0.05 = 7.2  >= 3   OK
n = 138: n*(1-q) = 6.9             >= 3   OK
n = 129: n*(1-q) = 6.45            >= 3   OK
```

p95 rank span with linear interpolation, `h = (n-1)·q`, `i = floor(h)`
(`_quantile_sorted`, `analyze_stats.py:279-288`):

```
n = 144: h = 143*0.95 = 135.85 -> between order stats 136 and 137 (1-based), 7.2 obs above
n = 138: h = 137*0.95 = 130.15 -> between order stats 131 and 132,           6.9 obs above
n = 129: h = 128*0.95 = 121.60 -> between order stats 122 and 123,           6.45 obs above
```

All three clear the floor: the discrepancy does **not** change whether a p95 is
admissible. It changes the sample actually pooled and the width of the interval,
and therefore the reported n and the tail weight — which is why it has to be
stated rather than papered over.

## 5. What this does to the plan

- The grid's 3-rep plan targets **3 × 48 = 144 usable turns per arm**, and the
  frozen definition does reach it on every cell measured here (`a = 48`,
  selector duplicate count 0).
- The price of 1,016 for 480 turns (10 cells × 48) buys 480 turns; at 3 reps an
  arm that pools 3 cells gets 144. That holds **for files written by the current
  one-row-per-send writer**, which emits `turn-initial` + `tool-followup` +
  `turn` with no mirrored pair, so rule R has nothing to drop on turn rows.
- As the tooling stands, on a legacy mirrored tools file the pooled numbers the
  report prints are 3 × 46 = **138** (G8) and 3 × 37 = **111** (G9), not 144 —
  a 4% and a 23% shortfall. Those are the numbers to distrust, not the 48.
- Rule R itself does not have to be removed: keeping the turn-kind row on a
  collision gives 48 turns and the same 2 / 11 measurement drops, so the plan
  reaches 144 without changing the price.

## 6. Test

`tests/test_turn_dedup.py` — 8 cases, `PYTHONPATH=src python3 -m pytest tests/test_turn_dedup.py -q`:

- 4 green: `a/b/c/d` census on both files, plus the evidence that each dropped
  row is the mirrored twin of a kept `tool-followup` (same `ts`, `ttft_ms`,
  `latency_s`, `completion_tokens`).
- 4 red (`test_rule_r_keeps_every_turn_the_definition_selects` and
  `test_dedupe_keeps_a_selectable_row_for_every_turn`, × 2 files): rule R leaves
  2 (G8) / 11 (G9) turns with no selectable row.

The analyser is not fixed here; the red test names the smallest fix in its
docstring.
