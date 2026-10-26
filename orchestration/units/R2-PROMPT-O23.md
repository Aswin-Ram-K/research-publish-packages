# R2-PROMPT-O23 — fill the eight missing cells (O2 = 9B × SGLang, O3 = occamy × vLLM)

**Status:** done — 16 of 16 cells measured (was 8 of 16)
**Card prompt:** "R2-PROMPT-O23 — fill the 8 missing cells: O2 (9B×SGLang) and O3 (occamy×vLLM), docker
over SSH, harness already exists"
**Automated session:** never asked a question; every missing value was resolved from disk and recorded.

## Contract (what this unit owed)

Run the **frozen** `R2-PROMPT` harness — `experiments/context-cache/cells/R2-PROMPT/prompt_r2prompt_cell.py`,
unchanged arms, 71 turns per arm, budget 32768, four arms (P0/P1/P2/P3) — against the two setups that the
previous unit had to record as `unavailable`:

- **O2** = qwen3.5-9b × SGLang, argv = `state/config/best-config.json` → `setups.O2.argv` **verbatim**
- **O3** = occamy-1.0 × vLLM, launched from the argv behind its published numbers
  (`GX10:/home/zer0null/r2/launch-oh2.sh`, the R2-VLLM-FIX/OH1 launch)

Launch path: `ssh -F /dev/null -o BatchMode=yes zer0null@192.168.2.168` + `docker run` on the GX10.
**Never stop `gx10-occamy-nvfp4`.** No Round-1 config substituted. No nulls in rows.

## What ran

| setup | container | endpoint | rows | requests | G0 | run window (UTC) |
|---|---|---|---|---|---|---|
| O2 | `gx10-p-o2` (SGLang, image `72457f09d20e`) | `:8017` | 284 | 368 | `call2_cached 6848` | 10:30:10 → 10:33:40 |
| O3 | `r2o3` (vLLM, image `2c211a1273b4`) | `:8018` | 284 | 366 | `call2_cached 6880` | 10:39:52 → 10:44:22 |

Startup fields verified from `get_server_info` / `docker logs`, not from the config:
O2 `page_size 64, c128_page_size 16, extra_buffer, max_mamba_cache_size 40, mamba_track_interval 256,
enable_cache_report true, max_total_num_tokens 71424`; O3 `block_size 64, prefix_match_unit 16,
mamba_cache_mode align, enable_prompt_tokens_details true, resolved attention block **2112**, KV 12.12 GiB /
895,162 tokens`.

Both containers removed afterwards; `gx10-qwen9b` (stopped for O2's memory fraction) restarted with its
stored production argv at 10:44Z. Restore verified `:8012/health 200` and `:8014/v1/models 200` at 10:52:06Z.

## Findings (numbers are fields of `state/r2-prompt-matrix.json`)

- **Census 16/16** (was 8/16): `measured_cells 16, unavailable_cells 0`.
- **P1/P0 null on O1, O2 and O3** (−7.68 [−51.84, +36.49]; −7.68 [−51.84, +36.49]; +55.65 [−137.50,
  +248.80]); non-null only on O4 (−219.51, −11.7 %).
- **P2/P0 non-null and FAVOURABLE on both new setups**: O3 **−664.48 [−885.34, −443.62] = −51.5 %**
  uncached prefill per turn on a measured **73.1-token** pad, hit 0.4083 → 0.7335; O2 **−74.28 [−124.58,
  −23.99] = −14.0 %** on a measured **96.5-token** pad. This **refutes the previous blanket reading** that
  padding never pays: it pays when the cache unit is fine (16–64) and loses at O4's coarse, misdeclared grid
  (+20.6 %, 606.7-token pad).
- **P3/P1 null on all four setups.** O3's point estimate leans the other way (−140.31, ratio 0.896) and is
  unexplained — it must not be read as "the edit is cheap".
- **P3 survival:** identical collapse on O1 and O2 (1984 → 1024 at the edit turn, 48.4 %); **unmeasurable on
  O3 and O4** (cached 0 in both arms at the edit turn).
- **Quality:** O2 14/20 (0.70), O3 20/20 (1.00) first-32-token mismatches — the pointer form is not
  output-equivalent on any setup.
- **O2 is a live replication of O1's accounting, not a copy**: all 142 P0/P1 rows identical in
  `prompt_tokens` *and* `cached_tokens`, P3 70/71, because the two models share a tokenizer and cache at
  page 64.

## Instrument repairs made here (both proven, neither backfilled)

1. **P3 survival printed a collapse when the control was also 0.** `collapse_fraction 1.0` +
   "did NOT collapse -- measurement suspect" for O3/O4's both-arms-zero turn. Fixed at
   `prompt_r2prompt_cell.py:832-856`: the fraction is `null` unless the control arm still shows its cached
   prefix, and the verdict names the missing denominator. O3's `analysis.json` was re-derived through the
   same function (`p3_survival` otherwise unchanged); O4's file was **not** touched.
2. **The matrix reported O4's instrument as the generic one.** `build_matrix.py`'s unmeasurable verdict said
   "(counter-derived instrument)", which is false for O3 (it reports `prompt_tokens_details` natively); the
   text now names both.

## Deviation recorded, not silently repaired

`setups.O3.argv` in `best-config.json` is **not launchable**: `--model occamy-1.0` is the served name, not a
checkpoint path, and it omits `--trust-remote-code`. The launch therefore used the OH1 argv (the one behind
every published O3 number) and the divergence is pinned in
`experiments/context-cache/cells/R2-PROMPT/o23-launch.json`. The cell's `analysis.json` still carries
best-config's `config_sha256`, so the launch record is the authoritative provenance.

## Files

- `experiments/context-cache/cells/R2-PROMPT/O2/{rows.jsonl,analysis.json,g0.json,quality.json,p2_calibration.json}`
- `experiments/context-cache/cells/R2-PROMPT/O3/{rows.jsonl,analysis.json,g0.json,quality.json,p2_calibration.json}`
- `experiments/context-cache/cells/R2-PROMPT/o23-launch.json` — both containers, argv, startup fields, boot
  and restore times, the two O3 flag divergences
- `experiments/context-cache/cells/R2-PROMPT/prompt_r2prompt_cell.py` — P3-survival fix
- `experiments/context-cache/cells/R2-PROMPT/build_matrix.py` — instrument-neutral verdict
- `state/r2-prompt-matrix.json` — rebuilt, 16/16
- `docs/prompt-system/R2-PROMPT-RESULTS.md` — §1–§9 updated; every number cross-checked against the matrix
- `state/logs/R2-PROMPT-progress.log` — harness progress lines for both cells

## Bound

60 tool calls. Used ≈40, of which 8 were the ssh/docker launcher calls. 734 live requests added (368 + 366).

## Traps recorded (do not repeat)

1. **A heredoc piped into the progress wrapper is swallowed** — `node progress run -- ssh … <<EOF` returned
   exit 0 having run nothing. Write the remote script to a file and `ssh 'bash -s' < file`.
2. **Production containers bind `HostIp 192.168.2.168`, not 0.0.0.0** — a `127.0.0.1` health poll reads `000`
   against a perfectly healthy server. Probe the bound address.
3. **`nvidia-smi` on this GB10 reports `Not Supported` for memory**; free host memory (`free -m`) is the
   capacity signal, and the container's own `available_gpu_mem` line is the one to record.
4. **Do not derive the cache grid from a gcd of a small hot subset** — OH1's 48 became 16 over 284 rows, and
   vLLM's resolved attention block (2112 here, 1088 on the 9B) is a third number again.
