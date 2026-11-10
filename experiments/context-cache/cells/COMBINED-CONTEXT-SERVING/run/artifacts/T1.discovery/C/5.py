```python
import re

src_path = "src/hash.ts"
with open(src_path, "r") as f:
    lines = f.readlines()

# Line 74 (1-indexed) -> index 73: default hash algorithm.
algo_line = lines[73].strip()
# Extract the algorithm string, e.g., from some declaration like `const ALGO = "sha256"` or similar.
# We look for a quoted string that represents a hash algorithm.
algo_match = re.search(r'["\']([a-zA-Z0-9]+)["\']', algo_line)
algorithm = algo_match.group(1) if algo_match else algo_line

# Line 125 (1-indexed) -> index 124: shard function definition with slice call.
shard_line = lines[124].strip()
# Find the first slice(...) call and extract the SECOND argument.
slice_match = re.search(r'slice\(\s*[^,]*,\s*([0-9]+)', shard_line)
shard_prefix = int(slice_match.group(1)) if slice_match else None

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```