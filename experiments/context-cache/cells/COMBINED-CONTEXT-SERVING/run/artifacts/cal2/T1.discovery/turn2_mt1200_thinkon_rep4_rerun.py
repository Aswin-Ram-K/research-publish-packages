

```python
import re

with open('src/hash.ts', 'r') as f:
    lines = f.readlines()

# Line 74 (1-indexed) -> index 73
line_74 = lines[73].strip()
# Line 125 (1-indexed) -> index 124
line_125 = lines[124].strip()

# Extract the algorithm value (first quoted string or identifier on the line)
algo_match = re.search(r"['\"]([a-zA-Z0-9_.-]+)['\"]", line_74)
algorithm = algo_match.group(1) if algo_match else re.sub(r'^.*?=\s*', '', line_74).strip().strip("';")

# Extract the shard prefix value (first quoted string on the line)
prefix_match = re.search(r"['\"]([a-zA-Z0-9_.-]+)['\"]", line_125)
shard_prefix = prefix_match.group(1) if prefix_match else re.sub(r'^.*?=\s*', '', line_125).strip().strip("';")

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```