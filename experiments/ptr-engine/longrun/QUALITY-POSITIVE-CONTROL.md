# QUALITY-POSITIVE-CONTROL — can the quality path ever say yes?

**Verdict: PATH-CANNOT-SAY-YES.** Zero requests, zero network. Fixture
`experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json`
(sha256 `07abab0bd902bd88c86b8d2544f012caf63a9a4280b68b223bd605d399bd3e0b`),
source rows `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl`
(arm `pointer-stable`, 48 turns, read-only, copied to `/tmp/qpc/`).

## Why no log can pass both the fixture's contract and the scorer

`LR-01.v3.json` sets `"answer_marker": {"line_regex": "^ANSWER:[ ]*\\S.*$", "required": true}` —
the v3 runtime contract requires a checkpoint answer to end with an `ANSWER: <value>` line.
`score_longrun.py` never reads `answer_marker` (grep: 0 hits in `score_longrun.py` and
`grade_v2.py`), and all three `checkpoints[]` carry **no `match` key**, so
`score_longrun.py:814` defaults them to `mode = "exact"`, and `score_longrun.py:174-176`
compares the **entire turn content** to the expected string:

```python
    if mode == "exact":
        if ignore_case:
            return text.lower() == want.lower()
        return text == want
```

The mirror checks `acc.cp1..acc.cp3` and `acc.1` are the same `kind: fact`, `match: exact`,
same turns. So a checkpoint turn that satisfies the fixture's required marker
(any prose + `ANSWER: 64`) can never equal `"64"`.

Conversely `grade_v2.py` requires prose: `v2_numeric` needs a line ending in `. ! ? )`
carrying the number (`GRADE-V2 R1b`), so the only content `score_longrun.py` accepts
(`"64"`) fails `grade_v2`. **The two graders are mutually exclusive**, shown below by
`pos-exact-only`.

## Truth table (`score_longrun.py` FIXTURE RUN, arm `pointer-stable`)

| log | verified_success | checkpoint_accuracy | tokens_to_verified_success | false_claims | exit | flipped checks |
|---|---|---|---|---|---|---|
| `pos-full` | **false** | 0/3 | null | 0 | 1 | `cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1` — all `kind=fact`, exact |
| `neg-one` | false | 0/3 | null | 0 | 1 | identical 7 (indistinguishable from pos-full) |
| `neg-marker` | false | 0/3 | null | 0 | 1 | identical 7 (marker not read at all) |
| `neg-truncated` | false | 0/3 | null | 0 | 1 | identical 7 |
| `pos-exact-only` (diagnostic) | **true** | 3/3 | 22396 | 0 | 0 | — |

`pos-full` is exactly the log the card specifies: real 48 turns, real prose kept, correct
values appended both standalone and after `ANSWER:` (`ANSWER: 64` t12, `ANSWER: 31` t24,
`ANSWER: ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising`
t46), repair literal `restore the typed guard deleted at turn 8` at t30 (window 30-33),
turn-48 log facts satisfying `acc.2`/`acc.3`/`acc.4` (`test_scope.py`, `test_negative_controls.py`,
`exit 0`, `PtrNotAReferenceError`, `PTR_NOT_A_REFERENCE`, `ledger`, `def test_`, `9`), zero
constraint hits, `fixture_file` digest match, all 48 turns present. It still fails, on
**`cp.t12` (kind `fact`, turn 12, expected `"64"`, found the prose+`ANSWER: 64` turn)**.
`tokens_to_verified_success` is `null` on every false row because the metric is only computed
inside the `verified` branch (`score_longrun.py:917-924`) — it is undefined, not zero.

## `grade_v2.py` side (exit code always 0; it prints accuracy, no binary verdict)

`grade_v2.py --rows <log> --fixture <v3 fixture> --out /tmp/qpc/<log>.grade-v2.json`

| log | old acc | new acc (v2) | v2 new failures |
|---|---|---|---|
| `pos-full` | 3/10 | 10/10 | none |
| `neg-one` | 3/10 | 7/10 | `cp.t12`, `acc.cp1`, `acc.1` (correct — R1a bites) |
| `neg-marker` | 3/10 | **10/10** | none — a wrong `ANSWER:` line is invisible to v2 |
| `neg-truncated` | 3/10 | **10/10** | none — mid-line truncation is invisible at t46 |
| `pos-exact-only` | 10/10 | **3/10** | all 7 — v2 rejects the only shape the scorer accepts |

So on `score_longrun.py` the negative controls fail for **one shared reason** (exact match),
not the three distinct reasons the card predicts: a wrong value, a wrong marker and a
truncated answer are all reported with the same seven check ids. `grade_v2.py` is
*too lenient* on `neg-marker` and `neg-truncated` (10/10) and *incompatible* with the
primary scorer.

## Consequence

The 0/3, `verified_success: false` record on every real arm is **not evidence about the
model**. The instrument cannot return yes on a log that follows the fixture's own answer
contract, so no live spend can ever produce a pass through this path. The fix is a fixture
or grader change (checkpoint `match: "contains"` on the marker line, or splitting the turn
into a structured `answers` field the scorer reads) — a decision for the owner, not a patch
made here.

