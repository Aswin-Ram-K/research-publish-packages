# U-TELEMETRY — prompt-cache population table over recorded bili telemetry

**Status:** done. Script: `scratch/telemetry/population_table.py` (reruns every number below; prints Markdown;
`--json PATH` dumps the same numbers). Source opened strictly `mode=ro`.

---

## 0. Snapshot (the DB is live — these are the only frozen facts)

| field | value at write time |
|---|---|
| path | `/home/zer0null/.local/share/billion-context/sessions/index.db` |
| size | 969,879,552 bytes |
| mtime (unix) | 1792535614.24 |
| sessions | 1,278 |
| blocks | 3,029 across 332 distinct sessions |
| messages / content rows | 134,323 / 162,298 |

The DB grew by **5 sessions and 9 MB while this unit ran** (a parallel agent was writing to the same
live service). Every figure below is therefore "as of the run", not a permanent property. The script
re-prints this block each run, so a future reader can tell whether they are on the same snapshot.
**Reproduce against a copy of that size/mtime, not against "the" DB.**

## 1. Headline — CONFIRMED, with a correction to the request count

| quantity | card claim | measured | verdict |
|---|---|---|---|
| sessions | 1,269 | 1,278 | moved (live DB grew) |
| requests | 55,401 | 55,720 | moved (live DB grew) |
| `sum(inputTokens)` | 3,795,253,706 | 3,808,452,785 | moved (live DB grew) |
| `sum(cachedTokens)` | 3,588,681,817 | 3,601,299,289 | moved (live DB grew) |
| **cache hit ratio** | **94.56%** | **94.56%** | **CONFIRMED to two decimals** |
| mean requests / session | 43.7 | 43.60 | consistent |

The **ratio is the only stable quantity**: it moved by <0.005 pp across a 5-session / 9 MB drift.
Totals moved by ~13 M tokens. Anyone quoting absolute totals without a snapshot stamp is quoting a
moving target; the ratio is quotable.

Two structural facts the headline hides:

* `cachedTokens ≤ inputTokens` for **every** session (max ratio 1.0000, no session exceeds its own
  prompt). So `cachedTokens` is a sub-population of `inputTokens`, not an independent counter — the
  decomposition in §3 depends only on this.
* All 1,278 sessions share `protocol='openai'`, `origin='http://127.0.0.1:8790'`, `namespace='dsh'`,
  `status='active'`. This DB is the DSH proxy's view, not a multi-tenant corpus.

## 2. Population table by hit-rate band

Bands are right-closed on the session-level ratio `cachedTokens/inputTokens`. Both weightings shown —
they answer different questions and disagree by two orders of magnitude.

| band | sessions | share sessions | tokens | share tokens | mean requests | mean hit (session-wtd) |
|---|---|---|---|---|---|---|
| 0-1% | 139 | 10.88% | 403,421 | 0.01% | 9.8 | 0.01% |
| 1-25% | 58 | 4.54% | 10,490,192 | 0.28% | 62.5 | 12.69% |
| 25-50% | 194 | 15.18% | 3,591,465 | 0.09% | 15.3 | 37.99% |
| 50-75% | 195 | 15.26% | 12,122,181 | 0.32% | 55.6 | 60.84% |
| 75-90% | 217 | 16.98% | 331,502,313 | 8.70% | 25.8 | 85.24% |
| **90-99%** | **474** | **37.09%** | **3,450,340,502** | **90.60%** | **66.1** | **94.05%** |
| >99% | 1 | 0.08% | 2,711 | 0.00% | 1.0 | 99.15% |

**Coverage of the denominator (why the tails are thin).** Sessions at exactly 0 tokens: 90.
Sessions below 10,000 prompt tokens: 387, jointly 799,350 tokens = **0.021% of the corpus**; **none of
them carries a compression block**. So the card's "295 sessions < 50%" decomposes into ~139 near-empty
probe sessions (403 k tokens total, mean 9.8 requests) plus genuinely cache-hostile short sessions.
Correct reading:

> 10.9% of sessions but 0.01% of tokens sit below 1% hit; 37.1% of sessions and **90.6% of tokens**
> sit in 90-99%. A session-count-weighted statement ("a third of our traffic fails to cache") and a
> token-weighted statement ("we are at 94.6%") describe the same data and are both true — which is
> the point of showing both columns.

