```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> index 18:20
scope_block = "".join(lines[18:20])
# Count distinct string literal members in the union/enum declaration
members = re.findall(r"'([^']+)'", scope_block)
scope_count = len(set(members))

# Lines 51-57 (1-indexed) -> index 50:57
decision_block = "".join(lines[50:57])
# Fail-closed: a real change without a decision is refused
real_change_without_decision_refused = "Refused" in decision_block or "refused" in decision_block

print(f"authority_scopes={scope_count}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```