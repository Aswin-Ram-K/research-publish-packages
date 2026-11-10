```python
import re

source_path = "src/hash.ts"
with open(source_path, "r") as f:
    lines = f.readlines()

# Line 74 (1-indexed) -> index 73: default hash algorithm
algo_line = lines[73]
# Find the algorithm string (a quoted word)
m = re.search(r'["\']([a-z0-9]+)["\']', algo_line)
algorithm = m.group(1) if m else ""

# Line 125 (1-indexed) -> index 124: shard function with first slice(...) call
shard_line = lines[124]
matches = re.findall(r'slice\((\d+),\s*(\d+)\)', shard_line)
second_arg = int(matches[0][1]) if matches else 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={second_arg}")
```