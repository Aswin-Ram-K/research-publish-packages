# UNONCENSUS1 — non-census leak adjudication (`imajev` + invisible class)

**Status:** `done` for the classification and enumeration; **no neutralised tree emitted** (card gates step 3
on `imajev` = (b)). **Hard bound:** 25 tool calls. **Used:** 17. No remainder on the classification.

**Workspace:** `/home/zer0null/reserach extarctor` (quoted).

## Purpose
1. Classify `imajev` (42 hits / 10 files in `scratch/ubij3/tree-three-r2`) as third-party-public / internal /
   ambiguous, before touching it.
2. Enumerate the rest of the non-census, non-generic, project-revealing string class with counts and
   classifications, reusing the earlier units' scanner convention.
3. Only if (b): build `scratch/unoncensus1/tree-four` neutralised and re-run every diagnostic.
4. Report actual diagnostic values (never "should be unchanged").
5. Report file count / bytes / roll-up hash and prove idempotence.

## Write paths (declared, and the only paths written)
- `scratch/unoncensus1/**` (scanner + scan log + census log)
- `strategy/NONCENSUS_LEAKS.md`
- `orchestration/units/UNONCENSUS1.md`
- `orchestration/handoffs/UNONCENSUS1.json`

Nothing was written inside `scratch/ubij3/**` (read only). No git command was run against
`/home/zer0null/Duval`; nothing was written to `/home/zer0null/research-publish-packages`;
`orchestration/units/UBUILD1.build.sh` and `repro/**` untouched. No identifier map was shipped or logged.

## Verdict
- **`imajev` = (a) third-party public model.** `mohit67890/imajev-4b` on HuggingFace, Apache-2.0, PEFT LoRA
  rank 64 / alpha 128 on `Qwen/Qwen3.5-4B` rev `851bf6e8`, siblings `imajev-2b`/`imajev-9b`. Live fetch
  HTTP 200; the read-only target links it as an external contender (`docs/BOARD.md:286`). It is a
  **citation and must STAY**; neutralising it would replace a citation with a meaningless tag.
- **No tree emitted.** Step 3 gated on (b); not satisfied. Therefore no diagnostics re-run and **no claim
  is made** about `compare.py` route A/B, the arms or the 2×2 — the card's step 4 forbids asserting
  unchanged values. No idempotence build exists to report.
- Enumerated the sibling invisible class: internal = `second-labeller-190` (36/6), `instrument190` (48/7),
  `decider-4b` (43/8), `H-A`/`H-B` (319/13, 300/20), `typed-channel` (~52/8), `EXP#11` (15/4),
  `EXP#12` (39/10), `D35` (31/9), `D44` (6/3), `no-union` (14/3), `encoder-crossover-190` (9/5),
  `tccommon.py`/`tcmodel.py` (13/9, 9/8); third-party-public = `imajev`, `deberta-v3-base` (37/12),
  `modernbert-base` (39/11), `setfit-mpnet` (40/12); ambiguous = `LEAD`, `D09`.
- Scanner convention reused: `scratch/ubij1/census_one.py` + frozen 184-id list
  `scratch/uagnostic1/census.tsv`; my rule reproduces UBIJ3 exactly where the tree is stable
  (`imajev` 42/10, `second-labeller-190` 36). `no-union` 14 vs UBIJ3's 9 and `encoder-crossover-190` 9 vs 4
  differ by exactly the 5 references each that the concurrently edited `MANIFEST.json` now carries.
- Census (frozen 184-id, `census_one.py`, 45 files): TOTAL **3,354** · inside-stimulus **2,171** (d=30) ·
  outside **1,105** · keys **78** · 74/184 distinct. `imajev` appears **0** times in it — the invisible
  class in one line. Inside-stimulus is **unchanged** from UBIJ3's 2,171; the +6 outside is the concurrent
  `MANIFEST.json` edit.
- Roll-up (dated): sha256 over sorted `sha256sum` lines =
  `495ecf614d5b417b0aee0e12f957c3af7ad9e99c5439e5b2bf3975a4be05a616`; 45 files / 3,008,378 bytes;
  `MANIFEST.json` sha256 `f3e4a22c…` (moving, owned by another unit).

## Blocker
None for the classification. The sibling internal class remains **unneutralised by design** (step 3 gated on
`imajev` = (b)).

## Next unit hint
A follow-up unit should neutralise the internal neighbours from this list under NEUTRAL-TAG/v1
(`second-labeller-190`, `instrument190`, `decider-4b`, `H-A/H-B`, `typed-channel`, `EXP#11/#12`, `D35`,
`D44`, `no-union`, `encoder-crossover-190`, `tccommon.py`/`tcmodel.py`), decide `LEAD` and `D09/D15/D25`,
and separately decide whether `MANIFEST.json` may publish `source` paths and `source_sha256` digests of
unreleased private-repo files. It must pin the source tree by the roll-up hash above, because the owning
unit is editing `MANIFEST.json` concurrently.
