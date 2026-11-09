# V-INSTRUMENTS — recomputing the three instruments that govern spend and gating

**Unit:** V-INSTRUMENTS · **verdict:** `partial` · **tool calls:** 22 / 36 · **inference requests:** 0
**Corpus:** 14 `rows-*.jsonl` files, **1,101 rows**, aggregate sha256
`3a5ea7057efc1a4da10476d8100965d432aa3ee1642fe66f90bf6e85ed1245f7`
(`sha256sum experiments/ptr-engine/measure/rows-*.jsonl | sha256sum`).
**Independence:** every number below was computed by my own script *before* the corresponding
implementation file was opened. Ordering is stated per section.

---

## A. `request_ledger.py` — the spend count — **PASS**

### A.1 My number first (rows only, no implementation read)

| quantity | mine |
|---|---|
| row files | 14 |
| rows | 1,101 |
| `kind` census | `turn` 801 · `tool-followup` 68 · **no kind marker** 232 |
| **requests that reached the wire** | **1,099** |

My costing rule, chosen before seeing theirs: *a row is a request iff it reached the wire* — it carries
`prompt_tokens` (a usage payload came back), **or** an HTTP-status error (the server saw and rejected it).
Everything else is a row that records a failure *before* any call.

The two rows this excludes, both in `experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl`
(unit `LIVE-CELLS-2`), have null token fields, no `http_status`, and an `error` that is a harness setup
fault:

```
setup: TypeError: Ledger.__init__() missing 1 required positional argument ...
target_not_reached P1=385
```

Neither ever became a chat-completion call. 1,101 − 2 = **1,099**.

### A.2 How I would treat the four edge cases

| case | corpus count | my rule | theirs | same? |
|---|---|---|---|---|
| **HTTP error** | 12 rows, `HTTP 400`, unit `C0-BASELINE`, null tokens, no `http_status` field | **count** — a rejected request still occupied a wire slot | count (unmarked ⇒ `assumed_billed`) | ✅ |
| **`kind=tool-followup`** | 68 | **count** — a real follow-up call, billed like any turn | count | ✅ |
| **checkpoint row** | 23 (`is_checkpoint=True`: 21 `turn`, 2 `tool-followup`) | **count** — each carries its own `prompt_tokens`/`completion_tokens` and its own content (`"…ANSWER: NOT-AN-ANSWER"`); a distinct inference, not a marker | count | ✅ |
| **null token fields** | 14 (12 HTTP-400 + 2 setup) | **count iff an HTTP error is recorded** → 12 in, 2 out | count all 14 | ❌ **Δ 2** |

### A.3 Reconciliation with the recorded artefact

| figure | recorded | mine | Δ |
|---|---|---|---|
| files | 14 | 14 | 0 |
| rows | 1,101 | 1,101 | 0 |
| requests | **1,101** | **1,099** | **−2 (0.18 %)** |
| assumed_billed | 232 | 230 (the 2 setup rows are not billed) | −2 |
| remaining of cap 4,320 | 3,219 | 3,221 | +2 |

**Their rule, read second.** `classify()` counts every row without a recognised `kind` and flags it
`assumed_billed`; the docstring says so deliberately: "an unmarked row that did hit the wire must not
vanish from the budget." That is the right *conservative default* and the wrong *only* default: the
bucket cannot distinguish "unmarked row that hit the wire" from "unmarked row recording a pre-flight
setup failure". A one-line refinement — exclude an unmarked row when it has **no tokens and no HTTP
error** — recovers the 2 without weakening the guard.

**Which rule is right.** Both are defensible; mine is tighter and still conservative. The difference
**inflates** the spend by 2 (0.18 %) — it can only refuse a run, never over-spend. It changes a decision
only inside a 2-request band at the boundary: with spent = 1,101 a `--would-spend 3220` is refused (over
by 1), whereas at 1,099 the last admissible value would be 3,221.

**Exclusion markers are dead against this schema.** The rule licenses `billed:false`,
`followup_suppressed`, `served_from=='prompt'`; **0 rows carry any of them**. The rows that *look* like
suppression are `billed_round` (4× `False`) and `prompt_served` (4× `1`) — the same 4
`tool-followup` rows, whose completions are **288 / 279 / 405 / 58 tokens**. They generated text, so they
are billed calls and counting them is correct. The tool's docstring already says this; my corpus check
confirms it rather than overturning it.

