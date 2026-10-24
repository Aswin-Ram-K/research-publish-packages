# USIZEFIX1 — re-measure stale inventory sizes in PUBLICATION_CHECKLIST.md

**Status:** in progress (skeleton persisted before work, per unit contract)

## Purpose
`strategy/PUBLICATION_CHECKLIST.md` carries inventory sizes that are stale. Re-measure each against disk
with `stat -c%s` and correct in place, keeping the old value visible as dated history. Then sweep the whole
file for the same class of error (size / page count / digest) across the six upload artifacts and the three
release archives.

## Bound
**8 tool calls total.** Stop and report at the bound.

## Declared write paths (nothing outside these)
- `strategy/PUBLICATION_CHECKLIST.md`
- `orchestration/units/USIZEFIX1.md`
- `orchestration/handoffs/USIZEFIX1.json`
- `scratch/usizefix1/**`

## Inputs — reported stale pairs (UNVERIFIED by the reporting unit; measurement wins)
| line | artifact | stale | expected |
| --- | --- | --- | --- |
| :236 | `papers/encoder-crossover-190/tmlr/main.pdf` | 176,971 | 177,298 |
| :244 | `papers/replay-record-not-decision/released/…-released.tar.gz` | 107,641 | 107,764 |
| :256 | `papers/gated-read-batching/released/…-released.tar.gz` | 128,559 | 128,902 |
| :126, :243 | `papers/replay-record-not-decision/preprints/…-preprints.zip` | 11,379 | 11,526 |
| :176, :255 | `papers/gated-read-batching/preprints/…-preprints.zip` | 14,094 | 15,296 |

## Hard rules
- `/home/zer0null/Duval` READ-ONLY, and nothing under `papers/` is modified. Read sizes only.
- No `git` command against any target repo.
- Never invent a value: every number written must come from a command actually run.
- Noted, NOT changed: gated archive's packaged `CITATION.cff` comment names an older record id while the
  concept DOI is correct — dated history, outside this file.

## Work log
- [ ] skeleton persisted (this card + handoff stub)
- [ ] recon: `stat -c%s` + sha256 on the nine artifacts; locate each checklist line
- [ ] edit stale values in place with `Superseded 2026-10-19:` history notes
- [ ] sweep whole file for remaining size/page/digest mismatches
- [ ] verify + write handoff
