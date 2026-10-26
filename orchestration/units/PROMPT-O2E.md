# PROMPT-O2E — O2 on the production-proven strategy (extra_buffer, page 64)

Purpose: PROMPT-O2 measured `no_buffer` (page 1) and got hit 0 on every arm — a config defect, not an
experiment result. This unit re-runs the same 5-arm battery on `extra_buffer` at page 64, the strategy
production serves, in a NEW cell directory so `cells/PROMPT-O2` survives as the negative control.

Config: `gx10-p-o2`, image `72457f09d20e`, `--gpus all --shm-size=32g --ipc=host`, `--page-size 64
--mamba-radix-cache-strategy extra_buffer --max-mamba-cache-size 40 --enable-cache-report`,
mem-fraction 0.22, ctx 32768, endpoint 192.168.2.168:8017.

G0 (the gate the last cell failed): two identical calls, 11031 prompt tokens; call1 details=None,
call2 `{'cached_tokens': 11008}`.

Result: 355 rows, 5 arms x 71 turns, cached-null 0, non-200 0, 345/355 rows with cached>0 (control: 94),
weighted hit 0.8949. R 600.2 [558.9,641.5]; A 528.9 [521.2,536.5]; C 547.1 [539.5,554.7];
H 962.0 [739.4,1184.6]; C0 711.9 [660.6,763.1]. Deltas: A-R -71.3 [-113.4,-29.2]; C-R -53.1
[-94.8,-11.4]; H-R +361.8 [136.9,586.7]; C0-R +111.7 [47.6,175.8] — all exclude zero.
Against production O1 (A 529.3, C 547.1, C0 709.9) the battery reproduces production within ~3%.

Negative control `cells/PROMPT-O2` (no_buffer, page 1): R 4370.8, A 2300.2, C 2312.0, H 2416.8,
C0 4437.4 unc/turn, hit 0, 94/355 cached>0. Untouched.

Open: `tools/best_config_build.py --check` still rebuilds O2 from `cells/PROMPT-O2/rows.jsonl` with the
no_buffer argv, so it prints False against the corrected `setups.O2`; the fix is a one-block edit in
`tools/`, outside this unit's write paths.
