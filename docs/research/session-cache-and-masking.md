# Session-aware cache and observation masking — what is published, what is ours

Record: [`measure/research/session-cache-and-masking.json`](../../measure/research/session-cache-and-masking.json).
Protocol: [`docs/RESEARCH-PROTOCOL.md`](../RESEARCH-PROTOCOL.md). Retrieved 2026-11-04. Live model
requests spent on this note: **0**.

**Question:** Does the installed SGLang build support session-aware radix caching, and what does the
observation-masking result license for a cache-adjusted cost comparison on our stack?

## Sources

| id | source | retrieved | version scope |
|---|---|---|---|
| s1 | https://docs.sglang.io/docs/advanced_features/session_radix_cache | 2026-11-04 | current-main, unversioned — **not** the build at `:8012` |
| s2 | https://arxiv.org/abs/2508.21433 (Lindenbauer et al., 2025-08-29) | 2026-11-04 | arXiv:2508.21433 |

Local checks were run read-only inside the production container (`gx10-occamy-nvfp4`, version
`0.0.0.dev1+g4ccff141d`, image `sha256:72457f09…`) and against `GET /get_server_info`.

## Verified

**V1 — what the feature is (s1).** Enabled with `--enable-session-radix-cache`; implemented only by
`UnifiedRadixCache`; the application passes a top-level `session_id` on every request and calls
`POST /close_session` when the session ends. Protection is reference, not pinning: "Referenced KV can
still be evicted when reclaiming unreferenced KV is insufficient." Eviction drains unreferenced nodes
first, then referenced nodes with fewer session references, then the configured policy.

**V2 — component accounting (s1).** Each UnifiedRadixCache component is tracked separately with
cascade rules: evicting a full-attention node evicts its SWA and Mamba data; evicting SWA evicts Mamba;
evicting Mamba affects only Mamba.

**V3 — the build has it (local, s1 semantics).**

| check | result |
|---|---|
| `server_args.py` carries the flag | present, same semantics in its help text |
| `mem_cache/unified_radix_cache.py`, `unified_cache/session_ref_tracker.py` | present |
| `registry.py` builds `UnifiedRadixCache`, appends the **MAMBA** component when `ctx.is_hybrid_ssm` | present |
| `/close_session` route | `http_server.py:1567` |
| `session_id` in the OpenAI protocol models | `protocol.py:371, 840, 1548` |
| running configuration | `enable_session_radix_cache=false` |

So the feature is **available, compiled in, and switched off**. Enabling it is a restart with a
different flag set — a different `engine_fingerprint` under the interface contract, not a tuning change.

**V4 — masking's published result (s2).** In SWE-agent on SWE-bench Verified across five model
configurations, "a simple environment observation masking strategy halves cost relative to the raw
agent while matching, and sometimes slightly exceeding, the solve rate of LLM summarization". A hybrid
masking+summarization variant cuts cost a further 7 % (vs masking) and 11 % (vs summarization); initial
evidence generalises to OpenHands.

## Inferred

**I1 — the session cache cannot be adjudicated by this pilot.** It changes eviction *order under
memory pressure* and nothing else: it does not alter what the model sees, does not pin KV, and does not
raise the reuse ceiling. Pilot prompts are 5–40 K tokens against a ~1.58 M-token pool — two orders of
magnitude below the pressure where ordering matters. Where pressure *was* applied (STATE-CLIFF),
residency could only be bracketed within ≥128 documents
([`RESIDENCY-BOUNDS.md`](../../experiments/context-cache/cells/STATE-CLIFF/RESIDENCY-BOUNDS.md)). A feature
whose entire effect lives inside that bracket cannot be judged here. It is therefore recorded as
available-but-off and must not be credited with any measured difference.

**I2 — whether the OpenAI-compatible route honours `session_id` is unknown.** The field's presence in
the protocol models (`protocol.py:371, 840, 1548`) is necessary, not sufficient. Testing it needs a
variant container with the flag on; the answer would not change a single pilot number, so it stays open.

**I3 — the paper's cost axis does not transfer.** s2 prices provider tokens in a hosted setup and
reports no KV reuse and no uncached prefill. Our gate is cache-adjusted cost per verified success — a
different quantity, on a different model and engine.

**I4 — masking is a prefix rewrite, so it can invert here.** Masking removes earlier observation text
from the prompt. On a prefix-caching engine that can *raise* uncached prefill while lowering payload —
the exact conflation this workspace already paid for (payload −24.2 % / billed −2.4 % on one change,
`handoff from consonance/DO_NOT_REDO.md` §1). s2 therefore licenses a **quality** hypothesis (masking
need not hurt correctness) and not a cost result for us.

**I5 — one cheap GPU price schedule does not exist.** No trustworthy per-token price for this host is
recorded anywhere in the workspace, so the promotion gate must use uncached-input + output token counts
as a labelled proxy and must not call the difference dollars. (This one is a workspace fact, not a
source claim.)

## Contradicted

None. No observation on our stack disagrees with either source: the vendor page's feature is present in
the build and simply switched off, and the paper makes no claim about KV reuse that our rows could
contradict.

## What this changes

- The session cache is **not** a pilot candidate; it is a separate fingerprinted experiment requiring a
  restart, with no discriminating test available at pilot pressure.
- Arm C (masking + one checkpoint) keeps its quality prior from s2 but must still win on
  **cache-adjusted** cost per verified success measured on our rows, because I4 says the paper's axis
  can invert here.

## Open questions

- Does chat/completions honour `session_id` on `0.0.0.dev1+g4ccff141d`? Needs a variant container.
- Marginal prefill cost per uncached token on this box — a measurement (E1/E2), not research.
