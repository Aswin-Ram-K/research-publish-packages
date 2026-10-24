# Unit UBUILDALL1 — manifest-drive the package builder

**Purpose (one):** Turn `orchestration/units/UBUILD1.build.sh` (969 lines) into a manifest-driven
driver (`--package <slug>`) with per-package manifests under `orchestration/packages/`, and prove
the existing package (`gated-read-batching`) comes out byte-identical.

**Hard bound:** 30 tool calls. Working copy at `scratch/ubuildall1/` kept after each step.

**Declared write paths (exactly these):**
- `orchestration/units/UBUILD1.build.sh`
- `orchestration/packages/**`
- `tests/test_build_wiring.py`, `tests/test_package_build.py`
- `strategy/PACKAGE_BUILD.md`
- `orchestration/units/UBUILDALL1.md`
- `orchestration/handoffs/UBUILDALL1.json`
- `scratch/ubuildall1/**`

**Read-only constraints:** `/home/zer0null/Duval` strictly read-only, never `git` against it.
Never run the exclusion gate against a real release destination — build into `scratch/ubuildall1/**` only.

**Guards that must survive:** licence template sha256 check; never-ship check; fail-closed exclusion
gate (non-zero exit on failure, never reported as pass); no package digest pinned anywhere;
`SAN_SRC_OVERRIDE` / `SAN_SRC_FROZEN_OVERRIDE` with warning line before first destructive step.

**Acceptance evidence:** byte-identity comparison command + literal output; `test_build_wiring.py`
11 tests green; `test_package_build.py` red→green proof; `strategy/PACKAGE_BUILD.md` record.

**Progress log:**
- (start) card persisted.
- (1) script read completely; every per-package value listed by line number.
- (2) `scratch/ubuildall1/refactor.py` extracts the ship list (29), never-ship list (15), README
      head/tail and the code/public vocabulary from the ORIGINAL script's own bytes into
      `orchestration/packages/gated-read-batching/`, writes the manifest, and splices 22 anchored
      edits into the driver. Fragments byte-compared OK against the heredoc bodies.
- (3) driver driven by `--package <slug>`; manifest loaded fail-closed (exit 2); default package's
      built-in literal block kept and asserted equal to the manifest (two-way tripwire).
- (4) byte-identity proved: `diff -r --exclude=.git` exit 0, 39/39 files sha256-equal, git HEAD
      identical (245449617de274d8b7ee3059e399d25f5c30a965), both builds exit 1 with the same
      pre-existing gate failure (1133 flagged tokens).
- (5) `tests/test_build_wiring.py` UNMODIFIED, 11 passed. `tests/test_package_build.py` added
      (15 tests, manifest-derived); red→green shown by mutating a `ship_staged` entry
      (26 passed -> 3 failed -> restore -> 26 passed), and the driver refuses the mutation with
      exit 2 at the tripwire.
- (6) `strategy/PACKAGE_BUILD.md` written: schema, guards moved/stayed, byte-identity proof,
      red→green proof, and the five things left hard-coded.
- (done) status done.
