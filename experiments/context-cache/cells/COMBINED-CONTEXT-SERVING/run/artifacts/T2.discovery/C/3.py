```python
import re

# Read the seeded reference.ts and extract lines 49-70 (1-indexed).
with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]  # L49..L70
text = "\n".join(pinned)

# Find the reference kind union/enumeration. Heuristic: a type alias or enum
# whose members are quoted string literals separated by `|` or commas.
# Collect all quoted string-literal tokens in the pinned block in order.
tokens = re.findall(r"'([^']*)'", text)

# Deduplicate while preserving order.
seen = []
for t in tokens:
    if t not in seen:
        seen.append(t)

ref_kinds = len(seen)
first_ref_kind = seen[0] if seen else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```