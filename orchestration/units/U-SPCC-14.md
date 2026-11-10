# U-SPCC-14 — layers.py module header states the L0+L1 invariant

## Status

DONE.

## Defect

`experiments/ptr-engine/ptr_engine/layers.py` lines 1–5 said the module builds a
"byte-stable prefix (L0+L1+L2)" *and* an "append-only journal (L2)" — mutually
contradictory. An append-only L2 inside the hashed prefix changes on every
append, so the hash could never be stable. The code was already correct
(`prefix_sha256` = `L0+L1`; `L2` is the tail); only the header was wrong, and a
future reader could have "fixed" the hash to cover L2 — the original defect the
arm exists to avoid.

## Change

Header only, lines 1–11 of `experiments/ptr-engine/ptr_engine/layers.py`:

- prefix is `L0+L1`, rendered from bytes stable between compactions;
- `L2` is the append-only journal that grows after it;
- `prefix_sha256` covers `L0+L1` only, because hashing the growing tail would
  report drift on every legitimate append and could not distinguish an append
  from a destructive rewrite;
- compaction at the epoch boundary is the only permitted prefix break (it
  rewrites `L1`);
- rationale delegated to `compile_prompt`'s docstring and
  `research-seed-concepts/PROMPT-ENGINE-V1.md` (lines 48-56).

No code, no other comments changed. Docstring grew 6 → 11 lines (+8/−3), so
everything below shifted down by 5 lines; that is the only structural effect.

## Evidence

```
$ sed -n '1,20p' experiments/ptr-engine/ptr_engine/layers.py
"""Stable-prefix context compiler.

Builds a byte-stable prefix ``L0+L1`` from bytes that do not change between
compactions, plus an append-only journal ``L2`` that grows after it.

``prefix_sha256`` covers ``L0+L1`` only: hashing the growing ``L2`` tail would
report drift on every legitimate append and could not distinguish an append
from a destructive rewrite.  Compaction alone -- at the epoch boundary -- may
break the prefix; it rewrites ``L1``.  Rationale: ``compile_prompt`` below and
``research-seed-concepts/PROMPT-ENGINE-V1.md`` (lines 48-56).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import PtrError

$ git diff --stat -- experiments/ptr-engine/ptr_engine/layers.py
 experiments/ptr-engine/ptr_engine/layers.py | 11 ++++++++---
 1 file changed, 8 insertions(+), 3 deletions(-)

$ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_spcc_arm.py -q
4 passed in 0.32s

$ sha256sum experiments/ptr-engine/ptr_engine/layers.py
359ca310a07477bee2aecbb7e5bf9fa732dbfed8e3f0dc734ec47cec5d93be86  experiments/ptr-engine/ptr_engine/layers.py
```

Expected: the file hash differs from the pinned
`13b608e5d036c6d27ee4aa5b6675f550f262830e1b1602218da73f6cb229e606` — that pin
was of the pre-edit bytes and is superseded by this header rewrite.
