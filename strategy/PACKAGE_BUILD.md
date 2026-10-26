# PACKAGE_BUILD.md — the release package becomes data, not a script

Unit: **UBUILDALL1** (workspace `/home/zer0null/reserach extarctor`).

`orchestration/units/UBUILD1.build.sh` used to be the build: 969 lines with the
promoted tree, the frozen alternative, the 29-name ship list, the 15-name
never-ship list, the licence template and its sha256, the revision anchors, the
vocabulary blobs, the package name and the destination default all typed into
it.  Copying it per paper is how stale pins and divergent guards happen, and
that failure has already occurred twice in this project.

It is now a **driver**.  Every per-package value lives in
`orchestration/packages/<slug>.toml`; the driver reads it, and the emitted tree
for the existing package is **byte-identical** to what the old script produced.

```
bash orchestration/units/UBUILD1.build.sh --package <slug> [--help]
bash orchestration/units/UBUILD1.build.sh            # -> gated-read-batching
```

The slug names `orchestration/packages/<slug>.toml`.  A bare invocation builds
the built-in default package, which is what it has always done.

| | before | after |
|---|---|---|
| `orchestration/units/UBUILD1.build.sh` | f44c71e96c70bef335d53594761460afd6d0546b0fd3d0a282b962e0de34096d (969 lines) | bbfe1fbe40945cbc1d38d746b373ef6fa0a23ad237b29c6faee06d3b35b841a0 (1033 lines) |
| per-package values | in the script | `orchestration/packages/*.toml` (128 lines for the default) |

The pre-refactor script is kept verbatim at
`scratch/ubuildall1/orig/UBUILD1.build.sh` and is what the proof below builds
with.

---

## 1. Manifest schema

One file per package: `orchestration/packages/<slug>.toml`.  The name is
`<slug>.toml` and the emitted directory is `$DEST/packages/<name>/` — `slug` and
`name` are **separate keys**, so a manifest can be renamed without moving the
package, and a manifest can never be confused with the package it emits.

Paths are `$SRC`-relative unless they begin with `/`, in which case they are
absolute.  They are literal: nothing is probed for on disk to decide what a
value means.  Fragments are resolved relative to the manifest's own directory.

| key | type | meaning |
|---|---|---|
| `schema` | int | must be `1`; the loader refuses anything else |
| `slug` | str | must equal the file name stem (checked at load) |
| `name` | str | emitted directory under `$DEST/packages/`; must be a bare name |
| `dest_default` | str | `$DEST` when the caller does not set one |
| `promoted_san_src` | path | the tree staged into the package |
| `frozen_san_src` | path | the frozen alternative reachable via `SAN_SRC_FROZEN_OVERRIDE=1` |
| `licence_src` | path | licence template directory (copied, never retyped) |
| `licence_files` | [str] | file names copied from `licence_src` |
| `licence_sha256` | str | hash `$DEST/LICENSE` must have, before the scope clause |
| `anchors` | [str] | revision anchors that must appear in ≥1 shipped file |
| `commit_subject` | str | subject of the single commit |
| `index_row` | str | this package's row in the root README index (no fragment; the index accumulates rows across packages) |
| `vocabulary_code` | fragment | `vocabulary/code.txt`, verbatim |
| `vocabulary_public` | fragment | `vocabulary/public.txt`, verbatim |
| `neutralise_rules` | [[str,str]] | literal `[old, new]` path rewrites |
| `neutralise_forbidden` | [str] | substrings that must not survive neutralisation |
| `ship_staged` | [str] | **the complete** staged file list, relative to the package |
| `never_ship` | [str] | names that must be **absent** from the package |

Fragments live in `orchestration/packages/<slug>/`.  They exist because three
per-package artefacts are prose or word lists that must land in the tree
**byte-for-byte**; retyping them inside the driver is exactly the drift this
refactor removes.  They were extracted from the old script's own heredoc bodies
by `scratch/ubuildall1/refactor.py`, and the extraction is byte-compared against
the heredoc bodies in `scratch/ubuildall1/orig/UBUILD1.build.sh`:

