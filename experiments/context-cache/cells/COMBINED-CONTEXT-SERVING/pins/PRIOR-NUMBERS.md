# Re-derived prior-pilot headline numbers (HL-PILOT)

Source rows: `experiments/context-cache/cells/HL-PILOT/rows/e5.jsonl` (120 rows) and `rows/e5b.jsonl` (144 rows).
Method: sum `prompt_tokens`, `cached_tokens` (null rows excluded from cached sum, counted separately), `completion_tokens`, `usage_raw.reasoning_tokens`, `derived.uncached_prefill_tokens_from_prompt_minus_cached` (null rows excluded), and count rows where `text == ""`.

## LR-04 (e5), per arm (n=40 each)
| Arm | prompt | cached (reported rows) | null cached rows | uncached (prompt-cached, incl. null rows via uncached_for_analysis) | completion | reasoning | empty text |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 787,854 | 758,208 (39) | 1 | 29,646 | 25,831 | 22,699 | 5 |
| B | 742,320 | 716,736 (39) | 1 | 25,584 | 26,890 | 25,118 | 7 |
| C | 727,144 | 684,928 (39) | 1 | 42,216 | 28,362 | 26,742 | 9 |

## LR-01 (e5b), per arm (n=48 each)
| Arm | prompt | cached (reported rows) | null cached rows | uncached | completion | reasoning | empty text |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 526,453 | 491,968 (46) | 2 | 34,485 | 28,761 | 21,274 | 6 |
| B | 350,473 | 330,048 (46) | 2 | 20,425 | 37,380 | 31,482 | 14 |
| C | 326,399 | 284,864 (46) | 2 | 41,535 | 39,358 | 35,980 | 19 |

## Match verdict
- All totals above match `REPORT.md` (LR-04 and LR-01 tables) and `notes/e5-analysis.json`/`notes/e5b-analysis.json` to the token, including empty-text counts.
- Deltas reproduce: LR-04 B uncached -13.7%, C +42.4%; combined proxy B -5.4%, C +27.2%. LR-01 B uncached -40.8%, C +20.4%; combined B -8.6%, C +27.9%.
- Mismatch list: none for the headline totals. The only convention-dependent figures are derived-only uncached sums (12,295/8,233/24,865 for e5; 22,303/8,411/29,578 for e5b) which exclude null-cache rows; the report's `uncached_for_analysis` convention counts those rows as fully uncached, which is what the headline uses.

## Already reproduced by other units (not re-litigated here)
- `orchestration/handoffs/V-HL-PILOT.json` checks 3-4 reproduced E2 (all six prompt/uncached totals, verified counts, rebuild/noop costs) and E5 LR-04 (all twelve totals, deltas, 4/8 per-check map byte-identical across arms, 765-call ledger total, Duval 0-line porcelain).
- `orchestration/handoffs/V-HL-E5B.json` reproduced e5b totals and empty counts.
- This note extends them with reasoning totals and null-cache-row counts; it does not repeat their E1C residual/monotonicity or E2 verified-count work.
