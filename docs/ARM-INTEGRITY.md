# ARM-INTEGRITY — do the four arm labels name four behaviours?

**Unit** ARM-INTEGRITY · **auditor** (read-only; no runner, arm, row, fixture or report edited) ·
**offline** (zero inference requests; every number below is arithmetic over files on disk) ·
**date** 2026-10-26.

Sources pinned by sha256 (all read, none edited):

| file | sha256 |
|---|---|
| `experiments/ptr-engine/longrun/run_longrun.py` | `939c225c052319b91ef7df0e69678b85ae855fc9bb3fbf293441b7bafb99b1c3` |
| `experiments/ptr-engine/longrun/client.py` | `5aa23bb5470b7e0909992b3f0947867953ba39204e5d03eff0f95c30e57ca7bb` |
| `experiments/ptr-engine/longrun/analyze_stats.py` | `2c9756f3f6cf9c07174cda290a86cc506b0d608bd1c9a0dc6884540c966b2d1c` |
| `experiments/ptr-engine/longrun/cell.py` | `fd4f2b01a6bfdeea425a92de428f770bf9f07fbe3bdc3b1d8cfd1f4a17ee2ec6` |
| probe (re-derivable) | `/tmp/arm_integrity_probe.py` — `python3 /tmp/arm_integrity_probe.py` → `PROBE PASS`, exit 0 |

Rows read: `experiments/ptr-engine/measure/rows-longrun-2026-10-26.jsonl` (192),
`rows-longrun-c-2026-10-26.jsonl` (192), `rows-longrun-v3-2026-10-26.jsonl` (96),
`rows-longrun-v4-2026-10-26.jsonl` (96), `rows-longrun-v4-tools-2026-10-26.jsonl` (68),
`rows-longrun-v5-tools.jsonl` (72), `rows-longrun-v6-tools.jsonl` (72) — **788 rows**.
Fixtures: the 7 `experiments/ptr-engine/longrun/tasks-*/runtime-*/LR-01*.json` runtime fixtures,
all resolved by the `fixture_sha256` carried in the rows.

## 1. Mechanism per arm (code, as read)

One dispatch: `Planner.build`, `run_longrun.py:1052`; the four branches are disjoint `if` arms,
`run_longrun.py:1057` (grow), `:1076` (compact), `:1094` (pointer), `:1112` (lease).

- **transcript-grow** — `working_set_block(fixture)` + one `turn_block(...)` per prior turn +
  current question; at the declared wall `parts.pop(0)` (FIFO from the front), `run_longrun.py:1063`;
  byte-slice fallback `:1067`);
- **transcript-compact** — same replay, but at the wall a separate **digest request** replaces the
  older turns with a ≤700-token digest and keeps the last 4 raw turns
  (`run_longrun.py:1080-1091`, digest request built at `:1086`, `raw = raw[-4:]` at `:1089`);
- **pointer-stable** — `INDEX` + `index_lines(fixture)` + the bodies of `items[:min(t+1,N)]`,
  then a non-authoritative tail: 3 short state lines + current question
  (`run_longrun.py:1094-1110`); nothing before the tail is rewritten, so the prefix is
  **append-only** and cacheable;
- **lease-reopen** — `INDEX` + `index_lines` (no bodies) + a host-distilled ≤1800-byte state line
  (`_distill`, `:1026`) written at each wall, lease counter incremented (`:1113-1116`).

So the four are **four different code paths**, not four label values: `Planner.build` returns
prompts of different construction, and `ARMS` (`run_longrun.py:64`) is only the key list.

## 2. Pair matrix — how any two differ, in one line

| pair | difference in one line | verdict |
|---|---|---|
| grow × compact | at the wall: FIFO-drop from the front vs digest request + keep last 4 | **distinct-in-code-only** |
| grow × pointer | full replay of every prior turn vs frozen index + ≤4 bodies + 3-line tail | **distinct** |
| grow × lease | growing replay vs index-only, state-free, no bodies | **distinct** |
| compact × pointer | digest-at-wall replay vs append-only index prefix | **distinct** |
| compact × lease | digest-at-wall replay vs index-only flat prompt | **distinct** |
| pointer × lease | index **+ item bodies** + 3-turn tail vs index **lines only**, no bodies, no tail | **distinct** |

The one non-`distinct` verdict is argued in §5.

## 3. Signature from the ROWS (counts, per arm)

