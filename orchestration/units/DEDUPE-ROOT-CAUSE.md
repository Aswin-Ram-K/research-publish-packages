# DEDUPE-ROOT-CAUSE

**Purpose.** Find why one request's response is written twice (or prove it isn't), then give every
row a *request* identity so the ledger's duplicate rule stops comparing responses. Offline; zero
inference requests.

**Bound.** 28 tool calls — **exceeded (≈43)**. The overrun is the exact-line verification loop: every
cited `file:line` was printed and compared against the text before it was quoted, and the first pass
of the evidence tool had the line numbers off until that loop caught them. No extra scope.

**Write paths.** `experiments/ptr-engine/longrun/client.py`, `experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_request_identity.py`, `experiments/ptr-engine/tools/dedupe_root_cause.py`,
`experiments/ptr-engine/measure/DEDUPE-ROOT-CAUSE.json`, `docs/REQUEST-IDENTITY.md`, this card,
`orchestration/handoffs/DEDUPE-ROOT-CAUSE.json`, `orchestration/journals/DEDUPE-ROOT-CAUSE.jsonl`.
**Not** touched: rows files, grade files, `request_ledger.py`, `measure/REQUEST-LEDGER.json`,
`docs/REQUEST-LEDGER.md`, `cell.py`, `TVS.json`, `LATENCY-REPORT.json`.

## Finding — the double append is real: one `resp`, two `make_row` calls

- `run_longrun.py:2045` sends the turn's **initial** request (`resp = send_chat(cfg, planner.messages(info["prompt"]))`);
  `run_longrun.py:2082` counts it with `sent += 1`. It gets no row of its own.
- `run_longrun.py:2092` opens the follow-up path (`if tools_enabled(cfg) and not is_answer_turn:`).
  `fetch_rounds` sends each follow-up (`run_longrun.py:964` `resp = send_chat(cfg, next_messages)`,
  `:965` `sent += 1`), builds a `kind="tool-followup"` row from **that** response (`run_longrun.py:974`)
  and returns the **last** follow-up's `resp` (`run_longrun.py:980`
  `return messages, resp, sent, rounds_used, turn_calls, followups`).
- `run_longrun.py:2106` rebinds `resp` to that return value (`followup_rows) = fetch_rounds(`).
- `run_longrun.py:2167` builds the `kind="turn"` row from the same object
  (`row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,`),
  while `run_longrun.py:2152` still hashes the **initial** prompt
  (`row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))`). Rows are written
  `run_longrun.py:2178` (follow-ups) then `:2179` (turn).

**Condition:** `tools_enabled(cfg) and not is_answer_turn` **and** ≥1 follow-up request granted
(allowance, per-turn round cap and per-arm round budget all clear). With zero follow-ups
`fetch_rounds` returns the incoming `resp` untouched, so the two calls coincide and no mirror is
written.

**Not** a retry: `client.py` has no retry loop, `RequestFailure` writes a failure row and stops the
cell (`run_longrun.py:2076-2083`). **Not** a resume replay: `planner.replay` (`run_longrun.py:1904`)
rebuilds prompt state from existing rows and re-appends nothing. **Not** two writer entry points:
`append_row` has one definition (`run_longrun.py:1686`) and every runner row goes through `make_row`.

**Consequence — a misattribution, not an extra row.** Per turn with *N* follow-ups: *N+1* sends,
*N+1* rows, *N* distinct measurements. The initial send has no measurement of its own, so deducting
the mirror understates spend by one request per pair (30 in total). 33 turns carry follow-ups; the
tuple finds 30 because three pairs landed 1 ms apart on `ts`.

