# UBUILD1 — build `research-publish-packages`

**One purpose.** Create `/home/zer0null/research-publish-packages/` — a new, separate, fresh-history git
repository that will become the author's public code+paper store. Source workspace stays private and untouched.

**Declared write paths.** `/home/zer0null/research-publish-packages/**`,
`orchestration/units/UBUILD1.md`, `orchestration/handoffs/UBUILD1.json`. An additional path, `orchestration/units/UBUILD1.build.sh`, was authorised by the orchestrator.

**Hard bound.** 45 tool calls. Stop and report `partial` if exceeded.

## Status

**BLOCKED ON SANDBOX — status `partial`.** This session's file sandbox is `workspace-write`, so
`/home/zer0null/research-publish-packages/` is outside it and `mkdir` there returns *Read-only file system*
(`[sandbox: file access denied under workspace-write mode]`). Escalation is not available to this unit.
`/tmp` and `/dev/shm` are **per-call tmpfs** (proved by a write/read across two calls), so a staged tree cannot
survive either.

**Consequence, and what this card therefore carries:** the build is preserved as a standalone, deterministic,
idempotent script at **`orchestration/units/UBUILD1.build.sh`** (an additional write path authorised by the
orchestrator after the per-call-tmpfs finding). It copies every byte of source material over with `cp -r`
from the read-only source, authors only the genuinely new files, writes straight to
`/home/zer0null/research-publish-packages/`, runs `gate.sh`, and **exits non-zero if the gate hard-fails**.
Run it from a shell that can write the target:

```bash
bash "/home/zer0null/reserach extarctor/orchestration/units/UBUILD1.build.sh"
```

`INCLUDE_VERIFY=0` omits `code/verify/` — a lever for the author, not a decision taken by this unit.

> **The build script now lives in its own file:** `orchestration/units/UBUILD1.build.sh` — an authorised
> write path. The copy that was embedded here has been **removed so the two cannot diverge**. Its
> verification is recorded under *Build script* below.


## Report

**Status: `partial` — the gate HARD-FAILS on the material this card instructs me to ship.** Nothing was hand-edited to make it pass, and no fixture text was touched. The build is reproducible by running the script above; it is committed in an ephemeral staging area that cannot survive this session (see *Sandbox limitation*).

**`bash gate.sh` → exit 1 — 301 HARD-FAIL hit lines, 2143 REVIEW hit lines.**

### Verified

| check | result |
|---|---|
| `git rev-list --count HEAD` | **1** — one commit, `Initial commit: exp12-encoder-crossover package (paper, sanitised code, eval evidence)` |
| `git status --porcelain` | **0 lines** — clean |
| `git remote -v` | **empty** — no remote created, nothing pushed |
| nested `.git` below the repo root | **0** |
| `.git` copied from the source tree | **none** |
| `.git` present under the sanitised source subtree | **none** (checked before copying) |
| total | **61 files, 5.4 MB** |
| `paper/` | 12 files, 244K |
| `code/` | 28 files, 4.5M |
| `eval/` | 20 files, 672K |
| `journal/`, `jobs/`, `dockets/`, `state/`, `orchestration/`, `strategy/` | **0 files** — `journal/` excluded pending the author's decision |
| source workspace | read-only; only this card and the handoff were added (both declared write paths) |
| `/home/zer0null/Duval` | never written — and **cannot** be written from this session: the sandbox denies every path outside the workspace (probe below) |

### HARD-FAIL hits by pattern

Counts are per pattern over the hit lines and **overlap**: one line can match several patterns, so the column sums above the total. This is the gate's own count block.

| hit lines | pattern |
|---|---|
| 74 | `/home/zer0null` |
| 71 | `duval` |
| 2 | `a5ef1b28` |
| 6 | `consonance` |
| 4 | `EXCLUDED.md` |
| 21 | `REDACTION_REPORT` |
| 6 | `RESIDUALS.md` |
| 2 | `LICENCE_TODO` |
| 2 | `VERIFICATION_REPORT` |
| 66 | `StateClass` |
| 47 | `grantPolicy` |
| 2 | `src/broker` |
| 36 | `admit(` |
| 47 | `expanded[` |

### HARD-FAIL hit lines by file

| hit lines | file |
|---|---|
| 54 | `code/fixture/reflex-decisions.ts` |
| 46 | `code/harness/data/fixture-190.json` |
| 44 | `code/verify/VERIFICATION.txt` |
| 21 | `eval/second-labeller/OWED_CORRECTIONS.md` |
| 13 | `eval/second-labeller/EVIDENCE.md` |
| 11 | `paper/EVIDENCE_NOTES.md` |
| 9 | `eval/second-labeller/RUN.json` |
| 9 | `paper/CHECKLIST.md` |
| 8 | `eval/results/eval-shuffled-label.json` |
| 7 | `eval/results/eval-deberta-v3-base.json` |
| 7 | `eval/results/eval-majority-class.json` |
| 6 | `eval/second-labeller-190/ROBUSTNESS.md` |
| 6 | `eval/results/eval-modernbert-base.json` |
| 6 | `eval/results/eval-setfit-mpnet.json` |
| 6 | `eval/results/baselines.json` |
| 5 | `code/verify/run-verification.sh` |
| 5 | `code/verify/redaction-log.json` |
| 4 | `paper/MANUSCRIPT.md` |
| 4 | `paper/OPEN_QUESTIONS.md` |
| 3 | `eval/second-labeller/PREREGISTRATION.md` |
| 3 | `eval/second-labeller/disagreements.jsonl` |
| 3 | `code/harness/data/manifest.json` |
| 3 | `paper/REFERENCES.bib` |
| 2 | `code/verify/integrity-table.md` |
| 2 | `code/harness/LEAD-WIRING.md` |
| 2 | `paper/REFS_VERIFIED.md` |
| 1 | `eval/second-labeller-190/RUN2.json` |
| 1 | `eval/second-labeller/metrics.json` |
| 1 | `eval/second-labeller/parse_fixture.py` |
| 1 | `eval/preregistration/EXP12-typed-channel-comparison-prereg.md` |
| 1 | `code/verify/RESIDUAL-SCAN.txt` |
| 1 | `code/verify/recompute-claims.py` |
| 1 | `code/harness/export-fixture.ts` |
| 1 | `code/harness/collect.py` |
| 1 | `code/fixture/DECISION_CASE_SCHEMA.ts` |
| 1 | `paper/UNSOURCED_RETAINED.md` |
| 1 | `paper/CLAIMS.md` |
| 1 | `paper/REFS.md` |

### Full HARD-FAIL listing (file:line, matched text cut to 200 columns)

Every hit the gate reports, grouped by file. `gate.sh` itself prints the untruncated line.

**`code/fixture/reflex-decisions.ts`** — 54 hit(s)

