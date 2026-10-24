# UTREES1 — retire superseded unpacked release trees

**Bound:** 12 tool calls (used 10). **Date:** 2026-10-19 (sampled 15:16 CDT / 20:16Z).
**Write paths:** `papers/encoder-crossover-190/released/**`, `papers/replay-record-not-decision/released/**`,
`scratch/utrees1/**`, `orchestration/units/UTREES1.md`, `orchestration/handoffs/UTREES1.json`.
**Forbidden (respected):** any `.tar.gz`, any `MANUSCRIPT.md`, any `submission/` file, `papers/gated-read-batching/`.

## JOB 1 — measured myself, before moving

| tree | files | bytes | `diff -rq` vs fresh `tar -xzf` |
|---|---|---|---|
| `encoder-crossover-190-released/` | 31 | 856,779 | empty → identical |
| `encoder-crossover-190-released (2)/` | 31 | 856,779 | empty → identical |
| `replay-record-not-decision-released/` | 10 | 1,313,443 | empty → identical |

All three identical — the card's table is confirmed by my own measurement, not trusted.

## JOB 2 — moved, never deleted; space normalised

| from | to |
|---|---|
| `encoder-crossover-190-released/` | `scratch/utrees1/superseded-unpacked/encoder-crossover-190/encoder-crossover-190-released/` |
| `encoder-crossover-190-released (2)/` | `scratch/utrees1/superseded-unpacked/encoder-crossover-190/encoder-crossover-190-released-2/` |
| `replay-record-not-decision-released/` | `scratch/utrees1/superseded-unpacked/replay-record-not-decision/replay-record-not-decision-released/` |

Manifests beside each tree (`.sha256`, relative paths, one per line); `sha256sum -c` verified
31/31 OK, 31/31 OK, 10/10 OK. No `(2)` survives as a filename fragment.

## JOB 3 — appended dated sections (append only, existing text untouched)

- `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md` → 38 → 74 lines
- `papers/replay-record-not-decision/released/SUPERSEDED-UNPACKED.md` → 16 → 46 lines

Each records: trees moved, destinations, byte-identity at move, archive bytes + md5 (and sha256).

## JOB 4 — archives proven unchanged

| archive | bytes before/after | md5 before/after | changed |
|---|---|---|---|
| `encoder-crossover-190-released.tar.gz` | 159,182 / 159,182 | `b4dac172003233d7d6c8c78c909b5594` | no |
| `replay-record-not-decision-released.tar.gz` | 107,764 / 107,764 | `41afa2831ff2f43af91d9c4416d8f658` | no |

End state: encoder `released/` = archive + `README_DEPOSIT.md` + `SUPERSEDED-UNPACKED-TREE.md`;
replay `released/` = archive + `CITATION.cff` + `README_DEPOSIT.md` + `SUPERSEDED-UNPACKED.md`.

## Disagreements reported (not smoothed over)

1. The 2026-10-17 note in `SUPERSEDED-UNPACKED-TREE.md` claims the encoder archive is 157,305 B /
   sha256 `778818b2…`. Today it is 159,182 B / sha256 `dbbf7b1a…` / md5 `b4dac172…` — the archive was
   rebuilt after that note; I recorded the current authority instead of copying the stale figure.
2. Both markers describe **earlier generations** of these same trees (UDEPOSIT2 2026-10-17 for encoder,
   UDOITIDY2 2026-10-19 for two replay trees, both described as stale). Today's trees are repopulations
   and were **not stale** — all three matched a fresh extraction byte-for-byte.
3. The replay marker documented two trees moved by UDOITIDY2; only **one** replay tree existed today.

## Notes

- `scratch/utrees1/fresh/` holds the two throwaway reference extractions used as the diff target. They sit
  beside no archive and are labelled temp; a verifier should re-extract rather than trust them.
- `papers/gated-read-batching` carries mtime 2026-10-19 14:28:49 -0500, i.e. **before** this unit started
  at 15:16; this unit ran no operation on it. No `git` command was run anywhere in this workspace.
