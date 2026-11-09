# HANDOFF-LINT

`experiments/ptr-engine/tools/handoff_lint.py` makes a handoff's own evidence checkable.
`tests/test_orchestration_handoffs.py` proves every file in `orchestration/handoffs/` **parses as
JSON**; it does not prove that the artifacts a handoff lists exist, that a `done` carries evidence,
or that the file is anything more than the pre-run stub. This tool does.

Corpus numbers below were measured on the run recorded in
`experiments/ptr-engine/measure/HANDOFF-LINT.json` (946 files, `orchestration/handoffs/*.json`).

## The two contracted shapes

`AGENTS.md` contracts both; neither is "the wrong one".

| | unit handoff | verifier verdict |
|---|---|---|
| job | a unit reports its **own** work | a verifier reports whether an **author's** claims survived |
| verdict key | `status:"done"\|"failed"\|"partial"` | `overall:"pass"\|"fail"\|"partial"` |
| required keys | `unit`, `status`, `artifacts`, `evidence`, `blocker`, `next_unit_hint`, `write_paths` | `unit`, `overall`, `checks`, `blocker`, `next_unit_hint`, `write_paths` |
| carries artifacts | yes — the deliverables | no — `checks` are the evidence |
| common optional | `bound`, `assumptions`, `tool_calls`, `commands` | `not_reproduced`, `overstated`, `unverified`, `containment`, `red_green`, `corrections`, `tool_calls`, `bound`, `scope` |

Detection is `overall` present → verifier, else `status` present → unit, else `E_SHAPE`. (Some
verifier files carry both keys; `overall` wins, because that is the key the verdict is read from.)

## Codes

Each check has one stable code. Errors (`E_*`) set exit 1; warnings (`W_*`) do not unless `--strict`.

| code | fires when |
|---|---|
| `E_PARSE` | not valid JSON. Mid-write tolerance mirrors the existing guard: a file whose bytes change between two immediate reads is reported `skipped_mid_write` and is **never** a failure |
| `E_SHAPE` | matches neither shape (neither `status` nor `overall`), or the top level is not an object |
| `E_MISSING_KEY` | a required key for the detected shape is absent (per-shape, not one flat list) |
| `E_ARTIFACT_ABSENT` | a path in `artifacts` does not exist on disk — path reported **verbatim** |
| `E_DONE_NO_EVIDENCE` | `status:"done"` or `overall:"pass"` with empty/absent `evidence`/`checks`, or with an empty `artifacts` list |
| `E_DONE_NO_ARTIFACTS` | `status:"done"` listing zero artifacts that exist on disk |
| `E_STUB` | byte/structurally a stub: `status:"partial"` or `"stub"` with no artifacts, no evidence, no commands |
| `W_NO_COMMANDS` | `evidence` present but carrying no `commands` array |
| `W_VERSION_STALE` | best-effort rule: `orchestration/units/<unit>.md` contains a `superseded` marker **and** is newer than the handoff — i.e. the unit was replaced by a later card and this file describes the old one |

### What counts as "the artifact exists"

Writers annotate paths. To avoid calling a present file absent, existence is checked after stripping
only what cannot be part of a path:

- a trailing parenthetical note — `papers/x/GAPS.md (G16 appended)` → `papers/x/GAPS.md`
- a line anchor or JSON pointer — `RECORD.md#L145`, `RECORD.md:128`, `best-config.json#setups.O4`
- surrounding backticks; brace expansion `dir/{a,b,c}`; comma lists `a.py, b.py` (all parts must exist)

Relative paths resolve against the workspace root (`--root`, else the nearest ancestor holding
`AGENTS.md`). **This normalization is the difference between a true and a false accusation:** before
it, the same corpus reported 272 absent artifacts; 173 of those were real files with a trailing note.
Two remaining entries carry a remote scheme (`GX10:/…`) and ten are `/tmp` scratch paths — those are
genuinely absent locally, and the report counts them separately (`absent_remote_scheme`,
`absent_ephemeral_tmp`) rather than hiding them.

```
python3 experiments/ptr-engine/tools/handoff_lint.py orchestration/handoffs --summary \
    --out experiments/ptr-engine/measure/HANDOFF-LINT.json
```

Exit codes: **0** no errors · **1** at least one `E_*` · **2** usage/IO.

## Corpus numbers

946 handoffs scanned, 0 skipped mid-write, **0 unparseable**.

| shape | files |
|---|---|
| unit | 778 |
| verifier | 168 |
| neither | 0 |

| code | count | example |
|---|---:|---|
| `E_PARSE` | 0 | — |
| `E_SHAPE` | 0 | — |
| `E_MISSING_KEY` | 34 | `R2-A2.json` — unit shape requires `artifacts` |
| `E_ARTIFACT_ABSENT` | 75 | `FETCH-NVFP4-9B.json` — `/home/zer0null/models/qwen3.5-9b-nvfp4/` |
| `E_DONE_NO_EVIDENCE` | 4 | `R2-A3.json` — evidence empty/absent |
| `E_DONE_NO_ARTIFACTS` | 3 | `R2-A3.json` — done with 0 artifacts, 0 exist |
| `E_STUB` | 16 | `C8-SENTENCE-FIX.json` — partial with no artifacts, no evidence, no commands |
| `W_NO_COMMANDS` | 182 | `APPLY-ADJ-FIXES.json` |
| `W_VERSION_STALE` | 21 | `C63-CELL.json` — card newer and carrying a superseded marker |

