```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
kinds = re.findall(r"'([^']+)'", pinned)
# If no quoted literals, try unquoted enum/union identifiers.
if not kinds:
    kinds = re.findall(r'(?:type|enum)\s+\w+\s*=\s*(.*?);', pinned)
    if kinds:
        union_str = kinds[0]
        kinds = re.findall(r"'([^']+)'", union_str)
    if not kinds:
        kinds = re.findall(r'\b([A-Z][A-Za-z0-9]*)\b', pinned)

# Deduplicate while preserving order.
seen = set()
distinct = []
for k in kinds:
    if k not in seen:
        seen.add(k)
        distinct.append(k)

ref_kinds = len(distinct)
first_ref_kind = distinct[0] if distinct else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```