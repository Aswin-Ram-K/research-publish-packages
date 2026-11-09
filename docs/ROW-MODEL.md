# ROW-MODEL — which row carries which HTTP request

**Status:** the writer contract in §1–§3 is **live** as of 2026-10-26 (unit `TURN-ROW-ATTRIBUTION`,
`experiments/ptr-engine/longrun/run_longrun.py`). §4 is the **accounting of the historical record**
and it disputes published figures. No rows file, grade file, ledger, TVS or latency report was
edited by this unit; the rows files' sha256 before and after the audit are in
[`measure/ROW-ATTRIBUTION.json`](../experiments/ptr-engine/measure/ROW-ATTRIBUTION.json)
(`rows_file_sha256_before` / `…_after`, `rows_files_sha_unchanged: true`).

**Owners of neighbouring rules:** request identity is `docs/REQUEST-IDENTITY.md`; the spend
deduction rule is `docs/REQUEST-LEDGER.md`; per-grid latency publication is
`measure/LATENCY-REPORT.json` / `docs/LATENCY-REPORT.md` (not edited here).

---

## 1. The defect this document answers

`orchestration/handoffs/DEDUPE-ROOT-CAUSE.json` (`evidence.double_append`,
`evidence.nature_of_the_pair`) proved that the pre-fix writer built the
`kind="tool-followup"` row from the **last** follow-up's response and then handed that same
response object back to the caller, which built the `kind="turn"` row from it as well. Per turn
with *k* follow-ups that was **k+1 sends, k+1 rows, k distinct measurements**: the turn's own
**initial** request had no row, and the last follow-up's measurement was written twice.

The writer now writes **one row per send** (§2). Nothing historical was rewritten: the pre-fix
rows keep their bytes, and their misattribution is counted in §4 rather than repaired.

## 2. The model — one row per HTTP request

For one turn, `N + 1` requests are made when the turn buys `N` tool follow-ups
(`tools_enabled(cfg) and not is_answer_turn`, allowance granted). Each request has exactly one
row:

| # | request | row | written at | identity |
|---:|---|---|---|---|
| 1 | the turn's **own** request, `planner.messages(info["prompt"])` | `kind="turn-initial"`, `send_index=0`, `initial_send=true` | `run_longrun.py:2246-2258` | its own `request_sha256`; `prompt_sha256` = the turn's prompt |
| 2…N | tool follow-ups 1…N−1, `send_chat(cfg, next_messages)` | `kind="tool-followup"`, `send_index=1…N−1`, `fetch_followup=true` | `run_longrun.py:974-983` (built), written in the caller at `:2259-2260` | each its own `request_sha256`; `prompt_sha256` = that follow-up's user block |
| N+1 | tool follow-up **N** (the last one) | `kind="turn"`, `send_index=N`, `fetch_followup=true`, `fetch_round_final=true` | `run_longrun.py:2197-2238` | its own `request_sha256`; the turn still records `prompt_sha256` of the **turn's** prompt (the discriminator `docs/REQUEST-IDENTITY.md` §2 relies on) |

With `N = 0` (no follow-up granted, or tools off, or a checkpoint turn) the turn's own request
**is** the turn row: `kind="turn"`, `send_index=0`, `row_measurement_source="turn-initial"`.

**Why the last follow-up's separate row is not written twice.** The turn row *is* that request's
row: it carries that request's `request_sha256`, `ttft_s`, `ttft_ms`, `latency_s`, `wall_ms`,
`prompt_tokens`, `completion_tokens`, `content_sha256` and `finish_reason`, because
`make_row` is handed that request's response. The row count per turn is unchanged from the pre-fix
writer (**k+1**), so budget and spend arithmetic that counts rows and sends still reconciles — but
no two rows now share one measurement.

`fetch_rounds_spent` (`run_longrun.py:802`) counts a round per `kind="tool-followup"` row **or**
per `fetch_followup=true` row, so the folded last round still counts once on `--resume`;
`fetch_round_final`, `final_round_billed` and `final_round_prompt_served` carry that round's
bookkeeping on the turn row.

### Field classes

