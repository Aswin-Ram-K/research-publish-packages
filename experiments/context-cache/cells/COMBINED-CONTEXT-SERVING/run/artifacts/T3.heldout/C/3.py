```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_lines = lines[18:20]
scope_text = "\n".join(scope_lines)

# Extract the authority scope enum/union members
# Find all string literal members in the scope declaration
members = re.findall(r'"([^"]+)"', scope_text)
# Also check for non-quoted identifiers in case of union type
if not members:
    members = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)', scope_text)
    # Filter out keywords
    keywords = {'export', 'type', 'AuthorityScope', '|', '=', '=>', 'string', 'number', 'boolean'}
    members = [m for m in members if m not in keywords]

authority_scopes = len(members)

# Lines 51-57 (1-indexed) -> indices 50-56
decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)

# Check if a real change without a decision is refused
# Look for patterns like "refused", "reject", "denied" in the context of decision
refused = False
if re.search(r'refused', decision_text, re.IGNORECASE):
    refused = True
elif re.search(r'reject', decision_text, re.IGNORECASE):
    refused = True
elif re.search(r'denied', decision_text, re.IGNORECASE):
    refused = True

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={'true' if refused else 'false'}")
```