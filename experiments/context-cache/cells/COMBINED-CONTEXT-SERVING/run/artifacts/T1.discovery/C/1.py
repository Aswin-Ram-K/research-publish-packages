```python
import re

src_path = "src/hash.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Line 74 (0-indexed 73) should contain the default hash algorithm.
algo_line = lines[73].strip()
# Extract the algorithm string, e.g., from `const ALGO = "sha256"` or similar.
m = re.search(r'["\']([a-zA-Z0-9_\-]+)["\']', algo_line)
algorithm = m.group(1) if m else None

# Line 125 (0-indexed 124) should contain the shard function with a slice call.
shard_line = lines[124].strip()
# Find the first slice(...) call and take the second argument.
m2 = re.search(r'slice\(\s*0\s*,\s*(\d+)', shard_line)
shard_prefix = int(m2.group(1)) if m2 else None

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```