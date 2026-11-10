import re
from pathlib import Path
text = Path("src/hash.ts").read_text()
m = re.search(r'readonly algorithm = "([^"]+)";', text)
print(f"algorithm={m.group(1)}")
m2 = re.search(r'slice\(0,\s*(\d+)\)', text)
print(f"shard_prefix={m2.group(1)}")
