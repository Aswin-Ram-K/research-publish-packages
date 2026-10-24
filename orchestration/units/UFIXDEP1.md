# UFIXDEP1 — correct archive facts in the two strategy documents

**Purpose:** the deposit archive was rebuilt so its integrity manifest describes the archive it
ships inside. Two strategy docs were outside the rebuilding unit's write paths and still record the
superseded archive. Measure the archive from disk, correct both docs, keep superseded values as
dated history, and state the package/archive distinction plainly.

**Write paths (nothing else):**
- `strategy/DEPOSIT_ARCHIVE.md`
- `strategy/DEPOSIT_METADATA.md`
- `scratch/ufixdep1/**`
- `orchestration/units/UFIXDEP1.md`
- `orchestration/handoffs/UFIXDEP1.json`

**Hard bound:** 10 tool calls. Any figure not determinable from disk is reported UNKNOWN, not guessed.

**Do NOT:** touch the archive, the package, any paper, `tools/package/**`,
`strategy/ZENODO_DEPOSIT.md`; no network; nothing outside the write paths.

**Steps**
1. Measure from disk: archive size, sha256, member count (dirs+files), manifest `files[]` length,
   `counts.files`, `counts.bytes_total`; package manifest shape; before sha256 of both docs.
2. Correct every stale size/digest/member-count/file-count/manifest-shape statement in both docs,
   preserving the superseded values as dated history in each file's existing convention.
3. Make the package/archive distinction explicit: package = 29 files (28 listed + the manifest
   itself); archive = 31 files (the 29 package files + `CITATION.cff` + `README_DEPOSIT.md`).
4. Report before/after bytes + sha256 of both docs.

**Status:** in progress
