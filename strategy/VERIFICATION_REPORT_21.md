# VERIFICATION REPORT 21 — UVER21, independent verifier of UFIX24

**Verdict: `partial`.** UFIX24's central evidentiary claim (the build-script derivation) reproduces
exactly, and its judgement call on `redact.py` is **right**. But two of its sub-claims do not survive
re-checking, and MIT is still asserted as current, unpointed, in two workspace documents and in a
stale emitted build tree.

I did not write any of the work under verification. Every comparison-below was re-derived from disk.

---

## 1. Build-script derivation — CONFIRMED, in full

Re-derived independently from `orchestration/units/UBUILD1.build.sh`, not copied:

| claim | re-derived |
|---|---|
| size | **1,019 lines** |
| sha256 | `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69` |
| gate heredoc open | `:771` `cat > "$DEST/gate.sh" <<'GATE_EOF'` |
| gate heredoc close | `:896` `GATE_EOF` |
| `chmod +x` | `:897` |
| `CODE_VOCAB_EOF` | `:695`–`:743` |
| `PUBLIC_VOCAB_EOF` | `:748`–`:769` |
| invocation | `:1005` `bash "$DEST/gate.sh"` |
| exit propagation | `:1015` `exit "$GATE_RC"` |
| licence copy | `:575` `LIC_SRC=…`, `:579` `cp`, `:584` guard `3d364676…f900` |
| scope heredoc | `LICENSE_SCOPE_EOF` `:590`–`:602` |
| paper instrument | `PAPER_LICENSE_EOF` `:607`–`:637` |

All twelve match. The trap UFIX24 flagged is real and it respected it: **`sys.exit(1)` is not unique**
— it appears at **`:893` and `:954`** — so it is unusable as a standalone anchor.

## 2. The judgement call — UFIX24 is RIGHT; the earlier description was wrong

`repro/encoder-crossover-190-SANITISED/redact.py`, verbatim:

```
203|SAFE_KEYS = {"id", "kind", "_line", "sha256", "sourceSha256", "sha256_16", "correct",
204|             "recorded_index", "goldIndex", "predIndex"}
205|CASE_FIELD_RE = re.compile(r"^    [a-z_]+:")
206|# `options` is deliberately NOT here: REPORT2 §5 measured that substituting one option label moves
207|# routeA.ties 120 -> 119 in second-labeller/metrics.json, so an option label is not substitutable.
208|CASE_FIELDS = ("question",)
```

`:204`–`:205` is the **tail of `SAFE_KEYS`** plus **`CASE_FIELD_RE`** — a *different declaration*. The
symbol the citation is about, `CASE_FIELDS = ("question",)`, is at `:208`, with its rationale comment at
`:206`–`:207`; `SAFE_KEYS` opens at `:203`. So the citations had not merely drifted *within* one
construct — they pointed at a different construct, which the standing rule says to **fix**. UFIX24
fixed them; that was correct, and the earlier "adjacent within the same construct, record it" reading
was mistaken.

## 3. The three requested checks

**(a) PUBLISH pointers outside the authored-by-the-build fence — PASS.** The fence runs
`PUBLISH_PACKAGE_MANIFEST.md:333`–`:340`; the MIT line is `:335`, *inside* it and left untouched. All
three new UFIX24 pointers sit after the closing fence at **`:342`, `:448`, `:472`** — outside. No
quoted listing was corrupted.

**(b) No other file asserts MIT / 5,662 B / `25aa637b…` — CONTRADICTED in part.** The *5,662-byte /
`25aa637b…`* figure is now confined to `strategy/PUBLISH_PACKAGE_MANIFEST.md:441,442,445,451`, all
covered by the dated pointer at `:448`. **But MIT is still asserted as current, with no dated pointer,
in:**
- `strategy/VERIFICATION_REPORT_11.md:152` — "The root LICENSE is MIT with `<YEAR> <COPYRIGHT HOLDER>` placeholders"
- `strategy/VERIFICATION_REPORT_11.md:178` — table row "shipped `LICENSE` (`sha256 f2eb46b6…`) | **MIT License**"
- `strategy/VERIFICATION_REPORT_11.md:307` — "9. LICENSE MIT, no PolyForm | reproduced"
- `orchestration/units/UCURATE1.md:128`–`:129` — "The root `LICENSE` is a **root-level MIT** file authored by … (build-script lines 524–545)"

That report's dated pointers are at `:26, :200, :237, :242, :259, :277, :290` — none covers the MIT
block. `UCURATE1.md`'s five pointers (`:73, :112, :149, :161, :170`) likewise miss `:128`. Separately,
the **stale emitted tree** `.ucurate1/pre/research-publish-packages/` still ships MIT: `LICENSE` first
line is `MIT License`, `README.md:53` declares code **MIT**, `packages/…/README.md:97` likewise, and
there are **0** PolyForm files; mtime `2026-10-15 18:57` — i.e. built *before* ULICENCE3. It is
regenerable by re-running the build, but as it sits on disk it is a live MIT assertion.

**(c) Residual `grep -n '204-205\|204–206'` over the five files — NOT REPRODUCED.** I ran it, but its
output was destroyed inside the same command by unrelated pollution: a recursive grep matched a
vendored minified HTML blob in the workspace and consumed the output budget. No clean literal was
captured, so I do not claim a pass. Corroborating (not equivalent): the two files that *carried* those
strings — `strategy/REGEN_ASSESSMENT.md:126,263` and `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md:350,424`
— now read `:206`–`:207` and `:208`.