### A.4 Exit codes induced on the real corpus

```
$ python3 experiments/ptr-engine/tools/request_ledger.py
TOTAL  1101  1101  232  (14 files)
budget: spent=1101 would_spend=0 cap=4320 reserve=0 headroom=4320 projected=1101 remaining=3219
within budget: 1101 <= 4320 (3219 left)                                         exit 0

$ ... --would-spend 3220
OVER BUDGET: spent=1101 + would_spend=3220 = 4321 > cap=4320 - reserve=0 = 4320 (over by 1)
  [spent=1101 would_spend=3220 cap=4320 reserve=0 headroom=4320]                 exit 4

$ ... --glob /tmp/bad-rows.jsonl          # line 2 = "not json at all{{{"
row file error: /tmp/bad-rows.jsonl:2: unparseable row: Expecting value: line 1 column 1 (char 0)
nothing counted: an unreadable row file makes the total unknowable              exit 5

$ ... --glob /tmp/nomatch-*.jsonl
usage error: no row files matched '/tmp/nomatch-*.jsonl'                        exit 3
```

`4` is induced by a 1-request overshoot, so the printed arithmetic is the tightest possible test of the
comparison: `4321 > 4320`, over by 1. `5` refuses on the first unparseable line and counts nothing —
including the 1 valid row before it, which is the correct choice for a budget that must be knowable.

---

## B. The calibrated projection — **PARTIAL**

### B.1 My numbers first (rows only)

`wall_ms/1000` when present, else `latency_s`; rows with `error` dropped; linear-interpolated
percentiles; group = the row's own `thinking` value.

| group | n | mean s | p50 s | p90 s | s/token (Σwall/Σtokens) |
|---|---|---|---|---|---|
| live `cell-pointer-stable` (`thinking=auto`) | 6 | 190.9 | 129.1 | 427.7 | 0.0288 |
| on/auto pooled | 9 | 286.5 | 218.2 | 682.7 | 0.0349 |
| off/absent pooled | 960 | 27.5 | 2.9 | 38.1 | 0.0338 |

**Every figure equals `PROJECTION.json` to 4 decimal places — Δ 0.** The group classification also
reconciles: `thinking` values are `off` 601, absent 491, `auto` 8, `on` 1, so on/auto = 9 and
off/absent = 960, exactly the recorded `n`. My first pass mis-sorted `off` into "thinking on" by testing
truthiness; the recorded classification is the correct one, and this is the only place where my initial
number differed from theirs and theirs won.

**On `0.03 s/token`.** The figure is the *rounded published* number: `measure/BUDGET-SCHEDULE.md:24`
carries `0.0338 off · 0.0288 live · 0.0349 on/auto`. `0.03 × a nominal 2,000-token turn = 60 s`, which
is exactly `PROJECTION.json → defaults.projected_turn_wall_s`. So 0.03 is a summary constant, not a
fitted one, and it is optimistic for the on/auto group (0.0349) and conservative for off (0.0338) — by
less than 5 %, which is inside any sane tolerance.

### B.2 The residual spread — the aggregate hides a bimodal distribution

Per-**row** seconds/token:

| group | p10 | p50 | p90 | max | p90/p50 |
|---|---|---|---|---|---|
| live (n=6) | 0.0281 | 0.0283 | 0.0290 | 0.0290 | **1.02×** (tight) |
| on/auto (n=9) | 0.0281 | 0.0289 | 0.0439 | 0.0521 | **1.52×** |
| off (n=960) | 0.0280 | 0.0343 | 0.0420 | 2.4500 | 1.22× |

The ratio does **not** hold per row. The on/auto group is two clusters, not one distribution —
`0.0281, 0.0282, 0.0283, 0.0284, 0.0289, 0.0290` (n=6, the live rows) and `0.0416, 0.0419, 0.0521`
(n=3) — separated by a 1.5× step with nothing in between. The pooled 0.0349 is a number that describes
no single row. The off group is worse in the tail: median 0.0343, but rows reach **2.4500 s/token**
(71× the median), driven by long turns that emit few completion tokens (TTFT and tool waits are in the
wall but not in the token count). Any projection built on one ratio is a statement about the mass of the
distribution, never about a row.

