

```python
import re

with open("src/hash.ts", "r") as f:
    lines = f.readlines()

# Extract algorithm from line 74 (0-indexed: 73)
line_74 = lines[73].strip()
# Find the algorithm value - typically something like 'sha256' or similar
algo_match = re.search(r"(sha256|sha3-256|sha384|sha512|blake2b|keccak256|md5|sha1)", line_74, re.IGNORECASE)
algorithm = algo_match.group(1).lower() if algo_match else "unknown"

# Extract shard prefix from line 125 (0-indexed: 124)
line_125 = lines[124].strip()
# Look for a prefix pattern - typically a string like "duval-" or similar
prefix_match = re.search(r'["\']([a-z0-9-]+)["\']', line_125)
shard_prefix = prefix_match.group(1) if prefix_match else "unknown"

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```