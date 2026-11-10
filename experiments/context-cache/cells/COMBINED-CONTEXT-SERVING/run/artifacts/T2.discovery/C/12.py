```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

match = re.search(r"(?:export\s+type|type)\s+(\w+)\s*=\s*(.+)", text)
if not match:
    raise SystemExit("No type union found in pinned lines")

name = match.group(1)
body = match.group(2)

# Strip trailing semicolon and any comment after the union
body = body.split(";")[0].split("//")[0].strip()

# Split union members on top-level pipes
members = []
depth = 0
current = []
for ch in body:
    if ch in "<{(":
        depth += 1
    elif ch in ">}":
        depth -= 1
    if ch == "|" and depth == 0:
        members.append("".join(current).strip())
        current = []
    else:
        current.append(ch)
tail = "".join(current).strip()
if tail:
    members.append(tail)

kinds = [m for m in members if re.match(r"^\s*['\"]", m)]
ref_kinds = len(kinds)
first_ref_kind = kinds[0].strip("'\"") if kinds else kinds[0]

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```