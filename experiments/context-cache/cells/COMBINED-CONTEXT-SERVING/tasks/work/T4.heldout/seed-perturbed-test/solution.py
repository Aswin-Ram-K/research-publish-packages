import re
from pathlib import Path
text = Path("src/observation.ts").read_text()
m = re.search(r'has \*\*(\d+)\*\* fields', text)
print(f"state_fields={m.group(1)}")
m2 = re.search(r'produce the \*\*(\d+)\*\* regions', text)
print(f"derived_regions={m2.group(1)}")
