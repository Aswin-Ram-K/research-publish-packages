# TOOL-CHANNEL-WIRE — putting a schema on the wire and consuming the call that comes back

**Unit:** `TOOL-CHANNEL-WIRE` · **Date:** 2026-10-26 · **Bound:** 40 tool calls, **0 model
requests** (offline: every proof below is a fake response; the mechanism was already proven by
two live probes in `docs/TOOL-CHANNEL-ROOT-CAUSE.md` §3).
**Root cause fixed:** `client_never_sends_tools` (`docs/TOOL-CHANNEL-ROOT-CAUSE.md`,
`orchestration/handoffs/TOOL-CHANNEL-ROOT-CAUSE.json`).

Two coupled changes, because doing one alone makes the arms worse: a tools-on reply has
`content_len == 0` and the call in `message.tool_calls`, so a client that sends the schema but a
runner that still scans `content` would record **nothing at all**.

| # | File | Change |
|---|------|--------|
| 1 | `experiments/ptr-engine/longrun/client.py` (`request_body`, `:317`) | body gains `tools=[read_file schema]` + `tool_choice` **only** when `tools_enabled(cfg)`; `tools_body_members()` returns `{}` otherwise |
| 2 | `client.py` (`send_chat`, `:658` region; `collect_stream`) | `message.tool_calls` is surfaced as data (`tool_calls`), not flattened to `tool_calls_present`; streamed call deltas are assembled by index; argument-parse errors are kept on the record |
| 3 | `experiments/ptr-engine/longrun/run_longrun.py` (`calls_from_response`, new; `fetch_rounds` `:943`/`:1121`) | consumes structured `tool_calls` **first**, falls back to `parse_tool_calls(content)` only when there are none |
| 4 | `run_longrun.py` (`make_row`, `provenance_for`) | every row carries `tools_declared` and `tools_schema_sent`; `provenance_block` gained `tools_schema_sent` |
| 5 | `run_longrun.py` (`tool_names`/`tools_enabled`) | delegate to `client.tool_names`/`client.tools_enabled` — one predicate gates both the label and the wire |

The only body mutations that existed before were `client.py:340` (`stream_options`) and
`client.py:343` (`chat_template_kwargs`); the schema is appended after them, so key order and
bytes are untouched on a tools-off run.

## 1. The two request bodies, quoted

Measured offline with a `SimpleNamespace` cfg (`model=occamy-1.0`, `temperature=0`,
`max_tokens=64`, `thinking=off`, one user turn `hi`):

```
TOOLS-OFF  keys = ['model','messages','temperature','max_tokens','stream','chat_template_kwargs']
           'tools' in body = False   'tool_choice' in body = False
           request_digest = f0499dd1335cccb27db359bee8d29c02a0f3015ee8e734404f288fbff0e2f8da
           (identical to the digest captured BEFORE the change — byte identity, not a claim)

TOOLS-ON   keys = [...,'tools','tool_choice']
           tools[0].function.name = read_file
           tools[0].function.parameters.required = ['path','start_line','end_line']
           tool_choice = 'auto'
           request_digest = 3c0ff847d9689168b17ab8c50dbd754d7f67cc3f590f7b387ac74a32f2ee6561
           (CHANGED, as expected: the body gained two keys)
```

`experiments/ptr-engine/tests/test_tool_channel_wire.py` pins both facts: it compares the
tools-off body byte-for-byte against the legacy dict, reproduces the historical digest
`f0499dd1…` on the exact message set it was captured with, and asserts the tools-on digest differs.

## 2. What the runner does with each reply shape (fake responses, no network)

| fake reply | asserted outcome | test |
|---|---|---|
| `finish_reason='tool_calls'`, `arguments='{"path":"ptr_engine/resolve.py","start_line":66,"end_line":110}'` (probe A verbatim) | **exactly one** follow-up send; one `tool-followup` row with `billed_round=True`, `send_index=1`, `tools_schema_sent=True`; call record `executed=True`, `base="engine"`, `lines_returned=45` | `test_structured_call_performs_exactly_one_fetch_round` |
| same shape, `arguments='{not json'` | refused and recorded: `error="malformed_tool_arguments"`, `reason="malformed_arguments_json: …"`, `billed=False`; **zero** follow-up sends, zero rounds | `test_malformed_arguments_are_refused_and_recorded` |
| text `<tool_call>…{"path":…}…</tool_call>` | still parsed (backwards compatibility); one round, `billed_round=True` | `test_text_tool_call_reply_still_parses` |
| `content_len=0`, no `tool_calls`, no finish chunk | `stop_reason="empty_response"` on the response **and** on the row; `content_sha256` of `""`; `calls_from_response` returns `([], [])` | `test_empty_reply_with_no_tool_calls_is_recorded_not_empty` |
| tools off | `tools_schema_sent=False`, `tools_declared=False`, no `tools` key on the wire | `test_send_chat_puts_the_schema_on_the_wire_and_surfaces_the_call` |
| whole flow re-run with `urlopen`, `socket.socket`, `subprocess.Popen` all patched to raise | passes: **zero network, zero subprocess** | `test_flow_touches_no_socket_and_launches_no_subprocess` |

