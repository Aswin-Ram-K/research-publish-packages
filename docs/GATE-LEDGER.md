# GATE-LEDGER — what the gate chain has cost, and what it has actually prevented

**Decision card, not an implementation card.** Nothing here changes `cell.py`, `run_longrun.py`,
the fixture, `EXIT_TABLE` or the normative table in [`GATE-CHAIN.md`](GATE-CHAIN.md). The machine
record is [`GATE-LEDGER.json`](../experiments/ptr-engine/measure/GATE-LEDGER.json); the checker is
[`gate_ledger.py`](../experiments/ptr-engine/tools/gate_ledger.py) (`--check`, exit 1 on an
uncounted card, a gate with no stated benefit, or a decision with no compliance sentence).

Three gates and a spawn rule have now cost this batch more rounds than any measurement. This
document writes down, per gate, what it prevents, what would replace it, how many defects it had
itself, and whether a live cell can still walk past it — then decides **keep / demote / retire**
with the licence for that decision stated in one of two licensed forms.

## 1. The cost side — counted, not estimated

Card ids and execution ids are from the Host board ledger (`~/.dsh/task-board/ledger-v2.json`);
verdicts, tool calls and requests are from `orchestration/handoffs/*.json`. Requests are **0**
everywhere: six handoffs declare `0` explicitly, fifteen carry no field at all but every card
contract says OFFLINE / zero requests, and no live row exists for any of these cards.

| card | board id (short) | execution (short) | verdict | tool calls | defect class | gate |
|---|---|---|---|---|---|---|
| WIRE-GATES | `444654f4` | `658e961b` | done | — | nothing (the join) | chain |
| EXIT-CODE-TABLE | `779712a8` | `95489257` | done | 21 | false pass (`exit 7` declared, never raised) | chain |
| EXIT-CODE-TABLE-2 | `db4f1a76` | `0e5e4559` | **cancelled — "no verdict was recorded"; card still `todo`** | — | record binding | chain |
| GATE-OPERAND-VALIDATION | `300b867e` | `d6a067d4` | done | — | unchecked operand | G2 |
| V-GATE-CHAIN | `35c0edda` | `1342fd9f` | **fail** | 21 | bypass | G2 |
| V-GATE-CHAIN-2 | `721e94cb` | `89d3e252` | **fail** | 27 | bypass | G2 |
| V-GATE-CHAIN-3 | `4e7e8017` | `0884f187` | **fail** | 27 | unchecked operand | G2 |
| VERDICT-DISPUTE | `6bfa710a` | `1ebedc5d` | fail | 19 | record binding | chain |
| GATE-CHAIN-FIX | `f9af8ed6` | `69d38f4d` | done | 28 | bypass (repaired) | G2 |
| PREFLIGHT-SPAWN-DECLARE | `61adcc00` | `b9af29a1` | done | — | instrumentation scope | spawn |
| V-SPAWN-DECLARE | `8a166fe0` | `4bd23e0b` | partial | 21 | false pass | spawn |
| SPAWN-VALIDATOR-FIX | `e8636d84` | `0679d0e0` | done | 15 | false pass | spawn |
| V-SPAWN-ATTACK-2 | `ad65e8fb` | `8a5be989` | partial | 22 | bypass (4 shapes) | spawn |
| SPAWN-RECORD-BIND | `8e9df08d` | `0b644a75` | **in flight — running, no handoff, no verdict** | — | record binding (D5, open) | spawn |
| PROJECTION-MODE | `7864d1d7` | `5bb51dde` | done | — | false pass | G2 |
| PROJECTION-CALIBRATION | `c0c7d1c8` | `9660b12d` | done | — | instrumentation scope | G2 |
| WIRE-CAP-GATE | `9d182ed2` | `84fbcae2` | done | — | bypass (detection, not prevention) | G1 |
| GATE-OVERRIDE-FIX | `96e728ae` | `f6b2fc50` | done | — | bypass + record binding + dry-run contract | G2 |
| HYPOTHESIS-SMOKE-MODE | `1e55ee6a` | `66ef79c0` | done | 24 | record binding | G3 |
| WIRE-CLAIM-MODE | `5ef7fc0a` | `026adbbe` | done | 26 | record binding | G3 |
| V-GATE-REPIN | `ba2bdf49` | `172ae3b1` | partial | 19 | instrumentation scope | spawn |

