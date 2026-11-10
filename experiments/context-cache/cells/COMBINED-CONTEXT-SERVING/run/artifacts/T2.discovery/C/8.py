```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

union_match = re.search(r"(?:export\s+type|type)\s+\w+\s*=\s*(.+)", text)
if union_match:
    union_body = union_match.group(1).strip().rstrip(";")
    kinds = [k.strip().strip("'\"") for k in re.split(r"\|", union_body)]
    kinds = [k for k in kinds if k]
    ref_kinds = len(kinds)
    first_ref_kind = kinds[0]
else:
    enum_match = re.search(r"(?:export\s+enum|enum)\s+\w+\s*\{([^}]*)\}", text)
    if enum_match:
        enum_body = enum_match.group(1)
        kinds = []
        for line in enum_body.splitlines():
            m = re.match(r"\s*(\w+)\s*=?\s*;", line)
            if m:
                kinds.append(m.group(1))
        ref_kinds = len(kinds)
        first_ref_kind = kinds[0] if kinds else ""
else:
    ref_kinds = 0
    first_ref_kind = ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```