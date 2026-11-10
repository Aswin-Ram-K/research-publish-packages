```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\'](\w+)["\']', algorithm_line)
if not algorithm_match:
    raise SystemExit("Could not derive algorithm from line 74")
algorithm = algorithm_match.group(1)

# Line 125 (1-based) defines the shard function; take the second argument
# of the first slice(...) call on that line.
shard_line = lines[124].strip()
slice_match = re.search(r'slice\(\s*\d+\s*,\s*(\d+)\s*\)', shard_line)
if not slice_match:
    raise SystemExit("Could not derive shard prefix from line 125")
shard_prefix = int(slice_match.group(1))

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```