**Totals: 21 cards · 15 defects · 0 requests · ~468 tool-call rounds** (270 measured across the
12 handoffs that record a count, plus 22 × the 9 that record none; 22 is the median of the
measured set and is an estimate — stated, not smuggled).

**What could not be reconstructed, said plainly:**

- **`SPAWN-RECORD-BIND`** — running now; no handoff, no journal, no unit card. Its cost is
  uncounted, and its defect (D5) is recorded from the two verifier handoffs that named it, not
  from the card itself.
- **`EXIT-CODE-TABLE-2`** — the board holds a **cancelled** execution ("no verdict was recorded")
  and the card is still in `todo`, yet a `done` handoff exists. Card-round cost is real; the
  board's verdict is absent. That mismatch is itself a finding about the record.
- Nine cards' tool calls (listed as `—` above) are unrecorded in their handoffs; their rounds are
  estimated, and the estimate is the largest single uncertainty in the total.

Footnotes, so the number is not inflated: `WIRE-GATES`, `EXIT-CODE-TABLE-2`, `VERDICT-DISPUTE`
and `V-GATE-REPIN` did record and table work as well as gate work — each is counted **once**.
`GATE-OPERAND-VALIDATION` hardened all three gates but is counted against G2, where the operand
class it closed actually lived.

## 2. The benefit side — the honest part

### G1 — the ledger cap (`cap`; `spent + turns + ceil(turns×68/801)`)

1. **What has it actually prevented?** A measured incident: `cap=100 spent=100 headroom=100 →
   CAP REFUSED at T1, rc=4, rows=0, transport calls=0` (WIRE-CAP-GATE). The red is equally
   measured: with the pre-send call neutered, `rc=9, rows=3, requests=3`, first row `T1/turn`.
   This is the only gate in the chain whose prevention is a live-path measurement rather than a
   computed refusal.
2. **What would replace it?** Nothing. A post-hoc ledger recovers the count *after* the spend,
   which is exactly the defect (`known_limit`: detects rather than prevents) the brake removed.
3. **How many defects did the guard itself have?** Two: it did not exist as a brake at all
   (detection only), and its manifest name collided at second resolution so two same-second cells
   wrote one `gates.json` and the second silently replaced the first run's admission record.
4. **Is a bypass still possible on the live path?** Through the decision expression: no — three
   operand rounds closed it (167 hostile rows, 0 admitted). Residual: **yes, via `--budget-glob`**,
   which narrows the row-file set the brake scans, so a cell that passes it reads fewer rows than
   the corpus. And the cap is read from an artefact, not hard-coded per card. `thinking=off` and
   `on/auto` are identical here; G1 is mode-independent.

### G2 — the projection (`per-turn wall × turns` vs `--max-wall`)

1. **What has it actually prevented?** **Nothing observed.** No live cell has ever hit this
   refusal. Its refusals are computed: `48×180 = 8,640 s > 3,600 s`; a thinking-auto 60-turn cell
   at `13,092 s` against `3,600 s` (PROJECTION-MODE). Today's dry run at RUN-A\*'s own flags shows
   the gate **admitting at exact equality**: `projected_requests=48, projected_wall=2,880 s,
   limit=2,880 s` — while printing a worst case of `8,640 s`, 3× the ceiling.
2. **What would replace it?** `turns × --turn-wall-cap` is a bound true by construction and needs
   no fitted ratio — and it is **stricter**: at RUN-A\*'s flags it computes `8,640 s` and refuses
   the `2,880 s` ceiling. The replacement forbids the grid; the calibrated form is what admits it.
