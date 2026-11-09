# GATES-MESSAGE-CONSISTENCY

**Goal.** Make each gate's `consequence` sentence agree with its own `ok`, and make its
numerals name the right units. Sentences only: no decision, threshold, exit code or value
of `computed`/`limit`/`ok` may move.

**Evidence.** `experiments/ptr-engine/measure/cell-pointer-stable-20261026T182535Z-p4-001.gates.json`
has three verdicts with `ok: true` and two sentences that read as refusals:

- G1: "this cell needs 1,154 requests (48 turns x 1 arm(s) x 1 rep(s) = 48 + 5 fetch
  follow-up allowance) but only 4,320 remain: shortfall -3,166 requests". `projected` is
  the CUMULATIVE spend after the cell (spent 1,101 + would_spend 53), 4,320 is the cap
  (limit = cap - reserve), and 3,166 is what remains AFTER the cell, not a shortfall.
- G2: "projected wall 2880s = 48 request(s) x ... exceeds the allowed 2880s" on an
  admitted verdict (`V-GATE-CHAIN-2`: allow at 2,880, refuse at 2,881), with 48 called
  "request(s)" where the cell has 48 turns.

**Branches.** `cell.py:1227` (G1) and `cell.py:743` (G2) each emitted ONE consequence,
unconditionally; the allow path therefore printed the refusal text.

**Fix.** An allow family and a refuse family per gate, selected by `ok`. The G1 allow
family names `would_spend` (this cell's own requests), `projected` (cumulative after the
cell), the limit (cap - reserve), the headroom after the cell and the unspent amount
before it, and says the follow-up figure is an allowance. The G2 allow family says
"within ... by N s of slack" and names turns as turns and requests as requests; its
refusal family says "exceeds ... by N s".

**Tests.** `experiments/ptr-engine/longrun/tests/test_gate_messages.py` — (a) allowed G1:
no "shortfall", `spent + would_spend == projected <= headroom`, `remaining == headroom -
projected`; (b) refused G1 (cap 120, spent 100): "shortfall" + exit 4, no allow family;
(c) G2 allow at 2,880 / refuse at 2,881: sentences and codes unchanged, no "request(s)"
where turns are meant; (d) three `artefact_sha256` digests match their artefact bytes and
`artefact_digests`.

**Out of scope / deliberately unchanged.** The G1 `limit` string still renders
"cap X - reserve Y - spent Z" while carrying `cap - reserve`; changing it is a value
change and belongs to its own card (reported as a defect, not fixed here).
