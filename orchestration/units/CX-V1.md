# V1 — verifier: context module (U1) — Batch 2

**Role:** independent verifier; author of none of the units under test.
**Bound:** 30 tool calls · **used 28** · no live model calls, no git, no installs.
**Write paths:** `orchestration/handoffs/V1.json`, `orchestration/units/V1.md`.
One source edit (`render.py`) for the red→green check, restored byte-exactly (sha256 proven).

> Path collision: this path previously held the **batch-1** V1 verdict (2026-10-08, kg/graphify).
> That record survives in [`orchestration/VERDICTS.md:10`](../VERDICTS.md) and its section at `:42`, but
> `VERDICTS.md:45`'s link to `units/V1.md` now lands here — re-file if a stable name is wanted.

## Verdict: **pass**

U1's seven claims reproduce. One naming overstatement in the prefix test, two doc/robustness nits, no functional defect.

## Checks

| # | Check | Result |
|---|---|---|
| 1 | Four test files re-run | **36 passed in 0.06s** — matches U1; no vacuous test |
| 2 | Red→green | 2 tests failed as expected; sha256 before == after |
| 3 | No `StateNode` mutator (ast-grep + grep) | **0 matches** in `src/resextract/context/`; query validated elsewhere |
| 4 | Adversarial probes P1–P4 | all answered; P3 refutes full byte-prefix, P4 shows no `cached<=prompt` clamp |
| 5 | `U1.json` shape | valid JSON, exactly the 7 contracted keys |

### 1. Test re-run

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_context_nodes.py tests/test_context_render.py \
  tests/test_context_meter.py tests/test_context_runner.py -q
....................................                                     [100%]
36 passed in 0.06s
```

36 named tests (7 of them the parametrised `normalise_cache` rows). Every assertion compares independently
constructed nodes/rows — nothing asserts on a constant it just defined except the one case listed under
"overstated" (`test_tax_error_is_zero_on_the_64_token_grid`, whose fixture sets `uncached = prompt % 64`).

### 2. Red→green (mandatory)

Guard: `src/resextract/context/render.py` — `NAIVE_MUTABLE` made to delegate to `_pointer_messages(...)`, i.e.
identical to `POINTER`:

```
tests/test_context_render.py::test_naive_mutable_rewrites_the_preamble FAILED   (test_context_render.py:81)
tests/test_context_runner.py::test_mutable_policy_prefix_digest_changes_every_turn FAILED (test_context_runner.py:205)
2 failed in 0.04s
```

- before sha256 `162d6379012ce3da7feb5237ff4dbcbf0f44fc4412f99579e26870cefbbffc3d`
- after  sha256 **identical**, `cmp` clean against the `/tmp` backup
- restored run: `36 passed in 0.06s`

So the red→green pair really does distinguish the two policies: the diff that makes them equal is caught by
`test_naive_mutable_rewrites_the_preamble` **and** by the runner's prefix-digest test.

### 3. No mutator on `StateNode`

| Query | Hits in `src/resextract/context/` |
|---|---|
| ast-grep `$SELF.$FIELD = $VALUE` (py) | **0** |
| ast-grep `object.__setattr__($$$ARGS)` (py) | **0** |
| `grep -E 'def (edit|set_|_set|mutate|update)\(|__setattr__|__delattr__|frozen'` | only `nodes.py:42 @dataclass(frozen=True)` |

The `$SELF.$FIELD = $VALUE` pattern is not a dead query: over `src` it returns 8 matches
(`journal.py:125-126`, `cli.py:351/367`, `web/search.py:217-220`). Identity is the sha256 of
`{kind, text, parent, meta}` (`nodes.py:73-80`); the only mutation possible is constructing a new node, and
`frozen=True` backs the test's `FrozenInstanceError` assertion.

### 4. Probes

- **P1 — kind collision:** `("same text","delta")` → `651cb8d290…`, `("same text","invariant")` → `6cc61bfff8…`.
  No collision, and none should exist: `kind` is part of state identity.
- **P2 — unicode:** lone surrogate `"\ud800"` → `UnicodeEncodeError` (loud, no coercion). NFC vs NFD `café`
  hash **differently** (7 vs 8 canonical bytes) — no normalisation, so no silent collision. 200k-char CJK OK.
- **P3 — prefix:** `render_bytes(POINTER)` turn2 → turn3 is **not** a byte prefix (`b3.startswith(b2)` False,
  327/327 bytes). `messages[0]` and `messages[1]` are identical; `messages[2]` is replaced. The cacheable head
  is stable — the *whole render* is not prefix-stable, and the test does not claim otherwise once read closely.
- **P4 — cached > prompt:** `normalise_cache({"prompt_tokens":5,"prompt_tokens_details":{"cached_tokens":999}})`
  → `(5, 999)`, i.e. **no clamp to prompt** (`max(0, …)` only kills negatives, `meter.py:87`). `runner.py:220`
  does `uncached = max(0, prompt - cached)`, so recorded rows stay sane; the meter API alone can return an
  impossible pair.

### 5. `U1.json`

Valid JSON; keys exactly `{unit, status, artifacts, evidence, blocker, next_unit_hint, write_paths}`.

## Overstated / not reproduced / unverified

- **Overstated** — `test_pointer_prefix_is_byte_stable` (`tests/test_context_render.py:48-59`) proves
  message-0 stability (`first_bytes()` = `b"[" + canonical_bytes(messages[0])`); `prefix in b_turn_3` is
  redundant given `startswith`. The turn-N render is *not* a byte prefix of turn-N+1.
- **Overstated** — `render.py:14-17` calls `NAIVE_APPEND` "prefix-stable"; its last message gains/loses the
  `[volatile]` block each turn (`n3[:len(n2)] != n2`). Only the head up to message N−1 is stable.
- **Tautological-ish** — `test_tax_error_is_zero_on_the_64_token_grid` builds rows to satisfy the invariant it
  then asserts; the off-by-40 case is the discriminating one.
- **Unverified** — live SGLang usage shape; U1's full-suite counts; `pyproject` packaging of
  `resextract.context`.

## Next

Run the live gate (inject `functools.partial(ChatClient().chat, max_tokens=N)` as `runner.send`, build cells
over the four `RenderPolicy`s, `meter.to_jsonl`, `analyze.main`). First tighten the prefix test and either clamp
`cached` to `prompt` in `normalise_cache` or document the `runner.py:220` clamp.
