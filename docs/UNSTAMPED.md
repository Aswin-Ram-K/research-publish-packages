# The failed column is 97 pieces of unfinished work, zero measured failures

**Census of the 104 failed cards.** Generated 2026-10-26 from the Host task board ledger
(`ledger-v2.json` revision 4804), read-only; every card with `status=failed`
and no `archivedAt`. Row data is the closure's own verdict row (`command`, `exitCode`, `sha`), the
partition is [`VERDICT-SEMANTICS.md`](VERDICT-SEMANTICS.md) via
`experiments/ptr-engine/tools/verdict_semantics.py`, and the census is
[`measure/UNSTAMPED-CENSUS.json`](../experiments/ptr-engine/measure/UNSTAMPED-CENSUS.json).
Checked mechanically by `python3 experiments/ptr-engine/tools/unstamped_audit.py --check` (exit 0).

## Counts

| classification | cards |
|---|---|
| `never_had_a_row` | **96** |
| `superseded_or_duplicate` | 5 |
| `unstamped_refusal` | 1 |
| `verified_fail` | 2 |
| `blocked_by_another_card` | 0 |
| **total** | **104** |

Of the 104 failed cards, 97 are unfinished work: 96 never had a verdict row at all and 1 has a row that refused before measuring. 5 were redone and settled by a later card. 2 carry a measuring row — and both of those rows exit 0, so the column holds no measured failure of anyone's artefact.

Both `verified_fail` rows exit **0**: the command passed and the closure failed on `sha-mismatch`
(the recorded sha was not the execution head), so they are record defects, not failures of an
artefact. The single `unstamped_refusal` is exit **124**, a timeout that is not in `EXIT_TABLE` at
all and therefore measured nothing. No row in this column records a failure of the card's own work.
None of these cards appears in `measure/WITHDRAWN.json` or `docs/FALSE-PASS.md`, so the census neither re-opens a retracted figure nor re-charges a record already adjudicated.

## The table

