# U-SPCC-46 — the fetch arm refuses a tools-off launch

## Defect

E1 ran `bounded-context-fetch` with `--tools` absent (`tools_mode=off`). The fetch service
at the `arm == arm_cd.ARM_D` block of `experiments/ptr-engine/longrun/run_longrun.py` never
ran, so 43 of 48 checkpoint turns stranded as interim `fetch_followup` rows with
`protocol_violation=answer_wrapped_tool_call` and `send_index 0` on all 100 rows. The cell
exited 0 and reported 0 failed turns: a degenerate arm that looked like a real result.

## Change

`experiments/ptr-engine/longrun/run_longrun.py`:

- `EXIT_ARM_REQUIRES_TOOLS = 2` — the same code the runner already uses for a malformed
  launch (`--fetch-rounds-per-arm` non-positive, unknown arm, missing selector).
- `arm_requires_tools(arm)` — true only for `arm_cd.ARM_D`. `masking-no-fetch` is DEFINED
  by having no tool channel (`run_cell` clears `cfg.tools` for it) and `spcc` never
  fetches, so neither is gated.
- `refuse_arm_without_tools(cfg, arm)` — prints `ARM REFUSED (exit 2): arm
  'bounded-context-fetch' is the fetch arm and requires --tools (e.g. --tools read_file);
  --tools is absent, so tools_mode='off' and the fetch service would never run. No row was
  written and no request was sent.` and returns 2.
- `run_cell` calls it FIRST, before the `ARM_C` copy that clears `cfg.tools`, so the guard
  reads the launch's own `--tools`.
- `main()` calls it for EVERY requested arm before the first cell runs, so a multi-arm
  launch cannot spend the earlier arms' requests and then discover the degenerate one.

No fetch semantics changed: the D arm's fetch path, its budget, its row shape and its
`--tools` handling are untouched. Only the launch that cannot fire its treatment is
refused.

## Evidence

Red (unpatched `run_longrun.py` at `e4692f8`):

```
AssertionError: 2 != 0 : a refused launch must send no request, sent 2
```

Green (patched):

```
18 passed in 0.34s
```

`python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Tests

`experiments/ptr-engine/longrun/tests/test_arm_d_requires_tools.py` — offline, counting
fake `send_chat`, `socket.socket` denied:

- `bounded-context-fetch` + tools off → exit 2, 0 sends, 0 rows, refusal names `--tools`;
- `bounded-context-fetch` + tools on → exit 0, sends > 0, rows > 0, arm id on every row;
- `masking-no-fetch` + tools off → exit 0, sends > 0, rows > 0;
- `spcc` + tools off → exit 0, sends > 0, rows > 0;
- `main()` refuses a tools-off fetch arm and a `spcc,bounded-context-fetch` launch before
  any row file is created.
