```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enum declared there
scope_members = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_text)
# Filter out type keywords and common non-member tokens
exclude = {"readonly", "partial", "type", "interface", "extends", "Record", "string", "number", "boolean", "undefined", "null", "never", "unknown", "any", "keyof", "typeof", "import", "export", "from", "enum", "union", "authority", "Scope", "scope"}
scope_members = [m for m in scope_members if m not in exclude]
scope_count = len(set(scope_members))

# Lines 51-57 (1-indexed) -> indices 50-56
decision_block = lines[50:57]
decision_text = "\n".join(decision_block)

# Determine fail-closed: if a real change without a decision is refused
# Look for patterns indicating refusal of real change without decision
refused = False
# Check for keywords indicating refusal/fail-closed behavior for real changes without decisions
has_refuse = bool(re.search(r'\b(refuse|reject|fail.?closed|not.?allowed|disallow|prohibit)\b', decision_text, re.IGNORECASE))
has_real_change = bool(re.search(r'\b(real\s*change|write|mutate|update|apply)\b', decision_text, re.IGNORECASE))
has_without_decision = bool(re.search(r'\b(without\s*decision|no\s*decision|undecided|undecided)\b', decision_text, re.IGNORECASE))

if has_refuse and (has_real_change or has_without_decision):
    refused = True
elif has_refuse and has_real_change and has_without_decision:
    refused = True
elif re.search(r'\bfail.?closed\b', decision_text, re.IGNORECASE):
    refused = True

print(f"authority_scopes={scope_count}")
print(f"real_change_without_decision_refused={'true' if refused else 'false'}")
```