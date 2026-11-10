```python
import re

src_path = "src/reference.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Lines 49-70 (1-indexed) -> indices 48-69
pinned = "".join(lines[48:70])

# Find the reference kind type union or enum declaration.
# Look for a type alias or enum with a list of string literal members.
# Try to extract members from a union of string literals like:
#   export type ReferenceKind = "a" | "b" | ...
# or an enum:
#   export enum ReferenceKind { A = "a", B = "b" }

members = []

# Pattern 1: type union of string literals
type_match = re.search(r'(?:type|enum)\s+ReferenceKind\b.*?=\s*(.*?)(?:;|$)', pinned, re.DOTALL)
if type_match:
    body = type_match.group(1)
    # String literals in union
    strings = re.findall(r'"([^"]*)"', body)
    if strings:
        members = strings
    else:
        # Enum members without explicit values: count them
        enum_members = re.findall(r'(\w+)\s*=', body)
        if enum_members:
            members = enum_members
        else:
            # Bare enum member names
            members = re.findall(r'^\s*(\w+)', body, re.MULTILINE)

# Pattern 2: if no type/enum header found, search whole pinned block for ReferenceKind members
if not members:
    # Look for "kind" | "value" style unions anywhere
    all_strings = re.findall(r'"([^"]*)"', pinned)
    # Filter plausible reference kind strings (non-empty, not code keywords)
    candidates = [s for s in all_strings if s and not re.match(r'^[a-z_]+$', s) or len(s) > 1]
    if candidates:
        members = candidates

# Deduplicate while preserving order
seen = set()
unique_members = []
for m in members:
    if m not in seen:
        seen.add(m)
        unique_members.append(m)

ref_kinds = len(unique_members)
first_ref_kind = unique_members[0] if unique_members else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```