```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
kinds = re.findall(r"'([^']+)'", pinned)
# Also catch unquoted identifier members in a union (e.g., Foo | Bar).
idents = re.findall(r"(?:type\s+\w+\s*=\s*)?([^'`();|&\s][^|`';\n]*?)\s*\|", pinned)

members = []
for m in kinds:
    members.append(m)
for m in idents:
    m = m.strip()
    if m and m not in members:
        members.append(m)

# Deduplicate while preserving order.
seen = set()
distinct = []
for m in members:
    if m not in seen:
        seen.add(m)
        distinct.append(m)

ref_kinds = len(distinct)
first_ref_kind = distinct[0] if distinct else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```