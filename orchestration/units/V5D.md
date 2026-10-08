# V5D — independent verifier: U5.13 claim standing cap + attribution

**Scope:** verify U5.13 (docket claim asserting a model-grade `CONFIRMS` with no model
check and no attribution). I fix nothing; `materialize.py` was touched ONLY for two
sha-proven reverts, each restored byte-identically.

**Bound:** ≤28 tool calls (used 24). One Occamy probe (DOWN, `000`). Zero live LLM calls.

**Checks:** C1 suites · C2 adversarial cap (own fixtures, highest value) · C3 normalisation
equivalence re-derived · C4 load-vs-materialise · C5 single-predicate identity + literal
table · C6 red→green both guards · C7 honesty audit · C8 containment.

**Verdict: FAIL** — the cap is correct for every input the CHECK-constrained store can
produce, but it is applied to a *coerced* producer, so `"Model"` / `"MODEL"` / `"  model  "`
render `CONFIRMS` while `store.producer_is_model(raw)` is `False` (reachable through the
unvalidated curated `--lane-file` path, `cli.py:346`). Secondary: `_claim_producer` and
`derive_producer` diverge on `fixture`/`mixed`; and the cap is keyed off the *mining*
provenance (candidate row) rather than the *assessing* provenance (`verdicts.producer`).

Write paths used: `orchestration/{VERDICTS.md,units/V5D.md,handoffs/V5D.json}`,
`state/verify/V5D/**`. Nothing else.
