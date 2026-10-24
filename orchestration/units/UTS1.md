# UTS1 — Trade-secret audit of the author's own outputs

**Status:** done · **Written:** 2026-10-15 · **Hard bound:** max 50 tool calls · **Used:** 30

**Artifact:** [`strategy/TRADE_SECRET_AUDIT.md`](../../strategy/TRADE_SECRET_AUDIT.md)

## Purpose (one purpose)

Audit what the author's own outputs disclose, and produce a per-mechanism triage: what can be published
without destroying trade-secret status, and what cannot.

## Premise change applied mid-run

The card was written assuming `PAPER_DERIVATION.md` might be *edited* into a publishable state. The author
withdrew that (2026-10-15): *"dont publish any blanket papers, only small extracted projects that go public
and the papers associated with it."* The organising distinction is therefore **blanket paper (withhold)** vs
**extracted standalone project (publish)**, decided by the test: *could this be released on its own, without
the rest of Consonance, and still make sense?*

`PAPER_DERIVATION.md` fails that test **by its own admission** (§6.4 `:669–672`: every result is *"a result
about a model of the kernel, built against its real types and its real hasher"*). It is a blanket paper. Its
disclosure findings are recorded as **evidence the withholding decision is correct**, not as remediation.

## Findings

1. **Legal standard sourced.** 18 U.S.C. §1839(3)(A)/(B) (definition; "reasonable measures"; "not being
   generally known"), §1839(6)(B) (reverse engineering / independent derivation are not improper means),
   §1836(b)(1) (DTSA private action), 35 U.S.C. §102(a)(1) (printed publication = public disclosure). All
   fetched 2026-10-15 UTC from Cornell LII, quoted verbatim with URL. DTSA identified as Pub. L. 114–153,
   May 11, 2016, 130 Stat. 376 from the section's own amendment notes.
2. **Paper #3 hypothesis: CONFIRMED for the manuscript, REFUTED for its release package.** `MANUSCRIPT.md`
   is a pure measurement (F8) whose only kernel-adjacent text *withholds*. But `repro/encoder-crossover-190/`
   ships `fixture/DECISION_CASE_SCHEMA.ts` — the complete `DecisionKind` union and the six kernel namespaces
   — and `fixture/reflex-decisions.ts`, whose 2,220 lines contain **335 mechanism-narrating lines** naming
   `src/broker.ts`, `src/scope.ts`, `src/layer.ts`, `StateClass` (32×), `grantPolicy` (30×), `expanded[]`,
   `admit()`, and stating enforcement-by-absence outright at `:292`. `EXCLUDED.md` E1 bounds *implementation
   code*; it does not bound *mechanism*. This is `needs-author-decision` and is **time-sensitive** — it is
   already inside an announced release.
3. **`PAPER_DERIVATION.md` discloses the core.** 16 problem sections; the disclosed material *is* the paper's
   contribution (abstract `:11–16`; §1.4 `:72–76`), so **no minimal edit exists** — the compliant transform
   is a different paper. M1–M13 triaged `withhold`.
4. **Mosaic risk: high.** Three passages already recompose into a buildable spec (abstract M1 + §4.4 :339–345
   token grammar + §4.3b :321–325 gate requirement). The six derivation experiments are one architecture cut
   into six, all sharing §5.5's single binding rule. Emitting them as "extracted projects" would produce a
   set a reader can reassemble.
5. **Eight findings extracted as publishable without mechanism** (`abstract-to-findings`): F1 a read is not a
   gate; F2 outcomes-only journals cannot represent ambiguity; F3 replay reproduces the record not the
   decision; F4 a percentage without its break-even is not a result; F5 a positive result needs a control
   that could have said no; F6 M1–M7 failure taxonomy; F7 EXP#11 negative result; F8 encoder crossover.
6. **O-1 cost recorded, not argued:** withholding the blanket paper means the architectural claim is never
   published and cannot be claimed as a published contribution. Mitigation: report the result and the
   constraint, never the construction.

## Evidence commands

- `git -C /home/zer0null/Duval rev-parse HEAD` → `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` (before = after)
- `git -C /home/zer0null/Duval status --porcelain` → 4 untracked paths, identical before and after
  (`.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`)
  — **attributed to the unrelated concurrent session**, not this unit
- `grep -cEi 'StateClass|GrantPolicy|broker|admit\(\)|src/…' repro/encoder-crossover-190/fixture/reflex-decisions.ts` → **335**
- `find repro/encoder-crossover-190 -type f | wc -l` → **43** (`EXCLUDED.md` says 42 — recorded U9)
- fetched `law.cornell.edu/uscode/text/{18/1839,18/1836,35/102}` → HTTP 200, verbatim excerpts captured

## Read-only discipline

Target never written, no git state changes. The repo is permanently dirty from a concurrent session; the
same four untracked paths are recorded in `repro/encoder-crossover-190/EXCLUDED.md` §5 and
`papers/encoder-crossover-190/DISCLOSURE_CHANGES.md`, confirming attribution.

## Write paths touched

`strategy/TRADE_SECRET_AUDIT.md`, `orchestration/units/UTS1.md`, `orchestration/handoffs/UTS1.json` — nothing else.

## Not legal advice

A trade-secret strategy with commercial intent is worth a lawyer's time. Largest untested assumption:
no audit of prior public/social disclosure was performed (U13).