3. **How many defects did the guard itself have?** **Six, five of them its own decision
   expression** — the ceiling operand (`--max-wall 0/-1` = "unlimited"), the multiplicand
   (`--projected-turn-wall -1`), the p90 file (`--projected-from` pricing ≤ 0), non-finite/absurd
   operands (`inf/nan/1e308`), and a pooled 60 s/turn that priced thinking-auto 3.6× low. The
   three bypasses were three different operand classes of one expression; the repair was to
   validate every operand at the boundary, not the instance.
   **Found by this card, not repaired:** the projection prices `turns`, while G1 bills
   `turns + ceil(turns×68/801)`. One dry run shows it: G1 computed `1,154 = 1,101 + 48 + 5`,
   G2 `projected_requests=48`. G2 under-projects by the follow-up allowance and prices no wall
   clock for a fetch follow-up at all.
4. **Is a bypass still possible on the live path?** `thinking=off`: no operand bypass remains. A
   cell can still walk past the *decision*: a positive `--projected-turn-wall` below the
   calibrated 60 s is accepted and only recorded (`projection_override.direction=optimistic`,
   `reason_required=true`, an `OVERRIDE` line); a `--projected-from` file from a low-p90 arm does
   the same. Declared, not refused. `on/auto`: the same surface, **larger** — auto/on are priced
   at the pooled p50 `218.2 s`, so a cell whose real tail is above the p50 overruns while the
   gate prints `allow`; `--projected-from p90` (`682.7 s`) exists and is not the default.

### G3 — the prereg (n supports the claim; `--hypothesis` required; `claim=none` refused)

1. **What has it actually prevented?** **Nothing observed live.** Computed: absent
   `--hypothesis → exit 12` (before GATE-CHAIN-FIX it silently became H2 and ran); `none`/unknown
   `→ 12`; H1 at `n=48 → 12` naming 60. Today's dry run at RUN-A\*'s own flags returns
   `G3 WOULD-REFUSE computed n=48 | limit n >= 60`.
2. **What would replace it?** The analyser's own `incomparable_claim` refusal rejects `claim=none`
   rows by name — so the pre-run gate **is** redundant for *pooling*. It is not redundant for
   *spend*: the analyser refuses after the requests are billed, and nothing in it stops a
   660-request H1 cell at n=48 from being spent.
3. **How many defects did the guard itself have?** Three: silence defaulted to a claim (so the
   documented "refuses a run that declares no hypothesis" was false while reading as true); its
   refusal shared exit 2 with broken input; and there was no legal declaration for a claim-free
   run, so a smoke cell could only be expressed as an H# claim and its rows carried no claim field.
4. **Is a bypass still possible on the live path?** The n-thresholds are enforced pre-spend for
   H1/H2/H3. A cell may legally declare `--hypothesis smoke` (`claim="none"`, any n) and spend
   real requests — a **declared no-claim**, not a bypass: the analyser refuses to pool it. So G3
   constrains claims, not spend. Identical for `thinking=off` and `on/auto`.

### The spawn rule (refusal record: declared spawns, zero `runner_launch`)

1. **What has it actually prevented?** A measured result with an independent syscall oracle: at
   exits `{2,3,4,8,12}`, `runner_launch == 0`, declared preflight `0/1/1/1/1` equals observed
   Popen `0/1/1/1/1`; a `/tmp` mutant spawning without recording fails with *"the oracle counted
   2 real subprocess.Popen call(s) but the refusal record declares 1"*.
2. **What would replace it?** Nothing — the alternative is not counting spawns, which is the
   defect. The one candidate (an in-process self-check) would change what is being measured.
3. **How many defects did the guard itself have?** Four: the rule `popen_calls == 0 on every
   refusal` was **unsatisfiable** (every refusal makes one diagnostic self-check spawn, so the
   rule was wrong, not the counting); `validate_refusal()` accepted a record with no `spawns` and
   no declaration; four spoofable shapes survived the first hardening; and the record is **not
   tree-bound (D5, still open)**.
4. **Is a bypass still possible on the live path?** Yes, until D5 closes: counts are recomputed
   but the record carries no tree identity, so a record from another tree or argv validates.
   Mode-independent.

## 3. Decision

