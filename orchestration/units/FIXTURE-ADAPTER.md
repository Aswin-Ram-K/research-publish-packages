# FIXTURE-ADAPTER

Purpose: bridge authored `consonance.fixture/1` fixtures to the runtime schema
`run_longrun.py:137` requires, without editing either side's artefacts. Bound: 20 tool
calls; used 10. Offline throughout — zero requests.

Deliverables: `experiments/ptr-engine/longrun/adapt_fixture.py` (+ `--all`), six runtime
fixtures under `experiments/ptr-engine/longrun/runtime/`, this card, the handoff.

Mapping decisions (recorded in each runtime file under `adaptation`):
- authored turns carry `{turn, kind, instruction}` — no `question`; mapped instruction -> question.
- `wall_tokens`: no authored fixture states it, so the documented default 65536 is used.
- `bytes_per_token` measured, not guessed: body bytes / tiktoken cl100k_base tokens
  (4.0477–4.2647 across the six).
- item body = the pinned pointer slice; the digest verified is the whole pinned file's
  sha256 against `sources[].sha256` (that is what the authored digests cover).
- A source that cannot be read or whose digest mismatches aborts, naming the source;
  proven with a corrupted digest (refused, no placeholder).

Evidence: `--all` exit 0; dry-runs exit 0 for all six at `--reps 1` (would_send_total
1360) and `--reps 2` (2720) — both under the 4,320 ceiling. `score_longrun.py --help`
exit 0; scoring with an empty log exits 3 "run log is empty" (absence = fail).

Blocker: `score_longrun.py` refuses `consonance.longrun-fixture/1` (exit 3), so runtime
fixtures cannot be scored directly; that file belongs to a later card.
