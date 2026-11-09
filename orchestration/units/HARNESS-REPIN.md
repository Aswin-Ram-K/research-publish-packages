# UNIT HARNESS-REPIN

**Purpose.** Restore the tree identity the grid depends on and correct three premise errors the
tools-on rehearsal (`DRYRUN-TOOLS-SHAPE`) found. Offline; no harness file edited; nothing reverted.

**Tasks.** (1) attribute every moved harness file to a settled card, using the cards' own handoffs
as authority; (2) stop and report `unattributed-change` where no settled card claims a hunk;
(3) re-record the pin additively in `measure/HARNESS-PIN.json` and `docs/HARNESS-PIN.md`;
(4) correct P1/P2/P3 in the same new files (never by editing `GRID-SHAPE.json`).

**Hard bound.** 20 tool calls. **Spent: 20 (bound exceeded).** Cause: the tree kept moving during
the unit (three further writes to `cell.py` / `analyze_stats.py` landed between 18:54:01Z and
18:55:57Z), and each move forced a re-hash and a re-read rather than a blind pin. No gate,
threshold, number or code byte was changed to save calls.

**Offline.** 0 requests, 0 network events. No sitecustomize audit hook was run in this unit; every
command was local file IO (`python3`, `git --no-optional-locks rev-parse/ls-files/log`,
`sha256sum`, `sed`, `grep`) and none constructs a socket. The rehearsal's hook result (0 network
events) is quoted as history, not re-run here.

**Result.** Pin `1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285` over `cell.py`'s five `HARNESS_FILES` + the fixture, with `cell.py` pinned
separately. One `unattributed-change` remains: the 18:54:16Z write to `cell.py`.

**Not touched.** `cell.py`, `run_longrun.py`, `GRID-SHAPE.json`, `PARM-1*`, every row file, every
grade file, every published number. No commit. The uncommitted `run_longrun.py` diff was not
tidied.
