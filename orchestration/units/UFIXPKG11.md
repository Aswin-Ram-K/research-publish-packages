# UFIXPKG11 — Close the "documented number drifts from artifact" class in tools/package docs

**Purpose.** The packaging tool's own docs record "known-good" numeric/digest values for
`regen_manifest.py` that no longer match the live payload. Find every recorded value in
`tools/package/**` that *claims* to describe the current artifact (class a), measure the live
artifact, and correct class (a) in place. Class (b) (historical transcript of a specific past run)
keeps its value and gains a dated note with the current value. Class (c) (description of tool
behaviour) is untouched unless the behaviour description itself is wrong.

**Scope / write paths.**
- `tools/package/README.md`
- `tools/package/**` (only if a stale value is found in another doc there)
- `orchestration/units/UFIXPKG11.md`
- `orchestration/handoffs/UFIXPKG11.json`
- `scratch/ufixpkg11/**`

**Forbidden.** Writes under `papers/**` or `scratch/uneutral10/**`. Any `git` command against
`/home/zer0null/Duval`. Building into a real release destination (build only under `scratch/**`).
Weakening a guard or re-pinning a digest to make a checker pass.

**Hard bound.** 15 tool calls.

**Method.**
1. Read the tool interface (`tools/package/regen_manifest.py`, `check_manifest.py`) to confirm the
   payload path from the tool itself, not from assumption.
2. Run both tools against the payload; record literal command output.
3. Independent measurement: own `sha256sum`/`stat` walk over the payload's shipped files.
4. Sweep all of `tools/package/**` for recorded numeric/digest values; classify a/b/c.
5. Edit class (a); annotate class (b).
6. Run `python3 tests/test_package_tools.py` (with `--noconftest` or directly — `tests/conftest.py:19`
   imports an absent module so pytest cannot collect).
7. Prove the payload `MANIFEST.json` is byte-unchanged.

**Status:** in progress.
