# UCONCEPT1 — switch every deposit citation from the v1 version DOI to the concept DOI

**Purpose.** The Zenodo deposit v1 (`10.5281/zenodo.23463945`) is published and a **v2** is imminent. A new
version mints its own version DOI, so the v2 archive must not cite the v1 version DOI. Every citation of the
deposit moves to the **concept DOI** `10.5281/zenodo.23463944`, which always resolves to the latest version.

**Hard bound.** 30 tool calls. **Used 15** (plus this card / handoff / parent message).

**Declared write paths.** `papers/encoder-crossover-190/**`, `scratch/uzenodo2/run2/CITATION.cff`,
`scratch/ufixman1/build_archive.sh`, `strategy/DEPOSIT_ARCHIVE.md`, `scratch/uconcept1/**`,
`orchestration/units/UCONCEPT1.md`, `orchestration/handoffs/UCONCEPT1.json`.
Not touched: `scratch/_superseded-unpacked/**`, `/home/zer0null/Duval`, any git state.

## 1. Every occurrence of the version DOI before any change (repo-wide grep)

Live sources (the only ones edited): `papers/encoder-crossover-190/MANUSCRIPT.md:743`, `:794`, `:858`
(3); `papers/encoder-crossover-190/submission/METADATA.md:26` (1); the archive's `CITATION.cff` source
`scratch/uzenodo2/run2/CITATION.cff:25` (1). Derived (regenerated, never hand-edited):
`submission/main.tex:375,:407,:427`; `rendered/encoder-crossover-190.html:851,:931,:990`.
Out of write-path scratch copies (left alone): `scratch/utmlr6/*`, `scratch/udoiback1/*`,
`scratch/urepo1/*`, `scratch/uartifact2/*`, `scratch/_superseded-unpacked/*`, `scratch/ufixman1/build_archive.sh:41` (comment).
Pre-existing concept DOI `…23463944` (the survivor): `MANUSCRIPT.md:860`, `main.tex:427`,
`html:992`, `CITATION.cff:32` (comment). Historic `strategy/TMLR_*.md` and the dated sections of
`strategy/DEPOSIT_ARCHIVE.md` still name the v1 DOI as dated history (out of scope; left).

## 2. Authoritative CITATION.cff source — established by evidence, not assumption

`scratch/ufixman1/build_archive.sh:31` → `CIT="$ROOT/scratch/uzenodo2/run2/CITATION.cff"`, staged at `:59`.
`strategy/DEPOSIT_ARCHIVE.md:20` "inputs" row names the same three inputs. The stray unpacked trees under
`scratch/_superseded-unpacked/` are **not** consumed by the build (moved there by UARTIFACT2; untouched here).

## 3. Change applied + every derived artifact regenerated with project tooling

- live text: 3 substitutions in `MANUSCRIPT.md`, 1 in `submission/METADATA.md` (exact-string swap, asserted counts).
- `CITATION.cff` source: `doi:` → concept DOI + its now-false comment corrected (>`v1` wording removed, so the
  version-DOI string is not re-introduced). 2,006 B / `56300d7c…` → **2,152 B / `32bee18f…`**.
- `main.tex`: `python3 tools/package/md2tex.py --package encoder-crossover-190` (exact invocation from `--help`),
  run twice → `cmp` exit 0. Guard printed 13 bibitems / 23 `\cite` / 13 distinct keys / no uncited / no unresolved.
- payload: `tar --mtime=@0 --sort=name -cf - -C submission main.tex | gzip -n -9` (BUILD_NOTES recipe), built twice →
  `cmp` 0; extracted member `cmp` main.tex 0.
- PDF: `HOME/TMPDIR/TECTONIC_CACHE_DIR` inside `scratch/uconcept1/`, **no** `-Z continue-on-errors`:
  `scratch/utex1/bin/tectonic -r 1 --keep-logs -o … main.tex` → exit **0**, `Undefined control sequence` **0**, `^!` **0**, 25 pp A4.