| arm | signature the mechanism predicts | observed | rows lacking it |
|---|---|---|---|
| transcript-grow | prompt tokens climb with turn index; `evicted>0` after the wall | climb present (§4); **`evicted>0` in 0 of 192** turn rows (4 complete grids) | cap branch untested |
| transcript-compact | a `kind:"digest"` row at each wall; growth with sawtooth resets | **`kind:"digest"` rows: 0 of 788**; prompts climb 75–120 tok/turn monotonically; identical to grow at T1–T6 (6 shared `prompt_sha256`, stage1) / T1 (1 shared, C-V2) | **compaction never fired** |
| pointer-stable | small T1, ramp to a plateau bounded by `items` (N=4), no transcript-sized prompt; tool grids carry fetch rounds + `pinned_lines` | T1 723–3520 tok, plateau by ~T7, slope 2.7–4.9 tok/turn; **0 shared `prompt_sha256` with any other arm**; `fetch_rounds_used` cumulative 1→24 (v5) / 0→20 (v6); 37 `pinned_lines` occurrences inside `tool_calls` (v6) | none |
| lease-reopen | `lease` increments at walls; prompt resets at T23/T53 | **`lease == 1` on 96 of 96 rows** (stage1 + C-V2); prompt flat 178–434 tok | **reopen never fired** |

Row fields that would have shown the missing signatures, and are either absent or never
non-default: `evicted` (present, always 0), `kind:"digest"` (a row kind the runner writes and
`Planner.replay` reads at `run_longrun.py:1045` — never emitted), `lease` (present, always 1).
The pointer arm's *defining* identity field `prefix_sha256` is computed at `run_longrun.py:1098`
but **is not in `make_row`'s dict** (`run_longrun.py:1563-1690`) and appears in **0 of 788** rows —
so pointer identity is provable only from `prompt_sha256` + the growth signature, not from the
prefix digest the planner already knows.

## 4. The decisive test — prompt-token slope against turn index

OLS of `prompt_tokens` on `turn`, one row per turn (all rows here are `kind:"turn"`, so n = turns):

| grid (rows file) | transcript-grow | transcript-compact | pointer-stable | lease-reopen |
|---|---|---|---|---|
| stage1 (`rows-longrun-2026-10-26`) | **38.79** (n=48, 1870→3681) | **119.88** (n=48, 1870→7124) | **4.07** (n=48, 723→1898) | **-0.01** (n=48, 189→178) |
| G4 / RUN-C-V2 (`rows-longrun-c-2026-10-26`) | **676.96** (n=48, 2114→34279) | **74.98** (n=48, 2114→5640) | **4.44** (n=48, 967→2197) | **-0.01** (n=48, 433→422) |
| v3 (`rows-longrun-v3-2026-10-26`) | **60.89** (n=48, 2154→5006) | — | **4.68** (n=48, 1007→2245) | — |
| v4 (`rows-longrun-v4-2026-10-26`) | **61.01** (n=48, 4020→6887) | — | **4.85** (n=48, 2873→4117) | — |
| v4-tools | — | — | **2.72** (n=48, 3033→4196) | — |
| v5-tools | — | — | **-14.35** (n=48, 3515→4237) | — |
| v6-tools | — | — | **-24.25** (n=48, 3520→4247) | — |

**Does `pointer-stable` grow like a transcript? No, in every grid.** Pointer slope is 2.7–4.9
tok/turn and plateaus at ~2.2k (G4) / ~4.2k (tools); transcript-grow is 38.8–677 tok/turn and
reaches 34,279 tok. The negative slopes in v5/v6 are tool-fetch **transients** (v5 T3 = 9,771 tok,
v6 T4 = 7,219 tok) on an otherwise flat steady state (~4,230–4,250 tok from T5 on); they are not
growth and not compaction. Pointer's own plateau is explained by the fixture: **`items = 4`** in
every runtime fixture, and the prefix pins `items[:min(t+1,4)]`, so from T3 the body set is fixed.

## 5. The one finding: the cap is never reached, so three arms are degenerate as run

`wall_tokens = 65536` in **all 7** runtime fixtures; `lease_reopen_turns` is **absent** in **all 7**
(§6). The largest prompt observed anywhere is **34,279 tok** (G4 grow, T48) — **52.3 % of the wall**.
Consequences, each counted:

1. **transcript-grow** never evicts (`evicted>0` = 0/192). It is a pure replay arm.
2. **transcript-compact** never digests (`kind:"digest"` = 0/788). Below the wall its prompt is
   `working_set_block + all turn blocks` — *the same bytes as grow*: 6 shared `prompt_sha256`
   (T1–T6, stage1) and 1 (T1, G4) prove the two arms run the same code path until they diverge from
   **answer-length drift**, not from the mechanism. `expected_digests(fixture)` still reserves **2**
   digest requests per cell (`run_longrun.py:1133-1135`, used in `projected_requests` `:424`), so the
   request allocation over-declares by 2 per compact cell.
3. **lease-reopen** never reopens: `self.walls = fixture.get("lease_reopen_turns") or []`
   (`run_longrun.py:1004`) is `[]`, so `lease` stays 1 on 96/96 rows and the arm measures a
   *static index-only* prompt. The module docstring still claims walls at turns 23/56
   (`run_longrun.py:20-21`) and `expected_digests` claims 23 and 53 (`:1134`) — neither is in any
   fixture on disk.

