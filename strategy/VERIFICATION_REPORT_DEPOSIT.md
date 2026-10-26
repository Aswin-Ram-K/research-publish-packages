# VERIFICATION_REPORT_DEPOSIT — independent re-derivation of the rebuilt deposit archive

**Verifier:** VDEPOSIT1 (not the author — UFIXMAN1 rebuilt the archive).
**Subject:** `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`
**Bound:** 18 tool calls; used 15. **Nothing was edited** outside `scratch/vdeposit1/**` + this file + my unit card/handoff.

## Verdict

**Artifact: PASS — every machine-checkable claim reproduced, most of them stronger than claimed.**
**Exported documents: FAIL — `strategy/DEPOSIT_ARCHIVE.md` and `strategy/DEPOSIT_METADATA.md` are
stale and one states the *opposite policy* to what the shipped archive now does.**
Overall unit result: **partial** (artifact verified; documents not).

## 1. Archive re-derived — reproduced

I copied `scratch/ufixman1/build_archive.sh` to `scratch/vdeposit1/build_vdeposit1.sh`, changing only
`W=` and `OUT=` so nothing outside my scratch dir is written, and ran it twice with the pinned
`GENUTC=2026-10-18T08:05:47Z` (from `scratch/ufixman1/GENERATED_UTC.txt`):

| build | bytes | sha256 |
|---|---|---|
| my run 1 (`scratch/vdeposit1/my-out1.tgz`) | 158,762 | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` |
| my run 2 (`scratch/vdeposit1/my-out2.tgz`) | 158,762 | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` |
| shipped archive (on disk) | 158,762 | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` |

Members: `tar tzf` = **37** lines = **6 directories** (1 top-level `encoder-crossover-190-released/`
+ 5 subdirs) + **31 files**. `cmp`/`sha256sum` byte-identical across both runs and the shipped file.

Superseded archive `scratch/ufixman1/prev-encoder-crossover-190-released.tar.gz` re-measured:
**157,650 B**, sha256 `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3`. Matches claim.

## 2. Red → green (the check that distinguishes a fix from a coincidence) — reproduced

`tools/package/check_manifest.py` gates on five zero-counts; `unlisted = present − listed −
{"MANIFEST.json"}`.

**RED — the 28-file package manifest in the stage** (`scratch/vdeposit1/prev-extract/…`, extracted
from the superseded archive), run as
`python3 tools/package/check_manifest.py --package <abs prev root>`:

```
missing=0 hash_mismatch=0 size_mismatch=0 unlisted=2 listed_but_absent=0
  UNLISTED: CITATION.cff
  UNLISTED: README_DEPOSIT.md
