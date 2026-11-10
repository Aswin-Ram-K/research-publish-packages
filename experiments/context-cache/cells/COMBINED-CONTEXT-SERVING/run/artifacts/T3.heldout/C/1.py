```python
import re

# Parse the authority.ts file to extract the required values
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Extract authority scopes from lines 19-20 (0-indexed: 18-19)
# Looking for the scope enumeration or union type declaration
scope_lines = "".join(lines[18:20])

# Count distinct members in the union/enumeration
# Find all string literals or identifiers in the scope definition
scope_members = re.findall(r'"([^"]+)"', scope_lines)
if not scope_members:
    # Try to find identifier-based union members
    scope_members = re.findall(r"'([^']+)'", scope_lines)
if not scope_members:
    # Try direct identifier matching
    scope_members = re.findall(r'(?:\||,)\s*([A-Za-z_][A-Za-z0-9_]*)', scope_lines)
    if scope_members:
        scope_members = [m.strip() for m in scope_members if m.strip()]

authority_scopes = len(scope_members)

# Extract fail-closed behavior from lines 51-57 (0-indexed: 50-56)
decision_lines = "".join(lines[50:57])

# Check if a real change without a decision is refused
# Look for patterns indicating refusal of changes without decisions
refused_patterns = [
    r'refuse.*real.*change',
    r'change.*without.*decision.*refus',
    r'no.*decision.*real.*change',
    r'refused.*no.*decision',
    r'fail.?closed',
    r'return.*false.*change',
    r'reject.*change.*decision'
]

real_change_without_decision_refused = False
for pattern in refused_patterns:
    if re.search(pattern, decision_lines, re.IGNORECASE):
        real_change_without_decision_refused = True
        break

# If no explicit pattern found, check for explicit refusal indicators
if not real_change_without_decision_refused:
    refusal_indicators = [
        r'refuse',
        r'refus',
        r'fail.?closed',
        r'return\s+false',
        r'reject'
    ]
    for indicator in refusal_indicators:
        if re.search(indicator, decision_lines, re.IGNORECASE):
            real_change_without_decision_refused = True
            break

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```