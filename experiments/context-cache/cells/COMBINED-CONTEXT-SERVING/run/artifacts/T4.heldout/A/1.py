```python
import re

# Parse the pinned lines of src/observation.ts to derive counts.
# Line 42 (0-indexed 41) declares the state fields union.
# Line 43 (0-indexed 42) declares the derived regions union.
source = r"src/observation.ts"
lines = open(source).read().splitlines()

def count_union_members(line):
    # Find the union type: e.g. type X = A | B | C;
    m = re.search(r'type\s+\w+\s*=\s*(.+?);', line)
    if m:
        union_body = m.group(1)
        # Count distinct members separated by |
        members = [x.strip() for x in union_body.split('|') if x.strip()]
        return len(members)
    return 0

state_fields = count_union_members(lines[41])
derived_regions = count_union_members(lines[42])

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```