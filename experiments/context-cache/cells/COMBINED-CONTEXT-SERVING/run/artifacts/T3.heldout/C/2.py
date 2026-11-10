```python
# Parse the authority.ts file to extract the required values
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Extract authority scopes from lines 19-20 (1-indexed), which are indices 18-19
# We need to find the scope enumeration/union and count distinct members
scope_lines = lines[18:20]
scope_text = "".join(scope_lines)

# Count distinct members in the scope declaration
# Looking for enum members or union type members
import re

# Find all scope member identifiers (identifiers in an enum or union)
# Extract identifiers that look like enum members or union literals
members = re.findall(r'\b([A-Z_][A-Z0-9_]*)\s*[:=]', scope_text)
if not members:
    # Try to find simple enum-style members
    members = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*[,;]', scope_text)
    
# Count distinct members
distinct_members = len(set(members))
authority_scopes = distinct_members

# Extract fail-closed behavior from lines 51-57 (1-indexed), which are indices 50-56
decision_lines = lines[50:57]
decision_text = "".join(decision_lines)

# Check if a real change without a decision is refused
# Look for patterns indicating refusal/fail-closed behavior
refused = False
if re.search(r'refuse|refused|fail.?closed|reject|not.?allowed|forbidden|error', decision_text, re.IGNORECASE):
    refused = True

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={'true' if refused else 'false'}")
```