| card | title | exec | ended (UTC) | row | exit | class |
|---|---|---|---|---|---|---|
| `00588647` | V-XSTACK2 | 2 | 2026-10-23T09:21 | no | — | `never_had_a_row` |
| `4aec69a9` | T4-1 | 1 | 2026-10-23T09:28 | no | — | `never_had_a_row` |
| `284ebdc0` | GUARD-U4 | 2 | 2026-10-23T16:36 | no | — | `superseded_or_duplicate` |
| `133de3cd` | GAP-LEDGER | 1 | 2026-10-23T23:26 | no | — | `never_had_a_row` |
| `c795ffcd` | FIX-ADV | 1 | 2026-10-23T23:42 | no | — | `never_had_a_row` |
| `9b1cab63` | LATENCY-DERIVE | 1 | 2026-10-24T00:46 | no | — | `never_had_a_row` |
| `3f95bcf2` | R2-OPT-SIM | 1 | 2026-10-24T02:11 | no | — | `never_had_a_row` |
| `f27746ef` | R2-OPT-SIM2 | 2 | 2026-10-24T02:24 | no | — | `never_had_a_row` |
| `583f5df6` | SIM-PROMOTE | 2 | 2026-10-24T02:37 | no | — | `never_had_a_row` |
| `f3dab120` | SEAM-1 | 1 | 2026-10-24T02:57 | no | — | `never_had_a_row` |
| `e8614fd1` | M2-REVIEW-WIRE | 1 | 2026-10-24T02:57 | no | — | `never_had_a_row` |
| `10229a4a` | CB-TMPDIR | 1 | 2026-10-24T02:57 | no | — | `never_had_a_row` |
| `31d88bb3` | R2-VLLM-FIX | 2 | 2026-10-24T02:57 | no | — | `never_had_a_row` |
| `270fa343` | FIX-INSTRUMENT | 2 | 2026-10-24T03:06 | no | — | `never_had_a_row` |
| `3dfa9b74` | R2-VLLM | 2 | 2026-10-24T03:12 | no | — | `never_had_a_row` |
| `538ee08e` | MEASURE-VLLM | 2 | 2026-10-24T03:19 | no | — | `never_had_a_row` |
| `f9a3f5f3` | FIX-FRAME-PROGRESS | 1 | 2026-10-24T03:19 | no | — | `never_had_a_row` |
| `5c091b47` | FIX-DENIALS | 1 | 2026-10-24T03:32 | no | — | `never_had_a_row` |
| `532e1cda` | R2-SGL-9B | 2 | 2026-10-24T04:19 | no | — | `never_had_a_row` |
| `7dd0c2a7` | PROMPT-O2 | 2 | 2026-10-24T05:31 | no | — | `never_had_a_row` |
| `72a170c4` | PROMPT-O2B | 2 | 2026-10-24T05:50 | no | — | `never_had_a_row` |
| `d8a6a077` | M3-INSTRUMENTS | 1 | 2026-10-24T05:57 | no | — | `never_had_a_row` |
| `be1857c3` | PROMPT-O2C | 2 | 2026-10-24T06:02 | no | — | `never_had_a_row` |
| `02b7cb79` | PROMPT-O4 | 2 | 2026-10-24T06:31 | no | — | `never_had_a_row` |
| `22381d40` | SEED-PROMOTION | 1 | 2026-10-24T06:32 | no | — | `never_had_a_row` |
| `4f37169f` | ENVELOPE-RESCUE | 1 | 2026-10-24T06:32 | no | — | `never_had_a_row` |
| `b728d709` | WIRE-FIXTURES | 1 | 2026-10-24T06:34 | no | — | `never_had_a_row` |
| `2c1239ba` | ENVELOPE-RESCUE-2 | 1 | 2026-10-24T06:52 | no | — | `never_had_a_row` |
| `141ae874` | R2-P1-O1 | 1 | 2026-10-24T06:56 | no | — | `never_had_a_row` |
| `2543dde2` | GATE-RUN at fa01962 | 1 | 2026-10-24T07:05 | no | — | `never_had_a_row` |
| `718ee01d` | R2-P1-O2 | 2 | 2026-10-24T07:13 | no | — | `never_had_a_row` |
| `b912b1df` | ENVELOPE-PORT | 1 | 2026-10-24T07:29 | no | — | `never_had_a_row` |
| `cda00a57` | ENV-PIN | 1 | 2026-10-24T07:36 | no | — | `never_had_a_row` |
| `07dfbde0` | GATE-RUN envelope-port at a37bde6 | 1 | 2026-10-24T07:57 | no | — | `never_had_a_row` |
| `be6d5796` | V-PKG-CORR | 2 | 2026-10-24T08:25 | no | — | `superseded_or_duplicate` |
| `2788e69c` | ARMS-PARITY-WITHDRAW | 2 | 2026-10-24T08:25 | no | — | `superseded_or_duplicate` |
| `19b125b5` | ENV-GREEN | 1 | 2026-10-24T08:39 | no | — | `never_had_a_row` |
| `35d61d0e` | SEED-PROMOTION-2 | 1 | 2026-10-24T08:39 | no | — | `never_had_a_row` |
| `b626d10f` | PAPER-FINAL-V | 2 | 2026-10-24T13:25 | no | — | `superseded_or_duplicate` |
| `bbc1ddfd` | PAPER-FINAL-V2C | 1 | 2026-10-24T13:50 | no | — | `never_had_a_row` |
| `16c45cbc` | M3-INST-3 | 1 | 2026-10-24T14:26 | no | — | `never_had_a_row` |
| `a3a90441` | C63-CELL | 1 | 2026-10-24T14:35 | no | — | `never_had_a_row` |
| `18616029` | FUZZ-BUDGET | 2 | 2026-10-24T17:51 | no | — | `never_had_a_row` |
| `7d342534` | FUZZ-BUDGET-2 | 2 | 2026-10-24T21:06 | no | — | `never_had_a_row` |
| `737a5cd9` | Vision audit: orchestration board screenshots via the keyl | 2 | 2026-10-24T23:08 | no | — | `never_had_a_row` |
| `946300cb` | E11-7 | 2 | 2026-10-24T23:23 | no | — | `never_had_a_row` |
| `8ec3d0a4` | Landing queue | 2 | 2026-10-24T23:25 | no | — | `never_had_a_row` |
| `fa30c407` | Enforcement eval | 2 | 2026-10-24T23:32 | no | — | `never_had_a_row` |
| `c95853b4` | E16-1 | 2 | 2026-10-24T23:36 | no | — | `never_had_a_row` |
| `64641603` | E3-1 | 2 | 2026-10-25T00:00 | no | — | `never_had_a_row` |
| `04b6dc5b` | SEED-PROMOTION-RED | 2 | 2026-10-25T01:45 | no | — | `never_had_a_row` |
| `33452d1a` | SEED-PROMOTION-RED-2 | 1 | 2026-10-25T02:13 | no | — | `never_had_a_row` |
| `c82cbac5` | V-RELEASE-BATCH | 1 | 2026-10-25T02:29 | no | — | `never_had_a_row` |
| `d4639fec` | LAZY-LOAD-CROSSOVER | 1 | 2026-10-25T02:29 | no | — | `never_had_a_row` |
| `8a7c7315` | LAZY-LOAD-CROSSOVER-2 | 1 | 2026-10-25T02:38 | no | — | `never_had_a_row` |
| `854dc010` | SEED-RED3 | 1 | 2026-10-25T02:53 | no | — | `never_had_a_row` |
| `5319db06` | SEED-RED4 | 1 | 2026-10-25T03:29 | no | — | `never_had_a_row` |
| `c1112065` | FUZZ-BUDGET-4 | 2 | 2026-10-25T05:44 | no | — | `never_had_a_row` |
| `fd08b302` | AVALANCHE-INSERT | 2 | 2026-10-25T06:23 | no | — | `never_had_a_row` |
| `038ec45c` | AVALANCHE-2 | 1 | 2026-10-25T06:23 | no | — | `never_had_a_row` |
| `8b757757` | dogfood-bl1 | 1 | 2026-10-25T06:25 | no | — | `never_had_a_row` |
| `8dfe09b4` | V-MECH-RECORD offline diff-verifier of wording repairs | 1 | 2026-10-25T07:07 | no | — | `never_had_a_row` |
| `35f65e47` | V-PAPER-CLOSE independent verifier of experiment close | 1 | 2026-10-25T07:07 | no | — | `never_had_a_row` |
| `479eadff` | SEED-RED6 | 5 | 2026-10-25T07:14 | no | — | `never_had_a_row` |
| `1e06da66` | VERIFY-CLASSIFIER-FIX | 1 | 2026-10-25T07:50 | no | — | `never_had_a_row` |
| `8acfcd9a` | CONTAINMENT-RULING | 1 | 2026-10-25T07:51 | no | — | `never_had_a_row` |
| `17bd9588` | RSI-ATTR-1 | 1 | 2026-10-25T08:17 | no | — | `never_had_a_row` |
| `8eb0c381` | PROJ-ADOPT-1 | 1 | 2026-10-25T08:17 | no | — | `never_had_a_row` |
| `75abdae3` | DIRECTION-1 | 2 | 2026-10-25T08:27 | no | — | `never_had_a_row` |
| `b7b5998e` | FUZZ-BUDGET-5 | 2 | 2026-10-25T08:27 | no | — | `never_had_a_row` |
| `92d82888` | SCOPE-GUARD-MARKERS | 1 | 2026-10-25T10:39 | no | — | `never_had_a_row` |
| `4d83bd65` | C8-CENSUS | 2 | 2026-10-25T11:56 | no | — | `superseded_or_duplicate` |
| `cbd59518` | RSI-ATTR-VERIFY | 1 | 2026-10-25T12:41 | no | — | `never_had_a_row` |
| `10ce5669` | C8-CENSUS-FIX | 2 | 2026-10-25T13:26 | no | — | `never_had_a_row` |
| `e85b5d64` | C8-SENTENCE-FIX | 2 | 2026-10-25T14:28 | no | — | `never_had_a_row` |
| `6b462d4d` | RECORD-C8-PARAGRAPH | 2 | 2026-10-25T14:56 | no | — | `never_had_a_row` |
| `8619fdef` | RSI-SURFACES-1 | 1 | 2026-10-25T09:44 | no | — | `never_had_a_row` |
| `3df7b68e` | HOUSEKEEPING-WT | 1 | 2026-10-25T09:58 | no | — | `never_had_a_row` |
| `d069231c` | RECORD-C8-APPEND | 2 | 2026-10-25T16:26 | no | — | `never_had_a_row` |
| `533e8b97` | C8-ADDENDUM2 | 1 | 2026-10-25T16:58 | no | — | `never_had_a_row` |
| `7d0499e4` | STATE-GRAPH-VIEW | 1 | 2026-10-25T11:01 | no | — | `never_had_a_row` |
| `0215fb45` | MOCK 04 SIGNAL | 1 | 2026-10-25T21:49 | no | — | `never_had_a_row` |
| `3e57fe61` | UX 01 HORIZON | 1 | 2026-10-26T07:09 | no | — | `never_had_a_row` |
| `6ae7a4a6` | RUN-INSTRUMENT-FIX | 1 | 2026-10-26T08:01 | no | — | `never_had_a_row` |
| `0a175e23` | FULL MOCK | 1 | 2026-10-26T12:05 | no | — | `never_had_a_row` |
| `ac1afc9a` | APPLY-EVIDENCE | 1 | 2026-10-26T12:09 | no | — | `never_had_a_row` |
| `9091720f` | PROBE-CP3-V5 | 1 | 2026-10-26T12:23 | no | — | `never_had_a_row` |
| `5b756178` | FORK-CHECKPOINT | 1 | 2026-10-26T12:36 | no | — | `never_had_a_row` |
| `bfab721c` | STUDIO | 1 | 2026-10-26T12:36 | no | — | `never_had_a_row` |
| `fb087801` | FLAKE-RSI-SURFACES | 1 | 2026-10-26T13:01 | no | — | `never_had_a_row` |
| `b1a66d2d` | FLAKE-RSI-SURFACES-2 | 1 | 2026-10-26T13:08 | no | — | `never_had_a_row` |
| `17a76d24` | Q0-ANSWER-DEGENERACY | 1 | 2026-10-26T13:08 | no | — | `never_had_a_row` |
| `4e559586` | PROBE-CP3-V6 | 1 | 2026-10-26T13:24 | no | — | `never_had_a_row` |
| `cee214be` | QA + BUILD | 1 | 2026-10-26T13:24 | no | — | `never_had_a_row` |
| `dac474f3` | FLAKE-RSI-SURFACES-3 | 1 | 2026-10-26T13:24 | no | — | `never_had_a_row` |
| `7ce28b73` | ACCOUNT-INVENTORY | 1 | 2026-10-26T13:46 | yes | 0 | `verified_fail` |
| `c1150ee9` | PROFILE-PACK | 1 | 2026-10-26T13:46 | yes | 0 | `verified_fail` |
| `3d65a93c` | R2.1-TIGHTEN | 1 | 2026-10-26T13:49 | no | — | `never_had_a_row` |
| `962d4860` | GRADE-FIT-CONTROL | 1 | 2026-10-26T13:51 | no | — | `never_had_a_row` |
| `be32e196` | STRAND-MERGE-2 | 1 | 2026-10-26T14:05 | yes | 124 | `unstamped_refusal` |
| `ee720e25` | STUDIO FIX | 1 | 2026-10-26T14:12 | no | — | `never_had_a_row` |
| `68a0842b` | DET-VERIFY-FIX | 1 | 2026-10-26T14:14 | no | — | `never_had_a_row` |
| `28d96e4c` | RUN-REASONING-POLICY | 1 | 2026-10-26T09:03 | no | — | `never_had_a_row` |
| `b75a19a5` | REASONING-PILOT-OFF | 1 | 2026-10-26T09:35 | no | — | `never_had_a_row` |

