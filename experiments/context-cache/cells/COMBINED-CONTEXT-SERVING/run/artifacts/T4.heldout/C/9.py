```python
import re

source_path = "src/observation.ts"
with open(source_path, "r") as f:
    lines = f.readlines()

# Extract lines 37-71 (1-indexed), i.e., indices 36 to 70
pinned = "".join(lines[36:71])

# Derive state_fields: count distinct members of union/enum/literal list declared in pinned block
# Parse the pinned block for the state type definition and count union/enum members
state_fields = 0
derived_regions = 0

# Look for state field definition - typically a union, enum, or literal list
# Count distinct members
state_match = re.search(r'state\s*[:=]\s*(.+?)(?:;|$)', pinned, re.DOTALL)
if state_match:
    state_def = state_match.group(1)
    # Count union members (separated by |)
    if '|' in state_def:
        members = [m.strip() for m in re.split(r'\|', state_def) if m.strip() and not m.strip().startswith('//')]
        state_fields = len(members)
    # Count enum members
    elif '{' in state_def:
        members = re.findall(r'(\w+)\s*[:=]', state_def)
        state_fields = len(members)
    # Count array/literal list members
    elif '[' in state_def:
        members = re.findall(r'(\w+)', state_def)
        state_fields = len([m for m in members if m not in ('Array', 'of', 'in', 'for')])

# Look for derived regions - typically a length/offset from call argument or a list
region_match = re.search(r'derived\s*regions?\s*[:=]\s*(\d+)', pinned, re.IGNORECASE | re.DOTALL)
if region_match:
    derived_regions = int(region_match.group(1))
else:
    # Look for a call argument that specifies region count
    call_match = re.search(r'(?:regions?|derive)\s*\([^)]*(\d+)', pinned, re.IGNORECASE | re.DOTALL)
    if call_match:
        derived_regions = int(call_match.group(1))
    else:
        # Count region entries in a literal list
        region_list = re.findall(r'region\s*(\d+)', pinned, re.IGNORECASE)
        if region_list:
            derived_regions = len(region_list)
        else:
            # Default: count distinct region-like declarations
            region_decls = re.findall(r'(?:region|zone|area)\s+[\w$]+', pinned, re.IGNORECASE)
            derived_regions = len(region_decls)

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```