# Unit UDRAFT2 — draft paper #2 and its companion records

**Status:** in progress (card persisted first, per contract).
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
**Hard bound:** 30 tool calls. Increment writes to disk per section.

## Purpose
Draft `papers/replay-record-not-decision/` — a short note titled *"Replay reproduces the record, not
the decision"* — plus `CLAIMS.md`, `GAPS.md`, `AVAILABILITY.md`, from **already-recorded data only**.
No experiment is run; every number must exist on disk.

## Declared write paths (exactly these)
- `papers/replay-record-not-decision/**`
- `orchestration/units/UDRAFT2.md`
- `orchestration/handoffs/UDRAFT2.json`
- `scratch/udraft2/**`

No writes to `/home/zer0null/Duval`; no `git` command against it; no network.

## Read-first (source of record)
1. `strategy/PAPER2_REVERIFICATION.md` — the feasibility measurement; every number re-checked
   against the raw files it names.
2. `strategy/PAPER_SHORTLIST.md` — candidate A2/#2 context.
3. House shape: `papers/gated-read-batching/{MANUSCRIPT,CLAIMS,GAPS}.md`
   (`AVAILABILITY.md` does not exist in that directory; `papers/encoder-crossover-190/AVAILABILITY.md`
   is the availability/licence model).
4. `strategy/CODE_LICENSING_STRATEGY.md` — licence context.

## Corrections absorbed (the inventory's framing is wrong in three places)
1. 41.8 % at V0 has denominator **1,140** (6 model-pair × 190-case comparisons at one variant), not 3,040.
2. It is **one arm** (V0), not "across four variants" (V0–V3 = 41.75 / 47.11 / 40.00 / 43.33 %).
3. Pooled prompt 32.2 % hides a bimodal split: laya 62.63 % vs decider 15.8–26.8 %.
Plus: `l1-head-to-head.jsonl` is **not** an independent corpus — same 190 cases, same two models,
`picked_index` identical 190/190, only `ms` differs (380/380).

## Facts established from raw records (own commands, read-only)
Raw records (sha256, no `git`): DV `c5ec44a7…` 1,197,797 B / 3,040 lines; L1 `6af0e0d8…` 63,238 B / 380 lines.
Binding V0 476/1140 = 41.7544 %; V1 537/1140 = 47.1053; V2 456/1140 = 40.0000; V3 494/1140 = 43.3333.
Controls V0↔V2 and V1↔V3 each 244/244, 0 divergent. Prompt pooled 245/760 = 32.2368 %; laya 119/190 = 62.63 %.
Stability 60/190 = 31.5789 %. L1 98/190 = 51.5789 %; `correct` ∈ {0..4} in **both** files (index, not flag).
Correction to R2: `p_chosen`/`conf` are *identical* L1-vs-DV (0/380 differ); only `ms` differs (380/380).
