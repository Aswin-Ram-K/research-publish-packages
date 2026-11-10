```python
import re

source_path = "src/authority.ts"
with open(source_path, "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18:20
scope_block = "".join(lines[18:20])
# Extract the union members from the declared type.
members = re.findall(r'"([^"]+)"', scope_block)
if not members:
    # Fallback to non-quoted identifiers in a union.
    members = re.findall(r'([A-Za-z_]\w*)', scope_block)
authority_scopes = len(members)

# Lines 51-57 (1-indexed) -> indices 50:57
decision_block = "".join(lines[50:57])
# Fail-closed: a real change without a decision is refused.
real_change_without_decision_refused = bool(
    re.search(r'realChangeWithoutDecision\s*=\s*false', decision_block)
)

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```