| class | fields | meaning |
|---|---|---|
| **per-request** (belong to exactly one send) | `request_sha256`, `request_identity_complete`, `row_seq`, `send_index`, `row_measurement_source`, `ttft_s`, `ttft_ms`, `ttft_source`, `latency_s`, `wall_ms`, `prompt_tokens`, `cached_tokens`, `uncached_tokens`, `completion_tokens`, `content_sha256`, `finish_reason`, `stop_reason`, `truncated`, `max_tokens`, `prompt_sha256`\* | measured or computed from the one wire body / one response this row is |
| **per-turn** (repeat on every row of the turn, informational) | `turn`, `arm`, `rep`, `run_id`, `fetch_rounds_this_turn`, `fetch_rounds_used`, `fetch_rounds_cap_per_turn`, `fetch_prompt_serves`, `tool_calls`, `is_checkpoint`, `checkpoint` | describe the turn the request belongs to; identical across the turn's rows by construction |
| **row bookkeeping** | `kind`, `fetch_followup`, `initial_send`, `fetch_round_final`, `billed_round`, `prompt_served`, `final_round_billed`, `final_round_prompt_served`, `next_request_kind` | which slot of the turn this row occupies; never a measurement |

\* `prompt_sha256` is the hash of the prompt the **turn** asked with (`run_longrun.py:2197`), so on
the final follow-up's row (`kind="turn"`) it deliberately differs from `request_sha256`'s body —
that mismatch is the documented discriminator between *one request recorded twice* and *two
requests*. It is **not** a per-request field on a `kind="turn"` row that folded a follow-up.

## 3. The invariant a test can check

> **For every turn, the number of distinct `request_sha256` values across that turn's rows equals
> the number of HTTP requests the turn made** (`1 +` the number of `kind="tool-followup"` rounds
> bought), and no two rows share a `ttft_ms`/`latency_s` pair.

Checked in `experiments/ptr-engine/longrun/tests/test_row_attribution.py` for k = 0, 1, 2, 3
end-to-end through `run_cell` with a canned `send_chat` (**zero requests**, `socket.socket`
raises for the whole run): one row per send, distinct ttft per send, and the turn row's
`prompt_sha256` equals the hash of the user message the turn actually sent. The red→green proof
reverts the fix **in memory** (`run_longrun.attribute_initial_send = lambda: False`) and asserts
the pre-fix shape — k+1 rows, k distinct measurements, no `turn-initial` row — never by editing a
file on disk.

## 4. The accounting of the record — mirrors in the historical rows files

`experiments/ptr-engine/tools/row_attribution_audit.py` (read-only) classifies every
`kind="turn"` row: a **mirror** is a turn row whose `ttft_s` *and* `latency_s` equal a
`kind="tool-followup"` row's for the same `(arm, rep, turn)` — one response object, two rows. Full
list in `measure/ROW-ATTRIBUTION.json` (`grids[].mirrors`).

