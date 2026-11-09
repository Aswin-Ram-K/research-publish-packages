# REQUEST-IDENTITY — one row, one request

**Status:** the field contract is live in the writer as of 2026-10-26 (unit `DEDUPE-ROOT-CAUSE`).
Historical rows are **not** backfilled and cannot be.
**Owner of the duplicate rule:** `docs/REQUEST-LEDGER.md` / `measure/REQUEST-LEDGER.json`
(edited this round by `LEDGER-CONSERVATIVE`). This document states the rule the ledger *should*
adopt; it does not edit the ledger, and it does not edit `request_ledger.py`, `cell.py`,
`TVS.json`, `LATENCY-REPORT.json`, any rows file or any grade file.

**Why this document exists.** `V-DUPLICATE-RULE` failed the spend rule on one decisive point: the
ledger's tuple `(ts, content_sha256, prompt_tokens, completion_tokens)` compares **responses**.
`content_sha256` is `sha256(assistant content)` — `experiments/ptr-engine/longrun/run_longrun.py:1555-1556`
(confirmed on **869/869** rows carrying one). Two genuinely different sends that return byte-identical
text are merged by that tuple, and the tuple cannot name *which request* produced a row at all.

---

## 1. The row fields (written from now on)

| field | value | meaning |
|---|---|---|
| `request_sha256` | 64 hex chars, or the string `"unknown"` | `sha256` over the **exact serialized request body handed to the wire**: `model`, `messages`, `temperature`, `max_tokens`, `stream`, `stream_options`, and `chat_template_kwargs` (the thinking switch). The tools are prompt-side, so tool schemas ride inside `messages` and are covered by the digest too. Body built at `client.py:317-344`, serialised at `client.py:656` (`data = json.dumps(body).encode("utf-8")`), hashed at `client.py:660` (`request_sha = hashlib.sha256(data).hexdigest()`) — the *same* `data` object that goes to `urlopen`, so the hash cannot drift from the wire. Helper for callers holding a body: `client.request_digest` (`client.py:305`). |
| `request_identity_complete` | `true` / `false` | `true` only when the wire body was actually hashed for this row. `false` pairs with `"unknown"` and means **the row must not be deduplicated**. |
| `row_seq` | integer, strictly increasing per file | Write position, assigned **once per row object** in `run_longrun.append_row` (`run_longrun.py:1686-1700`), seeded from the file's own high-water mark (`_row_seq_high_water`, `run_longrun.py:1665`). A re-append of the same row keeps its seq; a new row (including a re-send) takes the next integer. |

Carried from the client: `client.py:785-786` returns `request_sha256` / `request_identity_complete`
on the response; a `TurnWallCap` is raised *after* the body went out and stamps the field at
`client.py:716`, so a wall-capped row is still identifiable; a response-shaped failure uses the
`"unknown"` / `false` pair (`client.py:292-293`). Folded onto the row by `make_row`
(`run_longrun.py:1563-1567`) beside `content_sha256` (`run_longrun.py:1555-1556`), which is
untouched and still hashes the response. The two hashes answer different questions: *what did we
get back* and *what did we send*.

`"unknown"` is the only permitted non-hash value. Where the body was not retained (a request that
failed before the client could hash it, a turn refused by the budget, a row written before this
field existed), the row says `"unknown"` / `false`. A plausible-looking hash over reconstructed
inputs is forbidden.

## 2. The double append — found, at `file:line`

There **is** a second write from one response object, one line apart from the first. It is **not** a
retry, not a `--resume` replay, not a writer called from two places. It is the tool-followup path
handing its last response back to the turn that bought it.

| # | site | the line |
|---:|---|---|
| 1 | `run_longrun.py:2045` | `resp = send_chat(cfg, planner.messages(info["prompt"]))` — the turn's **initial** request |
| 2 | `run_longrun.py:2082` | `sent += 1` — the initial send is **counted**, and no row is written yet |
| 3 | `run_longrun.py:2092` | `if tools_enabled(cfg) and not is_answer_turn:` — the follow-up path opens |
| 4 | `run_longrun.py:964` | `resp = send_chat(cfg, next_messages)` — the **follow-up** reaches the wire, `sent += 1` at `:965` |
| 5 | `run_longrun.py:974` | `cfg, fixture, arm, rep, run_id, t, resp, content, "tool-followup", manifest_sha,` — row built from **that** `resp` |
| 6 | `run_longrun.py:980` | `return messages, resp, sent, rounds_used, turn_calls, followups` — the **same object** leaves |
| 7 | `run_longrun.py:2106` | `followup_rows) = fetch_rounds(` — the caller rebinds `resp` to it |
| 8 | `run_longrun.py:2152` | `row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))` — still the **initial** prompt |
| 9 | `run_longrun.py:2167` | `row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,` — the **same** `resp` again |
| 10 | `run_longrun.py:2178-2179` | `append_row(rows_path, frow)` then `append_row(rows_path, row)` |

