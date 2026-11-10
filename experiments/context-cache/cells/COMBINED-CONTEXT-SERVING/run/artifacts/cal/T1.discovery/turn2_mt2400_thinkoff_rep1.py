I'll examine the pinned hash.ts source to confirm the algorithm declaration in the Blake2b512Hasher class.

```typescript
// Reading /home/zer0null/Duval/src/hash.ts lines 73-126
import * as fs from 'fs';
const content = fs.readFileSync('/home/zer0null/Duval/src/hash.ts', 'utf-8');
const lines = content.split('\n');
const start = 72; // 0-indexed for line 73
const end = 125; // 0-indexed for line 126
const snippet = lines.slice(start, end + 1).join('\n');
console.log(snippet);
```