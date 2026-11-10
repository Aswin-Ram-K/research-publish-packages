# V-SPCC-5B — independent re-check of the SPCC supervisor fix (U-SPCC-5B)

Verdict: **the three claimed fixes are real and reproducibly demonstrable** (window removal on every exit path, a genuine SIGTERM→SIGKILL kill path, and reads that raise). **Two accounting defects remain**, one of which directly contradicts the plan's "only VERIFIED when the remainder was measured" rule.

Target: `/home/zer0null/research extractor/experiments/ptr-engine/serving/spcc_supervisor.py` (535 lines, **untracked** — `git ls-files --error-unmatch` → *did not match any file(s) known to git*, so the fixing diff is not reviewable from history; all statements below are from behaviour I drove and from the current bytes).

All driving used a throwaway `--base-dir` (`SPCC_BASE_DIR`) and a throwaway cgroup root (`SPCC_CGROUP_ROOT`) under `/tmp`; MemAvailable was injected via `SPCC_MEMINFO_PATH` because the real box currently reports **13.98 GB** available, below the 68 GB admission reserve. The real `serving/` directory was never touched.

## 1. Suite

```
$ .venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q
............                                                             [100%]
12 passed in 7.53s
```

## 2. Window never leaks (driven independently of the author's tests)

**2a normal exit**

```
open: "opened memory window job=clean declared_peak=1.0GB mem_available=100.00GB"
run_rc=0  child_out="CHILD_OK"  window_exists=false  jsonl_lines=3
last record: exit_code=0 killed=null aborted=null allowance="VERIFIED" cgroup_peak_gb=0.0 unaccounted_gb=0.0
```

**2b child exits non-zero**

```
run_rc=7  window_exists=false
record: {"job":"nz", ..., "cgroup_peak_gb":0.0, "unaccounted_gb":0.0, "killed":null, "aborted":null,
         "exit_code":7, "returncode":7, "child_returncode":7, "allowance":"VERIFIED"}
```

**2c SIGTERM to the supervisor while a child sleeps**

```
sup_rc=241  child_pids=["3797756"]  child_alive_after=[]  window_exists=false
record: child_returncode=-15  child_signal=15
```

Child was signalled (its own process group, `-15`) and is gone; window removed. `sup_rc=241` is Python wrapping `SystemExit(-15)`.

**Real directory untouched:** `ls experiments/ptr-engine/serving/MEM-WINDOW.json` → `No such file or directory` (asserted again after all probes).

## 3. The kill path is real (`SPCC_PEAK_FILE`, `--grace 0.2`)

**3a peak = 64424509441 (> 60 GiB), obedient child**

```
run_rc=1  stdout="killed: cgroup-peak"  window_exists=false
record: killed="cgroup-peak"  child_returncode=-15  child_signal=15  allowance="VERIFIED"
```

**3b child ignores SIGTERM, peak crosses the cap 1.2 s after launch**

```
stdout="READY\nkilled: cgroup-peak"  elapsed_after_peak=0.23s  window_exists=false
record: killed="cgroup-peak"  child_returncode=-9  child_signal=9
```

SIGKILL after the 0.2 s grace is confirmed, not inferred: `-9` in the record.

## 4. Read failures are not zeros

Peak file deleted mid-run:

```
sup_rc=1  stdout="aborted: sample-unreadable /tmp/spccbase-6loxvz_5/peak"  window_exists=false
record: aborted="sample-unreadable"  aborted_path="/tmp/spccbase-6loxvz_5/peak"
        allowance="UNVERIFIED"  child_returncode=-15  child_signal=15
```

Child terminated, path named, window removed. The **reads** do raise — no `except` returns 0 into the read path:

```python
38: def mem_available_gb(path=None):
39:     p = Path(path) if path is not None else _meminfo_path()
40:     with p.open() as f:
41:         for line in f:
42:             if line.startswith("MemAvailable:"):
43:                 kb = int(line.split()[1])
44:                 return kb / (1024 * 1024)
45:     raise RuntimeError("MemAvailable not found in meminfo")
...
83: def _read_peak(cg_path, peak_source=None):
84:     if callable(peak_source):
85:         return int(peak_source())
86:     p = _peak_path(cg_path, peak_source)
87:     return int(p.read_text().strip())
```

But the claim "no code path substitutes `0` for a failed read" is **only true of the read functions, not of the record**. See defect 2.

## 5. Admission regressions