`make_row` reads `ttft_s`, `latency_s`, `wall_ms`, `prompt_tokens`, `completion_tokens`,
`content_sha256` and `finish_reason` off the `resp` it is handed, so those seven fields are
identical **by construction** — the 6-decimal agreement `V-DUPLICATE-RULE` measured is a code
property, not a coincidence. Every field that differs between the pair (`kind`, `fetch_followup`,
`prompt_sha256`, and in v6 `billed_round`, `prompt_served`, `fetch_rounds_*`) is bookkeeping passed
in `extra`.

**Condition.** `tools_enabled(cfg) and not is_answer_turn`, **and** the turn's first response asked
for at least one `<tool_call>` that was granted a follow-up request (allowance `may_request()`, the
per-turn round cap and the per-arm round budget not spent). With zero follow-ups `fetch_rounds`
returns the incoming `resp` untouched, so the two calls coincide and no mirror appears — which is
why 33 turns carry follow-ups but only 30 pairs were caught: the other 3 pairs landed 1 ms apart,
and the tuple keys on `ts`.

**What it is, precisely — a misattribution, not an extra row.** Per turn with *N* follow-ups there
are *N+1* sends and *N+1* rows, but only *N* distinct measurements: the turn row stands in the
initial send's slot wearing the follow-up's numbers. So the initial send has **no measurement of its
own** in the file, and deducting the mirror row would understate spend by exactly one request. That
is the defect `V-DUPLICATE-RULE` found, stated in the writer's own terms.

Three of the 30, re-derived independently (`experiments/ptr-engine/tools/dedupe_root_cause.py` — own
loader, own tuple, no import of the author's helper; machine-readable in
[`measure/DEDUPE-ROOT-CAUSE.json`](../experiments/ptr-engine/measure/DEDUPE-ROOT-CAUSE.json)):

| file | idx kept/dropped | turn | rows that turn | sends implied | distinct measurements | sends unrepresented |
|---|---|---:|---:|---:|---:|---:|
| `measure/rows-longrun-v4-tools-2026-10-26.jsonl` | 0 / 1 | 1 | 2 | 2 | **1** | **1** |
| `measure/rows-longrun-v5-tools.jsonl` | 3 / 4 | 2 | 3 | 3 | **2** | **1** |
| `measure/rows-longrun-v6-tools.jsonl` | 0 / 1 | 1 | 2 | 2 | **1** | **1** |

In all three, the pair is identical on every measured field and differs only in the bookkeeping
list above (`prompt_sha256` included: `3ffd73d9…` -> `ff82c059…` on v6 T1). Across all 30 decided
pairs: **30/30 identical on every measured field**, and the only `kind` pair observed is
`tool-followup`/`turn`. Recount reproduced: **1,101** rows in 14 files, **30** hash-applicable
groups / **30** excess; **41** groups / **54** excess if the three legacy files' naive same-second
tuple is counted (their `content_sha256` is absent, so they stay outside any hash rule).

**What would have proved the other possibility.** A retry would need a second `send_chat` from the
client: `client.py` has none — it raises `RequestFailure` on every non-HTTPError and the runner
writes a failure row and stops (`run_longrun.py:2076-2083`); `--resume` replays rows through
`planner.replay` (`run_longrun.py:1904`) without re-appending them. The durable discriminator now
exists on the row: **one `request_sha256` on both rows while their `prompt_sha256` differ** — the
follow-up's wire body against the initial prompt. That is what the field records, and it is what a
future reader should check before believing any pair is a rewrite.

**Not fixed here.** The writer still rebinds `resp` at `run_longrun.py:2106` and still builds the
turn row from it at `run_longrun.py:2167`. Changing that moves the row/send arithmetic every budget
number rests on, so it is the runner owner's call, not this unit's. What this unit adds is the
identity that makes the pair unambiguous.

## 3. What the identity proves (the discriminator test)

