# U-SPCC-35 — E1 cell refused at the precondition: `E1` is not a claim id

## Outcome

**Blocked. Zero requests spent. No rows file written. No cell run.**

The unit's precondition is that `resolve_claim("E1")` returns a record with
`comparison_eligible: True` and `claim: "E1"`. It does not. It raises
`ClaimRefusal`, so the cell was never launched.

## The refusal, verbatim

```
$ TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -c \
    "import sys; sys.path.insert(0,'experiments/ptr-engine/longrun'); import claim_mode; \
     print(claim_mode.resolve_claim('E1'))"

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/zer0null/research extractor/experiments/ptr-engine/longrun/claim_mode.py", line 222, in resolve_claim
    raise ClaimRefusal(flag_value)
claim_mode.ClaimRefusal: claim REFUSED: --hypothesis='E1' is not a declaration this run may make. The three accepted forms are (1) `--hypothesis smoke` and (2) `--hypothesis plumbing` -- both declare claim=none, so the cell is plumbing and its rows are NOT comparison_eligible -- and (3) `--hypothesis H1`, `--hypothesis H2` or `--hypothesis H3`, the PARM-1 claim the cell will make. Silence is not a claim: an absent or empty --hypothesis is refused here, and so is an explicit `none` -- a run may start without a hypothesis only by declaring that it makes no claim.
```

## Why

`experiments/ptr-engine/longrun/claim_mode.py:95` is the whole namespace:

```python
CLAIM_IDS = ("H1", "H2", "H3")
```

`resolve_claim` (`claim_mode.py:206-222`) accepts `smoke`/`plumbing` (→
`claim="none"`, `comparison_eligible=False`) and the three `CLAIM_IDS` (→
`comparison_eligible=True`). `E1` is in neither set, so it falls through to
`raise ClaimRefusal(flag_value)` at `:222`.

The claim-namespace unit that is to add `E1` has not landed. Evidence:

- `git log --oneline -- experiments/ptr-engine/longrun/claim_mode.py` → a single
  commit, `9fadcc9 wip(ptr-engine): preserve context x serving instrument,
  fixtures and measurements`. No commit adds `E1`.
- `grep -n "E1" experiments/ptr-engine/longrun/tests/test_claim_mode.py` → no
  matches; the test file still enumerates only `smoke`, `plumbing`, `H1`, `H3`,
  `None`, `""`, `"none"`, `"H4"` as its accepted/refused cases
  (`claim_mode.py:427`).
- `git --no-optional-locks status --porcelain` in the checkout shows no
  modification to `claim_mode.py`, so the on-disk resolver is the committed one.

## What was deliberately not done

The assignment forbids substituting `smoke`, `plumbing`, `H1`, `H2` or `H3` to
get past the precondition, and forbids raising the budget cap. Neither was done.
`H1`/`H2`/`H3` are the PARM-1 claims; stamping an SPCC cell with one of them
would write rows into a comparison under a claim the cell does not make, which
is exactly the failure `claim_mode.py:14-16` warns about.

## Consequence for the unit's acceptance criteria

| # | Criterion | State |
|---|---|---|
| 1 | 100 turns, 0 failed, 0 truncated, 100 rows | not attempted — no cell |
| 2 | three-arm table from the repo scorer | not attempted — no spcc rows |
| 3 | per-checkpoint spcc breakdown | not attempted |
| 4 | spcc billing line | not attempted |
| 5 | verdict against E1's preregistered prediction | not adjudicable — no data |
| 6 | FINDINGS-LEDGER row | not written — a ledger row without a measurement would be a fabricated result |
| 7 | `python3 tools/doc_check.py` exits 0 | run, see handoff |
| 8 | commit + push | this card and the handoff |

## Unblocking

Land `E1` in `claim_mode.CLAIM_IDS` (and its `resolve_claim` docstring, its
`_REFUSAL` text, and `tests/test_claim_mode.py`), then re-issue this unit
unchanged. The cell command, fixture, seed, temperature and budget cap in the
assignment are all still valid; nothing about them was found to be wrong.