## Reproduce

```
python3 /tmp/qpc/build.py    # writes /tmp/qpc/*.jsonl and runs both graders
python3 longrun/score_longrun.py longrun/tasks-v3/runtime-v3/LR-01.v3.json /tmp/qpc/pos-full.jsonl
python3 longrun/grade_v2.py --rows /tmp/qpc/pos-full.jsonl --fixture longrun/tasks-v3/runtime-v3/LR-01.v3.json --out /tmp/qpc/g2.json
```

Requests sent: **0**. Graders, fixture, plan and row file unmodified.

## Durability note

This session's sandbox gives every shell invocation a private `/tmp`, so `/tmp/qpc/*.jsonl` did not
survive the call that produced them; the truth table above is the output of that single call (build +
both graders in one invocation). Recreate the whole control, including both graders' output, with the
builder below: save as `/tmp/qpc/build.py` and `python3 /tmp/qpc/build.py` in one call.

```python
import json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path('/home/zer0null/reserach extarctor/experiments/ptr-engine')
FIX=ROOT/'longrun/tasks-v3/runtime-v3/LR-01.v3.json'
FSHA=hashlib.sha256(FIX.read_bytes()).hexdigest()
rows=[json.loads(l) for l in (ROOT/'measure/rows-longrun-c-2026-10-26.jsonl').read_text().splitlines() if l.strip()]
ARM='pointer-stable'
base=sorted([r for r in rows if r['arm']==ARM],key=lambda r:int(r['turn']))
EXP46='ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising'
REPAIR='restore the typed guard deleted at turn 8'
T12=("The default per-turn resolve budget in refs is 64. "
 "DEFAULT_MAX_REFS == 64 in resolve.py#L39, so the per-turn resolve budget is 64.")
T24="errors.py defines 31 Ptr* error classes across its body."
T30="Correction: "+REPAIR+" so the isinstance guards fall inside the recorded block."
T46="_refuse calls "+EXP46+"."
T48=("Verified with pytest: test_scope.py and test_negative_controls.py both reported exit 0. "
 "The refusal row is PtrNotAReferenceError with code PTR_NOT_A_REFERENCE and exactly one ledger row. "
 "grep -c '^def test_' test_scope.py still reports 9. "
 "ANSWER: all acceptance checks pass, exit 0")

def mk(name,tweak):
    out=[]
    for r in base:
        r=dict(r); t=int(r['turn']); r['fixture_sha256']=FSHA
        c=r['content']
        if t==12: c=c+"\n\n"+T12+"\nANSWER: 64"
        elif t==24: c=c+"\n\n"+T24+"\nANSWER: 31"
        elif t==30: c=c+"\n\n"+T30+"\nGuard restored: "+REPAIR
        elif t==46: c=c+"\n\n"+T46+"\nANSWER: "+EXP46
        elif t==48: c=T48
        r['content']=c; tweak(t,r); out.append(r)
    p=Path('/tmp/qpc')/name
    p.write_text("\n".join(json.dumps(r) for r in out)+"\n"); return p

def noop(t,r): pass
def neg_one(t,r):
    if t==12: r['content']=r['content'].replace('budget in refs is 64','budget in refs is 65').replace('== 64','== 65').replace('budget is 64.','budget is 65.').replace('ANSWER: 64','ANSWER: 65')
def neg_marker(t,r):
    if t==12: r['content']=r['content'].replace('ANSWER: 64','ANSWER: NOT-AN-ANSWER')
def neg_trunc(t,r):
    if t==46:
        r['content']=r['content'][:r['content'].index('ANSWER: ')+len('ANSWER: ')+len(EXP46)-14]
        r['finish_reason']='length'; r['truncated']='True'
def exact(t,r):
    if t==12: r['content']='64'
    elif t==24: r['content']='31'
    elif t==46: r['content']=EXP46
    elif t==48: r['content']=T48

logs={'pos-full.jsonl':noop,'neg-one.jsonl':neg_one,'neg-marker.jsonl':neg_marker,
      'neg-truncated.jsonl':neg_trunc,'pos-exact-only.jsonl':exact}
for name,f in logs.items(): mk(name,f)
SC=ROOT/'longrun/score_longrun.py'; GV=ROOT/'longrun/grade_v2.py'
for name in logs:
    log=Path('/tmp/qpc')/name
    p=subprocess.run([sys.executable,str(SC),str(FIX),str(log)],capture_output=True,text=True)
    card=json.loads(p.stdout)
    print(name,'score_longrun exit',p.returncode,'verified',card['verified_success'],
          'acc',card['checkpoint_accuracy'],'tokens',card['tokens_to_verified_success'],
          'failed',card['failed_required'])
    g=subprocess.run([sys.executable,str(GV),'--rows',str(log),'--fixture',str(FIX),
                      '--out','/tmp/qpc/%s.grade-v2.json'%name],capture_output=True,text=True)
    print(g.stdout)

```
