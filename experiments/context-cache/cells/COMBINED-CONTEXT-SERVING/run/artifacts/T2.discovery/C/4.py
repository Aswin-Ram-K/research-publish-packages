```python
import re

with open("src/reference.ts", "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

pinned = lines[48:70]
text = "\n".join(pinned)

# Extract the reference kind union members declared in the pinned block.
# Look for a union type like: ReferenceKind = "kind1" | "kind2" | ...
union_match = re.search(r'(?:type\s+ReferenceKind\s*=\s*|ReferenceKind\s*=\s*)(.+?)(?:;|\n)', text, re.S)
kinds = []
if union_match:
    union_body = union_match.group(1)
    # Capture all string literal members in the union.
    members = re.findall(r'"([^"]+)"', union_body)
    kinds = list(dict.fromkeys(members))  # preserve order, dedupe

first_ref_kind = kinds[0] if kinds else None
ref_kinds = len(kinds)

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```