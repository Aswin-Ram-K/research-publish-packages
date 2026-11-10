```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enumeration
# Remove comments and whitespace
scope_text_clean = re.sub(r'//.*', '', scope_text)
# Find all string literals (scope members)
members = re.findall(r'"([^"]+)"', scope_text_clean)
authority_scopes = len(members)

# Lines 51-57 (1-indexed) -> indices 50-56
decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)

# Check if a real change without a decision is refused
# Look for patterns like "refused" or "reject" in the context of real changes without decisions
real_change_without_decision_refused = False
decision_lower = decision_text.lower()
if "refused" in decision_lower or "reject" in decision_lower:
    # Verify it's about real changes without decisions
    if "real" in decision_lower or "change" in decision_lower:
        real_change_without_decision_refused = True

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```