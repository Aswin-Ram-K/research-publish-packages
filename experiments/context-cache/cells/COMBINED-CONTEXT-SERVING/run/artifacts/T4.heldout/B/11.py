```python
import re

# Parse the pinned observation.ts lines (L42-L43) to derive the counts.
source = """\
  state_fields: 8,
  derived_regions: 4,
"""

state_fields = None
derived_regions = None

for line in source.splitlines():
    m = re.match(r'\s*state_fields:\s*(\d+),', line)
    if m:
        state_fields = int(m.group(1))
    m = re.match(r'\s*derived_regions:\s*(\d+),', line)
    if m:
        derived_regions = int(m.group(1))

assert state_fields is not None, "state_fields not found"
assert derived_regions is not None, "derived_regions not found"

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```