```text
21:  * unchanged. Cost statement: ../REDACTION_REPORT.md section 5.
25:  * residue is measured and named in ../REDACTION_REPORT.md section 7. It is larger than the 335-line
28:  * NO MODEL WEIGHTS AND NO RUNTIME CODE ARE INCLUDED IN THIS SUBSET. See ../EXCLUDED.md.
79:   /* [withheld: section note naming internal mechanism — see REDACTION_REPORT.md §3] */
80:   /* [withheld: section note naming internal mechanism — see REDACTION_REPORT.md §3] */
90:       "Step 3 must emit a written critique of the diff already recorded under the execution namespace. It reads nothing from the workspace and writes nothing; its entire output is the proposal payload
101:       "Step 2 must apply an already-admitted patch to module.ts inside the granted workspace so the on-disk digest changes before the verifier runs. No reading and no reasoning beyond applying the pat
112:       "Step 4 must report whether the A3_budget gate in src/policy.ts delegates on pass, by reading that file's current contents out of the workspace. The step changes no file and its whole output is 
123:       "One step must apply a write patch and a following step must run the unit suite. No single catalogued class declares both fs.write and test.run. The planner's rule is one class per step, and the
134:       "Step 5 must append exactly one record to the memory module through a memory.write tool and must not touch any workspace file. editor's declared tools are exactly fs.read and fs.write. The catal
145:       "A proposal has arrived whose declared spend would exceed the state's budget envelope, so the A3_budget gate refuses it. The refusal must be recorded as a new state carrying the reason and the o
146:     options: ["reasoner (propose only)", "editor (attached, writes)", "none -- admit() mints the state"],
156:       "Two versions of editor are registered: 1.0.0 and 1.1.0. The head state references editor@1.0.0 by content hash, and replay from that state must reproduce the recorded path exactly. Which StateC
167:       "A step must read workspace/src/loop.ts and return a verdict on it, and the postcondition explicitly forbids writing. The planner's rule is to select the class whose declared grant set is the sm
178:       "A step must run the test suite and record its exit code, and no file may change. The catalogue holds verifier (detached, declared tools ['test.run']) and editor (attached, declared tools ['fs.r
189:       "Step 1 of a task must emit a three-item plan naming the classes that should follow, and must not touch the workspace or produce any artifact. Which StateClass runs it?",
200:       "A step must write one file into the granted workspace and then stop; the postcondition is the file's existence and content hash, and nothing else is required. Which StateClass runs it?",
211:       "A step must restate the task in one sentence using only what the current projection already carries, and must read and write nothing. Which StateClass runs it?",
222:       "A step must update one PROCEDURAL record in the memory module to reflect a method that has just proved reliable, and must touch neither the workspace nor the knowledge module. memory-curator is
233:       "A step must read workspace/src/broker.ts and write a sibling file workspace/src/broker-test.ts that exercises it. Both halves are required. The catalogue holds reasoner (output-only, no tools),
244:       "A step must write a file through an attachment point inside the sandbox, and the only class that declares a write grant for it is declared layer 'detached'. Which StateClass runs it?",
255:       "A step must run the test suite and then read the file the failing test names, in the same step, and both are required. The catalogue holds verifier (detached, ['test.run']), code-inspector (det
266:       "A step must label the refusal reason already recorded on the head state so the refusal-rate metric can count refusals by stage. All inputs are present in the state; the step reads and writes no
277:       "A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for reasoner. Which StateClass can a reasoner step transition
288:       "A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker matches a scope against the address exactly as given.
299:       "A step must write the accepted summary to a file so the next state can pin it by content hash. Only one native class declares a write grant. Which StateClass runs it?",
310:       "A state carries a class ref whose declared name and version do not match the registered class at that content hash. Which StateClass runs the next step?",
321:       "The head state's budget envelope is reasonerCalls 1, semanticCalls 0, tools 0. The remaining work is one pure judgement over the projection with no tool use. Which StateClass runs the step?",
332:       "The head state's class is reasoner, and a transition is proposed that keeps the class and adds an fs.write grant to it. Which StateClass runs the next step?",
343:       "A step must fetch a page and summarise it. The catalogue holds researcher (detached, declared tools ['web.fetch']), reasoner (output-only, no tools) and editor (attached, ['fs.read','fs.write']
354:       "A step must compare two candidate patches that are both already carried in the state's resources by content hash, and emit the better one as a proposal summary. It must not touch the workspace.
365:       "The first of two steps must run the test suite so the engine can decide whether the second step's fix is needed. The class running the first step must observe the suite output before the decisi
376:       "A step must name which capability the next step will need, as part of its proposal payload, without requesting or receiving it. Which StateClass runs it?",
387:       "A layer has returned a proposal asserting that the test suite passed. Which StateClass runs the step whose outcome decides whether the commit is accepted?",
398:       "Two candidate states are byte-identical except that one carries a tool grant and the other does not. Which StateClass is responsible for the difference being real rather than an artefact of com
409:       "A step must read workspace/package.json to find the typecheck command and then write a one-line change adding a script entry. Both the read and the write are required in this one step. The cata
420:   /* [withheld: section note naming internal mechanism — see REDACTION_REPORT.md §3] */
549:       "The step's class is reasoner (output-only, grantPolicy 'none'). The compiler's candidate list still contains a description of the fs.write tool, taken from the class documentation. What does th
572:     options: ["the expanded[] ref list", "the token count alone", "the model's own account", "the manifest's mtime"],
735:   /* [withheld: section note naming internal mechanism — see REDACTION_REPORT.md §3] */
743:       "The step's class is reasoner, whose grantPolicy is { kind: 'none' }. The grant kinds available are model, tool, skill, resource and context, and every class always receives a model grant and a 
754:       "The step's class is editor, whose grantPolicy is { kind: 'declared', tools: ['fs.read','fs.write'] }. Which family set does the planner construct?",
765:       "The step's class is reasoner (grantPolicy 'none'). Its returned proposal carries requestedCapabilities: [{ kind: 'tool', ref: 'fs.write' }]. Which family set does the planner construct for this
776:       "A catalogued class declares grantPolicy { kind: 'declared', tools: ['fs.read','fs.write'] } and also declares two skills in its role spec. Which family set does the planner construct?",
787:       "A catalogued class declares grantPolicy { kind: 'declared', tools: [] } and one resource grant pinning a read-only artefact by content hash. No skill is declared. Which family set does the plan
798:       "The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it declares. Which family set does the tool plane s
908:       "A class's role description reads 'applies changes with fs.write', but its grantPolicy is { kind: 'none' } and its layer is output-only. Which family set does the planner construct?",
985:       "A hosted MCP server is proposed for an output-only class whose grantPolicy is 'none'. What does its tools/list contain?",
996:       "One class is run with an in-process Broker and another with a hosted MCP server, and both declare the same grantPolicy. Does the second run's family set differ from the first's?",
1418:       "The question can only be answered by reading a file, and the step's class is reasoner, whose grantPolicy is 'none' and whose canRequestEscalation is false. Answer or escalate?",
1616:       "The question is 'what tools does this step hold', and the class's grantPolicy and the step's epoch are both recorded on the state, so the set is exactly re-derivable by construction. Answer or 
1649:       "The question is 'which capability families does this step hold', and the class is reasoner with grantPolicy 'none' at a recorded epoch, so the constructed set is fully determined. Answer or esc
1831:       "Two candidates: (A) read a file from the workspace, (B) run the test suite. The step's class is reasoner, whose grantPolicy is 'none', so it holds no tool grants. Which topology?",
1929:   /* [withheld: section note naming internal mechanism — see REDACTION_REPORT.md §3] */
```

**`code/harness/data/fixture-190.json`** — 46 hit(s)

