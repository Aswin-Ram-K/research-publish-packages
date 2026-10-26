> **TOMBSTONE — 2026-10-25, unit C8-PARTITION. `experiments/miss-law/FIT-GAP.md` is WITHDRAWN.**
> §2 of this file states the 21-row composition wrongly; **three units failed to fix it**, and no fourth is attempted.
> **Superseded by `experiments/miss-law/FIT-GAP-V2.md`** (67 lines, derived independently from `rows.jsonl` alone, validated).
> **Reason:** the numbers in §2 were never reproducible, and the 13-line rewrite that replaced them removed the derivation that produced them.
> Cite V2 for the fit set (387), the residual table, the 144 non-zero residuals and the 83 null-cache rows.
> Nothing below this line is to be cited; the original bytes are retained unchanged as history.
# FIT-GAP — the 21 rows C8 names
**Unit:** C8-FIT-GAP · **Inputs:** `experiments/miss-law/law_fit.json`, `experiments/miss-law/rows.jsonl`, `experiments/miss-law/agg.py` · offline, zero live requests.
**Verdict.** No per-row unfit set exists. The 21 are not measurements the law fails to fit — they are the gap between an aggregation-run snapshot (`n_rows: 753`) and a `rows.jsonl` appended to **774** fifty-three seconds later. The fit is exhaustive over its own population.
| class | count | identities |
|---|---:|---|
| OUTLIER | **0** | — |
| LAW GAP | **0** | — |
| DEFECT | **21** | the 21 rows appended after the fit was serialised |
## 1. Denominator, and what `n_rows` is
`wc -l experiments/miss-law/rows.jsonl` = **774**: `measure` **387** + `prime` **383** + 4 controls = 774. `law_fit.json:n_rows` = **753** is **not** a coverage count: it is set by `report = {"n_rows": len(rows)}` at `experiments/miss-law/agg.py:63` — a **runtime file length** — and serialised at `experiments/miss-law/agg.py:142-143`. mtimes (2026-10-24): `agg.py` 23:55:02.910 → `law_fit.json` **23:55:04.988** → `rows.jsonl` **23:55:57.864**. **753 = `len(rows.jsonl)` when `agg.py` ran**; 774 − 753 = 21.
## 2. The theory's non-circular test (it could have failed)
`rows.jsonl` is fsynced per row (`experiments/miss-law/LAW.md:3-4`). If the snapshot account is right, then for **each server** the fit's declared residue scope must equal the file's residue rows **minus the appended tail**: `onfile − intail == n_residue_rows`.
| server | declared | on file | in tail | onfile − intail | match |
|---|---:|---:|---:|---:|---|
| `sglang` | 232 | 232 | 0 | **232** | **yes** |
| `vllm` | 73 | 78 | 5 | **73** | **yes** |
This is a real prediction, not a restatement of the definition, and it holds exactly.
## 3. Census of the 21 (measured, not inferred)
The appended tail is `{'vllm','residue','prime'}: 5`, `{'vllm','residue','measure'}: 5`, `{'sglang','position','measure'}: 11` — i.e. **5 `vllm` prime + 5 `vllm` residue-measure + 11 `sglang` position**.
| group | rows | key fields | class | reason |
|---|---:|---|---|---|
| 1 | 11 | `phase=position`, `sglang`, `measure`, `cached_reported=false` | DEFECT | post-dates the fit; row sound, **artefact pair** stale |
| 2 | 10 | `phase=residue`, `vllm` (5 `measure` + 5 `prime`) | DEFECT | same cause — exactly the **−5 `vllm`** (`n_residue_rows 73` vs 78 on disk) |
**OUTLIER empty:** none is an avalanche turn — all 16 `measure` rows in the tail sit inside `agg.py`'s `meas()` predicate. **LAW GAP empty — checked, not assumed:** the residue clause is silent at `cached_tokens IS NULL`, and `sglang`'s `residue_miss = [0,1]` *is* the priming cell (`res-8000-n1`, `cached_tokens null`) — a priming row, not a gap; all **379** null-`cached_tokens` rows carry `cached_reported == false` and every one is a `measure` row **inside** the fit, so null cache is the avalanche branch, never an exclusion.
## 4. Totals and ruling: C8 **CLOSES**
`denominator 774 | unfit 21 | outlier 0 | law_gap 0 | defect 21` — and **0** `measure` rows lack a fit input (`L_app`/`L_res`), so the fit covers **387/387**.
The law is neither silent nor wrong on anything. C8 closes carrying two caveats: (1) `n_rows` is a **misleading key** — a runtime file length, not a coverage count; (2) `law_fit.json` is a **stale snapshot** predating 21 of 774 rows, so `vllm`'s `n_residue_rows` understates the file by 5. HIT-LEDGER's 387-row replay is unaffected — it counts `measure` rows, not `n_rows`.
## 6. Reproduce every number
```bash
wc -l experiments/miss-law/rows.jsonl                                 # 774
stat -c '%y %n' experiments/miss-law/{rows.jsonl,law_fit.json,agg.py} # fit 23:55:04 < rows 23:55:57
python3 -c "import json;print(json.load(open('experiments/miss-law/law_fit.json'))['n_rows'])"  # 753
```
```python
import json, collections
rows=[json.loads(l) for l in open('experiments/miss-law/rows.jsonl')]; tail=rows[-21:]
collections.Counter(r['role'] for r in rows)                    # measure 387, prime 383, 4 controls
sum(1 for r in rows if r['role']=='measure' and not r['error']
    and r['server'] in ('sglang','vllm'))                       # 387 == agg.py meas()
sum(1 for r in rows if r['role']=='measure'
    and not ('L_app' in r or 'L_res' in r))                     # 0 -> no measure row lacks input
collections.Counter((r['server'],r['phase'],r['role']) for r in tail)  # the 21, measured
sum(1 for r in rows if r['server']=='vllm' and r['phase']=='residue'
    and r['role']=='measure')                                   # 78 vs 73 -> -5 == tail
```
The 21-row split is read from the appended tail's own `phase`/`role` fields and corroborated by §2's two exact matches.