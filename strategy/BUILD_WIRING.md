# BUILD_WIRING — which tree the release build consumes

**Author:** UWIRE1 (wiring) · **Promoted by:** UWIRE2 (`tree-three-r2`) · **Re-wired by:** UWIRE3
**Scope:** `orchestration/units/UBUILD1.build.sh` · **Status:** the chosen release artifact
**`scratch/uneutral10/package/`** (29 files, 841,306 bytes) **is the default**. The frozen tree stays reachable
through `SAN_SRC_FROZEN_OVERRIDE=1`. Every build prints one machine-greppable line saying which tree it
read and whether it is the promoted default. A regression test guards all of it
(`tests/test_build_wiring.py`).

---

## 1. Scope change (UWIRE3)

The release scope changed: the package ships **data + verification tools only, the harness withheld**.
The build used to stage a 45-file `code/`+`eval/` tree (`scratch/ubij3/tree-three-r2`) and ship
**18 `code/harness/*` entries**. UWIRE3 removed those, re-derived the ship list from the package's real
files, and re-pointed the default at the proven artifact. The package is **flat**: it has no
`paper/`, no `code/`, no `eval/` — its layout is already the shipped layout, so the build stages it
**verbatim**: `cp -r "$SAN_SRC/." "$PKG/"`.

## 2. What the build consumes now

```bash
PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"            # THE DEFAULT — the single re-pin line
FROZEN_SAN_SRC="$SRC/repro/encoder-crossover-190-SANITISED"   # reachable, not default
if   [ -n "${SAN_SRC_OVERRIDE:-}" ]; then SAN_SRC="$SAN_SRC_OVERRIDE"
elif [ "${SAN_SRC_FROZEN_OVERRIDE:-0}" = "1" ]; then SAN_SRC="$FROZEN_SAN_SRC"
else SAN_SRC="$PROMOTED_SAN_SRC"
fi
```

Precedence, and nothing else:

| # | selection | tree |
|---|---|---|
| 1 | `SAN_SRC_OVERRIDE=<abs path>` (highest) | exactly that path — any tree, for ad-hoc runs |
| 2 | `SAN_SRC_FROZEN_OVERRIDE=1` | `$SRC/repro/encoder-crossover-190-SANITISED` (the pre-promotion input) |
| 3 | neither | **`$SRC/scratch/uneutral10/package`** (the promoted release artifact) |

Both variables are honoured **only from the environment** — never guessed from disk, never read from a
file. Neither is interactive:

```bash
# the default (promoted package)
bash orchestration/units/UBUILD1.build.sh

# the frozen pre-promotion input, still reproducible
SAN_SRC_FROZEN_OVERRIDE=1 bash orchestration/units/UBUILD1.build.sh

# any other tree
SAN_SRC_OVERRIDE="/home/zer0null/reserach extarctor/scratch/uneutral10/package" \
  bash orchestration/units/UBUILD1.build.sh
```

### 2.1 The loud wiring line

Every build prints, always and first:

```
SAN_SRC WIRING: tree=<absolute path> promoted_default=<yes|no>
```

When `promoted_default=no` it also prints a `WARNING` naming the promoted default, and — when the frozen
tree is selected — that this is the frozen original sanitised tree. The WARNING never changes the exit
code and never prompts, so builds stay scriptable; it is emitted **before the first destructive step**, so
it is present even in a build that stops immediately.

### 2.2 Consumers of `$SAN_SRC`

`$SAN_SRC` is the package root. Looked up by name, not by line:

| consumer | location | behaviour |
|---|---|---|
| resolution + wiring line | `grep -n '^PROMOTED_SAN_SRC=' …` | the tree root, and the loud line |
| staged copy | `step "staging candidate material…"` | the package staged **verbatim** into `$PKG` |
| `SHIP_STAGED=( … )` | `grep -n '^SHIP_STAGED=(' …` | **29** names; anything staged but unlisted is dropped (fail-closed) |
| fail-closed missing-file check | `FATAL: ship-list names a file the package does not have` | a listed file with no file behind it → `FATAL`, exit 1 |
| `NEVER_SHIP` list | `grep -n '^NEVER_SHIP=(' …` | 15 names asserted **absent** after the prune |
| licence plumbing (`LIC_SRC`) | `step "authoring the licence set…"` | licence templates from `$SRC/strategy/…`; not `$SAN_SRC`-derived |
| positive-vocabulary gate | `step "running the exclusion gate…"` | fails on any out-of-vocabulary token; `exit "$GATE_RC"` |

Only `$SAN_SRC`-derived bytes change with the wiring. The ship list, `NEVER_SHIP`, the licence plumbing,
the anchor assert and the gate are identical on every path.

## 3. Ship list ⇄ package reconciliation (UWIRE3, as measured)