The measured mean hit per session (0.700) versus the token-weighted 0.9456 is the entire gap between
"typical session" and "typical token".

## 3. Cost decomposition (tokens, no currency invented)

**Counters.** Uncached prompt contribution = `ΣinputTokens − ΣcachedTokens` = **207,153,496 tokens**.
Every prompt token is therefore presented **18.38×** on average (3.81 G presented / 207 M distinct
receipts). This multiplier needs no price and no assumption beyond §1's containment fact.

**Explicit assumption for the counterfactual.** "No cache" = every one of the 3.81 G prompt tokens
billed once, i.e. 3.81 G = 100% of the baseline. With cache, what a provider bills is
`(I − C) + w·C`, where `w` is the cache-read weight relative to a fresh prompt token. `w` is a
**sensitivity parameter, not a price**; we sweep it rather than assert it.

| cache-read weight `w` | billed token-equivalents | ratio vs no-cache | saving |
|---|---|---|---|
| 1.00 (cache buys nothing) | 3,808,452,785 | 100.00% | 0.00% |
| 0.50 | 2,007,803,140 | 52.72% | 47.28% |
| 0.25 | 1,107,478,318 | 29.08% | 70.92% |
| 0.10 | 567,283,425 | 14.90% | 85.10% |
| 0.00 (cache reads free) | 207,153,496 | 5.44% | 94.56% |

**Sensitivity range to quote:** with a cache read costing anywhere in 10-50% of a fresh token, the
pileup collapses the billable volume to **15-53% of the no-cache baseline — a 1.9× to 6.7× reduction**.
The 94.56% "saving" in the extreme column is *not* a billing saving; it is the saving only if cache
reads were free, and it must never be quoted as a discount. What **is** priced-independent and safe:
**the workload re-sends 18.4 prompt tokens for every distinct one it pays to ingest.**

## 4. Contamination check — resolved; not material

The workspace is `/home/zer0null/reserach extarctor`; its sessions are in this DB.

**Narrow rule** — `title ∪ host_title ∪ meta_json` matches `(?i)reserach|research[ _]extractor`
(this is the workspace path as spelled by its host titles, plus the project name):
**41 sessions, 44,497,015 tokens = 1.17% of the corpus**, 782 requests, hit rate 90.91% (below the
94.56% headline). Excluding them moves the headline to **94.60%** — +0.04 pp. `0/10` of the largest
sessions by tokens match the rule; the top session is "Rust browser runtime for agents" (417 M tokens),
unrelated to this project.

**Upper-bound convention** — widening to the *worst plausible* contamination: the narrow rule ∪ every
session whose `host_title` begins "You are" (the subagent/dispatch prompt shape used across *all*
projects on this machine): **588 sessions, 1,522,875,159 tokens = 39.99% of the corpus**, hit 93.67% vs
95.16% for the rest. Even deleting all of it moves the headline only to **95.16%**.

**Verdict: contamination is immaterial.** The headline is driven by one general-purpose session
(11% of tokens alone) and a long tail of unrelated development work; this research project is
1.2-~3% of tokens depending on how generously its subagents are attributed. The card's worst case
("top sessions by tokens are this project's") is **false** — none of the top 10 is.

## 5. Per-request distribution — what the aggregates allow and forbid

The raw per-request data is **NOT stored**. Schema has no per-request usage table: `sessions` (one
`stats_json` blob per session), `messages` (role/kind/content_hash only — no token counts),
`content`, `blocks`, `refs`. `messages.seq`/`ref` are usable for message ordering but carry **no
token attribution**, and `blocks.*_seq` are all zero while `blocks.start_ref/end_ref` do not line up
with message counts, so even a per-message proxy cannot be reconstructed. Therefore per-request prompt
size exists only as the session mean `inputTokens / requests`.

Allowed (what we can state):

| metric | p50 | p90 | p99 | max | mean |
|---|---|---|---|---|---|
| prompt tokens per request, session means | 40,435 | 82,963 | 126,584 | 223,279 | 37,825 |

Request-weighted pooled mean = **68,350 prompt tokens/request**. Per-session hit rate: p10 26.8%,
p50 86.0%, p90 95.8%, mean 70.0%. Sessions with zero cached tokens: 47 of 1,188.