### B.3 The boundary: does G2 accept what fits and refuse what does not?

`cell.eval_gate_projection` driven directly (`turns=60`, `reps=1`, artefact default 60 s/turn ⇒
`projected = 3,600 s`):

| `--max-wall` | projected | verdict |
|---|---|---|
| 3601 | 3600 | **ACCEPT** |
| 3600 | 3600 | **ACCEPT** (`ok = not(3600 > 3600)`) |
| 3599 | 3600 | **REFUSE (exit 8)** |

The comparison is `projected > max_wall`, so the boundary is exact at ±1 s and inclusive at equality.
The printed line is honest about what it is and what it is not:

```
turns=60 projected_requests=60 projected_wall~=3600s (cap-per-turn 180s -> worst case 10800s)
cap=3600s projected-turn-wall=60.0s source=artefact
```

### B.4 Can the original defect still be reached? **Yes — by flag.**

| invocation | projected | verdict |
|---|---|---|
| default (artefact 60 s) | 3,600 | accept |
| `--turn-wall-cap 180` **alone** | 3,600 | accept — the cap is *only* printed as the worst case |
| `--projected-turn-wall 180` | **10,800** | **refuse** — byte-for-byte the old defect (`60 × 180`) |
| `--projected-from rows-cell-pointer-stable…jsonl` (p90 427.7) | 25,662 | refuse |

So the repair is a **default change, not an invariant**: one flag restores the old worst-case projection
exactly. That is an acceptable design (the operator can always ask for a worst case) but it should be
stated as such — `--projected-turn-wall 180` is indistinguishable from the pre-repair behaviour.

### B.5 The gap that makes this `partial`

The default multiplier is **mode-blind**. `--projected-from` defaults to `None` and no code path in the
repository passes it, so a cell is admitted on the artefact's single 60 s unless a conductor remembers the
flag. For a `thinking=auto` cell the artefact's *own* data contradicts that default:

| cell | default projection | its own measured p50 | its own measured p90 |
|---|---|---|---|
| 60 turns, off/absent | 3,600 s | 60 × 2.9 = 174 s (default over-projects 20×) | 60 × 38.1 = 2,286 s |
| 60 turns, auto/on | 3,600 s | 60 × 218.2 = **13,092 s (3.6× under)** | 60 × 682.7 = **40,962 s (11.4× under)** |

`PROJECTION.json` already records this: `measured_p90_live_six_427.7` marks 12/48/60-turn cells
`admitted_under_3600: false` (5,132 / 20,530 / 25,662 s). The artefact knows the right answer; the gate's
default does not consume it. A thinking cell is therefore admitted at `--max-wall 3600` while the
instrument's own measurement of that exact configuration says 25,662 s — a 7.1× overrun of its ceiling.
Over-projection (the off case) is merely wasteful; under-projection (the thinking case) is the direction
that admits a cell which cannot finish.

---

## C. `client.STOP_REASONS` — **PARTIAL**

### C.1 Induction, 10/10 (my own inputs, my own script)

`client.derive_stop_reason(...)` called directly:

| # | member | input I chose | observed |
|---|---|---|---|
| 1 | `stop` | `finish_reason="stop"`, content present | `stop` |
| 2 | `length` | `finish_reason="length"`, no content | `length` |
| 3 | `tool_calls` | `finish_reason="tool_calls"`, no content | `tool_calls` |
| 4 | `content_filter` | `finish_reason="content_filter"`, content present | `content_filter` |
| 5 | `turn_wall_cap` | `error_code="turn_wall_cap"` | `turn_wall_cap` |
| 6 | `runaway_turn` | `error_code="runaway_turn"` | `runaway_turn` |
| 7 | `http_error` | `error_code="http_error"` | `http_error` |
| 8 | `stream_error` | `error_code="stream_error"` | `stream_error` |
| 9 | `empty_response` | no finish chunk, no content | `empty_response` |
| 10 | `unknown` | no finish chunk, content present | `unknown` |

