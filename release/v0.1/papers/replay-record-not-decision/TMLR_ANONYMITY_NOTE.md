# TMLR anonymity note — the companion-note citation (paper #2)

**Scope.** This note states only what TMLR's double-blind rule requires of the *citation* to the
companion note — paper #3's Zenodo deposit, concept DOI `10.5281/zenodo.23463944` — in
`papers/replay-record-not-decision/MANUSCRIPT.md` and the `submission/main.tex` regenerated from it.
It does **not** rebuild the anonymised variant, and it states no new measurement.

## What the rule requires

TMLR reviews under double-blind conditions on OpenReview: the submission PDF must carry no
author-identifying information (no byline, affiliation, acknowledgements, or self-identifying links),
and references to the authors' own work must be phrased in the **third person**. Check the current
policy text on the TMLR site/OpenReview before relying on this paragraph; the requirement below
follows from those two rules, not from quoted policy text.

## Why the DOI is identifying here

`10.5281/zenodo.23463944` is a **concept DOI**: it resolves to the Zenodo record for paper #3 and to
every version below it. That record's metadata carries the depositor/author name (the same author as
this note's byline) and the paper title. Printing the DOI in the anonymous PDF therefore hands the
reviewer a resolvable link that **names the author** — the disclosure double-blind forbids. It is not
rescued by being "only a dataset link": the linked record is author-attributed. The same applies to
the Zenodo URL, the deposit's version DOI, and any `\texttt{10.5281/…}` fragment appearing in the
abstract, the summary sentence, §2 or §7.

## What the anonymous variant must therefore say

1. **Do not print** the DOI, the Zenodo URL, or any other resolvable identifier that reaches the named
   deposit anywhere in the anonymous PDF (abstract, §2, §6, §7 and the bibliography alike).
2. **Refer to the companion in the third person, without the identifier**, e.g.
   *"The stimulus fixture is released with the companion note [citation withheld for double-blind
   review]; its case set and per-kind counts correspond to these records as described in §7."*
3. **Keep the substantive §7 content** — same 190 cases, same per-kind counts, different neutralised
   tagging, mapping recoverable uniquely from the per-kind sequence of `correct` values. Only the
   identifier is withheld; the availability statement stays true.
4. **Restore the DOI and the standard citation in the camera-ready** (non-anonymous) version, and
   record the withheld identifier in the anonymisation build record so the two variants are provably
   the same paper modulo the byline and this citation.
5. If the companion note is itself under double-blind review at submission time, cite it in the
   permitted anonymous form (e.g. *"Anonymous, under review"*) rather than by name; if it is not, a
   third-person named citation without the resolvable DOI is the form to confirm with the chairs.

## Update 2026-10-19 (UDOIBACK2) — this deposit's own DOI, same rule

The manuscript now carries a **second** DOI: its **own** deposit, Zenodo concept DOI
`10.5281/zenodo.23482511`, printed in §7 (Data availability). It is identifying for exactly the same
reason as the companion DOI above — it resolves to a record whose metadata names the author — so the
rule under "What the anonymous variant must therefore say" applies to it verbatim: the anonymous PDF
must print neither `10.5281/zenodo.23482511` nor the version DOI `10.5281/zenodo.23482512`, in §7 or
anywhere else. The availability statement stays true without the identifier: that paragraph names the
records and the tooling, and no resolvable link is required for it to hold. Nothing above is
retracted, and this note still does not rebuild the anonymised variant.

**Adjacent item, same rule (not performed here):** the current author block,
`\author{Aswin Ram Kalugasala Moorthy\\ Independent researcher\\ \texttt{aswinram.k.1603@gmail.com}}`
(as generated from the manuscript's author slot), must become an anonymous author block in the same
variant; the email address is doubly identifying.

**Correction 2026-10-19 (UDOITIDY2):** the byline quoted above previously dropped the `ram` from the local part of the contact address; that was a transcription error in this note, not in the paper. The shipped camera-ready LaTeX byline (`submission/main.tex:12`) reads `aswinram.k.1603@gmail.com` and is frozen — this note now matches it.
