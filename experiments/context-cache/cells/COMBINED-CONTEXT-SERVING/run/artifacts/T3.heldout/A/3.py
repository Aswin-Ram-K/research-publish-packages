```python
import re

path = "src/authority.ts"
with open(path) as f:
    lines = f.readlines()

# Lines 19-20 (1-based) -> indices 18..19
scope_text = "".join(lines[18:20])
# Count distinct string-literal members of the declared union/list.
scopes = re.findall(r'"([^"]+)"', scope_text)
authority_scopes = len(scopes)

# Lines 51-57 (1-based) -> indices 50..56
decision_text = "".join(lines[50:57])
# fail-closed: a real change without a decision is refused.
real_change_without_decision_refused = bool(
    re.search(r"realChangeWithoutDecision\s*=\s*false", decision_text)
)

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```