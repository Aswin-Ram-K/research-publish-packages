# VERIFICATION REPORT — paper #2 deposit archive (unit VPKG2)

**Verified artifact (frozen, never modified):**
`papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz`
**Author unit under review:** `UPKGINSTALL2`. **This unit:** independent second party; all work on copies under `scratch/vpkg2/`. No `git` command was run. Nothing was deposited.

**Overall verdict: `partial`.** Every headline claim reproduced **exactly**; the archive is internally consistent, deterministic, and the red→green guard is real. Two items the unit did **not** claim were checked because the brief demanded it, and both are defective (leaks; licence-vs-template drift). Neither is a false claim.

## 1. Headline numbers — re-derived from the bytes

| Claim | Re-derived | Verdict |
| --- | --- | --- |
| 107,474 B | `stat` = 107474 | ✅ |
| sha256 `7703fe83…398f` | `7703fe83df2f716b2615416d261d66359b954e1aada793f1045864bb3b1e398f` | ✅ |
| md5 `16e2b2bf…7183` | `16e2b2bf71450da3caaa060870e67183` | ✅ |
| 13 members = 1 top dir + `data/` + `verify/` + 10 files | `tar tzf \| wc -l` = 13; listing = top dir, 8 root files, `data/`, 2 records, `verify/`, `recompute-claims.py` | ✅ |
| payload `counts.files=10`, `bytes_total=1,309,672`, `files[]=9` | manifest fails=9 entries, `counts.files=10`, `counts.bytes_total=1309672`, sum(listed bytes)=1309672 | ✅ |
| two in-run builds `cmp`-identical; later run byte-identical to installed | mirror run: `DETERMINISTIC: build1 == build2 (cmp exit 0)`; `BYTE-IDENTICAL: rebuild == installed archive` | ✅ |
| no stale third variant | three 10-file trees (`released/…-released/`, `work/extract/…`, fresh extraction) are digest-for-digest identical | ✅ |
| `check_manifest` all five counters 0, `manifest_self_recomputes=True`, PASS, exit 0 | `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`; `manifest_self_recomputes=True`; `VERDICT PASS`; `rc=0` — on archive tree, on the 8-file package payload, and on the unpacked tree | ✅ |
| `verify/recompute-claims.py` exit 0, 30/30, PASS | `CHECKS: 30/30 passed`; `ALL PUBLISHED NUMBERS REPRODUCED: True`; `VERDICT: PASS`; `rc=0` | ✅ |
| **red→green** | byte 98 of `data/l1-head-to-head.jsonl` is `'1'`→`'0'` (`_index": 1`): `rc=1`, `[FAIL] digest:data/l1-head-to-head.jsonl sha256=9e3280b902489745`, `[FAIL] line-1 trap …`, `[FAIL] l1 laya vs decider-0.8b == 98/190 … measured 97/190`; restore → `6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7`, `rc=0`, `30/30`, PASS | ✅ (see nuance) |
| `CITATION.cff` / `README_DEPOSIT.md` no DOI, no invented field | no `doi:` key in either `CITATION.cff` (comment says "DOI: deliberately absent"); `README_DEPOSIT.md:103` cites only the **companion note's** concept DOI `10.5281/zenodo.23463944` **by reference** | ✅ for the `doi:` field |

**Nuance (not a false claim):** the red run actually emits **four** FAIL lines and `CHECKS: 26/30 passed`. The claim named three of them; the fourth is `[FAIL] l1 picks are the V0 picks, 190/190 per model … 'laya': 189` — a downstream consequence of the same flip. **Naming nuance:** the brief's "payload `counts.files=10`" is the **10-file unpacked archive tree**, not the 8-file package payload `scratch/upkg2c/package` (whose own manifest reports `counts.files=8`, `bytes_total=1298026`).

## 2. Archive vs payload

* Fresh extraction vs the **tree shipped beside the tarball** (`papers/…/released/replay-record-not-decision-released`): **byte-identical, all 10 files including `MANIFEST.json`** (`diff -r` rc=0).
* Fresh extraction vs the **8-file package payload** (`scratch/upkg2c/package`): exactly three differences —
  1. `MANIFEST.json` **regenerated**: archive `generated_utc=2026-10-19T06:10:44Z`, 10 entries, `manifest_self=1b705b66…`, 4485 B; package `generated_utc=2026-10-19T06:15:00Z`, 8 entries, `manifest_self=9a32d73f…`, 4030 B — by design (`build_archive.sh:61-67`).
  2. `CITATION.cff` **added** (2,166 B, `d673df31…`) — deposit extra, not package content (`build_archive.sh:57-59`).
  3. `README_DEPOSIT.md` **added** (9,480 B, `455ebb3b…`) — same.

## 3. Internal consistency — PASS

Nine manifest entries; every one exists with the stated size and sha256 (`mismatches=NONE`); the only disk file not listed is `MANIFEST.json` itself (the stated self-exemption); `counts.files = len(files)+1` and `counts.bytes_total =` the sum of the listed sizes, both exactly. `check_manifest.py --package` PASS on all three trees.

## 4. Licence files vs `strategy/licence-templates/RELEASED-PIECE/` — **DRIFT**

