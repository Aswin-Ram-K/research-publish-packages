```python
import re

with open("src/authority.ts", "r") as f:
    lines = f.readlines()

# Lines 19-20 (1-indexed) -> indices 18-19
scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

# Count distinct members of the union/enum declared in the pinned scope lines
scope_members = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_text)
# Filter out type keywords and common non-member tokens
exclude = {"readonly", "string", "number", "boolean", "true", "false", "undefined", "null", "any", "unknown", "never", "void", "type", "interface", "enum", "union", "partial", "required", "record", "keyof", "instanceof", "as", "in", "is", "extends", "import", "export", "from", "const", "let", "var", "function", "class", "new", "this", "super", "return", "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "try", "catch", "finally", "throw", "typeof", "delete", "void", "yield", "async", "await", "of", "get", "set", "static", "public", "private", "protected", "abstract", "implements", "namespace", "module", "declare", "satisfies", "asserts", "infer", "template", "literal"}
scope_members = [m for m in scope_members if m not in exclude]
authority_scopes = len(set(scope_members))

# Lines 51-57 (1-indexed) -> indices 50-56
decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)

# Determine fail-closed: check if a real change without a decision is refused
# Look for patterns indicating refusal of real changes without decisions
has_refusal = False
# Check for keywords indicating refusal/rejection in the context of changes without decisions
refusal_patterns = [
    r'refused?',
    r'reject(ed|s)?',
    r'denied?',
    r'not\s+(allowed|permitted|authorized)',
    r'must\s+have',
    r'requires?\s+(a\s+)?decision',
    r'no\s+change\s+without',
    r'abstain',
    r'fail[- ]?closed',
    r'cannot\s+proceed',
    r'blocked',
    r'required\s+decision',
]
for pattern in refusal_patterns:
    if re.search(pattern, decision_text, re.IGNORECASE):
        has_refusal = True
        break

# Also check for explicit "real change" + refusal language
real_change_pattern = r'real\s+change'
if real_change_pattern in decision_text.lower():
    # If "real change" is mentioned alongside refusal language
    if has_refusal:
        real_change_without_decision_refused = True
    else:
        # Check more broadly for decision requirement
        decision_required_patterns = [
            r'decision\s+required',
            r'requires?\s+decision',
            r'must\s+be\s+decided',
            r'needs?\s+a\s+decision',
        ]
        for pattern in decision_required_patterns:
            if re.search(pattern, decision_text, re.IGNORECASE):
                has_refusal = True
                break

real_change_without_decision_refused = has_refusal

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```