I need to be careful here. The instructions say I cannot read files, but the grader will execute my reply inside the directory with the pinned files. The task is to report Duval's default hash algorithm and shard prefix length by parsing the seeded source file `src/hash.ts`.

Let me think about this. The artifact I produce will be executed by the grader in the directory containing the pinned files. So I need to write a Python script that:
1. Reads `src/hash.ts`
2. Extracts the default hash algorithm from line 74
3. Extracts the shard prefix from line 125 (the second argument of the first `slice(...)` call)

Let me write a complete Python script that does this properly.

```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
# Extract the algorithm string - it's likely in a const or type definition
# Look for something like: const ALGORITHM = "sha256" or type = "sha256"
algorithm_match = re.search(r'["\']([a-zA-Z0-9]+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else algorithm_line

# Line 125 (1-based) defines the shard function with a slice call
shard_line = lines[124].strip()
# Find the first slice(...) call and get the second argument
slice_match = re.search(r'slice\((\d+),\s*(\d+)\)', shard_line)
shard_prefix = int(slice_match.group(2)) if slice_match else 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```

Wait, I need to be more careful about extracting the algorithm. Let me think about what line 74 might contain. It's a TypeScript file, and it likely has something like:

```typescript
const DEFAULT_HASH_ALGORITHM = "sha256";
```

or

```typescript
export const algorithm = "sha256";
```

The regex I have should handle the string extraction. Let me also consider that the algorithm might be a more complex string. Let me refine.

Actually, let me think about what the actual content might be. The file is `src/hash.ts` and it's about hashing in something called "Duval". The default hash algorithm is likely "sha256" or "sha3-256" or similar.

For the shard prefix, the instruction says: "on the line that defines the shard function, read the SECOND argument of the first slice(...) call, so slice(0, 2) gives 2". This is on line 125.

Let me write a more robust script:

```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
# Extract the first quoted string which should be the algorithm name
algorithm_match = re.search(r'["\']([a-zA-Z0-9\-]+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else ""

# Line 125 (1-based) defines the shard function with a slice call
shard_line = lines[124].strip()
# Find the first slice(...) call and get the second argument
slice_match = re.search(r'slice\([^,]+,\s*([^)]+)\)', shard_line)
shard_prefix = int(slice_match.group(1).strip()) if slice_match else 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```

Hmm, but I'm not sure if the algorithm line will have a simple quoted string. Let me think more carefully.

Actually, I realize I should just write the script and let it parse the actual file. The grader will run it. Let me make the regex robust enough to handle various formats.

Let me also consider that the algorithm might be defined like:
```typescript
const algorithm = "sha256" as const;
```

or

```typescript
export const HASH_ALGORITHM = "sha256";
```

The key is to extract the string value. My regex `["\']([a-zA-Z0-9\-]+)["\']` should work for most cases.

For the shard prefix, the slice call pattern `slice(0, 2)` - I need to extract the second argument. My regex `slice\([^,]+,\s*([^)]+)\)` should work.

Let me finalize the script:

```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
# Extract the first quoted string which should be the algorithm name
algorithm_match = re.search(r'["\']([a-zA-Z0-9\-]+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else ""

# Line 125 (1-based) defines the shard function with a slice call
shard_line = lines[124].strip()
# Find the first slice(...) call and get the second argument
slice_match = re.search(r'slice\([^,]+,\s*([^)]+)\)', shard_line)
shard_prefix = int(slice_match.group(1).strip()) if slice_match else 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```

This looks good. Let me verify the line indexing:
- Line 74 (1-based) = index 73 (0-based) ✓
- Line 125 (1-based) = index 124 (0-based) ✓

The print contract says: print exactly 2 lines in key=value form: `algorithm=<the algorithm string>` and `shard_prefix=<number>`.

My output format matches: `algorithm=sha256` and `shard_prefix=2`.

Let me make sure there's nothing else printed. The script only has two print statements, so that's good.

One concern: what if the algorithm string contains uppercase or special characters? The regex `[a-zA-Z0-9\-]+` should handle most hash algorithm names like "sha256", "sha3-256", "blake3", etc.

Another concern: what if there are multiple slice calls on the line? The regex `re.search` finds the first match, which is what we want (the first slice(...) call).

I think this script is solid. Let me present it.

```python
import re

src_path = "src/hash.ts"
with open(src_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Line 74 (1-based) holds the default hash algorithm.
algorithm_line = lines[73].strip()
algorithm_match = re.search(r'["\']([a-zA-Z0-9\-]+)["\']', algorithm_line)
algorithm = algorithm_match.group(1) if algorithm_match else ""

# Line 125 (1-based) defines the shard function with a slice call.
shard_line = lines[124].strip()
slice_match = re.search(r'slice\([^,]+,\s*([^)]+)\)', shard_line)
shard_prefix = int(slice_match.group(1).strip()) if slice_match else 0

print(f"algorithm={algorithm}")
print(f"shard_prefix={shard_prefix}")
```