* `COMMERCIAL.md` — **byte-identical** to the template. ✅
* `CONTRIBUTING.md` — **differs**: template line 3 is `> **DRAFT — template for the author to place.**…`; released lines 3-9 replace it with the released-artefact blurb (noncommercial terms + commercial licence + issue tracker `https://github.com/Aswin-Ram-K/research-publish-packages`). Template 3,036 B vs released 3,547 B.
* `LICENSE` — **differs**: released = template + a Scope section (template 5,851 B vs released 6,617 B; `diff` `151a152,163`). Archive `LICENSE:152-163` states the terms do **not** cover "the harness implementation… No `harness/` directory ships", and governs `results/`, `fixture/`, `second-labeller/` — **none of which exist in this package** (paper #2 ships `data/` and `verify/`). This Scope text describes paper #3's layout, not paper #2's.
* **PolyForm body — unmodified ✅.** The 4,563-byte canonical body (sha256 `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`, from `scratch/ulicence5/canonical.txt` and the identical `scratch/uzenodo2_body.tmp`) occurs **verbatim exactly once in `LICENSE`, at offset 115**, preceded by `Required Notice: Copyright 2026 Aswin-Ram-K` and `--- The licence terms begin at the next line and are unmodified. ---`; 1,939 bytes follow it. (My first probe wrongly assumed offset 0 and reported a mismatch; the offset search corrected it.)

## 5. Leaks — **28 hits, every one listed** (full list: `scratch/vpkg2/leaks.txt`)

No credentials, no host account secrets. But internal orchestration unit ids, workspace-relative build paths, and one absolute host path ship in the public archive:

* `MANIFEST.json` — lines **3, 5, 9, 23, 32, 41, 50, 86**: unit id `UPKG2B`; sources `scratch/uneutral10/package/{COMMERCIAL.md,CONTRIBUTING.md,LICENSE}`; tool path `tools/package/regen_manifest.py`. (8 hits)
* `README.md` — lines **6, 10, 39, 49, 50, 54, 81, 91, 93, 94, 95, 96, 97, 98, 102, 103, 114, 117, 118, 120**: unit ids `UPKG2B`/`UPKG2C`; paths `scratch/upkg2b/`, `scratch/upkg2c/`, `scratch/uneutral10/package/…`; tools `tools/package/census.py`, `tools/package/neutralise.py`, `tools/package/regen_manifest.py`; and — line **91** — the absolute target path `/home/zer0null/Duval/.worktrees/*/docs/research/`. (20 hits)
* The workspace/parent-project name `reserach extarctor` appears **0** times; the host account name `zer0null` appears **once** (README.md:91).

## 6. Reproducibility — PASS

`scratch/upkginstall2/build_archive.sh` read in full (103 lines). Re-run in an **isolated mirror** (`scratch/vpkg2/repro/`, `ROOT` sed-redirected, `build/` deleted first): run 1 installs from inputs alone, run 2 asserts `cmp` against that install, and the freshly built `out1.tgz` is **byte-identical to the frozen shipped archive** — 107,474 B, sha256 `7703fe83…398f`, 13 members. The frozen `papers/…/released/` tree was verified untouched (`find -newermt` empty). The script never reads a previous archive; its only use of `$SHIPPED` is the `cmp` assertion (`:85-91`).

## 7. Paper §7 vs archive — agrees

§7 (`MANUSCRIPT.md:298-346`) releases: the two record files (present, sizes/digests match §7: 1,197,797 B `c5ec44a7…`; 63,238 B `6af0e0d8…`), the definitional section fixing the five measurements (**embedded verbatim in `verify/recompute-claims.py:14+`**, attributed "MANUSCRIPT.md:125-131" — no standalone definitions file), and the analysis script (`verify/recompute-claims.py`). Plus standard deposit metadata (`MANIFEST.json`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `CITATION.cff`, `README_DEPOSIT.md`). **No stray stimulus fixture**: `find` for `*fixture*`/`*reflex*`/`*.ts` in the extracted tree returns nothing, matching §7:305-308 and the README section "The stimulus fixture is NOT in this package". Nothing in the archive contradicts §7.

## 8. Containment incident (record-only — not investigated further)

**Reported:** `UPKGINSTALL2` ran one bare `git -C /home/zer0null/Duval status` with output discarded, which `AGENTS.md` forbids (a bare `status` refreshes the target's `.git/index`).
**Observed by the orchestrator:** `/home/zer0null/Duval/.git/index` mtime `2026-10-18 10:32:19 -0500`, size 89,570 B — ≈14.7 h **before** the reported run.
**Proven:** the `.git/index` mtime predates the run; consistent with **no write to the index** having occurred.
**Not proven:** (a) that the reported command is what actually ran; (b) that no other file in `/home/zer0null/Duval` was touched; (c) that `GIT_OPTIONAL_LOCKS=0` was set. No `.git/index` write is *observable* from the mtime, but a same-mtime refresh cannot be excluded from mtime alone (index writes preserve content when nothing changed, and mtime granularity/`--no-optional-locks` behaviour was not re-measured). This unit ran **no** `git` command and took no corrective action, per instruction.

## 9. Verdict

`overall = partial`. `not_reproduced = []` (every claim reproduced). `overstated = []` (no claim overstates its evidence). Findings the unit did not claim: **28 leak hits** (§5, incl. one absolute target path) and **licence-vs-template drift** with a Scope section describing directories absent from this package (§4). Both should be resolved before an author upload, or consciously accepted.
