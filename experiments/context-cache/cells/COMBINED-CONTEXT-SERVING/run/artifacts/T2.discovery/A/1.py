```python
import re

# Parse the reference kinds from the pinned lines of src/reference.ts
# Lines 49-70 contain the reference kind declaration.
# We'll read the file and extract the relevant section.
with open("src/reference.ts", "r") as f:
    lines = f.readlines()

# Extract lines 49-70 (1-indexed, so indices 48-70)
pinned_lines = "".join(lines[48:70])

# Find the reference kind union/enumeration. Look for a pattern like:
# export type ReferenceKind = "kind1" | "kind2" | ...
# or an enum with members.
# Try to find a union of string literals.
match = re.search(r'(?:type|enum)\s+ReferenceKind\s*[=\:]\s*(.*?)(?:;|\{)', pinned_lines, re.DOTALL)
if match:
    content = match.group(1)
    # Extract string literals from a union like "kind1" | "kind2"
    kinds = re.findall(r'"([^"]*)"', content)
    if not kinds:
        # Try single quotes
        kinds = re.findall(r"'([^']*)'", content)
    if not kinds:
        # Could be an enum
        enum_match = re.search(r'(?:type|enum)\s+ReferenceKind\s*=\s*(.*?)(?:;|\{)', pinned_lines, re.DOTALL)
        if enum_match:
            enum_content = enum_match.group(1)
            # Enum members
            kinds = re.findall(r'(\w+)\s*=', enum_content)
            if not kinds:
                kinds = re.findall(r'(\w+)', enum_content)
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
first_ref_kind = distinct_kinds[0] if distinct_kinds else ""

print(f"ref_kinds={ref_kinds}")
print(f"first_ref_kind={first_ref_kind}")
```