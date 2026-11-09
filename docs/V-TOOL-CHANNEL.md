# V-TOOL-CHANNEL — adversarial verdict on `TOOL-CHANNEL-WIRE`

**Verifier unit:** `V-TOOL-CHANNEL` · **date** 2026-10-26 · **bound** 30 calls · **model calls 0**,
**network 0** (every reply below is a fake folded through the real `client.send_chat`; no socket,
no subprocess, no fixture write).
**Claim under test:** `TOOL-CHANNEL-WIRE`, execution `dda84411`, author PASS `f17663d1`
(`orchestration/handoffs/TOOL-CHANNEL-WIRE.json`, `docs/TOOL-CHANNEL-WIRE.md`).
**I did not write the change.** Everything below was re-derived from
`experiments/ptr-engine/longrun/client.py` and `experiments/ptr-engine/longrun/run_longrun.py`
(`client.py` sha256 `9b12b2ea…`, `run_longrun.py` sha256 `4f40dde1…` — both identical before and
after my work, and identical to the shas the author's handoff records).

**THE WIRE IS NOT SILENT.** A tools-on request carries the schema, and a structured `read_file`
call is executed and answered: the next request's last user message begins
`<tool_result for="read_file" path="ptr_engine/resolve.py" lines="66-110" base="engine">` with the
real line 66 in it. One call bills exactly one follow-up round.

**Overall: `partial`.** The two coupled halves work. The faults are in the **labels and edge
refusals**, not in the fetch path: three code paths can still claim `tools_schema_sent = true`
with no schema on any wire, a reversed range is silently swapped instead of refused, and the
executed call record throws away the `source`/`call_id` the hand-off promised a row would carry.

---

## Attack results (each with the command and its measured output)

Evidence file: `experiments/ptr-engine/tests/test_tool_channel_attack.py` (new, written by this
verifier). Frozen command:

```
bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/tests/test_tool_channel_attack.py -q'
-> ..............x........  [100%]
   22 passed, 1 xfailed in 0.53s          (exit 0)
```

The single `xfail(strict=True)` is the one expectation the card demands and the code does not
meet: a `start_line > end_line` call must be a recorded refusal. Marking it `strict` means it
goes red if someone later "fixes" the test instead of the code.

### 1. Byte neutrality — `confirmed` (the attacker did not get through)

```
tools-off shapes absent/""/none/None/False/0/["read_file"]/write_file
  keys == ['model','messages','temperature','max_tokens','stream','chat_template_kwargs']
  'tools' absent, 'tool_choice' absent, tools_body_members == {}
  request_digest == f0499dd1335cccb27db359bee8d29c02a0f3015ee8e734404f288fbff0e2f8da   (all 8)
tools-on  keys[-2:] == ['tools','tool_choice']; name read_file; required ['path','start_line','end_line']
  request_digest == 3c0ff847d9689168b17ab8c50dbd754d7f67cc3f590f7b387ac74a32f2ee6561
real send path (send_chat->_RecordingOpener): tools-off wire body has no `tools` key at all
mutate-after-build: body built with tools="", then cfg.tools="read_file"
  -> 'tools' not in body, digest still f0499dd1…  (no aliasing into the body)
```

`tool_choice` is `auto` on every tools-on body. **Correction to the hand-off's wording:** the cfg
attribute is `cfg.tool_choice` (not `tools_choice`), and **no CLI flag sets it** — `--tools` is the
only tool flag (`run_longrun.py:2992`). `required` is reachable only if a caller injects
`cfg.tool_choice="required"`; the "mode" does not ask for it in any live path.

**Red→green (guard sensitivity):** reverted the fix in memory
(`client.tools_body_members = lambda cfg: {"tools":[READ_FILE_TOOL_SCHEMA],"tool_choice":"auto"}`)
and re-ran attack 1:

```
cd /tmp/vwire && /usr/bin/python3 -m pytest test_redgreen.py -q
-> 1 passed in 0.01s      # the byte-neutrality guard FAILS (pytest.raises catches it) when the gate is removed
```

So the byte-identity guard bites when the gate is reverted. No tools-off body gained a `tools`
key on any path I could construct.

### 2. Double consumption — `confirmed` (one round), with an attribution defect

Fake reply with **both** `message.tool_calls = [PROBE_CALL]` **and**
`content = '<tool_call>read_file <tool_call>{"path": …}'`:

```
follow-up sends (fake.messages): 1
sent=2  rounds=1  follow-ups=1  billed_round=True
turn_calls: exactly 1 record, executed=True
```

One request, one bill. The text copy is not executed — `calls_from_response` returns the
structured call and never runs the text parser when `tool_calls` is non-empty
(`run_longrun.py:697-699`).

**`overstated` sub-claim.** The executed record is rebuilt by `execute_tool_call`
(`run_longrun.py:801-802`) as `{path,start_line,end_line,executed,truncated,...}` — it **drops**
`source="structured_tool_call"` and `call_id` that `_call_from_arguments` put on the pending call.
The hand-off's `next_unit_hint` promises rows "carrying tool_calls with source='structured_tool_call'";
no executed row can carry it (only refusals keep `tool`/`call_id`, and they do not carry `source`).
Verified:

```
'source' not in turn_calls[0] and 'call_id' not in turn_calls[0]   -> True
```

### 3. Malformed arguments — `overstated` (3 of 4 confirmed, reversed range is not refused)

| input | measured | verdict |
|---|---|---|
| `arguments='{not json'` | refusal `error=malformed_tool_arguments`, `reason=malformed_arguments_json: …`, `executed=False`, `billed=False`; **0** follow-up sends, rounds=0 | `confirmed` |
| missing `path` | refusal `reason=missing_path`, 0 sends | `confirmed` |
| unknown tool `shell` | refusal `reason=unknown_tool`, 0 sends | `confirmed` |
| `path="../../etc/passwd"`, `"/etc/passwd"`, `"~/.ssh/id_rsa"`, `"creds.env"` | `executed=False`, `error=path_refused`/`path_not_found`; the next prompt gets `<tool_result error="…"/>` with **no file content**; but one round IS billed and a follow-up IS sent | `confirmed` (recorded refusal; billing is a design choice, not a fabricated fetch) |
| `start_line=110, end_line=66` | **silently swapped to 66–110 and EXECUTED**; `executed=True`, one round billed | **`overstated`** — the card requires a recorded refusal |

```
run_longrun._call_from_arguments("id","read_file",{"path":"ptr_engine/resolve.py",
    "start_line":110,"end_line":66})
-> ({'path': 'ptr_engine/resolve.py', 'start_line': 66, 'end_line': 110,
     'source': 'structured_tool_call', 'call_id': 'id'}, None)
```

`calls_from_response` never sees an error for it (`refusals == []`). The text parser does the same
swap (`run_longrun.py:651-652`), so the behaviour is uniform — but it is a normalisation, not the
refusal the hand-off claims.

### 4. Empty-content turn — `confirmed` (explicit, recorded, not vanished)

`content_len == 0`, no `tool_calls`, no finish chunk:

```
resp.stop_reason == 'empty_response';  calls_from_response(resp) == ([], [])
row: stop_reason='empty_response', content='', content_tokens=0,
     content_sha256=e3b0c442…(sha of ""), tools_schema_sent=True
same shape with finish_reason='stop' -> stop_reason='stop'
```

### 5. Text fallback — `confirmed` for a text-only reply; one edge `unverified`

`<tool_call>…{"path":"ptr_engine/resolve.py","start_line":66,"end_line":110}` with no structured
calls: `calls_from_response` returns 1 call, 1 follow-up, `billed_round=True`.

**Edge (observation, not a contradiction):** a reply with an **invalid** structured call *and* a
valid text call fetches nothing — any structured entry suppresses the text parser even when every
structured entry is refused (`calls == []`, `rounds == 0`). Defensible (structured wins), but it
means "text fallback" is only preserved for replies with **zero** structured calls.

### 6. Label honesty — `overstated` (3 paths claim `sent` with no wire)

Honest path confirmed: a response-stamped row follows the body — tools-off → `False`,
tools-on → `True`; `client.send_chat` stamps `tools_schema_sent = bool(body.get("tools"))`
(`client.py:847`).

Faults, each measured:

1. **Failure row.** `make_row(cfg tools=read_file, resp=None)` → `tools_schema_sent=True`.
   Nothing was serialised or sent. `make_row` falls back to
   `client.tools_enabled(cfg)` (`run_longrun.py:2071-2072`), i.e. the **declared** flag, not any
   body. This contradicts the doc's §3 claim that the fallback is "the request body's own
   deterministic gate" — there is no body on this path.
2. **Wall-cap stamp.** `TurnWallCap.as_response(cfg)` stamps
   `tools_schema_sent = bool(tools_enabled(cfg))` (`client.py:298-299`). With a tools-off body
   already built and `cfg.tools` flipped afterwards, the cap row says `True` over a body that has
   no `tools` key. Contrived (requires a mid-turn mutation), but it is "true without a schema on
   the wire".
3. **Manifest provenance.** `provenance_for(..., tools_schema_sent=client.tools_enabled(cfg))`
   (`run_longrun.py:1846`) is derived from the flag, so a **dry run** with `--tools read_file`
   publishes `provenance.tools_schema_sent = true` while making zero requests. The six existing
   dry-run manifests predate the change and still read `None`, but any new dry run will lie in
   the same direction.

**Historical `on:read_file` rows — quantified, not rewritten.** Across the workspace's
`experiments/ptr-engine/**/*.jsonl` row files:

```
row files carrying tools_mode: 5
tools_mode == "on:read_file": 48 rows
  tools_schema_sent absent: 48   true: 0   false: 0
tools_mode off rows: 27
```

So all **48** historical `on:read_file` rows are still labelled that way and **none** carries
`tools_schema_sent`. They are not retrofitted (correct — rewriting would invent evidence). Their
request bodies are not retained on the rows, so the "no schema was ever serialised" claim is not
re-provable per row from the row files alone; it rests on the pre-change body digest
`f0499dd1…` on the one captured message set. I did not claim more than that.

### 7. The claim nobody tested — `confirmed` at the `fetch_rounds` seam, `unverified` inside `run_cell`

Fake harness: initial reply `finish_reason='tool_calls'`, `arguments={"path":"ptr_engine/resolve.py",
"start_line":66,"end_line":110}`; scripted follow-up `content="answer"`.

```
follow-up sends: 1; sent=2; rounds=1
follow-up prompt[-2] == {"role":"assistant","content":""}
follow-up prompt[-1].content[:200] ==
  '<tool_result for="read_file" path="ptr_engine/resolve.py" lines="66-110" base="engine">\n
   def _refuse(ledger: Optional[Ledger], scope_name: str, text: str, error: PtrError) -> None:\n
       """Record the re'
line 66 of experiments/ptr-engine/ptr_engine/resolve.py occurs in the block  -> True
call record: executed=True, base='engine', lines_returned=45
row.prompt_sha256 == sha256(block)
```

So the result is not merely a parsed object: the real file content reaches the next request.

Two honest limits:
- the follow-up does **not** use the OpenAI tool protocol — no assistant `tool_calls` echo and no
  `role:"tool"`/`tool_call_id`; the result is a synthetic **user** message with an XML block
  (`run_longrun.py:1105-1109`). That is consistent with the engine's text-style usage and with
  the existing `<tool_result>` channel, but a server that validates the tool protocol strictly is
  **untested**.
- this was proven at the `fetch_rounds` seam, not through `run_cell` (no live cell is runnable:
  pin generation 5 is stale because both changed files are `HARNESS_FILES`). Whether a cell writes
  the row and bills the follow-up through the full loop remains `unverified` here.

---

## Originals unchanged (proof)

Hashes measured **before** any work and again **after**. `client.py` and `run_longrun.py` — the two
files the wire fix actually changes — are identical both times and still equal the digests the
author's handoff records. `cell.py` is the exception: it was `a6446bfc…` at 19:12 and `0bddd4e0…`
at 19:15, **changed by a concurrent unit, not by me** (mtime `2026-10-26 19:14:55`, and its content
now equals `git HEAD`; `orchestration/handoffs/HARNESS-PIN-GEN6.json` and
`orchestration/handoffs/LAUNCHER-GEN6-WIRE.json` appeared in the same window). I made no write to
`cell.py`; the change is recorded here as an external change rather than hidden.

```
client.py       9b12b2ea948b23f0f1600c4bcf4c8f6d72e17e900c046e555e7bc78d6630c0c6   (before == after)
run_longrun.py  4f40dde188b4812031c01304b3bd07c9f5b64ecc268aa48bb46eb3aabf69a4ca   (before == after)
cell.py         a6446bfc… -> 0bddd4e0…  (EXTERNAL: concurrent gen-6 pin/launcher unit, mtime 19:14:55)
run_a_star.py   4709cd6c48ddfe3b72c07604874b19f0f80353922ac753f4a0c5d60237c905d1
analyze_stats.py 30b07d4d61930e0cb863badd553d0e11e8c9bdcfdba7de5973abdbd675253c9a
grade_v5.py     3d70ed1d43d2ab098eeeba4b50fa574273c71e9ff24af5adaa9e519d10c77940
HARNESS-PIN.json fc1b56856def43ba988f6a5d8c6e25ec719463c5774094d6d45cf3e9900fad1a
GRID-PARAMS.json 10596c5442154990fd2c9f160d016638cb98e62c4a190eaf553c2816cc3a7898
```

No row, fixture, grade or published page was written; the attack tests only **read**
`tasks-v6/LR-01.v8.json` and `ptr_engine/resolve.py`.

## Correction the author should make

`docs/TOOL-CHANNEL-WIRE.md` §3 should not say the failure-row fallback is "the request body's own
deterministic gate" — it is the declared flag. And the hand-off's promise of
`source='structured_tool_call'` on rows should be dropped or implemented in `execute_tool_call`'s
record. Neither changes the wire fact; both change what a later analysis may believe.

## Files

- `experiments/ptr-engine/tests/test_tool_channel_attack.py` — 22 assertions + 1 strict xfail
- `docs/V-TOOL-CHANNEL.md` — this report
- `orchestration/handoffs/V-TOOL-CHANNEL.json` — verdict handoff
- `orchestration/units/V-TOOL-CHANNEL.md`, `orchestration/journals/V-TOOL-CHANNEL.jsonl`
