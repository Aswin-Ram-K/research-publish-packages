# LIVE-MEAS — four render policies at scale (80 turns x 3 epochs)

## Headline: total uncached tokens (raw)

| epoch | C | A | R | F | R/A | F/A |
|---|---|---|---|---|---|---|
| 1 | 58826 | 74368 | 93684 | 80222 | 1.260 | 1.079 |
| 2 | 58631 | 74437 | 98217 | 79851 | 1.319 | 1.073 |
| 3 | 59335 | 74448 | 98057 | 77933 | 1.317 | 1.047 |

Pooled R/A: mean 1.299 (min 1.260, max 1.319, t95 [1.215, 1.383], df=2), sum-ratio 1.299; U15 reference (40 turns, 2 folds) 1.700x.

## Horizon check (U15's 40-turn window reproduced inside this run)

- R/A over t1_40: mean 1.731 (min 1.705, max 1.768, n=3)
- R/A over t41_80: mean 1.012 (min 0.951, max 1.056, n=3)
- R/A over t1_80: mean 1.299 (min 1.260, max 1.319, n=3)

Pad-adjusted R/A: mean 1.296 (1.256-1.316); F/A mean 1.064; R/F mean 1.219. Pads (E4 control) cost {'R': 2466, 'F': 2044, 'A': 1490, 'C': 1505} uncached tokens by arm.

## Break vs steady-state (arithmetic split of excess over C)

- A: excess 46461 = break 3658 + steady 42803 (break share 0.079); steady 187.7 tokens/turn
- R: excess 113166 = break 5081 + steady 108085 (break share 0.045); steady 474.1 tokens/turn
- F: excess 61214 = break 8960 + steady 52254 (break share 0.146); steady 229.2 tokens/turn

## Fold-count scaling (post-fold reuse lag, tokens; 4 folds at [18, 35, 53, 71])

- R: f1@t18 med 1248/max 1600; f2@t35 med 1088/max 1536; f3@t53 med 384/max 960; f4@t71 med 0/max 512; f1@t18 med 1248/max 1600; f2@t35 med 1088/max 1536; f3@t53 med 0/max 896; f4@t71 med 896/max 1408; f1@t18 med 1248/max 1600; f2@t35 med 960/max 1408; f3@t53 med 0/max 896; f4@t71 med 960/max 1408
  before t40 median 1152.0 (n=99), after t40 median 448.0 (n=78)
  lag +1 turns after a fold: median 896 (n=12)
  lag +2 turns after a fold: median 1344 (n=12)
  lag +3 turns after a fold: median 928 (n=12)
  lag +4 turns after a fold: median 1344 (n=12)
  lag +5 turns after a fold: median 896 (n=12)
  lag +6 turns after a fold: median 960 (n=117)
- F: f1@t18 med 1312/max 1728; f2@t35 med 448/max 960; f3@t53 med 448/max 1408; f4@t71 med 0/max 512; f1@t18 med 1312/max 1728; f2@t35 med 384/max 960; f3@t53 med 64/max 1408; f4@t71 med 448/max 960; f1@t18 med 1312/max 1728; f2@t35 med 0/max 512; f3@t53 med 64/max 1408; f4@t71 med 448/max 1472
  before t40 median 896.0 (n=99), after t40 median 224.0 (n=78)
  lag +1 turns after a fold: median 1280 (n=12)
  lag +2 turns after a fold: median 448 (n=12)
  lag +3 turns after a fold: median 0 (n=12)
  lag +4 turns after a fold: median 448 (n=12)
  lag +5 turns after a fold: median 0 (n=12)
  lag +6 turns after a fold: median 448 (n=117)
- A: f1@t18 med 448/max 960; f2@t35 med 0/max 512; f3@t53 med 960/max 1472; f4@t71 med 0/max 512; f1@t18 med 192/max 512; f2@t35 med 0/max 512; f3@t53 med 960/max 1472; f4@t71 med 448/max 960; f1@t18 med 192/max 512; f2@t35 med 384/max 960; f3@t53 med 960/max 1472; f4@t71 med 384/max 960
  before t40 median 384.0 (n=99), after t40 median 896.0 (n=78)
  lag +1 turns after a fold: median 0 (n=12)
  lag +2 turns after a fold: median 480 (n=12)
  lag +3 turns after a fold: median 0 (n=12)
  lag +4 turns after a fold: median 480 (n=12)
  lag +5 turns after a fold: median 0 (n=12)
  lag +6 turns after a fold: median 448 (n=117)

## Law checks

- E3 two-term append law over 912 append rows: 335 clean (deficit<=0), 6 grid-only (0<d<=64), 308 exactly one trailing body, deeper lag {'2': 104, '3': 78}, unexplained 81 (deficit histogram top: [(0, 335), (448, 239), (512, 71), (960, 62), (896, 45), (1344, 34)])
- E4 multiple-of-64: 3 rows at residue 0 of 960; 195 rows padded; min distance to a multiple 0
  - residue 0: e1 F t53 (prompt 2176)
  - residue 0: e1 A t19 (prompt 9792)
  - residue 0: e2 A t31 (prompt 15232)

## Epoch warmth

- epoch 1 t10: R prompt 5394/cached 4928, F prompt 5339/cached 4864, A prompt 5366/cached 4864, C prompt 5347/cached 4864 | prompts identical False, cached identical False
- epoch 1 t17: R prompt 8596/cached 7680, F prompt 8533/cached 7616, A prompt 8534/cached 7616, C prompt 8525/cached 7616 | prompts identical False, cached identical False
  t1 cached {'R': 0, 'F': 0, 'A': 0, 'C': 0} (all zero True)
- epoch 2 t10: R prompt 5347/cached 4864, F prompt 5355/cached 4864, A prompt 5356/cached 4864, C prompt 5354/cached 4864 | prompts identical False, cached identical True
- epoch 2 t17: R prompt 8525/cached 7616, F prompt 8507/cached 7616, A prompt 8508/cached 7616, C prompt 8506/cached 7616 | prompts identical False, cached identical True
  t1 cached {'R': 0, 'F': 0, 'A': 0, 'C': 0} (all zero True)
- epoch 3 t10: R prompt 5358/cached 4864, F prompt 5358/cached 4864, A prompt 5358/cached 4864, C prompt 5358/cached 4864 | prompts identical True, cached identical True
- epoch 3 t17: R prompt 8510/cached 7616, F prompt 8510/cached 7616, A prompt 8510/cached 7616, C prompt 8510/cached 7616 | prompts identical True, cached identical True
  t1 cached {'R': 0, 'F': 0, 'A': 0, 'C': 0} (all zero True)

Order: ['R', 'F', 'A', 'C'] in all 3 epochs; salts fresh per (epoch, arm). Every arm runs its full 80 turns from t1; no mid-chain cold start anywhere.