A malformed call is never a silent no-op: it lands in `turn_calls` (hence on the turn row's
`tool_calls`), with `executed=False`, `billed=False` and a `reason`.

## 3. `tools_mode` honesty — historical `on:read_file` rows were a FALSE label

`client.tools_mode_label()` (`:862`) derives `on:read_file` from the runner argv. Until this
change that label was the **only** thing a row said about tools, and **no `tools` member was ever
serialised into any request body**. So every historical row whose `tools_mode` reads
`on:read_file` was a *declared* label with **no schema behind it** — the arms were tools-off on
the wire. Those rows are **not retrofitted** (rewriting them would be inventing evidence); the
defect is recorded here and in the handoff. From now on:

- `tools_declared` — the run's `--tools` switch (what `on:<csv>` has always meant);
- `tools_schema_sent` — the WIRE fact for that row's request (`True` only when a `tools` member
  was serialised; on a failure row with no response stamp it falls back to the request body's own
  deterministic gate, and a tools-off row is always `False`).

## 4. Provenance moved on purpose (do not claim continuity)

`request_digest`/`request_sha256` hash the exact body bytes. Every **tools-on** row written from
now on has a **new** request identity (`f0499dd1…` → `3c0ff847…` for the quoted body): a row
before this change and a row after it are **not** the same request and must not be deduplicated
against each other. **Tools-off rows are unchanged** — established by the byte-identity proof in
§1, not asserted by fiat. The generation-5 pin records the old harness digests, so this change
also moves `harness_sha256` (see §6).

## 5. Test evidence

```
bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_tool_channel_wire.py -q'
8 passed
```

Whole engine suite (`-k "not pin_matches_the_bytes_on_disk"`):
`10 failed, 326 passed, 1 deselected`. Classification:

- `test_embedded_digests_match_pin.py::test_pin_matches_the_bytes_on_disk` — **expected** and
  excluded from that count: the pin embeds `35ff41b7…`, the tree now hashes to `efefd885…`
  (`client.py` and `run_longrun.py` are `HARNESS_FILES`). This is the pin consequence, not a
  test defect — see §6.
- `test_launcher_pin_and_cells.py` (6 tests) — **pre-existing, unrelated**: every one fails on
  `REFUSED: ledger records disagree on 'remaining': {'baseline-2': 3192/3219, 'request-ledger':
  3144}` raised by `experiments/ptr-engine/tools/run_a_star.py:229`. No tool-channel code is
  involved and `run_a_star.py` is a forbidden write path.
- `test_launch_contract_diff.py` (3 tests) — **pre-existing, neighbour-caused**: the tool exits 1
  and a sibling assertion in the same file reports `competing values: 108, 67 (108 at
  run_a_star.py:631; 67 at run_a_star.py:763)` where a `run_a_star.py:241` anchor was expected —
  again `run_a_star.py`, not the tool channel.
- `test_era_b_rehearsal_2.py::test_grader_sha_is_the_repaired_one_and_pin_is_stale` —
  **pre-existing**: its premise (the pin's recorded `grade_v5.py` is pre-repair) no longer holds
  (`current_grade_v5_sha256 = 3d70ed1d…` equals the pin's recorded value), so `pin_is_stale`
  is `False`. Independent of this change and of `grade_v5.py`'s bytes.

## 6. PIN CONSEQUENCE — generation 6 is required before any live cell

`experiments/ptr-engine/longrun/client.py` and `experiments/ptr-engine/longrun/run_longrun.py`
are both in `cell.HARNESS_FILES`. This unit ran under **pin generation 5**, which is now **stale**:
the recorded harness digest and the per-file digests for those two files no longer match the
bytes on disk. A generation 6 must be generated (pin generation is a separate card; this unit is
forbidden to touch pins, cells, params or ledgers) **before any live cell**. Until then every
live cell launched against generation 5 would be measuring a harness the pin does not name.

The canary was **not** re-run here — that is the next card's job, after generation 6.

## 7. Files

- `experiments/ptr-engine/longrun/client.py` — schema + body gate, structured tool_calls, row facts
- `experiments/ptr-engine/longrun/run_longrun.py` — `calls_from_response`, consumption, row facts
- `experiments/ptr-engine/tests/test_tool_channel_wire.py` — 8 offline proofs
- `orchestration/units/TOOL-CHANNEL-WIRE.md`, `orchestration/handoffs/TOOL-CHANNEL-WIRE.json`,
  `orchestration/journals/TOOL-CHANNEL-WIRE.jsonl`
