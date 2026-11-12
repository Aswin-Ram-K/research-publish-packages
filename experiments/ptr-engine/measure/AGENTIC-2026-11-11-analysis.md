| arm | episodes | requests | graded | verified | accuracy | mean prompt | mean cached | folds | dropped | pinned | refetch |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 8 | 128 | 15 | 12 | 0.800 | 9864.1 | 8023.0 | 0 | 0 | 0 | 0 |
| pinned | 8 | 128 | 6 | 5 | 0.833 | 4128.1 | 1873.5 | 38 | 771 | 43550 | 88 |
| compact | 8 | 129 | 6 | 6 | 1.000 | 4153.0 | 1766.7 | 45 | 819 | 44379 | 91 |

Per-episode rows only; solved rate is NOT reported.

| arm | episodes | void | checkpoints | ok | checkpoint accuracy | cost units | cost/ok | mean refetch | mean compactions |
|---|---|---|---|---|---|---|---|---|---|
| none | 8 | 0 | 32 | 12 | 0.375 | 1273054 | 106087.8 | 4.00 | 0.00 |
| pinned | 8 | 0 | 32 | 5 | 0.156 | 288589 | 57717.8 | 5.00 | 4.75 |
| compact | 8 | 0 | 32 | 6 | 0.188 | 304518 | 50753.0 | 5.50 | 5.50 |

`verdict: instrument_ok=True fired=[]`
