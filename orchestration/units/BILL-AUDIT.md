# UNIT BILL-AUDIT — prove the bill instead of computing it

**Status:** done · **Bound:** 40 tool calls · **Server:** `occamy-1.0` (SGLang)
`http://192.168.2.168:8012` — sole writer, no restart, no `/flush_cache`.

## Purpose

Every token number the engine reports is derived from the append-cost law
(`miss-law/LAW.md`), not read from the server. QUALITY-ARM said so itself: *"billed tokens are
LAW-DERIVED, not server-observed"*, and its next-hint named the fix — read
`meta_info.cached_tokens_prompt`. This unit exists to **falsify** the law against the server's own
accounting, not to confirm it.

## Hard rules honoured

* Sole writer on `:8012`; never touched `:8014`.
* Never restarted a server; never called `/flush_cache`.
* Read-only on `quality/**` and `measure/**`; wrote only under `audit/`.
* Never touched `/home/zer0null/Duval`, `release/**`, `papers/**`, `src/**`,
  `experiments/agentic-lazy/**`, `experiments/miss-law/**`.
* One row per request, `flush()` + `fsync()` per row.
* Never treated a null as zero. Never computed a "server" number from the law.

## Method

1. Located the server-side field on `POST /generate` (`meta_info.cached_tokens`,
   `cached_tokens_details.{device,host}`) and confirmed it populates on warm requests —
   `cached_tokens: 0` on cold (a reported zero, not a null), `384` on an identical repeat.
2. Found the same count on `usage.prompt_tokens_details.cached_tokens` of
   `/v1/chat/completions` — the endpoint QUALITY-ARM actually used and never read.
3. Ran a 7-cell sample (residue 2 / 0 / high, at ~424 and ~8,066 token prefixes, 3 reps each),
   aiming each residue by reading `P1` **back from the server** before measuring.
4. Replayed QUALITY-ARM's own arm-A turn plan from its shipped artefacts and read the server's
   number per turn.

## Findings (falsification, reported first)

1. **`L` is mis-specified in `quality/runner.py:467`** — it passes the whole prefix size
   (`prompt_tokens + FRAMING`) where the law requires the append (`P2 − P1`). The formula
   degenerates to *billed = prompt size*. Against the server the replay overstates the true bill
   by **57.6×** (law 123, server 7,087).
2. **The avalanche is one block, not the whole prefix.** At residue 0 the server bills `64 + L`,
   not `P1 + L`; at residue 1, `1 + L`. 6/6 rows. `LAW.md` §7(i)'s "~8,000 tokens per append" is
   wrong by ~2 orders of magnitude.
3. **The law's non-avalanche branch is exactly right** — `(P1 mod 64) + L`, `delta = 0` in 12/12
   warm rows at both prefix sizes.

## Verdict

The law does **not** survive as an accounting instrument. Its non-avalanche branch is sound for
one warm append at residue 2–63; it fails at residue {0, 1} (wrong by `P1 − 64`) and is not
applicable at all to multi-turn conversational bills, which is QUALITY-ARM's whole regime.

## Deliverables

* `experiments/ptr-engine/audit/rows.jsonl` — 693 rows (21 measure + 672 aim probes), fsync per row
* `experiments/ptr-engine/audit/REPORT.md` — side-by-side tables and the verdict
* `experiments/ptr-engine/audit/audit.py`, `replay_quality.py`, `raw_meta.json`
* `orchestration/handoffs/BILL-AUDIT.json`

## Open questions carried forward

* Why ENGINE-R1's cell C observed `cached = null` at residue 0 while this unit's residue-0 cells on
  `/generate` all reported a number. Prompted an untested hypothesis (chat-endpoint usage wrapper),
  deliberately not reported as a finding.
* Whether the 2-token replay appends fall below the cache's minimum reusable length (turn 1 was
  `server-null`).