Plus an unmappable server string: `finish_reason="weird"` → `unknown` (never squeezed into a neighbour).
Code path for each row-level value (`run_longrun.stop_reason_for_row`, the writer):

| row condition | observed |
|---|---|
| `resp.stop_reason` in the vocabulary | carried unchanged (`"length"`→`length`) |
| `resp` None, `extra.error="turn_wall_cap"` | `turn_wall_cap` |
| `resp` None, `extra.error="runaway_turn"` | `runaway_turn` |
| `resp` None, `extra.error` + `http_status` | `http_error` |
| `resp` None, `extra.error`, no status | `stream_error` |
| `resp` None, `extra` None | `unknown` |

### C.2 The three adversarial cases

| # | attempted wrong label | observed | reading |
|---|---|---|---|
| (i) | `finish_reason="length"` with `completion_tokens=5 < max_tokens=4096` | **`length`** | The server's finish chunk outranks token arithmetic (precedence 2 over 3). The label follows the wire, so a `length` row is **not** independently corroborated by `completion_tokens >= max_tokens`. Defensible (the server is the authority on its own stop) but it means "length" alone proves the server said so, nothing more. |
| (ii) | stream ends with **no finish chunk** and `completion_tokens=128 >= max_tokens=128` | **`length`** | Correct, and this is the recovery rule: the 128-token cap stop that used to look like a refusal is labelled `length` from token arithmetic when the server sent no final chunk. |
| (iii) | tool-call response with `finish_reason="tool_calls"` | **`tool_calls`** | Correct **when the finish chunk arrives**. |
| (iii-b) | tool-call response whose stream ends with **no finish chunk** and no text content | **`empty_response`** | **HOLE.** `derive_stop_reason` has no `tool_calls` parameter and only sees `content_present`; a tool call that produced no assistant text and no finish chunk is indistinguishable from a silent empty response. The row would say `empty_response` while a tool call had been dispatched. |

### C.3 `runaway_turn` is a declared member with no producer

`client.py:698` calls `derive_stop_reason(finish_reason, content_present=…, completion_tokens=…,
max_tokens=…)` — **`error_code` is never passed**. So members 5–8 can only arrive through
`stop_reason_for_row`'s `extra.error` branch. That branch accepts a code equal to
`"turn_wall_cap"` or `"runaway_turn"` — but **nothing anywhere writes `error="runaway_turn"`**
(`grep` over the non-test tree: the only occurrences are the constant, the tuple, and the accept test).
`run_longrun` records runaway turns as `error=turn_wall_cap` (`run_longrun.py:1812`). Consequence:
**0 rows can ever carry `runaway_turn`**; it is inducible only by handing the function a code that no
caller produces. The vocabulary is closed but not fully reachable.

### C.4 Historical rows: the "seven cap-exhausted arm-checks" claim

`group by stop_reason` over the corpus:

```
rows                                 1101
rows carrying a stop_reason field       0
group by stop_reason  ->  {None: 1101}
rows with finish_reason field         677
rows with max_tokens field            677
```

**The seven are not identifiable today.** No historical row carries the field, so grouping yields
nothing but `None`. What a **future** run records is the vocabulary word, derived in
`client.stream_response` and copied by `make_row`; `truncated` is derived *from* the word, so the two
cannot disagree. What the **old** rows would have recorded depends on information they never carried:

```
stage-1 rows (rows-longrun-2026-10-26.jsonl)                     192
  content empty, completion_tokens == 128                         99
  …of which lacking max_tokens                                    99
  re-derive WITH the manifest cap 128  ->  {length: 99}
  re-derive from the row as-is         ->  {empty_response: 99}
```

So the vocabulary **could** have labelled the old rows `length` — but only by supplying `max_tokens=128`
from the frozen manifest (`longrun/manifests/stage1-lr01-lease-reopen-r1.json:36`), because the row itself
never stored the cap. Without that supply they resolve to `empty_response`. The claim in
`docs/STOP-REASON.md:9` that the seven are "now identifiable by `group by stop_reason`" is **true only
for runs taken after RECORD-STOP-REASON**; for the existing immutable rows it is an offline
re-derivation, not a property of the rows.

---

## Verdicts

