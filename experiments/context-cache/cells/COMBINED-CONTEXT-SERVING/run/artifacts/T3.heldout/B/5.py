```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

scope_block = "".join(lines[18:20])
members = re.findall(r"'([^']+)'", scope_block)
authority_scopes = len(set(members)) if members else 0

decision_block = "".join(lines[50:57])
real_change_without_decision_refused = bool(re.search(r"realChange.*Refused|Refused.*realChange", decision_block, re.DOTALL | re.IGNORECASE))

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```