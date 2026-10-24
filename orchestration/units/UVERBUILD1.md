# UVERBUILD1 — independent verifier: UBUILDALL1 package-driver refactor

**Purpose.** Independently re-check UBUILDALL1's claim that `orchestration/units/UBUILD1.build.sh`
became a `--package <slug>` driver (default `gated-read-batching`) with per-package values in
`orchestration/packages/<slug>.toml` + fragments, and that the existing package still comes out
**byte-identical** with every guard intact.

**Author of the change:** UBUILDALL1 (not this unit). **Verifier:** UVERBUILD1 (this unit). No edits
to the builder, manifest, or tests — report only.

**Declared write paths (exactly these):**
- `strategy/VERIFICATION_REPORT_BUILDALL.md`
- `orchestration/units/UVERBUILD1.md`
- `orchestration/handoffs/UVERBUILD1.json`
- `scratch/uverbuild1/**`

**Hard bound: 25 tool calls.** Builds only into `scratch/uverbuild1/**`.

**Checks:** (1) reproduce byte-identity with pristine script vs driver into fresh dests; (2) exit codes
+ gate message; (3) determinism — driver run twice; (4) guards present (licence sha256, never-ship
absence, fail-closed ship list, DEST suffix guard, override warning ordering, `exit "$GATE_RC"`);
(5) no pinned 64-hex package digest; (6) tripwire on a COPY of the manifest; (7) both test files +
red→green; (8) whether the new tests derive expectations from the manifest or re-hard-code them.

**Constraint:** `/home/zer0null/Duval` strictly read-only, no git command against it, no network, no installs.
