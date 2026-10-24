# UFIX8 — label the inference in `RELEASED-PIECE/COMMERCIAL.md`

**Unit:** UFIX8 (correction unit, finishing UFIX7's outstanding item under `VERIFICATION_REPORT_7.md`).
**Bound:** max 20 tool calls — **used 14**, stopped inside the bound.
**Target repo:** `/home/zer0null/Duval` — strictly read-only; **never touched** (no write, no `git`, not even a read).

## Purpose (one purpose)

Make every claim in the released-piece templates **honestly labelled** — quoted licence text where it is
quoted, inference where it is inference. **Fix the attribution, not the substance:** no conclusion is
weakened.

## Declared write paths (touched nothing else)

- `strategy/licence-templates/RELEASED-PIECE/COMMERCIAL.md`
- `strategy/licence-templates/RELEASED-PIECE/CONTRIBUTING.md` (swept, **no edit needed**)
- `orchestration/units/UFIX8.md`
- `orchestration/handoffs/UFIX8.json`

Explicitly **not** touched: `RELEASED-PIECE/LICENSE` (any line, in particular 10–140), `PLACEMENT.md`,
`README-PARAGRAPHS.md`, `TRADE-SECRET-NOTICE.md`, `strategy/**` outside `RELEASED-PIECE/`, and
`/home/zer0null/Duval`.

## Changes applied to `COMMERCIAL.md`

1. **`:16` (the work order's target) — "no free commercial evaluation" is now labelled an inference.**
   The bullet keeps the conclusion (*"There is no free commercial evaluation and no trial grant — a
   commercial licence must be obtained first"*) and adds: the licence does not use the word
   *"evaluation"* and grants no trial; the result is an **inference from the licence's own qualifier**,
   *"without any anticipated commercial application"*, read with its exhaustive list of permitted
   purposes; **not** quoted licence text. Wording mirrors the corrected model in
   `README-PARAGRAPHS.md` (UFIX7).
2. **`:7–8` (further sweep — claim presented as licence text that the licence does not contain).** The
   blanket *"The Noncommercial licence does not cover commercial use, and no commercial right is granted
   by it"* was stated without attribution. It is now labelled an **inference from the scope of the
   grant**, quoting the licence's own words verbatim — a copyright licence "to do everything you might
   do with the software that would otherwise infringe the licensor's copyright in it **for any permitted
   purpose**" — read with `No Other Rights` ("These terms do not imply any other licenses."). The
   commercial-requires-payment position is **unchanged**.
3. **`:30–37` ("What is free") — paraphrase labelled.** The list of free purposes is now attributed:
   it is a **paraphrase** of the licence's `Personal Uses` and `Noncommercial Organizations` clauses;
   the clauses are the operative text and `LICENSE` carries them verbatim. The academic carve-out
   conclusion is unchanged and not weakened.

## Sweep of the other two `RELEASED-PIECE/` files

- **`LICENSE` (outside lines 10–140).** Read only. Lines 1–9 (Required Notice line with `<YEAR>`
  `<COPYRIGHT HOLDER>`; name/logo reservation) and 141–150 (closing delimiter + provenance note) are
  correctly and explicitly labelled: the provenance note itself states that the block is a verbatim copy,
  that the only additions are the Required Notice line, the name/logo reservation and the delimiters.
  **No unmarked licence claim found. No edit.**
- **`CONTRIBUTING.md`.** Swept against the report's overstated list. Checked and found faithful:
  the `Changes and New Works License` claim ("make changes and new works … for any permitted purpose",
  `LICENSE:50–53`) and the `Distribution License` claim ("a copyright licence to distribute copies of
  the software", `LICENSE:32–34`) both match the quoted clauses; the `Notices` requirement is stated
  correctly; the CLA/DCO passage (`:34–37`) is a consequence of accepting no code, not licence text;
  the block quote at `:27–29` is explicitly framed as the author's reason ("Here is the reason, stated
  plainly"), not as licence text; and the name/logo section already carries UFIX7's `Notices`
  non-propagation limitation (`:59–66`). **No unmarked licence claim found. No edit.**

## Placeholders (step 3)

- `COMMERCIAL.md:44` — `<CONTACT EMAIL OR URL — author to fill in>`: **labelled a placeholder** (the
  adjacent gap block at `:46–50` says it "must be filled in by the author before release"), and **left
  unfilled**, per UVER7 Priority 4(a).
- `COMMERCIAL.md:3` — DRAFT banner present ("template for the author to place").
- `CONTRIBUTING.md:3` — DRAFT banner present.
- `LICENSE:1,3` — `<YEAR>`, `<COPYRIGHT HOLDER>`, `<PROJECT NAME>` remain unfilled placeholders; the
  provenance/Required Notice framing at `LICENSE:1` and the placement step in `PLACEMENT.md` are the
  author's fill-in route. Not invented here.

## PolyForm body untouched (step 4)

```
sed -n '10,140p' strategy/licence-templates/RELEASED-PIECE/LICENSE | sha256sum
ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8  -
```

Matches UVER7's upstream value `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`
exactly. Full-file sha256 `25aa637ba1689e87ad34c5acc25464a4eaaa2f5b2c84e3dc4d7ed84158277cfe`
(150 lines). **No byte inside lines 10–140 was edited** — all edits were made in `COMMERCIAL.md`, a
different file.

## Rules honoured

- **No licence text, clause or legal claim was invented.** Every quotation used is a byte-exact substring
  of `LICENSE` lines 10–140 (verified by reading those lines before quoting).
- **No conclusion weakened:** commercial-requires-payment, the academic carve-out and the ideas-only
  contribution rule all stand exactly as drafted.
- **Read-only discipline:** nothing written or run in `/home/zer0null/Duval`.

## Did not do

- Did not edit `CONTRIBUTING.md` (swept; nothing needed).
- Did not fill `<CONTACT>` or any other placeholder.
- Did not edit `LICENSE` at all, and nothing outside the declared write paths.

## Next hint

The declared write-path corrections from UVER7 are now complete across both `RELEASED-PIECE/` and the
`strategy/licence-templates/` top level. A fresh **verifier** unit should re-run the hash, confirm the
two new `Attribution:` labels are present at `COMMERCIAL.md:22–26`, `:12–13`, `:35–37`, and run the
red→green check (strip the label → the claim reads as unqualified licence text again). Remaining
author-side gap: `<CONTACT>` and the `<YEAR>`/`<COPYRIGHT HOLDER>` placeholders, deliberately unfilled.
