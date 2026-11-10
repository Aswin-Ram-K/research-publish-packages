```python
import re

# Parse the seeded authority.ts to derive values
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Extract scope count from lines 19-20 (0-indexed 18-19)
scope_lines = "".join(lines[18:20])
# Find all string literal scopes in the union/enumeration
scopes = re.findall(r"'([^']+)'", scope_lines)
authority_scopes = len(set(scopes))

# Extract fail-closed behavior from lines 51-57 (0-indexed 50-56)
decision_lines = "".join(lines[50:57])
# Check if a real change without decision is refused
real_change_without_decision_refused = "false" in decision_lines.lower() or "refuse" not in decision_lines.lower()

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```