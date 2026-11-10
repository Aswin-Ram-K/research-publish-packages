```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\']([^"\']+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else None

# Find the shard function definition line (first slice(...) call)
shard_prefix = None
for idx, line in enumerate(lines):
    if "slice(" in line and idx >= 120 and idx <= 126:
        matches = re.findall(r'slice\((\d+),\s*(\d+)\)', line)
        if matches:
            shard_prefix = int(matches[0][1])
            break

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```