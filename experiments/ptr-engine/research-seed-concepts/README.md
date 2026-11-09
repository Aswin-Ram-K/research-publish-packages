# Research seed — the paper(s) the record actually supports

**What this folder is.** A documentation-only subfolder of the existing `ptr-engine` experiment. It
synthesises evidence already on disk into one flagship paper concept and one independently
warranted second concept, and it states what would have to be measured before either can be
submitted. There is **no `RUN.json`, no run, no execution status and no result in this folder**: the
experiment it documents is `experiments/ptr-engine/`, whose record is
[`../RECORD.md`](../RECORD.md).

**What this folder is not.** Not a manuscript, not a new experiment, not an implementation plan, not
an approval to spend. `papers/` is untouched; the three filed papers and the in-progress
`papers/context-cache/` manuscript are cited, never modified.

**Written:** 2026-11-06. **Requests sent while writing it:** 0. **Cells launched:** 0.
**Ledger snapshot used:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` — 2,591 spent /
1,729 remaining of 4,320, rebuilt 2026-10-28. That is a *dated record*: it must be reconciled again
at execution time, never assumed current.

---

## The recommendation

**Paper count: two.** One flagship, one methods paper that needs no new measurement. Not three, and
not the "one short law paper" the 2026-11-04 candidate index ranked first — that law is the
flagship's measured core, and shipping it alone would leave its own consequence untested.

| # | Paper | Question | Evidence today | New requests to finish |
|---:|---|---|---|---|
| **F** | **The bill is set by the append, not the window** (flagship) | On a prefix-cached serving stack, is the billed cost of long agent context set by *how much* history is retained, or by *where and how* each append lands — and can a bounded, recoverable context design that respects that arithmetic deliver non-inferior verified answers at lower uncached work? | One exact per-append law (recomputed today from the rows), a residue-based class change, a cross-engine tax, a working prototype with a capability result and a refusal guarantee | **~9** to close the law's own open cell; **≈185** for an instrument pilot; **≈7,560** for the comparative ⇒ `UNFUNDED` at 1,729 remaining |
| **S** | **An instrument must be able to say yes and no** (methods) | When may a harness's null be read as evidence about the system rather than about the harness? | A falsification case series: five logs, identical failure sets, two mutually exclusive graders, four grid defects, one admitted absent stamp | **0** |

**The flagship's thesis in one sentence.** On a prefix-cached server with block size *B*, appending
*L* tokens to a primed prefix of *P1* tokens re-bills `(P1 mod B) + L` — a tail fixed by arithmetic
nobody instruments and independent of the payload — and at `P1 mod B ∈ {0,1}` the entry is gone and
the whole prefix is billed instead; therefore the unit of context design is the **append**, not the
window, and a context engine should be built to batch and align appends rather than to shorten
history.

**Why that is one paper and not two.** The law, the class change and the intervention are one
mechanism seen at three strengths (`(P1 mod B)+L` → avalanche → 2-token rule). The prototype is the
same mechanism seen at design level: its measured properties are exactly the ones the law prices —
12-line index instead of bodies (30,000 B / 447 B = **67.1141×** body-to-index bytes, not a token
saving), one `fetch` per body (an append), a retention cap that produces a **named** refusal instead
of a silent loss (33/33 `PTR_STORE_MISS`), and no-body control discrimination (0/3). Splitting the
law from the design would leave a short measurement note with no consequence, and a design paper
whose economics rest on an unpriced append.

**Why a second paper is warranted at all.** S is not the flagship's method section: its claim is
about *measurement validity*, its evidence is a case series of instruments (not of costs), and it
can be written and submitted **without** F existing, without a single endpoint call, and without
citing F's law. See §"The second paper, and why it is independent" below and
[`SECOND-PAPER-BRIEF.md`](SECOND-PAPER-BRIEF.md).

---

## The boundary: what each paper owns

The workspace already has three filed papers and a fourth manuscript in progress. The seed must not
re-publish them.

| Material | Owner | Why the seed does not take it |
|---|---|---|
| Renderer equivalence, fan-out placement (C53/C55–C57), compaction is silently lossy, the 2×2 engine-vs-model result (C63), compaction at a real boundary (C62), padding costs (C64/C64a), the 64-grid hit law on repeats (C40/C41) | **`papers/context-cache/` (4th paper, sealed 2026-10-24, in progress)** | Already drafted, package-complete and claim-ledgered (`CLAIMS.md`, 69 claims mapped 1:1 by `verify_package.py` today). F **cites** these and must not re-derive them. |
| Encoder crossover economics; replay-record vs decision; gated read batching | **Filed 2026-10-19** — Zenodo `10.5281/zenodo.23463944`, `…23482511`, `…23483314`; TMLR `L9GcDGb2fr`, `U2WjJMH0EK`, `q72ZB9ZMqy` (`strategy/SUBMISSION_RECORD.md`) | Filed work is published work. Standing rule: never assert this work was never published. |
| The append-cost law, the residue cliff, vLLM's `+B`, the two-token rule | **F** | Not in the manuscript: its §9 covers immediate-repeat misses, §9a the per-stack grid, and §8a argues the opposite way about padding because it prices a 64-token page-recovery pad, not a 2-token cliff-avoidance pad. `grep` of `papers/context-cache/` for the law's terms returns only fold/compilation plumbing. |
| The prototype: index + content-addressed bodies + `fetch` + retention refusal + no-body control | **F** | `papers/context-cache/CLAIMS.md` carries **no** claim about the ptr-engine, its ratio, the law or the hit ledger — checked by the engine record's own grep (`RECORD.md` §5 "Checked and clear"). |
| Behaviour of the harness under test (class-indistinguishable negatives, unfireable treatments, replicate collapse, absent stamp, cap-gate under-count, bill identity, A/B bill refutation) | **S** | Different claim type. F may state that its measurements were gated by S's regime; F may not present the case series. |

**Deliberate exclusions.** Nothing in this folder proposes integration into a production agent, a
Rust kernel, or an omp build; no wire API is invented; the `handoff from consonance/` contract's
field names are treated as given. BRCV-style naming appears only where a source document uses it.

---

## The second paper, and why it is independent

**Test applied:** can S stand without recycling F's contribution? Yes, on three counts.

1. **Different claim type.** F claims a cost law and a design consequence. S claims a *validity
   requirement* on measurement, evidenced by a case series in which five scoring variants produced
   one identical failure set (`QUALITY-POSITIVE-CONTROL.md`) and two graders were mutually exclusive
   (`score_longrun.py` accepts only `"64"`; `grade_v2.py` accepts only prose `…64.`).
2. **Different unit of evidence.** S's rows are check-ids, exclusion rules, stamps and control
   tables. It would be unchanged if the cost law were false.
3. **Independent evidence base.** S's central artefacts are offline, zero-request and already
   complete: 0 requests for the quality positive control, 0 for the census in `docs/GRID-2-FINAL.md`
   §0, 0 for the bill refutation (`V-QUALITY-ARM`), all re-derivable without an endpoint.

**Overlap boundary, stated so a reviewer can check it.** The gen-6 grid appears in both, in
different roles: in F it is the reason the comparative is *unmeasured*; in S it is one *case* of an
instrument that could not say yes. S may cite the grid's defect list as one row of its case series;
it may not carry the append-cost law, and F may not carry S's taxonomy as a contribution. No number
is claimed as new in both.

**Priority.** S is second: it is smaller, its venue is a methods/reproducibility track, and it
strengthens F's credibility rather than competing with it. If only one can be finished, finish F.

---

## What cannot be claimed today (read before writing a single sentence)

| Tempting claim | Why it is unavailable | What the record supports instead |
|---|---|---|
| "A pointer/bounded context design is cheaper than a full transcript" | **Not measured.** The comparative is `UNFUNDED` (7,560 vs 1,729); the grid is `not_adjudicable`; and the one equal-information measurement points the **other way** — `C0-EQUALINFO` C0F mean **1,911** vs R mean **3,524** uncached, ratio **1.8441** | "The design changes *which* appends happen; whether that is cheaper at equal information is the paper's open question" |
| "The bounded design is quality-neutral" | Quality path **cannot say yes** (`PATH-CANNOT-SAY-YES`); every quality arm's `verified_success` limb is void before its first call | "Capability: 3/3 exact-fact retrieval through one `fetch`; refusal: 33/33 named `PTR_STORE_MISS`, never a silent wrong answer; discrimination: no-body control 0/3" |
| "The cliff re-bills whole-prefix; the padding rule saves ~8,000 tokens" | The *billed magnitude* is instrument-dependent: one field reads `cached = 8,000` at P1=8064 and bills `64 + L`, another reads `null` and bills `P1 + L`; `RECORD.md:114` records the 5.2× as withdrawn then **UNDECIDABLE** | "The tail law is exact; the class change is measured on both instruments; the magnitude is instrument-dependent; padding is positive under **every** reading (≈64 tokens on the counter reading, ≈`P1 − r` on the null reading)" |
| "67.1× is a saving" | It is **body bytes over index bytes**, not tokens, cost or latency (`RECORD.md` §1) | "the prompt carries a 447 B index instead of 30,000 B of bodies; the bill is measured separately" |
| "Cache hits make an append-only transcript cheap" | An append-only transcript still grows in logical input; hits cut prefill work, not token count (protocol R12) | as stated, with `cached_tokens` reported per turn |
| "The law applies to conversations" | Its own §8 scope: **one** append onto an already-primed prefix; multi-append was never swept end to end | "the multi-append extension is prospective" — and Roadmap stage B prices the ~9-request cell that closes one shape of it |

---

## Package documents

| doc | what it answers |
|---|---|
| [`EVIDENCE-DOSSIER.md`](EVIDENCE-DOSSIER.md) | every usable contribution mapped to its dataset, record, claim, conditions, recompute command, evidentiary status, contradictions and proposed role |
| [`RESEARCH-BRIEF.md`](RESEARCH-BRIEF.md) | the flagship: problem, question, contribution, baselines, prototype, evidence available, claims needing validation, limitations, failure conditions |
| [`SECOND-PAPER-BRIEF.md`](SECOND-PAPER-BRIEF.md) | the methods paper: question, contribution, existing evidence, validation, overlap boundary |
| [`VALIDATION-ROADMAP.md`](VALIDATION-ROADMAP.md) | staged plan: offline freeze → cheap instrument pilot → stage-0 gates → adjudicable comparative, with controls, measurements, adjudication rules, stop conditions and approval gates |

### Source anchors this folder rests on

| path | role |
|---|---|
| [`../../miss-law/LAW.md`](../../miss-law/LAW.md) | the law, its scope, its withdrawals (`§8`, "Scope and withdrawals") |
| [`../../miss-law/rows.jsonl`](../../miss-law/rows.jsonl) | 774 rows the law is fitted on |
| [`../RECORD.md`](../RECORD.md) | the reconciled engine record; C1/C3/C10 contradictions |
| [`../../../docs/GRID-2-FINAL.md`](../../../docs/GRID-2-FINAL.md) | the grid census, the collapse arithmetic, the `not_adjudicable` verdict |
| [`../longrun/QUALITY-POSITIVE-CONTROL.md`](../longrun/QUALITY-POSITIVE-CONTROL.md) | `PATH-CANNOT-SAY-YES`, five-log truth table |
| [`../../../research/next-candidates/consonance-bounded-context-evaluation.md`](../../../research/next-candidates/consonance-bounded-context-evaluation.md) | the prospective protocol: arms, controls, budgets, void conditions |
| [`../../../research/next-candidates/2026-11-04-candidates.md`](../../../research/next-candidates/2026-11-04-candidates.md) | the candidate ranking this folder supersedes as a *recommendation* (not as a record) |
| [`../../../docs/STATE.md`](../../../docs/STATE.md) | current state, ledger, open decisions |

---

## Verifying this folder

```bash
# the law, recomputed from the rows (no network, no endpoint)
cd "/home/zer0null/research extractor" && python3 - <<'PY'
import json, collections
rows=[json.loads(l) for l in open('experiments/miss-law/rows.jsonl') if l.strip()]
fit=[r for r in rows if r.get('L_app') is not None and r.get('role')=='measure' and r.get('prev_prompt_tokens') is not None]
def resid(r,B,extra): return r['uncached_tokens']-((r['prev_prompt_tokens']%B)+extra+r['L_app'])
for srv,B,extra in (('sglang',64,0),('vllm',1056,1056)):
    sub=[r for r in fit if r['server']==srv]
    print(srv,len(sub),dict(sorted(collections.Counter(resid(r,B,extra) for r in sub).items())))
