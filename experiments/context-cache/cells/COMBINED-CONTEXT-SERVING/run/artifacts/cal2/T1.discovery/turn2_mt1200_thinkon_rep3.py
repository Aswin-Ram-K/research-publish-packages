

```python
import re

PATH = "/home/zer0null/Duval/src/hash.ts"

with open(PATH, "r") as f:
    lines = f.readlines()

# Line numbers in the pointer are 1-based; convert to 0-based.
# Line 74 -> index 73, line 125 -> index 124.
algorithm_line = lines[73].strip()
shard_line = lines[124].strip()

# Extract the algorithm value (a quoted string).
alg_match = re.search(r"['\"](\w+)['\"]", algorithm_line)
algorithm = alg_match.group(1) if alg_match else algorithm_line

# Extract the shard prefix length (a number).
shard_match = re.search(r"(\d+)", shard_line)
shard_prefix = int(shard_match.group(1)) if shard_match else int(shard_line)

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```