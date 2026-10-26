# FETCH-CHANNEL — bounded, opt-in read_file tool channel for the longrun runner

**Status:** done · **Verdict:** TOOL-CHANNEL-READY · **Requests sent:** 0 · **Bound:** 26 tool calls (used 16)

## Purpose

`RUN-V4-GRID` checkpoint 3 (arm `pointer-stable`) produced a real fetch request that nothing served:

```
<tool_call>2629 <tool_call>read_file <tool_call>{"path": "experiments/ptr-engine/ptr_engine/resolve.py", "start_line": 66, "end_line": 71}
```

The pointer arms' designed resolution path — pointer plus on-demand fetch — has never existed in any
run of this programme. This unit adds the channel, behind a flag, without changing anything historical.

## What was added (all additive)

`experiments/ptr-engine/longrun/run_longrun.py` (+291 lines, 1212 → 1503):

| Piece | Bound |
|---|---|
| `--tools LIST` (default `""` = off) | off = no code path runs, no row/manifest key added |
| `parse_tool_calls()` | accepts the observed repeated-marker shape and a bare JSON object after `read_file` |
| `execute_tool_call()` / `resolve_read_path()` | 200 lines / 8,000 chars cap, `truncated="true"`; refusal before any open |
| `limit_calls()` | ≤ 2 calls per turn (`turn_call_cap` for the overflow) |
| `fetch_rounds()` | exactly 1 follow-up request per fetch, ≤ 8 rounds per arm |
| rows | `kind="tool-followup"`, `fetch_followup: true`, `tool_calls: [{path,start_line,end_line,executed,truncated}]` |
| budget | `N + digests + 8` **only** when tools are on |

Refusals: absolute, `~`, any `..` component, realpath escaping the workspace, secret-shaped
basenames (`.env*`, `id_rsa*`, `*.pem/.key/.p12/.pfx`, `credentials|secrets|secret|keys|clients[.ext]`)
→ `<tool_result error="path_refused"/>`, zero reads. Safe-but-missing → `path_not_found`.

## Verification (offline, no model)

1. **Tools off is byte-identical.** Pre-edit runner reconstructed by reversing the six hunks (1212
   lines); both run on `LR-01.v4.json`, 4 arms, `--dry-run --show-prompts` → stdout diff 0
   (sha256 `487e4fdb…` both sides), 12/12 preview request bodies identical. The only excluded line is
   `manifest[...]`, whose sha256 embeds `created_utc` and differs between any two runs of the same code.
2. **`tests/test_tool_channel.py` exit 0**, assertions (a)–(e) plus (f) accounting and (g) row schema.
3. **Dry-run with tools:** exit 0, `would_send_total=48`, and the added system-prompt sentence is
   present in the actual payload under `/tmp/longrun-previews/…/turn-01.json`, not merely in stdout.

## The counting rule a CP3 probe must expect

A fetch is a request. Worst case per arm: **N + 8 = 56** requests; typical: 48 + (turns that fetched).
`summarise_rows.requests_spent` counts rows with `error == null`, so extra requests are visible there.
A fetch row is never the turn's answer — the final response of the turn is the `kind="turn"` row, and
follow-up rows are appended before it so `by_turn[t]` still resolves to the real answer.

## Not touched

`grade_v3.py`, `score_longrun.py`, `grade_v2.py`, `analyze_longrun.py`, every existing fixture, every
row file, every check, the marker rule, all historical budgets. `LR-01.v4.json` unchanged (mtime 06:13,
before this unit's writes); its `.tools.json` copy differs only in `system_prompt`.

## Known pre-existing failure (out of scope)

`tests_score_adapter.py` exits 1 at `assert "check.1" in card["unverifiable_required"]` (line 229).
It subprocesses `score_longrun.py` only and never imports `run_longrun.py`, so this unit cannot have
caused it.
