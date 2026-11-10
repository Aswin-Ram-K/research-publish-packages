```python
import re

lines = open("src/observation.ts").read().splitlines()

def count_union_members(line):
    m = re.search(r'type\s+(\w+)\s*=\s*(.+?);', line)
    if m:
        union_body = m.group(2)
        members = [x.strip() for x in union_body.split('|') if x.strip()]
        return len(members)
    return 0

state_fields = count_union_members(lines[41])
derived_regions = count_union_members(lines[42])

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```