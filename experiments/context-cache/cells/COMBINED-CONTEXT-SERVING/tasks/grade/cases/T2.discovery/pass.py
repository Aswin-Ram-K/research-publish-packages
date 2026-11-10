import re
from pathlib import Path
text = Path("src/reference.ts").read_text()
m = re.search(r'export const REF_KINDS = \[\n(.*?)\] as const;', text, re.S)
items = re.findall(r'"([^"]+)"', m.group(1))
print(f"ref_kinds={len(items)}")
print(f"first_ref_kind={items[0]}")
