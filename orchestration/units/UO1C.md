# UO1C — O-1A evidence assessment on the corrected disclosure facts

**Unit:** UO1C · **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Date:** 2026-10-15
**Status:** done
**Hard bound:** max 20 tool calls. **Used: 12.**

## One purpose
An updated, honest **evidence assessment** for an O-1A petition on the corrected facts: 13/13 kernel
mechanisms are already public (MIT), the umbrella paper is withdrawn, the implementation is proven
still private.

## Inputs (all on disk; no web tool used)
- `AGENTS.md`
- `strategy/VISA_US_ROUTES.md` — grepped for O-1; §3 (`:209–308`), §4 (`:348–358`), §7 (`:595–615`)
  read only in ranges.
- `strategy/TRADE_SECRET_AUDIT.md` — section headers grepped only (**not** read in full).
- `strategy/DISCLOSURE_INVENTORY.md` — grepped for the 13/13, MIT, digest, 404 facts.
- `strategy/CODE_LICENSING_STRATEGY.md:375–419` — criterion-5 quotes.
- `orchestration/units/ULIC.md:63` — criterion-6 no-citation sentence.

## Constraint compliance
- **No web tool of any kind was called.** All quotes lifted from disk.
- `strategy/VISA_US_ROUTES.md` was **never read in full** — grepped, then ranged reads only.
- File was **created as a skeleton after the first reads** and filled incrementally; it was never
  left empty and no existing file was edited.
- `/home/zer0null/Duval` untouched; no git run anywhere.

## Findings
1. **Card correction (recorded, not worked around):** the criterion-5 quotes are **not** in
   `strategy/TRADE_SECRET_AUDIT.md` §4 — that section is "Per-mechanism triage". They are on disk at
   `strategy/CODE_LICENSING_STRATEGY.md:382–393` (fetched by UCODE1, 2026-10-15), corroborated at
   `strategy/VERIFICATION_REPORT_2.md:16`.
2. **Criterion 6's no-citation sentence is not in** `VISA_US_ROUTES.md` or a `VERIFICATION_REPORT`;
   it is at `orchestration/units/ULIC.md:63`.
3. **6 statements in `VISA_US_ROUTES.md` are superseded** (S1–S6, tabulated in the artifact).
4. **5 assets assessed** on what an officer could verify: public design repo, private implementation,
   MIT mechanisms, papers, criterion 6.
5. **6 gaps ranked** by reachability; **highest-leverage action** = mint a DOI for the public design
   repo and document the MIT grant as the standing invitation for third-party use.
6. **The ceiling is stated unsoftened**: no verified precedent for a software/AI researcher without a
   PhD (`VISA_US_ROUTES.md:773`), and the nearest analogue — *Kazarian v. USCIS*, 596 F.3d 1115
   (9th Cir. 2010), a PhD physicist denied — is cautionary, not supportive.
7. **Central inversion reported both ways:** the disclosure is the biggest evidentiary **loss** (it
   removes secrecy) *and* the only remaining path to criterion 5, because criterion 5 wants
   **third-party use**, which the permissive MIT licence enables and a noncommercial licence would
   have foreclosed.

## Artifact
`strategy/O1_EVIDENCE_ASSESSMENT.md`

## Bound / stop
Completed within bound. No blocker.
