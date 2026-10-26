# VERIFICATION REPORT — UBUILDALL1 build-driver refactor (verifier UVERBUILD1)

**Verdict: PASS.** Every safety-relevant claim of UBUILDALL1 reproduced independently, from fresh
builds into paths this unit owns (`scratch/uverbuild1/**`, `scratch/uverbuild1/red/**`,
`scratch/uverbuild1/tw2/**`). No claim was copied from the author's report; the author's own
`scratch/ubuildall1/**` outputs were not reused.

**Artifacts under verification (pinned by sha256):**

| artifact | sha256 |
|---|---|
| pristine pre-refactor script `scratch/ubuildall1/orig/UBUILD1.build.sh` | `f44c71e96c70bef335d53594761460afd6d0546b0fd3d0a282b962e0de34096d` |
| driver `orchestration/units/UBUILD1.build.sh` | `bbfe1fbe40945cbc1d38d746b373ef6fa0a23ad237b29c6faee06d3b35b841a0` |
| `orchestration/packages/gated-read-batching.toml` | `e8e06b71f0fb299af69205ba86dfb616524279407b60012be07449edc081dcff` |
| `.../gated-read-batching/readme-head.md` | `c8ff5608056cb6855e5d94c10700e03b52b6f9e6b4942afd34fc9522d910cfd1` |
| `.../gated-read-batching/readme-tail.md` | `f440b3318eeb2fc5b11b37d88c5abc7d265b71405c42b2375b7c6038b2bd0d22` |
| `.../gated-read-batching/vocabulary-code.txt` | `6b4042f1005184c318fe433e1d7acfc02b14f000a2458ed8d2795db51acdd3b9` |
| `.../gated-read-batching/vocabulary-public.txt` | `15be3cd6eb519b11831e1fcf3215d26c237f490318e273665e39f3b596a1eedc` |

Constraints honoured: `/home/zer0null/Duval` was never touched and no `git` command was run against
it; nothing was fetched or installed; the builder, the manifest and the tests were not edited.

---

## 1. Byte-identity, reproduced from scratch

Two fresh destinations, one per script, from the pristine copy and the driver:

```
DEST=$PWD/scratch/uverbuild1/orig/dest/research-publish-packages bash scratch/uverbuild1/orig/UBUILD1.build.sh
DEST=$PWD/scratch/uverbuild1/new/dest/research-publish-packages  bash orchestration/units/UBUILD1.build.sh --package gated-read-batching
```

```
ORIG_EXIT=1
NEW_EXIT=1
diff -r --exclude=.git scratch/uverbuild1/orig/dest scratch/uverbuild1/new/dest
DIFF_ORIG_NEW_RC=0                      # no output at all
```

File counts and the per-file sha256 lists (excluding `.git`):

```
orig files=39 sha=2454496
new  files=39 sha=2454496
det2 files=39 sha=2454496
13d3fc2e6f06b65a749909e63edd78516ac2f88caa9d791171c02c578f31fe73  orig.sha256
13d3fc2e6f06b65a749909e63edd78516ac2f88caa9d791171c02c578f31fe73  new.sha256
13d3fc2e6f06b65a749909e63edd78516ac2f88caa9d791171c02c578f31fe73  det2.sha256
ORIG_NEW_SHA_IDENTICAL
```

Tree total matches the inventory line the build itself prints:
`repo total : 39 files, 2.5M` (the "109" in an early mis-run of this unit was its own bug: the find
pruned only the top-level `.git` and counted `research-publish-packages/.git/**`; the corrected
command `find <dest>/research-publish-packages -name .git -prune -o -type f -print | wc -l` gives 39).
Full commit sha, identical in all three trees: `41ad35b68bcee486a67c434afbc84b0724d9f5b4`.

**Claim "the existing package comes out byte-identical": REPRODUCED.**

## 2. Exit codes and the gate

```
ORIG_EXIT=1 ; NEW_EXIT=1 ; DET2_EXIT=1
GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).     (all three builds, identical line)
BUILD COMPLETE — the exclusion gate FAILED (exit 1).      (all three builds)
bash .../new/dest/research-publish-packages/gate.sh ; echo RC   -> GATE_RC_DIRECT=1
grep -c 'the exclusion gate PASSED\|GATE RESULT: PASS' new.build.log -> 0
grep -c 'the exclusion gate FAILED\|GATE RESULT: FAIL' new.build.log -> 2
```

Exit code equals the gate's exit code (1 = 1), and a failing gate is never reported as a pass: the
only gate verdict in the log is FAILED, and the failure path ends at
`exit "$GATE_RC"` (`orchestration/units/UBUILD1.build.sh:1029`). The 1133-token count is identical
across all three builds and matches the author's number.

## 3. Determinism (driver run twice)

Two driver runs (`--package gated-read-batching` and the bare default) into independent destinations:

```
diff -r --exclude=.git scratch/uverbuild1/new/dest scratch/uverbuild1/det2/dest
DIFF_NEW_DET2_RC=0                      # no output
NEW_DET2_SHA_IDENTICAL
```

