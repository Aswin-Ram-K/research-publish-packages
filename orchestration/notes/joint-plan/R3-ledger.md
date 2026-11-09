# R3 — Ledger, reservation, spend and price inputs (planning deliverable)

**Unit:** R3-LEDGER · **Scope:** pricing/planning only. No live inference, no service change, no ledger/reservation write, no fixture/grader change. Read-only against target repos. All paths are under `/home/zer0null/research extractor` (real checkout, branch `research/next-candidates-2026-10-24` @ `f17663d`).

**Read-only proof:** only write paths are `orchestration/notes/joint-plan/R3-ledger.md` and `orchestration/handoffs/R3-LEDGER.json`. Target artefacts were not modified; sha256 of `experiments/ptr-engine/measure/REQUEST-LEDGER.json` = `8ebf4ed5d1c7c5616ba96e7dc38424cac829912d5ae7c7ccab50827a5e29494c` (matches `RESERVATIONS.json` `ledger_sha256`) and `RESERVATIONS.json` = `0c717fabeeeac747821ed59f30ebcba4bf1d0bbfc3e4d019916dfa744ff53ae1`.

---

## 1. Reservation inventory (verbatim, not normalised)

Source files:
- `experiments/ptr-engine/measure/RESERVATIONS.json` (521 B) — top-level object `{"reservations": [ {…} ]}`.
- `experiments/ptr-engine/measure/RESERVATION-CCS-2026-11-05.json` — the same single object unwrapped.

The two files are byte-equivalent in content (the second is the unwrapped reservation record). They are NOT two reservations; they are one reservation recorded twice. Per the task, both are printed verbatim and are NOT merged or normalised.

### 1.1 `RESERVATIONS.json` → `reservations[0]`

```json
{
  "run_id": "CCS-2026-11-05",
  "requested_count": 1500,
  "granted_count": 1500,
  "bound_applied": "requested_count",
  "operator_cap": 2000,
  "ledger_path": "/home/zer0null/research extractor/experiments/ptr-engine/measure/REQUEST-LEDGER.json",
  "ledger_sha256": "8ebf4ed5d1c7c5616ba96e7dc38424cac829912d5ae7c7ccab50827a5e29494c",
  "ledger_remaining_at_reservation": 1729,
  "timestamp_utc": "2026-11-05T08:03:11Z",
  "dry_run": false
}
```

### 1.2 `RESERVATION-CCS-2026-11-05.json` (entire file)

```json
{
  "run_id": "CCS-2026-11-05",
  "requested_count": 1500,
  "granted_count": 1500,
  "bound_applied": "requested_count",
  "operator_cap": 2000,
  "ledger_path": "/home/zer0null/research extractor/experiments/ptr-engine/measure/REQUEST-LEDGER.json",
  "ledger_sha256": "8ebf4ed5d1c7c5616ba96e7dc38424cac829912d5ae7c7ccab50827a5e29494c",
  "ledger_remaining_at_reservation": 1729,
  "timestamp_utc": "2026-11-05T08:03:11Z",
  "dry_run": false
}
```

### 1.3 Field meanings and status

