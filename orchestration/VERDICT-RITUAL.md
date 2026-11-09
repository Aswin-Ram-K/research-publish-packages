# VERDICT-RITUAL — the verdict row comes BEFORE the handoff write

The gate is binary and it is **derived from a verdict row**, never from a card's own report. A card that
delivers its work and writes no row settles **FAIL `no-verdict`**.

This page was rewritten on 2026-10-26 after the ritual it used to describe was measured at **0 of 7**
closures that happened *after* it landed. The old order lost; the numbers below are the reason.

## 0. Why the order changed — the measurement

`docs/HARNESS-MAP-V3.md` (card `2149bee1`, verdict PASS `f17663d1`): verdict rate by closure —
**all-time 4/897 = 0.45 %** · before the ritual **0/39** · this batch **1/46** · **after the ritual landed
0/7**. Its top new waste: **45 of 46 batch closures are `FAIL no-verdict`**.

The seven post-ritual closures, diagnosed from their own journals and handoffs (no retroactive edit was
made to any of them):

| unit | execution | journal's last event | verdict call attempted? | acceptance command in handoff? |
|---|---|---|---|---|
| `ROW-PROVENANCE` | `866ee0f3` | `end` | **no** — no mention of a verdict anywhere in 6 events | yes (`tools/row_provenance.py`) |
| `DEDUPE-ROOT-CAUSE` | `44d74428`, `31e3b9a5` | `end` | **no** — 0 mentions in 13 events | yes (`test_request_identity.py`) |
| `V-GATE-CHAIN-2` | `89d3e252` | `verdict` (a *verifier* verdict event) | **no gate row** — it wrote `overall`/`checks` in the verifier shape | **no** |
| `LEDGER-CONSERVATIVE` | `4d03e65b` | `disclosure` | **no** — 0 mentions in 11 events | yes (`request_ledger.py --cap 4320`) |
| `REGRADE-ONE-COMMAND` | `3c8ca01f` | `done` | **no** — 0 mentions in 8 events | yes (`tools/regrade.py --all --report`) |
| `LATENCY-UNDER-DISPUTE` | `c18716a1` | `next` | **no** — 0 mentions in 8 events | yes (`tools/latency_report.py`) |
| `FAILED-TRIAGE` | `5e7e5af7` | `end` | **no** — it *measured* "0 verdict rows for these executions" and still wrote none | **no** |

**Counts per class: never attempted 7 · attempted and refused 0 · attempted too late 0 · no acceptance
command existed 2 (both also never attempted) · other 0.** The dominant class is **never attempted**, and
its proximate cause is visible on the cards themselves: **0 of the 7 carried a `verdict` tag** — the board
holds 19 tagged cards and none of the seven is among them. The instruction was on the tag rollout, not on
these cards, and the page put the call *after* the handoff.

The timing shape still matters. In the old order the verdict was step **(b)**, i.e. *after* the handoff:
the last act of a card was the act most likely to be lost to a session death (this workspace lost at least
three sessions at the handoff step — `PROBE-CP3-V6`, `Q0-ANSWER-DEGENERACY`, and one more). A rule that
competes with the handoff for the final step loses to session death, and it also loses to the feeling of
being finished that arrives when the handoff file is written.

`ORDER: verdict-row-before-handoff` — this literal marker is asserted by
`experiments/ptr-engine/longrun/tests/test_verdict_ritual.py`, so the order cannot be quietly reversed.

## 1. The order — three steps, and the handoff is LAST

1. **Run the acceptance command** — the same command the card's `verify:` line names, as one frozen string.
2. **Record the verdict row** — `orchestration_verdict {action:"record", ...}` (payload in §3).
3. **Write the handoff** `orchestration/handoffs/<UNIT>.json` — and in it state
   `"verdict_recorded_before_handoff": true` (or the declared gap of §4).

Why this order and not the reverse: the handoff write is the step every unit actually reaches; the verdict
is the step units skip. Making the verdict a **precondition of the handoff** means a unit that stops early
stops *before* claiming completion instead of after it. If the session dies during the handoff write, the
row already exists and the gate can still derive PASS.

## 2. The three ways a card loses its PASS

1. **No verdict row.** The gate settles `no-verdict` whatever the diff says. The row is read from
   `~/.dsh/storages/orchestration/verdict.jsonl`, keyed `taskId:executionId`.
2. **A different command on a retry.** The command hash is **frozen per execution**: re-running the *same*
   command overwrites the row; a different command is refused (`command-frozen`). Fixing code and adopting
   a different test line does not convert FAIL to PASS.
