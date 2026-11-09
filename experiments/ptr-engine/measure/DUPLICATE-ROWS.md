# Duplicate rows — the defect measured across all 14 rows files

**Unit:** `TVS-REGRADE`. **Offline:** zero inference requests, zero network. **Nothing was edited** except the two TVS artefacts the definition tells this unit to rewrite: no rows file, no existing grade file, no `REQUEST-LEDGER.json`, no `LATENCY-REPORT.json`. Everything below is a re-read of existing rows.

## 1. The rule, defined before counting

**Rule R:** within one rows file, two rows are duplicates iff they share an identical tuple
`(ts, content_sha256, prompt_tokens, completion_tokens)`.
The first occurrence is kept, the rest are excess. A file's de-duplicated request count is `rows − excess`.

**Applicability, discovered while applying it (this matters):** R can only decide a file that actually carries a `content_sha256` and a millisecond `ts`. Five of the 14 files use the older schema — they have **no `content_sha256` field** and their timestamp is `ts_utc` at **one-second resolution**. Applying R there collapses rows that are demonstrably different requests (different `rep`, different `latency_s`/`ttft_server_s`), i.e. it manufactures duplicates. So R is reported **as decided only on the 9 rows files that carry `content_sha256`**; on the 5 legacy files the honest answer is `rule_not_applicable`, and the defensible duplicate count is **0** (proved below).

**What R cannot distinguish:**

- A genuine double-send with an identical prompt *and* an identical completion. Two calls can in principle return the same text, but they cannot share a client-measured `ttft_s`/`latency_s` to six decimals *and* the same millisecond `ts`, so this case is possible but improbable — and it is not what these rows are (§6).
- A retried request (it would carry a new `ts`), and a resumed run re-recording a turn (new `ts`, new measurement) — R does **not** catch either, by design.
- R is blind to *near*-duplicates: same request, re-tokenised or re-serialised (different `content_sha256`). None were found; the counts below are a floor, not a ceiling.
- R cannot say **which** copy is the write and which is the artefact; §6 answers that from the non-key fields.

## 2. Per file — rows · duplicate groups · excess · raw vs de-duplicated

