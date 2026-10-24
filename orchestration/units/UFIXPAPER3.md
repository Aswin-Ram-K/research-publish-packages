# UFIXPAPER3 — correct two record defects in paper #3 companion files

**Purpose.** Fix (1) the digest mislabelled as the fixture sha256 in `papers/encoder-crossover-190/`,
and (2) the stale published A/B mutual agreement `0.3526` where it is a live claim rather than a frozen
record, without disturbing anything already right.

**Read first:** `strategy/RESIDUAL_TRIAGE_3.md` part C (C.1 digests, C.2 the A/B value).

**Declared write paths (exactly these).**
- `papers/encoder-crossover-190/**`
- `orchestration/units/UFIXPAPER3.md`
- `orchestration/handoffs/UFIXPAPER3.json`
- `scratch/ufixpaper3/**`

**Do not edit:** `scratch/**` (except `scratch/ufixpaper3/**`), `orchestration/packages/**`,
`orchestration/units/UBUILD1.build.sh`, `papers/replay-record-not-decision/**`.

**Ground truth (read from disk, not invented).**
- shipped fixture `fixture/fixture-190.json` → sha256 `a15224ba…852e`, 76,897 bytes.
- as-audited instrument `repro/encoder-crossover-190/fixture/reflex-decisions.ts` → `076164ac…b4796`,
  145,031 bytes; shipped instrument hashes `369159b0…` so `076164ac` is not in the shipped set.
- tree A/B mutual agreement = `0.3684210526315789` (70/190); old value `0.3526` = 67/190.

**Rules.** Assert each before-string occurs exactly once before editing; introduce no new number;
report ambiguity rather than guessing; separate measured / inferred / not determined; no installs,
no fetches, no git against `/home/zer0null/Duval`.

**Hard bound:** 20 tool calls.
