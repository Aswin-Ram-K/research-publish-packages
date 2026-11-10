```python
import re

# Parse the pinned lines of reference.ts to derive Duval reference kinds.
# Lines 49-70 are the source of truth; line 51 gives the first kind.
# We reconstruct the relevant declaration by reading the seeded file.
source_path = "src/reference.ts"

with open(source_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract lines 49-70 (1-indexed), i.e., indices 48..69
pinned = "".join(lines[48:70])

# Find the reference kind union/enumeration. Look for a type or enum declaration
# that lists the reference kinds. Common patterns:
#   type RefKind = "A" | "B" | "C"
#   enum RefKind { A, B, C }
# We'll search the pinned block for a union of string literals or an enum.

# Try to find a union of string literals like "..." | "..."
union_match = re.search(r'(?:type|interface|enum)\s+\w*[Rr]ef\w*\s*=\s*(.*?)(?:;|$)', pinned)
if union_match:
    union_body = union_match.group(1)
    # Extract string literals
    kinds = re.findall(r'"([^"]*)"', union_body)
else:
    # Try enum style: enum RefKind { A, B, C }
    enum_match = re.search(r'enum\s+\w*[Rr]ef\w*\s*\{\s*([^}]*)\s*\}', pinned)
    if enum_match:
        enum_body = enum_match.group(1)
        kinds = re.findall(r'(\w+)', enum_body)
    else:
        # Fallback: look for any list of string literals in the pinned block
        kinds = re.findall(r'"([^"]*)"', pinned)

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