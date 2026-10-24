# UNEUTRAL2 — run the REDACT_PINS=0 branch and measure it

**Unit card.** Workspace `/home/zer0null/reserach extarctor`. Parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.
Bound: ≤30 tool calls (reported actual count: 30).

## Purpose

The parent superseded UNEUTRAL1's digest-invariance clause. The invariant of record is now
**no published CLAIM NUMBER may move**. This unit runs the implemented-but-never-run
`REDACT_PINS=0` branch, gives the residual census on both sides, measures whether any claim number
moves, evaluates the dead-field-stripping option, re-reports the digests, and re-checks idempotence.

## What was done

1. Ran the unpinned generator into `scratch/uneutral2/tree-full` (live tree proven unchanged by a
   before/after sha256 sweep). `redact.py` was **not** modified.
2. Wrote `scratch/uneutral2/census2.py` (same census source/method as UNEUTRAL1's
   `scratch/uneutral1/scan.py`, plus per-file/per-class/per-line attribution) and censused four trees.
3. Ran `verify/recompute-claims.py` inside the unpinned tree (verbatim output captured).
4. Re-ran `parse_fixture.py` + `compare.py` on live, pinned and unpinned.
5. Read the training code for field consumption and measured the strip saving; built
   `scratch/uneutral2/tree-stripped`.
6. Re-ran the generator a second time and diffed.

## Result

**`done`.** Headline: the unpinned branch **does not reach 0 and is not shippable** — it corrupts
every JSONL record and moves 5 of 6 route-A claim numbers.

| | |
|---|---|
| census, unpinned `tree-full` | 44 files · 16/184 ids · **29 occurrences** |
| the 29 | all in `verify/redaction-log.json` (the log is rewritten *after* stage E) |
| census, pinned `scratch/uneutral1/tree` | 45 files · 99/184 · 26,351 |
| census, stripped | 45 files · 99/184 · **9,254** |
| `recompute-claims.py` in tree-full | `ALL CLAIM NUMBERS PRESERVED: True`, exit 0, digest `9997da62…` |
| route A, unpinned | ties **121** · agreement **0.336842** · kappa **0.319886** · exact **64** · zero 41 · AB **0.347368** |
| route A, pinned/live | 120 · 0.342105 · 0.325207 · 65 · 41 · 0.352632 |
| JSONL corruption | train 800/800 bad, dev 200/200 bad — `Invalid \escape`; cause `nKind`/`nSituation`/`nCandidate` matching inside `\nKind` |
| tooling breakage | `second-labeller/parse_fixture.py:16` → `"D07.sandbox.ts"`; `FileNotFoundError` |
| strip saving | −1,695,674 B train (−76.90 %) + −366,478 B dev (−75.57 %) = **−2,062,152 B** |
| idempotence | two runs byte-identical (log sha256 `0496d732…` both runs) |

## Blockers

None. The measurement is complete.

## Recommendation

**(A) ship the pinned tree now.** **(B) must not ship.** Commission **(C′) = A + strip the five dead
JSONL fields (`texts`, `id`, `familyId`, `clanId`, `stratum`) + selectively retag the non-fixture
material**, keeping `PIN_LITERAL_KEYS` and the tooling pins. Full reasoning in
`strategy/UNPINNED_MEASUREMENT.md` §7.

## Files

`scratch/uneutral2/{tree-full,tree-full-run2,tree-stripped,rt/**,census2.py,census-*.txt,gen-run*.log,live-{before,after}.sha}`
· `strategy/UNPINNED_MEASUREMENT.md` · this card · `orchestration/handoffs/UNEUTRAL2.json`.
