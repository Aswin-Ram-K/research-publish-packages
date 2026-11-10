```python
import re

# Parse the seeded authority.ts to derive the values.
source_path = "src/authority.ts"
with open(source_path, "r") as f:
    lines = f.readlines()

# Extract authority scopes from lines 19-20 (1-indexed in the pointer, so list indices 18-19).
# We look for the union/enumeration/literal list declared there.
scope_lines = "".join(lines[18:20])
# Find all string literals in the scope definition which represent the distinct scopes.
scopes = re.findall(r'"([^"]+)"', scope_lines)
authority_scopes = len(scopes)

# Extract fail-closed outcome from lines 51-57 (list indices 50-56).
decision_lines = "".join(lines[50:57])
# Determine if a real change without a decision is refused.
# Look for a pattern indicating refusal of real changes without decisions.
real_change_without_decision_refused = False
if re.search(r'realChangeWithoutDecision\s*=\s*false', decision_lines) or \
   re.search(r'real_change_without_decision\s*=\s*false', decision_lines) or \
   re.search(r'no_decision_refused\s*=\s*false', decision_lines):
    real_change_without_decision_refused = False
elif re.search(r'realChangeWithoutDecision\s*=\s*true', decision_lines) or \
     re.search(r'real_change_without_decision\s*=\s*true', decision_lines) or \
     re.search(r'no_decision_refused\s*=\s*true', decision_lines):
    real_change_without_decision_refused = True
else:
    # Fallback: check for explicit refusal language
    if re.search(r'refuse.*real.*change.*without.*decision', decision_lines, re.IGNORECASE) or \
       re.search(r'no.*decision.*refused', decision_lines, re.IGNORECASE):
        real_change_without_decision_refused = True
    else:
        real_change_without_decision_refused = False

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```