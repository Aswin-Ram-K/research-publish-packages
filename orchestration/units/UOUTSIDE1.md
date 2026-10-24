# UOUTSIDE1 — outside-stimulus residue redaction (release build exclusion gate)

**Purpose (one purpose).** Starting from `scratch/utool1/tree-six` (copy → `scratch/uoutside1/tree-seven`),
enumerate and classify the OUTSIDE-stimulus residue of the release build's exclusion gate, redact what can be
redacted under NEUTRAL-TAG/v1 without editing shipped tooling, and prove the invariants (no published claim
number moves; inside-stimulus census delta = 0; manifest regenerated and independently checked; idempotent).

**Hard bound.** 30 tool calls. Status `done` | `partial`. Partial with named remainder is a result.

**Not mine.** The 10 mechanism tokens inside the model's `question`/`options` stimulus (author has not ruled).
Do not touch, rename, or "helpfully" fix one.

**Write paths (declared).** `scratch/uoutside1/**`, `strategy/OUTSIDE_TOKEN_REDACTION.md`,
`orchestration/units/UOUTSIDE1.md`, `orchestration/handoffs/UOUTSIDE1.json`.
Never write any other `scratch/**` subtree, `repro/**`, `papers/**`, `strategy/**` other than my report,
`orchestration/units/UBUILD1.build.sh`, `tests/test_build_wiring.py`, `strategy/BUILD_WIRING.md`,
`/home/zer0null/research-publish-packages`.

**Conventions.** NEUTRAL-TAG/v1 as in `scratch/ubij1/bij_one.py` and `scratch/udtag1/dtag_one.py`: stable
neutral tags, applied consistently, mapping **never written, logged or shipped**. Tag family `TAG_NN`
(`TAG_01`, `TAG_02`) because `TAG_[0-9][0-9]` is the only family accepted by BOTH gate copies, whereas
`P[0-9][0-9]` (dtag's family) is not accepted by the build gate's `TAG_RE`.

**Filename rule applied.** For each file that would be renamed, its references were enumerated first. Where a
rename would require editing shipped tooling, the token is STOPPED and reported, not renamed (a tool rewired
to follow a rename stops being evidence). See report §Conflict.

**Deliverable.** `strategy/OUTSIDE_TOKEN_REDACTION.md` + the unit handoff.

---

## Outcome (recorded 2026-10-16, status `partial`)

- Emitted `scratch/uoutside1/tree-seven` (45 files) from `scratch/utool1/tree-six`; rebuilt as `tree-seven-b`
  for idempotence (build digest `63d015b1…52ef6`, all 44 non-manifest files byte-identical; manifest differs
  only in `generated_utc`).
- Redacted 2 identifiers / 13 occurrences / 4 files under NEUTRAL-TAG/v1 (`TAG_01`,`TAG_02`; map withheld).
  All `.json`/`.jsonl`/`.ts`/`.md` files byte-identical to tree-six.
- `recompute-claims.py` exit 0, `ALL CLAIM NUMBERS PRESERVED: True`; compileall exit 0; train/dev/disagreements
  800/200/18 all malformed=0; both second-labeller tools exit 0 and are byte-stable against the unredacted
  control.
- Census inside-stimulus 2171 occurrences / 30 distinct before and after — delta **0**.
- Manifest regenerated from disk and proved by an independently written checker: 0 missing, 0 hash mismatch,
  0 size mismatch, 0 unlisted, 0 listed-but-absent; `MANIFEST.json` 443 lines / 22709 bytes /
  sha256 `fecd31574bad62cef328d7d95b851ac338aad552c420d1b08a1126cb48cd97ef`.
- STOPPED and reported: `tccommon`/`harness/tccommon.py`, `tcmodel`/`harness/tcmodel.py`,
  `evals/fixtures/reflex-decisions.ts` — renaming them rewires shipped harness + second-labeller tooling.
- Report: `strategy/OUTSIDE_TOKEN_REDACTION.md`.
