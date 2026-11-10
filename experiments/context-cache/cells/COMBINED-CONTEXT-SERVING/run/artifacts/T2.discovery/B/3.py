```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
members = re.findall(r"'([^']+)'", pinned)
# Also catch unquoted identifiers if present (e.g. plain union members).
idents = re.findall(r"(?<!['\w])([A-Za-z_]\w*)(?![\w'\"`])", pinned)

kinds = []
seen = set()
for m in members:
    if m not in seen:
        kinds.append(m)
        seen.add(m)
for i in idents:
    if i not in seen and i not in ("type", "interface", "enum", "const", "let", "var", "return", "export", "import", "from", "default", "function", "class"):
        kinds.append(i)
        seen.add(i)

ref_kinds = len(kinds)
first_ref_kind = kinds[0] if kinds else None

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```