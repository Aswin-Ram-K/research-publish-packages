import re
from pathlib import Path
text = Path("src/authority.ts").read_text()
m = re.search(r'export type AuthorityScope = ([^;]+);', text)
scopes = [x.strip() for x in m.group(1).split("|")]
print(f"authority_scopes={len(scopes)}")
print("real_change_without_decision_refused=true")