- HTML: `cd rendered && python3 convert.py` → exit 0, 86,041 B, 0 `AUTHOR SLOT`.
- archive: `BUILD_WORK=… sh scratch/ufixman1/build_archive.sh`; `want_cit` re-pinned to `32bee18f…`
  (`want_front` `71f76e60…` unchanged). Built in two independent work dirs → byte-identical; run 1 exits 1 on the
  final v1 comparison (expected), the new build was installed at the shipped path, run 2 reports
  `BYTE-IDENTICAL … cmp exit 0`, exit 0.

## 4. Verification

`check_manifest.py --package <ABSOLUTE extracted root>` → `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0
listed_but_absent=0 / VERDICT PASS` exit 0. `verify/recompute-claims.py` inside the extraction →
`ALL PUBLISHED NUMBERS REPRODUCED: True / VERDICT: PASS / fixture correctness digest c7696edc…` exit 0.
`diff -rq` v1-extract vs v2-extract differs in exactly `CITATION.cff` + re-derived `MANIFEST.json`
(`bytes_total` 844,877 → 845,023; `manifest_self` `5afab382…` → `48344e50…`). v1 archive preserved at
`scratch/uconcept1/superseded-v1-archive.tar.gz`.

## 5. Nothing but the identifier moved

Numeric-literal multiset, before → after, identical totals: `MANUSCRIPT.md` 1195→1195, `main.tex` 1322→1322,
PDF text 1354→1354; each with token deltas exactly `{'23463944': +3, '23463945': -3}` and nothing else.
`\cite` 23 / distinct 13 / `\bibitem` 13 / uncited 0 / unresolved 0 — unchanged.

## 6. New digests for the v2 upload

| artifact | bytes | sha256 | md5 |
|---|---|---|---|
| `released/encoder-crossover-190-released.tar.gz` (37 members) | 159,185 | `196f5311a9b5446af44bafdd688f00035e11f5ec2912f20233e5fa8feedc9a34` | `b3b30f66d231924e02706de0eb3fbc15` |
| `submission/main.tex` | 84,786 | `35a1bc966f6e8f1333085a696fe97557e52215da8553ca20ad7bc84d329d926a` | `2b1df8fee1f2f8805a0458fffb870450` |
| `submission/encoder-crossover-190.tar.gz` | 28,572 | `6743c918f4ec74213e7dfe9d38433f4955e4e667ba2790498b5efeb516aaa184` | `d454f5e2e8776e7979b14799719d6ef4` |
| `rendered/encoder-crossover-190.pdf` (25 pp A4) | 188,819 | `80b3f3e4199f4ab8b4d807e0a2e04ecd4e447e55fa956bf88b0985f339794152` | `323f378a1fe81da89b48237565b0cc19` |
| `rendered/encoder-crossover-190.html` | 86,041 | `e9ffddb0eb322e278c82df2cf3158f32fd14d6748847a9c40ecc1dd464765b46` | `19c0990b690623ecad296d1faf57a20b` |
| `MANUSCRIPT.md` | 71,513 | `5b2bf36f8aea25d4762f3f2ac89610b24d59bb7e83e51942497bdc5d72f559fd` | `349a9d372e29ed5fb4fb3347f65e3319` |

## 7. Card claims that disagreed with measurement (reported, not silently absorbed)

- `rendered/encoder-crossover-190.html`: the DOI is at **`:990`** (+ the survivors at `:992`), not "around `:989-992`".
- Stale "current" figures in `submission/BUILD_NOTES.md`: it records `main.tex` 84,695 B / `397713d7…` and the PDF
  188,364 B / `752747f8…`; measured on disk **before** this unit's edit: `main.tex` 84,786 B / `1468b61e…`,
  PDF 188,820 B / `7b98c109…`. `BUILD_NOTES.md` was left unedited (out of the card's change list).
- `MANUSCRIPT.md` measured 71,513 B / `16934916…` (notes record 71,110 B / `8ba18a51…`);
  payload measured 28,553 B / `2612fe61…` (notes record 28,554 B / `76dfe5db…`).
- The substitution leaves the *Persistent identifier* paragraph naming the concept DOI twice
  ("under that DOI … (concept DOI …)"). No extra duplication was introduced (4 mentions, not 5); rewording was
  out of scope and would move more than the identifier.

## Open objective carried forward
None for this unit beyond the above; the v2 upload is the author's action.