| instrument | verdict | my number vs recorded | delta |
|---|---|---|---|
| `request_ledger.py` | **pass** | 1,099 vs 1,101 requests; 3,221 vs 3,219 remaining | −2 (0.18 %), conservative |
| calibrated projection | **partial** | every per-mode wall/ratio identical to `PROJECTION.json`; boundary exact | 0 on numbers; default multiplier mode-blind (3.6×–11.4× under for thinking) |
| `client.STOP_REASONS` | **partial** | 10/10 inducible; 0/1,101 rows carry the field; 1 unreachable member; 1 mislabel path | n/a (coverage + reachability) |
| **overall** | **partial** | — | — |

**Overall is not `pass`** because two instruments carry a gap a future consumer must know about.
**It is not `fail`** because no instrument's *number* is wrong: A over-counts by 2 in the safe direction,
and B and C reproduce their recorded figures exactly — their gaps are about which number is consumed and
which paths are reachable, not about arithmetic that misreports the corpus.

### Which instrument's error would change a decision already made?

- **A — none.** The +2 inflates spend; at worst it refuses a run that would have fitted by ≤2 requests.
- **B — none already made, but the next admission.** `PROJECTION.json` already records the thinking-cell
  refusals correctly (25,662 s > 3,600 s). The risk is that the default admits the same cell when the
  operator does not pass `--projected-from`, contradicting the artefact's own measurement.
- **C — one retrospective claim.** `docs/STOP-REASON.md:9` states the seven cap-exhausted arm-checks are
  now identifiable by `group by stop_reason`. For the 1,101 existing rows that is **false**: the field is
  absent from every one. The claim holds only for future runs, or for an offline re-derivation that
  supplies the cap from the manifest — which is possible and gives `length` for all 99 stage-1 analogues.

## Shas confirmed unchanged at end

```
6eaf221234334d604fef0e54955f70bc94377fd5d58c4fdc8caa85e324b00b95  tools/request_ledger.py
f387c4abbb835f2e28dc641f6ba2ee962dc5b0ee29a25514ac94cdb338a89fc2  longrun/cell.py   (SEE NOTE)
195939a7052c8d405c15a23203745f312357913620b7fd9e3a1e2f58ad2d2feb  longrun/client.py
266406e4f46d2ceda8ecc460f8699152581337061adb2acf54f9c792410be7b9  longrun/run_longrun.py
69305f014a0270bccef2fb8994d7306eb78d729ab854abdb3e97cccab371dbad  measure/PROJECTION.json
e47d6970124627daeee1c042843d57e75f74e1a0d2c7a59b0dc448b581c68fc1  measure/REQUEST-LEDGER.json
4b14ced4572319c2cc209ff1bcca6632d26be0b84d4cb0aba0b28260959c01a3  measure/STOP-REASON.json
3a5ea7057efc1a4da10476d8100965d432aa3ee1642fe66f90bf6e85ed1245f7  rows-*.jsonl (14 files, aggregate)
```

**NOTE — `cell.py` changed under this unit (not by me).** I read and exercised it at sha
`ccda8520bddd09e932ac4a729df60ef0b6cbdb4dc44ae42a1cd59761cbd091e6`; when I re-hashed at the end it was
`f387c4abbb835f2e28dc641f6ba2ee962dc5b0ee29a25514ac94cdb338a89fc2`, mtime `2026-10-26 10:58:15 -05:00`,
65,374 bytes — a concurrent session edited it between my shas call and my final validation. I wrote no
source. **I re-ran the G2 boundary on the current bytes and the behaviour is identical**: `--max-wall`
3601 → (3600, ACCEPT), 3600 → (3600, ACCEPT), 3599 → (3600, REFUSE), `--projected-turn-wall 180` →
(10800, REFUSE). So the B verdict stands on the file as it now exists; the diff itself is outside this
unit (I hold no pristine copy, and the repository is read-only to me). Every other sha above is unchanged
before and after my writes. Nobody should treat this unit's B findings as pinning `cell.py` — pin it by
the sha a fresh unit reads.

No row, grade, settled document or instrument was modified. `PYTHONDONTWRITEBYTECODE=1` +
`sys.dont_write_bytecode=True` throughout, so not even a `__pycache__` entry was written.