The promoted package holds **29 files** on disk; `SHIP_STAGED` holds **29 names**; the sets are
**identical** (`tests/test_build_wiring.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is` asserts
equality, so a stale pin is RED).

| bucket | files |
|---|---|
| package root | `README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `MANIFEST.json` |
| `fixture/` | `DECISION_CASE_SCHEMA.ts`, `fixture-190.json`, `reflex-decisions.ts` |
| `preregistration/` | `EXP12-typed-channel-comparison-prereg.md` |
| `results/` | `REPORT.md`, `baselines.json`, 6 × `eval-*.json` |
| `second-labeller/` | 12 files (cases, blinded cases, labelsB, metrics, run record, evidence, disagreement ledger, the two tools, `parse_summary.json`, `OWED_CORRECTIONS.md`) |
| `verify/` | `recompute-claims.py` |

Removed from the old list: all **18** `code/harness/*` entries, the 12 `paper/*` entries and the
`eval/*` re-mapping. `MANIFEST.json` and `second-labeller/OWED_CORRECTIONS.md` are now real package
members, so they were **removed from `NEVER_SHIP`** (which asserts absence) and added to the ship list.
`NEVER_SHIP` still holds 15 names — the sanitised-tree process documents (none of which the package has).

**Missing** (listed but not staged → would `FATAL`): **none**.
**Unlisted** (staged but not listed → dropped): **none**.

## 4. Measured effect (UWIRE3, real run)

Run: `DEST="$PWD/scratch/uwire3/dest/research-publish-packages" bash orchestration/units/UBUILD1.build.sh`
(log `scratch/uwire3/build.log`):

| | promoted default (UWIRE3 measurement; tree re-pinned since) |
|---|---|
| staged → kept / dropped | **29 → 29 / 0** |
| ship-list check | `29 staged file(s) present` |
| never-ship check | `15 names checked absent` |
| anchor | `907fa39 present in 4 file(s)` |
| emitted tree | **38 files** (29 package + 9 root: `README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `.gitignore`, `gate.sh`, `vocabulary/{english,code,public}.txt`) |
| gate verdict | `FAIL -- 1689 out-of-vocabulary token(s).` |
| exit code | 1 (the gate) |

**UFIXPIN2 caveat — these numbers are not current for the promoted tree.** They are the UWIRE3 real run
against the tree pinned at that time; the pin has since moved to `scratch/uneutral10/package`, whose
staged/kept, ship-list, never-ship, anchor, emitted-tree and gate counts were **not** re-measured here.
Treat the table as belonging to the superseded tree, not as a statement about `scratch/uneutral10/package`.
Only the §3 ship-list reconciliation (29 names ⇄ 29 files, path sets identical) is known to carry over,
because the two trees ship the same 29 paths.

The gate still fails — by design: the package legitimately contains the instrument's own vocabulary
(that is what the models read). The out-of-vocabulary count falls from **29,936** to **1,689** (17.7×
fewer) once the harness and the corpus-related surface are gone. The build never fails at the ship list.

**Anchor note.** The historical second anchor `ad301ae` lived in the **paper text**
(`papers/encoder-crossover-190`), a separate artifact that is not part of this data+verification package.
The build now asserts the anchor this package actually carries (`907fa39`); the absence of `ad301ae` is
expected, not a regression.

## 5. Designing for UNEUTRAL6

A later unit (**UNEUTRAL6**) is neutralising ten identifiers **inside the package**, so the package's
**digests will change**. Nothing here pins a package digest: the only pinned value is the **path**, in the
single constant line:

```bash
PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"
```

If UNEUTRAL6 lands the neutralised package at a new path (or the old path is replaced by a new tree),
re-pinning is **that one line** — the ship list must then be re-derived from the new tree's real files, and
`test_ship_list_is_exactly_the_promoted_tree_as_it_is` enforces exactly that.

## 6. Reproducing this

```bash
cd "/home/zer0null/reserach extarctor"
# promoted default
DEST="$PWD/scratch/uwire3/dest/research-publish-packages" \
  bash orchestration/units/UBUILD1.build.sh
# the guard
.venv/bin/python -m pytest tests/test_build_wiring.py -q
```

Log: `scratch/uwire3/build.log`. Red→green transcript: `scratch/uwire3/red-green.log`.

## 7. Still open

1. **The gate still fails** (1,689 out-of-vocabulary tokens). A failing gate is by design here, but the
   release cannot pass its own gate until the vocabulary question is settled. Separate unit.
2. **`repro/encoder-crossover-190-SANITISED` is not frozen** in the filesystem sense. If the frozen input
   must be genuinely reproducible, freeze it by digest or point `SAN_SRC_FROZEN_OVERRIDE` at an immutable
   copy.