Three of the 30, re-derived independently (`dedupe_root_cause.py`, own loader, own tuple, no import
of the author's helper): v4-tools T1 = 2 rows / 2 sends / **1** measurement; v5-tools T2 = 3 / 3 /
**2**; v6 T1 = 2 / 2 / **1**. Across all decided pairs **30/30** are identical on every measured
field (`ttft_s`, `ttft_ms`, `latency_s`, `wall_ms`, `prompt_tokens`, `completion_tokens`,
`content_sha256`, `finish_reason`), and the only `kind` pair observed is
`tool-followup`/`turn`. Recount: 1,101 rows / 14 files / 30 hash-applicable groups / 30 excess;
41 groups / 54 excess counting the legacy files' naive same-second tuple.

## Fix (identity, not behaviour)

- `client.send_chat` hashes the exact wire bytes — body at `client.py:317-345`, serialised at
  `client.py:656`, hashed at `client.py:660` — and returns `request_sha256` +
  `request_identity_complete` (`client.py:785-786`); a `TurnWallCap` stamps it at the raise site
  (`client.py:716`); a response-shaped failure carries `"unknown"` / `false` (`client.py:292-293`);
  helper `client.request_digest` (`client.py:305`).
- `run_longrun.make_row` writes both fields beside `content_sha256` (`run_longrun.py:1563-1566`) —
  never a guess.
- `run_longrun.append_row` assigns a monotonic per-file `row_seq` **once per row object**
  (`run_longrun.py:1686-1700`, seeded from the file's high-water mark at `:1665`): a re-append keeps
  the seq (the duplicate signature), a re-send takes the next integer.
- The run loop's behaviour (the rebinding at `:2106`) is **not** changed: it moves the row/send
  arithmetic every budget number rests on, and its owner is not this card.

## Proof

`python3 experiments/ptr-engine/longrun/tests/test_request_identity.py` → **17 checks, 0 failed**,
exit 0. (a) two different requests with byte-identical response text get different `request_sha256`
while `content_sha256` collides (the old tuple merges them — RED as designed); (b) same request
re-sent → same hash, `row_seq` 1 then 2; (c) one request whose row is written twice → same hash
**and** same `row_seq`; (d) the historical pair rebuilt with the real writer functions, including a
failure row that keeps `"unknown"` / `false`.

Red→green: `python3 …/test_request_identity.py --red-green` →
`RED with the guards reverted: new identity keeps them apart on the row itself, same object written
twice -> same row_seq, duplicate = same request_sha256 AND same row_seq` then
`RED->GREEN: 3 check(s) red with the identity reverted, all green restored`. The reversion is **in
memory** (`make_row` writes the old response hash; `append_row` re-sequences every write); nothing on
disk is modified to make the test fail.

Neighbours: `unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_*.py'` → 118 tests,
2 failures, both `test_decidability_seam` (`grader decidable=3` vs the cell's `decidable=1`). That
test writes its own `rows.jsonl` (`experiments/ptr-engine/longrun/tests/test_decidability_seam.py:103`) and never imports the
runner's writer — the disagreement is `grade_v5.py:653` vs `analyze_stats.py:457`, outside this
unit's change surface. Recorded, not hidden.

## Historical backfill: 0

14 rows files, 1,101 rows, **0** retaining any part of the request body (`request_sha256` 0,
`request_identity_complete` 0, `row_seq` 0, body 0) → **0** rows can be given a request identity.
The body lives only as a local in `send_chat` and dies with the process; a hash computed now would
be a guess over a reconstructed body. Rows files were not modified (every mtime predates this
session; the artefact records each file's sha256).

## Rule recommendation (not an edit)

Deduct only rows sharing `request_sha256` **and** a `row_seq` that proves one send (same `row_seq`,
or two positions the writer marks as one send); deduct nothing on a row with
`request_identity_complete: false`; equal hash + different `row_seq` = billed re-send, never a
duplicate — and specifically never the 30 historical `tool-followup`/`turn` mirrors; different hash =
distinct requests regardless of `ts`/`content_sha256`/tokens; the old tuple is a candidate detector
that must be confirmed by the identity before any spend is removed; re-publish only after
`request_sha256` has been live for one full live cell, and publish `requests_raw` until then.

## Next

A verifier re-runs the test, re-derives the 30 pairs with its own loader, and checks the rows-file
digests. The runner owner should then decide whether to give the initial send its own row (fixing
`run_longrun.py:2106`/`:2167`) — with `request_sha256` in place, the ledger can read either writer
correctly.
