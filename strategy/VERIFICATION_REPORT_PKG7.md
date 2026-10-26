# VPKG7 — independent verification of UPKGINSTALL7 (paper #7 deposit package)

Verifier: VPKG7 (not the author). Method: every number recomputed from the files; the shipped
archive and payload were treated as frozen and only copies under `scratch/vpkg7/` were used.

## Claim re-derivation — all 8 claims reproduced

| # | Claim | Re-derived | Result |
|---|---|---|---|
| 1 | 12-file payload dir; archive `gated-read-batching-released.tar.gz` | `find -type f` = 12; name confirmed | match |
| 2 | 126,032 B; sha256 `8eedf2e2…f5038d`; md5 `af513024…7446b`; 16 members = 1 dir + 3 subdirs + 12 files; one top-level dir | `stat`, `sha256sum`, `md5sum`, `tar tzf` | match, all |
| 3 | Two builds byte-identical (`cmp` 0) | re-ran the build twice in fresh stages | `cmp` 0, 126,032 B each |
| 4 | `check_manifest.py` on payload and extraction → all counters 0, PASS, exit 0 | ran on both | identical output, exit 0 |
| 5 | `verify/recompute-claims.py` → 49/49, PASS, exit 0 | ran in fresh extraction | `checks: 49 passed: 49 failed: 0`, exit 0 |
| 6 | Red→green: byte flip at offset 1,000,000 → `hash_mismatch=1`, `HASH: data/gated-read-rows.jsonl`, FAIL, exit 1; restore → exit 0, md5 `3aad1ae2…afa5` | flipped 0x6c→0x93 at 1,000,000, then restored from a second extraction | exactly as claimed |
| 7 | Payload `MANIFEST.json`: `counts.files=12`, `counts.bytes_total=2372774`, 11 entries | parsed JSON | match |
| 8 | `CITATION.cff`: YAML parses, no `doi`, licence `PolyForm-Noncommercial-1.0.0`, author Aswin Ram Kalugasala Moorthy | `yaml.safe_load` | match |

## Checks the report did not make

1. **One top-level directory / extraction vs payload.** Exactly one component
   `gated-read-batching-released`; extraction produces 12 files + 3 subdirs and is **byte-identical
   to the payload including `MANIFEST.json`** (`diff -r` exit 0, 12/12 `cmp` SAME). No file differs,
   so the "apart from the regenerated MANIFEST.json" caveat is unnecessary — the manifest was
   regenerated in-stage, so the shipped copy is the same bytes.
2. **Payload internal consistency.** Independent re-hash (stdlib only, no helper): all 11 listed
   entries exist with the stated size and sha256; the only on-disk unlisted file is `MANIFEST.json`
   itself. `counts.files=12` counts it, `bytes_total=2372774` excludes its 4,676 B — a **documented
   self-exemption** convention (`README_DEPOSIT.md:104-108`), not a bookkeeping error. But the
   manifest's own `policy` string says it "lists exactly the files on disk in this package", which is
   false as written (11 of 12).
3. **Licence templates.** `COMMERCIAL.md` is byte-identical; `LICENSE` (+766 B) and
   `CONTRIBUTING.md` (+511 B) are **intentionally edited**, not identical: the `LICENSE` PolyForm body
   is still verbatim — found at offset 115, exactly 4,563 B, sha256 `ffcca388…c94cc8` — and the extra
   bytes are an appended scope section. `CONTRIBUTING.md` replaces the template's DRAFT banner with
   release terms. **Defect:** the appended `LICENSE` scope section says what ships is
   "the decision instrument (`fixture/`), the published measurements (`results/`) and the verification
   tools (`verify/`, `second-labeller/`)" — `fixture/` and `second-labeller/` **do not exist** in this
   package (12 files: data/, results/, verify/ only). That paragraph describes a different paper's
   package and is wrong here.
4. **Leakage — FAIL.** 6 of 12 files carry internal material:
   - `MANIFEST.json:3,5` — internal unit id **`UPKG7B`**, twice, and `tools/package/regen_manifest.py`.
   - `README.md:72,73` — `scratch/upkg7b/cuts/`, `scratch/upkg7b/cut-ladder.log`;
     `README.md:125` — `scratch/uneutral10/package/LICENSE`; `README.md:3,29` — `papers/gated-read-batching/MANUSCRIPT.md`, `GAPS.md`;
     `README.md:107` — `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/`.
   - `README_DEPOSIT.md:140` — `tools/package/regen_manifest.py`.
   - `results/GATED_READ_PROVENANCE.md:276` — `scratch/.tools/`.
   - `verify/recompute-claims.py:20` — `papers/gated-read-batching/MANUSCRIPT.md`.
   - `data/gated-read-rows.jsonl` — 4 e2e rows carry `"answer": "2026-09-28-duval-m0"`, i.e. the
     **parent/target project name `duval` and its trace id**, plus corpus file paths
     (`docs/TRACES.md`, `tools/trace.ts`, `AGENTS.md`, …).
   No `/home/zer0null` absolute path leaks.
5. **Clean-state rebuild — PASS.** `scratch/upkginstall7/build_archive.sh` reads no previously built
   archive (source-verified: inputs are `scratch/upkg7b/package` + `deposit-metadata`, sha256-pinned,
   then two fresh stages + `regen_manifest.py`). Re-run with only the install destination redirected
   into `scratch/vpkg7/`: both stages 126,032 B, `cmp` 0, shipped sha256/md5 reproduced exactly, and
   the rebuilt payload tree is `diff -r`-identical. (First attempt exited "MISSING INPUT DIR" because
   `deposit-metadata/` hangs off `BUILD_WORK`; copying that input under the redirected work dir fixed
   it — an input-locating artefact, not a build defect.)
6. **Release README accuracy.** `papers/gated-read-batching/released/README.md` correctly names the
   `.tar.gz` as **the deposit artifact** and warns against hand-zipping the unpacked tree (the
   same-stem hand-made-archive trap). Its "byte-identical to the archive's tree" line is true
   (verified). Gap: it does not warn that extracting the archive in that same directory collides with
   the same-named `gated-read-batching-released/` payload dir.

## Verdict

**partial.** Every one of the 8 quoted numbers reproduces exactly — the report is honest about what it
measured. But the package is **not deposit-clean**: internal unit id `UPKG7B` and `scratch/`,
`tools/package/`, `state/refresh-verify/duval/…` paths ship in 6 files, the target project name `duval`
ships in 4 data rows, and the `LICENSE` scope paragraph describes files that are not in this package.
Frozen artifacts were not modified (`sha256`/`md5` unchanged, mtime 2026-10-19 01:10:54).
