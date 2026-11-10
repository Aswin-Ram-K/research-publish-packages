with open("src/authority.ts", "r") as f:
    lines = f.readlines()

scope_block = lines[18:20]
scope_text = "\n".join(scope_block)

import re
idents = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', scope_text)
scope_members = []
for m in idents:
    if m not in scope_members:
        scope_members.append(m)
authority_scopes = len(scope_members)

decision_block = lines[50:57]
decision_text = "\n".join(decision_block)
real_change_without_decision_refused = "refused" in decision_text.lower() or "refuse" in decision_text.lower()

print(f"authority_scopes={authority_scopes}")
print(f"real_change_without_decision_refused={str(real_change_without_decision_refused).lower()}")
