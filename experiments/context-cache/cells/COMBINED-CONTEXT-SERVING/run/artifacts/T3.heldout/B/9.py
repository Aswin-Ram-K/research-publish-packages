```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> index 18:20
scope_block = "".join(lines[18:20])
members = re.findall(r"'([^']+)'", scope_block)
authority_scopes = len(set(members)) if members else 0

# Lines 51-57 (1-indexed) -> index 50:57
decision_block = "".join(lines[50:57])
real_change_without_decision_refused = "Refused" in decision_block

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```