# UPIPE1 — promote publication-package pipeline into `tools/package/`

**Purpose (one only):** Promote the seven throwaway publication-package scripts (currently copied into
~100 `scratch/` dirs with hard-coded absolute paths) into a maintained, parameterised `tools/package/`
directory driven by `--package <slug>`, so a second package can be built without re-deriving them.

**Bound:** 40 tool calls. Stop condition: if a named scratch source cannot be found, or its behaviour
cannot be reproduced in 3 attempts, STOP, mark that command `partial`, report which — no substitutes.

**Target repo `/home/zer0null/Duval` is STRICTLY READ-ONLY** — no writes, no `git` command at all.

**Write paths (exactly these):**
- `tools/package/**` (new)
- `tests/test_package_tools.py` (new)
- `orchestration/units/UPIPE1.md`
- `orchestration/handoffs/UPIPE1.json`
- `scratch/upipe1/**`

**Sources:**
1. `neutralise.py` ← `scratch/ubij1/bij_one.py`, `scratch/uneutral9/rename.py`, NEUTRAL-TAG/v1
2. `census.py` ← `scratch/ubij1/census_one.py`, `scratch/uneutral1/scan.py`
3. `classify.py` ← `scratch/ugate1/classify_oov.py` + `scratch/uagnostic1/census.tsv` (c-mechanism authority)
4. `scan_markers.py` ← ad-hoc greps (product name, CONSONANCE, U[A-Z]+[0-9]+)
5. `regen_manifest.py` ← `scratch/udtag1/regen_manifest.py`
6. `check_manifest.py` ← `scratch/utool1/check_manifest6.py`, `scratch/uver24/`
7. `gate.sh` ← `scratch/ugate2/gate.sh`, `scratch/ugate1/gate_scoped.sh`

**Proof:** equivalence (new vs old on same input), 4+ tests in `tests/test_package_tools.py`.
Report (never fix) the 28-vs-29 file count defect.
