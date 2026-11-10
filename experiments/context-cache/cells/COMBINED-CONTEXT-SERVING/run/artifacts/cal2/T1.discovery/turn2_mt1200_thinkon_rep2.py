

```python
import re

path = "/home/zer0null/Duval/src/hash.ts"
with open(path, "r") as f:
    lines = f.readlines()

# Line 74 (0-indexed 73) -> default hash algorithm
line74 = lines[73].strip()
# Line 125 (0-indexed 124) -> shard prefix
line125 = lines[124].strip()

# Extract algorithm value - look for a string assignment
algo_match = re.search(r"['\"](\w+)['\"]", line74)
algorithm = algo_match.group(1) if algo_match else line74

# Extract shard prefix value
prefix_match = re.search(r"['\"](\w+)['\"]", line125)
shard_prefix = prefix_match.group(1) if prefix_match else line125

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```