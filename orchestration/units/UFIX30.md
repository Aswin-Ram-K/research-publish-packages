# UFIX30 — settle UBUILD1.build.sh revision authority + corrected gate numbers

HARD BOUND: 15 tool calls (used 12). WRITE PATHS: `strategy/GATE_VOCABULARY_ANALYSIS.md` (append dated
section only), `orchestration/units/UFIX30.md`, `orchestration/handoffs/UFIX30.json`, `scratch/ufix30/**`.
FORBIDDEN: editing `orchestration/units/UBUILD1.build.sh` (follow-up unit owns it), any package/paper file,
`/home/zer0null/Duval`, `/home/zer0null/research-publish-packages`. No git anywhere (none run).

## Verdict
Authoritative revision = **the current on-disk file**: sha256
`bbf5a52cb1983a0a0f3b6adf8aeaa1ab87e0dc3eabc97c21563e5e6b0512c372`, 48500 bytes, **968 lines**, mtime
`2026-10-16 01:15:52.564369969 -0500`, `:134 PROMOTED_SAN_SRC` intact. Stable (two hashes 15 s apart
identical); last write 01:15:52 = UGATE2's post-patch revision, ~10 min before the probe. UGATE3's
"unmodified" claim is unsupported: its build log is 01:14:04, *before* that mtime.

## Revision trail (filesystem only)
- live `orchestration/units/UBUILD1.build.sh` — `bbf5a52c…`, 968 lines, 01:15:52 (contains `DATAVOCAB_EOF`).
- `scratch/ugate2/UBUILD1.build.sh.pre-ugate2.bak` — `bb4896e5…`, 843 lines, 01:12:24 (pre-patch).
- `scratch/uwire3/UBUILD1.build.sh.green` — `bb4896e5…`, 843 lines, 01:09:55 (same bytes).
- `scratch/uwire2/UBUILD1.build.sh.orig` — `df471955…`, 1036 lines, 10-15 21:47:26.
- `scratch/uwire1/UBUILD1.build.sh.orig` — `a2a1df17…`, 1019 lines, 21:47:20;
  `scratch/uver15/UBUILD1.pre.sh` — `5c837c8d…`, 1019, 20:58:51;
  `scratch/ulicence5/UBUILD1.build.sh` — `eecab269…`, 1019, 19:49:27.
- `scratch/uver21/staled/orchestration/units/UBUILD1.build.sh` is a **symlink to the live file** — not a
  snapshot; must not be cited as an older revision.

Producer map: uwire3 dest gate `0940edb9…` (124 lines, 0 self-refs) ← 843-line revision; ugate3 dest gate
`7df3ed72…` (184 lines, 13 self-ref occurrences) ← **unpreserved intermediate revision** ~01:13–01:14:04
(only ugate3/uver30 artifacts contain its marker `NKFS`); ugate2 dest gate `cccacbe9…` (176 lines, 0
self-refs) + `scratch/uver30/build1.log` ← current revision.

## Corrected numbers
- pre-correction old shipped gate **1740** (`strategy/GATE_VOCABULARY_ANALYSIS.md:376`; UGATE2 agrees).
  The card's 1689 is an earlier revision of the staged bytes — superseded.
- post-correction **1398** (`scratch/ugate2/build.log:1455`; reproduced by `scratch/uver30/build1.log:1455`).
- superseded **1410** (`scratch/ugate3/build1.log:1467`) = 1398 + 12, because its emitted gate carried 13
  self-reference occurrences / 12 distinct tokens: UGATE2, UBUILD1, UNCAPPED×3, DATA_EXT×2, fam, abr,
  A-Za-z, NKFS, uncapped×3 (+ enum-label named by UVER30). Current heredoc `:661-836` contains **0** of them.
- mechanism-in-stimulus **268 occ / 10 distinct** authoritative (`scratch/ugate2/residual_by_class.txt`);
  UGATE3's **276 / 11** superseded (counts the self-reference tokens as mechanism).

## Follow-up edits (not made)
1. `orchestration/units/UBUILD1.build.sh:134` current text: `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"` — re-pin this one line.
2. `SHIP_STAGED=( … )` = **lines 178–214** (29 names at 179–213).
3. On any promoted-tree change: re-derive `SHIP_STAGED` from the new tree's real files and re-measure the gate
   counts — `strategy/BUILD_WIRING.md:143-144`, enforced by
   `tests/test_build_wiring.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is` (`:222-235`).

## Evidence commands
`sha256sum`/`stat -c%y`/`wc -l` over the live file and every copy; `cmp`; double hash 15 s apart;
`grep -oiF` self-reference token scan over live heredoc `661-836` and over each emitted `gate.sh`;
`grep -nE 'GATE RESULT|flagged tokens'` in ugate2/ugate3/uver30 logs; `grep -rl NKFS` over the workspace.
