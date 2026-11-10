```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

union_match = re.search(r"(?:export\s+type|type)\s+\w+\s*=\s*(.+)", text)
if union_match:
    union_body = union_match.group(1)
    kinds = re.findall(r"'([^']+)'", union_body)
else:
    enum_match = re.search(r"(?:export\s+enum|enum)\s+\w+\s*{([^}]*)}", text)
    if enum_match:
        enum_body = enum_match.group(1)
        kinds = re.findall(r"(\w+)\s*=", enum_body)
    else:
        list_match = re.search(r"\[(.*?)\]", text)
        if list_match:
            kinds = re.findall(r"'([^']+)'", list_match.group(1))
        else:
            kinds = []

ref_kinds = len(kinds)
first_ref_kind = kinds[0] if kinds else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```