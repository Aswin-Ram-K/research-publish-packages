# EMITTED_TREE — what the build actually emits, and what the gate actually scans

Unit: **UEMIT1**. Measured, not averaged. Build script under audit:
`orchestration/units/UBUILD1.build.sh` (968 lines, re-pinned to
`scratch/uneutral10/package`, 29 files, `promoted_default=yes`).
Fresh run: `DEST="$PWD/scratch/uemit1/dest/research-publish-packages"` →
full log at `scratch/uemit1/build.log`. Exit 1 (gate FAIL). Nothing edited.

## 1. The emission stage (`UBUILD1.build.sh:155-238`)

- `:155` `PKG="$DEST/packages/exp12-encoder-crossover"`.
- `:221` `cp -r "$SAN_SRC/." "$PKG/"` — the promoted tree is staged **verbatim**
  (`scratch/uneutral10/package`, 29 files). Log: `staged 29 file(s): 29 kept, 0 dropped`.
- `:186-238` prune to the fail-closed `SHIP_STAGED` list (29 entries): `in_ship()`;
  every unlisted staged file is `rm -f`'d, and a listed-but-missing file is FATAL
  (`FATAL: ship-list names a file the package does not have: <rel>`).
- Author-written files, at `$DEST` root, not `$PKG`:
  - `:306,372,374` `README.md` (root README, licence table, gate description)
  - `:437-452` `LICENSE` (PolyForm NC 1.0.0 + scope clause; sha256-gated at `:430-432`)
  - `:424` `COMMERCIAL.md`, `CONTRIBUTING.md`
  - `:455` `.gitignore`
  - `:492-593` `gate.sh` + `vocabulary/`: `english.txt` (74,959 words frozen from
    `/usr/share/dict/*`), `code.txt`, `public.txt`
  - `:599-656` `vocabulary/data.txt` — **generated**, 501 declared JSON keys derived
    from 32 parsed documents (JSON object keys only, fail-closed on empty)
- `:925-938` `git init -q -b main` **at `$DEST`**, `git add -A`, one commit
  (`GIT_COMMITTER_DATE="$COMMIT_DATE"`), no remote. So the repo's `.git` is a
  **build artifact of the destination**, at the repo root — not inside `$PKG`.
- `:943` the script's own inventory line counts `find "$DEST" -path "$DEST/.git" -prune -o -type f -print`.
- The script applies **no** transforms to the payload beyond the three literal
  path-neutralisation rules (`:845+`); log: `0 occurrence(s) in 0 file(s)`.

## 2. Emitted counts, two ways (fresh run)

```
find "$D" -type f | wc -l                                # 109   (includes .git)
find "$D" -type f -not -path '*/.git/*' | wc -l          #  39   (excludes .git)
find "$D/.git" -type f | wc -l                           #  70   (.git internals)
```

Breakdown excluding `.git` (39 files, by top-level path):

| top-level | files | what |
|---|---|---|
| `packages/` | **29** | the promoted ship-list payload (verbatim `$SAN_SRC`) |
| `(root files)` | **6** | `README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `.gitignore`, `gate.sh` |
| `vocabulary/` | **4** | `english.txt`, `code.txt`, `public.txt`, `data.txt` (generated) |

**109 = 39 working-tree files + 70 `.git` object-store files.**
The script's own inventory says `repo total : 39 files, 2.5M` — consistent.

## 3. What the gate scans

Gate heredoc `UBUILD1.build.sh:660-836`.
- Scan root: `ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"` = **`$DEST`**
  (the whole repository root), invoked at `:954` as `bash "$DEST/gate.sh"`.
- File-selection rule (`os.walk(ROOT)` at `:804-812`): all files recursively, subject to
  - `SKIP_DIRS = {".git"}` (`:766`) → `.git` internals **not** scanned;
  - `if rel.split(os.sep)[0] == VOCAB_REL: continue` (`:807`) → top-level
    `vocabulary/` **not** scanned ("THE CHECKER DOES NOT SCAN ITS OWN vocabulary/ INPUTS").
