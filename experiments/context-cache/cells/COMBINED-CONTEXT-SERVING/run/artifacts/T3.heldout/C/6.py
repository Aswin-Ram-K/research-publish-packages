```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enumeration/literal list declared there
# Remove comments, then find all members separated by commas/| in the scope declaration
# Strip out comment text
scope_clean = re.sub(r'//.*', '', scope_text)
# Find all identifiers that are members (alphanumeric + underscore)
members = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_clean)
# Filter out type keywords and common non-member tokens
exclude = {'scope', 'authority', 'string', 'number', 'boolean', 'true', 'false', 'type', 'interface', 'enum', 'union', '=>', 'readonly', 'partial'}
distinct_members = [m for m in members if m not in exclude]
authority_scopes = len(distinct_members)

# Lines 51-57 (1-indexed) -> indices 50-56
decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)

# Check if a real change without a decision is refused (fail-closed)
# Look for patterns like "refused", "reject", "fail", "denied" in the context of no decision
has_refusal = bool(re.search(r'\b(refused|reject|refuse|denied|fail)\b', decision_text, re.IGNORECASE))

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={'true' if has_refusal else 'false'}")
```