3. **A sha that is not the head.** Sample it with `git --no-optional-locks rev-parse HEAD` **before** the
   command runs and paste it verbatim. If git cannot answer, record **`unstamped`** in the handoff:
   an absent sha is refused honestly (`bad-sha`); a guessed one is not.

## 3. The one-liner that produces the payload

```sh
python3 experiments/ptr-engine/tools/verdict_payload.py \
  --task <taskId> --execution <executionId> \
  --command '<the exact acceptance command>'
```

It prints **one** JSON object — `{taskId, executionId, command, exitCode, sha, output_tail}` — echoes
`command` byte-identical (a re-quoted retry is a different frozen command), exits with the acceptance
command's own exit code, warns on stderr for a dirty tree, and drops `sha` with `UNSTAMPED` rather than
inventing one. Acceptance test: `python3 experiments/ptr-engine/longrun/tests/test_verdict_payload.py`.

## 4. A card with no acceptance command must declare it

In its handoff **and** its board end line:

```json
"acceptance": {"command": null, "reason": "prose re-issue; no executable that fails when the page is wrong"}
```

A declared gap is a record a reader can act on. It is not a PASS. Two of the seven post-ritual units
(`V-GATE-CHAIN-2`, `FAILED-TRIAGE`) had no runnable acceptance command at all — for those the honest
record is this declaration, and the gate still settles on evidence.

## 5. The gate that makes a skip visible offline

```sh
python3 experiments/ptr-engine/longrun/tests/test_verdict_ritual.py
```

It reads the **local** ledgers (`closure.jsonl`, `verdict.jsonl` — both plain JSONL, no network, no
inference), pairs every done/verdict-shaped handoff with its closed executions, and **fails** when a
closure settled after the recorded baseline has no verdict row. It also asserts the order above in this
page and in `orchestration/units/TEMPLATE.md`. It never writes and never fabricates: a repaired gap is
accepted, a new gap is red. Because it is a suite test, skipping the ritual now shows up in a test run
instead of in an audit two days later. The baseline and the known-gap list live in
`experiments/ptr-engine/measure/VERDICT-ADOPTION.json`.

## 6. The re-measurement the next auditor runs (HARNESS-MAP-V4 does not have to invent it)

Read-only; prints closures, verified count, rate, and the verdict rate split at the ritual boundary:

```sh
python3 - <<'PY'
import json, os, datetime
B = os.path.expanduser('~/.dsh/storages/orchestration/')
RIT = datetime.datetime(2026, 10, 26, 16, 13, 5, tzinfo=datetime.timezone.utc).timestamp() * 1000
state = {}
for line in open(os.path.join(B, 'closure.jsonl')):
    line = line.strip()
    if line:
        rec = json.loads(line)
        state[rec['key']] = rec['value']
rows = sorted(state.values(), key=lambda v: v.get('createdAt') or 0)
def rate(rs):
    return (sum(1 for v in rs if v.get('verdict') == 'verified'), len(rs))
for name, rs in (('all-time', rows),
                 ('after-ritual', [v for v in rows if (v.get('createdAt') or 0) > RIT])):
    ok, n = rate(rs)
    print('%-13s %d/%d = %.2f%%' % (name, ok, n, 100.0 * ok / n if n else 0.0))
PY
```

Definition used, so the number is comparable: a **closure** is one `put` in `closure.jsonl` (latest per
`taskId:executionId`); it is **verified** when its `verdict` is `verified`; the **ritual boundary** is
`2026-10-26T16:13:05Z` (`VERDICT-RITUAL`'s own artifacts landing) and a closure is dated by `createdAt`,
the time the ledger wrote it. A row recorded *after* a closure does not retroactively change that closure's
verdict — it closes when re-settled (see `VERDICT-READJUDICATE-27`).

## 7. Bind the row to bytes

A commit sha is not a verdict about bytes. `f17663d1` has been followed by five moves of
`cell.py` alone (`0136052e` → `24627d7b` → `5a812a98` → …), so a row recorded today can be re-run
tomorrow against different bytes and the gate would still read PASS. **A verdict must name the bytes
it judged.** The wrapper does it as one command, and prints a paste-ready payload:

```sh
python3 experiments/ptr-engine/tools/tree_freeze.py \
  --path <declared file> --path <declared file> --path <declared file> \
  --verdict-row --wrap /tmp/rec.json -- <the exact acceptance command>
```

It prints one payload line `{"command", "exitCode", "sha"}` — `command` the exact string run,
`exitCode` the **command's** real exit (never the wrapper's 13), `sha` = `git rev-parse HEAD`
sampled at wrap start — and then a human line `verdict=…` with per-path `before -> after` (or
`deleted` / `created`), so the operator sees which file moved without opening the record. A dirty
tree at HEAD prints `WARNING: dirty tree at HEAD <sha>; the row names a commit that does not contain
these bytes` on **stderr**; the row still prints. An empty set of paths is refused (exit 2): a verdict
with no bytes is the defect this section exists for.

