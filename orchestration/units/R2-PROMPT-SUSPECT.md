# R2-PROMPT-SUSPECT — is the O4 prompt cell real?

**Status:** done (offline audit, 0 live requests, 21/22 tool calls) · handoff `orchestration/handoffs/R2-PROMPT-SUSPECT.json` · log `state/logs/r2-prompt-suspect.json`
**Question:** O4's P1-P3 hit fractions (0.21-0.27) sit BELOW P0 (0.85) and P3's mid-edit did not collapse — is the cell real?

## Answer: yes — both red flags are misreadings, the cell's rows are sound

### Rebuilt from rows (71 turns x 4 arms x 2 setups, 568 emits, all 200)
| setup | arm | unc/turn | hit | prompt total | gcd | off-grid |
|---|---|---|---|---|---|---|
| O1 SGLang | P0 | 530.39 | 0.9569 | 874010 | 64 | 0/71 |
| | P1 | 522.72 | 0.7701 | 161465 | 64 | 0/71 |
| | P2 | 541.75 | 0.7713 | 168192 | 64 | 0/71 |
| | P3 | 520.55 | 0.7720 | 162079 | 64 | 0/71 |
| O4 vLLM | P0 | 1883.86 | 0.8470 | 874010 | 1056 | 65/71 |
| | P1 | 1664.35 | 0.2681 | 161465 | 1056 | 31/31 |
| | P2 | 2271.10 | 0.2117 | 204544 | 1056 | 31/31 |
| | P3 | 1687.87 | 0.2606 | 162079 | 1056 | 31/71 |

### Why the hit fraction inverts (not a defect)
`hit = cached / prompt_tokens`, and the pointer arms send **5.413x fewer prompt tokens per turn** (2274 vs 12310, identical on both setups). The same reused blocks are a much smaller fraction of a much smaller prompt; unc/turn *falls* for P1 on O4 (1884 -> 1664). Hit fraction is not comparable across arms with different denominators.

### Why P3 "did not collapse" (the parent's reading is wrong)
O4 cached(t40) = 0 in **both** P3 and P1, so the parent's `cached(41..71)/cached(40)` is 0/0. The collapse is at **turn 41**: P3 0 vs P1 1056 — 100% of the cacheable prefix, one block, re-prefilled. P3's first hit is t42, P1's t41. The edit was paid for.

### Mechanism (nailed to the renderer)
`pointer_index` appends index lines at the tail (`cells/VLLM-CELL/vllm_cell.py:79-88`); the growing index crosses the 1056-token block boundary at turn 41, freezing block 0 (first hit 1056) and block 1 at turn 62 (2112). P3's edit of line `t020` (`prompt_r2prompt_cell.py:66-67, 174-189`) sits inside block 0, so it stops matching at 41. Cached on O4 is the `vllm:prefix_cache_hits_total` delta (`:292-299`) and is synchronous — the loss lands at 41, not 42.

### Caveats recorded (do not invalidate the cell, do bound it)
- O4 cached is counter-derived and **1056-quantised**, not the declared 1088 — the observed unit contradicts the declared grid.
- P2's pad is tail-appended, so it is structurally unable to buy a hit: P2 cached == P1 cached on **71/71** O4 rows and `P2 unc = P1 unc + pad` exactly. Its 1088 grid is also off the real 1056 unit.
- Arm identity is clean: 4 distinct first-prompt digests (P0 `4a8e1712…`, P1 `ec7c22ef…`, P2 `256c49e6…`, P3 `aab17702…`), 71 distinct prompt digests per arm, 0 collisions, identical across setups.

**Verdicts: O1 VALID · O4 VALID** (cached 1056-quantised; control fires at t41, not t40).
