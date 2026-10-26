# V2-CURRENT — independent verifier of the CURRENT artefacts

Card: `V2-CURRENT` (verifier; not the author of anything checked here).
Bound: 40 tool calls. Used: 30. Status: **partial** (all three checks completed; one sub-item,
the 30,000-char cold CROSSOVER for qwen, is genuinely UNMEASURED on disk — not a bound failure).

Write paths used: `orchestration/units/V2-CURRENT.md`, `orchestration/handoffs/V2-CURRENT.json`,
`.verify-scratch/**`. Nothing in `release/v0.1/**`, `papers/**` or `experiments/**` was modified;
every probe needing extra files ran on a copy at `.verify-scratch/rel/`. All Python ran with
`PYTHONDONTWRITEBYTECODE=1` so no `__pycache__` entered any hashed tree.

Deliverable: `orchestration/handoffs/V2-CURRENT.json` (`overall: fail`).

---

## CHECK A — release self-sufficiency: **CONFIRMED BROKEN**

### A1. Reproduced, as shipped

| command (from `cd release/v0.1`) | exit | decisive line |
|---|---:|---|
| `papers/context-cache/verify_package.py` | **0** | `verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none` |
| `papers/context-cache/recompute.py all` | **1** | `FileNotFoundError: [Errno 2] No such file or directory: '/home/zer0null/reserach extarctor/release/v0.1/state/config/rows.jsonl'` |
| `papers/context-cache/recompute_r2.py all` | **1** | same `FileNotFoundError` |
| `tests/test_gap_closure_ledger.py` | **1** | `8 failed in 0.14s` — `FileNotFoundError: … state/gap-ledger.json` |

**Path correction to REPRO.md:** `release/v0.1/verify_package.py` and `release/v0.1/recompute.py`
do **not** exist — the literal commands from `cd release/v0.1` exit **2** with
`can't open file '…/release/v0.1/verify_package.py': [Errno 2] No such file or directory`.
The scripts ship under `papers/context-cache/`. The claims about *what fails* are right; the
paths in REPRO are one directory off.

### A2. Minimal self-sufficiency set (measured on `.verify-scratch/rel/`)

| added to the copy | recompute.py | recompute_r2.py | ledger tests |
|---|---:|---:|---|
| nothing | 1 | 1 | 8 failed |
| `state/config/rows.jsonl` only (82,565 B) | **0** | **0** | 6 failed, 2 passed |
| `+ state/gap-ledger.json` (25,834 B) | 0 | 0 | **6 failed, 2 passed** |

`recompute.py all` with `rows.jsonl` present prints `COVERAGE GUARD PASS  69 claims documented,
67 runnable here + 2 script-backed`. So the recompute pair needs **exactly one file**, and the
gap-ledger tests need **eleven**: `state/config/rows.jsonl`, `state/gap-ledger.json`, plus the
nine evidence refs the ledger resolves — `orchestration/VERDICTS.md`,
`state/config/live-server-config.json`, `state/sys-opt-verdict.json`,
`scratch/cache-audit/docs/pin_{sgl_hicache_design,sgl_radix_eviction_policy,sgl_session_radix_cache}.mdx`,
`scratch/cache-audit/docs/pin_{vllm_cache,vllm_argutils}.py`, and handoffs
`orchestration/handoffs/{CACHE-AUDIT,PAPER-FINAL}.json`. With all eleven: **8 passed**.
(The ledger additionally expects a handoff literally named `PAPER-FINAL`; the tree has
`PAPER-FINAL.json`, `PAPER-FINAL-V*.json` — resolution succeeded, so the naming is tolerated.)

### A3. Does "every number re-derives from raw rows" hold? **No — 6 of 69 claims are unreachable.**

| tree | `recompute.py all` | `recompute_r2.py all` | distinct claim blocks printed |
|---|---:|---:|---:|
| shipped `release/v0.1` | 59 blocks, then crash | 0 blocks, then crash | **59** |
| live | 64 blocks | 6 blocks | **65** |

