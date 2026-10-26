#!/usr/bin/env python3
"""Red->green proof for the SGLang 64-token grid guard in recompute.py.

GREEN: the restored cell PROMPT-O1 passes.
RED:   a hand-planted copy with cached_tokens=1409 must make the guard FAIL and
       name that value. The planted copy is removed afterwards.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recompute as R

cell = R.CELLS / "PROMPT-O1"
planted = cell / "rows.GUARD-RED-TEST.jsonl"

print("--- GREEN (restored corpus) ---")
print(f"exit={R.assert_sglang_grid()}")

lines = (cell / "rows.jsonl").read_text(encoding="utf-8").splitlines()
rec = json.loads(lines[2])
rec["cached_tokens"] = 1409
lines[2] = json.dumps(rec, sort_keys=True)
planted.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("--- RED (planted cached_tokens=1409 in %s, row 3) ---" % planted.name)
try:
    R.assert_sglang_grid()
except SystemExit as exc:
    print(str(exc))
    rc = 1
else:
    print("RED FAILED: guard passed on a planted 1409")
    rc = 2
finally:
    planted.unlink()

print("--- GREEN again (planted copy removed) ---")
print(f"exit={R.assert_sglang_grid()}")
if rc != 1:
    sys.exit(rc)
