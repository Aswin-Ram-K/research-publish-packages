```python
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

scope_block = "".join(lines[18:20])
members = []
for m in __import__("re").finditer(r"'([^']+)'", scope_block):
    members.append(m.group(1))
authority_scopes = len(set(members)) if members else 0

decision_block = "".join(lines[50:57])
real_change_without_decision_refused = "Refused" in decision_block

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```