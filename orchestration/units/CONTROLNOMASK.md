# CONTROLNOMASK

Control arm masking-no-fetch with masking disabled (WINDOW_TURNS=100 via sitecustomize patch of arm_cd.WINDOW_TURNS, least invasive: no source edit; cutoff t-100 <=0 for all 48 turns so mask_old_turns never runs). Dry-run: 48 requests, masked_rows 0; turn-1 tool_outputs body present in prompt at turn 20 (turn_block renders bodies unmasked).

Live run: 48 requests, 0 truncated, all 48 answers from content. Score: 14/14 (12 checkpoints pass). Interpretation: with the fact visible the whole time, masking-no-fetch scores 12/12, so masking (not model incapacity) causes the treatment arm's 0/12.
