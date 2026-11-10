

```python
import re

with open("src/hash.ts", "r") as f:
    lines = f.readlines()

# Line 74 (0-indexed 73) contains the algorithm
algorithm_line = lines[73].strip()
# Extract the algorithm string - look for something like 'sha256' or similar
algo_match = re.search(r"(sha[234]?|sha-?256|keccak|blake|md5|ripemd|whirlpool|xxhash|cityhash|fnv|crc32)", algorithm_line, re.IGNORECASE)
if algo_match:
    algorithm = algo_match.group(1).lower()
    # Normalize common variants
    if algorithm in ("sha2", "sha-256"):
        algorithm = "sha256"
    elif algorithm in ("sha3", "sha-3"):
        algorithm = "sha3"
else:
    # Fallback: take the whole line's meaningful content
    algorithm = algorithm_line.split("=")[-1].strip().strip(";").strip("'\"")

# Line 125 (0-indexed 124) contains the shard prefix
prefix_line = lines[124].strip()
# Look for a number representing hex characters
num_match = re.search(r"(\d+)", prefix_line)
if num_match:
    shard_prefix = int(num_match.group(1))
else:
    # Try to find a hex literal like 0x... and count
    hex_match = re.search(r"0x([0-9a-fA-F]+)", prefix_line)
    if hex_match:
        shard_prefix = len(hex_match.group(1))
    else:
        shard_prefix = 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```