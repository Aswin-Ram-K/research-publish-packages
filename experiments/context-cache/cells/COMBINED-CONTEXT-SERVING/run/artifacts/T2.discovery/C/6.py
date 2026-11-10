```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

# Find the reference kind union (e.g. export type RefKind = 'a' | 'b' | ...)
m = re.search(r"(?:export\s+)?type\s+\w*[Rr]ef[Kk]ind\w*\s*=\s*(.+?)(?:\s*;|$)", text)
if not m:
    # maybe enum or const union
    m = re.search(r"(?:export\s+)?(?:enum|const)\s+\w*[Rr]ef[Kk]ind\w*\s*=\s*\{?(.+?)}?", text, re.S)

members = []
if m:
    union_str = m.group(1)
    # extract string literals
    for lit in re.findall(r"'([^']*)'", union_str):
        members.append(lit)
    if not members:
        for lit in re.findall(r'"([^"]*)"', union_str):
            members.append(lit)

ref_kinds = len(members)
first_ref_kind = members[0] if members else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```