PY

# the grid verdict, recomputed from its machine twin
python3 experiments/ptr-engine/tools/grid2_final_report.py --check   # or read measure/GRID-2-FINAL.json

# the manuscript package as it stands today
.venv/bin/python papers/context-cache/verify_package.py

# the documentation contract
python3 tools/doc_check.py
```

Expected from the first block (2026-11-06): `sglang 301 {0: 218, 2048: 2, 4096: 2, 6144: 2, 7680: 1,
7936: 2, 8000: 8, 8064: 66}` and `vllm 86 {-1056: 1, 0: 85}` — i.e. residual zero on every row that
is not an avalanche, and the avalanche rows billing `P1 + L` exactly. Any other output means the
file changed and this folder's numbers must be re-derived before reuse.

---

## Corrections this folder folds into the record

Found while reconciling, each with its evidence, so the next reader does not repeat them:

1. **`1,892 uncited rows` is not reproducible.** `N4-finish-flagship.md` and
   `2026-11-04-candidates.md` state seven uncited cells hold 1,892 rows. Re-counted today:
   `experiments/context-cache/cells/E1` 264, `E2` 222, `E3` 264, `E4` 395, `E4R` 360, `LIVE-MEAS` 3,791, `M1-M` 107 —
   **5,403 `.jsonl` lines**. The *qualitative* claim (all seven uncited: a grep of `papers/context-cache/`
   for `experiments/context-cache/cells/E1|E2|E3|E4|E4R|LIVE-MEAS|M1-M` still hits only `RUN.json`) stands; the number does not.
2. **`63 claims` is a RUN.json synthesis count, not today's ledger.** `verify_package.py` today:
   `PASS — 69 claims in CLAIMS.md, 69 mapped 1:1`. Quote 69 for the package, and 63 only as
   `RUN.json`'s `verification/synthesis_recompute.claims`.
3. **`LAW.md` §3 prose says "four separate block indices"** while its own list contains six
   (`#32, #64, #96, #120, #124, #125`) and the rows carry 11/11 misses across exactly those. Six.
4. **`docs/GRID-GAP-DIAGNOSIS.md:188`'s 162 requests/cell is declined** and recomputed as 79.375 —
   already recorded in `GRID-2-FINAL.md` §5; repeated here because the number still circulates.