- Nothing else is excluded. `gate.sh` itself and the root `README.md` **are** scanned.
- Measured scan set: `find "$D" -type f -not -path '*/.git/*' -not -path '*/vocabulary/*' | wc -l`
  → **35 files** = 39 − 4 vocabulary files (29 payload + 6 root).
- The known past defect (gate scanning its own `vocabulary/` inputs) is **not**
  recurring: offenders from `vocabulary/` files = 0, and the run prints
  `vocabulary/ is not scanned; the list is complete`. `README.md` is scanned (14
  offender lines); `gate.sh` contributes 0 here because it carries only declared vocabulary.

## 4. Gate count measured

`bash "$D/gate.sh"` → `flagged tokens: 1133`, `GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s)`, exit 1.
Class split (`GATE_JSON=1`): `{'prose-source': 774, 'data': 359}`.
Top files: `results/REPORT.md` 183, `second-labeller/compare.py` 90,
`verify/recompute-claims.py` 87, `second-labeller/EVIDENCE.md` 78,
`fixture/reflex-decisions.ts` 72.
This reproduces `scratch/ufixpin1/build.log` exactly (1,133).

## 5. Settling 38/39 vs 109

Dest trees still on disk, counted directly:

```
scratch/uwire3/dest/research-publish-packages  excl .git = 38   incl .git = 107   vocabulary = 3
scratch/ugate3/dest                            excl .git = 39   incl .git = 109   vocabulary >= 4
scratch/ugate2/dest                            excl .git = 39   incl .git = 109
scratch/uver30/dest                            excl .git = 39   incl .git = 109
scratch/ufixpin1/dest                          excl .git = 39   incl .git = 109
scratch/uemit1/dest                            excl .git = 39   incl .git = 109
```

- **38 vs 39 is a revision difference, not a counting difference**: `uwire3`
  predates `vocabulary/data.txt` (3 vocabulary files; its log says `repo total : 38 files`).
  Every later revision emits 39 excluding `.git`.
- **39 vs 109 is purely include/exclude `.git`** (70 `.git` files).

Gate counts measured in the older trees: 1,689 (`uwire3`), 1,398/1,399 (`ugate2`),
1,410/1,411 (`ugate3`); `ugate2/residual_by_class.txt` splits its 1,398 as
b-thirdparty 1023, c-mechanism 268, a-schema 64, unclassified 43.
Against `scratch/ugate2/gate_old.sh`, the current gate differs by (i) loading a
**new fourth vocabulary file `data.txt`** (declared JSON keys — 501 keys from 32
documents) and (ii) `continue`-ing over `vocabulary/`. The payload did not change:
29 staged files in every revision, `29 kept, 0 dropped` in both `ufixpin1` and `uemit1`.

## 6. One-sentence reconciliation

The three disagreements are three different denominators: **109 vs 39** counts the
build's own `.git` (70 files) in or out, **38 vs 39** is one added `vocabulary/data.txt`
between revisions, and **1,398/1,410 → 1,133** is a gate *rule* change — the scoped gate
declares 501 JSON keys from `vocabulary/data.txt` (absorbing identifier-shaped data
tokens the older gate flagged) and skips `vocabulary/` — not a shrinking tree.

## 7. The number to quote

> The deliverable is a **39-file working tree, excluding the build's own `.git`**:
> the **29-file promoted package** under `packages/exp12-encoder-crossover/`
> plus a **10-file author-added envelope**.

Envelope, exactly: `README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`,
`.gitignore`, `gate.sh`, and `vocabulary/{english.txt,code.txt,public.txt,data.txt}`.

Do **not** quote 109 as the shipped-file count — it is the repo including its
`.git` object store. Do not quote any gate number as a pass: the current gate
**FAILS** with 1,133 out-of-vocabulary tokens (774 prose/source + 359 data);
`uwire3`'s 1,689 and `ugate2`/`ugate3`'s 1,398/1,410 are older gate revisions and
are not comparable.

## 8. Change log

Nothing changed. No edit to `UBUILD1.build.sh`, any `scratch/*/package`, `papers/`,
`repro/`, or `/home/zer0null/Duval`. Writes confined to `scratch/uemit1/**`,
`strategy/EMITTED_TREE.md`, `orchestration/units/UEMIT1.md`,
`orchestration/handoffs/UEMIT1.json`.