**`UNSTAMPED:`** — when any declared path is `moved`, `deleted` or `created`, the payload line is
prefixed `UNSTAMPED: ` and the run exits **13**. A caller that pipes it into `orchestration_verdict`
therefore sees the refusal in the line itself, and cannot mistake a row that names dead bytes for a
row that judged them. **`moved_during_run` is unstamped, not FAIL**: the remedy is a re-run against
the settled tree, not a re-reading of the result. `failed_and_moved` keeps its command-failed exit
(1) — the non-zero command is the more urgent fact and no exit code changes — but its row is
`UNSTAMPED:` prefixed too, because the bytes moved either way.

Acceptance: `python3 -m pytest -q experiments/ptr-engine/longrun/tests/test_tree_freeze.py`
(class `VerdictRowTests`: clean → `verdict=pass` + real exit · mutated → `UNSTAMPED:` + 13 ·
created → `created` row + 13 · empty `--paths` → 2 and no row · dirty tree → stderr warning).

## 8. Scope: which bytes the row judged

A row `{command, exit, sha}` says *what ran* and *how it ended*; it never says **which files the
command read**. Three rows settled this batch on a foreign red instead of a real one:
`SEAM-TEST-RED` recorded `FAIL exit-1` while `tests/test_cap_gate.py:205` was red from ANOTHER
card's in-flight edit of `cell.py`; `GRID-PARAMS-DIGEST-SUPERSEDE` recorded `FAIL exit-1` for a
`launch_contract_diff --check` that passed at 19:27 and failed only because `grade_v5.py` moved at
14:44; and the stale assertion itself manufactured three FAILs before anyone read the assertion.

[`tools/verdict_scope.py`](../experiments/ptr-engine/tools/verdict_scope.py) closes that gap with two
verbs and imports `tools/tree_freeze.py` rather than forking its freezer, classifier or exit code.

**`run`** freezes the named paths before the command, runs the command as an argv list, classifies
after against the before freeze, and prints ONE paste-ready payload:

```sh
python3 experiments/ptr-engine/tools/verdict_scope.py run --record /tmp/rec.json \
  --paths <declared file> --paths <declared file> -- <the exact acceptance command>
# {"command", "argv", "exitCode", "sha", "head_is_meaningful",
#  "scope": {"paths": [{path, sha_before, sha_after, moved}], "moved": [...],
#            "exit": N, "command": "...", "verdict": "clean" | "tree-moved"}}
```

`command` is the exact argv re-quoted (`shlex.join(argv)`) — never a shell program string; `argv`
carries the tokens unquoted. `exitCode` is the command's measured exit, never the wrapper's 13.
`sha` is the repo HEAD; **`head_is_meaningful` is `false` whenever a named path is untracked**, so
a row cannot present `sha f17663d1` as a statement about bytes that commit does not contain.

**`check`** re-freezes the row's named paths now and classifies it against present bytes:
`same` (present bytes are what it judged, exit 0), `moved_since` (the tree moved after the row —
information, exit 0), `path_missing` (a named path is gone — **exit 1**), `undatable` (no `scope`
block, exit 0).

**Exit 13 is `exit_codes.EXIT_TREE_MOVED`** — imported through `tree_freeze`, never re-typed. If
any named path moved, was deleted or was created under a declared root, the payload's
`scope.verdict` is `tree-moved` and the process exits **13**: the tree moved, the work did not
fail. The row is unstamped; re-run against the settled tree and do not re-read the result as a
verdict.

**The rule: a row without a scope block is `undatable`; an untracked load-bearing path makes
`head_is_meaningful: false`.**

Acceptance: `python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py` — 11 tests,
and the three historical instances are cases there (edit mid-run → 13 with both shas · named path
deleted → `check` 1 `path_missing` · untracked path → `head_is_meaningful: false`).
