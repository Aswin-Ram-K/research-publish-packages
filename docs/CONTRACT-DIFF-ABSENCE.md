# ABSENT is a result: how `launch_contract_diff.py` reports a missing field

**Owner card:** `LAUNCH-CONTRACT-ABSENT` (962c8fcb). **Tool:** `experiments/ptr-engine/tools/launch_contract_diff.py`.
**Tests:** `experiments/ptr-engine/tests/test_launch_contract_diff_absent.py`.

## The defect this closes

`--check` died with

```
File ".../launch_contract_diff.py", line 653, in checks
    params["price"]["components"]["tranche"]
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'components'
```

The crash was **not** in the probe runner (which already caught exceptions) but in `checks()`,
while *building* the row table: a computed probe indexed the params record directly. One
absent key therefore took down the whole table, and a successor reading exit 1 could not
tell "a number disagrees" (the tool's whole job) from "the tool never ran".

## The rule now installed

1. **One accessor.** Every JSON field a row depends on is resolved through
   `resolve_field(obj, keys) -> (present, value, path)`. Nothing indexes a raw record.
   A missing key is data, never an exception.
2. **Absence is printed with its location.** A row reports `ABSENT price.components.tranche
   in experiments/ptr-engine/measure/GRID-PARAMS.json` — the dotted path a successor must
   add, and the file that should carry it. The row also carries `absent: ["price.components…"]`
   and the document carries `summary.absent`.
3. **Absence is not agreement.** `--check` exits **non-zero** when any row is `ABSENT`,
   alongside `DISAGREES`/`UNRESOLVED`. The scoped `--pin-generation N` path is unchanged:
   a moved tree is still `MOVED` → **13**, and a real disagreement still exits **1**.
4. **Disagreement outranks absence.** The `DISAGREES` test runs *before* the `ABSENT` test,
   so adding absence handling can never mask two competing values. A wrong total on a
   components-less record still names both numbers.
5. **Narrow backstop only.** `run_probe`'s last-resort catch is restricted to
   `(OSError, ValueError, TypeError, IndexError, KeyError)` for a malformed record
   (unparseable JSON, wrong shape). Absence never reaches it.

## The price arithmetic is restored in the REPORT, not in the params file

`GRID-PARAMS.json` (schema `consonance.grid-params/3`) records `price.total = 1056`,
`price.arithmetic`, `price.factor = 1.374532` and `price.factor_path`, but **no
`price.components`** — the breakdown that let 792/660 and 1,016/1,056 drift for rounds is
gone, leaving a bare total with no arithmetic behind it. The checker therefore derives
what the total must reconcile against and prints it *beside* the recorded fact:

```
price: 1056 recorded (price.total)
price: components ABSENT price.components
derivation: 768 turns x 1.374532 = 1055.640576 -> 1056
factor provenance: experiments/ptr-engine/measure/GRID-SHAPE.json :: factor.tools_off_historical = 1.374532
like-for-like: rev 2's 1,016 = 964 tranche + 48 canary + 4 warm-ups. …
```

`price_derivation()` returns status `JUSTIFIED-BY-COMPONENTS` (breakdown present),
`JUSTIFIED-BY-DERIVATION` (derivation reconciles), or `price_unjustified` (it does not),
and sets `flag: "price_unjustified"`. The card's scope forbids editing
`measure/GRID-PARAMS.json`; the recommendation is recorded instead.

**Recommendation (owner: `GRID-PARAMS-16CELL`'s successor):** restore
`price.components = {tranche, canary, warm_ups}` — and, because rev 3 prices 768 turns of a
tools-on shape at the tools-off factor, record the like-for-like figure too — so the total
stops being a bare number. Until that card lands, this page's report is the only place the
1,056 is shown with its arithmetic.

## Verification

```
/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_launch_contract_diff_absent.py -q
/usr/bin/python3 experiments/ptr-engine/tools/launch_contract_diff.py --check          # 1 today, ABSENT rows named
/usr/bin/python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --pin-generation 4  # 13, MOVED
```
