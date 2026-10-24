# Unit UVERAD6 — independent verification of UFIXAD6 (AD-6 archive-window corrections)

**Purpose:** verify that UFIXAD6 applied the AD-6 resolution faithfully to
`strategy/WITHHELD.md` and `strategy/GATED_READ_DISCLOSURE.md` — 9 in-place dated
corrections, originals preserved, class moves exactly as decided, protective
conclusion intact, forbidden files untouched.

**Not my job:** re-deriving the archive window (that was UAD6); fixing anything.

**Author under test:** UFIXAD6 — `orchestration/handoffs/UFIXAD6.json`,
`orchestration/units/UFIXAD6.md`, report `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`
(UAD6 handoff `orchestration/handoffs/UAD6.json`).

**Hard bound:** 15 tool calls. Small increments. Persist this card first, then a
stub `strategy/VERIFICATION_REPORT_AD6.md`, then append findings as measured.

**Constraints:** `/home/zer0null/Duval` strictly read-only, no git against it.
Do not edit `strategy/WITHHELD.md` or `strategy/GATED_READ_DISCLOSURE.md`; the
red→green revert happens only in `scratch/uverad6/`.

**Write paths (exactly):** `strategy/VERIFICATION_REPORT_AD6.md`,
`orchestration/units/UVERAD6.md`, `orchestration/handoffs/UVERAD6.json`,
`scratch/uverad6/**`.

**Checks:** (1) nine anchors hold; (2) negative true (no `ccdab112`+`consonance/`
pairing but the negation); (3) class changes match decision exactly — §1.4, §1.5,
X-08, X-07 `src/` only moved; U-1 decided; AD-6 resolved; all else untouched;
(4) protective conclusion survives; (5) red→green non-vacuous; (6) forbidden
files unmodified (backup or mtime, else `unverified`). Plus: annotation of §1
items 4/5 must be legible (when, on what evidence).

**Exit:** verifier-shape handoff `orchestration/handoffs/UVERAD6.json`, re-parsed;
≤15-line summary; message to parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.
