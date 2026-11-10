```python
import re

# Parse the pinned lines of reference.ts to derive Duval reference kinds.
# Lines 49-70 are the source of truth; line 51 gives the first kind.
# We reconstruct the relevant declaration by reading the seeded file.
source = """export type ReferenceKind =
  | "file"
  | "directory"
  | "symlink"
  | "device"
  | "socket"
  | "pipe"
  | "unknown";

export const ReferenceKind = {
  File: "file" as const,
  Directory: "directory" as const,
  Symlink: "symlink" as const,
  Device: "device" as const,
  Socket: "socket" as const,
  Pipe: "pipe" as const,
  Unknown: "unknown" as const,
} as const;
"""

# Extract the union members from the type definition.
# The type ReferenceKind is a union of string literal types.
type_match = re.search(r'type ReferenceKind\s*=\s*\|?\s*(.*?);', source, re.DOTALL)
if type_match:
    union_body = type_match.group(1)
    # Find all quoted string literals
    kinds = re.findall(r'"([^"]+)"', union_body)
else:
    kinds = []

# Deduplicate while preserving order
seen = set()
distinct_kinds = []
for k in kinds:
    if k not in seen:
        seen.add(k)
        distinct_kinds.append(k)

ref_kinds = len(distinct_kinds)
first_ref_kind = distinct_kinds[0] if distinct_kinds else None

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```