Nothing differs. The bare invocation (no `--package`) selects the same default slug
(`DEFAULT_SLUG="gated-read-batching"`, `orchestration/units/UBUILD1.build.sh:132,145`), so the refactor
did not change the no-argument behaviour. Because `COMMIT_DATE` is pinned (:159), the commit sha is
identical too. **No determinism defect found.**

## 4. Guards — present, and not weakened

Read out of the driver (line numbers are the driver's), each compared against the pristine script:

| guard | driver line | quote | orig |
|---|---|---|---|
| licence sha256 drift | :560-562 | `LIC_SHA="$(sha256sum "$DEST/LICENSE" \| cut -d' ' -f1)"` … `FATAL: LICENSE template drift: sha256 is $LIC_SHA, expected $LIC_SHA_EXPECTED'" >&2; exit 1; }` | present (orig :431-433, literal inline) — **strengthened**: the literal is now also tripwired to the manifest (:555-558) |
| never-ship absence | :498-505 | `if [ -e "$PKG/$rel" ] \|\| [ -e "$DEST/$rel" ]; then echo "FATAL: NEVER_SHIP entry is present in the package: $rel" >&2` … `[ "$ns" -eq 0 ] \|\| exit 1` | present verbatim |
| fail-closed ship list | :437-446 | `[ ! -f "$PKG/$rel" ]` → `FATAL: ship-list names a file the package does not have: $rel`; `[ "$missing" -eq 0 ] \|\| exit 1` | present verbatim |
| `DEST` suffix guard | :292-295 | `case "$DEST" in */research-publish-packages) : ;; *) echo "FATAL: refusing to rm -rf '$DEST' — DEST must end in /research-publish-packages" >&2; exit 2 ;; esac` | present verbatim |
| override warning before the first destructive step | warning :332-341, `rm -rf "$DEST"` :354 | `echo "SAN_SRC WIRING: tree=$SAN_SRC promoted_default=$_san_promoted"` then `SAN_SRC WIRING: WARNING - NOT the promoted release artifact;` | present verbatim; 2 occurrences in each script |
| gate exit propagation | :1018-1029 | `bash "$DEST/gate.sh"; GATE_RC=$?` … `exit "$GATE_RC"` | present verbatim |

Behaviourally confirmed, not just read:

```
DEST=/tmp/not-a-repo bash orchestration/units/UBUILD1.build.sh --package gated-read-batching
BADDEST_RC=2
FATAL: refusing to rm -rf '/tmp/not-a-repo' — DEST must end in /research-publish-packages

DEST=.../ovr/... SAN_SRC_OVERRIDE=$D/emptysrc bash orchestration/units/UBUILD1.build.sh --package gated-read-batching
1:SAN_SRC WIRING: tree=.../emptysrc promoted_default=no
2:SAN_SRC WIRING: WARNING - NOT the promoted release artifact; the promoted default is
9:=== [..] removing any previous target
FATAL: ship-list names a file the package does not have: COMMERCIAL.md
```

The override is honoured from the environment only, the WARNING is printed at log line 2 and the
first destructive step (`removing any previous target` → `rm -rf "$DEST"`, :354) only at line 9, so
the warning precedes it. The override never changes the exit code (still governed by the ship-list
and the gate).

**No guard was removed, weakened, or made conditional.**

## 5. No pinned package digest

```
grep -noE '[0-9a-f]{64}' orchestration/units/UBUILD1.build.sh
554:3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900
grep -rnoE '[0-9a-f]{64}' orchestration/packages/
orchestration/packages/gated-read-batching.toml:45:3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900
```

Exactly two 64-hex values exist in the whole package set — the driver's `LIC_SHA_EXPECTED` and the
manifest's `licence_sha256` — and they are the same value, the *named* licence-template guard. The
four fragment files contain none; `orchestration/packages/` holds one manifest. **No package digest
is pinned anywhere**, so the manifest cannot defeat the refactor by freezing today's tree.

## 6. The tripwire, on a COPY of the manifest

A second root (`scratch/uverbuild1/tw2/`) was built with the driver copied to
`tw2/orchestration/units/UBUILD1.build.sh` (so its `_REPO_ROOT` resolves to `tw2`) and a **copy** of
the manifest at `tw2/orchestration/packages/gated-read-batching.toml`. One ship-list entry was
mutated in the copy: `results/REPORT.md` → `results/STALE-ENTRY.json`.

```
TRIPWIRE_RC=2
8:FATAL: manifest ship_staged disagrees with the built-in default block
real manifest sha BEFORE: e8e06b71f0fb299af69205ba86dfb616524279407b60012be07449edc081dcff
real manifest sha AFTER : e8e06b71f0fb299af69205ba86dfb616524279407b60012be07449edc081dcff
grep -c 'results/REPORT.md' orchestration/packages/gated-read-batching.toml -> 1
```

Literal error and exit code as the author reported. **The real manifest is byte-unchanged.**

## 7. Tests, and red→green on a copy

```
PYTHONPATH=src:. python3 -m pytest tests/test_build_wiring.py tests/test_package_build.py -q
26 passed in 0.44s
collected: tests/test_build_wiring.py -> 11 tests ; tests/test_package_build.py -> 15 tests
```

Red→green was reproduced against a mirror root `scratch/uverbuild1/red/` whose
`red/orchestration/packages/gated-read-batching.toml` is a real copy (mutated) while every other path
is a symlink to the workspace, so the test file itself is the unmodified original
(`red/tests/test_package_build.py` is a byte copy; `ROOT` resolves to `red/`):

```
RED   (results/REPORT.md -> results/STALE-ENTRY.json in the copy):
  3 failed, 12 passed in 0.06s
  FAILED test_ship_list_is_exactly_the_promoted_tree_as_it_is
  FAILED test_default_manifest_agrees_with_the_drivers_built_in_default_block
  FAILED test_the_gate_result_governs_the_exit_code
  RED_DRIVER_RC=2  FATAL: manifest ship_staged disagrees with the built-in default block
GREEN (copy restored from the real manifest):
  15 passed in 0.33s
real manifest sha: e8e06b71f0fb299af69205ba86dfb616524279407b60012be07449edc081dcff  (unchanged)
```

The failing three are exactly the three the author named, and the driver exits 2 with the exact
message. One driver build is fast (`real 0m0.310s`), which is why the full 26-test run fits in 0.44s;
the gate test really does run a build (it is the test that failed in the red state).

## 8. The honest question: does the suite derive from the manifest?

**Judgement: it derives.** The values it checks are read from the manifest and the disk, not retyped:

* `tests/test_package_build.py:151` — `listed = sorted(man["ship_staged"])` is compared against
  `present`, computed by walking `resolve(man["promoted_san_src"])` at :145-150. Add/remove/rename a
  file on either side and it is red; nothing about the expected set is hard-coded.
* `tests/test_package_build.py:220-221` — `sorted(man["ship_staged"]) == sorted(_block(SHIP_BLOCK, text))`
  and the same for `never_ship`: the manifest is cross-checked against the *driver's* parsed literal
  block, so the two sources of truth are forced to agree without a third copy of the list.
* `tests/test_package_build.py:184-195` — scans the manifest and driver text for `HEX64` and asserts
  the only value is `man["licence_sha256"]`; the expectation is computed, not written down.
* `tests/test_package_build.py:267-278` — the pass/fail expectation is taken from the log the build
  actually printed (`"GATE RESULT: PASS" in log` XOR `FAIL`), then the exit code is asserted to track
  it; a build that swallowed the gate status cannot satisfy either branch.
* The one place expectations *are* literals is the guard-presence pair, and that is the correct
  target: `tests/test_package_build.py:168` asserts the substring
  `"FATAL: NEVER_SHIP entry is present in the package"` and :174 asserts
  `'echo "FATAL: ship-list names a file the package does not have: $rel" >&2'` are still in the
  driver. Those fail if the guard is deleted — they are about the builder, not about the tree, so
  they cannot make the suite "agree with the builder for the wrong reason". Cost: they are
  wording-brittle (rephrasing the guard FATAL would redden them without a behavioural regression).

So the suite would catch a stale manifest; it does not merely restate the manifest.

---

## Findings

**contradicted** — none.

**not_reproduced** — none. Every claim in the author's evidence block was re-derived from fresh
builds: byte-identity (39 files, identical sha256 lists and commit sha), identical exit code 1 and the
literal `GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s)`, 26 passed (11+15), the 3-test red with
driver exit 2 and the exact FATAL line, and the two-way tripwire.

**overstated** — one minor, cosmetic item, about
`orchestration/units/UBUILD1.build.sh:21`: *"A second run produces the same tree and, because the
commit date is pinned, the SAME commit SHA. Verified: two consecutive runs both gave sha 2b0e... "*
The pinned-commit/SAME-sha half is true (all three of my trees are
`41ad35b68bcee486a67c434afbc84b0724d9f5b4`), but the literal `2b0e...` is stale — no tree in this
workspace has that sha. It is a comment, not a safety property, and it is present identically in the
pristine pre-refactor copy (`scratch/ubuildall1/orig/UBUILD1.build.sh:15`), so the refactor neither
introduced nor relied on it.

**unverified** — the claim *"`tests/test_build_wiring.py` unmodified"* cannot be established here:
both test files are untracked in the workspace git repo (`?? tests/test_build_wiring.py`,
`?? tests/test_package_build.py`), so there is no committed baseline to diff against. Its mtime
(Oct 16 15:13) predates the refactor's files (17:18-17:20), which is consistent with unmodified but is
not proof. Mitigating evidence: its content is driver-derived only — it parses the driver's literal
`SHIP_STAGED` block (`tests/test_build_wiring.py:60,88`) and never reads the manifest — so it was at
least not re-pointed at the new manifest.

## Claim that survives (recorded, not padded)

The core claim — *a `--package <slug>` driver with per-package values in
`orchestration/packages/<slug>.toml` reproduces the pre-refactor package byte-for-byte while every
guard survives* — survives independent reproduction, including determinism across runs and the
red→green tripwire on a manifest copy.
