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
    if re.match(r'\s*state_fields:', line):
        m = re.search(r'(\d+)', line)
        if m:
            state_fields = int(m.group(1))
    elif re.match(r'\s*derived_regions:', line):
        m = re.search(r'(\d+)', line)
        if m:
            derived_regions = int(m.group(1))

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```