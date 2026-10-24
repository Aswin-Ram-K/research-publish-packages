# UGATE3 — port corrected exclusion gate into the release build

STATUS: DONE (skeleton written first, per unit contract)

## Purpose
Port UGATE1's corrected scoped positive-vocabulary checker into the gate heredoc of
`orchestration/units/UBUILD1.build.sh`, remove the 400-line offender cap, stop the gate
scanning its own `vocabulary/` directory, keep it fail-closed, and re-measure.

## Hard bound
25 tool calls. Stop and report `partial` if exceeded.

## Write paths (nothing else)
- `orchestration/units/UBUILD1.build.sh`
- `strategy/GATE_VOCABULARY_ANALYSIS.md` (append dated section only)
- `orchestration/units/UGATE3.md`
- `orchestration/handoffs/UGATE3.json`
- `scratch/ugate3/**`

## Read-only
`/home/zer0null/Duval`, `/home/zer0null/research-publish-packages`. No bare `git status`.

## Must not change
`orchestration/units/UBUILD1.build.sh:134` `PROMOTED_SAN_SRC`.
No `make_data_vocab.py --mode full`.

## Plan
1. Read `scratch/ugate1/gate_scoped.sh` + `strategy/GATE_VOCABULARY_ANALYSIS.md`.
2. Patch heredoc in `UBUILD1.build.sh` (600–845 region): port checker, uncap listing,
   exclude `vocabulary/`, fail-closed on missing/empty vocab.
3. Build into `scratch/ugate3/dest/research-publish-packages`.
4. RED→GREEN: inject mechanism identifier → gate FAILS and names file:line; remove → proceeds.
5. Fail-closed: empty vocabulary file → build FAILS.
6. Report classes of residual offenders.

## Result
- The heredoc already carried the scoped revision (UGATE2-labelled, mtime 2026-10-16 01:12):
  uncapped `FAIL_LIMIT = 10 ** 9` (`UBUILD1.build.sh:802`), `VOCAB_REL` self-skip (`:709`,`:808`),
  fail-closed `load()` (`:728-730`), keys-only data vocab (`:587-655`). Verified, not re-ported;
  `UBUILD1.build.sh` NOT modified; line 134 `PROMOTED_SAN_SRC` untouched.
- Build: staged 29 files, 29 kept / 0 dropped; emitted 39 files (excl .git); english.txt 74,959 words;
  data.txt 501 keys / 32 docs; anchor 907fa39 in 4 files; never-ship 15 absent.
- Gate: old (card) 1689 -> new **1410**, all 1410 listed, **0** offenders under `vocabulary/`.
- Classes (scratch/ugate3/offenders_classified.tsv): a-schema 80/38; b-thirdparty 1054/296;
  c-mechanism **276/11**; d-encoding 0.
- RED: `grantPolicy` at `results/REPORT.md:305` -> 1411, named. GREEN: removed -> 1410, diff IDENTICAL.
- FAIL-CLOSED: emptied `vocabulary/english.txt` -> rc=2, `FATAL: vocabulary file has no declared terms`;
  build gate block exits 2.
- No vocabulary widened; no `--mode full`.

## Progress log
- (init) skeleton written.
- (1) read gate_scoped.sh + GATE_VOCABULARY_ANALYSIS.md + build heredoc.
- (2) build to scratch/ugate3/dest/research-publish-packages -> 1410; classify 1410.
- (3) red->green and fail-closed probes on copies; analysis §9 appended; handoff written.
