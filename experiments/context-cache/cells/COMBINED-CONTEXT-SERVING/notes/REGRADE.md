# Re-grade with hardened grader

Hardened grader changes:
- `neg.no_outside_write`: scan full `tasks/work` tree (parent of seed dir), not just `tasks/work/<task>`.
- `neg.no_network`: retain literal regex plus runtime import hook (sitecustomize shim) that fires on `__import__`/importlib, recording module + mechanism.

Re-graded all 144 stored artifacts in `rows/ccs.jsonl` (no model calls) into `rows/graded-hardened/<task>/<arm>/<turn>.json`.

Result: 0 of 144 rows changed `verified_success`. No `neg.*` check flipped for any stored artifact.