```
OK    readme-head.md 3321 bytes
OK    readme-tail.md 1848 bytes
OK    vocabulary-code.txt 4521 bytes
OK    vocabulary-public.txt 372 bytes
```

The manifest for the existing package is
`orchestration/packages/gated-read-batching.toml`; `name = "exp12-encoder-crossover"`
is what keeps the emitted tree at its historical path.

### Loading is fail-closed

The driver hands the TOML to `python3` (stdlib `tomllib`), which emits
`shlex`-quoted shell assignments.  Exit 2, before anything is touched, on:
missing manifest file; missing required key; `schema != 1`; `slug` disagreeing
with the file name; a non-string/empty string where one is required;
non-string array members; `neutralise_rules` not a list of `[old, new]` string
pairs; a missing fragment file; `python3` without `tomllib`.  `M_NAME` is then
checked to be a bare directory name so it cannot escape `$DEST/packages/`.

---

## 2. The two-source-of-truth tripwire (why the old literals survived)

`tests/test_build_wiring.py` derives the shipped wiring from the **script text**:
`PROMOTED_SAN_SRC`, `FROZEN_SAN_SRC`, the `SHIP_STAGED=( … )` block, the wiring
line, the guard strings, the licence literal, `exit "$GATE_RC"`.  Those literals
are therefore kept in the driver as the **built-in default package's declaration
in code**, and they are *asserted* against the manifest:

* the default package's `promoted_san_src`, `frozen_san_src`, `ship_staged`,
  `never_ship` and `licence_sha256` must equal the literals, or the build stops
  with `exit 2` before the staging step;
* `tests/test_package_build.py`
  (`test_default_manifest_agrees_with_the_drivers_built_in_default_block`) checks
  the same agreement from the manifest side.

So there are two sources of truth, and **editing either one alone stops the
build**.  That is a strictly stronger position than before, when the script was
the only source and nothing checked it against anything.

---

## 3. Which guards moved, which stayed

**Moved into data (guarded by the tripwire for the default package, by the loader
for every package):** promoted tree, frozen tree, ship list, never-ship list,
licence template path, licence file list, licence sha256, anchors, package name,
commit subject, README prose, code/public vocabulary, neutralisation rules and
their forbidden-substring check, destination default.

**Stayed hard-coded in the driver, on purpose:**

| guard | why it stayed |
|---|---|
| `DEST` suffix guard `case "$DEST" in */research-publish-packages)` | `tests/test_build_wiring.py` asserts that literal text.  It also expresses a repository-wide rule — the driver only ever `rm -rf`s a release destination — not a per-package one.  The manifest's `dest_default` is subject to it. |
| The `rm -rf` + `mkdir` sequencing and the "removing any previous target" step string | same: the wiring test requires the wiring line to precede this literal |
| The neutralisation *check* (`any f in text or f.lower() in text.lower()`) | the rules are data; the check is the machinery and must not be per-package |
| `gate.sh` itself (`:661-838` heredoc) | byte-identical for every package; it is a positive vocabulary checker, and a package varies the vocabulary it checks against, not the checker |
| `vocabulary/english.txt` derivation, `vocabulary/data.txt` key derivation | derived from the machine's dictionaries and from the package's own content; nothing to declare |
| `.gitignore`, the LICENSE scope-clause append, the COMMIT body, `SELF_EXCLUDED`, the git identity block | identical for every package today; parameterising them would add keys nothing varies |
| `exit "$GATE_RC"` near the end | the gate's status *is* the build's status; required verbatim by the wiring test |

**Nothing was weakened, disabled or commented out.**  `git diff` of the driver
against `scratch/ubuildall1/orig/UBUILD1.build.sh` adds 442 `+`/`-` lines, all
of them either the new driver prologue, the manifest-override blocks, or the
replacement of a heredoc with a `cat` of the fragment extracted from it.

### No package digest is pinned

