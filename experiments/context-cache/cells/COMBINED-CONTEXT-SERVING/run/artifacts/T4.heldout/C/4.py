```python
import re

source_path = "src/observation.ts"
with open(source_path, "r") as f:
    lines = f.readlines()

# Extract lines 37-71 (1-indexed), i.e., indices 36 to 70
pinned = "".join(lines[36:71])

# Derive state_fields: count distinct members of the union/enumeration/literal list declared in the pinned block
# Look for the state fields union declaration
state_fields_match = re.search(r'state_fields\s*=\s*\((?:[^()]*\((?:[^()]*\))*\)*\)', pinned)
# More robust: find the union type definition
union_match = re.search(r'(?:state_fields|StateFields)\s*=\s*\{([^}]*)\}', pinned)
if union_match:
    members = union_match.group(1)
    # Count distinct members separated by commas at top level (not inside nested braces)
    depth = 0
    members_list = []
    current = []
    for ch in members:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        elif ch == ',' and depth == 0:
            members_list.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        members_list.append(''.join(current).strip())
    state_fields = len([m for m in members_list if m])
else:
    # Fallback: count enum-like members
    enum_match = re.search(r'enum\s+\w+\s*\{([^}]*)\}', pinned)
    if enum_match:
        members = [m.strip() for m in enum_match.group(1).split(',') if m.strip()]
        state_fields = len(members)
    else:
        # Count array literal members
        array_match = re.search(r'\[([^\]]*)\]', pinned)
        if array_match:
            members = [m.strip() for m in array_match.group(1).split(',') if m.strip()]
            state_fields = len(members)
        else:
            state_fields = 0

# Derive derived_regions: count distinct members of the union/enumeration/literal list
derived_regions_match = re.search(r'derived_regions\s*=\s*\{([^}]*)\}', pinned)
if derived_regions_match:
    members = derived_regions_match.group(1)
    depth = 0
    members_list = []
    current = []
    for ch in members:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        elif ch == ',' and depth == 0:
            members_list.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        members_list.append(''.join(current).strip())
    derived_regions = len([m for m in members_list if m])
else:
    enum_match = re.search(r'enum\s+\w+\s*\{([^}]*)\}', pinned)
    if enum_match:
        members = [m.strip() for m in enum_match.group(1).split(',') if m.strip()]
        derived_regions = len(members)
    else:
        array_match = re.search(r'\[([^\]]*)\]', pinned)
        if array_match:
            members = [m.strip() for m in array_match.group(1).split(',') if m.strip()]
            derived_regions = len(members)
        else:
            derived_regions = 0

print(f"state_fields={state_fields}")
print(f"derived_regions={derived_regions}")
```