| # | rows file | rows | dup groups | excess | raw → de-duplicated | rule status |
|---|---|---|---|---|---|---|
| 1 | `rows-longrun-v6-tools.jsonl` | 72 | 11 | **11** | 72 → **61** | decided |
| 2 | `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 17 | **17** | 68 → **51** | decided |
| 3 | `rows-longrun-v5-tools.jsonl` | 72 | 2 | **2** | 72 → **70** | decided |
| 4 | `rows-longrun-2026-10-26.jsonl` | 192 | 0 | 0 | 192 → 192 | decided |
| 5 | `rows-longrun-c-2026-10-26.jsonl` | 192 | 0 | 0 | 192 → 192 | decided |
| 6 | `rows-longrun-v3-2026-10-26.jsonl` | 96 | 0 | 0 | 96 → 96 | decided |
| 7 | `rows-longrun-v4-2026-10-26.jsonl` | 96 | 0 | 0 | 96 → 96 | decided |
| 8 | `rows-longrun-2026-10-26-fix.jsonl` | 29 | 0 | 0 | 29 → 29 | decided |
| 9 | `rows-longrun-2026-10-26-policy.jsonl` | 40 | 0 | 0 | 40 → 40 | decided |
| 10 | `rows-baseline-2026-10-26.jsonl` | 105 | 1 | 11 | 105 → 105 (**0** defensible) | **rule_not_applicable** |
| 11 | `rows-equalinfo-2026-10-26.jsonl` | 100 | 2 | 2 | 100 → 100 (**0** defensible) | **rule_not_applicable** |
| 12 | `rows-live-2026-10-26.jsonl` | 27 | 8 | 11 | 27 → 27 (**0** defensible) | **rule_not_applicable** |
| 13 | `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 0 | 0 | 6 → 6 | decided |
| 14 | `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 0 | 0 | 6 → 6 | decided |
| | **all 14** | **1,101** | **41 (30 decided)** | **54 (30 decided)** | **1,101 → 1,071** | — |

The 30 decided duplicates are **all** in the three tool-era grids — the same 11 / 17 / 2 the prior unit found, now with the applicability boundary stated. The 54 "raw under R" figure is shown only so the number is auditable; the defensible excess is **30**.

**Why the 5 legacy files are not duplicates (the proof).** The literal tuple collapses because the fields are absent, not because the requests repeat:

- `rows-baseline-2026-10-26.jsonl` group at `ts_utc=2026-10-26T05:49:00Z`, indices 48-59: 12 rows, all HTTP 400 errors — `rep` 1,2,3 × `turn` 1,2,3,4, every token field `null`, no `content_sha256` at all. Twelve distinct failed requests inside one clock second. The key matched on `(ts_utc, None, None, None)`.
- `rows-equalinfo-2026-10-26.jsonl` indices 7 & 11: `rep` 2 vs `rep` 3, `latency_s` 0.324 vs 0.323 — two calls, not one.
- `rows-live-2026-10-26.jsonl` indices 0 & 2: `rep` 0 vs 1, `client_elapsed_s` 0.1399 vs 0.1393 — two calls, and the file has `nonce_sha`, not `content_sha256`.

## 3. Impact on `REQUEST-LEDGER` — raw 1,101 → **1,071**

| quantity | raw (as published) | de-duplicated |
|---|---|---|
| requests counted across the 14 files | **1,101** | **1,071** (−30, −2.7%) |
| budget remaining (cap 4,320) | 4,320 − 1,101 = **3,219** | 4,320 − 1,071 = **3,249** |
| `assumed_billed` (rows with no `kind`) | 232 | **232 (unchanged)** — all 232 live in the legacy files, which carry no duplicates |

**A second, larger discrepancy the same read exposes** — reported, not republished: the ledger's rule says it counts `kind in {turn, tool-followup}` and excludes `billed:false`, `followup_suppressed`, `served_from:prompt`. The rows actually carry **`billed_round: false`**, **`fetch_followup: true`** and **`prompt_served: 1`** — none of which match the ledger's exclusion marker names. So the ledger counts all **68** `kind=tool-followup` rows as billed requests (v4-tools 20, v5-tools 24, v6 24), of which **30 are the duplicate mirrors** counted again and **4 (v6) are explicitly marked `billed_round: false`** by the writer itself. A correct billed count needs the marker names reconciled, not just de-duplication; that decision belongs to the follow-up card.

## 4. Impact on `LATENCY-REPORT` — n per cell

`p95` requires n ≥ 60; `p50` requires n ≥ 20. Every duplicate pair carries **one** usable latency measurement (`ttft_s`, `latency_s` identical on both copies), so de-duplication removes one sample per excess row, in exactly three cells — all `pointer-stable`, all in the tool-era grids:

| grid | cell (label) | n now | n after dedup | crosses n ≥ 60? |
|---|---|---|---|---|
| G7 | `pointer-stable` / V4-TOOLS | **68** | **51** | **YES — falls below 60.** This cell reaches the p95 threshold *only* by counting duplicates; its published p95 must be treated as duplicate-inflated and re-derived (or the cell refused at n=51) by a follow-up card |
| G8 | `pointer-stable` / V5-TOOLS | **72** | **70** | no — stays above, by 10 |
| G9 | `pointer-stable` / V6-TOOLS | **72** | **61** | no — but by **1** sample (72→61); fragile, named here |
| G1 | all 4 arms / stage1 | 0 | 0 | unchanged; already refused (no usable latency samples) |
| G4 | all 4 arms / RUN-C-V2 | 48 | 48 | unchanged; already below 60, p95 refused |
| G5 | both arms / V3 | 48 | 48 | unchanged; already below 60, p95 refused |
| G6 | both arms / V4 | 48 | 48 | unchanged; already below 60, p95 refused |
| G2 | 4 arms / smoke-rp | 3, 3, 3, 31 | unchanged | all below 60, unchanged |
| G3 | 4 arms / fix-smoke | 3, 3, 5, 18 | unchanged | all below 60, unchanged |
| G10 | `pointer-stable` / CELL-145758Z | 6 | unchanged | below 60, unchanged |

**No cell gains n from de-duplication** (a duplicate can only remove a sample). Exactly **one published p95 cell — G7, V4-TOOLS, `pointer-stable` — is duplicate-inflated across the n ≥ 60 boundary**; G9 is duplicate-inflated but survives by a single sample.

## 5. Rows inspected

- `rows-longrun-v6-tools.jsonl` lines 1-2 (indices 0,1): `ts=2026-10-26T13:16:13.529Z`, turn 1, prompt 3,520 / completion 288, `content_sha256=eb879145…d0138a`, `ttft_s=0.192567`, `latency_s=8.057474` on both.
- `rows-longrun-v4-tools-2026-10-26.jsonl` lines 1-2 (indices 0,1): `ts=2026-10-26T11:55:35.461Z`, turn 1, prompt 3,033 / completion 71, `content_sha256=5d956fe4…603583d`, `ttft_s=0.526405`, `latency_s=2.872481` on both.
- `rows-longrun-v5-tools.jsonl` lines 4-5 (indices 3,4): `ts=2026-10-26T12:17:49.893Z`, turn 2, prompt 5,614 / completion 441, `content_sha256=4aa24cfd…def80e9`, `ttft_s=0.454734`, `latency_s=12.742209` on both.
- The five legacy files, all groups listed in §2 — inspected field by field to show they are distinct requests.

## 6. Cause: **writer bug** — the same billed response recorded twice

**Verdict: `writer bug`, not a harness artefact (not a resumed-run re-record).** Evidence:

1. **All 30 decided duplicate pairs have the shape `(kind: "tool-followup", kind: "turn")`** — 11/11 in v6, 17/17 in v4-tools, 2/2 in v5-tools. Nothing else duplicates.
2. **The two copies are the same measurement, not two measurements.** Identical `ts` to the millisecond, and identical client-measured `ttft_s` and `latency_s` to six decimals. Two HTTP round-trips cannot share a client-measured latency; a resumed run would carry a fresh `ts` and a fresh latency and would not sit adjacent inside one `rep`.
3. **They differ only in bookkeeping fields**: `kind`, `prompt_sha256`, `fetch_followup: true`, `fetch_rounds_this_turn`, and — in v6 only — `prompt_served: 1`, `billed_round: false`, `fetch_prompt_serves: 1`. Same `content_sha256`, same `content`, same token counts. The writer is emitting the turn's response twice: once as the turn record and once as the fetch-round ("tool-followup") record for the same message.
4. The `billed_round: false` marker on 4 of the 24 v6 followup rows shows the **writer knew those rows were not separately billed** — yet wrote them as rows that the ledger's kind-based rule counts as requests. That is a writer/ledger defect, not an inference defect: the wire saw one request, the file has two rows.

What this is **not**: not evidence of double-billing by the provider (the token counts and cached tokens are identical, i.e. one response's usage object), and not a replayed run. It is a **double write of one request**, and it is confined to the tool-calling grids — the six long-run grids without tool follow-ups record zero duplicates.

## 7. What is left for a follow-up card (this unit publishes nothing)

- `REQUEST-LEDGER.json`: 1,101 → 1,071 requests, remaining 3,219 → 3,249; plus the marker-name reconciliation of §3 (68 `tool-followup` rows, 4 self-marked `billed_round:false`) — a *decision*, not arithmetic, so it is left unedited here.
- `LATENCY-REPORT.json`: G7 `pointer-stable` p95 must be re-derived at n=51 (refused) or reported as duplicate-inflated; G8/G9 n resolve to 70/61.
- The v6 TVS window is **155,955 raw → 111,994 de-duplicated = 1.39×**, not the ~1.8× previously estimated; the prior unit's direction was right, its magnitude was 1.3× too high.