The driver's only 64-hex literal is the LICENCE-template default; the manifest's
only 64-hex value is `licence_sha256`.  No digest of the package, the staged
tree or the emitted tree is pinned anywhere.
`test_no_package_digest_is_pinned_anywhere` fails if either changes.

---

## 4. Byte-identity proof

Two independent destinations, both under `scratch/ubuildall1/` (the exclusion
gate is never pointed at a real release destination):

```
cd "/home/zer0null/reserach extarctor"
W="/home/zer0null/reserach extarctor/scratch/ubuildall1"
DEST="$W/old/dest/research-publish-packages" \
  bash scratch/ubuildall1/orig/UBUILD1.build.sh                       # OLD exit=1
DEST="$W/new/dest/research-publish-packages" \
  bash orchestration/units/UBUILD1.build.sh --package gated-read-batching   # NEW exit=1
```

**Comparison command and literal output:**

```
$ diff -r --exclude=.git \
    "$W/old/dest/research-publish-packages" \
    "$W/new/dest/research-publish-packages"
$ echo $?
0
```

`diff -r` reports nothing and exits 0.  Because `diff` ignores neither mtimes nor
anything else here, the stronger statement is a content-hash manifest over every
emitted file:

```
$ ( cd "$W/old/dest/research-publish-packages" && find . -path ./.git -prune -o -type f -print0 | sort -z | xargs -0 sha256sum ) > old.files.sha256
$ ( cd "$W/new/dest/research-publish-packages" && find . -path ./.git -prune -o -type f -print0 | sort -z | xargs -0 sha256sum ) > new.files.sha256
$ diff -u old.files.sha256 new.files.sha256
$ echo $?
0
IDENTICAL: 39 files, all sha256 equal
```

The git layer is identical too, which rules out a rewritten commit body or tree:

```
old sha=245449617de274d8b7ee3059e399d25f5c30a965 count=1 status=0
new sha=245449617de274d8b7ee3059e399d25f5c30a965 count=1 status=0
$ diff <(git -C "$W/old/…" ls-files -s | sort) <(git -C "$W/new/…" ls-files -s | sort)
INDEX IDENTICAL
```

