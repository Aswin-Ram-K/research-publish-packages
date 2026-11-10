```python
import re

src_path = "src/hash.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Line 74 (1-indexed) -> index 73: default hash algorithm.
algo_line = lines[73].strip()
# Extract the algorithm string, e.g., from something like: const ALGO = "sha256";
m = re.search(r'["\']([a-zA-Z0-9+/=]+)["\']', algo_line)
algorithm = m.group(1) if m else algo_line

# Line 125 (1-indexed) -> index 124: shard function with first slice(...) call.
shard_line = lines[124].strip()
# Find first slice(...) call and take the second argument.
slice_match = re.search(r'slice\([^,]+,(\d+)\)', shard_line)
shard_prefix = int(slice_match.group(1)) if slice_match else None

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```