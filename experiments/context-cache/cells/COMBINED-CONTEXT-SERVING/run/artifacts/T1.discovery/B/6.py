```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'"([^"]+)"', algorithm_line)
if not algorithm_match:
    algorithm_match = re.search(r"'([^']+)'", algorithm_line)
algorithm = algorithm_match.group(1)

# Find the shard function definition line within L73-L126 and its first slice(...) call.
shard_prefix = None
for idx in range(72, min(126, len(lines))):
    line = lines[idx]
    slice_match = re.search(r'slice\((\d+),\s*(\d+)\)', line)
    if slice_match:
        shard_prefix = int(slice_match.group(2))
        break

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```