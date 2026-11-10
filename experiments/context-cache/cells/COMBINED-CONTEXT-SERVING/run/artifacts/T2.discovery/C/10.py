```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

union_match = re.search(r"(?:export\s+type|type)\s+(\w+)\s*=\s*(.+)", text)
if not union_match:
    raise SystemExit("no union found")

kind_name = union_match.group(1)
union_body = union_match.group(2).strip().rstrip(";")

members = [m.strip() for m in re.split(r"\|", union_body) if m.strip()]
distinct = []
seen = set()
for m in members:
    if m not in seen:
        seen.add(m)
        distinct.append(m)

ref_kinds = len(distinct)
first_ref_kind = distinct[0]

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```