manifest_self_recomputes=True (blank generated_utc; drop manifest_self; sort_keys indent=2)
VERDICT FAIL
EXIT=1
```

**GREEN — the regenerated 30-file manifest** (my extracted archive), same command:

```
missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0
manifest_self_recomputes=True (blank generated_utc; drop manifest_self; sort_keys indent=2)
VERDICT PASS
EXIT=0
```

The guard genuinely fails when the fix is reverted. Exit codes are literal (`1` vs `0`).

## 3. Manifest describes its own tree — reproduced

Extracted archive root `scratch/vdeposit1/extract/encoder-crossover-190-released/`:
`check_manifest.py --package <abs>` → all five counts **0**, `VERDICT PASS`, **exit 0** (literal output
above). This is exactly the required property: every file present is either listed or is
`MANIFEST.json` itself, and every listed file is present with matching sha256 and byte size.

Manifest contents: `files[]` = **30** entries, `counts.files` = **31**, `counts.bytes_total` =
**844,089**, `counts.staged_from_source_tree` = 20, `generated_utc` = `2026-10-18T08:05:47Z`,
`manifest_self` = `8daf32ea280059b26b3b43edb0709a3c0c389025fc426e901170925f836a8839`. Note
`bytes_total` lives **inside `counts`**, not top-level. All match the claim. The archive manifest
digest is `e9e5e5e07fc63c6887c88127bb2a1c03300c8d6dac692b31ba288757d5457a4d` — i.e. the archive's copy
was genuinely regenerated, not the package's copy.

Same tool on `scratch/uneutral10/package` (absolute, and the relative form
`--package scratch/uneutral10/package` from `/tmp`) → all-zero, `VERDICT PASS`, exit 0. Reproduced.

## 4. `verify/recompute-claims.py` inside the extraction — reproduced

Exit **0**; final lines:
```
  ALL PUBLISHED NUMBERS REPRODUCED: True
  VERDICT: PASS
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```
All checkable values (`0.347368`, `0.452632`, `0.291052`, `0.678947`, McNemar 39/27/90/34 = 190,
second-labeller 0.883702/0.913997/0.368421, route-A kappa 0.3249 vs published 0.3252) reproduce
within tolerance. Matches the claim.

## 5. Package unchanged + payload identity — reproduced (with one caveat)

- `scratch/uneutral10/package/MANIFEST.json` sha256 =
  `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` — **matches the claimed
  `d41d82cf…`**. 28 `files[]` entries, `counts.files` 29, `counts.bytes_total` 831,775,
  `manifest_self` `f8337fc2030c938f17dbe8d396362107a69070ae83761edb6929721fad2249d5`. All match.
  Package tree checks clean (all-zero, PASS, exit 0).
- Package inventory = **29 files**; archive payload = **31 files**.
- Full `diff -r -q` (no exclusions) between `scratch/uneutral10/package` and the archive payload
  shows **exactly three** differences and nothing else: `CITATION.cff` only-in-archive,
  `README_DEPOSIT.md` only-in-archive, `MANIFEST.json` differs. With those three excluded the diff is
  **empty** (`DIFF_EXIT=0`). The claim is reproduced and is in fact stronger: both extra files are
  *absent* from the package, not merely excluded.

**Caveat (unverifiable here):** "byte-unchanged" is verified only as *equals the claimed digest now*.
I hold no pre-fix copy of the package manifest, so change-over-time is unverified.

## 6. `overstated` / imprecise — provenance of the build, and `--package` required

**(a) The build does not stage the package.** `build_archive.sh` declares
`PKG="$ROOT/scratch/uneutral10/package"` at `scratch/ufixman1/build_archive.sh:22` and **never uses
it** (grep: that line is the only occurrence). The actual inputs are: step 1 stashes the shipping
archive as `prev-*.tar.gz`; step 2 copies the extracted **superseded archive tree** (`$E/ref/$TOP`);
step 3 overwrites the manifest by regenerating it in-stage; and `README_DEPOSIT.md` is refreshed from
`papers/encoder-crossover-190/released/README_DEPOSIT.md`. `CITATION.cff` is **inherited** from the
previous archive — this script never adds it. So the task's description ("stage the 29 package files
→ add `CITATION.cff` and `README_DEPOSIT.md`") misstates the mechanism, and the build is **not
self-contained**: it cannot be re-run if `prev-encoder-crossover-190-released.tar.gz` is lost. The
*output* is nonetheless correct and empirically equal to the package + the two extras (verified in §5).

**(b) `--package` is mandatory.** `check_manifest.py` has no cwd default: `--package` is a required
argparse argument. Invoked bare at the extracted archive root it exits **2** with
`error: the following arguments are required: --package`. The claim's phrase "at the extracted archive
root" therefore only holds with an explicit `--package` (as the task noted). Not a data contradiction,
but the claim's phrasing implies cwd resolution that the tool does not implement.

## 7. Exported documents vs disk — **FAIL (report only; not edited)**

`strategy/DEPOSIT_ARCHIVE.md` and `strategy/DEPOSIT_METADATA.md` have mtimes of
**2026-10-17 17:09:02 / 17:16:09** — unchanged since before the Oct-18 rebuild, so **no concurrent
update had landed** when I read them. They still describe the superseded state:

- `strategy/DEPOSIT_ARCHIVE.md:78-79` — bytes **157,650** (was 157,305), sha256 **`7389bd87…`**. Disk is
  158,762 / `956d6363…`. **STALE.**
- `strategy/DEPOSIT_METADATA.md:43` — row A: **157,650** / **`7389bd87…`** / 37 members. Bytes+sha
  **STALE**; member count 37 still correct.
- `strategy/DEPOSIT_METADATA.md:138-139`, `:342`, `:347` repeat **157,650** / **`7389bd87…`** as the
  chosen deposit. **STALE.**
- **Larger problem than stale numbers:** `strategy/DEPOSIT_ARCHIVE.md:45-46`, `:65-71`, `:84-85` state
  that the payload manifest covers only the 29 payload files and deliberately omits `CITATION.cff` /
  `README_DEPOSIT.md`, so `unlisted=2` / `VERDICT FAIL` / exit 1 at the extracted archive root is
  "**by design**", with "the correct invocation being `--package scratch/uneutral10/package`". The
  shipped archive now does the **opposite** (manifest describes its own tree; the same check
  **PASSes**, exit 0). The documents assert the reversed design decision. UFIXMAN1's report — "still
  citing the old 157,650-byte archive" — **understates** this.
- `strategy/DEPOSIT_ARCHIVE.md:39` cites `papers/encoder-crossover-190/released/encoder-crossover-190-released/`
  (unpacked dir). That path **does not exist**; it was retired and replaced by
  `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md` (dated 2026-10-17, UDEPOSIT2).
- Correct-and-current: `strategy/DEPOSIT_METADATA.md:45` cites the package manifest digest
  `d41d82cf…`, which matches disk.

## Explicit lists

**contradicted:** *(empty for the archive artifact)* — every stated byte, digest, count, exit code and
verdict reproduced exactly. Separately, the two strategy documents contradict disk (§7) — reported,
not edited.

**overstated:** (1) "stage the 29 package files → add CITATION.cff and README_DEPOSIT.md" misstates
the real inputs: the package is never read by the script (`PKG` unused at
`scratch/ufixman1/build_archive.sh:22`); the tree is inherited from the superseded archive and
`CITATION.cff` is inherited, not added. (2) UFIXMAN1's characterisation of the doc problem as merely
"still citing the old 157,650-byte archive" understates it — the docs state the reversed manifest
policy. (3) "at the extracted archive root" implies cwd resolution; `--package` is required.

**not_reproduced:** *(empty)*

**unverified:** (1) "The package's own manifest is byte-unchanged" and "no package file was touched" —
current digest matches the claim, but no pre-fix copy exists to prove no change; only
*digest-equals-claim* is established. (2) Nothing else outstanding.

## Recommendation

The archive is publish-ready as a *file*: reproducible, self-describing manifest, red→green guard
proven. **Do not upload while `strategy/DEPOSIT_ARCHIVE.md` and `strategy/DEPOSIT_METADATA.md` still
state 157,650 B / `7389bd87…` and declare the now-reversed `unlisted=2` policy "by design"** — a
different unit should update both to 158,762 B / `956d6363…` and to the manifest-describes-its-own-tree
policy. Also flag `build_archive.sh`'s non-self-contained inputs if reproducibility-from-package is a
deposit requirement.
