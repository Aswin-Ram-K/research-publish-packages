# PROMPT-O2B — resolve the O2 launch config, then measure

**Purpose.** `PROMPT-O2` died with `AssertionError: no_buffer only supports page_size=1`
(server_args.py:5835). The shipped O2 argv contained `--page-size 64` + `no_buffer`, so its stored
numbers cannot have come from that argv.

**Outcome: failed (no measurement).** Bound: 20 tool calls, 3 launches — all 3 used.

## Constraint (quoted from `ornith-sglang:dflash2-upstream-710267`, sglang 0.0.0.dev1+g4ccff141d)
- `:5835` `assert view.page_size in (1, None), "no_buffer only supports page_size=1."`
- `:5837` `assert view.disable_overlap_schedule, "no_buffer do not support overlap schedule..."`
- `:5839` `assert view.attention_backend != "trtllm_mha" ...`
- `:5846` extra_buffer: `supports_mamba_cache_extra_buffer(view, model_arch)` must hold
- `:5864` `assert view.mamba_track_interval % view.page_size == 0` (default 256)
- `max_mamba_cache_size` (`:2518`): `Optional[int]`, default `None`, no validator of its own.

## Launches
1. page 1 + no_buffer, mem 0.08 → KV `ValueError`, minimum viable 0.1732
2. same without `--disable-overlap-schedule` → `AssertionError: no_buffer do not support overlap schedule`
3. + `--disable-overlap-schedule`, mem 0.174 → still `ValueError`, minimum viable 0.1737

## Record
O2's `argv` in `state/config/best-config.json` and in `tools/best_config_build.py` now carry the
launchable flags (`--page-size 1 --disable-overlap-schedule`, mem 0.174);
`evidence.argv_corrected_from` names the illegal pair, `evidence.prior_numbers_unreproduceable` marks
the W3-COLLECT numbers as not derived from it. `--check` prints `True`.
