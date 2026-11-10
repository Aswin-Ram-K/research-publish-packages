```python
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

scope_block = "".join(lines[18:50])
scope_count = len(re.findall(r'[A-Z_][A-Z0-9_]*', scope_block))
decision_refused = "Refused" in "".join(lines[50:57])
print(f"authority_scopes={scope_count}")
print(f"real_change_without_decision_refused={'true' if decision_refused else 'false'}")
```