```
5a declared 61        -> rc=2 "refusing: declared peak 61.0 GB exceeds cap 60 GB"      window_exists=false
5b MemAvailable 0.95  -> rc=2 "refusing: MemAvailable 0.95 GB < 68 GB (cap+reserve)"   window_exists=false
5c run, no window     -> rc=3 "refusing to run: no memory window open"                 marker file absent
5d cgroup root = plain file
   open_rc=0; run rc=3 "refusing to run: cgroup root not writable: [Errno 20] Not a directory: '.../not_a_dir/spcc-test-write'"
   marker file absent; jsonl lines 0 (no record, no child)
```

No child starts on any refusal. (Nit: 5d's refusal leaves the open window in place — the caller must `close-window`; nothing closes it automatically.)

## 6. Cap and cgroup constants

```
22:CAP_BYTES = 64424509440  # 60 GiB
214:        (test_cg / "memory.max").write_text(str(CAP_BYTES))
215:        (test_cg / "memory.max").unlink(missing_ok=True)
228:        (cg_path / "memory.max").write_text(str(CAP_BYTES))
289:            (cg_path / "memory.max").read_text()
309:            (cg_path / "cgroup.procs").write_text(str(proc.pid) + "\n")
361:                if peak > CAP_BYTES:
```

`64424509440 == 60 * 1024**3` exactly. The only `Popen` (line ~306) is after `_setup_cgroup` success, a `memory.max` read-back, and the MemAvailable read; the single failure point after launch (`cgroup.procs` write, line 309) SIGKILLs the child and returns 3. Check 5d proves the post-launch path is unreachable from a broken root. No path runs a child without a configured cgroup.

## 7. Honesty of the record — **defects here**

```python
405:            peak_bytes = 0
406:            peak_ok = True
407:            try:
408:                peak_bytes = _read_peak(cg_path, self.peak_source)
409:            except Exception:
410:                peak_ok = False
411:                if aborted is None:
412:                    aborted = "sample-unreadable"
413:                    aborted_path = str(_peak_path(cg_path, self.peak_source))
414:            cgroup_peak_gb = (peak_bytes / (1024 ** 3)) if peak_ok else 0.0
415:            close_ma_ok = True
416:            try:
417:                close_ma = mem_available_gb(self.meminfo_path)
418:            except Exception:
419:                close_ma_ok = False
420:                if aborted is None:
421:                    aborted = "sample-unreadable"
422:                    aborted_path = str(self.meminfo_path)
423:                close_ma = opened_ma
424:            unaccounted_gb = ((opened_ma - close_ma) - cgroup_peak_gb) if close_ma_ok else 0.0
...
439:            if aborted is not None:
440:                w2["allowance"] = "UNVERIFIED"
441:            elif unaccounted_gb > 0:
442:                w2["allowance"] = "UNVERIFIED"
443:            else:
444:                w2["allowance"] = "VERIFIED"
```

`unaccounted_gb = (opened_ma − close_ma) − cgroup_peak_gb`, i.e. exactly *(MemAvailable drop) − cgroup peak*. Correct arithmetic, and a positive value does yield `UNVERIFIED` (line 441).

**Could a window that never measured its outside-cgroup remainder be recorded `VERIFIED`? Yes — three ways, one proven above:**

- **Killed window (proven, 3a).** `killed="cgroup-peak"`, `unaccounted_gb=0.0` → line 444 writes `allowance="VERIFIED"`. A window that breached the cap is stamped VERIFIED. This contradicts the plan's verification item 9 and is the defect that matters.
- **No-op / unallocated child (proven, 2a/2b).** peak 0, drop 0 → `VERIFIED`. `VERIFIED` means "the drop did not exceed the cgroup peak", not "a delta test was performed for this workload shape".
- **Negative remainder.** If MemAvailable rose during the run, `unaccounted_gb < 0` → line 444 again `VERIFIED`, and the negative number is written verbatim into the row.

So `VERIFIED` is an arithmetic verdict on two endpoint reads, not evidence that allocations outside the cgroup were measured.

## Defects (actionable)

1. `spcc_supervisor.py:439-444` — a cap-killed window is recorded `allowance: "VERIFIED"`; make the verdict `UNVERIFIED` whenever `killed_reason is not None`, and re-drive 3a.
2. `spcc_supervisor.py:414` and `:424` — a failed closing peak read still writes `cgroup_peak_gb: 0.0`, and a failed closing MemAvailable read still writes `unaccounted_gb: 0.0`, into the finalised record; write `null`/omit the field instead so no consumer can sum a fabricated zero (my check-4 row carries `cgroup_peak_gb: 0.0` next to `aborted: "sample-unreadable"`).
3. `spcc_supervisor.py:424,441` — a negative `unaccounted_gb` (MemAvailable rising mid-run) is indistinguishable from a measured zero and yields `VERIFIED`; clamp it and mark the window `UNVERIFIED` (or record a `measurement_noise` note) when the remainder is negative.
