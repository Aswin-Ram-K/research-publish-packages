```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\'](\w+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else None

shard_line = lines[124].strip()
slice_match = re.search(r'slice\((\d+),\s*(\d+)\)', shard_line)
shard_prefix = int(slice_match.group(2)) if slice_match else None

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```