Unreachable as shipped: **C62, C63, C65, C66, C67, C68** — exactly the six missing by set
difference. (C63/C65–C68 are printed by `recompute_r2.py`, which dies before its first block;
C62 is downstream of `recompute.py`'s crash.)

### A4. Manifest

`MANIFEST.json`: **943 entries, 0** whose path starts with `state/` (matches the expected 0).
Candidate sizes: `state/config/rows.jsonl` **82,565 B**, `state/gap-ledger.json` **25,834 B**.
The manifest is not *lying* — the data dependency is simply outside the shipped surface, so the
manifest cannot contain it by construction.

---

## CHECK B — crossover rows vs the claimed verdict: **handoff's `done` is OVERSTATED; verdict is CONDITIONAL, not NEGATIVE**

### B1. Cell completeness (my own count)

Round-level files (`rows_occamy.jsonl` 119 rows, `rows_qwen.jsonl` 28 rows) are **not**
rep-countable — L1 runs carry up to 7 rounds per rep. Reps were counted from `runs.json`
(66 run-level records) and cross-checked against `runs_occamy.json` (50) / `runs_qwen.json` (16).

| model | grid slots | COMPLETE (3 reps, both arms) | INCOMPLETE | ABSENT |
|---|---|---|---|---|
| occamy-1.0 | 8 | 3k/12 cold, 3k/12 warm, 3k/30 cold, 3k/30 warm, 10k/12 cold, 10k/12 warm, **30k/12 cold**, **30k/12 warm** (7) | 10k/30 cold (c0 reps 1–2, **0 L1 runs**) | — |
| qwen3.5-9b | 4 | 3k/12 cold, 3k/12 warm (2) | 10k/12 cold (c0 3, **0 L1**), 10k/12 warm (1 c0, **0 L1**) | every 30,000 and every n=30 slot |

Totals: **9 complete cells, 4 incomplete, everything else absent.** The handoff's
"24 runs complete, 65 request rows, 12 of 12 cells measured" is contradicted on all three
numbers by its own files (66 runs; 147 round rows; 9 complete cells).

### B2. Recomputed table (runs.json, `uncached = prompt_tokens − cached_tokens`, mean over 3 reps)

| size | model | cache | reps | C0_unc | L1_unc | saving_billed % |
|---:|---|---|---:|---:|---:|---:|
| 3,000 | occamy-1.0 | cold | 3 | 1044.7 | 2162.0 | **−106.96** |
| 3,000 | occamy-1.0 | warm | 3 | 6.0 | 83.3 | **−1288.89** |
| 3,000 | occamy-1.0 | cold (n=30) | 3 | 1455.7 | 9353.3 | **−542.55** |
| 3,000 | occamy-1.0 | warm (n=30) | 3 | 32.0 | 602.0 | **−1781.25** |
| 10,000 | occamy-1.0 | cold | 3 | 2460.0 | 2522.7 | **−2.55** |
| 10,000 | occamy-1.0 | warm | 3 | 13.0 | 298.0 | **−2192.31** |
| 30,000 | occamy-1.0 | cold | 3 | 6492.0 | 3582.0 | **+44.82** |
| 30,000 | occamy-1.0 | warm | 3 | 12.0 | 96.3 | **−702.78** |
| 3,000 | qwen3.5-9b | cold | 3 | 1045.7 | 2163.3 | **−106.89** |
| 3,000 | qwen3.5-9b | warm | 3 | 1030.0 | 2119.0 | **−105.73** |
| 10,000 | qwen3.5-9b | cold/warm | — | — | — | **UNMEASURED** |

`analysis.json` (10 cells, its own aggregation) reproduces every one of these to 3 s.f. — the
aggregation script is consistent; it is `RESULTS.md`/`cells.json` that are not.

### B3. RESULTS.md / cells.json differences

| cell | RESULTS.md | recomputed | note |
|---|---|---|---|
| occamy 3k/12 cold | L1_unc 2161, −106.8 % | 2162.0, −106.96 % | matches |
| occamy 3k/12 **warm** | 184, **+80.8 %** | 83.3, **−1288.89 %** | **sign flip, 45× off** |
| occamy 10k/12 cold | 2161, −107 % | 2522.7, **−2.55 %** | 4× off, and the sign of the *trend* inverts |
| occamy 3k/30 cold | L1 13,822 over **7 requests** | 9353.3 over **3 runs** | run count contradicts runs.json |
| qwen 3k/12 warm | +31.4 % | **−105.73 %** | sign flip |
| occamy 30k/30 cold+warm, qwen 30k/12 ×2, qwen 30k/30 ×2, qwen 10k ×2 | published cells | **no L1 rows exist** | fabricated cells |

Also overstated: §2 says "a **B** in the last column means the server returned
`prompt_tokens_details: null` — the cache instrument is blind". On the two cells I could check
(qwen 3k/12 cold and warm) the rows report `cache_reporting: true` and non-zero `cached_tokens`,
so "blind" does not describe those rows.

### B4. Cold-cache crossover — **measured, and it crosses**

For **occamy-1.0** the 30,000-char cold L1 cells exist (3 reps, 9 round rows):
`saving_billed = +81.61 %` on the round-summed basis and **+44.82 %** on the per-run basis.
At 10,000 chars it is **−6.31 %** (round-summed) / **−2.55 %** (per-run). So on occamy the
saving **crosses zero between 10,000 and 30,000 and is POSITIVE at 30,000** — it is not still
negative. The round-summed and per-run bases disagree in magnitude because L1's later rounds are
cheap (`cached`), which the per-request billing is what actually pays for; the sign agrees.
For **qwen** the cold 30,000 L1 cell is **ABSENT** (no rows at any 30,000 size) — that half is
**UNMEASURED**, and I do not extrapolate it.

### B5. Verdict the rows support: **CONDITIONAL**

- **Cold cache:** L1 loses at 3,000 (`−106.96 %`), is ~breakeven at 10,000 (`−2.55 %`), and **wins at 30,000** (`+44.82 %`, C0_unc **6492.0** vs L1_unc **3582.0**).
- **Warm cache:** L1 loses in **every** measured warm cell — from `−168.75 %` to `−2192.31 %`; decisively at 30,000/12 occamy, C0_unc **12.0** vs L1_unc **96.3** (`−702.78 %`).
- RESULTS.md's headline — "**Verdict: NEGATIVE** … does not beat inline loading on billed tokens anywhere in the 3 k–30 k range" — is **not what its own rows show** for the cold regime. Its warm-prefix sub-claim ("no corpus size makes L1 stop losing to warm C0") **is** supported in every warm cell that exists.
- The handoff's `status: done` is **overstated**: 4 published cells have zero L1 data, the run/row counts are wrong, and no committed artefact records the 3 reps that `runs.json` actually contains.

Mitigating context for the release gate: the crossover is **not** in `papers/context-cache/MANUSCRIPT.md`
(no lazy-loading section; `grep` for `lazy|crossover` finds only C69 wording) and **not** in
`release/v0.1/experiments`. It does not block the release; it blocks only the claim that this
technique has no operating regime.

---

## CHECK C — the paper and the release copy: **PASS**

| item | measured | expected |
|---|---|---|
| live `wc -l` | **1214** | 1214 ✓ |
| live `grep -c 'CITATION NEEDED'` | **0** | 0 ✓ |
| live sha256 | `37a3f1b34eb43c0c47dc9d41dd02158e6ac000f888b6ee92fe26c93f3ef008cd` | — |
| live `192.168.` | **1** (line 993) | — |
| release sha256 | `9490bba6f3555bbae6ff32ac3df783d92503131c0c1e8254ed7dbe7559d6d700` | `9490bba6…` ✓ |
| release `wc -l` | **1214** | 1214 ✓ |
| release `grep -c 'CITATION NEEDED'` | **0** | 0 ✓ |
| release `192.168.` | **0** | 0 ✓ |

The copies differ by **exactly one line** (`diff -u` shows a single hunk at line 993): live says
`http://192.168.2.168:8012`, release says `http://serving-host` — the release is sanitised of
internal LAN endpoints, which is why the digests legitimately differ.

Live-tree runs (all with `PYTHONDONTWRITEBYTECODE=1`):

| command | exit | decisive line |
|---|---:|---|
| `papers/context-cache/verify_package.py` | **0** | `verify_package: PASS — 69 claims … UNVERIFIED: none` |
| `papers/context-cache/recompute.py all` | **0** | `PASS 43/43`, `GRID GUARD PASS 7/7`, `COVERAGE GUARD PASS 69` |
| `papers/context-cache/recompute_r2.py all` | **0** | `PASS 85/85`, `70/70`, `50/50`, `61/61`, `38/38`, `48/48`, `75/75` |
| `pytest tests/test_gap_closure_ledger.py tests/test_g5_fanout_attribution.py tests/test_paper_g3_bands.py -q` | **0** | `25 passed in 0.09s` |

**LICENSE line 5:** `release/v0.1/LICENSE` L5 is **byte-identical** to
`sed -n '5p' /home/zer0null/Duval/LICENSE` (`cmp` silent; `od -c` prefixes match:
`Required Notice: Copyright As win-Ram-K (https://github.com/As win…`). No git command was run
against the target at all, so no lock-free exception was needed.

---

## Containment

- `release/v0.1/**`, `papers/**`, `experiments/**`: read-only throughout; `verify_package.py`
  was run in place but writes nothing.
- `__pycache__`: none created by me (`PYTHONDONTWRITEBYTECODE=1` on every invocation). The stale
  `experiments/agentic-lazy/crossover/__pycache__/` predates this unit and was not touched.
- Target `/home/zer0null/Duval`: read via `sed`/`cmp` only.

## Assumptions

1. REPRO's "from `cd release/v0.1`" was read as "run the scripts the package ships"; since they
   sit one level down I ran them from `papers/context-cache/` and separately confirmed the
   literal commands exit 2.
2. `saving_billed` uses `uncached = prompt_tokens − cached_tokens`, null `cached_tokens` → 0,
   mean over 3 reps; per-run basis (`runs.json`) reported as authoritative and the round-summed
   basis given because `cells.json` used a third basis and the three disagree.
3. No model server was contacted — this unit verifies artefacts, not re-measurement.
