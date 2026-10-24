# E3C — `e3-record-correction`

**Status:** done. 0 live requests, no lock, no re-measurement. Record repair of E3 from VE13's verdict.
**Parent:** `session-79bf48c9-4a77-41e0-8f20-b838599872a0`. **Automated session: no `ask_user_question`.**
**Precedent:** `U8.47` repairing `U8.40.json`.

## Purpose (one only)

Apply the verifier's corrections to **E3's record**, so no later unit cites a statement the rows do not
license. Additive only: no author value is deleted or overwritten; every original is quoted beside its
corrected form. `experiments/context-cache/cells/E3/*` is untouched (read-only input here).

## Inputs read

`orchestration/handoffs/VE13.json`, `orchestration/units/VE13.md` (checks 7-9, `overstated[0..2]`,
`corrections[1..2]`), `orchestration/handoffs/E3.json`, `orchestration/units/E3.md`, and under
`experiments/context-cache/cells/E3/`: `e3_analyze.py`, `e3_rows.jsonl`, `e3_replicate_rows.jsonl`,
`e3_report.json`, `e3_server_state.json`, `e3_metrics.jsonl`.

## Corrections applied (4)

### 1. Headline word → NOT ESTABLISHED

- Original (`E3.md:4`, `E3.json.evidence.verdict`): `G7 hypothesis REFUTED (mamba checkpoint eviction)`.
- Corrected: `G7: mamba checkpoint eviction NOT ESTABLISHED (universal attribution refuted; mechanism
  unestablished)`. Licensed word for the mechanism is **not established**: pool-scale gauges only, no
  per-chain checkpoint counter, a 3-append pressure manipulation that moved the deficit 0,0, and 4/35
  repeats still losing state. **"Refuted" survives only** for the universal claim that mamba
  checkpointed-state eviction explains the append deviation on this server. Scope: 35 appends, one hybrid
  endpoint (`occamy-1.0 @192.168.2.168:8012`), one U4-shape replication — not "universally" (VE13 check 9).
- Original wording is preserved in `E3.md` (`## Corrections` quote) and in `E3.json.verifier_corrections[0]`;
  the corrected headline is added as `E3.json.corrected_headline` + `E3.json.evidence.verdict_corrected`.

### 2. Histogram provenance → two series, both stated

- Original: `deficit histogram {0:31, 192:2, 768:1, 832:1}` (`E3.json.evidence.decomposition`, `E3.md` Result).
- **Stored-row series** — the `deficit` field as written by the driver in `e3_rows.jsonl`, n=35:
  `{0:30, 192:2, 768:1, 832:1, -1728:1}`.
  Command: `.venv/bin/python -c "import json,collections;rows=[json.loads(l) for l in open('experiments/context-cache/cells/E3/e3_rows.jsonl') if l.strip()];ap=[r for r in rows if r['kind']=='append' and r.get('error')==''];print(len(ap),sorted(collections.Counter(r['deficit'] for r in ap).items()))"`
  → `35 [(-1728, 1), (0, 30), (192, 2), (768, 1), (832, 1)]`.
- **Recomputed salt-scoped series** — `e3_analyze.py:120-136`: the previous prompt is the previous request
  **with the same salt**, `deficit = 64*(L_prev//64) - cached`; authoritative per
  `e3_report.json.recomputed_rows`, `decomposition.deficit_append{n:35,min:0,max:832}` — n=35,
  `{0:31, 192:2, 768:1, 832:1}`. This is the series the headline, the `31/35` and the report quote.
  Command: `.venv/bin/python experiments/context-cache/cells/E3/e3_analyze.py`, then the verbatim loop
  below (0 live requests, 1 mismatch):

  ```python
  import json, collections
  G = 64; prev = {}
  rows = [json.loads(l) for l in open('experiments/context-cache/cells/E3/e3_rows.jsonl') if l.strip()]
  for r in sorted(rows, key=lambda r: r['seq']):
      pL = prev.get(r['salt'])
      if r['kind'] in ('append', 'repeat') and pL is not None:
          r['deficit'] = G*(pL//G) - r['cached_tokens']
      if r['kind'] != 'interleave':
          prev[r['salt']] = r['prompt_tokens']
  ap = [r for r in rows if r['kind'] == 'append' and r.get('error') == '']
  print(len(ap), dict(sorted(collections.Counter(r['deficit'] for r in ap).items())))
  # -> 35 {0: 31, 192: 2, 768: 1, 832: 1}
  ```
- **The negative −1728 is explained, not papered over.** Row `seq=101`, salt `f5a38d9edaa8cd0d`, chain
  `p60`, round 2, `L=2806`, `cached=1984`, stored `prev_prompt_tokens=269`. 269 is the immediately
  preceding **interleaved fresh-salt probe**, not the chain predecessor (`L_prev=2019`); the stored driver
  field, not the deficit rule, is contaminated. `64*(269//64) = 256`, `256 - 1984 = -1728` reproduces the
  stored value exactly; against the chain predecessor, `64*(2019//64) - 1984 = 0`. Classification:
  **explained — aggregation artifact of the driver's `prev_prompt_tokens` field** (not clamping, not a
  genuine negative deficit); it is the single `deficit_recomputed_vs_driver_mismatch: 1`.

### 3. Identity wording → tail term, not residual

- Original (`E3.md` Result, first bullet; `E3.json.evidence.verdict`): `residual == L - 64*floor(L_prev/64) - L%64`.
- Corrected: **`tail_term = L - 64*floor(L_prev/64) - L%64`**, and **`residual = tail_term + deficit`**.
  The displayed `L - 64*floor(L_prev/64) - L%64` form is the *tail term* and equals `residual` **only where
  `deficit == 0`** — 31/35 appends; on the other 4 the residual exceeds the tail term by 192, 192, 768, 832.
  Stored as `E3.json.corrected_facts.identity`; the original sentence stays in `## Result`.

### 4. Snapshot count → 44

- Original: `43 metrics snapshots` (`E3.json.evidence.gets`, `mamba_pool.trajectory`, `E3.md` Result).
- Corrected: **44** snapshots. `wc -l experiments/context-cache/cells/E3/e3_metrics.jsonl` → `44`;
  the probe's 44 GETs = 2 info + 42 metrics, i.e. 46 GETs including `/server_info` and `/get_model_info`.
  Stored as `E3.json.corrected_facts.metrics_snapshots`.

## Bound (hit)

≤ 12 tool calls (used 8), ≤ 10 min, 0 live requests, no lock acquisition, no writes outside the three
paths below. `cells/E3/*` not modified (read-only inputs).

## Write paths (mine alone)

`orchestration/units/E3C.md`, `orchestration/handoffs/E3C.json`, `orchestration/units/E3.md`
(corrections section + headline only), `orchestration/handoffs/E3.json` (additive keys + corrected
headline string only; original 7 contracted keys + `assumptions` intact).

## Result

E3's record now states the licensed word, both histogram series with the −1728 explained, the tail-term
identity, and 44 snapshots. `E3.json` parses and its original keys are byte-identical; the additions are
`verifier_corrections[4]`, `corrected_headline`, `corrected_facts`, `corrections_meta`, and
`evidence.verdict_corrected`. **Later units should cite `orchestration/handoffs/E3C.json` for the corrected
headline/identity/series; `E3.json.evidence.verdict` is superseded wording.**