**Substantiation gap: 40 of 759 `done`/`pass` claims (5.3%) list artifacts that are not all present**
— 2 of those are remote-host paths, 10 `/tmp` scratch. The other ~94.7% of success claims name files
that really exist. The 16 stubs are the more interesting number: a `partial` with nothing in it is a
handoff that was written before the work, and the card that produced it read as finished or failed
depending on who looked.

## Red → green

Each check was disabled in turn and its own test run; every code goes red when the check is removed
and green when restored (`python3 -m pytest experiments/ptr-engine/longrun/tests/test_handoff_lint.py -q`,
13 passed):

| code | with the check removed | restored |
|---|---|---|
| `E_PARSE` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_SHAPE` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_MISSING_KEY` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_ARTIFACT_ABSENT` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_DONE_NO_EVIDENCE` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_DONE_NO_ARTIFACTS` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `E_STUB` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |
| `W_NO_COMMANDS` | `1 failed, 12 deselected` | `1 passed, 12 deselected` |

Exit codes 0/1/2 and the mid-write skip are asserted in the same file
(`test_exit_codes`, `test_mid_write_is_skipped_not_error`).

## Live demonstration (temp copy, never a real handoff)

Three crafted handoffs in a temp workspace:

```
FAIL  …/DEMO-DONE.json  shape=unit  errors=E_ARTIFACT_ABSENT
        E_ARTIFACT_ABSENT: docs/NEVER-WRITTEN.md
FAIL  …/DEMO-STUB.json  shape=unit  errors=E_STUB
        E_STUB: status:partial with no artifacts, no evidence, no commands
        (DEMO-VERIFY.json: overall=pass with a real check — clean, not printed)
summary: files scanned 3 · unit=2 verifier=1 neither=0 · done/pass missing artifacts: 1 · exit 1
```

## Divergence with the existing guard (found by running both)

`tests/test_orchestration_handoffs.py::test_no_new_contract_key_gaps` fails today, **pre-existing and
not caused by this card** (all three files are git-unmodified): it reports verifier-shape gaps
`['overall','checks']` for `V2-RUNTIME.json`, `V3-FIXTURE.json`, `V3-PILOT.json`. Those three carry
`status:"done"` and no `overall` — they are **unit-shaped handoffs whose unit name starts with `V`**,
and the guard's classifier keys off the name prefix. `handoff_lint` classifies by key presence, so it
reads them as unit handoffs and finds them clean. Two classifiers, two answers on three legacy files;
neither is wrong about the JSON, but any automation that groups by shape must say which rule it uses.

## What this does not prove

A linter proves **artifacts exist**, not that they are **correct**. A `done` whose every file is real
can still be a wrong measurement, a mis-read log, a stale number, or a fix that does not fix the bug —
`E_ARTIFACT_ABSENT` will not fire, and the handoff will look immaculate. Likewise `W_NO_COMMANDS` says
only that the evidence is prose rather than a command that can be re-run; prose evidence can be true.
Nor does a green lint mean the two shapes are being used well: it checks the presence of keys, not
whether a `checks` list actually re-ran the author's command.

That gap — is the claim true — is the verifier's job, and stays the verifier's job. This tool removes
one specific class of lie (the file that was never written, the stub that reads as a result) so that
verification is spent on the harder question.

## `status:"recovered"` — a third valid status, not an exemption

A recovered record says *"this unit was a stub, it was re-run, and the real work landed"*. That is a
positive claim, so it carries every duty of the unit shape and two of its own. Before this rule the
status matched no check at all: `E_STUB` was evaluated only for `partial`/`stub`, and the evidence
gate only for `done`/`pass`, so `{"unit": "X", "status": "recovered"}` linted clean.

| code | fires when |
|---|---|
| `E_MISSING_KEY` | any of `unit, status, artifacts, evidence, blocker, next_unit_hint, write_paths` absent |
| `E_ARTIFACT_ABSENT` | a listed artifact does not exist (path reported verbatim) |
| `E_RECOVERED_NO_EVIDENCE` | `evidence` empty/absent, **or** no `recovery` block |
| `E_RECOVERED_NO_PROVENANCE` | `recovery` missing `from_stub_sha256` and/or `evidence_basis` |
| `E_STUB` | `recovered` with no artifacts **and** no evidence (it is still a stub) |

`E_STUB` does not fire on a recovered record whose evidence and artifacts are present. `partial`,
`stub`, `done` and `pass` behave exactly as before.

**Exit codes.** Every invocation returns 0 (clean), 1 (any `E_*`), or 2 (usage/IO). `exit_code_for()`
derives 0/1 from the summary and the `__main__` wrapper normalises anything else to 2 — a `None` or
missing exit code is itself a defect, not an allowance.

**Corpus effect (measured, 2026-10-26).** Eight records under `orchestration/handoffs/recovered/`
all lint clean and exit 0; they add **zero** `E_*`. Before → after over
`orchestration/handoffs/*.json`: `E_PARSE 0→0`, `E_SHAPE 0→0`, `E_MISSING_KEY 34→34`,
`E_ARTIFACT_ABSENT 75→75`, `E_DONE_NO_EVIDENCE 4→4`, `E_DONE_NO_ARTIFACTS 3→3`, `E_STUB 16→16`;
the two new codes are 0→0. The only delta is `W_NO_COMMANDS 182→183`, from a concurrently written
handoff outside this unit's scope, and the file count grew 959→962 for the same reason plus this
unit's own handoff.
