# Analysis pipeline check

Snapshot: /tmp/ccs-snapshot.jsonl, 80 rows (main run partial).

analyse.py ran to exit 0 on snapshot; output /tmp/analysis-out.json:
A: calls=32 verified=12 combined_proxy_tokens=30100
B: calls=24 verified=14 combined_proxy_tokens=33938
C: calls=24 verified=12 combined_proxy_tokens=50628

Cost paths (uncaught_tokens):
1. reported cached_tokens: row 1a27f25a-f0cf-4b81-adc9-ee7d239b0944 (B) prompt=589 cached=576 derived=13 -> uncached=13.
2. no cached reported (null): row ad719086-c2ff-4e3b-a292-2185ff0b9d06 (A) prompt=560 cached=None -> uncached=560.
3. derived carries subtraction: row 311ef1f4-db6d-4a3a-a837-5d0687578a07 (A) prompt=589 cached=576 derived=13 -> uncached=13 (derived branch).

verified() paths:
- inline verified_success: row 311ef1f4... -> True.
- graded_path only (inline removed): same row -> reads graded file -> True (flips to False when graded file tampered).

Gate shapes:
- baseline zero verified -> undefined-no-verified-success.
- candidate lower verified rate -> quality_ok=False, promote=False.
- equal quality, <10% saving -> quality_ok=True, cost_ok=False, promote=False.
- equal quality, >=10% saving -> quality_ok=True, cost_ok=True, promote=True (B).

analyser needed no fix.
