# CONSONANCE-INTEGRATION — unit card

**Objective.** Fold the 2026-10-25 Consonance package (`handoff from consonance/`, 6 files) onto what this project has
measured, as an integration document whose every mapping is justified by named evidence on both sides. Document only,
zero requests. **Bound 22 calls; used 24 (two over: card line-cap rewrites, see `bound_note` in the handoff). Status: done.**
**Write paths (3, declared, no clashes):** `papers/context-cache/CONSONANCE-INTEGRATION.md`,
`orchestration/handoffs/CONSONANCE-INTEGRATION.json`, this card. **Not edited**, per the card: `RECORD.md`, `CLAIMS.md`,
`MANUSCRIPT.md`, `BOUNDARY-PREREG.md`, any row file.
## Read
Package: `README.md`, `INTERFACE_CONTRACT.md`, `MEASURED_FACTS.md`, `EXPERIMENTS.md`, `DO_NOT_REDO.md`, `handoff.json`.
Candidates: `2026-10-24-sweep.md` + briefs `P1-wall.md`, `P2-zero-hits.md`, `P3-round2.md`. State:
`experiments/ptr-engine/RECORD.md`, `CLAIMS.md` (C50-C69, C53/C55/C57/C58/C62/C63 in detail), `COMPILATION.md`,
`GAPS-INVENTORY.md`, `handoffs/{C0-EQUALINFO,LIVE-CELLS-2}.json`, `experiments/ptr-engine/ADOPTION.md`.
## Checks run here, no requests
- `rows-equalinfo-2026-10-26.jsonl`: vLLM **0/52** report a cached token, `prompt_tokens_details` null 52/52 (handoff
  and card say 45/45); SGLang **46/48** (handoff says 47/48). Direction unchanged; counts corrected in the document.
- Phrase search for the "close enough" aim: **no repo hit** outside corpus data, so the aim is attributed to the
  2026-10-26 operator direction carried in this card and the absence is recorded as a gap, not papered over.
## Verdicts
Convergence: F1/F2 (payload −24.2 % / billed −2.4 %, 0 cached at every step) and `C0-EQUALINFO` (1,911.2 vs 3,524.0
uncached/turn = **1.84x**; accuracy 3/3 both) are **one mechanism measured twice** — payload size is not the lever,
prefix stability is; framed for the gap-closing aim, not a win/lose verdict.
E-status **ANSWERED 0 / PARTLY 4 (E1,E2,E5,E6) / NEW 2 (E3,E4)**; plan **440 calls**, hard stop 180 after E2; vLLM
retired from cache/cost/hit-rate claims, kept for **E4 capability only**.
## Failure modes met
`write` refused the first overwrite until the stub was `read` (fs-observation policy) — one wasted call. `awk` on
`^## C53` found nothing because `CLAIMS.md` rows are table rows, not headings — switched to `grep -n`. E2's 1,407.7
exists in no file on disk: labelled "card figure", not given a citation it does not have.
