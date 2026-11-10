```python
import re

path = "src/hash.ts"
lines = open(path).readlines()

# Line 74 (1-indexed) = index 73: default hash algorithm string
algo_line = lines[73]
m = re.search(r'["\']([a-z0-9]+)["\']', algo_line)
algorithm = m.group(1)

# Line 125 (1-indexed) = index 124: shard function, first slice(...) second arg
shard_line = lines[124]
slices = re.findall(r'slice\((\d+)\s*,\s*(\d+)\)', shard_line)
shard_prefix = int(slices[0][1])

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```