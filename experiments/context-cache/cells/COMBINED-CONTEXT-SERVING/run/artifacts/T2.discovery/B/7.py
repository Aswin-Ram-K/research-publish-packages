```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
members = re.findall(r"'([^']+)'", pinned)
# Also catch unquoted identifier members in a union like:  | 'a' | B | 'c'
idents = re.findall(r"(?:\|\s*)([A-Za-z_]\w*)", pinned)
# Combine, preserving order, dedup while keeping first occurrence order
seen = set()
kinds = []
for m in members + idents:
    if m not in seen:
        seen.add(m)
        kinds.append(m)

ref_kinds = len(kinds)
first_ref_kind = kinds[0] if kinds else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```