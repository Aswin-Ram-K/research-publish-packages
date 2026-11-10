```python
import re

# Parse the pinned observation.ts lines to derive the counts.
source = """\
  state_fields: 8,
  derived_regions: 4,
"""

state_fields = None
derived_regions = None

for line in source.splitlines():
    if re.match(r'\s*state_fields:\s*(\d+),', line):
        state_fields = int(re.match(r'\s*state_fields:\s*(\d+),', line).group(1))
    elif re.match(r'\s*derived_regions:\s*(\d+),', line):
        derived_regions = int(re.match(r'\s*derived_regions:\s*(\d+),', line).group(1))

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```