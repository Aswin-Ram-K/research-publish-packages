```python
import re

# Parse the pinned lines of reference.ts to derive Duval reference kinds.
# Lines 49-70 contain the reference kind union/enumeration.
# We read the seeded source file directly (no network, no outside writes).
src_path = "src/reference.ts"
with open(src_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract lines 49-70 (1-indexed), i.e., indices 48-69
pinned = "".join(lines[48:70])

# Find the reference kind union or enum members.
# Look for a type union like: "KindA" | "KindB" | ...
# or an enum with members.
# Try to find a string literal union pattern first.
union_match = re.search(r'(?:type\s+\w+\s*=\s*)?("(?:[^"\\]|\\.)*"\s*\|\s*)*', pinned)
# More robust: find all string literals in the relevant declaration.
# Look for the reference kind declaration. Common pattern:
#   export type ReferenceKind = "kind1" | "kind2" | ...
type_match = re.search(r'type\s+\w*\bReference\w*\b\s*=\s*("(?:[^"\\]|\\.)*"(?:\s*\|\s*"(?:[^"\\]|\\.)*")*)', pinned)
kinds = []
if type_match:
    literals_str = type_match.group(1)
    kinds = re.findall(r'"((?:[^"\\]|\\.)*)"', literals_str)

# If no union type found, look for an enum
if not kinds:
    enum_match = re.search(r'enum\s+\w*\bReference\w*\b\s*\{([^}]*)\}', pinned)
    if enum_match:
        members_str = enum_match.group(1)
        # enum members: "Name" = "value" or just Name
        kinds = re.findall(r'=\s*"((?:[^"\\]|\\.)*)"', members_str)
        if not kinds:
            kinds = re.findall(r'\b([A-Za-z_]\w*)\b', members_str)

# Deduplicate while preserving order
seen = set()
distinct_kinds = []
for k in kinds:
    if k not in seen:
        seen.add(k)
        distinct_kinds.append(k)

ref_kinds = len(distinct_kinds)
first_ref_kind = distinct_kinds[0] if distinct_kinds else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```