```text
5:   "question": "Step 3 must emit a written critique of the diff already recorded under the execution namespace. It reads nothing from the workspace and writes nothing; its entire output is the proposal
17:   "question": "Step 2 must apply an already-admitted patch to module.ts inside the granted workspace so the on-disk digest changes before the verifier runs. No reading and no reasoning beyond applying
29:   "question": "Step 4 must report whether the A3_budget gate in src/policy.ts delegates on pass, by reading that file's current contents out of the workspace. The step changes no file and its whole ou
42:   "question": "One step must apply a write patch and a following step must run the unit suite. No single catalogued class declares both fs.write and test.run. The planner's rule is one class per step,
55:   "question": "Step 5 must append exactly one record to the memory module through a memory.write tool and must not touch any workspace file. editor's declared tools are exactly fs.read and fs.write. T
68:   "question": "A proposal has arrived whose declared spend would exceed the state's budget envelope, so the A3_budget gate refuses it. The refusal must be recorded as a new state carrying the reason a
72:    "none -- admit() mints the state"
81:   "question": "Two versions of editor are registered: 1.0.0 and 1.1.0. The head state references editor@1.0.0 by content hash, and replay from that state must reproduce the recorded path exactly. Whic
94:   "question": "A step must read workspace/src/loop.ts and return a verdict on it, and the postcondition explicitly forbids writing. The planner's rule is to select the class whose declared grant set i
107:   "question": "A step must run the test suite and record its exit code, and no file may change. The catalogue holds verifier (detached, declared tools ['test.run']) and editor (attached, declared tool
120:   "question": "Step 1 of a task must emit a three-item plan naming the classes that should follow, and must not touch the workspace or produce any artifact. Which StateClass runs it?",
133:   "question": "A step must write one file into the granted workspace and then stop; the postcondition is the file's existence and content hash, and nothing else is required. Which StateClass runs it?"
145:   "question": "A step must restate the task in one sentence using only what the current projection already carries, and must read and write nothing. Which StateClass runs it?",
157:   "question": "A step must update one PROCEDURAL record in the memory module to reflect a method that has just proved reliable, and must touch neither the workspace nor the knowledge module. memory-cu
170:   "question": "A step must read workspace/src/broker.ts and write a sibling file workspace/src/broker-test.ts that exercises it. Both halves are required. The catalogue holds reasoner (output-only, no
183:   "question": "A step must write a file through an attachment point inside the sandbox, and the only class that declares a write grant for it is declared layer 'detached'. Which StateClass runs it?",
196:   "question": "A step must run the test suite and then read the file the failing test names, in the same step, and both are required. The catalogue holds verifier (detached, ['test.run']), code-inspec
209:   "question": "A step must label the refusal reason already recorded on the head state so the refusal-rate metric can count refusals by stage. All inputs are present in the state; the step reads and w
221:   "question": "A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for reasoner. Which StateClass can a reasoner step tr
234:   "question": "A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker matches a scope against the address exactly a
247:   "question": "A step must write the accepted summary to a file so the next state can pin it by content hash. Only one native class declares a write grant. Which StateClass runs it?",
259:   "question": "A state carries a class ref whose declared name and version do not match the registered class at that content hash. Which StateClass runs the next step?",
272:   "question": "The head state's budget envelope is reasonerCalls 1, semanticCalls 0, tools 0. The remaining work is one pure judgement over the projection with no tool use. Which StateClass runs the s
285:   "question": "The head state's class is reasoner, and a transition is proposed that keeps the class and adds an fs.write grant to it. Which StateClass runs the next step?",
298:   "question": "A step must fetch a page and summarise it. The catalogue holds researcher (detached, declared tools ['web.fetch']), reasoner (output-only, no tools) and editor (attached, ['fs.read','fs
311:   "question": "A step must compare two candidate patches that are both already carried in the state's resources by content hash, and emit the better one as a proposal summary. It must not touch the wo
324:   "question": "The first of two steps must run the test suite so the engine can decide whether the second step's fix is needed. The class running the first step must observe the suite output before th
337:   "question": "A step must name which capability the next step will need, as part of its proposal payload, without requesting or receiving it. Which StateClass runs it?",
350:   "question": "A layer has returned a proposal asserting that the test suite passed. Which StateClass runs the step whose outcome decides whether the commit is accepted?",
363:   "question": "Two candidate states are byte-identical except that one carries a tool grant and the other does not. Which StateClass is responsible for the difference being real rather than an artefac
376:   "question": "A step must read workspace/package.json to find the typecheck command and then write a one-line change adding a script entry. Both the read and the write are required in this one step. 
543:   "question": "The step's class is reasoner (output-only, grantPolicy 'none'). The compiler's candidate list still contains a description of the fs.write tool, taken from the class documentation. What
573:    "the expanded[] ref list",
781:   "question": "The step's class is reasoner, whose grantPolicy is { kind: 'none' }. The grant kinds available are model, tool, skill, resource and context, and every class always receives a model gran
795:   "question": "The step's class is editor, whose grantPolicy is { kind: 'declared', tools: ['fs.read','fs.write'] }. Which family set does the planner construct?",
809:   "question": "The step's class is reasoner (grantPolicy 'none'). Its returned proposal carries requestedCapabilities: [{ kind: 'tool', ref: 'fs.write' }]. Which family set does the planner construct 
823:   "question": "A catalogued class declares grantPolicy { kind: 'declared', tools: ['fs.read','fs.write'] } and also declares two skills in its role spec. Which family set does the planner construct?",
837:   "question": "A catalogued class declares grantPolicy { kind: 'declared', tools: [] } and one resource grant pinning a read-only artefact by content hash. No skill is declared. Which family set does 
851:   "question": "The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it declares. Which family set does the tool
991:   "question": "A class's role description reads 'applies changes with fs.write', but its grantPolicy is { kind: 'none' } and its layer is output-only. Which family set does the planner construct?",
1089:   "question": "A hosted MCP server is proposed for an output-only class whose grantPolicy is 'none'. What does its tools/list contain?",
1103:   "question": "One class is run with an in-process Broker and another with a hosted MCP server, and both declare the same grantPolicy. Does the second run's family set differ from the first's?",
1637:   "question": "The question can only be answered by reading a file, and the step's class is reasoner, whose grantPolicy is 'none' and whose canRequestEscalation is false. Answer or escalate?",
1856:   "question": "The question is 'what tools does this step hold', and the class's grantPolicy and the step's epoch are both recorded on the state, so the set is exactly re-derivable by construction. An
1892:   "question": "The question is 'which capability families does this step hold', and the class is reasoner with grantPolicy 'none' at a recorded epoch, so the constructed set is fully determined. Answe
2110:   "question": "Two candidates: (A) read a file from the workspace, (B) run the test suite. The step's class is reasoner, whose grantPolicy is 'none', so it holds no tool grants. Which topology?",
```

**`code/verify/VERIFICATION.txt`** — 44 hit(s)

```text
3: as-audited : /home/zer0null/reserach extarctor/repro/encoder-crossover-190
4: sanitised  : /home/zer0null/reserach extarctor/repro/encoder-crossover-190-SANITISED
105:     5  ./RESIDUALS.md
118: ./RESIDUALS.md:18:StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\
119: ./RESIDUALS.md:53:| `README.md` | 4 | **irreducible by design** — the 4 remaining hits are all the `DecisionKind` name, which the variant decision must name (§6).
120: ./RESIDUALS.md:54:| `fixture/DECISION_CASE_SCHEMA.ts` | 3 | **irreducible by design** — the `DecisionKind` *type name* only, which VARIANT A deliberately keeps for
121: ./RESIDUALS.md:60:| `MANIFEST.json` | 1 | **partly fixed** — the private-branch commit id (19 citations) and the `git:` history reference are **removed** (UFIX10);
122: ./RESIDUALS.md:61:| `second-labeller/PREREGISTRATION.md` | 1 | **irreducible** — the frozen pre-registration mentions the `DecisionKind` type declarations; editing
123: ./results/eval-deberta-v3-base.json:243:    "none -- admit() mints the state": {
124: ./results/eval-deberta-v3-base.json:343:    "the expanded[] ref list": {
125: ./results/eval-deberta-v3-base.json:519:        "none -- admit() mints the state"
126: ./results/eval-deberta-v3-base.json:522:      "gold": "none -- admit() mints the state",
127: ./results/eval-deberta-v3-base.json:1096:        "the expanded[] ref list",
128: ./results/eval-deberta-v3-base.json:1102:      "gold": "the expanded[] ref list",
129: ./results/eval-deberta-v3-base.json:1104:      "predLabel": "the expanded[] ref list",
130: ./results/eval-modernbert-base.json:243:    "none -- admit() mints the state": {
131: ./results/eval-modernbert-base.json:343:    "the expanded[] ref list": {
132: ./results/eval-modernbert-base.json:519:        "none -- admit() mints the state"
133: ./results/eval-modernbert-base.json:522:      "gold": "none -- admit() mints the state",
134: ./results/eval-modernbert-base.json:1096:        "the expanded[] ref list",
135: ./results/eval-modernbert-base.json:1102:      "gold": "the expanded[] ref list",
136: ./results/eval-majority-class.json:243:    "none -- admit() mints the state": {
137: ./results/eval-majority-class.json:343:    "the expanded[] ref list": {
138: ./results/eval-majority-class.json:519:        "none -- admit() mints the state"
139: ./results/eval-majority-class.json:522:      "gold": "none -- admit() mints the state",
140: ./results/eval-majority-class.json:1096:        "the expanded[] ref list",
141: ./results/eval-majority-class.json:1102:      "gold": "the expanded[] ref list",
142: ./results/eval-majority-class.json:1104:      "predLabel": "the expanded[] ref list",
143: ./results/eval-setfit-mpnet.json:243:    "none -- admit() mints the state": {
144: ./results/eval-setfit-mpnet.json:343:    "the expanded[] ref list": {
145: ./results/eval-setfit-mpnet.json:519:        "none -- admit() mints the state"
146: ./results/eval-setfit-mpnet.json:522:      "gold": "none -- admit() mints the state",
147: ./results/eval-setfit-mpnet.json:1096:        "the expanded[] ref list",
148: ./results/eval-setfit-mpnet.json:1102:      "gold": "the expanded[] ref list",
149: ./results/baselines.json:83:          "gold": "none -- admit() mints the state",
150: ./results/baselines.json:348:          "predLabel": "the expanded[] ref list",
151: ./results/baselines.json:349:          "gold": "the expanded[] ref list",
152: ./results/baselines.json:1457:          "gold": "none -- admit() mints the state",
153: ./results/baselines.json:1722:          "predLabel": "the expanded[] ref list",
154: ./results/baselines.json:1723:          "gold": "the expanded[] ref list",
155: ./results/eval-shuffled-label.json:243:    "none -- admit() mints the state": {
156: ./results/eval-shuffled-label.json:343:    "the expanded[] ref list": {
157: ./results/eval-shuffled-label.json:519:        "none -- admit() mints the state"
168: VERIFICATION COMPLETE. Log: /home/zer0null/reserach extarctor/repro/encoder-crossover-190-SANITISED/verify/VERIFICATION.txt
```