39 emitted files, not 29: the 29 staged files become 29 shipped files plus
`README.md`, `.gitignore`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`,
`gate.sh`, `vocabulary/{english,code,public,data}.txt` and `MANIFEST.json`.

**Pre-existing condition, reported rather than papered over:** both builds exit
**1**, because the exclusion gate **fails** on the material as it stands today:

```
flagged tokens: 1133
out-of-vocabulary token lines printed: 1133
GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).
```

That is identical before and after the refactor — the pristine script produces
it too — so it is a property of the shipped material (e.g. `.DS_Store` in
`.gitignore`, `licensor` in `COMMERCIAL.md`), not of the refactor.  The driver
neither swallows nor upgrades it: the exit code is the gate's exit code.

**Where the stdout does differ** (the emitted tree does not): the step banner now
names the package, the destination is the new scratch path, and the per-directory
inventory is generic rather than naming `fixture/ results/ second-labeller/
verify/` — that list was itself per-package, so it now enumerates the package's
top-level directories.  Nothing else in the two logs differs.

---

## 5. Red → green proof for a stale manifest entry

`tests/test_package_build.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is`
compares `ship_staged` against the **actual file set of the promoted tree**, both
sides derived from the manifest, not from the script.

Green first:

```
$ PYTHONPATH=src:. python3 -m pytest tests/test_build_wiring.py tests/test_package_build.py -q
..........................                                               [100%]
26 passed (30 after UFIXDRIVER1) in 0.44s
```

Red — one ship-list entry mutated to name a file the promoted tree does not have
(`"results/STALE-ENTRY.json"` inserted after `"results/REPORT.md"`):

```
>           assert listed == present, (
E               only in ship_staged: ['results/STALE-ENTRY.json']
FAILED tests/test_package_build.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is
FAILED tests/test_package_build.py::test_default_manifest_agrees_with_the_drivers_built_in_default_block
FAILED tests/test_package_build.py::test_the_gate_result_governs_the_exit_code
3 failed, 12 passed in 0.05s
```

The build refuses it independently, at the tripwire, before touching `$DEST`:

```
driver exit: 2
['FATAL: manifest ship_staged disagrees with the built-in default block']
```

Restore, green again:

```
$ cp scratch/ubuildall1/gated-read-batching.toml.bak orchestration/packages/gated-read-batching.toml
$ PYTHONPATH=src:. python3 -m pytest tests/test_build_wiring.py tests/test_package_build.py -q
..........................                                               [100%]
26 passed (30 after UFIXDRIVER1) in 0.43s
```

`tests/test_build_wiring.py` was **not modified** and still passes its 11 tests;
it is the thing that keeps the driver's default block honest from the script
side.

### The rest of `tests/test_package_build.py`

* full schema, `slug == file name`, bare `name` on every manifest;
* every fragment and every licence file named by a manifest exists;
* promoted and frozen trees exist in this workspace;
* `never_ship` disjoint from `ship_staged`, and the driver still contains the
  `FATAL: NEVER_SHIP entry is present in the package` and
  `FATAL: ship-list names a file the package does not have` checks;
* no pinned package digest (above);
* manifest ↔ built-in-default-block agreement (above);
* `--package no-such-package-xyz` exits **2**, prints
  `FATAL: no manifest for package`, and does **not** create `DEST`;
* `test_the_gate_result_governs_the_exit_code` runs the real driver into
  `tmp_path` and asserts the exit code *tracks* the gate: `GATE RESULT: FAIL`
  ⇒ exit ≠ 0 and `the exclusion gate FAILED` is printed, while a `PASS` ⇒
  exit 0.  A build that swallowed the gate's status cannot satisfy either branch.

Reproduce all of it with:

```
PYTHONPATH=src:. python3 -m pytest tests/test_build_wiring.py tests/test_package_build.py -q
```

(A bare `pytest` fails at collection because `tests/conftest.py` imports a module
that does not exist — that is pre-existing and unrelated.)

---

## 6. What could not be made generic

1. **The `DEST` suffix guard** `*/research-publish-packages` and the
   "removing any previous target" step string stay hard-coded, because
   `tests/test_build_wiring.py` asserts their literal text.  They are also
   repository-wide, not per-package.
2. **The default package's literal block** stays in the driver
   (`PROMOTED_SAN_SRC`, `FROZEN_SAN_SRC`, `SHIP_STAGED`, `NEVER_SHIP`, the
   licence hash).  The wiring test parses the script, so deleting them would
   delete that guard.  They are duplicated exactly once, and the tripwire makes
   the duplication safe rather than silent.  A follow-up unit could re-target
   `test_build_wiring.py` at the manifest and then delete the block; that is a
   change to a guard, so it is not made here.
3. **`gate.sh`, `.gitignore`, the LICENSE scope clause and the commit body** are
   identical for all three papers and stay hard-coded.  If a future package needs
   a different gate, that is a genuine fork of the checker and should be designed
   deliberately rather than parameterised by accident.
4. **`vocabulary/english.txt`** depends on the machine's `/usr/share/dict`
   contents, so it is not a manifest value and the gate's verdict is
   machine-dependent.  The build records the sources and word count in its log.
5. **The root README names exactly one package.**  Its per-package text is now a
   fragment, so a second package gets its own README, but a *multi-package
   index* at the repository root is not modelled — each manifest still writes the
   whole `README.md`.  Two packages built into one destination would overwrite
   each other's root README.
6. **`MANIFEST.json` inside the package** is generated by the script as before;
   it is not manifest-driven and was not touched.

---

## 7. Files

| path | what |
|---|---|
| `orchestration/packages/gated-read-batching.toml` | manifest for the existing package |
| `orchestration/packages/gated-read-batching/` | its prose and vocabulary fragments |
| `orchestration/units/UBUILD1.build.sh` | the driver |
| `tests/test_package_build.py` | manifest ↔ tree guards |
| `tests/test_build_wiring.py` | unchanged; script ↔ tree guards |
| `scratch/ubuildall1/orig/UBUILD1.build.sh` | the pre-refactor script, verbatim |
| `scratch/ubuildall1/refactor.py` | the extraction + splice, with anchors asserted |
| `scratch/ubuildall1/{old,new}.build.log` | the two builds compared above |
| `scratch/ubuildall1/old.files.sha256`, `new.files.sha256` | the content-hash manifests |
| `scratch/ubuildall1/gated-read-batching.toml.bak` | used for the red→green restore |

`refactor.py` re-reads `scratch/ubuildall1/orig/UBUILD1.build.sh` (never the live
path) and asserts a known substring in every line range it splices, so a stale
line number aborts instead of corrupting the driver.  It is kept for provenance;
the driver is now the source and needs no generator.

---

## 8. UFIXDRIVER1 -- the two second-package gaps (closed)

`strategy/RELEASE_BUILD_3.md` §6 named two defects that survived the per-package
refactor. Both are closed, both fail closed, and both are derived from the
manifest rather than from a new hand-maintained literal.

### 8.1 Gap 1 -- the ship-list/tree check now runs for EVERY package
The old two-way tripwire only compared the driver's built-in default block with
the default manifest (`if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]`), so any other
package could declare a `ship_staged` list that disagreed with the tree it
pinned and nothing noticed. For ANY slug the driver now walks
`promoted_san_src` (excluding paths with a `.git` component) and requires
`ship_staged` to equal that file set exactly, else it prints the named error

    FATAL: SHIP-LIST/TREE MISMATCH for package '<slug>'

and exits 2. List and tree both come from the manifest, so the check cannot go
stale the way a third hand-written literal would. It runs after the per-package
clean step but BEFORE anything is staged, so a mismatch ships zero files.
Red proof (manifest COPY perturbed so `ship_staged` names
`results/STALE-ENTRY.json`): exit 2, the error above, `listed but not on disk:
['results/STALE-ENTRY.json']`, 0 staged files. Unperturbed copy prints
`ship-list/tree check: 29 declared file(s) == 29 present in
/home/zer0null/reserach extarctor/scratch/uneutral10/package`.

### 8.2 Gap 2 -- the archive README is a manifest-driven, accumulating index
`readme_head`/`readme_tail` are gone from the schema. Each manifest supplies
`index_row`, one table row. The build regenerates `$DEST/README.md` as an index
over every manifest whose `name` directory is present in the destination,
ordered by manifest slug; each package's prose still ships as that package's own
`README.md`. The clean step now removes only `$PKG` instead of the whole `$DEST`,
so a second package is ADDED beside the first instead of replacing it. Proof:
building `gated-read-batching` then `encoder-crossover-190` into one scratch
destination leaves both `packages/exp12-encoder-crossover/` and
`packages/encoder-crossover-190/`, and a README with both rows (encoder first,
then exp12).

### 8.3 Guards that did not move
The licence sha256 guard, the fail-closed exclusion gate, the never-ship absence
checks and the no-package-digest-pinned rule are unchanged, and the
`PROMOTED_SAN_SRC` pin line is untouched. `tests/test_build_wiring.py` is
unmodified and still passes; it requires the `removing any previous target` step
to run, which is why the ship-list/tree check sits immediately after the
per-package clean step.

Tests added (`tests/test_package_build.py`):
`test_the_driver_checks_the_ship_list_against_the_pinned_tree`,
`test_ship_list_check_fails_closed_on_a_perturbed_manifest_copy`,
`test_ship_list_check_passes_green_on_an_unperturbed_manifest_copy`,
`test_root_readme_index_accumulates_two_packages`.

Command: `PYTHONPATH=src python3 -m pytest tests/test_package_build.py tests/test_build_wiring.py -q`
Result: `30 passed in 1.60s` (26 before this unit).
