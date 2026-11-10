```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enumeration/literal list declared in lines 19-20
# Remove comments and whitespace, then find the content between { and }
# Extract the enum/union body
match = re.search(r'\{([^}]*)\}', scope_text)
if match:
    body = match.group(1)
    # Split by commas and clean up
    members = [m.strip() for m in re.split(r',', body) if m.strip()]
    # Filter out empty strings and non-member lines
    authority_scopes = len([m for m in members if m and not m.startswith('//')])
else:
    # Fallback: count comma-separated values in the lines
    all_text = " ".join(scope_block)
    # Remove comments
    all_text = re.sub(r'//.*', '', all_text)
    members = [m.strip() for m in re.split(r',', all_text) if m.strip() and not m.strip().startswith('//')]
    authority_scopes = len(members)

# Lines 51-57 (1-indexed) -> indices 50-56
decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)

# Determine if a real change without a decision is refused (fail-closed)
# Look for patterns like "refused", "fail-closed", "denied", "reject" in the context of real changes without decisions
real_change_without_decision_refused = False
decision_lower = decision_text.lower()
if re.search(r'real\s*change', decision_text) or re.search(r'no\s*decision', decision_text):
    if re.search(r'refuse|fail.?closed|deny|reject|prohibit|block', decision_text, re.IGNORECASE):
        real_change_without_decision_refused = True

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={'true' if real_change_without_decision_refused else 'false'}")
```