`experiments/ptr-engine/longrun/tests/test_request_identity.py` — 17 checks, fake stream, fake
clock, `socket.socket` replaced by a raise for the duration of the run (**zero requests**).

| case | request | new identity | old tuple |
|---|---|---|---|
| (a) two **different** requests, byte-identical response text | distinct | different `request_sha256` | **merges them** (the old rule cannot pass this) |
| (b) the **same** request re-sent | one body | same `request_sha256`, **different `row_seq`** | merges them |
| (c) **one** request whose row is written twice | one body | same `request_sha256`, **same `row_seq`** | merges them |
| (d) the historical pair rebuilt with the real `make_row` | one `resp` | same `request_sha256`, different `row_seq`, different `prompt_sha256` | merges them |

Case (a) also asserts the RED premise in the same run: the legacy `content_sha256` **collides** on
the two distinct requests, so the defect is reproduced rather than assumed. A failed row keeps
`"unknown"` + `false`.

So: **duplicate ⇔ same `request_sha256` and a `row_seq` that proves one send**. Two rows sharing
only the hash are either a re-send or one send recorded at two write positions — the pair must be
read by `row_seq` (and `prompt_sha256`/`kind`) before anything is deducted; two rows differing in
`request_sha256` are two requests even when `content_sha256`, `ts` and the token counts coincide.

## 4. The rule the ledger should adopt next (recommendation, not an edit)

Deduct a row as a duplicate only when it shares `request_sha256` with another row **and** a
`row_seq` that proves a single send wrote both (the same `row_seq`, or two positions the writer
itself marks as one send); treat a pair with equal `request_sha256` and different `row_seq` as a
**re-send**, billed, never a duplicate — and specifically never deduct the 30 historical
`tool-followup`/`turn` mirrors, whose two rows stand for two counted sends one of which has no
measurement of its own; deduct **nothing** on a row whose `request_identity_complete` is `false`
(`"unknown"` is not evidence of identity, so all history is non-deductible); treat rows differing
in `request_sha256` as distinct requests even when their `content_sha256`, `ts` and token counts are
identical; and keep the old tuple only as a *candidate detector* that must be confirmed by the
request identity before a single request of spend is removed. Re-publish the deduction only after
`request_sha256` has been live for **one full cell** — rows written from a wire body, counted
against the ledger and reconciled with the engine's own request counter — and publish the
pre-deduction count (`requests_raw`, 1,101) until then.

## 5. Historical rows: **0** could be given a request identity

Measured over all 14 rows files (`measure/rows-*.jsonl`, **1,101** rows): `request_sha256` present
**0**, `request_identity_complete` **0**, `row_seq` **0**, any retained request body **0**. Rows that
could be given a true request identity today: **0**.

The zero is structural, not an oversight: the serialized body exists only as a local in
`send_chat` and dies with the process. A digest computed now would have to reconstruct the body from
the row — `prompt_sha256` hashes one message, not the message list, and `max_tokens`/`thinking`
are not on the row — so it would be a guess dressed as evidence. The rows files, manifests and
grades were not modified; `measure/DEDUPE-ROOT-CAUSE.json` pins their sha256 before/after so a later
reader can prove nothing moved.

Consequence for any future rule: historical rows are **not** deduplicable by request identity, and
no arithmetic may assume they are.

## 6. Verification

```
python3 experiments/ptr-engine/longrun/tests/test_request_identity.py
17 checks, 0 failed
ALL GREEN (and both RED assertions failed as designed)          # exit 0

python3 experiments/ptr-engine/longrun/tests/test_request_identity.py --red-green
RED with the guards reverted: new identity keeps them apart on the row itself,
  same object written twice -> same row_seq, duplicate = same request_sha256 AND same row_seq
RED->GREEN: 3 check(s) red with the identity reverted, all green restored
```

The red state is produced **in memory**: `make_row` is patched to write the old response hash in the
identity field, and `append_row` to take a fresh `row_seq` on every write. Nothing on disk is
modified to make the test fail, and both are restored afterwards.

Neighbours: `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_*.py'`
→ **118 tests, 2 failures**, both in `test_decidability_seam`
(`grader decidable=3` vs the cell's `decidable=1`). Those two are **not** in this unit's change
surface: that test writes its own `rows.jsonl` (`experiments/ptr-engine/longrun/tests/test_decidability_seam.py:103`) and never
imports the runner's writer — the disagreement is between `grade_v5.py:653` and
`analyze_stats.py:457`. Recorded, not hidden; no request was sent to investigate it.
