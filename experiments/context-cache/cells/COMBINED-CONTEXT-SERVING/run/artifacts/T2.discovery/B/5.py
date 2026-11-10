```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48:70
pinned = "".join(lines[48:70])

# Extract string literal members (reference kinds) from the union/enum.
kinds = re.findall(r"'([^']+)'", pinned)
# Also catch unquoted identifiers that are members of a union type like: Foo = 'a' | 'b' | Bar
# If no string literals were found, try identifier members.
if not kinds:
    # Look for a type union: type X = A | B | C
    union_match = re.search(r"type\s+\w+\s*=\s*(.+)", pinned)
    if union_match:
        members = [m.strip() for m in union_match.group(1).split("|")]
        kinds = [m for m in members if m and not m.startswith("//")]
    else:
        # Enum style: enum X { A, B }
        enum_match = re.search(r"enum\s+\w+\s*\{([^}]*)\}", pinned)
        if enum_match:
            members = [m.strip() for m in enum_match.group(1).split(",")]
            kinds = [m for m in members if m and not m.startswith("//")]

# Deduplicate while preserving order
seen = set()
distinct = []
for k in kinds:
    if k not in seen:
        seen.add(k)
        distinct.append(k)

ref_kinds = len(distinct)
first_ref_kind = distinct[0] if distinct else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```