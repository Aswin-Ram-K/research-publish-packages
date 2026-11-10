```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
kinds = re.findall(r"'([^']+)'", pinned)
# If no string literals (e.g. enum members), fall back to identifier members.
if not kinds:
    kinds = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', pinned)

kinds = list(dict.fromkeys(kinds))
ref_kinds = len(kinds)
first_ref_kind = kinds[0] if kinds else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```