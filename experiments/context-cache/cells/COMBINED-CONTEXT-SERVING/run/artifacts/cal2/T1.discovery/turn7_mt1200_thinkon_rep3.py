

```python
import re

PATH = "/home/zer0null/Duval/src/hash.ts"

with open(PATH, "r") as f:
    lines = f.readlines()

# Line numbers in the pointer are 1-based; convert to 0-based.
# Line 74 -> index 73, line 125 -> index 124.
algorithm_line = lines[73].strip()
shard_prefix_line = lines[124].strip()

# Extract the algorithm value from line 74.
# Expected pattern: something like `const ALGORITHM = "sha256"` or similar.
algo_match = re.search(r'["\']([a-zA-Z0-9_-]+)["\']', algorithm_line)
algorithm = algo_match.group(1) if algo_match else algorithm_line

# Extract the shard prefix length from line 125.
# Expected pattern: something like `const SHARD_PREFIX = 16` or `shardPrefix: 16`.
prefix_match = re.search(r'(\d+)', shard_prefix_line)
shard_prefix = int(prefix_match.group(1)) if prefix_match else shard_prefix_line

print(f"algorithm: {algorithm}")
print(f"shard_prefix: {shard_prefix}")
```