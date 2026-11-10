

```python
import re

path = "/home/zer0null/Duval/src/hash.ts"
with open(path, "r") as f:
    lines = f.readlines()

# Extract algorithm from around line 74 (0-indexed: 73)
algorithm = None
for i in range(max(0, 73 - 5), min(len(lines), 73 + 5)):
    line = lines[i].strip()
    if "algorithm" in line.lower() and ("=" in line or ":" in line):
        match = re.search(r'["\'](\w+)["\']', line)
        if match:
            algorithm = match.group(1)
            break

# Fallback: search the whole file for a default algorithm declaration
if not algorithm:
    for i, line in enumerate(lines):
        lower = line.lower()
        if "default" in lower and "algorithm" in lower:
            match = re.search(r'["\'](\w+)["\']', line)
            if match:
                algorithm = match.group(1)
                break

# Extract shard prefix length from around line 125 (0-indexed: 124)
shard_prefix = None
for i in range(max(0, 124 - 5), min(len(lines), 124 + 5)):
    line = lines[i].strip()
    if "shard" in line.lower() and ("prefix" in line.lower() or "length" in line.lower() or "len" in line.lower()):
        match = re.search(r'(\d+)', line)
        if match:
            shard_prefix = int(match.group(1))
            break

# Fallback: search the whole file
if not shard_prefix:
    for i, line in enumerate(lines):
        lower = line.lower()
        if "shard" in lower and ("prefix" in lower or "length" in lower):
            match = re.search(r'(\d+)', line)
            if match:
                shard_prefix = int(match.group(1))
                break

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```