```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

# Find the reference kind union (e.g. export type RefKind = 'a' | 'b' | ...)
m = re.search(r'(?:export\s+)?type\s+\w*[Rr]ef[Kk]ind\w*\s*=\s*(.+?);', text, re.S)
if m:
    members = [s.strip().strip("'\"") for s in re.split(r'\|', m.group(1))]
    members = [s for s in members if s]
    ref_kinds = len(members)
    first_ref_kind = members[0]
else:
    # Fallback: enum
    m = re.search(r'(?:export\s+)?enum\s+\w*[Rr]ef[Kk]ind\w*\s*\{(.+?)\}', text, re.S)
    if m:
        members = [s.strip().split('=')[0].strip().strip("'\"") for s in re.split(r',', m.group(1))]
        members = [s for s in members if s]
        ref_kinds = len(members)
        first_ref_kind = members[0]
    else:
        raise RuntimeError("Could not find reference kind declaration")

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```