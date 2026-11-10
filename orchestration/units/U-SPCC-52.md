# U-SPCC-52 — the fetch parser accepts the tool names the run declared

**Status:** DONE. Offline only: 0 endpoint requests, 0 model calls.

## The defect

`run_longrun.py:3677` read the fetch arm's reply through
`arm_cd.parse_fetch_calls_from_response` → `ptr_engine/fetch_tool.py:82 parse_fetch_calls`,
which kept only calls whose `function.name == 'fetch'` (`fetch_tool.py:96-99`).

The wire schema declares **`read_file`** (`TOOL_NAMES = ("read_file",)` at
`run_longrun.py:468`; `tools_mode: on:read_file` and `tools_schema_sent=true` on every
tools-on row). So a `read_file` call was filtered out, `_calls` came back empty, no
follow-up was bought, the empty content parsed as `no_answer_line`, and the checkpoint
scored `unparsed`.

Measured on `measure/rows-e1-tools-2026-11-10.jsonl`: 10 checkpoints stranded at turns
**9, 13, 25, 51, 56, 58, 60, 67, 74, 76**; only turns **21, 73, 84** were serviced.
`first_token_kind=tool_call` on all ten proves the server signalled the call and
`client.collect_stream` assembled it — the loss was downstream of the client.

`U-SPCC-49` (`4c6c8a0`) preserved the dropped call on the row and labelled it
`protocol_violation='tool_call_unserviced'`. That is a diagnostic, not a fix: the ten
still scored `unparsed`.

## The fix

The parser now takes the tool names the run DECLARED, so the parser and the wire schema
cannot drift apart again.

| file | change |
|---|---|
| `ptr_engine/fetch_tool.py` | `parse_fetch_calls(assistant_message, tool_names=None)`; `DEFAULT_FETCH_TOOL_NAMES = ("fetch", "read_file")`; `_accepted_tool_names()`; the name filter is `name not in accepted` |
| `longrun/arm_cd.py` | `parse_fetch_calls_from_response(resp, tool_names=None)` forwards the set |
| `longrun/run_longrun.py` | new `fetch_call_tool_names(cfg)` = `client.tool_names(cfg)` + `fetch`; the call site at `:3699` passes it |

A `read_file` call is serviced exactly as a `fetch` call is: same `ref`/`range`
extraction, same `tool_call_id` requirement, same budget accounting. Its `path` is the
only ref-bearing field the wire schema gives it, so `path` → `ref`. Its
`start_line`/`end_line` are **line numbers** and are deliberately NOT mapped onto
`range`, which stays byte offsets into the stored body — the pointer table has no line
index, so passing them as bytes would slice the wrong text.

`fetch` still works: the ARM_D prompt teaches `fetch(ref=...)`, and
`fetch_call_tool_names` always includes it.

An UNDECLARED name is still rejected, and the rejection is visible: the call is preserved
verbatim on the row and labelled `protocol_violation='tool_call_unserviced'` by
`unserviced_structured_calls` (`run_longrun.py:1030`).

Unchanged: the answer contract, the scoring, the fetch budget, the per-turn cap.

## Red → green

Red (pre-fix `fetch_tool.py` + `arm_cd.py`, call site reverted to
`parse_fetch_calls_from_response(resp)`):

```
FAILED test_fetch_call_names.py::test_parser_accepts_the_declared_set
FAILED test_fetch_call_names.py::test_read_file_call_is_serviced
  AssertionError: 'tool_call_unserviced' is not None : a declared tool name must not be
  labelled unserviced: protocol_violation='tool_call_unserviced'
  tool_calls=[{'id': 'call_c1985245fd5c457d83111c74', 'name': 'read_file', ...}]
SUBFAILED(name='read_file') test_declared_name_does_not_raise_unserviced_label
3 failed, 3 passed, 1 subtests passed
```

Green:

```
24 passed, 2 subtests passed in 0.56s
```

over `test_fetch_call_names.py test_tool_call_capture.py test_fetch_arm_row_persistence.py
test_arm_cd_wiring.py test_fetch_rounds_accounting.py`.

`python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Test changes

`tests/test_fetch_call_names.py` (new) proves the four cases: a `read_file` call is
parsed and serviced (follow-up bought, round spent, `retrieval_outcomes == ["OK"]`); a
`fetch` call is still serviced; an undeclared name is rejected and visible on the row;
the `tool_call_unserviced` label no longer fires for a declared name.

`tests/test_tool_call_capture.py` (U-SPCC-49) asserted the OLD contract — that a
`read_file` call is dropped and labelled. Its two capture tests now use an UNDECLARED
name (`write_file`), so the guarantee they protect (nothing the server signalled is
dropped silently) still holds under the new contract.

## Pre-existing failures, not caused by this unit

The wider `experiments/ptr-engine/{tests,longrun/tests}` sweep reports 71 failures, all
pre-existing and unrelated: `repeat-identity: rep=1 not present in run_id='run-offline'`
(`run_longrun.py:2705`), `treatments contract not declared by this fixture`, the global
cap already at `spent=8699 cap=4320`, and the ledger/pin/digest/verbosity families
(`rows file missing from corpus: rows-e1-final-2026-11-10.jsonl`). None names a tool
name, the fetch parser, or a row this unit touches.

## Writes

`experiments/ptr-engine/ptr_engine/fetch_tool.py`,
`experiments/ptr-engine/longrun/arm_cd.py`,
`experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_fetch_call_names.py`,
`experiments/ptr-engine/longrun/tests/test_tool_call_capture.py`,
`orchestration/units/U-SPCC-52.md`, `orchestration/handoffs/U-SPCC-52.json`.
`measure/rows-*.jsonl`, every fixture, `ptr_engine/layers.py`, `longrun/arm_cd.py`'s
budget code, `longrun/claim_mode.py`, `longrun/cell.py`, `FINDINGS-LEDGER.md`,
`docs/STATE.md`, `journal/2026-11-10.md`, `orchestration/STATUS.md` and
`research-seed-concepts/PREREG-SPCC.md` untouched.