Hence **grow × compact = `distinct-in-code-only`**: the mechanism differs in code, the rows cannot
show it, and the field that should have shown it is a `kind:"digest"` row (plus `evicted>0` on the
grow side). The other five pairs are `distinct` and their rows show it.

Nothing here is a *mislabel*: no row is labelled `pointer-stable` while carrying a transcript
prompt — pointer shares **0** `prompt_sha256` with any other arm and never exceeds 9,771 tok
(v5 T3 transient). The pointer engine is on the path in the tool grids: `fetch_rounds_used` is
non-zero and cumulative per turn, `tool_calls` entries carry `pinned_lines` and
`served_from:"prompt"` (v6 T1: `pinned_item resolve.py`, `pinned_lines 36-110`).

## 6. Cross-grid consistency of the `pointer-stable` label

- All 7 runtime fixtures carry `N=48`, `wall_tokens=65536`, `items=4`, `lease_reopen_turns=None`,
  differing only in `task_id`/content (`fixture_sha256` per grid: stage1 `72c3832d…`,
  G4 `0a07db1b…`, v3 `07abab0b…`, v4 `5a5f8c4b…`, v4-tools `a592a48f…`, v5/v6-tools `5bf5f639…`).
- **`provenance`/`harness_sha256` cannot answer implementation identity.** No row carries a
  `harness_sha256` or `code_sha` (key union over all `measure/rows*.jsonl` has neither), and the
  manifests (`experiments/ptr-engine/longrun/manifests/*.json`, **92 files**) carry
  `N, arm, created_utc, dry_run, engine_flags, fixture, model, prediction, prereg, renderer, rep,
  rows_path, run_id, schema` (+ optional `thinking`×31, `tools`×7, `provenance`×3, and a few one-off
  blocks) — and **not one of the 92 carries a key containing `sha`**: no commit, no runner sha.
  This is stated as a gap, not assumed.
- One **observable** cross-grid difference inside the same label: v5-tools and v6-tools share
  `fixture_sha256 5bf5f639…`, yet the pointer T1 prompt (no history — a pure function of fixture +
  renderer) is **3,515 tok in v5 and 3,520 tok in v6**, with different `prompt_sha256` and different
  `run_manifest_sha256`. So `pointer-stable` in v5tools2 and in v6 are **not byte-identical
  renderings**; the runner's own v6 comment (`run_longrun.py:223`, "PROBE-CP3-V6: DO NOT PAY FOR
  LINES THAT ARE ALREADY IN THE PROMPT") says the v6 fetch path was edited. Which build produced
  each cell cannot be attributed from the record — only that they differ.

## 7. What a finding invalidates

The published record keys latency and accuracy by `arm` (e.g. `measure/P95-POWER.json` carries
per-set entries such as `rows-longrun-c-2026-10-26::transcript-compact` and the
pointer×grow disjointness test implemented in `measure/p95_power_gen.py:169-187`; any p50/p95 table
in `measure/LATENCY-REPORT.json` / `docs/LATENCY-REPORT.md` groups the same way).

- **Survives**: every `pointer-stable` vs `transcript-*` comparison. Pointer is a different prompt
  construction in code and in rows (slope 2.7–4.9 vs 38.8–677; 0 shared prompt bytes). The
  pointer-vs-grow p95 disjointness test is **not** comparing a thing with itself.
- **Not licensed by these rows**: (a) any claim that `transcript-compact`'s **digest/compaction**
  changed a number — the digest never ran (0 rows); grow and compact below the wall are the same
  prompt construction. P4 ("B within 2x of C on p95 but fails t30") is untested, not refuted.
  (b) any claim resting on grow's **FIFO eviction** at the cap — 0 evictions; P2's "hits the wall at
  N=60" is untested. (c) **all** `lease-reopen` numbers, including P3 ("lowest p95 TTFT but loses
  t30/t60 accuracy"): the arm never reopened, so those rows measure a static index-only prompt.
- **Unchanged**: the four-arm labels are not collapsed — the audit found no mislabel — but three of
  the four arms' *pre-registered* behaviours are unexercised at the 48-turn × 64k configuration, so
  the arm comparison is, in this grid, really a two-mechanism comparison
  (`pointer-stable` vs "replay everything", where the two replay arms differ only by drift).

## 8. What this audit could not prove

1. Nothing about runs whose rows are not in the 7 files above (`rows-longrun-2026-10-26-fix`,
   `-policy`, `rows-pilot-thinking`): they are 3–31-row fragments; their `arm` fields were counted
   but no slope is claimed for them.
2. That any two runs share a **runner build** — the record carries no code sha (§6).
3. A *behavioural* difference between grow and compact **at or above the wall** in any grid — none
   exists to observe: no cell in any grid crossed 65,536 prompt tokens.