## (a) A refusal is not a failure

Every failed card here settled because a conductor stopped or a host interrupted, not because a
check said the work was wrong. Three of the 104 have any row at all: one refusal (exit 124, a timeout
outside `EXIT_TABLE`) and two rows whose command exited 0 and whose settlement turned on `sha-mismatch`
alone. A refusal is the record saying *I could not judge*; a `sha-mismatch` is the record saying *I
judged a command that passed, but I cannot bind it to a tree*. Neither is evidence about the card's
artefact, and neither may be read as one — the cost of reading them that way is that 104 unjudged
cards look like 104 bad ones. The other 101 never wrote a row at all: 96 have no row and 5 were
redone and settled by a later card, which is not a failure either.

## (b) How to re-open one properly

Re-open a card by recording a command that measures **the card's own artefact**, not the runner's
budget: for a guard or ledger card a `pytest <that one test file> -q`; for a record card the
checker that re-derives its table from the rows; for a lane card the lane's own suite. The
command must be frozen before the run, must exit in the measuring set (`0,1,5,6,9,10,11`, decided by
`verdict_semantics.is_refusal`, never copied), and its sha must be the execution head. Do not re-charge
a refusal as a failure: replace the row, keep the old one in the journal, and settle from the new row.
Exit codes `2,3,4,7,8,12,13` mean the conductor refused before judging (preflight, budget, ledger cap,
unwritable artefact, projection, prereg, tree-moved); exit `124` currently means nothing at all and
should either be added to `EXIT_TABLE` as a refusal or replaced by a bounded command.

