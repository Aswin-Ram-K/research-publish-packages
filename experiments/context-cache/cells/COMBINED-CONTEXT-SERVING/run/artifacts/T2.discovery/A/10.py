```python
import re

with open("src/reference.ts", "r") as f:
    lines = f.readlines()

pinned = "".join(lines[48:70])

m = re.search(r'(?:export\s+)?(?:type|enum)\s+ReferenceKind\s*[=:]?\s*(.*?)(?:;|\)|\n)', pinned, re.DOTALL)
kinds = []
if m:
    body = m.group(1)
    lit = re.findall(r'["\']([^"\']*)["\']', body)
    if lit:
        kinds = lit
    else:
        members = re.findall(r'^\s*(\w+)', body, re.MULTILINE)
        kinds = members

seen = set()
distinct = []
for k in kinds:
    if k not in seen:
        seen.add(k)
        distinct.append(k)

ref_kinds = len(distinct)
first_ref_kind = distinct[0]

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```