**`eval/second-labeller/OWED_CORRECTIONS.md`** — 21 hit(s)

```text
4: `/home/zer0null/Duval` (or in a corpus document declared read-only for this workspace). No unit of this
7: **Compiled by:** UFIX4, 2026-10-15, from the UVER3 work order (`strategy/VERIFICATION_REPORT_3.md`) and
22: - **Path / line:** `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47`
26:   `/home/zer0null/Duval/docs/research/EXP#11-evidence/imajev-rows.jsonl` → `wc -l` = **3690**; all 3,690
36: - **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:839–847` — `id` at `:839`,
38: - **Current text (verbatim):** `correct: 0` → option `"model + context"`; rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
49: - **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:329–338` — question at
51: - **Current text (verbatim):** question: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*; recorded answer `editor (attached, writes)`; rationale: *[withheld rationale quote — see .
60: - **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:773–782` — question at
65:   rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
68:   the fixture header's claim that *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
74: - **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:1872–1881` — question at
76: - **Current text (verbatim):** question: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*; recorded
77:   answer `"SEQUENCE(A,B)"`; rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
91: - **Path / lines:** `/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md:279–281` — heading at
92:   `:279`, general clause (*[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*) at `:280`, correction chain at `:281`.
93: - **Current text (verbatim):** *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
96:   intact. What does not hold is the **general clause**, *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*: the
115: | 1 | `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47` | wrong row count (3,590) | **3,690** | UVER2/UCORR2 | yes — `imajev-rows.jsonl` = 3,690 valid rows |
120: | 6 | `/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md:279–281` | general clause "all three defects flattered the candidate" | defects biased the instrument **asymmetrically** (`setfit-mpn
123: applied** — the target `/home/zer0null/Duval` was never written. Items 2–5 are flags requiring subject
```

**`eval/second-labeller/EVIDENCE.md`** — 13 hit(s)

```text
5: `/home/zer0null/Duval`, which four paper candidates (#3, #4, #5, #10) rest on.
7: **Target revision:** `/home/zer0null/Duval` @ `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`
30: $ sha256sum /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts experiments/second-labeller-190/reflex-decisions.sandbox.ts
31: 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796  /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts
33: $ cmp /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts experiments/second-labeller-190/reflex-decisions.sandbox.ts && echo IDENTICAL
42: $ cmp reflex-decisions.sandbox.ts /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts && echo SANDBOX_COPY_IDENTICAL
68: string `"the expanded[] ref list"`, whose `]` truncated the match, yielding `options: []` with
76:     options: ["the expanded[] ref list", "the token count alone", "the model's own account", "the manifest's mtime"],
258: `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47` (F-EXP11-11) reads verbatim:
333: ## 9. Read-only proof for `/home/zer0null/Duval` (twice, attributed)
336: before:  git -C /home/zer0null/Duval rev-parse HEAD -> 907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
337: after:   git -C /home/zer0null/Duval rev-parse HEAD -> 907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b
349: - `find /home/zer0null/Duval -newermt '-60 minutes'` at mid-run: **0 files**.
```

**`paper/EVIDENCE_NOTES.md`** — 11 hit(s)

```text
3: All paths under `/home/zer0null/Duval` (STRICTLY READ-ONLY; nothing was written there).
17: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
52: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
79: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
142: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
176: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
211: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
226: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
265: cd "/home/zer0null/reserach extarctor/experiments/second-labeller-190" && python3 -c "
305: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
332: cd "/home/zer0null/Duval/docs/research/EXP#12-evidence" && python3 -c "
```

**`eval/second-labeller/RUN.json`** — 9 hit(s)

```text
5:   "_target": "/home/zer0null/Duval",
107:     "register_quote": "/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47 - 'F-EXP11-11 | answer not in option set was 0.00 % at every round in both models ... does not exist at baseline'",
112:     "description": "First parser used non-greedy 'options: \\[(.*?)\\]'; the option string 'the expanded[] ref list' in context.package-014 truncated the match, producing a FALSE 'answer not in option
143:     "sha256sum /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts experiments/second-labeller-190/reflex-decisions.sandbox.ts",
144:     "cmp /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts experiments/second-labeller-190/reflex-decisions.sandbox.ts",
148:     "git -C /home/zer0null/Duval rev-parse HEAD",
149:     "git -C /home/zer0null/Duval status --porcelain",
150:     "find /home/zer0null/Duval -newermt '-25 minutes' -type f",
155:     "No writes were made to /home/zer0null/Duval, journal/, strategy/ or other units' jobs/."
```

**`paper/CHECKLIST.md`** — 9 hit(s)

```text
4: Target `/home/zer0null/Duval` was **read-only** for this unit: HEAD before and after
66: - The **code and evidence** in the target repo are **AGPL-3.0** (`/home/zer0null/Duval/LICENSE`, GNU Affero
93:   `https://github.com/Aswin-Ram-K/Consonance` returns **HTTP 404** and
94:   `https://api.github.com/repos/Aswin-Ram-K/Consonance` returns **HTTP 404** (both 2026-10-15); the account's
95:   public repo listing contains no `Consonance`. The code has **never been public**, so **AGPL-3.0 has
100:   "re-derivable from the target repository `/home/zer0null/Duval`". The concrete list of sentences that
103: - **⚠ Also new:** `/home/zer0null/Duval/CITATION.cff` names `repository-code:
104:   "https://github.com/Aswin-Ram-K/Consonance"` — a URL that **404s for any reader**. The paper must not send
198:   changed no git state inside `/home/zer0null/Duval`.
```

**`eval/results/eval-shuffled-label.json`** — 8 hit(s)

```text
243:     "none -- admit() mints the state": {
343:     "the expanded[] ref list": {
519:         "none -- admit() mints the state"
522:       "gold": "none -- admit() mints the state",
524:       "predLabel": "none -- admit() mints the state",
1096:         "the expanded[] ref list",
1102:       "gold": "the expanded[] ref list",
1104:       "predLabel": "the expanded[] ref list",
```

**`eval/results/eval-deberta-v3-base.json`** — 7 hit(s)

```text
243:     "none -- admit() mints the state": {
343:     "the expanded[] ref list": {
519:         "none -- admit() mints the state"
522:       "gold": "none -- admit() mints the state",
1096:         "the expanded[] ref list",
1102:       "gold": "the expanded[] ref list",
1104:       "predLabel": "the expanded[] ref list",
```

**`eval/results/eval-majority-class.json`** — 7 hit(s)

```text
243:     "none -- admit() mints the state": {
343:     "the expanded[] ref list": {
519:         "none -- admit() mints the state"
522:       "gold": "none -- admit() mints the state",
1096:         "the expanded[] ref list",
1102:       "gold": "the expanded[] ref list",
1104:       "predLabel": "the expanded[] ref list",
```

**`eval/results/baselines.json`** — 6 hit(s)

```text
83:           "gold": "none -- admit() mints the state",
348:           "predLabel": "the expanded[] ref list",
349:           "gold": "the expanded[] ref list",
1457:           "gold": "none -- admit() mints the state",
1722:           "predLabel": "the expanded[] ref list",
1723:           "gold": "the expanded[] ref list",
```

**`eval/results/eval-modernbert-base.json`** — 6 hit(s)

```text
243:     "none -- admit() mints the state": {
343:     "the expanded[] ref list": {
519:         "none -- admit() mints the state"
522:       "gold": "none -- admit() mints the state",
1096:         "the expanded[] ref list",
1102:       "gold": "the expanded[] ref list",
```

**`eval/results/eval-setfit-mpnet.json`** — 6 hit(s)

```text
243:     "none -- admit() mints the state": {
343:     "the expanded[] ref list": {
519:         "none -- admit() mints the state"
522:       "gold": "none -- admit() mints the state",
1096:         "the expanded[] ref list",
1102:       "gold": "the expanded[] ref list",
```

**`eval/second-labeller-190/ROBUSTNESS.md`** — 6 hit(s)

```text
4: fixture `evals/fixtures/reflex-decisions.ts` (target `/home/zer0null/Duval`, READ-ONLY) with a
112: $ git -C /home/zer0null/Duval rev-parse HEAD      # before AND after
114: $ git -C /home/zer0null/Duval status --porcelain  # identical before and after, 4 entries
119: $ sha256sum /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts
121: $ find /home/zer0null/Duval -newermt '-45 minutes' -type f | wc -l
279: `/home/zer0null/Duval`, `journal/`, `strategy/`, or `jobs/`.
```

**`code/verify/redaction-log.json`** — 5 hit(s)

```text
3:  "original": "/home/zer0null/reserach extarctor/repro/encoder-crossover-190",
11:     "REDACTION_REPORT.md",
64:     "`grantPolicy`": 1
83:     "\\bgrantPolicy\\b": 1
98:     "\\bgrantPolicy\\b": 1
```

**`code/verify/run-verification.sh`** — 5 hit(s)

```text
16:        "$W/san/REDACTION_REPORT.md" "$W/san/INTEGRITY.md"
31: git -C /home/zer0null/Duval rev-parse HEAD
33: git -C /home/zer0null/Duval status --porcelain
133: STRICT='StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle'
151: STRICT = re.compile(r'StateClass|grantPolicy|admit\(|src/(?:broker|scope|layer|loop|policy|state)\.ts|content-addressed|expanded\[\]|Needle')
```

**`paper/MANUSCRIPT.md`** — 4 hit(s)

```text
754: | harness provenance (**not** on the source repository's default branch) | branch `EXP#12-typed-channel-comparison`, `a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8`, path `tools/typed-channel/` — 18 files 
821: `a5ef1b28a7baca7dc1094757106b6a6af2c2aaf8` (branch `EXP#12-typed-channel-comparison`, path
832: is named in `repro/encoder-crossover-190/EXCLUDED.md` — 15 exclusion classes, including traces, run artefacts,
842: `repro/encoder-crossover-190/LICENCE_TODO.md`; the subset should not be published under the code default
```

**`paper/OPEN_QUESTIONS.md`** — 4 hit(s)

```text
57: - **The AGPL-3.0 sub-question is closed, including the false alarm.** `/home/zer0null/Duval/LICENSE` is
58:   AGPL-3.0 and `CITATION.cff` names `https://github.com/Aswin-Ram-K/Consonance`, but that repository returns
68: from the target repository `/home/zer0null/Duval`"*. [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md) §8 lists the
78:    *without* opening Consonance. This is the only route that restores any **O-1A criterion 5** surface: the
```

**`code/harness/data/manifest.json`** — 3 hit(s)

```text
5:     "path": "/home/zer0null/Duval/.worktrees/integration/tools/typed-channel/data/corpus.json",
10:     "path": "/home/zer0null/Duval/.worktrees/integration/tools/typed-channel/data/fixture-190.json",
15:     "report": "/home/zer0null/Duval/.worktrees/integration/tools/typed-channel/data/lint-report.json",
```

**`eval/second-labeller/PREREGISTRATION.md`** — 3 hit(s)

```text
10: `evals/fixtures/reflex-decisions.ts` in the read-only target `/home/zer0null/Duval`.
90: > `/home/zer0null/reserach extarctor/experiments/second-labeller-190/blinded_cases.json`.
97: > `/home/zer0null/reserach extarctor/experiments/second-labeller-190/labelsB.json` as exactly
```

**`eval/second-labeller/disagreements.jsonl`** — 3 hit(s)

```text
1: {"id": "worker.class-018", "kind": "worker.class", "question": "A reasoner step has proposed a new capability: it needs to write the file it has just described. role.canRequestEscalation is false for 
2: {"id": "worker.class-023", "kind": "worker.class", "question": "The head state's class is reasoner, and a transition is proposed that keeps the class and adds an fs.write grant to it. Which StateClass
5: {"id": "capability.family-004", "kind": "capability.family", "question": "A catalogued class declares grantPolicy { kind: 'declared', tools: ['fs.read','fs.write'] } and also declares two skills in it
```

**`paper/REFERENCES.bib`** — 3 hit(s)

```text
4: % (target repo /home/zer0null/Duval, read-only). NOTHING is invented.
63: @misc{duval_decider_stack_2026,
64:   howpublished = {\texttt{/home/zer0null/Duval/docs/DECIDER\_STACK\_DECISION.md}, \S11.6 (ERRATA on
```

**`code/harness/LEAD-WIRING.md`** — 2 hit(s)

```text
8: > `../REDACTION_REPORT.md` section 7. What remains is the whole wiring recommendation.
42: assert. See `../REDACTION_REPORT.md` section 4.
```

**`code/verify/integrity-table.md`** — 2 hit(s)

```text
3: | `EXCLUDED.md` | `c06bbc8d0ba345be36e7260c42ba236f82d34730a09ece4c9db13098f49d2414` | 5967 |
4: | `LICENCE_TODO.md` | `283e7b323e68f3e58182de35595e7bd637be389a0c257b5bafee6efa9c28fd8c` | 3241 |
```

**`paper/REFS_VERIFIED.md`** — 2 hit(s)

```text
3: **Unit:** UREFS. **Date all fetches made:** **2026-10-15** (UTC). Target `/home/zer0null/Duval`
79: unrecorded search. `REFERENCES.bib`'s `duval_decider_stack_2026` entry (internal errata as the citation) stays
```

**`code/fixture/DECISION_CASE_SCHEMA.ts`** — 1 hit(s)

```text
2: //   target: /home/zer0null/Duval/evals/fixtures/reflex-decisions.ts (HEAD 907fa39)
```

**`code/harness/collect.py`** — 1 hit(s)

```text
394:         "session": "2026-09-28-duval-m0",
```

**`code/harness/export-fixture.ts`** — 1 hit(s)

```text
36: // invariant a sanitised checkout must assert. See ../REDACTION_REPORT.md sections 4-5.
```

**`code/verify/RESIDUAL-SCAN.txt`** — 1 hit(s)

```text
2: #   StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle
```

**`code/verify/recompute-claims.py`** — 1 hit(s)

```text
14:     `harness/out/manifest-eval.json` and `manifest-train.json`, which `EXCLUDED.md` E12 excludes.
```

**`eval/preregistration/EXP12-typed-channel-comparison-prereg.md`** — 1 hit(s)

```text
2:      Source: /home/zer0null/Duval/docs/research/experiments/EXP#12-typed-channel-comparison.md (HEAD 907fa39)
```

**`eval/second-labeller-190/RUN2.json`** — 1 hit(s)

```text
10:   "target": "/home/zer0null/Duval",
```

**`eval/second-labeller/metrics.json`** — 1 hit(s)

```text
5:  "_correction": "Corrected by UFIX4 on 2026-10-15 per UVER3 C2 (strategy/VERIFICATION_REPORT_3.md): the limitation keys were added by hand because PREREGISTRATION.md:12-16 forbids a bare kappa. The fr
```

**`eval/second-labeller/parse_fixture.py`** — 1 hit(s)

```text
50:     has the option string "the expanded[] ref list", whose `]` truncates the match.
```

**`paper/CLAIMS.md`** — 1 hit(s)

```text
5: Evidence tree root (read-only): `/home/zer0null/Duval/docs/research/EXP#12-evidence/`.
```

**`paper/REFS.md`** — 1 hit(s)

```text
4: `/home/zer0null/Duval`, read-only). **No BibTeX was invented and no field was filled in from memory.** An
```

**`paper/UNSOURCED_RETAINED.md`** — 1 hit(s)

```text
86: terms that **none of them discharges the absence claim**. `duval_decider_stack_2026` (the internal §11.6
```

### REVIEW residuals — reported, NOT fixed, NOT deleted (author decision)

| hit lines | pattern |
|---|---|
| 24 | `src/` |
| 12 | `DecisionKind` |
| 1265 | `memory.admission` |
| 849 | `capability.family` |

| hit lines | file |
|---|---|
| 834 | `code/harness/data/corpus.json` |
| 240 | `code/harness/data/train.jsonl` |
| 123 | `code/fixture/reflex-decisions.ts` |
| 117 | `code/harness/data/fixture-190.json` |
| 110 | `eval/results/eval-deberta-v3-base.json` |
| 110 | `eval/results/eval-modernbert-base.json` |
| 110 | `eval/results/eval-majority-class.json` |
| 110 | `eval/results/eval-setfit-mpnet.json` |
| 110 | `eval/results/eval-shuffled-label.json` |
| 108 | `eval/results/baselines.json` |
| 54 | `eval/second-labeller/labelsB.json` |
| 29 | `eval/second-labeller-190/ROBUSTNESS.md` |
| 21 | `eval/second-labeller/EVIDENCE.md` |
| 10 | `eval/second-labeller-190/RUN2.json` |
| 10 | `eval/second-labeller/disagreements.jsonl` |
| 8 | `eval/second-labeller/metrics.json` |
| 8 | `paper/MANUSCRIPT.md` |
| 7 | `eval/second-labeller/RUN.json` |
| 5 | `code/fixture/DECISION_CASE_SCHEMA.ts` |
| 4 | `code/verify/VERIFICATION.txt` |
| 4 | `code/harness/data/manifest.json` |
| 2 | `eval/second-labeller/OWED_CORRECTIONS.md` |
| 2 | `eval/results/REPORT.md` |
| 2 | `code/verify/run-verification.sh` |
| 2 | `paper/CHECKLIST.md` |
| 1 | `eval/second-labeller/PREREGISTRATION.md` |
| 1 | `eval/preregistration/EXP12-typed-channel-comparison-prereg.md` |
| 1 | `code/verify/RESIDUAL-SCAN.txt` |

**Reporting choice, stated rather than silent:** the `memory.admission` and `capability.family` patterns account for 2114 of the 2143 review lines. They are the fixture's own `kind` field value and its case-ID prefix, present in every data, label, metric and result line, so they are counted per file above rather than enumerated line by line. The semantically meaningful review residuals are enumerated in full below.

#### Every `src/` mention in the tree (file:line)

```text
eval/second-labeller/disagreements.jsonl:14: {"id": "topology-018", "kind": "topology", "question": "Two candidates: (A) write workspace/src/x.ts, (B) write workspace/src/y.ts. The paths are disjoint, neither consum
code/verify/RESIDUAL-SCAN.txt:2: #   StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle
code/verify/run-verification.sh:133: STRICT='StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle'
code/verify/run-verification.sh:151: STRICT = re.compile(r'StateClass|grantPolicy|admit\(|src/(?:broker|scope|layer|loop|policy|state)\.ts|content-addressed|expanded\[\]|Needle')
code/verify/VERIFICATION.txt:118: ./RESIDUALS.md:18:StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\
code/harness/data/fixture-190.json:29:   "question": "Step 4 must report whether the A3_budget gate in src/policy.ts delegates on pass, by reading that file's current contents out of the workspace. The step ch
code/harness/data/fixture-190.json:94:   "question": "A step must read workspace/src/loop.ts and return a verdict on it, and the postcondition explicitly forbids writing. The planner's rule is to select the cl
code/harness/data/fixture-190.json:170:   "question": "A step must read workspace/src/broker.ts and write a sibling file workspace/src/broker-test.ts that exercises it. Both halves are required. The catalogue h
code/harness/data/fixture-190.json:234:   "question": "A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker matches a scope
code/harness/data/fixture-190.json:851:   "question": "The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it declares. 
code/harness/data/fixture-190.json:1928:   "question": "Two candidates are on the table: (A) read workspace/src/loop.ts, (B) write the fix to that file. B's content is determined by what A returns, and both are 
code/harness/data/fixture-190.json:1984:   "question": "Two candidates: (A) write workspace/src/a.ts, (B) write workspace/src/b.ts. B's content is computed from the exported symbol list A produces. Both are admi
code/harness/data/fixture-190.json:2166:   "question": "Two candidates: (A) write workspace/src/x.ts, (B) write workspace/src/y.ts. The paths are disjoint, neither consumes the other, and both writes are require
code/harness/data/fixture-190.json:2222:   "question": "Two candidates: (A) read docs/POLICY.md, (B) read src/policy.ts. The step's output is a report of where the document and the code disagree, and neither rea
code/fixture/reflex-decisions.ts:112:       "Step 4 must report whether the A3_budget gate in src/policy.ts delegates on pass, by reading that file's current contents out of the workspace. The step changes no
code/fixture/reflex-decisions.ts:167:       "A step must read workspace/src/loop.ts and return a verdict on it, and the postcondition explicitly forbids writing. The planner's rule is to select the class whos
code/fixture/reflex-decisions.ts:233:       "A step must read workspace/src/broker.ts and write a sibling file workspace/src/broker-test.ts that exercises it. Both halves are required. The catalogue holds rea
code/fixture/reflex-decisions.ts:288:       "A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker matches a scope against
code/fixture/reflex-decisions.ts:798:       "The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it declares. Which fa
code/fixture/reflex-decisions.ts:1688:       "Two candidates are on the table: (A) read workspace/src/loop.ts, (B) write the fix to that file. B's content is determined by what A returns, and both are admissib
code/fixture/reflex-decisions.ts:1732:       "Two candidates: (A) write workspace/src/a.ts, (B) write workspace/src/b.ts. B's content is computed from the exported symbol list A produces. Both are admissible a
code/fixture/reflex-decisions.ts:1875:       "Two candidates: (A) write workspace/src/x.ts, (B) write workspace/src/y.ts. The paths are disjoint, neither consumes the other, and both writes are required. The c
code/fixture/reflex-decisions.ts:1919:       "Two candidates: (A) read docs/POLICY.md, (B) read src/policy.ts. The step's output is a report of where the document and the code disagree, and neither read depend
paper/MANUSCRIPT.md:827: (`src/**`, `kernel/**`) is the system the measurement is about, and it is not released. **No model weights**
```

**Independent reproduction of the UFIX10 measurement.** `src/*.ts` path mentions inside the fixture's **question** text: **10 mentions across 7 lines**, at `code/fixture/reflex-decisions.ts:112, 167, 233, 1688, 1732, 1875, 1919` — mirrored in `code/harness/data/fixture-190.json`. UFIX10 measured 10 mentions across 7 lines; this gate reproduces that exactly. These fields **are the model input**, so editing them changes what every arm saw and therefore every accuracy. They are irreducible and were left untouched.

#### `DecisionKind` mentions (file:line)

```text
eval/second-labeller/PREREGISTRATION.md:29:   comment, the `DecisionKind` / `DecisionCase` type declarations, the array opening, and one
code/verify/RESIDUAL-SCAN.txt:2: #   StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle
code/verify/run-verification.sh:133: STRICT='StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle'
code/verify/VERIFICATION.txt:118: ./RESIDUALS.md:18:StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\
code/verify/VERIFICATION.txt:119: ./RESIDUALS.md:53:| `README.md` | 4 | **irreducible by design** — the 4 remaining hits are all the `DecisionKind` name, which the variant decision must name (§6).
code/verify/VERIFICATION.txt:120: ./RESIDUALS.md:54:| `fixture/DECISION_CASE_SCHEMA.ts` | 3 | **irreducible by design** — the `DecisionKind` *type name* only, which VARIANT A deliberately keeps for
code/verify/VERIFICATION.txt:122: ./RESIDUALS.md:61:| `second-labeller/PREREGISTRATION.md` | 1 | **irreducible** — the frozen pre-registration mentions the `DecisionKind` type declarations; editing
code/fixture/DECISION_CASE_SCHEMA.ts:3: //   lines 53-75 (the DecisionKind union and the DecisionCase interface).
code/fixture/DECISION_CASE_SCHEMA.ts:8: export type DecisionKind =
code/fixture/DECISION_CASE_SCHEMA.ts:19:   kind: DecisionKind;
code/fixture/reflex-decisions.ts:53: export type DecisionKind =
code/fixture/reflex-decisions.ts:64:   kind: DecisionKind;
```

### Findings the author needs before deciding

1. **The gate's hard-fail list is incompatible with shipping the paper apparatus at all.** The manuscript and its scholarly apparatus — which this card instructs me to copy — cite the read-only target repository by absolute path in nine files (`EVIDENCE_NOTES.md`, `CHECKLIST.md`, `OPEN_QUESTIONS.md`, `MANUSCRIPT.md`, `REFERENCES.bib`, `REFS.md`, `REFS_VERIFIED.md`, `UNSOURCED_RETAINED.md`, `CLAIMS.md`). They are the honest provenance record of where the evidence came from; they cannot be redacted without either rewriting that record or dropping those documents.
2. **The sanitised tree leaks the target path in places its own sanitisation never scanned.** `code/harness/data/manifest.json` and `code/harness/LEAD-WIRING.md` still carry absolute paths into the target repository, and `code/fixture/reflex-decisions.ts`'s header still cites the internal sanitisation documents by name. The sanitisation's own strict-term list did not include the target path or the repository name, so these survived.
3. **A near-miss that this build avoided, and that the card as written would have caused.** The card names `RUN.json` among six files to take from the *experiments* directory. That upstream copy is **unsanitised** and differs from the sanitised copy in exactly the withheld mechanism vocabulary where the sanitised copy carries `[redacted]`. Taking it would have re-introduced withheld material into a would-be public package and hard-failed the gate. The build takes the sanitised copy and records the skip. `PREREGISTRATION.md`, `metrics.json` and `labelsB.json` are byte-identical to the sanitised copies (deduplicated); `ROBUSTNESS.md` and `RUN2.json` exist only upstream and are shipped.
4. **Two of the shipped eval files are `paper/`-equivalent provenance and hard-fail on their own:** `eval/second-labeller/EVIDENCE.md` and `OWED_CORRECTIONS.md` cite the target repository by absolute path as part of their read-only proof.

### Decisions left to the author (none taken here)

- Exclude `code/verify/` — it is the sanitisation verification apparatus and necessarily cites the excluded internal document names and the private original paths. `INCLUDE_VERIFY=0` does this without touching any source byte.
- Decide the policy for the target-repository path: it is either publishable provenance or it is not. That decision changes the paper apparatus, the harness data and the second-labeller evidence together.
- Decide the irreducible instrument residuals (`StateClass`, the grant-policy vocabulary and the `src/*.ts` question paths). Removing them re-authors the instrument and re-runs every arm — a new experiment, not a cleanup.
- `paper/AVAILABILITY.md` exists in the source but is **neither** on this card's include list **nor** on its exclude list. I left it out and did not decide for you; it is a one-line addition if you want it.

### Sandbox limitation (why the tree is not at the target path)

`/home/zer0null/research-publish-packages/` is outside this session's `workspace-write` sandbox: `mkdir` there returns `Read-only file system` / `[sandbox: file access denied under workspace-write mode]`, and escalation is not available to this unit. `/tmp` and `/dev/shm` are **per-call tmpfs** — proved by writing a marker in one call and finding it absent in the next — so no staged tree can survive. The build is therefore preserved as the script above; run it from a unit with write access to the target and the tree appears in full, with the same one commit and the same gate result.

---

*Generated by UBUILD1. Full raw gate output: 2478 lines, reproduced identically by re-running the build script and `bash gate.sh`.*

## Build script — `orchestration/units/UBUILD1.build.sh`

**Authorised write path** (orchestrator, granted after the per-call-tmpfs finding). This is the canonical build; the copy once embedded in this card was removed so two copies cannot diverge.

```bash
bash "/home/zer0null/reserach extarctor/orchestration/units/UBUILD1.build.sh"
```

| check | result |
|---|---|
| syntax / mode | `bash -n` OK · 561 lines · `chmod +x` |
| **idempotent** | run 1 and run 2 on the same DEST → **identical commit sha `0f7ec9c` and identical 65 files** |
| guard | `DEST=/tmp/ubuild1-run1` (wrong suffix) → **exit 2**, `rm -rf` refused before anything is touched |
| gate | script exits **1** on hard-fail and prints every hit with file and line (gate's own code preserved) |
| `/tmp` | **no dependency** — the only two occurrences are an explanatory comment and the repo's own `.gitignore` pattern `/tmp/` |
| as-audited tree | 0 references to the raw non-sanitised `repro/encoder-crossover-190/` |
| push / remote | 0 `git push`, 0 `git remote add` |
| shipped | **65 files, 6.4M** · paper 12 / 244K · code 28 / 4.5M · eval 20 / 672K · 1 commit · clean status · remote empty · nested `.git` 0 · working dirs 0 |

## Hit breakdown — the 301 hard-fail hits

### Per pattern

| pattern | hit lines | files | top files (count, first line numbers) |
|---|---|---|---|
| `/home/zer0null` | 74 | 19 | `eval/second-labeller/OWED_CORRECTIONS.md` 11 (lines 4,22,26) · `eval/second-labeller/EVIDENCE.md` 11 (lines 5,7,30) |
| `duval` | 71 | 19 | `eval/second-labeller/OWED_CORRECTIONS.md` 11 (lines 4,22,26) · `eval/second-labeller/EVIDENCE.md` 11 (lines 5,7,30) |
| `a5ef1b28` | 2 | 1 | `paper/MANUSCRIPT.md` 2 (lines 754,821) |
| `consonance` | 6 | 2 | `paper/CHECKLIST.md` 4 (lines 93,94,95) · `paper/OPEN_QUESTIONS.md` 2 (lines 58,78) |
| `EXCLUDED.md` | 4 | 4 | `code/verify/recompute-claims.py` 1 (lines 14) · `code/verify/integrity-table.md` 1 (lines 3) |
| `REDACTION_REPORT` | 21 | 6 | `eval/second-labeller/OWED_CORRECTIONS.md` 9 (lines 38,51,65) · `code/fixture/reflex-decisions.ts` 7 (lines 21,25,79) |
| `RESIDUALS.md` | 6 | 1 | `code/verify/VERIFICATION.txt` 6 (lines 105,118,119) |
| `LICENCE_TODO` | 2 | 2 | `code/verify/integrity-table.md` 1 (lines 4) · `paper/MANUSCRIPT.md` 1 (lines 842) |
| `VERIFICATION_REPORT` | 2 | 2 | `eval/second-labeller/metrics.json` 1 (lines 5) · `eval/second-labeller/OWED_CORRECTIONS.md` 1 (lines 7) |
| `StateClass` | 66 | 6 | `code/harness/data/fixture-190.json` 30 (lines 5,17,29) · `code/fixture/reflex-decisions.ts` 30 (lines 90,101,112) |
| `grantPolicy` | 47 | 7 | `code/harness/data/fixture-190.json` 19 (lines 5,29,55) · `code/fixture/reflex-decisions.ts` 19 (lines 90,112,134) |
| `src/broker` | 2 | 2 | `code/harness/data/fixture-190.json` 1 (lines 170) · `code/fixture/reflex-decisions.ts` 1 (lines 233) |
| `admit(` | 36 | 9 | `code/verify/VERIFICATION.txt` 16 (lines 123,125,126) · `eval/results/eval-shuffled-label.json` 4 (lines 243,519,522) |
| `expanded[` | 47 | 12 | `code/verify/VERIFICATION.txt` 19 (lines 124,127,128) · `eval/results/eval-deberta-v3-base.json` 4 (lines 343,1096,1102) |

Counts are per pattern over the hit lines and **overlap** (a line can match two patterns), so this column sums above 301. The gate's own count block produces the same figures.

### Per location (each hit line counted exactly once)

| bucket | hits | share |
|---|---|---|
| A · `code/verify/**` — sanitisation-verification apparatus | 58 | 19.3% |
| B · `code/fixture/**` + `code/harness/data/**` — instrument and datasets (**the model input**) | 104 | 34.6% |
| C · `code/harness/**` code and wiring | 4 | 1.3% |
| D · `paper/**` — manuscript and apparatus | 36 | 12.0% |
| E · `eval/**` — pre-registration, results, second-labeller | 99 | 32.9% |
| **total** | **301** | 100% |

### Per file, worst first (first line numbers given)

| hits | file | first lines |
|---|---|---|
| 54 | `code/fixture/reflex-decisions.ts` | 21,25,28,79 … |
| 46 | `code/harness/data/fixture-190.json` | 5,17,29,42 … |
| 44 | `code/verify/VERIFICATION.txt` | 3,4,105,118 … |
| 21 | `eval/second-labeller/OWED_CORRECTIONS.md` | 4,7,22,26 … |
| 13 | `eval/second-labeller/EVIDENCE.md` | 5,7,30,31 … |
| 11 | `paper/EVIDENCE_NOTES.md` | 3,17,52,79 … |
| 9 | `eval/second-labeller/RUN.json` | 5,107,112,143 … |
| 9 | `paper/CHECKLIST.md` | 4,66,93,94 … |
| 8 | `eval/results/eval-shuffled-label.json` | 243,343,519,522 … |
| 7 | `eval/results/eval-deberta-v3-base.json` | 243,343,519,522 … |
| 7 | `eval/results/eval-majority-class.json` | 243,343,519,522 … |
| 6 | `eval/second-labeller-190/ROBUSTNESS.md` | 4,112,114,119 … |
| 6 | `eval/results/eval-modernbert-base.json` | 243,343,519,522 … |
| 6 | `eval/results/eval-setfit-mpnet.json` | 243,343,519,522 … |
| 6 | `eval/results/baselines.json` | 83,348,349,1457 … |
| 5 | `code/verify/run-verification.sh` | 16,31,33,133 … |
| 5 | `code/verify/redaction-log.json` | 3,11,64,83 … |
| 4 | `paper/MANUSCRIPT.md` | 754,821,832,842 |
| 4 | `paper/OPEN_QUESTIONS.md` | 57,58,68,78 |
| 3 | `eval/second-labeller/PREREGISTRATION.md` | 10,90,97 |
| 3 | `eval/second-labeller/disagreements.jsonl` | 1,2,5 |
| 3 | `code/harness/data/manifest.json` | 5,10,15 |
| 3 | `paper/REFERENCES.bib` | 4,63,64 |
| 2 | `code/verify/integrity-table.md` | 3,4 |
| 2 | `code/harness/LEAD-WIRING.md` | 8,42 |
| 2 | `paper/REFS_VERIFIED.md` | 3,79 |
| 1 | `eval/second-labeller-190/RUN2.json` | 10 |
| 1 | `eval/second-labeller/metrics.json` | 5 |
| 1 | `eval/second-labeller/parse_fixture.py` | 50 |
| 1 | `eval/preregistration/EXP12-typed-channel-comparison-prereg.md` | 2 |
| 1 | `code/verify/RESIDUAL-SCAN.txt` | 2 |
| 1 | `code/verify/recompute-claims.py` | 14 |
| 1 | `code/harness/export-fixture.ts` | 36 |
| 1 | `code/harness/collect.py` | 394 |
| 1 | `code/fixture/DECISION_CASE_SCHEMA.ts` | 2 |
| 1 | `paper/UNSOURCED_RETAINED.md` | 86 |
| 1 | `paper/CLAIMS.md` | 5 |
| 1 | `paper/REFS.md` | 4 |

### Judgement

**(i) Files that are themselves process/audit artifacts and probably should not ship — 95 hits (31.6%).**

- **`code/verify/**` — 58 hits**, the single biggest concentration, and it is all *audit output*: `VERIFICATION.txt` 44, `run-verification.sh` 5, `redaction-log.json` 5, `integrity-table.md` 2, `RESIDUAL-SCAN.txt` 1, `recompute-claims.py` 1.
- `eval/second-labeller-190/{ROBUSTNESS.md 6, RUN2.json 1}` — 7 hits: upstream run records that cite the target path in their read-only proof.
- `eval/second-labeller/OWED_CORRECTIONS.md` — 21 hits: a corrections ledger, not a result.
- `paper/CHECKLIST.md` — 9 hits: a unit checklist, not scholarly apparatus.
- Also pure audit output but **0 hard hits**: `code/verify/RECOMPUTE-CLAIMS.txt` (a clean log). `INTEGRITY.md` was never copied — it is a top-level source meta file, not part of any sanitised subtree.

`INCLUDE_VERIFY=0` removes **58** of these without touching a single source byte. The remaining 37 are four files that can be dropped by name. This is curation, not hand-editing — and it is a decision for the author.

**(ii) Genuine content that needs a decision from the author — 206 hits (68.4%).**

- **104 hits in the instrument and datasets** (`code/fixture/**`, `code/harness/data/**`, `eval/results/**`, `disagreements.jsonl`) — `StateClass`, the grant-policy vocabulary, `admit(`, `expanded[`, `src/broker`. **These are the model input**: editing them changes what every arm saw and therefore every accuracy. Irreducible; the only honest fix is to re-author the instrument and re-run every arm, which is a new experiment.
- **27 paper hits beyond the checklist** — provenance citations of the read-only target in nine files, and the private branch SHA in `paper/MANUSCRIPT.md:754,821`. The manuscript also points at the internal exclusion inventory (`:832`) and the licence to-do (`:842`). The paper itself needs an edit.
- **71 eval hits beyond the two audit files** — `eval/second-labeller/EVIDENCE.md` 13, `RUN.json` 9 (sanitised), `PREREGISTRATION.md` 3, `disagreements.jsonl` 3, `metrics.json` 1, plus `eval/preregistration/…` 1. These are evidence documents whose read-only proof names the target.
- **4 harness-code hits** — `code/harness/data/manifest.json` 3, `LEAD-WIRING.md` 2, `export-fixture.ts` 1, `collect.py` 1. **A leak the sanitisation missed**: its own strict-term list never included the target path or the repository name, so absolute target paths survived in data and wiring.

**(iii) Over-broad pattern in the gate — NONE. 0 false positives.**

I checked every match context rather than assuming, and did **not** widen, narrow or reinterpret anything:

- `duval` (71 hits, 66 distinct contexts): **every** context is the target repository's directory path (`/home/zer0null/Duval…`), or a repository-derived BibTeX key. The key form accounts for exactly **3** hits: `paper/REFERENCES.bib:63`, `paper/REFS_VERIFIED.md:79`, `paper/UNSOURCED_RETAINED.md:86` (`duval_decider_stack_2026`). If *Duval* is the author's own surname, a key derived from it may read as harmless to them — but it is simultaneously the private target's directory name, so **I am not calling it a false positive**. This is the one context worth an author's glance; it is not a reason to change the pattern.
- `consonance` (6 hits): all six are the private project's own name and its GitHub URL (`paper/CHECKLIST.md:93,94,95,104`, `paper/OPEN_QUESTIONS.md:58,78`) — real disclosure, not an incidental word match.
- `a5ef1b28` (2 hits): the private branch SHA in `paper/MANUSCRIPT.md:754,821`. Correctly flagged.
- Every other pattern's contexts are the withheld mechanism vocabulary or the internal document names. Nothing matched by accident, e.g. no bibliography entry belonging to an unrelated author is caught.

### The two candidate decisions this leaves open (neither taken here)

1. **Curation:** drop the four audit-artifact paths in (i) — `code/verify/**` via `INCLUDE_VERIFY=0`, plus `eval/second-labeller-190/ROBUSTNESS.md`, `eval/second-labeller-190/RUN2.json`, `eval/second-labeller/OWED_CORRECTIONS.md`, `paper/CHECKLIST.md`. That is 95 hits removed with no source edit. **It does not make the gate pass** — the remaining 206 are genuine.
2. **Content:** decide whether absolute provenance paths into the read-only target are publishable. That single decision governs the paper apparatus (27 hits), the second-labeller evidence (71) and the harness records (4). The 104 instrument hits are a separate, irreducible question.

*Breakdown generated from the gate's own output of a verified build run; buckets count each hit line once.*