**"Keep" for all four is the evidence's answer, not a refusal to decide.** The strongest
demotion case was G2 — never a live refusal, five of six defects its own — and it fails on the
measurement, not on inconvenience: demoting it admits a thinking-auto cell at `13,092 s` against
a `3,600 s` ceiling, bounded only per turn at 180 s, and buys **no** relief for RUN-A\* (which the
gate already admits at exact equality). Retiring a guard to make a grid easier is precisely what
the standing rule forbids; here the grid does not even need it.

### G1 — `keep`

Effect on `RUN-A*`: at the card's own hard brake `cap=900` the brake **refuses the first cell**
(computed `1,154 = 1,101 spent + 48 + 5` against `900`, exit 4); the grid can only launch under
the ledger's own `cap=4,320`, which is the number the card already reads in precondition 7.

> **Compliance sentence (verbatim):** *this does not weaken a guard: the refusal is unchanged and
> the removed element is nothing — exit 4 with 0 rows and 0 transport calls stays exactly as
> measured, and the residual `--budget-glob` surface is recorded, not repaired, because repairing
> it is a separate card.*

### G2 — `keep`

Effect on `RUN-A*`: unchanged — each 48-turn `thinking=off` cell is admitted at exactly
`2,880 s of 2,880 s`; a 49th turn or any higher per-turn figure refuses with exit 8.

> **Compliance sentence (verbatim):** *this does not weaken a guard: the refusal is unchanged and
> the removed element is nothing — exit 8, the operand validation, and the printed worst case all
> stay, and the two measured weaknesses found here (the follow-up allowance is not priced; the
> bound is not the default) are recorded as the next strengthening card, not applied.*

**Follow-up card this decision owes (not implemented here):** price
`turns + ceil(turns×68/801)` and add the `turns × --turn-wall-cap` bound as a printed advisory
line beside the forecast. Both *strengthen* G2; neither may be smuggled in by this card.

### G3 — `keep`

Effect on `RUN-A*`: unchanged — H1 at `n=48` returns exit 12 (`n >= 60`), so the grid must run
`turns=60` or declare H2.

> **Compliance sentence (verbatim):** *this does not weaken a guard: the refusal is unchanged and
> the removed element is nothing — exit 12, the required `--hypothesis`, and the analyser's
> `incomparable_claim` refusal all stay; the smoke path is a declared no-claim and is not
> converted into an exemption.*

### Spawn rule — `keep`

Effect on `RUN-A*`: precondition 2 stays **hardening, not met** — D5 is open and `SPAWN-RECORD-BIND`
is still running. This decision does not promote it.

> **Compliance sentence (verbatim):** *this does not weaken a guard: the refusal is unchanged and
> the removed element is nothing — `runner_launch == 0` at every refusal exit stays the acceptance
> rule, and D5 (tree binding) is recorded as OPEN rather than waived, with `SPAWN-RECORD-BIND`
> still running.*

## 4. What this card did not do

- It did not edit `cell.py`, `run_longrun.py`, the fixture, `EXIT_TABLE`, or the normative table in
  `GATE-CHAIN.md`. The decision is implemented by a separate card.
- It did not repair the two weaknesses it found in G2 (allowance not priced; bound not the
  default). Naming them is this card's job; repairing them is the follow-up's.
- It did not settle `EXIT-CODE-TABLE-2` (board: cancelled execution, card in `todo`) or
  `SPAWN-RECORD-BIND` (running). Both are recorded as gaps in the cost table rather than rounded
  away.
- **Dated observation on the pinned tree.** `cell.py` (mtime `2026-10-26 12:59:55`) and
  `docs/GATE-CHAIN.md` (`12:59:15`) changed on disk *during* this card, from the concurrent
  rehearsal — not from this card, which wrote only the four deliverable paths. The evidence above
  was measured against `cell.py` sha256 `b549e45e…` — the same digest `GATE-CHAIN.md` §11 cites —
  and `PROJECTION.json` sha256 `75d02c73…`, so the byte-identical restore is confirmed rather than
  assumed.
