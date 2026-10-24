# URELEASE3 — second release package through the driver

- **Unit:** URELEASE3 (parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`)
- **Status:** done
- **Bound:** 25 tool calls (used 24)
- **Purpose:** drive a SECOND package through `orchestration/units/UBUILD1.build.sh`
  (`--package encoder-crossover-190`), verify the emitted tree against
  `papers/encoder-crossover-190/CLAIMS.md`, classify the gate residual, and
  record what the driver cannot yet do.
- **Write paths (exactly these):** `orchestration/packages/encoder-crossover-190.toml`,
  `orchestration/packages/encoder-crossover-190/**`, `strategy/RELEASE_BUILD_3.md`,
  `orchestration/units/URELEASE3.md`, `orchestration/handoffs/URELEASE3.json`,
  `scratch/urelease3/**`
- **Not touched:** the driver, `orchestration/packages/gated-read-batching.toml`,
  `tests/test_package_build.py`, `papers/**`, `/home/zer0null/Duval` (no git run).

## Result

Manifest written (29-file ship list, 16 never-ship names, licence sha, anchor
`907fa39`, 4 shared fragments). Build into
`scratch/urelease3/dest/research-publish-packages` **exited 1** — the exclusion
gate's 1133 out-of-vocabulary tokens, by design. Emitted tree verifies:
`recompute-claims.py` exit 0 (`ALL CLAIM NUMBERS PRESERVED: True`),
`parse_fixture.py` exit 0, `compare.py` exit 0 (route B κ 0.9014, agreement
0.9053, A/B mutual agreement 0.3684, 18 disagreements, 4 route-A-backed).
Finding: `CLAIMS.md:109` quotes A/B mutual agreement 0.3526 while the shipped
tree computes 0.3684 (`reproduced=False`) — recorded, not adjusted.

## Progress log

1. Read `strategy/PACKAGE_BUILD.md`, `orchestration/packages/gated-read-batching.toml`,
   `orchestration/units/UBUILD1.build.sh`, `papers/encoder-crossover-190/CLAIMS.md`;
   measured the payload, licence, anchors, tests.
2. Persisted this card; wrote the manifest + 4 fragments.
3. Built with the driver (exit 1, 1133 flagged); saved stdout to `scratch/urelease3/build.log`.
4. Ran all three verification tools in the emitted tree (all exit 0); compared to CLAIMS.md.
5. Captured the gate JSON (`scratch/urelease3/gate.json`) and classified the residual.
6. Wrote `strategy/RELEASE_BUILD_3.md`; handoff `orchestration/handoffs/URELEASE3.json`.

## Residual/next

Open objective for a follow-on unit: declare the 1133-token residual (or a
subset) instead of scrubbing it; extend the tripwire beyond the default slug;
make the root README index manifest-driven (driver `:514`).
