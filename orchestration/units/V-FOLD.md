# V-FOLD — independent verification of FOLD-PROPOSAL.md

Unit: V-FOLD. Verifier (not author). Read-only on the repo except `orchestration/handoffs/V-FOLD.json`
and this card. Bound 18 tool calls. No network, no endpoint, no git against a target.

## Objective
Does every figure `papers/context-cache/FOLD-PROPOSAL.md` wants to publish survive re-derivation, and
does every figure it says must be dropped deserve dropping?

## Verdict: fail
4 of 5 drafted claims (C70-C72, C73-capability) re-derived exactly. The fifth, C74, is false on
today's tree. Three classification defects and a systematic citation-index error.

## What was re-derived (by command, not by prose)
1. **C70 exact.** `.venv/bin/python experiments/ptr-engine/tools/rebuild_corpus.py` exit 0:
   BODIES 12, BODY_BYTES 30000, INDEX_BYTES 447, INDEX_LINES 12, BYTES_PER_LINE 37.25,
   ZERO_RESOLUTION_PROMPT 472, RATIO 67.1141, sha256 `e08700c9…9bd2`. 30000/447 = 67.1141.
2. **C71 exact.** `experiments/miss-law/rows.jsonl`: 774 rows, 387 with both `n_payload`/`L_app`,
   `sum(L_app != n_payload+12) = 0`. The draft's denominator is the subset and is stated as such.
3. **C72 exact.** `experiments/ptr-engine/measure/rows.jsonl`: 9 warm rows; A/5/18, B/2/15, D/2/15
   uncached at L = 13; 0 violations of `cached = P1 − residue` and of `uncached = residue + L`.
4. **C73 capability exact.** A 3/3, B 0/3, C 3/3, D 0/3 (T4 `answer_has_fact`, 12 request rows/arm);
   arm D rep rows `resolved_total [0,0,0]`, `withheld_total [5,5,5]`, `final_answer 756741be` x3.
5. **C74 wrong.** Suite is **190 passed in 0.24 s**, not 187 — same under `python3` and `.venv/bin/python`.
   The proposal prints 187 in bucket (i), in bucket (ii) ("only 187 is re-derivable") and in the draft.

## Findings
- **F1 (worst).** C74 is the one figure the draft states as re-derived on today's tree and it is wrong;
  bucket (ii)'s branch-suite limitation inherits the error.
- **F2.** "33 `PTR_STORE_MISS` (11/rep)" is in no field of `quality/rows.jsonl`: 3 code occurrences
  total, arm B `withheld_total` 0, `resolved_total` 5, `refused_total` 0.
- **F3.** Bucket (iii) **omits** the retired 3.0418x dense engine ratio (`CLAIMS.md:239`); "3.0418"
  occurs 0 times in the proposal. The other three required items are present.
- **F4.** Negative-control and warmpool items are called publishable now but carry no claim id and are
  absent from the drafted §9e — no `CLAIMS.md` entry would ever exist for them.
- **F5.** 7 of 8 `checks[...]` citations name the wrong element: the strings are labelled 1..7 while the
  array is 0-based with an extra `2b FINDING` at index 2. V-ENGINE-P0: r is `checks[4]` (cited 3),
  determinism `checks[3]` (cited 2), negative controls `checks[6]` (cited 5), warmpool `checks[7]`
  (cited 6). V-QUALITY-ARM: discrimination is `checks[1]` (cited 2 — the same index line 28 correctly
  uses for the index leak), telescoping refutation `checks[4]` (cited 5).
- **F6.** Numbering is clean inside `papers/context-cache/CLAIMS.md` (ends C69, 0 hits for C70-C74) but
  **C70-C73 already exist** in `papers/gated-read-batching/CLAIMS.md:121-124` (+130/134/136).
- **F7.** The proposal understates its own reproducibility: it says no runnable 12-body corpus build
  exists and asks for one, while `tools/rebuild_corpus.py` prints exactly 30000/447/472/67.1141 at exit 0.
- **F8.** The brief's premise that `V-RECORD.json` refutes the 5.2x is not supported: that file holds
  0 occurrences of "5.2"/"undecidab". The verdict lives in `RECON-C1.md`, which is what the proposal cites.

## Not edited
`FOLD-PROPOSAL.md`, `MANUSCRIPT.md`, `CLAIMS.md`, `RECORD.md`, every row file and experiment artefact
were read only. A wrong figure is a finding here, not an edit.