Forbidden by the aggregates: the maximum single-request prompt; growth *within* a session; whether
cache hits were contiguous prefixes or scattered; the number of cache misses per session; and
therefore any statement of the form "the p99 request costs X".

## 6. Compression vs caching — a selection effect, not a demonstrated benefit

| group | sessions | tokens | share tokens | token-wtd hit | mean session hit | median session hit | mean requests |
|---|---|---|---|---|---|---|---|
| has blocks | 332 | 3,366,177,028 | 88.39% | 95.06% | 90.82% | 92.37% | 90.3 |
| no blocks | 946 | 442,275,757 | 11.61% | 90.76% | 61.91% | 61.60% | 27.2 |

Naive reading: +28.9 pp session-weighted, +4.31 pp token-weighted. **Both are confounded.** Median
requests: 45 (blocks) vs 12 (no blocks); median prompt tokens 2.91 M vs 22 k. Compression only
happens to sessions long enough to compress, and hit rate is a prefix-length phenomenon.

Stratifying on the corpus-median request count (18):

| requests | sessions (blocks / none) | hit (blocks) | hit (none) | Δ |
|---|---|---|---|---|
| ≤ 18 | 45 / 601 | 84.31% | 89.50% | **−5.18 pp** |
| > 18 | 287 / 345 | 95.19% | 91.27% | **+3.93 pp** |

The sign flips between strata. In the token-dominant stratum compression sessions show a small
+3.9 pp advantage; among short sessions those few that got compressed show a *deficit*. **The data do
not support a claim that compression damages cache reuse, nor that it helps it** — the honest statement
is that at ~95% token-weighted hit in the compressed stratum, compression and caching coexist without
apparent harm, and the aggregate gap is length selection. A true test needs within-session pre/post-block
hit rates, which this schema cannot produce (§5).

## 7. Strongest publishable sentence the data support

> Over 1,278 recorded agent sessions and 55,720 model requests, 3.81 billion prompt tokens were
> presented to the provider of which 94.56% were served from the prompt cache — 207 million distinct,
> uncached tokens re-presented an average of 18.4 times — and 90.6% of all prompt tokens were spent in
> the 37% of sessions whose hit rate exceeded 90%.

That sentence is snapshot-stamped, priced-free, and survives the contamination bound (95.2% worst case).

## 8. Reproduction

```bash
python3 "scratch/telemetry/population_table.py"            # Markdown report, ~0.4 s
python3 "scratch/telemetry/population_table.py" --json /tmp/x.json
```

SQL executed (also printed by the script, verbatim, as §7 of its output):

```sql
SELECT s.session_id, s.parent_session_id, s.protocol, s.origin, s.status, s.created_at, s.updated_at,
       s.title, s.host_title, s.meta_json,
       COALESCE(json_extract(s.stats_json,'$.requests'),0)      AS requests,
       COALESCE(json_extract(s.stats_json,'$.inputTokens'),0)   AS input_tokens,
       COALESCE(json_extract(s.stats_json,'$.cachedTokens'),0)  AS cached_tokens,
       COALESCE(json_extract(s.stats_json,'$.outputTokens'),0)  AS output_tokens,
       COALESCE(json_extract(s.stats_json,'$.lastInputTokens'),0) AS last_input_tokens,
       COALESCE(json_extract(s.stats_json,'$.cacheSamples'),0)  AS cache_samples,
       COALESCE((SELECT COUNT(*) FROM blocks b WHERE b.session_id = s.session_id),0) AS n_blocks
FROM sessions s;

SELECT (SELECT COUNT(*) FROM sessions), (SELECT COUNT(*) FROM blocks),
       (SELECT COUNT(DISTINCT session_id) FROM blocks),
       (SELECT COUNT(*) FROM messages), (SELECT COUNT(*) FROM content);
```

## 9. Known limits (stated, not hidden)

1. Live DB: totals are only comparable within one snapshot stamp; the ratio is stable.
2. `w` in §3 is not measured — no provider price list is in this DB, and none was invented.
3. Contamination attribution uses prompt text, so it is a text heuristic, not a session-ownership record
   (`parent_session_id` is NULL for every session; there is no workspace column).
4. Compression vs caching is cross-sectional; the schema forbids the within-session test.
