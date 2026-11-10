```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\']([a-zA-Z0-9_\-]+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else None

# Find the shard function definition line within the pinned range (L73-L126)
shard_prefix = None
for idx in range(72, min(126, len(lines))):
    line = lines[idx].strip()
    if "slice(" in line and ("function" in line or "shard" in line.lower() or re.search(r'(const|let|var)\s+\w*\s*=\s*(async\s+)?\s*\(?.*?\)?.*=>', line) or re.search(r'\bshard\b', line)):
        # Find first slice(...) call
        slice_match = re.search(r'slice\((\d+),\s*(\d+)\)', line)
        if slice_match:
            shard_prefix = int(slice_match.group(2))
            break

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```