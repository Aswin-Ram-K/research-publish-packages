```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Extract identifier tokens that are scope members (exclude keywords/types)
idents = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', scope_text)
# Filter out TS keywords and type names
keywords = {'string', 'number', 'boolean', 'any', 'unknown', 'never', 'void', 'object', 'union', 'enum', 'type'}
scope_members = [m for m in idents if m not in keywords and not m.startswith('__')]
scope_count = len(set(scope_members))

# Lines 51-57 (1-indexed) -> indices 50-56
decision_block = lines[50:57]
decision_text = "\n".join(decision_block)

# Detect fail-closed: a real change without a decision is refused
# Look for patterns like: throws, reject, false, denied, refused, error in decision path
has_refusal = bool(re.search(r'\b(refused|reject|throw|denied|false|error|forbidden)\b', decision_text, re.IGNORECASE))

print(f"authority_scopes={scope_count}")
print(f"real_change_without_decision_refused={'true' if has_refusal else 'false'}")
```