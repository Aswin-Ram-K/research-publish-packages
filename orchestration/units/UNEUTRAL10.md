# UNEUTRAL10 — case-variant settlement

**Purpose (one):** settle the survivors `strategy/VERIFICATION_REPORT_32.md` found after the
whole-class sweep, verdict them, neutralise the genuine system names, and prove nothing published moved.

**Write paths:** `scratch/uneutral10/**`, `strategy/CASE_VARIANT_SETTLEMENT.md`,
`orchestration/units/UNEUTRAL10.md`, `orchestration/handoffs/UNEUTRAL10.json`.
**Hard bound:** 25 tool calls.
**Source tree:** `scratch/uneutral9/package/` — read-only; worked on `scratch/uneutral10/package/`.

**Steps + outcome:** re-derived the survivor list case-insensitively; bucketed by location
(inside stimulus / prose-comments / record keys / filenames); classified (a) names vs (b) ordinary
English vs (c) harness names; renamed `Broker` by the existing injective case-sensitive scheme and
reworded the `ANSWER` comment at `verify/recompute-claims.py:117`; measured κ/agreement/pe/exact_index/
ties/zero_score before and after (no movement); regenerated `MANIFEST.json` and proved it with an
independent re-hash checker plus a build-twice idempotence run.

Full settlement record: `strategy/CASE_VARIANT_SETTLEMENT.md`.
