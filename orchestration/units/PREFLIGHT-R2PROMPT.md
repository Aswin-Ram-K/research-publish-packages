# PREFLIGHT-R2PROMPT — offline launchability pre-flight for the four R2-PROMPT substrates

**Card:** `PREFLIGHT-R2PROMPT`. **Bound:** 18 tool calls. **Permission:** workspace-write.
**Writes:** `state/config/r2-prompt-preflight.json`, `orchestration/units/PREFLIGHT-R2PROMPT.md`,
`orchestration/handoffs/PREFLIGHT-R2PROMPT.json`. **Offline:** 0 model starts, 0 docker verbs,
0 inference requests, no ssh, `.occamy.lock` untouched.

**Why:** R2-PROMPT will spend ~1,600 requests on the four optimised argv in
`state/config/best-config.json`. The defect class that must not recur is a launch that dies on an
illegal flag pair — PROMPT-O2 died with `AssertionError: no_buffer only supports page_size=1.
(sglang/srt/server_args.py:5835 _validate_mamba_no_buffer)` and PROMPT-O2B then burned its whole
launch budget on the KV floor.

## What was done

1. Read `state/config/best-config.json` (sha256 recorded in the report) and quoted O1–O4 argv,
   `config_id`, `config_sha256`, resolved grid.
2. `experiments/context-cache/tools/launch_variant.py` **does not exist** (the whole
   `experiments/context-cache/tools/` directory is absent), so the dry-run was impossible and all
   validators were evaluated **statically** — the card's own fallback.
3. Evaluated the SGLang validators (no_buffer gate, page-size vs mamba-track-interval, mem-fraction
   floor, slot arithmetic) against O1/O2, and the vLLM checks (block divisibility, prefix-match-unit,
   mamba-cache-mode, mtp absence, prompt-token details, quantization) against O3/O4.
4. Traced O2's argv to the launch artefact that actually produced its rows:
   `experiments/context-cache/cells/PROMPT-O2-EXTRA/launch.json` — `config_sha256 652ff99d…`
   byte-identical, `startup_fields` resolved `page_size=64`, `mamba_radix_cache_strategy=extra_buffer`,
   `mamba_track_interval=256`, `mem_fraction_static=0.22`, `enable_cache_report=true`.
5. Emitted `state/config/r2-prompt-preflight.json` with per-setup
   `{launchable, rules:[{rule,status,launch_blocking,evidence,source}], blocker}`.

## Result

| setup | launchable | decisive evidence | remaining caveat |
|---|---|---|---|
| O1 | **true** | live 19 h, `/health` **200** at `192.168.2.168:8012`; `extra_buffer` never enters the no_buffer gate | 0.45 vs the dated 0.4993-class floor — re-read free memory at window start |
| O2 | **true** | argv byte-identical to the PROMPT-O2-EXTRA launch that served 355 rows | none in flags; the **doc** is stale (below) |
| O3 | **true** | 284 rows from this argv; 2096 % 16 == 0 | 2096 % 64 = **48** (grid law broken, not the launch); container torn down |
| O4 | **true** | 1088 % 64 == 0 and 1088 % 16 == 0 per `state/config/startup.txt` | 0.22 vs the 0.15 quoted in BEST-CONFIG §4 — unreconciled |

Slot arithmetic: O1 64/5 = **12.8** implied concurrency against `--max-running-requests 5` (slots not
binding — matches R2-SGL-CAP); O2 40/5 = **8.0** against an unset cap (pass).

## The finding that matters more than the launch checks

`docs/serving-options/BEST-CONFIG.md` — the prose `R2-PROMPT` is told it "may read" — still describes
**O2 as `--page-size 64 --mamba-radix-cache-strategy no_buffer --mem-fraction-static 0.08`**. That is
the exact illegal pair that killed PROMPT-O2, plus a memory fraction below the recorded 0.1732 floor;
`best-config.json` has since been corrected to `extra_buffer` / `0.22` / 355 rows. A unit that launches
from the document instead of the JSON reproduces the original failure. Also unreconciled: O4's stored
`--gpu-memory-utilization 0.22` vs the §4 narrative's `0.15`, and O2's `unc_ci [558.85, 641.49]`
bracketing 600.169 rather than the 669.99 beside it.

## Deviations / assumptions

- No dry-run tool existed; static evaluation substituted (card fallback, reported verbatim).
- The card's "--quantization modelopt_fp4 present only for O4" premise is **corrected**: occamy-1.0 is
  also an NVFP4 checkpoint, so the flag is right on O3 too; the real risk is the model path, which is
  unverified offline.
- No ssh was made to `ls` model paths (the `automated` tag says offline), so three checks are `unknown`
  with the reason recorded, not guessed.
- `best-config.json` was **not** edited.
