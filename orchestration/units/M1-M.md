# M1-M — how much of a 200-item prefix survives one edit?

**Status:** done — 99 matrix + 8 diagnostic live requests (107/120), 64 s matrix
span; handoff [`M1-M.json`](../handoffs/M1-M.json).

## Purpose (one)

Measure, on the live Occamy stack, how many cached prompt tokens survive when
**one item of a 200-item (~10k-token) prompt is altered** — and whether the
surviving count equals the token position of the edit, floors to the 64-token
grid, or is 0. Distinguish an **in-place replacement** (same token count, no
shift) from an **insertion** (everything after the edit shifts).

## Fixed design

- Corpus: 200 lines `ITEM 0037: <44 common words>` (deterministic, no clock,
  no `random`), ≈10,000 tokens by the local sizing tokenizer; achieved length
  is whatever the server reports and is recorded on every row.
- Salt: `resextract.context.salt.make_salt(seed)`, placed at the very front of
  a system message (`salted`). Same salt for every request of one rep-pass;
  **fresh salt per rep** → every base prompt is cold. Never `/flush_cache`.
- `client.chat(messages, max_tokens=2, thinking=False, stream=True, timeout=120)`;
  `usage.prompt_tokens_details.cached_tokens`, null → 0.
- One request in flight, strictly serial; lock `experiments/context-cache/.occamy.lock`
  held for the whole run (flock, 300 s timeout; release on exit).

## Cells (n=3 each, fresh salt per rep)

1. **control** — base, then the identical base again → hit?
2. **replacement** — items 10, 50, 100, 165, 190; text of the item word-reversed
   (same multiset ⇒ same token count, no shift). Per rep: base → common-prefix
   probe → edited.
3. **insertion** — one new `ITEM 9999:` item before 10, 50, 100, 165, 190.
   Per rep: base → common-prefix probe → edited.
4. **truncated probe** — folded into replacement@165: after the base, send the
   prompt truncated to items 1..165 (a strict byte prefix of the base) and
   record whether it fully hits. This is the maximum recoverable prefix
   independent of the edit.

The common-prefix probe is `items 1..N-1` (insertion) or
`items 1..N-1 + "ITEM NNNN: "` (replacement): its `prompt_tokens` **is** the
edit position, and its `cached` tests whether a pure prefix of a warm prompt
hits at all.

## Hard bounds

- ≤120 live chat requests (planned 99 + ≤3 control retries), ≤20 min wall.
- One attempt; if the endpoint is unreachable or the lock is busy for 300 s,
  STOP and write a `blocked` handoff.
- Rows appended to `rows.jsonl` and fsynced before the next request; on
  restart a (series, item, rep) cell is skipped only when complete.

## Write paths

- `experiments/context-cache/cells/M1-M/**`
- `orchestration/handoffs/M1-M.json`
- `orchestration/units/M1-M.md`

No `src/` or `tests/` edit.

## Results (measured, 2026-10-21T05:17Z–05:26Z)

Achieved base prompt: 10,442–10,446 tokens (200 items, `ITEM 0037:` headers);
`prompt_token_details` null → 0 on every cold send.

| series | cell | edit position (tokens) | cached | Δ vs position |
| --- | --- | --- | --- | --- |
| control | rep 0/1/2 | 10,446 / 10,445 / 10,444 | 10,432 (all three) | −14 / −13 / −12 |
| replacement | item 10 | 521 / 519 / 519 | 512 / 448 / 448 | −9 / −71 / −71 |
| replacement | item 50 | 2601 / 2599 / 2599 | 2560 / 2560 / 2560 | −41 / −39 / −39 |
| replacement | item 100 | 5201 / 5199 / 5199 | 5184 / 5184 / 5184 | −17 / −15 / −15 |
| replacement | item 165 | 8581 / 8579 / 8579 | 8512 / 8512 / 8512 | −69 / −67 / −67 |
| replacement | item 190 | 9881 / 9879 / 9879 | 9856 / 9856 / 9856 | −25 / −23 / −23 |
| insertion | before 10 | 514 / 513 / 510 | 448 / 448 / 448 | −66 / −65 / −62 |
| insertion | before 50 | 2594 / 2593 / 2590 | 2560 / 2560 / 2560 | −34 / −33 / −30 |
| insertion | before 100 | 5194 / 5193 / 5190 | 5184 / 5184 / 5120 | −10 / −9 / −70 |
| insertion | before 165 | 8574 / 8573 / 8570 | 8512 / 8512 / 8512 | −62 / −61 / −58 |
| insertion | before 190 | 9874 / 9873 / 9870 | 9856 / 9856 / 9856 | −18 / −17 / −14 |

**Answers.**

1. **Control: 3/3 hit**, but never literally to the last token. A byte-identical
   repeat reports `cached = prompt − prompt % 64` (10,432), i.e. the trailing
   partial 64-token page is never counted. "Hit" on this stack = page-aligned
   full reuse, not `cached == prompt_tokens`.
2. **`cached` never equals the edit position** (positions are never multiples
   of 64) and **is never 0**. All 30 edited-prompt `cached` values are exact
   multiples of 64: **22/30 equal `floor64(position)`**, **8/30 are exactly one
   64-block lower** (`floor64 − 64`). So the answer to "floored to 64" is
   *yes, page-aligned*, with a one-block granularity in which value is chosen;
   the measured spread is 0 or −64 relative to the floor, never in between.
3. **Replacement and insertion behave identically** at the same position: both
   recover the same page-aligned prefix. An insertion does **not** preserve the
   shifted tail — the whole 10.4k-token suffix after the insertion is
   re-prefilled. The only difference is mechanical: an in-place word-reversal
   keeps the edit at the item's header, so its position sits 5–9 tokens into
   the next 64-block (and so floors one block lower at item 165); a
   before-item insertion sits at the end of the previous item.
4. **Truncation alone does not hit on the first send.** A prompt cut to items
   1..165 (8,623–8,625 tokens) sent right after its warm base recovered only
   8,192 tokens (3/3 reps). A retry diagnostic then showed the second and
   third identical sends recover **8,576/8,623 = floor64** — and at 10,394
   tokens the first send again stopped at exactly **8,192**, the repeats at
   **10,368 = floor64**. First-send truncation recovery is capped at 8,192;
   the page-aligned maximum (`floor64` of the truncated length) appears only
   on a repeat.

Invariants over all 99 matrix rows: `cached % 64 == 0` (99/99),
`cached <= prompt_tokens` (99/99).

Anomalies recorded: none (no exact-multiple-of-64 base prompt, so no warm-twice
retry was needed; no cold-start contract violation).
