# DUPLICATE-ATTACK — independent audit of the duplicate rule

Verifier unit `V-DUPLICATE-RULE`. The rule under attack lives in
`orchestration/handoffs/TVS-REGRADE.json` → `duplicate_rows`: **within one file**, two rows
are duplicates iff they share `(ts, content_sha256, prompt_tokens, completion_tokens)`;
first kept. Claimed result 41 groups · 54 excess · 30 decided · `excess_defensible` 30, so
spend 1,101 → 1,071 and remaining 3,219 → 3,249.

Independent re-derivation: `experiments/ptr-engine/tools/duplicate_attack.py` (own loader,
own tuple, no import of the author's helper, read-only). Run from the repo root:

```
python3 experiments/ptr-engine/tools/duplicate_attack.py          # human summary
python3 experiments/ptr-engine/tools/duplicate_attack.py --json   # machine evidence
```

---

## Attack 1 — recompute 41 / 54 / 30 / 30

**Reproduced exactly.** 14 files, 1,101 rows, 41 groups, 54 excess, 30 decided groups with
30 excess. Every decided group is size 2, so no decided file has a group with excess > 1.

| file | rows | groups | excess | decided |
|---|---:|---:|---:|---|
| rows-longrun-v6-tools.jsonl | 72 | 11 | 11 | yes |
| rows-longrun-v4-tools-2026-10-26.jsonl | 68 | 17 | 17 | yes |
| rows-longrun-v5-tools.jsonl | 72 | 2 | 2 | yes |
| rows-longrun-2026-10-26.jsonl | 192 | 0 | 0 | yes |
| rows-longrun-c-2026-10-26.jsonl | 192 | 0 | 0 | yes |
| rows-longrun-v3-2026-10-26.jsonl | 96 | 0 | 0 | yes |
| rows-longrun-v4-2026-10-26.jsonl | 96 | 0 | 0 | yes |
| rows-longrun-2026-10-26-fix.jsonl | 29 | 0 | 0 | yes |
| rows-longrun-2026-10-26-policy.jsonl | 40 | 0 | 0 | yes |
| rows-baseline-2026-10-26.jsonl | 105 | 1 | 11 | **no** (legacy) |
| rows-equalinfo-2026-10-26.jsonl | 100 | 2 | 2 | **no** (legacy) |
| rows-live-2026-10-26.jsonl | 27 | 8 | 11 | **no** (legacy) |
| rows-cell-pointer-stable-20261026T145758Z.jsonl | 6 | 0 | 0 | yes |
| rows-pilot-thinking-2026-10-26.jsonl | 6 | 0 | 0 | yes |

The three legacy files are only "grouped" for comparison; `attack4` explains why the literal
tuple must not be applied to them. Groups with excess > 1 (all in skipped files, listed in
full because the card asked): baseline `[48,49,50,51,52,53,54,55,56,57,58,59]`,
live `[13,14,16,17]`, live `[21,22,23]`. **No decided group exceeds 1.**

Verdict: **sound** — the arithmetic is not the defect.

## Attack 2 — is a dropped row a second attempt?

For each of the 30 dropped rows, every field outside the tuple was compared with its kept row:
`turn, rep, arm, kind, latency_s, wall_ms, ttft_s, ttft_ms, http_status, error, tool_calls,
fetch_followup, billed_round, prompt_served, prompt_sha256, max_tokens, finish_reason,
stop_reason, reasoning_sha256, run_id` plus `attempt`/`msg_index`/`started_at` when present.

**30/30 have identical `ttft_s` and `latency_s` to six decimals**, and identical
`prompt_tokens`, `completion_tokens`, `content_sha256`. Two independent HTTP round trips cannot
share a client-measured TTFT and latency to 1e-6 s, so none of the 30 is a retry. The only
differing fields are bookkeeping: `kind`, `fetch_followup`, `prompt_sha256`, and in v6
`billed_round`/`prompt_served`, occasionally `tool_calls`.

Verdict: **sound for the retry question — and this is exactly why it is dangerous.** The rows
are one measurement recorded twice; the question the spend depends on is a different one
(attack 5).

## Attack 3 — what does `content_sha256` hash?

Re-hashing each row's own payloads: **869 of 869** rows with a `content_sha256` equal
`sha256(content)`; 0 equal anything else. Writer:
`experiments/ptr-engine/longrun/run_longrun.py:1493` —

```python
"content_sha256": (sha256_text(recorded_content) if recorded_content is not None else None),
```

It hashes the **assistant response content**. It encodes nothing about `max_tokens`, `tools`,
`thinking`, or the message list (those live in separate fields; `prompt_sha256` is a different
hash). Therefore identical tuples are proof of *one HTTP response written twice*, not of *one
request*, and the error direction of dedupe is to **understate** spend. This is the hinge the
author's "cause: writer bug" gets right and then reads backwards.

Verdict: **unsound as request identity.**

## Attack 4 — the `not_applicable` half

Premise in the card ("applied on 9 of 14, skipped on 5") and in the handoff prose ("the 5
legacy-schema files") **does not reproduce**. The handoff's own table, `REQUEST-LEDGER.json`
(`files_deduped: 11`, `files_not_applicable: 3`) and this recount all say **11 applied /
3 skipped**:

| skipped file | rows | `content_sha256` present | ts resolution | naive tuple groups / excess |
|---|---:|---|---|---:|
| rows-baseline-2026-10-26.jsonl | 105 | 0 | `ts_utc`, seconds | 1 / 11 |
| rows-equalinfo-2026-10-26.jsonl | 100 | 0 | `ts_utc`, seconds | 2 / 2 |
| rows-live-2026-10-26.jsonl | 27 | 0 | `ts_utc`, seconds | 8 / 11 |

**232 rows are left uncorrected.** The skip is nevertheless defensible, and demonstrably so:
every same-second same-token group there is a set of *distinct sends*. baseline rows 48–59 are
12 identical `HTTP 400: "auto" tool choice requires --enable-auto-tool-choice...` failures
across `rep` 1/2/3; equalinfo 7/11 are `rep` 2 and 3 with `latency_s` 0.324 vs 0.323, and 90/91
are `rep` 1 and 2 with `latency_s` 7.312 vs 0.593; every live group differs in `rep` and
`client_elapsed_s`. Applying the tuple naively would fabricate 24 merges, as the author wrote.
What is **unverified** is whether those 232 rows hide a true mirror: with no content hash and a
one-second clock, it is not decidable from the rows.

Verdict: **skip sound; the file count in the prose is wrong; completeness unverified.**

## Attack 5 — the request-count audit (the finding)

`fetch_rounds()` sends each follow-up and appends one row per send
(`run_longrun.py:965` `sent += 1`; row built at `:974` with
`prompt_sha256=sha256_text(next_messages[-1]["content"])`). The main loop sends and counts the
turn's **initial** request (`run_longrun.py:1969` `sent += 1`), then appends the follow-up rows
and finally the turn row **from the same `resp` object** `fetch_rounds` returned
(`run_longrun.py:2065-2066`). The turn row's prompt hash is the initial prompt
(`:2039`, `prompt_sha256=sha256_text(info["prompt"])`), but every measurement on it is the
last follow-up's.

So for a turn with N follow-ups: **N+1 sends, N+1 rows** — and the initial send has no row of
its own. The row count already equals the send count (1,101), and the pair is the mirror of
follow-up N replacing the unrecorded initial send, not an extra row. Removing the 30 mirrors
therefore leaves 30 billed sends with no representative: **1,071 understates sends by 30.**

Three mirrors escape the tuple entirely, because `make_row` stamps `ts` per call and the two
calls landed 1 ms apart — evidence that the rule is *incomplete in detection* as well:

| file | turn | rows | ts follow-up / turn | same measurement? |
|---|---:|---|---|---|
| rows-longrun-v6-tools.jsonl | 4 | 8/9 | 13:16:31.644 / .645 | yes |
| rows-longrun-v6-tools.jsonl | 13 | 28/29 | 13:19:39.946 / .947 | yes |
| rows-longrun-v5-tools.jsonl | 1 | 0/1 | 12:17:29.765 / .766 | yes |

33 turns carry follow-ups (v6 13, v4-tools 17, v5-tools 3) and only 30 pairs were found.

Consequence: a fixed writer would emit one row per send — 1,101 rows, no mirrors — and a
correct de-duplication of that row set would return 1,101. **1,071 is the fixpoint of a writer
bug that has not been fixed**, which is why no re-publication on the deduplicated figure can be
correct while `run_longrun.py:2065-2066` still appends the turn row from the follow-up's
response.

Verdict: **unsound as applied.** Remaining budget is **3,219**, not 3,249.

---

## The 30 dropped rows

`prompt_sha` columns are the first 12 hex chars; `differs` lists every non-tuple field whose
value differs between kept and dropped.

| # | file | kept/dropped idx | turn | ts (ms) | ptok | ctok | content_sha | prompt_sha kept -> dropped | ttft_s | latency_s | differs |
|---:|---|---|---:|---|---:|---:|---|---|---:|---:|---|
| 1 | longrun-v4-tools-2026-10-26 | 0/1 | 1 | 2026-10-26T11:55:35.461Z | 3033 | 71 | `5d956fe4c8dd` | `685263b1c58f` -> `ff82c059835d` | 0.526405 | 2.872481 | fetch_followup, kind, prompt_sha256 |
| 2 | longrun-v4-tools-2026-10-26 | 2/3 | 2 | 2026-10-26T11:55:41.188Z | 3801 | 111 | `b94742131e46` | `685263b1c58f` -> `e4bf02b57ee4` | 0.318143 | 4.00401 | fetch_followup, kind, prompt_sha256 |
| 3 | longrun-v4-tools-2026-10-26 | 4/5 | 3 | 2026-10-26T11:55:46.590Z | 4274 | 84 | `f2b5e9876d54` | `768ee9128a72` -> `6c2552ee32eb` | 0.282976 | 3.070827 | fetch_followup, kind, prompt_sha256 |
| 4 | longrun-v4-tools-2026-10-26 | 6/7 | 4 | 2026-10-26T11:55:51.489Z | 4345 | 40 | `34861af62e2f` | `768ee9128a72` -> `347eedaf8993` | 0.222016 | 1.530747 | fetch_followup, kind, prompt_sha256 |
| 5 | longrun-v4-tools-2026-10-26 | 8/9 | 5 | 2026-10-26T11:57:23.012Z | 4384 | 63 | `066e66a841a4` | `768ee9128a72` -> `b5f16e0a3f6b` | 0.221571 | 2.672379 | fetch_followup, kind, prompt_sha256 |
| 6 | longrun-v4-tools-2026-10-26 | 11/12 | 7 | 2026-10-26T11:57:33.379Z | 4294 | 122 | `23d490d72ba8` | `685263b1c58f` -> `4be6cf1d146f` | 0.202151 | 4.995698 | fetch_followup, kind, prompt_sha256 |
| 7 | longrun-v4-tools-2026-10-26 | 13/14 | 8 | 2026-10-26T11:57:37.881Z | 4310 | 60 | `9f36fdf273f8` | `685263b1c58f` -> `e65b468ff831` | 0.198171 | 2.535539 | fetch_followup, kind, prompt_sha256 |
| 8 | longrun-v4-tools-2026-10-26 | 15/16 | 9 | 2026-10-26T11:57:43.060Z | 4336 | 63 | `e29c6372d1a2` | `768ee9128a72` -> `395dda171de6` | 0.165326 | 2.618835 | fetch_followup, kind, prompt_sha256 |
| 9 | longrun-v4-tools-2026-10-26 | 17/18 | 10 | 2026-10-26T11:57:47.842Z | 4318 | 57 | `f78cd47f78b7` | `768ee9128a72` -> `a2d2cbf26490` | 0.211727 | 2.426108 | fetch_followup, kind, prompt_sha256 |
| 10 | longrun-v4-tools-2026-10-26 | 19/20 | 11 | 2026-10-26T11:57:54.603Z | 4320 | 85 | `b5e431e9b743` | `685263b1c58f` -> `84ad40a26fdf` | 0.204617 | 3.538168 | fetch_followup, kind, prompt_sha256 |
| 11 | longrun-v4-tools-2026-10-26 | 22/23 | 13 | 2026-10-26T11:58:06.119Z | 4284 | 97 | `513b30274465` | `685263b1c58f` -> `56f3f7f36874` | 0.202286 | 4.016421 | fetch_followup, kind, prompt_sha256 |
| 12 | longrun-v4-tools-2026-10-26 | 24/25 | 14 | 2026-10-26T11:58:09.768Z | 4303 | 51 | `bb34b9f99ae8` | `ed0b5461798f` -> `d513bcfbd9c7` | 0.173105 | 2.161589 | fetch_followup, kind, prompt_sha256 |
| 13 | longrun-v4-tools-2026-10-26 | 36/37 | 25 | 2026-10-26T12:02:08.467Z | 4288 | 74 | `dffd9c675931` | `685263b1c58f` -> `da666e52965f` | 0.171733 | 2.74119 | fetch_followup, kind, prompt_sha256 |
| 14 | longrun-v4-tools-2026-10-26 | 39/40 | 27 | 2026-10-26T12:02:15.297Z | 4298 | 54 | `b087673abcbb` | `768ee9128a72` -> `00e51a70d7f2` | 0.172622 | 2.040582 | fetch_followup, kind, prompt_sha256 |
| 15 | longrun-v4-tools-2026-10-26 | 41/42 | 28 | 2026-10-26T12:02:23.010Z | 4347 | 93 | `913f6d749e9c` | `768ee9128a72` -> `d4b29ed1d120` | 0.212609 | 3.454359 | fetch_followup, kind, prompt_sha256 |
| 16 | longrun-v4-tools-2026-10-26 | 43/44 | 29 | 2026-10-26T12:02:29.145Z | 4295 | 87 | `e3f5c5df286c` | `685263b1c58f` -> `5a39b3bebee5` | 0.20861 | 3.236008 | fetch_followup, kind, prompt_sha256 |
| 17 | longrun-v4-tools-2026-10-26 | 48/49 | 30 | 2026-10-26T12:03:02.558Z | 5165 | 268 | `8065c0124e51` | `ed0b5461798f` -> `79ef778a8295` | 0.20396 | 7.650749 | fetch_followup, kind, prompt_sha256, tool_calls |
| 18 | longrun-v5-tools | 3/4 | 2 | 2026-10-26T12:17:49.893Z | 5614 | 441 | `4aa24cfd5e39` | `5095d7baa9fe` -> `86d135127cd5` | 0.454734 | 12.742209 | fetch_followup, kind, prompt_sha256, tool_calls |
| 19 | longrun-v5-tools | 25/26 | 3 | 2026-10-26T12:18:49.027Z | 9771 | 1146 | `f0b37db7b755` | `ed0b5461798f` -> `7e5e038cdcbe` | 0.156262 | 33.328267 | fetch_followup, kind, prompt_sha256, tool_calls |
| 20 | longrun-v6-tools | 0/1 | 1 | 2026-10-26T13:16:13.529Z | 3520 | 288 | `eb8791454799` | `3ffd73d90220` -> `ff82c059835d` | 0.192567 | 8.057474 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |
| 21 | longrun-v6-tools | 4/5 | 3 | 2026-10-26T13:16:21.851Z | 5587 | 13 | `4eb1d4a521f0` | `bdc884599fb5` -> `60bdc3fd3acb` | 0.21508 | 0.550735 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256, tool_calls |
| 22 | longrun-v6-tools | 12/13 | 7 | 2026-10-26T13:18:40.041Z | 4732 | 279 | `30ce79cc36d0` | `3ffd73d90220` -> `acecdc95d1f5` | 0.208654 | 7.964046 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |
| 23 | longrun-v6-tools | 14/15 | 8 | 2026-10-26T13:18:52.489Z | 4404 | 405 | `ad4eaa6d503c` | `d53acdf2dd4d` -> `ef6b96725469` | 0.168073 | 11.398331 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |
| 24 | longrun-v6-tools | 18/19 | 9 | 2026-10-26T13:19:07.031Z | 6982 | 118 | `a4dc6b9d1255` | `4d23b8219a86` -> `06ddd93d7353` | 0.309174 | 3.624833 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256, tool_calls |
| 25 | longrun-v6-tools | 22/23 | 10 | 2026-10-26T13:19:19.817Z | 7816 | 87 | `58d250506953` | `68752cef2d66` -> `d14276a0d3fb` | 0.529892 | 2.882796 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256, tool_calls |
| 26 | longrun-v6-tools | 24/25 | 11 | 2026-10-26T13:19:23.984Z | 5154 | 59 | `c4eb2210e56a` | `105325615b44` -> `82fe1f1a625a` | 0.252478 | 1.887003 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |
| 27 | longrun-v6-tools | 26/27 | 12 | 2026-10-26T13:19:26.841Z | 4480 | 37 | `4669c245e85d` | `d4da59a6b06a` -> `ff49a7e2b29d` | 0.158187 | 1.165148 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |
| 28 | longrun-v6-tools | 33/34 | 15 | 2026-10-26T13:19:51.968Z | 6840 | 153 | `a1061b43ad98` | `a476e64032e8` -> `0e6e63b95356` | 0.378835 | 4.581119 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256, tool_calls |
| 29 | longrun-v6-tools | 37/38 | 16 | 2026-10-26T13:19:58.762Z | 6147 | 13 | `4eb1d4a521f0` | `685263b1c58f` -> `04792705714a` | 0.175631 | 0.514918 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256, tool_calls |
| 30 | longrun-v6-tools | 68/69 | 46 | 2026-10-26T13:23:44.625Z | 4803 | 58 | `ecdb3fc9d9f0` | `b8d74bda182c` -> `3afe9abf9ac0` | 0.216018 | 1.816664 | billed_round, fetch_followup, kind, prompt_served, prompt_sha256 |

Reading of the table: every pair is `kind=tool-followup` kept and `kind=turn` dropped, with
identical `ttft_s`/`latency_s`/prompt/completion counts and identical `content_sha256`, and a
**different** `prompt_sha256` — the dropped row claims the initial prompt's hash while wearing
the follow-up's measurement. That internal contradiction is the citation that the initial send
is not represented anywhere in the file.

## What the operator has to decide

If the 30 were sound, the project would believe that 1,101 requests were sent but only 1,071
were billed, and every "what can we afford" answer since round 40 would gain 30 requests of
room. They are not: none of the 30 is a retry (attack 2), but each is the only row standing in
for a turn's initial send, which the writer never wrote separately (attack 5). The number that
replaces 1,071 is **1,101**, remaining **3,219** (the file already carries both as
`requests_raw` / `remaining_raw`), and what must be un-published is the dedup-adjusted
`requests`/`budget.spent`/`projected`/`remaining` triple in `REQUEST-LEDGER.json` (and in any
`REQUEST-LEDGER-2` derived from it), `TVS-REGRADE.json`'s `excess_defensible: 30` /
`dedup_requests: 1071`, and `LATENCY-REPORT-2`'s G7 `pointer-stable V4-TOOLS 68 -> 51`
threshold crossing — dedupe changes the latency *sample set*, so n must stay 68 and the
"crosses threshold downward" claim must be withdrawn rather than republished. `RUN-A*`'s
precondition 6 (`remaining >= 900`) still passes at 3,219, with 30 fewer requests of margin.
The 30 rows remain defensible to drop from **token sums** (a duplicated measurement should not
be counted twice in a window), which is why `TVS.json`'s window arithmetic is not automatically
wrong — but the same rule must not be used to count requests, and the initial send's tokens are
missing from every total either way.