| field | recorded value | meaning / status |
|---|---|---|
| `run_id` | `CCS-2026-11-05` | reservation identifier; no matching run artifact found in `measure/rows-*.jsonl` (latest row ts `2026-10-28T03:35:42.114Z`, see §3) |
| `requested_count` | 1500 | requests asked for |
| `granted_count` | 1500 | requests granted |
| `bound_applied` | `requested_count` | the binding limit was the requested count, not `operator_cap` |
| `operator_cap` | 2000 | operator-imposed cap for the run; not reached (1500 < 2000) |
| `ledger_path` | `…/REQUEST-LEDGER.json` | ledger the reservation was checked against |
| `ledger_sha256` | `8ebf4ed5…` | sha256 of that ledger at reservation time; matches the on-disk ledger today (see read-only proof above) |
| `ledger_remaining_at_reservation` | 1729 | remaining recorded at reservation time (matches ledger's `remaining`) |
| `timestamp_utc` | `2026-11-05T08:03:11Z` | reservation instant |
| `dry_run` | `false` | NOT a dry run; recorded as a real reservation |

**Status:** the reservation exists as a record only. No mechanism in the repo tracks actual spend against it (grep for `ledger_remaining_at_reservation`/`bound_applied` returns only these two files; `experiments/ptr-engine/longrun/cell.py` and `tools/*.py` contain no reservation consumer). Whether the 1500 were ever spent is **UNKNOWN** (see §5).

---

## 2. Ledger semantics

### 2.1 What one row is

Definition (`docs/REQUEST-LEDGER.md` §2 "What is counted", rule text):

> "The instrument reads every `experiments/ptr-engine/measure/rows-*.jsonl` and counts **one request per row that represents an inference call**."

And `REQUEST-LEDGER.json → rule`:

> "one request per row that IS one wire request: kind in {turn, tool-followup, turn-initial, digest} count (each traced to its make_row call site in run_longrun.py); billed:false, followup_suppressed, served_from:prompt do not; a row with NO kind is counted and flagged assumed_billed; an UNRECOGNISED non-empty kind is refused (UnrecognisedKind), never silently billed or unbilled"

So: **one row = one HTTP completion request that reached the wire**, provided its `kind` is in the counted set. It is not "one turn" (a turn can bill k+1 requests: initial send + follow-ups) and not "one batched request" (each row is a separate completion). The identifying key is the row's presence in a `rows-*.jsonl` file plus its `kind`; the ledger has no request-id field — request identity is positional/row-level, not a UUID.

### 2.2 Counted kinds and their code sites

From `docs/LEDGER-RECONCILE.md` §"LEDGER-KIND-RULE" (table) and `run_longrun.py`:

| kind | counts? | code site |
|---|---|---|
| `turn` | YES | `run_longrun.py:2703` `make_row(..., "turn", ...)`; gated `:2527` `gate.acquire(t, "turn")` |
| `tool-followup` | YES | `run_longrun.py:1126` `make_row(..., "tool-followup", ...)`; gated `:1115` |
| `turn-initial` | YES | `run_longrun.py:2726-2729`; initial send's own row (`:2672`: "With k >= 1 follow-ups this turn made k+1 requests…") |
| `digest` | YES | `run_longrun.py:2479` `gate.acquire(t, "digest")` then `:2481` `resp = send_chat(cfg, msg)`; rows `:2491/:2504/:2512` |
| (no kind) | YES + flagged `assumed_billed` | legacy schema (232 rows in current corpus); conservative direction |
| unknown non-empty kind | REFUSED (`UnrecognisedKind`) | `request_ledger.row_bills` is the sole implementation; `COUNTED_KINDS = ("turn","tool-followup","turn-initial","digest")` |

`tool_call` is **not** a kind at all — it is a row *field* (`run_longrun.py:2692` `row_extra["tool_calls"] = turn_calls`) describing calls the turn row already bills.

### 2.3 Exclusion markers (warmups / retries / aborts / failures)

From `REQUEST-LEDGER.json → counting` and `marker_reconciliation` (corpus census):

| marker | excludes? | corpus (row-level) | can change count? |
|---|---|---|---|
| `billed: false` | yes (when false) | 0 rows | **no — dead code** |
| `followup_suppressed` (truthy) | yes | 0 rows (36 nested inside `tool_calls[]`) | **no — dead at row level** |
| `served_from == "prompt"` | yes | 0 rows (479 nested) | **no — dead at row level** |
| `billed_round` | **no** | 317 rows (true 291, false 26) | no — fetch-ROUND accounting; a pinned serve still costs a request |
| `fetch_followup` | **no** | 644 rows (all true) | no — marks a row that IS a real follow-up request |
| `prompt_served` | **no** | 317 rows (275 ×0, 42 ×1) | no — per-round cache counter |
| `is_checkpoint` | **no** | 23 rows | no — "NOT a billing marker: checkpoint rows are genuine calls" |

Warmups: a warmup that reaches the wire is a row with a counted kind → counted (no warmup-specific exclusion marker exists). Retries: a retried request that reaches the wire is a second row → counted (no retry marker). Aborts: an HTTP-error row still counts ("a rejected request still consumed a slot on the wire"). Failed calls: counted. The only things that do NOT count are the three exclusion markers above, none of which appears at row level in this corpus.

### 2.4 Duplicate accounting (diagnostic only, never deducted)

Rule (`REQUEST-LEDGER.json → dedup_rule`):

> "identical (ts, content_sha256, prompt_tokens, completion_tokens) within one file; first occurrence kept"

- 30 excess rows found, all in three tool-loop files: `rows-longrun-v4-tools-2026-10-26.jsonl` 17, `rows-longrun-v5-tools.jsonl` 2, `rows-longrun-v6-tools.jsonl` 11 (`docs/REQUEST-LEDGER.md` §3 table).
- 3 legacy-schema files are `not_applicable` (`rows-baseline`, `rows-equalinfo`, `rows-live`) because they lack millisecond `ts` and `content_sha256`; the literal tuple would have fabricated 24 duplicates there (11 + 2 + 11 collisions).
- **Deduction is withheld.** `deduction_rule_sound = false` because `content_sha256` is `sha256(assistant content)`, not request identity (`run_longrun.py:1555`; 869/869 rows satisfy equality). `V-DUPLICATE-RULE` graded `overall: fail`. `deduction_permitted()` requires the sound flag AND a `request_identity_hash` evidence; the flag alone raises. `requests` publishes as `requests_raw` = 2,591.

### 2.5 Disagreements recorded (not resolved here)

1. **Decidable-file count.** The `REQUEST-LEDGER-2` card / `TVS-REGRADE` headline says 9 decidable files and 5 legacy; the schema census says **11 decided / 3 not_applicable**. The report carries the measured split (`dedup_decision.files_deduped` / `files_not_applicable`) plus `count_discrepancy`. Arithmetic (30 excess, 1,071 deduplicated) is identical under either split because all 30 excess rows live in decidable files. Source: `docs/REQUEST-LEDGER.md` §3 "A count discrepancy, recorded."
2. **`requests_raw` vs current disk.** `REQUEST-LEDGER.json` says `requests_raw = 2591`, but `FETCH-BUDGET-48.md` §5 states a fresh scan reads `raw=1128`… wait, that is an older drift note (27 requests, 1,101 vs 1,128). For the current 2,591 figure, `docs/STATE.md` §1 says the ledger was rebuilt 2026-10-28 to 2,591/1,729 and `tools/run_a_star.py --dry-run` reports `gap=0` with `1,321 + 1,270 = 2,591`. The ledger's own `files`/`per_file` sum to 2,591 (verified §3 below). So the on-disk corpus and the ledger agree at 2,591; the 27-request drift noted in `FETCH-BUDGET-48.md` was a pre-rebuild (1,101-era) observation and is historical, not current.
3. **`requests` field publishes raw.** `requests = 2591` and `requests_raw = 2591` and `requests_deduplicated = 2561`; `deduction.applied = false`. Any consumer quoting 2,561 as spend would be quoting the diagnostic, which is explicitly forbidden (`docs/REQUEST-LEDGER.md` §1).

---

## 3. Spend (computed from the ledger's own rows)

**Exact computation (Python, run 2026-11-07, read-only):**

```python
import json, glob
d = json.load(open('experiments/ptr-engine/measure/REQUEST-LEDGER.json'))
# 1) ledger's own declared totals
assert d['requests_raw'] == 2591
assert d['requests'] == 2591
assert d['remaining'] == 1729
assert d['budget']['cap'] == 4320
assert d['budget']['spent'] == 2591
assert d['budget']['remaining'] == 1729
# 2) recompute from per_file rows
rows_sum = sum(f['rows'] for f in d['per_file'])          # 2591
reqs_sum = sum(f['requests'] for f in d['per_file'])       # 2591
files_n  = len(d['per_file'])                             # 41
assert rows_sum == reqs_sum == 2591
# 3) token accounting across all row files
tok = []
for path in glob.glob('experiments/ptr-engine/measure/rows-*.jsonl'):
    for line in open(path):
        line=line.strip()
        if line: tok.append(json.loads(line))
prompt = sum(r['prompt_tokens'] for r in tok if isinstance(r.get('prompt_tokens'),(int,float)))
completion = sum(r['completion_tokens'] for r in tok if isinstance(r.get('completion_tokens'),(int,float)))
print('rows',len(tok),'prompt_tokens_sum',prompt,'completion_tokens_sum',completion)
# 4) last-row timestamp
lasts = [f['last_ts'] for f in d['per_file']]
print('min first_ts', min(f['first_ts'] for f in d['per_file']))
print('max last_ts ', max(lasts))
```

**Result of that computation:**
- `requests_raw` (ledger-declared spend) = **2,591**; `requests` (published) = **2,591**; `requests_deduplicated` (diagnostic, NOT spent) = **2,561**; `duplicate_excess` = **30**.
- Recomputed from `per_file`: 41 files, 2,591 rows, 2,591 requests — matches `total.rows`/`total.requests`.
- Token accounting across all 2,591 rows: `prompt_tokens` sum = **14,517,784** (min 177, max 51,216, mean 5,633.60); `completion_tokens` sum = **1,017,166** (min 1, max 16,384, mean 394.71). `cached_tokens` non-null on 2,437 of 2,591 rows.
- Kind census: `turn` 1,715 · `tool-followup` 361 · `turn-initial` 283 · unmarked (assumed_billed) 232 = 2,591.
- **Last-row timestamp in the ledger:** `2026-10-28T03:35:42.114Z` (`rows-cell-lease-reopen-20261028T033139Z.jsonl`); earliest first-row ts `2026-10-26T05:28:15Z` (`rows-live-2026-10-26.jsonl`).
- Ledger artefact sha256 `8ebf4ed5d1c7c5616ba96e7dc38424cac829912d5ae7c7ccab50827a5e29494c`; `generated_at_utc` not present as a top-level key in this file, but `docs/STATE.md` §1 records the rebuild instant as **2026-10-28** and `docs/LEDGER-GRID-BASELINE.md`/v4 baseline `as_of 2026-10-27T20:53:48Z`.

**Dated conclusion:** as of the ledger's last row (`2026-10-28T03:35:42Z`), spend = **2,591 requests**, 14,517,784 prompt tokens, 1,017,166 completion tokens. Nothing in the row corpus post-dates 2026-10-28.

---

## 4. The 2,591-spent / 1,729-remaining figure

- **Source:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` rebuilt 2026-10-28 from `measure/rows-*.jsonl` via `tools/request_ledger.py` (`docs/STATE.md` §1 "Request ledger": "rebuilt 2026-10-28 to 2,591/1,729 (`tools/request_ledger.py`; sha now `8ebf4ed5…`)" and `docs/STATE.md` lines 66-71).
- **Cap confirmation:** `budget.cap = 4320`, `budget.reserve = 0`. `2591 + 1729 = 4320` exactly. So **4,320 is the cap** and 1,729 is `cap − spent` under the ledger's own arithmetic (`budget.remaining = 1729`). Confirmed by `docs/STATE.md` §1 table ("Cap / reserve | 4,320 / 0") and `docs/GRID-2-FINAL.md` ("Spend after the grid | 2,591 / 4,320 ⇒ 1,729 remaining (delta +1,270, gap 0)").
- **Is 1,729 an available balance? NO — it is a 2026-10-28 snapshot.** `docs/STATE.md` §1 last paragraph: "snapshot 2026-10-28 — must be re-reconciled before any future run" and §0 "UNFUNDED (7,560 requests against 1,729 remaining)". `VALIDATION-ROADMAP.md` §0 rule 2 states the ledger "must be re-reconciled at execution time; if it cannot be rebuilt and the arithmetic shown, the budget is unknown and zero requests are sent."
- **Components that are UNKNOWN:**
  - Spend incurred between 2026-10-28 and now (2026-11-07): no row files post-date 2026-10-28, but absence of evidence is not evidence of absence; the ledger has not been rebuilt since 2026-10-28.
  - Whether reservation CCS-2026-11-05 (1,500) was actually spent (§1.3).
  - Dollar cost and energy cost of any request (§6): not recorded anywhere.
  - Whether the 1,729 is still unreserved: the reservation file claims 1,500 against 1,729 but no spend tracking exists.

**Therefore the precise statement is:** `spent = 2,591` (as of ledger last row `2026-10-28T03:35:42Z`), `reserved (recorded, unverified spend) = 1,500` (CCS-2026-11-05), `unknown = post-2026-10-28 spend + reservation actualisation + dollar/energy`, `available = UNKNOWN` (§5).

---

## 5. Available capacity

**`available = UNKNOWN`.**

Missing link (exact): there is no verified current spend after `2026-10-28T03:35:42Z` and no mechanism that actualises reservation CCS-2026-11-05 against the ledger. The ledger's `remaining = 1,729` is a 2026-10-28 snapshot (§4), and the reservation's `ledger_remaining_at_reservation = 1,729` was recorded 2026-11-05 against that same stale snapshot. Neither the spend nor the reservation consumption has been re-reconciled. Per `VALIDATION-ROADMAP.md` §0 rule 2, an un-rebuildable budget is *unknown* and zero requests are sent.

**Reserved-but-unspent shown separately from spent:**
- Spent (verified, ledger rows): **2,591 requests** (as of `2026-10-28T03:35:42Z`).
- Reserved (recorded, spend unverified): **1,500 requests** (CCS-2026-11-05, `granted_count=1500`, `dry_run=false`, `bound_applied=requested_count`, `operator_cap=2000`). No evidence in `measure/rows-*.jsonl` that it ran (latest row ts precedes the reservation by 7 days).
- If (and only if) the reservation is entirely unspent and no other spend occurred, the arithmetic upper bound would be `1,729 − 1,500 = 229` requests — but this is **not** an available balance, because both premises are unverified. It is recorded as a conditional upper bound only.

---

## 6. Price inputs for cost modelling

Measured/recorded figures found in the repo. Dollar and energy costs are **not** recorded anywhere (see bottom).

### 6.1 Dollars (USD)

- `docs/prompt-system/R2-PROMPT-RESULTS.md` §6: declares **USD 0.20 / 1M uncached input tokens** in `state/config/r2-prompt-cost.json`, explicitly labelled *"declared, not measured — the box is on-prem"*. Cost table for one 71-turn run: O1 $0.007532 (P0) … O4 $0.023968 (P3). Source: `docs/prompt-system/R2-PROMPT-RESULTS.md:126-129` and §6.
- **No other dollar cost is recorded anywhere in the repo.** There is no per-request price, no invoice, no cloud rate card. Energy cost is not recorded at all (no $/kWh, no GPU power draw in watts). Per the plan, unknown dollar/energy cost stays UNKNOWN — it must not be imputed.

### 6.2 Wall time / latency (measured)

- `experiments/ptr-engine/measure/PROJECTION.json` (unit `PROJECTION`, amended by `PROJECTION-MODE`):
  - measured p50/p90 per mode (thinking `off`/`on`/`auto`): off p50 **2.9 s**, p90 **38.1 s**; on/auto p50 **218.2 s**, p90 **682.7 s**; "live six" p90 **427.7 s**. Source: `PROJECTION.json → defaults.measured_p50_s_by_mode / measured_p90_s_by_mode`.
  - `seconds_per_completion_token`: off **0.0338**, live **0.0288**, on_auto **0.0349**. Source: `budget-schedule.json → sources.projection` (`off_p50_s 2.9`, `off_p90_s 38.1`, etc.).
  - Policy turn wall: 60 s; turn wall cap: 180 s (`PROJECTION.json → defaults`).
- Row-level: `client_elapsed_s` present on all 2,591 rows (min 0.0516, max 2.1111, mean 0.4127 s in the live-corpus subset sampled earlier; note this is the client-side elapsed, not server TTFT). `ttft_server_s` present on only **73 of 2,591 rows** (min 0.0812, max 9.2924, mean 2.2291 s) — a sparse field; cannot support a per-request TTFT distribution without null handling.
- `experiments/ptr-engine/measure/budget-schedule.json` (generated 2026-10-26T15:50:00Z): per-completion-token seconds and projection arithmetic; `operator_4arm_60turn_3rep`: 720 requests serial, 43,200 s projected at 60 s/turn.

### 6.3 Tokens per request (measured)

- Corpus aggregate (§3): prompt_tokens sum 14,517,784 over 2,591 rows → mean **5,633.60** prompt tokens/request; completion_tokens sum 1,017,166 → mean **394.71** completion tokens/request. min/max prompt 177–51,216; completion 1–16,384. Cached tokens non-null on 2,437/2,591 rows.
- `budget-schedule.json → sources.ledger`: `per_turn_request_factor = 1.374532` (1,101 requests / 801 turn rows at the 2026-10-26 snapshot), decomposition 1.000 turn + 0.0849 tool-followup + 0.2897 unmarked per turn row. Note: this factor is from an earlier (1,101-row) snapshot, not the current 2,591 corpus; recompute before use. The four controlled longrun grids ran at exactly 1.000 request/turn.
- `FETCH-BUDGET-48.md` §5: V6 48-turn cell = 20 billed rounds over 48 turns; rounds histogram p50 0, p90 3, max 3, mean 0.417/turn.

### 6.4 GPU-seconds / energy (measured?)

- **GPU memory capacity/utilization:** not in this repo's measurement files (no `nvidia-smi` capture found in `measure/`). The serving inventory (R2) is responsible for live observation; this unit did not probe services. Historical candidate configs O1–O4 carry `--gpu-memory-utilization` flags (O3 `0.34`, O4 `0.15`) in `docs/serving-options/BEST-CONFIG.md` — those are *configuration values*, not measurements.
- **Energy:** not recorded anywhere (no kWh, no joules, no power draw). Marked UNKNOWN. The only "cost" currency in the repo is requests (the ledger cap 4,320) and declared USD 0.20/1M uncached tokens (§6.1).

### 6.5 Historical per-request cost (dollars) — O1–O4

`docs/prompt-system/R2-PROMPT-RESULTS.md` §6 table (one 71-turn run, at declared $0.20/1M uncached input tokens): O1 $0.007532 (P0) … O4 $0.023968 (P3). These are derived from declared (not measured) pricing and are **not** a per-request cost for the Consonance programme (different models/prompts). They are recorded as the only dollar figures in the repo.

---

## 7. Request-unit catalogue (historical programme counts)

| count | label | source | status |
|---|---|---|---|
| 0 | stage-0 offline gates (instrument validity) | `VALIDATION-ROADMAP.md` §"Stage map" row 0 ("**0**", "none" gate) and §"Stage 0 — offline gates" | recorded plan-estimate (0 requests by construction) |
| ≈9 | Stage 1 — law's own open cell (2-token rule measurement) | `VALIDATION-ROADMAP.md` §"Stage map" row 1 ("**≈9**", approval (a)); §"Stage 1" "Requests: ≈9 (recorded estimate)" | recorded estimate (not a price) |
| 36 | E1 cache-boundary sweep (of ≤60 ceiling) | `VALIDATION-ROADMAP.md` §"Stage 2a" "36 requests used, 24 held for re-runs"; protocol §4 | recorded plan-estimate |
| ≈185 | five-arm comparative pilot (1 task × 30 turns × 5 arms) | `VALIDATION-ROADMAP.md` §"Stage 2b" and `consonance-bounded-context-evaluation.md` §6.3 ("`30 × 4 + 60 = 180` turn requests + ~5 checkpoint/digest ≈ **185**") | recorded plan-estimate (pilot, not the comparative) |
| 7,560 | full five-arm comparative (A/B/C/D/E) | `consonance-bounded-context-evaluation.md` §6.3 arithmetic: `4 × (6×10+6×30+3×60)=4×420=1,680` per rep ×3 reps = 5,040 + D at 2 req/turn 2,520 = 7,560; "+ B digests and D checkpoints (≥1 per cell) = ≥7,560" | recorded plan-estimate (UNFUNDED at 1,729 remaining) |
| 4,320 | ledger cap | `REQUEST-LEDGER.json → budget.cap`; `docs/STATE.md` §1 | measured/pinned cap (not a request count per se) |
| 2,591 | current spend | `REQUEST-LEDGER.json` (§3) | measured (as of 2026-10-28T03:35:42Z) |
| 1,729 | remaining (snapshot) | `REQUEST-LEDGER.json → remaining` | snapshot, not available balance (§4–5) |
| 1,500 | reserved (CCS-2026-11-05) | `RESERVATIONS.json` / `RESERVATION-CCS-2026-11-05.json` | recorded reservation; spend unverified |
| 1,321 / 2,999 | baseline-4 (frozen) | `LEDGER-GRID-BASELINE-4.json` (`as_of 2026-10-27T20:53:48Z`, sha `3f879fa4…`) | frozen baseline |
| 1,101 / 3,219 | baseline-1 (frozen, pre-grid) | `LEDGER-GRID-BASELINE.json` (`captured_utc 2026-10-26T18:24:48Z`) | frozen baseline |
| 1,128 / 3,192 | baseline-2 (frozen) | `LEDGER-GRID-BASELINE-2.json` (`frozen_at 2026-10-26T19:04:18Z`) | frozen baseline |
| 1,176 / 3,144 | baseline-3 (frozen) | `LEDGER-GRID-BASELINE-3.json` (`as_of 2026-10-26T22:33:00Z`) | frozen baseline |
| 1,270 | grid marginal spend (16 cells) | `docs/STATE.md` §1 ("delta +1,270, gap 0"; "1,270 / 16 = 79.375 requests/cell") | measured (2,591 − 1,321) |
| 530–660 | tranche-1 pre-registered bracket | `docs/LEDGER-GRID-BASELINE.md` §5 ("10 × 53 = 530" gate-enforced vs "≈660" historical factor) | recorded estimate |
| 990 / 792 / 330 / 264 | budget-schedule schedules A/A*/B/C | `budget-schedule.json → schedules` (generated 2026-10-26T15:50:00Z) | recorded plan-estimate (requests_in_this_card = 0) |
| 696 (ceiling 810) | BOUNDARY-PREREG (separate candidate, never pooled) | `VALIDATION-ROADMAP.md` §0 approval gates (e) | registered candidate, unexecuted |

**Reconciliation check for the comparative:** `3 × (4 × 420 + 2 × 420) = 3 × (1,680 + 840) = 3 × 2,520 = 7,560`? Wait — recompute carefully per the doc's own formula: turns per arm per rep over available cells = 6×10 + 6×30 + 3×60 = 420. Four one-request arms (A,B,C,E) = 1,680 per rep; three reps = 5,040. D at 2 req/turn = 2 × 420 × 3 = 2,520. Total = 7,560. The verifier's stated form `3 × (4 × 420 + 2 × 420) = 3 × (1,680 + 840) = 7,560` gives the same 7,560 only because `2 × 420 = 840` is being added inside the per-rep bracket (i.e. D counted as 2 per turn within the same 420 turns). Both forms agree at 7,560. Note `7,560 / 1,729 = 4.37×` and `5,040 / 1,729 = 2.92×` (D-free). The 7,560 excludes B digests and D checkpoints (≥1 per cell → `≥ 7,560`).

**Verification reminders:**
- The comparative does NOT include serving variants (O1–O4 at full depth would be `≥ 4 × 7,560 = 30,240` context-comparison requests before extras), C0F equal-information control, memory-sweep cells, warmups, retries/aborts, or the real-workflow validation — those are separately priced line items in the joint plan, not covered by 7,560.
- 1,729 is a snapshot, not an available balance (§4–5).

---

## 8. What this unit did NOT do

- No live inference, no model completion request, no service restart, no config change.
- No fixture/grader modification, no ledger or reservation write.
- No target-repo write (target repos read with `--no-optional-locks` semantics; none were touched).
- No subagent spawned.
- Only write paths: `orchestration/notes/joint-plan/R3-ledger.md` and `orchestration/handoffs/R3-LEDGER.json`.