## (c) Which subset is worth re-running, ranked by cost

1. **Offline single-file tests — cheapest, no request spent (3):** SIM-PROMOTE, FIX-INSTRUMENT, VERIFY-CLASSIFIER-FIX.
   A single `pytest` file each; these are the cards whose whole acceptance surface is local and whose
   failure today is pure absence of a row.
2. **Offline analysis over rows already on disk (14):** V-XSTACK2, R2-OPT-SIM2, M3-INSTRUMENTS, GATE-RUN envelope-port at a37bde6, PROJ-ADOPT-1, C8-CENSUS-FIX, C8-SENTENCE-FIX, RECORD-C8-PARAGRAPH, RECORD-C8-APPEND, C8-ADDENDUM2, STATE-GRAPH-VIEW, R2.1-TIGHTEN, GRADE-FIT-CONTROL, DET-VERIFY-FIX.
   No requests, but each needs a re-derivation run before it can record a measured row.
3. **Excluded — anything that would spend a request, or only talks to the live endpoints (26):**
   LATENCY-DERIVE, R2-OPT-SIM, R2-VLLM-FIX, R2-VLLM, MEASURE-VLLM, R2-SGL-9B, PROMPT-O2, PROMPT-O2B, PROMPT-O2C, PROMPT-O4, R2-P1-O1, R2-P1-O2, C63-CELL, LAZY-LOAD-CROSSOVER, LAZY-LOAD-CROSSOVER-2, AVALANCHE-INSERT, AVALANCHE-2, V-MECH-RECORD offline diff-verifier of wording repairs, V-PAPER-CLOSE independent verifier of experiment close, RSI-SURFACES-1, RUN-INSTRUMENT-FIX, PROBE-CP3-V5, Q0-ANSWER-DEGENERACY, PROBE-CP3-V6, RUN-REASONING-POLICY, REASONING-PILOT-OFF. These must not be re-run under an offline bound; they need a live window and a
   request cap, and re-running one here would itself be the failure.
4. **Not ranked here (53):** T4-1, GAP-LEDGER, FIX-ADV, SEAM-1, M2-REVIEW-WIRE, CB-TMPDIR, FIX-FRAME-PROGRESS, FIX-DENIALS, SEED-PROMOTION, ENVELOPE-RESCUE, WIRE-FIXTURES, ENVELOPE-RESCUE-2… — these belong to other workspaces (Duval lane work, presence, Studio), where the
   acceptance surface is that workspace's own gate, not this one.

Repair order: 1, then 2, then re-record the two `sha-mismatch` rows from their existing passing
commands (no re-run needed — only the sha binding), and leave 3 and 4 to a card that may spend.
