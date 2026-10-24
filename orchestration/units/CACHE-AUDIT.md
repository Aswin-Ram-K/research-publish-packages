# CACHE-AUDIT — did we run the best documented cache options, or just the ones we happened to try?

**Trigger.** Task-board card, `[automated]` tag; no human present. Bound: answer from docs + rows
already on disk, **0 live inference requests**. Prompts/answers for the engines under audit
(SGLang, vLLM) are documentation, so network doc fetches were used and every claim carries a URL.

**Question.** The package's cache statements all say "measured knob X did not help". That is only
load-bearing if X is what the engines document as best. This unit counts what was tried, reads
what the pinned docs say the levers are, and re-checks the package's two cache *rejections*.

**What was done**
1. Tallied the flags actually launched (`cells/WIN-SGL/logs/*-config.json`,
   `cells/TUNED/logs/variant-launch.json`, `cells/WIN-VLLM/*`), and the offload/host-tier
   settings in every captured `server_info`/`/metrics`.
2. Pinned the SGLang and vLLM docs (SGLang `main` `docs/docs/advanced_features/*.mdx`; vLLM
   `v0.27.1` tag source, because the box runs 0.27.1 and `latest` docs would be the wrong
   version) into `scratch/cache-audit/docs/` with sha256.
3. Re-checked two rejections against their cited sources.
4. Appended `GAPS.md` **G16**, withdrew `PACKAGE.md` §4's HiCache claim, corrected three
   overreaching `SERVING-BRIEF.md` lines, re-ran the brief guard and the package verifier.

**What is deliberately NOT written here.** No divergence from AGENTS.md was taken. `tests/test_gap_closure_ledger.py`
now fails on G16 by design (the ledger's owners re-derive it); that is stated in the GAPS.md
header and in the handoff rather than hidden by editing another unit's artifact.

**Handoff:** `orchestration/handoffs/CACHE-AUDIT.json`.