## 4. The "Zero further stale citations in this file." claim — CONTRADICTED as stated

The sentence the brief says UFIX24 wrote "for each" of the five files occurs **0 times in all five**.
It occurs **5 times in `orchestration/units/UFIX24.md:58, 75, 90, 111, 125`** — once per file, in
UFIX24's own card. The benign reading is that UFIX24 recorded the per-file sweep result in its card
rather than in the files (which is the normal convention, and writing it *into* a document would be
odd); the literal reading of the claim is false. I record it as **overstated**, not fabricated.

## 5. Citation census — my raw counts versus UFIX24's

UFIX24 reported 14 / 9 / 9 / 15 / 7 (and "17 edits"; the reported action counts 3+4+3+4+2 sum to
**16**, a small internal inconsistency). My mechanical census of colon-number tokens is a different
unit and is not like-for-like:

| file | UFIX24 | my `:N` tokens | my range tokens |
|---|---|---|---|
| `orchestration/units/UCURATE1.md` | 14 | 44 | 48 |
| `orchestration/units/UVER11.md` | 9 | 51 | 51 |
| `strategy/PUBLISH_PACKAGE_MANIFEST.md` | 9 | 86 | 89 |
| `strategy/REGEN_ASSESSMENT.md` | 15 | 94 | 95 |
| `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` | 7 | 773 | 774 |

The gap is explained, not dismissed: my count includes non-citation colon-numbers (timestamps, log
paths). But `CODE_AGNOSTIC_RELEASE_POLICY.md` alone accounts for 773 tokens — its §A.2 identifier
census table (~172 rows, `:212`–`:342`) cites `harness/analyze.py:<line>` once per row. UFIX24's "7"
cannot be a citation count for that file. **I read the whole file but did not open
`harness/analyze.py` at ~172 individual census lines**, so that census is `unverified`, and the
per-file reconciliation is left for the next unit.

## 6. Frozen-record treatment and pointer hygiene

- Pointers present: `UCURATE1.md` 5 (`:73, :112, :149, :161, :170`), `UVER11.md` 6
  (`:34, :45, :61, :70, :78, :92`), `PUBLISH_PACKAGE_MANIFEST.md` 6 (`:8, :260, :342, :415, :448, :472`),
  `REGEN_ASSESSMENT.md` **0**, `CODE_AGNOSTIC_RELEASE_POLICY.md` **0**.
- Zero pointers in REGEN/CODE_AGNOSTIC is *correct*, not an omission: in both, UFIX24 **fixed** live
  citations rather than recording stale ones, and the frozen-record rule governs records of past
  measurements, not live source pointers.
- Spot-check of four frozen records across three files (`UCURATE1.md:73`, `UVER11.md:61`,
  `PUBLISH_PACKAGE_MANIFEST.md:342`, `PUBLISH_PACKAGE_MANIFEST.md:415`): original sentences and
  numbers are intact and the corrections are additive dated notes. No duplication, no disturbance,
  no orphaned pointer found.
- **One pointer that says something now false**: `orchestration/units/UCURATE1.md:128`–`:129` (above).

## 7. RED→GREEN

Checker: `scratch/uver21/check_citations.py` (64 lines, 21 anchored citations across both docs and
both targets — `redact.py` and `UBUILD1.build.sh`). For each citation it asserts the anchor text is
present on the cited target line.

```
$ python3 scratch/uver21/check_citations.py
GREEN  21/21 anchors found   rc=0

$ python3 scratch/uver21/check_citations.py --target-root scratch/uver21/staled
RED    11/21   drifted=10   rc=1
```

The red run's `--target-root` is a symlink farm: `UBUILD1.build.sh` is symlinked to the real file, and
only `repro/encoder-crossover-190-SANITISED/redact.py` is a real copy with two blank lines spliced in
before former `:206`, shifting the rationale to `:208`–`:209` and `CASE_FIELDS` to `:210`. The ten
failures are exactly the citations targeting `:206`, `:207`, `:208` and `:689`. A checker that fails
only where the drift was planted, and passes clean otherwise, is a checker that can fail.

## 8. New stale citations found (reported, not fixed — this is a verification unit)

1. `strategy/VERIFICATION_REPORT_11.md:152`, `:178`, `:307` — root LICENSE asserted MIT; now false; no dated pointer.
2. `orchestration/units/UCURATE1.md:128`–`:129` — root LICENSE asserted MIT at build-script `524`–`545`; now false; no dated pointer.
3. `.ucurate1/pre/research-publish-packages/LICENSE` (and `README.md:53`, `packages/…/README.md:97`) — stale emitted MIT tree, pre-ULICENCE3.
4. Unverified: the ~172 `harness/analyze.py:<line>` rows of the `CODE_AGNOSTIC_RELEASE_POLICY.md` census (`:212`–`:342`).

## 9. Coverage and bound

All five files were opened and read in full, plus `redact.py`, `UBUILD1.build.sh`, and
`strategy/VERIFICATION_REPORT_11.md` (MIT lines). I did not open `harness/analyze.py` line-by-line for
the census rows, and I did not re-run check (c) cleanly. Tool calls: **25 of a 25 bound** — the last
call was the mandated report-back to the parent.
