# REQUEST-LEDGER — the request budget as a number a machine computes

**Status:** landed 2026-10-26 (`REQUEST-LEDGER`) · amended 2026-10-26 (`REQUEST-LEDGER-2`: the duplicate rule) · **reversed 2026-10-26 (`LEDGER-CONSERVATIVE`: the deduction is withheld, see the reversal section)**
**Instrument:** `experiments/ptr-engine/tools/request_ledger.py`
**Report of record:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json`
**Tests:** `experiments/ptr-engine/tests/test_request_ledger_dedup.py` (8, offline) and
`experiments/ptr-engine/longrun/tests/test_request_ledger.py` (16, offline)

Six rounds of status lines carried **"≈466 of 4,320 requests used"**. That number was maintained by
hand. This document replaces it with a count derived from the row files, states the rules that produce
it, and records — rather than smooths — the difference. Two corrections sit on top of it: the ledger
figured out what was spent (1,101 rows counted), and `REQUEST-LEDGER-2` figured out that 30 of those
rows are duplicate mirrors of a request already counted (1,071 requests — that figure is the
de-duplicated **diagnostic, NOT deducted**; see the reversal below. The budget is 1,101 raw, 3,219
remaining, because `content_sha256` is a response hash and deducting the 30 would understate spend:
`V-DUPLICATE-RULE` fail, WI-002).

---

## Reversal 2026-10-26 (`LEDGER-CONSERVATIVE`) — the headline is the RAW count again

**Published before, now withdrawn:** `requests` = **1,071**, `remaining` = **3,249** (de-duplicated).
**Published now:** `requests` = **1,101**, `remaining` = **3,219** (raw).

**The evidence that caused the reversal, in one sentence:** `content_sha256` is
`sha256(assistant content)` — a **response** hash (`experiments/ptr-engine/longrun/run_longrun.py:1555`,
and all **869/869** rows that carry it satisfy `content_sha256 == sha256(content)`), so identical
response text does **not** mean identical request and the rule's excess **understates** spend instead
of measuring it.

`V-DUPLICATE-RULE` (`f9654fff`) graded `overall: fail` on exactly that third attack: two of its five
attacks were sound (the 41/54/30/30 recomputation; 0 of the 30 dropped rows distinguishable as a
second attempt — identical `ttft_s`/`latency_s` to 6 dp), but tuple identity is not request identity.
A deduction must not be spent against on an unsound rule, so the 30-request deduction is withheld and
the RAW count is the number anything may spend against.

**The 1,071 is not deleted.** It stays in `REQUEST-LEDGER.json` as
`diagnostic.requests_deduplicated` with `diagnostic.deducted: false`, its per-file excess
(v6-tools 11, v4-tools 17, v5-tools 2), and all 30 rows named individually with
`deducted: false` and the reason. A number that changed twice must show both — and it does.

**A future sound rule re-publishes the deduction, and it cannot happen silently.**
`request_ledger.deduction_permitted()` is the single place a deduction is authorised: it requires
the `deduction_rule_sound` flag **and** evidence naming a `request_identity_hash`. The flag alone
raises. There is no CLI switch. `experiments/ptr-engine/tests/test_request_ledger_sound.py` pins both directions
(`requests == requests_raw` today; the flag without evidence red; the flag with a real
request-identity hash green). The number must not silently flip back.

---

## 1. The two figures, side by side

| figure | value | what it is |
|---|---:|---|
| `requests_raw` | **1,101** | rows the counting rule counts as an inference call (rules 1–2 below) |
| `duplicate_excess` | **30** | rows that are duplicate mirrors of a request already counted, in files whose schema can decide it |
| `requests_deduplicated` (diagnostic, **not deducted**) | **1,071** | raw minus the duplicate excess — published under `diagnostic`, explicitly NOT spent against |
| `remaining_raw` | **3,219** | cap 4,320 − 1,101 |
| `remaining` (headline) | **3,219** | cap 4,320 − 1,101 (the raw remainder; `remaining_deduplicated` = 3,249 is the withdrawn figure) |
| files where the rule decided | **11** | `rule_status: "decided"` |
| files where it could not | **3** | `rule_status: "not_applicable"` (named in §3) |

**Both figures are published on purpose.** The number moved; a reader must be able to see what it was
before the correction, what it is after, and re-derive either. Nothing in the instrument drops the raw
figure, and `budget.spent_raw` / `budget.spent_deduplicated` keep both in the machine-readable report.

A caller that wants a spend number must quote **`requests` (1,101) and remaining 3,219** — that is
the headline and the only figure anything may spend against. The de-duplicated 1,071 is a *diagnostic*
kept for audit: quote it as **"1,071 de-duplicated, NOT deducted"**, never as the spend. A caller that
wants to show the correction should quote the pair **1,101 → 1,071 (−30), withheld**.

---

## 2. What is counted

The instrument reads every `experiments/ptr-engine/measure/rows-*.jsonl` and counts **one request per
row that represents an inference call**. The vocabulary is closed; it is not extended silently.

| # | Row shape | Verdict |
|---|---|---|
| 1 | `kind == "turn"` | **counted** — a chat-completion turn |
| 2 | `kind == "tool-followup"` | **counted** — a follow-up call in the tool loop reaches the server and bills like any other |
| 3 | `billed` is `false` | **not counted** — the row says it was not billed |
| 4 | `followup_suppressed` truthy | **not counted** — the client skipped the call |
| 5 | `served_from == "prompt"` | **not counted** — served out of the prompt, no call left the client |
| 6 | no recognised `kind`, no marker | **counted and flagged `assumed_billed`** |

Rule 6 is the honest edge. Where a row's schema cannot decide the question, the tool counts it —
the conservative direction, because an unmarked row that did reach the wire must not vanish from a
hard budget — and reports the count separately so the doubt stays visible instead of being laundered
into a confident total. `assumed_billed` is therefore a *confidence* column, not a second total.

**Then the duplicate rule, per file.**

```
identical (ts, content_sha256, prompt_tokens, completion_tokens) within one file;
first occurrence kept
```

This is `TVS-REGRADE`'s rule, applied exactly: no field added, no near-duplicate threshold invented.
It removes a row only when the writer wrote the same request twice — a `kind=tool-followup` mirror of a
`kind=turn` row (or vice versa) sharing the millisecond `ts`, the `content_sha256` of the response, and
both token counts, with identical `ttft_s`/`latency_s` to six decimals. One measurement, two rows.

**The rule is applied only where the schema can decide it.** A file is `decided` when **every** row
carries a non-empty `content_sha256` and a millisecond-resolution `ts`. On the legacy schema
(second-resolution `ts_utc`, no `content_sha256`) the literal tuple over-merges rows that differ in
`rep`, `turn` and `latency_s` — demonstrably distinct requests — so it is **not applied**, the file is
marked `rule_status: "not_applicable"`, and the reason is written to `rule_reason`. The collisions the
tuple *would* have merged are still counted and reported under `collisions_not_applied`, so the
non-application is a visible decision rather than a silent one.

**What counts that a reader might expect not to.** An HTTP-error row counts: a rejected request still
consumed a slot on the wire. A checkpoint row counts: the 23 `is_checkpoint` rows are distinct calls
with their own prompt/completion tokens (0 duplicate `(arm, task, turn, rep)` keys), so the flag marks
a position in a run, not a non-call. **`is_checkpoint` is not a billing marker.**

---

## 3. The decision status, per file

| file | rows | dup groups | excess | dedup | rule status |
|---|---:|---:|---:|---:|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | — | 0 | 105 | **not_applicable** — no `content_sha256`, second-resolution `ts_utc` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 0 | 0 | 6 | decided |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | — | 0 | 100 | **not_applicable** — no `content_sha256`, second-resolution `ts_utc` |
| `rows-live-2026-10-26.jsonl` | 27 | — | 0 | 27 | **not_applicable** — no `content_sha256`, second-resolution `ts_utc` |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 0 | 0 | 29 | decided |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 0 | 0 | 40 | decided |
| `rows-longrun-2026-10-26.jsonl` | 192 | 0 | 0 | 192 | decided |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 0 | 0 | 192 | decided |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 0 | 0 | 96 | decided |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 0 | 0 | 96 | decided |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | **17** | **17** | **51** | decided |
| `rows-longrun-v5-tools.jsonl` | 72 | **2** | **2** | **70** | decided |
| `rows-longrun-v6-tools.jsonl` | 72 | **11** | **11** | **61** | decided |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 0 | 0 | 6 | decided |
| **TOTAL** | **1,101** | **30** | **30** | **1,071** | **11 decided / 3 not_applicable** |

The whole 30-row excess sits in three tool-loop files — 11 (v6), 17 (v4-tools), 2 (v5-tools) — and in
all 30 cases a `kind=tool-followup` row mirrors a `kind=turn` row. The other 11 files have no duplicate
groups at all.

**A count discrepancy, recorded.** The `REQUEST-LEDGER-2` card (and `TVS-REGRADE`'s headline) say
**9** decidable files and **5** legacy ones. The schema census says **11 and 3**: the only three files
without `content_sha256` and a millisecond `ts` are `rows-baseline`, `rows-equalinfo` and `rows-live`.
The reason the difference does not move the numbers is that *every one of the 30 excess rows lives in
a decidable file*, so the published arithmetic (30 excess, 1,071 deduplicated, 3,249 remaining) is
identical under either split. The report carries the measured split (`dedup_decision.files_deduped` /
`files_not_applicable`, with `count_discrepancy` naming the disagreement) rather than the card's.

**Correction 2026-10-26 (`REQUEST-LEDGER-DOC-FIX`, WI-002).** The parenthetical above quotes the withdrawn arithmetic; the budget is **1,101 of 4,320 raw, 3,219 remaining**.
The de-duplicated **1,071 / 3,249** is a *diagnostic, NOT deducted*: `V-DUPLICATE-RULE` failed
because `content_sha256` hashes the response, not the request, and deducting the 30 would
understate spend. Both figures stay visible; only the raw 1,101 may be spent against.

The legacy collisions that were *not* subtracted are reported too: `rows-baseline` 1 group / 11 excess,
`rows-equalinfo` 2 / 2, `rows-live` 8 / 11 under the literal tuple. Applying the rule there would have
published **24 fabricated duplicates** — requests that differ in rep, turn and latency.

---

## 4. Exclusion markers — what the writer actually emits

The counting rule names three exclusion markers. A census of the 14 real files shows **none of the
three exists as a top-level row field**: they are dead branches at row level. The fields the writer
really emits — `billed_round`, `fetch_followup`, `prompt_served` — are all **not** request-suppression
markers. The instrument reports all six, with corpus counts, in
`REQUEST-LEDGER.json → marker_reconciliation`.

| marker | rows in corpus | values | excludes? | can it change the count? |
|---|---:|---|---|---|
| `billed` | **0** | — | yes (when `false`) | **no — dead code**: no row carries the field |
| `followup_suppressed` | **0** | — | yes (when truthy) | **no — dead at row level**; occurs only *nested* (31×, v6) inside `tool_calls[]` on the row that records a refused follow-up. A refused follow-up emits no row of its own, so a row-level check can never see it |
| `served_from` | **0** | — | yes (when `"prompt"`) | **no — dead at row level**; `served_from: "prompt"` occurs *nested* (37×) inside `tool_calls[]`, describing the served block of a follow-up that was still bought as a request |
| `billed_round` | 24 | `true` 20, `false` 4 | **no** | **no** — fetch-**round** accounting. A follow-up that read no fresh lines costs no round but is still a request; the writer's own `followups_spent()` counts it ("cost no round … not free"). The 4 `false` rows stay counted |
| `fetch_followup` | 68 | `true` 68 | **no** | **no** — it marks a row that *is* a real follow-up request (`kind=tool-followup`). Excluding on it would delete 68 real requests |
| `prompt_served` | 24 | `1` 4, `0` 20 | **no** | **no** — a per-round cache-accounting counter (0/1/2), not the `served_from` marker. A row with `prompt_served=1` still bought a call |

So the answer to "which markers can ever change the count" is: **none in this corpus**. The three the
rule named are implemented and will be honoured if a future writer emits them; today they are
unreachable, and the report says so instead of leaving a branch that looks exercised. The three the
writer actually emits are reported and never subtracted, with the reason attached to each.

The three original markers remain in the report as named exclusions because a fixture must still be
able to exercise them (test cases b / b2 in `test_request_ledger.py`), and because deleting a branch
because today's corpus does not use it would be the same mistake in the other direction.

---

## 5. The cap gate — the door a conductor must walk through

```
python3 experiments/ptr-engine/tools/request_ledger.py --cap 4320 --reserve 0 --would-spend N
```

| Exit | Meaning | Conductor must |
|---|---|---|
| **0** | `spent + N <= cap - reserve` — within budget | may send |
| **4** | would exceed — arithmetic printed to stderr | **abort; propagate 4** |
| **3** | usage error (bad args, no row files, no such directory) | treat as fatal, do not send |
| **5** | a row file is unreadable/unparseable — total unknowable | treat as fatal, do not send |

The gate's `spent` **is the RAW figure** (reversal 2026-10-26). On exit 4 the message prints all five
values in a machine-readable bracket and then names the figure it used and names the de-duplicated one
as withheld, so a wrapper never parses prose and no reader mistakes 1,101 for a different count:

```
OVER BUDGET: spent=1101 + would_spend=4000 = 5101 > cap=4320 - reserve=200 = 4120 (over by 981) \
[spent=1101 would_spend=4000 cap=4320 reserve=200 headroom=4120] (spent is the RAW count; the \
de-duplicated diagnostic figure is 1071 and is NOT deducted -- the duplicate rule is unsound as a \
request-identity test)
```

The within-budget path says the same thing in one line:
`within budget: 1101 <= 4320 (3219 left; spent is the RAW count, de-duplicated diagnostic 1071 is NOT deducted)`.

Defaults: `--cap 4320` (unchanged), `--reserve 0` (unchanged; the cap and the reserve were not touched
by this correction). `--write PATH` writes the JSON report and nothing else; `--json` echoes it.

**Where the conductor calls it.** The call belongs at the *last* point before a request leaves the
client — inside `run_longrun.py`'s per-turn loop — not once per run: the budget is per-request. Exit 4
is propagated as the run's own exit code, unmodified; 3 and 5 propagate identically.

**Known limit of the gate as shipped.** The gate reads the row files on disk, so it sees a request only
*after* the writer recorded it. A hard pre-send guarantee needs the writer to be flush-ordered relative
to the gate (record → gate → send). Shipping the gate without that ordering buys detection, not
prevention. `WIRE-CAP-GATE` (below) closes exactly that.

---

## 6. Determinism and non-mutation

Same rows in → same bytes out. Files are ordered by **basename**, never by directory-listing order. No
wall-clock field is written (`generated_at` never appears), so two runs over unchanged input are
byte-identical and a diff in the report means the corpus changed. The tool writes only its own output
file and never a row file; both test suites hash every row file before and after each run and fail if
any digest moves. `rows-longrun-2026-10-26.jsonl` still re-hashes to `bc61d381…`.

Verification:

```
python3 -m unittest discover -s experiments/ptr-engine/tests -p 'test_request_ledger_dedup.py' -v      # 8 tests, OK
python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_request_ledger.py' -v    # 16 tests, OK
```

Red evidence for the duplicate rule: a copy of the tool with the dedupe call disabled
(`dedupe_applied = True` → `False`) fails `test_1_three_duplicate_groups_excess_three` with
`AssertionError: 0 != 3 : 3 duplicate groups`, and the published corpus regresses to
`requests_deduplicated = 1101`; restoring the line returns 8/8 green.

---

## 7. Reconciliation against the hand-carried "≈466"

**The computed total is 1,101 raw / 1,071 de-duplicated. The difference from 466 is +635 (raw) or
+605 (deduplicated) — the hand figure understated actual spend by a factor of 2.36× (2.30× after the
correction), and it hid 59% (57%) of the requests that were spent.**

Three measured facts bound what "466" could have meant:

1. **No artefact ever produced 466.** `orchestration/handoffs/RUN-C-PLAN.json:38` holds the only
   recorded spend arithmetic: *"ceiling 4320 - 208 spent = 4112 left, of which config C consumes 204,
   leaving 3908."* The last artefactual figure is **208 spent**, not 466 — a discrepancy
   `orchestration/DRIVER_LOG.md:21` had already logged as *"not corroborated by any artefact read
   this pass … 466 is logged as unverified."* This tool does not repair that by choosing a nicer
   number; it records that 466 has no derivation on disk, 208 does, and 1,101 raw / 1,071 de-duplicated
   is what the rows count.
2. **No subset of the corpus yields 466.** The narrowest defensible count — `kind == "turn"` only,
   dropping every tool-follow-up and all 232 unmarked rows — is **~801**, still far above 466. So "466"
   is not a filtered view of today's corpus; it measures a corpus that no longer exists.
3. **It matches a snapshot taken around 04:39.** Ordering the files by first-write time and summing
   cumulatively: 105 → 132 → **232** → 424 → 430 → **459** (through `rows-longrun-2026-10-26-fix.jsonl`)
   → 651 → 747 → 843 → 883 → 951 → 1,023 → **1,095** (through `rows-longrun-v6-tools.jsonl`) → 1,101.
   Two anchors fall out: **459 stands within 7 of 466**, and **1,095 is exactly the row count an earlier
   card cited**. So 466 was almost certainly a hand tally taken near 04:39 and then **carried forward
   unchanged for six rounds while the corpus grew 459 → 1,101**.

This is a *reconstruction*, and it is labelled as one: facts 1 and 2 are measured; fact 3 is the
best-attested explanation and no artefact proves it. What is not in doubt is the direction and size of
the error.

**Why the error was structural, not careless.** The hand figure was a scalar. The instrument is a sum
over files. Any new arm wrote a new `rows-*.jsonl` and the scalar never heard about it, because nothing
forced the two to agree — there was no gate that could fail. After this change a conductor that forgets
a file gets a total that is *low by construction*, and a low total still passes a cap gate silently. So
the row directory must stay the single place requests are recorded.

**Why the second error was structural too.** The writer recorded one request as two rows. A row-based
counter cannot see that unless it knows the duplicate rule, so the ledger now asks the schema whether
the rule can be decided and applies it file by file. Where it cannot, it says so — an applied rule on
an undecidable schema would have fabricated 24 duplicates instead of removing 30.

## WIRE-CAP-GATE — the brake is now pre-send, not post-hoc (2026-10-26)

`REQUEST-LEDGER`'s `known_limit` was honest: a gate that reads rows on disk sees a request only after
the writer recorded it, so it bought **detection**. `run_longrun.py` now calls the same ledger
(`experiments/ptr-engine/tools/request_ledger.py`, imported — the counting rule is NOT re-implemented)
per request, immediately before the send:

    record -> gate -> send

* **At run start** the gate scans the row files (default `experiments/ptr-engine/measure/rows-*.jsonl`,
  overridable with `--budget-glob`) and fixes `spent_at_start`.
* **Per request** `RequestCapGate.acquire(turn, kind)` reserves the slot in an **in-memory** count and
  raises `CapRefusal` if the request would exceed either the declared allocation
  (`--request-allocation N`) or the global `--budget-cap`/`--budget-reserve` headroom.
* **At exit** the run re-reads the same files and requires `spent_after - spent_at_start == used_in_run`.
  `delta > 0` exits **9**; `delta < 0` prints `CAP GATE UNRECORDED` loudly, never silently.
  Because `budget.spent` is the RAW figure (reversal 2026-10-26), a request the writer mirrors into two
  rows now contributes **two** to the count and `delta == 0` holds — the pre-send reservation and the
  written rows agree, because every row is spent against. The duplicate is still reported (under
  `diagnostic`), it is simply not credited back. Before the reversal a mirror made `delta < 0`; that
  asymmetry is gone, and it was the tell that the deducted figure was not the one the writer produced.
* **Exit codes propagate unmodified**: 4, 3, 5 come out of `run_cell` → `main` → `sys.exit`, verified
  through a subprocess.

The run manifest's `cap_gate` block is unchanged in shape; its `spent_at_start` is the ledger's
**raw** count (1,101 as published, not 1,071):

    "cap_gate": {
      "schema": "consonance.longrun-cap-gate/1",
      "ordering": "record->gate->send: the slot is reserved BEFORE the request is issued",
      "counting_rule": "<the ledger's RULE string>",
      "cap": 4320, "reserve": 0, "headroom": 4320,
      "spent_at_start": 1101,
      "allocation": 72,
      "used_in_run": null,
      "final_used_in_run": 72,
      "running_count": 72,
      "reconcile": {"spent_at_start": 1101, "used_in_run": 72, "spent_after": 1173,
                    "expected": 1173, "delta": 0},
      "counted_files": ["rows-....jsonl", "..."],
      "own_rows_file": "<this run's row file>",
      "frozen_sha256": "<the manifest bytes the rows were stamped with>"
    }
