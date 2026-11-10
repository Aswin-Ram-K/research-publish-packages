```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\'](\w+)["\']', algorithm_line)
algorithm = algorithm_match.group(1)

# Line 125 (1-based) defines the shard function with the first slice(...) call.
shard_line = lines[124].strip()
slice_match = re.search(r'slice\(\s*\d+\s*,\s*(\d+)\s*\)', shard_line)
shard_prefix = int(slice_match.group(1))

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```