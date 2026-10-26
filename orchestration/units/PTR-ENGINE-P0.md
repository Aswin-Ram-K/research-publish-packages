# PTR-ENGINE-P0 — build the makeshift pointer engine

**Unit type:** BUILD (no live model calls, no network, no servers).
**Bound:** 60 tool calls.
**Status at time of writing:** done.

## Purpose

The inference side measured what pointer-style lazy loading costs (crossover at
~30,000 chars, cold cache only) but had no engine that *compiles* a pointer index at
turn end and resolves it on demand. This unit builds that engine plus the adoptable
contract, so a later project can implement the same seam instead of re-deriving it.

## Model implemented (read-only prior art)

Duval `src/reference.ts` and `src/state.ts`: `ResourceRef` = content identity
`{scheme, locator, hash, pin}`; `Reference` = position
`{kind, id, pointer?, revision?, projection?}`; resolution is one-way
(`Reference -> ResourceRef`); the text form is a serialization, not the primitive.

## Write paths (declared)

- `experiments/ptr-engine/` (SPEC.md, ptr_engine/, tests/, examples/)
- `orchestration/units/PTR-ENGINE-P0.md` (this card)
- `orchestration/handoffs/PTR-ENGINE-P0.json`

Read-only, untouched: `src/**`, `papers/**`, `release/**`,
`experiments/agentic-lazy/**`, `/home/zer0null/Duval`.

## Deliverables

| path | what |
|---|---|
| `SPEC.md` | the contract: envelope, one-way rule, lifecycle, warmpool layout, four annotations, harness surface (6 items, with what a plain chat harness has and does not), stated limits |
| `ptr_engine/errors.py` | 20 named `PtrError` subclasses, each with a stable `PTR_*` code |
| `ptr_engine/reference.py` | `Reference`, `ResourceRef`, strict `parse()`, `format()`, `REF_KINDS` |
| `ptr_engine/store.py` | `BodyStore`: sha256 key, `<root>/<aa>/<sha256><ext>`, dedupe, atomic put, hash-verified get, warmpool-inside-repo refusal |
| `ptr_engine/compile.py` | `compile_turn(...) -> TurnIndex`, deterministic index bytes, `Entry`, `TurnIndex` |
| `ptr_engine/resolve.py` | `Scope`, `resolve(ref, scope, ledger) -> ResourceRef`, one ledger row per request |
| `ptr_engine/annotate.py` | `depth`, `scope`, `append_cost`, `ledger_id` |
| `ptr_engine/ledger.py` | append-only JSONL, refusal rows, null-not-zero token fields |
| `ptr_engine/adapter.py` | `build_prompt(index, resolved_bodies, ledger=None)`, `fetch_tool_spec()` |
| `tests/` | 95 tests, all green, one file per invariant |
| `examples/worked_example.py` | offline 12-item / 30,000-char worked example printing r |

## Acceptance

- `python3 -m pytest tests -q` → `95 passed`.
- `python3 examples/worked_example.py` → 12 items, 30,000 body bytes, 447-byte index,
  **r = 67.1×**; zero-resolution prompt 472 bytes; two resolves 2,496 B and 25 B.
- Determinism: two processes, two different warmpool roots → identical index sha256
  (`tests/test_determinism.py`).
- Red check: mutating `store.get`'s hash comparison and `resolve`'s scope comparison
  turns 4 tests red; restoring returns 95 green.
