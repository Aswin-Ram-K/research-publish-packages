#!/usr/bin/env bash
# P95-POWER-FROM-ROWS — evidence command.
# Regenerates P95-POWER.json from the rows files and diffs it against the committed copy.
# Exit 0 = the committed JSON is exactly what the generator produces today.
set -eu

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

OUT="$(mktemp "$ROOT/experiments/ptr-engine/measure/.p95-power-regen.XXXXXX.json")"
trap 'rm -f "$OUT"' EXIT

python3 experiments/ptr-engine/measure/p95_power_gen.py "$OUT" >/dev/null
diff -q "$OUT" experiments/ptr-engine/measure/P95-POWER.json
echo "P95-POWER.json regenerated identically"