| grid | rows file | rows | `kind=turn` | mirrors | genuine | `tool-followup` | turns with follow-ups |
|---|---|---:|---:|---:|---:|---:|---:|
| G7 V4-TOOLS | `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 48 | **17** | 31 | 20 | 17 |
| G8 V5-TOOLS | `rows-longrun-v5-tools.jsonl` | 72 | 48 | **3** | 45 | 24 | 3 |
| G9 V6-TOOLS | `rows-longrun-v6-tools.jsonl` | 72 | 48 | **13** | 35 | 24 | 13 |
| G1–G6, G10 (tools off) | — | 192/40/29/192/96/96/6 | 192/40/29/192/96/96/6 | 0 | all | 0 | 0 |

**33 turn rows across the three tools grids are mirrors** (17 + 3 + 13); every tools-off grid is
clean. In each mirror turn the initial send is unmeasured and the last follow-up is counted twice.
This is the whole tools-era record: **no tools-grid row in any published file measures a turn's own
initial request.**

### 4.1 Which published figures are `attribution_disputed`

The figures below were computed over rows that include these mirrors, so their turn-row content is
the **follow-up's** latency and the pooled distribution double-counts the last follow-up of every
mirror turn. They are marked `attribution_disputed: true` in
`measure/ROW-ATTRIBUTION.json` → `attribution_disputed_published_figures`. **They were not
recomputed or edited here** — this is a finding, not a repair.

| figure | file / entry | published value | why disputed |
|---|---|---|---|
| G7 V4-TOOLS `pointer-stable` p50 | `measure/LATENCY-REPORT.json` `cells[grid_id=G7]`; `docs/LATENCY-REPORT.md` §G7 | `198.72 [166.05, 206.66] n=51` | 17 of 48 turn rows are mirrors; G7's p95 is already **withdrawn**, its p50 is not |
| **G8 V5-TOOLS** `pointer-stable` p50 | `measure/LATENCY-REPORT.json` `cells[grid_id=G8]`; `docs/LATENCY-REPORT.md:36`, `:51`, `:91`, `:154` | `143.91 [140.23, 151.95] n=70` | 3 of 48 turn rows carry a follow-up's measurement; 3 turns' initial sends unmeasured |
| **G8 V5-TOOLS** `pointer-stable` p95 | same entry; `docs/LATENCY-REPORT.md:36`, `:91`, `:107`, `:118`, `:154` | `397.41 [273.84, 659.70] n=70` | same rows; `n_turn_dedup=46` counts mirror rows as turn rows |
| **G9 V6-TOOLS** `pointer-stable` p50 | `measure/LATENCY-REPORT.json` `cells[grid_id=G9]`; `docs/LATENCY-REPORT.md:37`, `:51`, `:92`, `:155` | `147.59 [144.26, 168.07] n=61` | 13 of 48 turn rows carry a follow-up's measurement; 13 turns' initial sends unmeasured |
| **G9 V6-TOOLS** `pointer-stable` p95 | same entry; `docs/LATENCY-REPORT.md:37`, `:92`, `:107`, `:118`, `:155` | `429.70 [318.80, 477.06] n=61` | same rows; `n_turn_dedup=37` counts mirror rows as turn rows |

`G8` and `G9` are the only two published per-grid p95 values left (both pointer-stable **tools**
grids) — so **both surviving published p95 figures are attribution-disputed**. The p95 *n* is a
count of rows, not of requests: under the §3 model the honest per-request n for these grids would
be `n_kept + (mirrors)` (each mirror turn made one more request than it has rows) minus nothing —
i.e. G8 = 70 + 3 = 73 requests, G9 = 61 + 13 = 74, G7 = 51 + 17 = 68, if the unmeasured initial
sends were measured. Deriving those numbers from the rows is impossible (the initial responses were
never recorded); computing them would require re-running the cells, which this unit does not do.

**What is *not* disputed.** Every tools-off grid (G1–G6, G10): no follow-ups, so every turn row is
the turn's own request and the invariant holds trivially. Correctness/quality figures are not
affected: they read `content` from the turn row, and the turn row is still the turn's final
response.

## 5. What a future cell must record so per-turn latency means the turn's own request

1. **Read `kind="turn-initial"`** for a turn's own request: latency, TTFT, prompt and completion
   tokens of send 0 (`send_index=0`).
2. **Read `kind="turn"`** for the turn's **final** response (content, stop reason, answer fields,
   `finish_reason`) — and when `fetch_followup=true` on it, know that its latency is the **last
   follow-up's**, not the initial send's.
3. **Count requests, never rows**, for spend: distinct `request_sha256` (bounded below by
   `request_identity_complete`; `"unknown"` is not evidence). A row pair sharing a
   `request_sha256` is one request written twice, not two requests.
4. **Never pool `kind="tool-followup"` rows with `kind="turn"` rows as if each were a turn.** A
   per-request distribution must be one row per send (§3); a per-turn distribution must use
   `turn-initial` (or, for k=0, the `kind="turn"` row).
5. **Stamp the writer identity** on future rows so the era is readable from the row: rows written
   by the fixed writer carry `row_measurement_source`; rows from the pre-fix era carry no such
   field, so their attribution cannot be trusted and a cell must not silently pool the two eras.

## 6. Remaining holes (stated, not hidden)

- **Mid-turn aborts.** On a `RequestFailure` at follow-up *j* the cell now writes the initial row
  plus a failure row, but the follow-ups `1…j−1` of that turn were never appended (pre-existing
  behaviour: rows are appended after `fetch_rounds` returns). The §3 invariant is therefore stated
  for a turn that **completed** its tool rounds; a failed turn is under-recorded, and no analysis
  may treat such a turn as fully measured.
- **Historical rows cannot be repaired.** `request_sha256` is absent (`"unknown"`) on every row
  written before 2026-10-26, so a historical mirror can be proved only by measurement agreement
  (what §4 does), never by request identity.
- **The published figures stay published.** §4 marks them disputed; withdrawing or recomputing
  them is the latency report owner's call, not this document's.

## 7. Where this is enforced

| claim | artefact |
|---|---|
| one row per send, distinct measurement per send, turn prompt hash | `experiments/ptr-engine/longrun/tests/test_row_attribution.py` (k=0,1,2,3 + in-memory red→green) |
| the writer contract | `run_longrun.py:840-983` (`fetch_rounds`), `:2116-2262` (turn attribution), `:1500-1660` (`make_row` + `send_index`/`row_measurement_source` passthrough), `:1489` (`attribute_initial_send`), `:982` (follow-up `send_index`) |
| mirrors per grid, disputed figures, rows-file sha256 unchanged | `experiments/ptr-engine/tools/row_attribution_audit.py` → `measure/ROW-ATTRIBUTION.json` |
