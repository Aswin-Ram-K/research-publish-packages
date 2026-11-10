```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

union_match = re.search(r"(?:export\s+type|type)\s+\w+\s*=\s*(.+)", text)
if union_match:
    union_body = union_match.group(1).strip().rstrip(";")
    members = [m.strip().strip("'\"") for m in re.split(r"\s*\|\s*", union_body)]
    members = [m for m in members if m]
    ref_kinds = len(members)
    first_ref_kind = members[0]
else:
    enum_match = re.search(r"(?:export\s+enum|enum)\s+\w+\s*{([^}]+)}", text)
    if enum_match:
        members = [m.strip().split("=")[0].strip() for m in re.split(r",", enum_match.group(1))]
        members = [m for m in members if m]
        ref_kinds = len(members)
        first_ref_kind = members[0]
    else:
        list_match = re.search(r"\[\s*(.+?)\s*\]", text)
        if list_match:
            members = [m.strip().strip("'\"") for m in re.split(r",", list_match.group(1))]
            members = [m for m in members if m]
            ref_kinds = len(members)
            first_ref_kind = members[0]
        else:
            ref_kinds = 0
            first_ref_kind = ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```