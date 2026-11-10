```python
with open("src/authority.ts", "r") as f:
    lines = f.readlines()

scope_lines = lines[18:20]
scope_text = "\n".join(scope_lines)

import re
scope_members = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_text)
scope_members = [m for m in scope_members if m not in ('readonly', 'string', 'number', 'boolean', 'true', 'false', 'null', 'undefined', 'void', 'any', 'never', 'unknown', 'type', 'interface', 'enum', 'export', 'import', 'from', 'const', 'let', 'var', 'function', 'class', 'extends', 'implements', 'private', 'protected', 'public', 'static', 'abstract', 'async', 'await', 'yield', 'return', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'default', 'try', 'catch', 'finally', 'throw', 'new', 'delete', 'typeof', 'instanceof', 'in', 'of', 'this', 'super', 'constructor', 'get', 'set', 'keyof', 'infer', 'declare', 'namespace', 'module', 'global', 'as', 'satisfies')]
authority_scopes = len(set(scope_members))

decision_lines = lines[50:57]
decision_text = "\n".join(decision_lines)
real_change_without_decision_refused = "refused" in decision_text.lower() or "fail-closed" in decision_text.lower() or "refuse" in decision_text.lower()

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
```