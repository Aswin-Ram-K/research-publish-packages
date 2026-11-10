```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enum declared there
# Extract identifiers that are members (not keywords like 'export', 'type', 'const', etc.)
keywords = {'export', 'type', 'const', 'let', 'var', 'function', 'interface', 'enum', 'union', '|', '=>', 'string', 'number', 'boolean', 'true', 'false', 'null', 'undefined'}
scope_members = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_text)
scope_members = [m for m in scope_members if m not in keywords]
scope_count = len(set(scope_members))

# Lines 51-57 (1-indexed) -> indices 50-56
decision_block = lines[50:57]
decision_text = "\n".join(decision_block)

# Determine if a real change without a decision is refused (fail-closed)
# Look for patterns indicating refusal of real changes without decisions
refused = False
# Check for keywords indicating refusal/fail-closed behavior
decision_lower = decision_text.lower()
if any(pattern in decision_lower for pattern in [
    'refuse', 'fail-closed', 'fail closed', 'without decision', 
    'no decision', 'reject', 'denied', 'not allowed',
    'real change', 'change without'
]):
    refused = True

# More specific: look for the actual logic pattern
# If the code shows that changes without decisions are refused
has_refuse_pattern = (
    'refuse' in decision_lower or
    'fail.closed' in decision_lower or
    ('without' in decision_lower and 'decision' in decision_lower and ('refuse' in decision_lower or 'reject' in decision_lower or 'deny' in decision_lower))
)

if has_refuse_pattern:
    refused = True

print(f"authority_scopes={scope_count}")
print(f"real_change_without_decision_refused={str(refused).lower()}")
```