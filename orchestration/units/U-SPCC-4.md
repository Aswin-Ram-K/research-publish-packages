# U-SPCC-4 — Serving launch script + decision docs

Status: done

## Write paths
- /home/zer0null/research extractor/experiments/ptr-engine/serving/launch-sglang-spcc.sh
- /home/zer0null/research extractor/docs/serving-options/FORK-DECISION.md
- /home/zer0null/research extractor/experiments/ptr-engine/serving/REMOTE-ROOT.md
- /home/zer0null/research extractor/orchestration/units/U-SPCC-4.md
- /home/zer0null/research extractor/orchestration/handoffs/U-SPCC-4.json

## Summary
Captured live invocation from container gx10-occamy-nvfp4 (image 72457f09d20e)
via ssh docker inspect. Mirrored it verbatim into launch-sglang-spcc.sh, adding
--enable-hierarchical-cache (live reported false), keeping --page-size 1,
--kv-cache-dtype fp8_e4m3, --enable-cache-report, --mamba-radix-cache-strategy
extra_buffer. mem-fraction-static stays 0.45 with arithmetic in comment.
--dry-run prints command and exits 0. Refuses to start if MEM-WINDOW.json present.

FORK-DECISION.md: no fork; three criteria; image tag + version recorded.
REMOTE-ROOT.md: remote writes blocked by default; proposed root as proposal only.
