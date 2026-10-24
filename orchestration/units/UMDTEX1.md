# UMDTEX1 — Unify the two md2tex converters into one config-driven tool

**Purpose:** Remove the duplicated Markdown→LaTeX converter (one copy per paper) by building a single
`tools/package/md2tex.py --package <slug>` driven by per-package config, with **byte-identical** output
for both existing papers.

**Write paths:** `tools/package/md2tex.py`, `tools/package/README.md` (append only), `tests/test_md2tex.py`,
`orchestration/units/UMDTEX1.md`, `orchestration/handoffs/UMDTEX1.json`, `scratch/umdtex1/**`

**Hard bound:** 30 tool calls.
**Rules:** `/home/zer0null/Duval` strictly read-only, no git against it. Do not edit `papers/**`.
Do not install/fetch. No number not read from disk or measured.

**Proof required:** diff of the two converters + what is paper-specific; cmp+sha256 for both
regenerations; literal test output (pytest needs `--noconftest`); non-vacuous red→green; before/after
digests of both papers' files.

## Outcome (UMDTEX1, done)

Built `tools/package/md2tex.py` (31714 B, sha256 `c62feb657a14aa957f0ca2296435ce3820750af98d457acb0a4ac187d97867ec`),
one converter with `--package <slug>`; per-paper values live in the pure-data `PACKAGES` registry inside it.
**Deviation from this card:** no TOML under `orchestration/packages/` — that path is outside the declared
write paths **and** `orchestration/packages/<slug>.toml` are UBUILD1's own `schema = 1` build manifests read
by `check_manifest.py`, so writing md2tex keys there would be an undeclared write and a foreign-schema edit.
Migration documented in the tool docstring and README: lift `PACKAGES` verbatim to
`orchestration/packages/<slug>/md2tex.toml` + `tomllib`, no logic change.

**Byte-identity proven** (`cmp` exit 0 and equal sha256 for every pair; outputs in `scratch/umdtex1/new-*/`):
encoder `main.tex` = `90db2cd4e7fa6a63d4b91e2c0636c3879de54fc2a4e7f55fcbf2cce4197c9b86`; gated `main.tex` =
`a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`; gated `ABSTRACT.txt` =
`59ef6d55d64d6a3c3b500ffb653e8f85c11fca9e841b1ff37fc8b43c0ef1a6e9`; gated `ABSTRACT_METADATA.txt` =
`05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962`. `papers/**` byte-unchanged
(39-file before/after snapshot diff clean); no write ever targeted `papers/**`.

**Tests:** `python3 tests/test_md2tex.py` → `ALL 4 TESTS PASSED` (exit 0); `python3 -m pytest
tests/test_md2tex.py --noconftest -q` → `4 passed`. Without `--noconftest`: `tests/conftest.py:19` →
`ModuleNotFoundError: No module named 'resextract'` (exit 4), so the wider suite cannot collect.
Non-vacuity shown by mutation: `scratch/umdtex1/mut/md2tex_mut.py` (citation guard disabled) exits 0 and
writes an uncited `\bibitem{uncited_probe_2099}`, while the real tool exits 1 naming that key.

**Note:** `tools/package/README.md` grew 198 → 215 lines from another unit mid-task; my `### \`md2tex.py\``
section was appended immediately before `## Tests` (now 267 lines) and no existing line was changed.
