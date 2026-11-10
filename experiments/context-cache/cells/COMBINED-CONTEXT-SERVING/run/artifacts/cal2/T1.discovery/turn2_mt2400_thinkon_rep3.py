

```python
import re

# The pinned file path from the manifest
hash_ts_path = "/home/zer0null/Duval/src/hash.ts"

with open(hash_ts_path, "r") as f:
    lines = f.readlines()

# Line 74 (1-indexed) -> index 73
line_74 = lines[73].strip() if len(lines) > 73 else ""
# Line 125 (1-indexed) -> index 124
line_125 = lines[124].strip() if len(lines) > 124 else ""

# Extract algorithm from line 74
# Look for common patterns like: DEFAULT_HASH = '...', algorithm = '...', etc.
algorithm = None
# Try to find a string value assigned in this line
match = re.search(r"['\"]([a-zA-Z0-9_\-]+)['\"]", line_74)
if match:
    algorithm = match.group(1)
else:
    # Fallback: use the whole line content
    algorithm = line_74

# Extract shard prefix from line 125
shard_prefix = None
match = re.search(r"['\"]([a-zA-Z0-9_\-]+)['\"]", line_125)
if match:
    shard_prefix = match.group(1)
else:
    # Fallback: use the whole line content
    shard_prefix = line_125

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```