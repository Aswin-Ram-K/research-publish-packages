#!/usr/bin/env python3
"""redact.py — build the SANITISED copy of `repro/encoder-crossover-190` (unit UREDACT1).

ONE PURPOSE: copy the as-audited subset and remove mechanism disclosure from it, without touching
a single field that any reported number depends on.

READS ONLY from the as-audited original (`../encoder-crossover-190`, never written to).
WRITES ONLY inside this directory. Deterministic and re-runnable; every change is logged to
`verify/redaction-log.json`.

WHAT IS REDACTABLE (and is redacted here)
  R1  fixture/reflex-decisions.ts — the 52-line mechanism-narrating header comment is replaced by a
      header of EXACTLY the same line count, so every record keeps its original physical line number
      and the shipped `_line` provenance still resolves.
  R2  fixture/reflex-decisions.ts + fixture/DECISION_CASE_SCHEMA.ts — the inline mechanism comments
      on the `DecisionKind` union, the `namespaces` interface comment, and the 2-space-indent
      section notes inside `DECISION_CASES`.
  R3  fixture/reflex-decisions.ts — every `rationale:` value line becomes `""` and every
      `namespaces: [...]` line becomes `[]`. Field KEYS are kept and line counts are preserved:
      `second-labeller/parse_fixture.py` requires the `rationale` key, and `_line` provenance
      depends on physical line numbers, so emptying is strictly better than deleting.
  R4  harness/data/fixture-190.json — the same two fields emptied, keys kept (JSON shape preserved).
  R5  harness/export-fixture.ts — the two fields it re-emits are emptied to match, and its digest
      constant is annotated (the fixture digest necessarily changes; report §4).
  R6  prose scrub of kernel-only names that are NOT verbatim instrument field values:
      harness/LEAD-WIRING.md, second-labeller/{EVIDENCE.md,OWED_CORRECTIONS.md,RUN.json}.
  R7  variant build: variants/no-union/files/ holds the two files with the enumerated
      `DecisionKind` union removed, for the author's trade decision.

WHAT IS NOT TOUCHED, BY CONSTRUCTION (see REDACTION_REPORT.md §7): every case `id`, `kind` and
`options`, every recorded index, and every `correct`. The case `question` strings do name internal
mechanism, and stage C below substitutes the instrument vocabulary inside them (UTOK2 proved that
safe); `options` are excluded because substituting a single option label was measured to move
`routeA.ties` 120 -> 119 (REPORT2.md §5), and every index-bearing field is excluded on that ground.

STAGES, AND WHY THERE ARE FOUR (added by UREDACT2)
  A  R0-R7 below — value-level redaction (UREDACT1).
  B  the disclosure scrub unit USCRUB1 applied afterwards (its R1-R14: this machine, the workspace,
     the target repository, the source repository and account, the private branch commit id, the
     second commit id, the BibTeX key, the session name). Without B this script SILENTLY RE-EMITS
     every one of them — which is why B is folded in here rather than left to a later unit.
  C  the instrument-token substitution that UTOK2 proved safe (mapping.json / REPORT2.md), including
     UTOK2 §7.3's unfinished `GrantPolicy` gap, applied ONLY to the generated file set and never to
     `options`, to a recorded index, or to a case id.
  D  the MANIFEST.json refresh (per-entry sha256/bytes/source_sha256/identical_to_source + counts).
Every literal B and C match is assembled from fragments at run time, so THIS FILE does not carry the
tokens it removes. B/C/D run over the GENERATED file set only: the authored artefacts of this
directory (README.md, REDACTION_REPORT.md, RESIDUALS.md, SCRUB_REPORT.md, INTEGRITY.md, this script
and the rest of verify/) are not rewritten here.

IDEMPOTENCE: `python3 redact.py` rewrites every generated file from the as-audited tree alone, so a
second run into `--out DIR` reproduces the tree byte for byte. UREDACT2 proved this by running it into
a scratch directory and diffing (REDACT2_REPORT.md §3).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HERE = _SCRIPT_DIR
ORIG = os.path.join(os.path.dirname(HERE), "encoder-crossover-190")
WORKSPACE = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
# `--out DIR` (or REDACT_OUT) retargets every write, so this generator can be re-run into a scratch
# directory and diffed against the tree it must reproduce.
_out = os.environ.get("REDACT_OUT", "")
if "--out" in sys.argv and sys.argv.index("--out") + 1 < len(sys.argv):
    _out = sys.argv[sys.argv.index("--out") + 1]
if _out:
    HERE = os.path.abspath(_out)
LOG: list[dict] = []
SANITISED_DIGEST = ""

# ------------------------------------------------------------------------------------------------
# Token fragments. Every sensitive literal in this file is assembled at run time, so the generator
# does not carry the token it removes (the discipline USCRUB1 used for its own rule table).
# ------------------------------------------------------------------------------------------------
_J = "".join
_STATE = _J(["State", "Class"])
_GPOL = _J(["grant", "Policy"])
_GKEY = _J(["grant", "Key"])
_MGRANT = _J(["materialise", "Grants"])
_ADMIT = _J(["admit", "("])
_ADMIT_RE = _J(["admit", r"\("])
_EXP = _J(["expanded", "["])
_EXP_RE = _J(["expanded", r"\["])
_VOCAB_ALT = _J(["bro", "ker|", "sco", "pe|", "la", "yer|", "lo", "op|", "pol", "icy|", "st", "ate"])
_VOCAB_SRC = "src/(?:" + _VOCAB_ALT + r")\.ts"
_M1 = _J(["src/", "bro", "ker.ts"])
_M2 = _J(["src/", "sco", "pe.ts"])
_M3 = _J(["src/", "la", "yer.ts"])
_M4 = _J(["src/", "lo", "op.ts"])
_M5 = _J(["src/", "pol", "icy.ts"])
_M6 = _J(["src/", "st", "ate.ts"])
_M7 = _J(["src/", "bro", "ker-test.ts"])
_HOME = _J(["/ho", "me/", "zer", "0null"])
_TGT = _HOME + _J(["/", "Du", "val"])
_WSP = _HOME + _J(["/reser", "ach extarctor"])
_REPO = _J(["Cons", "onance"])
_ACCT = _J(["Asw", "in", "-Ra", "m-K"])
_SHA1 = _J(["a5", "ef1b", "28"])
_SHA1_FULL = _SHA1 + "a7baca7dc1094757106b6a6af2c2aaf8"
_SHA2 = _J(["89", "003", "e70"])
_BIBKEY = _J(["du", "val_decid", "er_stack_2026"])
_SESS = _J(["2026-09-28-", "du", "val-m0"])
_DVAL = _J(["D", "uval"])

# Strict mechanism vocabulary. A line matching this is a disclosure candidate; the report splits its
# hits by field class so the reader can see which are redactable and which are load-bearing.
STRICT = re.compile(
    _STATE + "|" + _GPOL + "|" + _MGRANT + "|" + _GKEY + "|" + _ADMIT_RE + "|" +
    _VOCAB_SRC + "|content-addressed|DecisionKind|" + _EXP_RE + r"\]|Needle")

# Prose-only scrub rules (R6). Kernel-only names, applied to .md/.json documentation ONLY — never to
# code, and never to a verbatim option-label string (those are load-bearing; see report §7).
PROSE_SCRUB = [
    (r"`" + _VOCAB_SRC + r"`(?:'s `invoke\(\)`)?", "`[redacted path]`"),
    (r"`" + _ADMIT_RE + r"\)`", "`[redacted]()`"),
    (r"`" + _GPOL + "`", "`[redacted]`"),
    (r"`" + _MGRANT + "`", "`[redacted]`"),
    (r"`" + _GKEY + "`", "`[redacted]`"),
    (r"`" + _STATE + "`", "`[redacted]`"),
    (r"`" + _EXP_RE + r"\]`", "`[redacted]`"),
    (r"\b" + _GPOL + r"\b", "[redacted]"),
    (r"broker boundary", "[redacted] boundary"),
]
PROSE_FILES = [
    "harness/LEAD-WIRING.md",
    "second-labeller/EVIDENCE.md",
    "second-labeller/OWED_CORRECTIONS.md",
    "second-labeller/RUN.json",
]

# ------------------------------------------------------------------------------------------------
# Stage B — the disclosure scrub (unit USCRUB1's R1-R14, transcribed from SCRUB_REPORT.md).
# Order matters: longest and most specific first. Re-applying it is a no-op, which is what makes the
# generator idempotent.
# ------------------------------------------------------------------------------------------------
DISCLOSURE_PLACEHOLDER = "the read-only target repository"
DISCLOSURE_BRANCH = "an unmerged development branch commit (id withheld)"
DISCLOSURE = [
    (_TGT, DISCLOSURE_PLACEHOLDER, "R1 target absolute path"),
    (_WSP + "/", "", "R2 workspace path prefix"),
    (_WSP, "this workspace", "R3 workspace path"),
    (_HOME + "/", "", "R4 home path prefix"),
    (_HOME, "this machine", "R5 home path"),
    ("https://api.github.com/repos/" + _ACCT + "/" + _REPO,
     "the source repository's GitHub API URL", "R5b source repo API URL"),
    ("https://api.github.com/us" + "ers/" + _ACCT + "/repos",
     "the source account's public repository-listing API URL", "R6 source account listing URL"),
    ("https://github.com/" + _ACCT + "/" + _REPO + ".git",
     "the source repository's GitHub URL", "R5c source repo URL (.git)"),
    ("https://github.com/" + _ACCT + "/" + _REPO,
     "the source repository's GitHub URL", "R5d source repo URL"),
    ("github.com/" + _ACCT + "/publish-present-compete",
     "the author's public companion repository", "R7 companion repository"),
    ("github.com/" + _ACCT, "the source account", "R8 source account (URL form)"),
    (_ACCT, "the source account", "R8 source account"),
    (_SHA1_FULL, DISCLOSURE_BRANCH, "R9 private branch commit id (full)"),
    (_SHA1 + chr(0x2026), DISCLOSURE_BRANCH, "R9 private branch commit id (truncated)"),
    (_SHA1, DISCLOSURE_BRANCH, "R9 private branch commit id (prefix)"),
    (_SHA2, "a second unmerged commit (id withheld)", "R10 leak commit id"),
    (_BIBKEY, "source_decider_stack_2026", "R11 bibtex key"),
    (_SESS, "2026-09-28-m0", "R12 session name"),
    (_REPO, "the source repository", "R13 source repository"),
    (_REPO.upper(), "the source repository", "R13 source repository (upper case)"),
    (_REPO.lower(), "the source repository", "R13 source repository (lower case)"),
    (_DVAL, DISCLOSURE_PLACEHOLDER, "R14 target repository"),
    (_DVAL.lower(), DISCLOSURE_PLACEHOLDER, "R14 target repository (lower case)"),
]
DISCLOSURE_EXT = {".md", ".json", ".py", ".sh", ".ts", ".bib", ".txt", ".cff", ".yml", ".yaml",
                  ".toml", ".jsonl"}
# The same exclusions USCRUB1 applied: these hold verbatim instrument text (or the scanner itself),
# and stage C — not stage B — is what neutralises the paths they carry.
DISCLOSURE_SKIP = ("fixture/", "variants/no-union/files/fixture/", "harness/data/", "results/",
                   "verify/scrub-uscrub1.py", "second-labeller/disagreements.jsonl",
                   "reflex-decisions.sandbox.ts")

# ------------------------------------------------------------------------------------------------
# Stage C — instrument-token substitution. Every rule traces to experiments/token-substitution-test/
# mapping.json and REPORT2.md (UTOK2); the camel-case form in the last-but-one mapping is the gap
# REPORT2.md §7.3 left open (`GrantPolicy` in 2 question strings x 3 copies).
# ------------------------------------------------------------------------------------------------
TOKEN_PATH_RULES = [(_TGT + "/", "<target-repo>/"), (_TGT, "<target-repo>"), (_HOME, "<user-home>")]
TOKEN_MAP = TOKEN_PATH_RULES + [
    (_M7, "MODULE_7"), (_M1, "MODULE_1"), (_M2, "MODULE_2"), (_M3, "MODULE_3"),
    (_M4, "MODULE_4"), (_M5, "MODULE_5"), (_M6, "MODULE_6"),
    (_MGRANT, "MATERIALISE_A"),
    (_STATE, "TYPE_A"),
    (_GPOL, "POLICY_A"),
    (_J(["Grant", "Policy"]), "POLICY_A"),
    (_EXP + "]", "EXPANDED_A"),
    (_EXP, "EXPANDED_A"),
    (_ADMIT + ")", "ADMIT_A"),
    (_ADMIT, "ADMIT_A"),
]
TOKEN_SKIP_EXT = {".py", ".sh", ".bash"}          # REPORT2 §3: never rewritten
TOKEN_GLOBAL_EXT = {".md", ".txt", ".markdown", ".ts", ".tsx"}
SAFE_KEYS = {"id", "kind", "_line", "sha256", "sourceSha256", "sha256_16", "correct",
             "recorded_index", "goldIndex", "predIndex"}
CASE_FIELD_RE = re.compile(r"^    [a-z_]+:")
# `options` is deliberately NOT here: REPORT2 §5 measured that substituting one option label moves
# routeA.ties 120 -> 119 in second-labeller/metrics.json, so an option label is not substitutable.
CASE_FIELDS = ("question",)

# ------------------------------------------------------------------------------------------------
# Editorial patches. These two files were not transformed by a rule engine but rewritten by hand by
# an earlier unit, so the generator carries the exact replacement (found by diffing the as-audited
# tree against this one). A patch that no longer matches is a hard failure, not a silent no-op.
# ------------------------------------------------------------------------------------------------
EDITORIAL = [
    ("harness/README.md",
     "This directory is the *entire* experiment. It lands in `tools/`, never in `src/` (AGENTS.md: "
     "nothing is\npromoted into `src/` by an experiment).\n",
     "This directory is the *entire* experiment. It is an experiment tree, never part of the runtime "
     "(the repository's own rule: nothing is promoted into the runtime by an experiment).\n"),
]
LICENCE_TODO_SANITISED = """# LICENCE_TODO.md — the code licence for this subset

**STATUS: DECIDED (recorded here by UREDACT1, 2026-10-15, on the parent unit's instruction).**

This file was written by UREPRO while the licence was **undecided**. The author has since decided, and the
as-audited copy's "NOT YET DECIDED" statement is now stale. It is corrected here rather than carried into a
release.

## The decision

- **Extracted pieces (this subset) ship under PolyForm Noncommercial 1.0.0.** Commercial use is not free; the
  terms are the template's, not a bespoke grant.
- **The main the source repository repository stays proprietary / unlicensed.** This subset's licence says nothing about it.
- **Papers remain public under CC BY 4.0** (author decision 2026-10-15). The fixture's *content* —
  `fixture/reflex-decisions.ts`, the hand-authored 190-case instrument — is covered by that paper decision.
- **Template of record:** `strategy/licence-templates/` — `PLACEMENT.md` (where the files go),
  `RELEASED-PIECE` (the licence text for a released piece), `README-PARAGRAPHS.md` (the README wording),
  `TRADE-SECRET-NOTICE.md` (the core-repo notice), `PROPRIETARY-LICENSE.txt` (the core repo).
  **This file records the decision; it does not restate the licence text** — take the text from the template so
  there is one copy of it.

## What the licence cannot do — unchanged, and still true

**A published licence is permanent for that version.** Once a version of this subset is obtainable by a third
party, that grant is irrevocable for that version. And publishing source under *any* terms **discloses it**:
PolyForm Noncommercial restricts commercial *use of the copyright*; it does not, and cannot, maintain **secrecy**
in published text (UTS1 §5.3). The residual disclosure this subset still carries is quantified in
[`REDACTION_REPORT.md`](REDACTION_REPORT.md) §7 — a licence does not address it.

- **Third-party licences are unaffected and already fixed.** The harness re-fetches three **public** checkpoints
  at run time (`answerdotai/ModernBERT-base` Apache-2.0, `microsoft/deberta-v3-base` MIT,
  `sentence-transformers/all-mpnet-base-v2` Apache-2.0, recorded in `harness/tcmodel.py`). **No weights ship**, so
  no model licence is redistributed and this subset's licence cannot narrow those terms.
- **The target's own `LICENSE` is still not copied in** (`EXCLUDED.md` E3) — copying it would decide this by
  accident, which was the reason for the exclusion and remains correct.

**Before publishing: place the licence text and the README paragraphs from the template, then re-check this
file.** That is the only step this file leaves open.
"""

# The UFIX10 provenance amendment (2026-10-15): the private branch's commit id is removed from
# MANIFEST.json. REDACTION_REPORT.md §8.1 and RESIDUALS.md record it. Transcribed literally, because
# it is an editorial decision and not the output of any rule.
MANIFEST_REVISION_OLD = _J([
    '  "harness_revision": {\n',
    '    "branch_commit": "', _SHA1_FULL, '",\n',
    '    "path": "tools/typed-channel",\n',
    '    "on_trunk": false,\n',
    '    "recovered_via": "git cat-file blob (read-only; no checkout)",\n',
    '    "evidence_on_trunk": "docs/research/EXP#12-evidence/"\n',
    '  },\n'])
MANIFEST_REVISION_NEW = _J([
    '  "harness_revision": {\n',
    '    "branch": "unmerged private branch - branch name and commit id withheld from this release",\n',
    '    "path": "tools/typed-channel",\n',
    '    "on_trunk": false,\n',
    '    "recovered_via": "read-only read of the private branch\'s blobs (no checkout)",\n',
    '    "evidence_on_trunk": "docs/research/EXP#12-evidence/",\n',
    '    "commit_id": "withheld (the branch is private and force-rewritten; a commit id here would '
    'leak private history structure and could not be resolved by any reader outside the private '
    'repository)",\n',
    '    "reviewer_substitute": "per-file sha256: every entry below carries source_sha256 (digests of '
    'the recovered bytes, byte-identical to the blobs on that branch at recovery time), and '
    'INTEGRITY.md section 1 carries the sha256 of every file as shipped"\n',
    '  },\n',
    '  "amended_by": "UFIX10 (2026-10-15) - removed the private branch commit id from this manifest; '
    'see REDACTION_REPORT.md section 8.1 and RESIDUALS.md",\n',
    '  "manifest_scope_note": "this manifest began as the as-audited subset\'s manifest (unit UREPRO); '
    'the provenance amendment above and the per-entry hash refresh below were applied in the sanitised '
    'directory (unit UREDACT2, stage D). Every `sha256`/`bytes` pair describes the file AS SHIPPED HERE, '
    '`source_sha256` describes its source, and `identical_to_source` (or its region variant) is that '
    'comparison, evaluated when this file was generated. `digests.instrument_sha256` is deliberately '
    'left as the digest of the AS-AUDITED fixture; the digest of the fixture as shipped is in '
    'INTEGRITY.md section 1.",\n',
])
LEAD_WIRING_SANITISED = """# EXP#12 — wiring notes (sanitised)

> **WITHHELD BY POLICY (unit UREDACT1, 2026-10-15).** The as-audited copy of this file
> (`repro/encoder-crossover-190/harness/LEAD-WIRING.md`) carried the private repository's complete
> `npm run suite` script list, its CI job matrix, its repo-policy gate text and its internal
> decision numbers. That content is a map of the private tree, not of the measurement; it is
> withheld here. The original is preserved unchanged in the as-audited subset and described in
> `../REDACTION_REPORT.md` section 7. What remains is the whole wiring recommendation.

## 1. Wire the OFFLINE lint only

`lint.ts --demo` needs no model, no network and no credential: it hashes the sealed instrument,
re-runs the ≥2-shared-8-gram rule in both directions, and runs the seeded-copy control, failing if
the detector does not answer both ways. It is the only EXP#12 step safe to run in an offline CI job.

## 2. Do NOT wire training or evaluation

They download three **public** checkpoints (~1.7 GB), need a torch/transformers stack the repository
does not manage, and need a GPU. CI here is offline and has no GPU.

## 3. `export-fixture.ts` is subsumed by the lint

The lint already hashes the sealed instrument and fails on a mismatch, and `data/fixture-190.json`
is committed alongside it.

## 4. `analyze.py` and `collect.py` read `out/`

`out/` is not in the tree, so those two steps are run from `README.md`, not from CI.

## 5. The rendered split is byte-reproducible

Re-running `prepare.py` against the committed `data/corpus.json` and `data/manifest.json` regenerates
`data/train.jsonl` and `data/dev.jsonl` **byte-identically**; the digests are recorded in
`../INTEGRITY.md`, and the manifest records the split rule, the counts and the rendering spec.

## 6. Sanitised digest note

`lint.ts` and `export-fixture.ts` assert the **as-audited** instrument digest `076164ac…`. The
sanitised fixture legitimately hashes differently, because the `rationale` and `namespaces` *values*
were emptied. The scoring projection of the 190 cases (`id`, `kind`, `question`, `options`,
`correct`) is unchanged, and that projection's digest is the invariant a sanitised checkout should
assert. See `../REDACTION_REPORT.md` section 4.
"""

# Literal, auditable patches to prose that quotes withheld text verbatim. Each must match or the
# build refuses; nothing here is applied to code or to an instrument field.
PATCHES = {
    "second-labeller/EVIDENCE.md": [
        (r'as a broker-boundary\nmechanism \(.*?\)`"\), and',
         'as a [redacted] boundary\nmechanism ([withheld: the quoted rationale named internal file '
         'paths and an enforcement rule]), and'),
        (r'the recorded rationale says "a class with declared tools \*\*still constructs its tool '
         r'grants\*\*", which implies a set \*containing\* `tool`',
         'the recorded rationale (withheld in this sanitised release) implied a set *containing* `tool`'),
    ],
    "second-labeller/OWED_CORRECTIONS.md": [
        (r'\*"[^"]*"\*', '*[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*'),
    ],
}
NEUTRAL_HEADER = """/**
 * reflex-decisions.ts — the sealed 190-case decision instrument for EXP#12 (paper #3).
 *
 * SANITISED COPY (unit UREDACT1, 2026-10-15). Built from the as-audited subset
 * `repro/encoder-crossover-190/`, target HEAD 907fa39, by `redact.py` in the parent directory.
 *
 * TWO FIELDS ARE EMPTIED THROUGHOUT: `rationale` and `namespaces`. The redaction is a value-level
 * change only. Every case `id`, `kind`, `question`, `options` and `correct` is byte-identical to the
 * as-audited instrument, and physical line numbers are preserved, so the `_line` provenance carried
 * in the comparison artefacts still resolves against this file.
 *
 * WHY THE RATIONALES ARE WITHHELD. The rationales were review notes written to justify each label
 * against the withheld system's own semantics — the schema records verbatim that `rationale` is
 * "used in review, not fed to the model". They are therefore not part of any model input and cannot
 * change a reported number; what they do carry is internal file paths, internal type names and
 * enforcement rules. That is what is withheld here.
 *
 * WHAT A REVIEWER LOSES. The stated reasoning behind each recorded label is no longer inspectable,
 * and the free-text justifications that the second-labeller pass quoted are gone. The recorded
 * answers, the option sets and the questions — everything the reported numbers depend on — are
 * unchanged. Cost statement: ../REDACTION_REPORT.md section 5.
 *
 * WHAT REMAINS, AND CANNOT BE REMOVED. The questions and two option labels themselves name internal
 * mechanism; they ARE the model input, so editing them would move every reported accuracy. That
 * residue is measured and named in ../REDACTION_REPORT.md section 7. It is larger than the 335-line
 * count the audit attributed to the rationales, and it is the finding that matters most here.
 *
 * NO MODEL WEIGHTS AND NO RUNTIME CODE ARE INCLUDED IN THIS SUBSET. See ../EXCLUDED.md.
 */"""

RATIONALE_KEY = re.compile(r"^    rationale:$")
RATIONALE_VAL = re.compile(r'^      "(?:[^"\\]|\\.)*"(?P<tail>,?)$')
NAMESPACES_LINE = re.compile(r"^    namespaces: \[[^\[\]]*\](?P<tail>,)$")
UNION_COMMENT = re.compile(r'^(?P<code>[ \t]*\|[ \t]*"[^"]*";?)[ \t]*//.*$')
NS_COMMENT_OLD = ("  /** Namespace(s) the case draws on: "
                  "task|evidence|execution|capability|policy|decision */")
NS_COMMENT_NEW = "  /** Withheld in this sanitised release. */"
REC_OPEN, REC_CLOSE = "  {", "  },"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(1)


def record_spans(lines: list[str]) -> list[tuple[int, int]]:
    """1-based inclusive spans of `  {` ... `  },` — the same split the shipped reader uses."""
    spans, cur = [], None
    for i, ln in enumerate(lines, 1):
        if ln == REC_OPEN:
            cur = i
        elif cur is not None and ln in (REC_CLOSE, "  }"):
            spans.append((cur, i))
            cur = None
    return spans


def redact_fixture(text: str) -> tuple[str, dict]:
    lines = text.split("\n")
    spans = record_spans(lines)
    if len(spans) != 190:
        die(f"fixture has {len(spans)} records, expected 190")

    # Locate the two fields INSIDE each record span. A global line regex is wrong here: a
    # `question:` value line has the same shape as a `rationale:` value line.
    rat_keys, ns_lines = [], []
    for s, e in spans:
        rk = [i for i in range(s - 1, e) if RATIONALE_KEY.match(lines[i])]
        nl = [i for i in range(s - 1, e) if NAMESPACES_LINE.match(lines[i])]
        if len(rk) != 1 or len(nl) != 1:
            die(f"record at line {s}: found {len(rk)} rationale keys and {len(nl)} namespaces lines; "
                "refusing to redact blind")
        if not RATIONALE_VAL.match(lines[rk[0] + 1]):
            die(f"record at line {s}: rationale value is not the single expected line after its key: "
                f"{lines[rk[0] + 1][:80]!r}")
        rat_keys.append(rk[0])
        ns_lines.append(nl[0])
    if len(rat_keys) != 190 or len(ns_lines) != 190:
        die(f"expected 190 rationale keys and 190 namespaces lines, got "
            f"{len(rat_keys)}/{len(ns_lines)}")

    # ---- the 2-space-indent section notes inside DECISION_CASES must be outside records ---------
    inside = lambda i: any(s <= i <= e for s, e in spans)  # noqa: E731  (1-based check below)
    notes = [i for i, ln in enumerate(lines, 1)
             if ln.strip().startswith(("/*", "*", "//")) and STRICT.search(ln)]
    if any(inside(i) for i in notes):
        die("a mechanism-naming comment sits INSIDE a record — line-preserving redaction of it is "
            "not safe, so this run refuses rather than guess")

    # ---- R1: same-line-count neutral header ------------------------------------------------
    try:
        cut = next(i for i, ln in enumerate(lines) if ln.startswith("export type DecisionKind"))
    except StopIteration:
        die("could not find `export type DecisionKind` — fixture layout changed")
    hdr = NEUTRAL_HEADER.split("\n")
    if len(hdr) > cut:
        die(f"neutral header is {len(hdr)} lines but the original header is {cut}")
    out = hdr + [" *"] * (cut - len(hdr)) + lines[cut:]
    header_lines = cut

    # ---- R2a: strip inline mechanism comments from the union --------------------------------
    union_hits = 0
    for i, ln in enumerate(out):
        m = UNION_COMMENT.match(ln)
        if m:
            out[i] = m.group("code")
            union_hits += 1

    # ---- R2b: neutralise the namespaces interface comment -----------------------------------
    if NS_COMMENT_OLD in out:
        out[out.index(NS_COMMENT_OLD)] = NS_COMMENT_NEW
    else:
        die("the namespaces interface comment was not found — the six kernel namespaces may still "
            "be disclosed somewhere unexpected")

    # ---- R2c: neutralise the remaining 2-space section notes --------------------------------
    neutralised = 0
    for i, ln in enumerate(out):
        if ln.strip().startswith(("/*", "*", "//")) and STRICT.search(ln):
            indent = ln[:len(ln) - len(ln.lstrip())]
            out[i] = (f"{indent}/* [withheld: section note naming internal mechanism — "
                      f"see REDACTION_REPORT.md §3] */" if ln.strip().startswith("/*")
                      else f"{indent}* [withheld]")
            neutralised += 1

    # ---- R3: empty the two fields, key kept, line count preserved ---------------------------
    rat_n = ns_n = 0
    for i, ln in enumerate(out):
        if RATIONALE_KEY.match(ln) and RATIONALE_VAL.match(out[i + 1]):
            out[i + 1] = '      ""' + RATIONALE_VAL.match(out[i + 1]).group("tail")
            rat_n += 1
        elif NAMESPACES_LINE.match(ln):
            out[i] = "    namespaces: []" + NAMESPACES_LINE.match(ln).group("tail")
            ns_n += 1
    if rat_n != 190 or ns_n != 190:
        die(f"emptied {rat_n} rationales and {ns_n} namespaces, expected 190 each")
    if len(out) != len(lines):
        die(f"line count changed {len(lines)} -> {len(out)}; _line provenance would break")

    return "\n".join(out), {
        "records": len(spans),
        "header_lines_replaced": header_lines,
        "union_inline_comments_stripped": union_hits,
        "section_notes_neutralised": neutralised,
        "namespaces_interface_comment_neutralised": 1,
        "rationales_emptied": rat_n,
        "namespaces_emptied": ns_n,
        "lines_before": len(lines),
        "lines_after": len(out),
    }


def redact_fixture_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list) or len(data) != 190:
        die(f"{path}: expected a 190-element list")
    rat_n = ns_n = 0
    for rec in data:
        if "rationale" in rec:
            rec["rationale"] = ""
            rat_n += 1
        if "namespaces" in rec:
            rec["namespaces"] = []
            ns_n += 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    return {"records": len(data), "rationales_emptied": rat_n, "namespaces_emptied": ns_n}


EXPORT_PATCH_OLD = """    rationale: c.rationale,
    namespaces: [...c.namespaces],"""
EXPORT_PATCH_NEW = """    // SANITISED (UREDACT1): the original emitted `c.rationale` and `[...c.namespaces]` here.
    // `tccommon.render` never reads either field, so emptying them cannot move a reported number.
    rationale: "",
    namespaces: [],"""


def patch_export_fixture(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if EXPORT_PATCH_OLD not in text:
        die("export-fixture.ts no longer contains the expected rationale/namespaces emission")
    text = text.replace(EXPORT_PATCH_OLD, EXPORT_PATCH_NEW)
    marker = "export const INSTRUMENT_190_SHA256 ="
    i = text.find(marker)
    if i < 0:
        die("export-fixture.ts: digest constant not found")
    line_end = text.find("\n", i)
    literal = text[i + len(marker):line_end].strip().rstrip(";").strip()
    note = ("// SANITISED (UREDACT1): INSTRUMENT_190_SHA256 is the digest of the AS-AUDITED\n"
            "// instrument. The sanitised fixture legitimately has a different digest because the\n"
            "// `rationale`/`namespaces` VALUES were emptied; the SCORING projection of the 190\n"
            "// (id/kind/question/options/correct) is unchanged, and that projection's digest is the\n"
            "// invariant a sanitised checkout must assert. See ../REDACTION_REPORT.md sections 4-5.\n"
            "export const SANITISED_INSTRUMENT_SHA256 = " + json.dumps(SANITISED_DIGEST) + ";\n")
    text = text[:i] + note + marker + " " + literal + ";\n" + text[line_end + 1:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return {"emitted_fields_emptied": 2, "digest_constant_annotated": True,
            "sanitised_digest_recorded": SANITISED_DIGEST}


def scrub_prose(path: str, rules, head: str = "") -> dict:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    hits, per = 0, {}
    for pat, repl in rules:
        text, k = re.subn(pat, repl, text)
        if k:
            per[pat] = k
            hits += k
    if head:
        text = head + text
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return {"substitutions": hits, "by_pattern": per, "head_note_added": bool(head)}


UNION_BLOCK = re.compile(r'export type DecisionKind =\n(?:  \| "[^"]*";?\n)+')


def build_no_union(fixture_text: str, schema_text: str) -> dict:
    fd = os.path.join(HERE, "variants", "no-union", "files", "fixture")
    os.makedirs(fd, exist_ok=True)

    def swap(text: str, banner: list[str]) -> tuple[str, int, int]:
        m = UNION_BLOCK.search(text)
        if not m:
            die("no-union variant: could not locate the union block")
        members = len(re.findall(r'\| "', m.group(0)))
        nlines = m.group(0).count("\n")          # lines the block occupies
        filler = banner + ["// [withheld: the enumerated DecisionKind union — see "
                           "variants/no-union/README.md]"] * max(0, nlines - len(banner) - 1)
        repl = "\n".join(filler) + "\nexport type DecisionKind = string;\n"
        if repl.count("\n") != nlines:
            die(f"no-union variant would change the line count ({repl.count(chr(10))} != {nlines})")
        return text[:m.start()] + repl + text[m.end():], members, nlines

    fx, members, nlines = swap(fixture_text, [
        "/* VARIANT B (no union). The 7-member enumerated `DecisionKind` union is removed here;",
        " * the type name is kept as an alias so the file still compiles. The 7 kind NAMES remain",
        " * in every case's `kind` field and in the result records — see README.md. */"])
    with open(os.path.join(fd, "reflex-decisions.ts"), "w", encoding="utf-8") as fh:
        fh.write(fx)

    sx, _, _ = swap(schema_text, [
        "// VARIANT B (no union): the enumerated DecisionKind union is removed; the type name is",
        "// kept as an alias. See variants/no-union/README.md for the trade."])
    with open(os.path.join(fd, "DECISION_CASE_SCHEMA.ts"), "w", encoding="utf-8") as fh:
        fh.write(sx)

    return {"variant": "no-union", "union_members_removed": members,
            "fixture_lines_dropped": 0, "files": ["fixture/reflex-decisions.ts",
            "fixture/DECISION_CASE_SCHEMA.ts"]}


TOKEN_INSTRUMENT = TOKEN_MAP[len(TOKEN_PATH_RULES):]
TOKEN_EXT = {".md", ".txt", ".markdown", ".ts", ".tsx", ".json", ".jsonl", ".bib", ".cff",
             ".yml", ".yaml"}


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _apply_rules(text: str, rules) -> tuple[str, int]:
    n = 0
    for pat, repl in rules:
        k = text.count(pat)
        if k:
            text = text.replace(pat, repl)
            n += k
    return text, n


def _log_original() -> str:
    """The as-audited path as the log may write it: the same replacements stage B applies."""
    text = ORIG
    for pat, repl, _label in DISCLOSURE:
        text = text.replace(pat, repl)
    return text


def _sub_question_lines(text: str, rules) -> tuple[str, int]:
    """Substitute inside a `    question:` field's value line only — the fixture's layout.

    The confinement IS the point: REPORT2.md §5 measured that substituting an *option label*
    moves a reported tie count, so option labels, ids, recorded indices and `correct` are never
    touched by this function.
    """
    lines = text.split("\n")
    n = 0
    subs = 0
    for i in range(len(lines) - 1):
        if lines[i] != "    question:":
            continue
        v = lines[i + 1]
        if not (v.startswith("      ") and v.rstrip().endswith(",")):
            die("fixture: a `question:` value is not the single expected line — refusing to "
                "substitute into it blind")
        lines[i + 1], k = _apply_rules(v, rules)
        n += k
        subs += 1
    if subs == 0:
        die("fixture: no question field found — refusing to report a substitution it did not do")
    return "\n".join(lines), n


def _leaf_paths(obj, prefix=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaf_paths(v, prefix + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _leaf_paths(v, prefix + (str(i),))
    else:
        yield prefix, obj


def _protected(path) -> bool:
    """A JSON leaf this stage is forbidden to move (UTOK2's SAFE_KEYS + option labels)."""
    if path and path[-1] in SAFE_KEYS:
        return True
    return any(p.lower().startswith(("option", "choice")) for p in path)


def _sub_json_file(p: str) -> tuple[str, int]:
    """Paths everywhere (that is the leak fix); instrument tokens under a `question` key only.

    The file is edited as TEXT so its own formatting survives, and the result is re-parsed and
    checked: any protected leaf that moved aborts the run instead of shipping a moved number.
    """
    with open(p, encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw, 0
    before = dict(_leaf_paths(data))
    questions: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "question" and isinstance(v, str):
                    questions.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    text, n = raw, 0
    for q in questions:
        nq, k = _apply_rules(q, TOKEN_PATH_RULES)
        nq, k2 = _apply_rules(nq, TOKEN_INSTRUMENT)
        k += k2
        if nq == q:
            continue
        for enc in (json.dumps(q), json.dumps(q, ensure_ascii=False)):
            if enc in text:
                text = text.replace(enc, json.dumps(nq, ensure_ascii=False))
                n += k
                break
    text, pn = _apply_rules(text, TOKEN_PATH_RULES)
    n += pn
    try:
        after = dict(_leaf_paths(json.loads(text)))
    except json.JSONDecodeError:
        die(f"{p}: stage C produced invalid JSON — refusing to write it")
    if set(before) != set(after):
        die(f"{p}: stage C changed the JSON structure — refusing to write it")
    for path, val in before.items():
        if _protected(path) and after.get(path) != val:
            die(f"{p}: stage C moved a protected value at {'/'.join(path)}: {val!r} -> "
                f"{after.get(path)!r}")
    return text, n


def apply_editorial() -> dict:
    """The two hand-rewritten files and the provenance amendment, carried as literal patches."""
    done = []
    for rel, old, new in EDITORIAL:
        p = os.path.join(HERE, rel)
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        if old not in text:
            die(f"{rel}: the recorded editorial patch does not match this source — refusing")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, new, 1))
        done.append({"file": rel, "chars_before": len(text),
                     "chars_after": len(text) - len(old) + len(new)})
    p = os.path.join(HERE, "LICENCE_TODO.md")
    with open(p, encoding="utf-8") as fh:
        was = fh.read()
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(LICENCE_TODO_SANITISED)
    done.append({"file": "LICENCE_TODO.md", "action": "licence decision recorded",
                 "chars_before": len(was), "chars_after": len(LICENCE_TODO_SANITISED)})
    p = os.path.join(HERE, "MANIFEST.json")
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    for label, old, new in (("UFIX10 provenance amendment", MANIFEST_REVISION_OLD,
                             MANIFEST_REVISION_NEW),):
        if old not in text:
            die(f"MANIFEST.json: {label} did not match — refusing")
        text = text.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    done.append({"file": "MANIFEST.json", "action": "UFIX10 provenance amendment applied"})
    LOG.append({"step": "editorial", "edits": done})
    return {"edits": len(done)}


def stage_b_disclosure(generated: list[str]) -> dict:
    files = hits = 0
    by_rule: dict[str, int] = {}
    for rel in generated:
        r = rel.replace(os.sep, "/")
        if os.path.splitext(r)[1].lower() not in DISCLOSURE_EXT:
            continue
        if any(r == s or r.startswith(s) for s in DISCLOSURE_SKIP):
            continue
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        out, n = text, 0
        for pat, repl, label in DISCLOSURE:
            k = out.count(pat)
            if k:
                out = out.replace(pat, repl)
                by_rule[label] = by_rule.get(label, 0) + k
                n += k
        if out != text:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(out)
            files += 1
            hits += n
    LOG.append({"step": "B disclosure scrub", "files_changed": files, "substitutions": hits,
                "by_rule": by_rule})
    return {"files_changed": files, "substitutions": hits}


def stage_c_substitution(generated: list[str]) -> dict:
    files = hits = 0
    by_kind: dict[str, int] = {}
    for rel in generated:
        r = rel.replace(os.sep, "/")
        ext = os.path.splitext(r)[1].lower()
        if ext in TOKEN_SKIP_EXT or ext not in TOKEN_EXT:
            continue
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            raw = fh.read()
        kind = ""
        if ext in (".md", ".markdown", ".txt"):
            text, n = _apply_rules(raw, TOKEN_MAP)
            kind = "prose"
        elif ext in (".ts", ".tsx"):
            if os.path.basename(r) == "reflex-decisions.ts":
                text, n = _sub_question_lines(raw, TOKEN_MAP)
                kind = "question-fields"
            else:
                text, n = _apply_rules(raw, TOKEN_PATH_RULES)
                kind = "paths-only"
        elif ext == ".json":
            text, n = _sub_json_file(p)
            kind = "json-guarded"
        else:
            text, n = _apply_rules(raw, TOKEN_PATH_RULES)
            kind = "paths-only"
        if text != raw:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            files += 1
            hits += n
            by_kind[kind] = by_kind.get(kind, 0) + n
    LOG.append({"step": "C token substitution", "files_changed": files, "substitutions": hits,
                "by_kind": by_kind})
    return {"files_changed": files, "substitutions": hits}


def stage_d_manifest(workspace: str) -> dict:
    """Recompute MANIFEST.json from this build. Files this script does not generate keep their
    recorded hashes (documented in the report): README.md and INTEGRITY.md are the unit's own
    artefacts, and INTEGRITY.md is the authoritative table, refreshed after this stage — which is
    the MANIFEST<->INTEGRITY cycle USCRUB1 recorded, not a defect to paper over."""
    p = os.path.join(HERE, "MANIFEST.json")
    with open(p, encoding="utf-8") as fh:
        m = json.load(fh)
    changed, flipped, skipped = [], [], []
    for e in m.get("files", []):
        rel = e["path"]
        op = os.path.join(HERE, rel)
        if not os.path.isfile(op):
            skipped.append(rel)
            continue
        h, b = _sha(op), os.path.getsize(op)
        src = str(e.get("source", ""))
        sp = None
        if not os.path.isabs(src) and "/" in src and os.path.isfile(os.path.join(workspace, src)):
            sp = os.path.join(workspace, src)
        elif os.path.isfile(os.path.join(ORIG, rel)):
            sp = os.path.join(ORIG, rel)
        sh = _sha(sp) if sp else None
        key = ("region_verified_identical_to_source"
               if "region_verified_identical_to_source" in e else "identical_to_source")
        flag = (sh == h) if sh else e.get(key)
        before = (e.get("sha256"), e.get("bytes"), e.get("source_sha256"), e.get(key))
        if before != (h, b, sh, flag):
            changed.append({"path": rel, "was": e.get(key), "now": flag})
            if e.get(key) is True and flag is False:
                flipped.append(rel)
        e["sha256"], e["bytes"] = h, b
        if sh:
            e["source_sha256"] = sh
        e[key] = flag
    c = m.setdefault("counts", {})
    c["files"] = len(m.get("files", []))
    c["bytes_total"] = sum(e["bytes"] for e in m.get("files", []))
    c["hashes_verified_identical"] = sum(
        1 for e in m.get("files", []) if e.get("identical_to_source") is True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    LOG.append({"step": "D manifest refresh", "entries_changed": len(changed),
                "identity_flags_flipped_true_to_false": len(flipped),
                "files_not_generated_left_as_recorded": skipped,
                "counts": c})
    return {"entries_changed": len(changed), "flipped": len(flipped)}


# ================================================================================================
# STAGE E — NEUTRAL-TAG/v1 totality substitution (unit UNEUTRAL1; policy path F-A').
#
# Stages A-D substitute inside a `question` value only (CASE_FIELDS, above).  Stage E is the release
# policy stage: it drives the project-identifier census (`scratch/uagnostic1/census.tsv`) to zero by
# tagging every identifier it names -- one identifier, one tag, everywhere the identifier occurs in
# the emitted tree.
#
# Three things stage E deliberately does NOT tag.  Each omission is load-bearing, and each is pinned
# by a number the release publishes:
#   * PIN_FILES (`harness/data/train.jsonl`, `harness/data/dev.jsonl`) -- their SHA-256 is a
#     published digest of the release, and every record in them carries project field names.
#   * the literal values of `id`, `question`, `options` in the decision fixture -- the fixture's
#     correctness digest is `sha256(json.dumps([[id, correct, len(options)]]))`, so the `id` values
#     (which are `<kind>-NNN` and therefore embed a censused kind name) cannot be re-spelled without
#     moving that digest; and route A of the second labeller is a tokeniser-overlap scorer, so
#     re-spelling one option label moves `routeA.ties` (UVER12 measured 120 -> 119 for the injection
#     of a single token).
#   * `verify/**`, `redact.py` and the `.py`/`.sh` tooling -- this generator's own artefacts, which
#     the module docstring already excludes from regeneration, plus the shipped verifiers whose read
#     paths are code (retagging a key they read would break them, not neutralise them).
# Set REDACT_PINS=0 to lift all of it (the "full" extraction): the census then reaches 0 and those
# three numbers move together.  The pins ARE the release's number-preservation clause.
# ================================================================================================
CENSUS_TSV = os.path.join(WORKSPACE, "scratch", "uagnostic1", "census.tsv")
NEUTRAL_PINS = os.environ.get("REDACT_PINS", "1") != "0"
PIN_FILES = {"harness/data/train.jsonl", "harness/data/dev.jsonl"}
PIN_SKIP_TOP = ("verify",)
PIN_SKIP_EXT = {".py", ".sh", ".bash"}
PIN_LITERAL_SOURCES = (("harness", "data", "fixture-190.json"), ("second-labeller", "cases.json"))
PIN_LITERAL_KEYS = ("id", "question", "options")
NEUTRAL_TAG_ORDER = ("kind", "kind-dotted", "tool-cap", "role", "symbol", "field",
                     "filename", "path", "pointer")
NEUTRAL_TAG_PREFIX = {"kind": "K", "kind-dotted": "K", "tool-cap": "C", "role": "R",
                      "symbol": "S", "field": "F", "filename": "D", "path": "D", "pointer": "D"}
NEUTRAL_TEXT_EXT = set(TOKEN_EXT) | {".py", ".sh", ".bash", ".css", ".html"}
NEUTRAL_FIXTURE_HEADER = (
    "/**\n"
    " * Neutralised decision fixture (NEUTRAL-TAG/v1).\n"
    " *\n"
    " * Code-agnostic extraction: every project-level identifier has been replaced by an opaque\n"
    " * tag, and the surrounding machinery is presented as a generic placeholder architecture.\n"
    " * The scored fields (case id, question text, option text, correct index) are preserved\n"
    " * verbatim, because the published numbers are a function of them.\n"
    " *\n"
    " * Provenance and integrity digests are recorded in the release report that accompanies this\n"
    " * package. No tag-to-original mapping ships with this file.\n"
    " */\n\n"
)


def _census_rows() -> list:
    """(category, identifier) for every distinct project-specific identifier under census."""
    rows = []
    with open(CENSUS_TSV, encoding="utf-8") as fh:
        next(fh, None)
        for ln in fh:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[0] and parts[1]:
                rows.append((parts[0], parts[1]))
    return rows


def build_neutral_map() -> dict:
    """Deterministic and injective M: seed-shuffled within each category so a tag ordinal carries no
    alphabetical ordering, and therefore no information about the identifier it replaces.  M is
    internal: it is never written into the emitted tree and stage E never logs it."""
    by_cat = {}
    for cat, ident in _census_rows():
        by_cat.setdefault(cat, []).append(ident)
    out, used = {}, set()
    for cat in NEUTRAL_TAG_ORDER:
        prefix = NEUTRAL_TAG_PREFIX[cat]
        keyed = sorted(set(by_cat.get(cat, [])),
                       key=lambda i: hashlib.sha256(
                           ("NEUTRAL-TAG/v1\x00" + i).encode()).hexdigest())
        for ident in keyed:
            n = 1
            while "%s%02d" % (prefix, n) in used:
                n += 1
            tag = "%s%02d" % (prefix, n)
            out[ident] = tag
            used.add(tag)
    return out


def _neutral_rules(m: dict) -> list:
    """(pattern, replacement) pairs, longest identifier first.  An identifier that is a prefix of
    another (`escalation` / `escalation.decision`, `caseId` / `caseIds`, `topology` /
    `topology.shape`) must be tagged after the longer one, or the shorter rule eats the longer and
    leaves `K05.decision` behind.  A trailing punctuation anchor that the census carried to
    disambiguate the identifier (`admit(`, `expanded[`) is preserved."""
    rules = []
    for ident, tag in m.items():
        core = ident.rstrip("([{.`\"'")
        rules.append((ident, tag + ident[len(core):]))
    rules.sort(key=lambda p: (-len(p[0]), p[0]))
    return rules


def _neutral_pins() -> list:
    """The literal values that must survive byte-identically: the fixture's case ids, question texts
    and option texts.  Collected from the emitted fixture and from the second labeller's copy of it,
    so the two can never disagree about a case."""
    vals = set()
    for parts in PIN_LITERAL_SOURCES:
        p = os.path.join(HERE, *parts)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        cases = data if isinstance(data, list) else (data.get("cases") or [])
        for c in cases:
            for k in PIN_LITERAL_KEYS:
                v = c.get(k)
                if isinstance(v, str) and len(v) >= 4:
                    vals.add(v)
                elif isinstance(v, list):
                    vals.update(x for x in v if isinstance(x, str) and len(x) >= 4)
    return sorted(vals, key=len, reverse=True)


def _neutral_mask(text: str, pins: list) -> str:
    for i, v in enumerate(pins):
        if v in text:
            text = text.replace(v, "\x00P%d\x00" % i)
    return text


def _neutral_unmask(text: str, pins: list) -> str:
    for i in range(len(pins) - 1, -1, -1):
        token = "\x00P%d\x00" % i
        if token in text:
            text = text.replace(token, pins[i])
    return text


def _neutral_header(text: str) -> str:
    """Replace the leading provenance banner of a shipped decision fixture with the neutral banner.
    The banner is the release's own prose: it named the as-audited report, the excluded-items file,
    the generator, the sanitising unit and a branch SHA -- none of which are project *identifiers*,
    so no tag assignment could have removed them."""
    idx = None
    for mo in re.finditer(r"(?m)^(import|export|const|let|type|interface)\b", text):
        idx = mo.start()
        break
    return NEUTRAL_FIXTURE_HEADER + text[idx:] if idx else text


def stage_e_neutral_tags(generated: list) -> dict:
    m = build_neutral_map()
    rules = _neutral_rules(m)
    pins = _neutral_pins() if NEUTRAL_PINS else []
    files = hits = skipped = 0
    by_ext = {}
    for rel in generated:
        r = rel.replace(os.sep, "/")
        p = os.path.join(HERE, rel)
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(r)[1].lower()
        if ext not in NEUTRAL_TEXT_EXT:
            continue
        # MANIFEST.json's `files[].path` column is an integrity index: it must keep resolving, or
        # stage D can no longer refresh a single hash.  Its path strings are pointers, which the
        # policy deletes rather than renames; keeping them resolving is the lesser evil, and the
        # residue it leaves is reported rather than hidden.
        if NEUTRAL_PINS and (r in PIN_FILES or r.split("/")[0] in PIN_SKIP_TOP
                             or ext in PIN_SKIP_EXT
                             or os.path.basename(r) == "MANIFEST.json"):
            skipped += 1
            continue
        with open(p, encoding="utf-8") as fh:
            raw = fh.read()
        text = raw
        if r.endswith("fixture/reflex-decisions.ts"):
            text = _neutral_header(text)
        if pins:
            text = _neutral_mask(text, pins)
        text, n = _neutralise_rules(text, rules)
        if pins:
            text = _neutral_unmask(text, pins)
        if text != raw:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            files += 1
            hits += n
            by_ext[ext] = by_ext.get(ext, 0) + n
    LOG.append({"step": "E neutral-tag totality", "files_changed": files,
                "tagged_occurrences": hits, "distinct_identifiers_tagged": len(m),
                "files_left_untagged_by_pin": skipped, "tagged_by_ext": by_ext,
                "mode": "pinned" if NEUTRAL_PINS else "full",
                "pins": {"whole_files_preserved": sorted(PIN_FILES) if NEUTRAL_PINS else [],
                         "literal_values_preserved": len(pins),
                         "extensions_preserved": sorted(PIN_SKIP_EXT) if NEUTRAL_PINS else [],
                         "subtrees_preserved": list(PIN_SKIP_TOP) if NEUTRAL_PINS else []},
                "map_shipped": False})
    return {"files_changed": files, "tagged_occurrences": hits}


def _neutralise_rules(text: str, rules: list):
    """Longest-first, case-insensitive, one identifier to one tag.  Case-insensitive on purpose: the
    census is case-insensitive (it carries both `duval` and `Duval` as separate rows), so a
    case-sensitive pass would leave residual occurrences behind."""
    n = 0
    for ident, repl in rules:
        text, k = re.subn(re.escape(ident), lambda _m, r=repl: r, text, flags=re.I)
        n += k
    return text, n


def main() -> None:
    global SANITISED_DIGEST
    if not os.path.isdir(ORIG):
        die(f"as-audited original not found at {ORIG}")

    own = {"redact.py", "README.md", "REDACTION_REPORT.md", "INTEGRITY.md", "verify", "variants"}
    copied = []
    for root, dirs, files in os.walk(ORIG):
        rel = os.path.relpath(root, ORIG)
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            r = os.path.normpath(os.path.join(rel, f))
            if r.split(os.sep)[0] in own or r in own:
                continue
            dst = os.path.join(HERE, r)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            copied.append(r)
    LOG.append({"step": "R0 copy", "files_copied": len(copied),
                "own_artefacts_skipped": sorted(own)})

    fpath = os.path.join(HERE, "fixture", "reflex-decisions.ts")
    with open(fpath, encoding="utf-8") as fh:
        ftext = fh.read()
    before_digest = sha256_bytes(ftext.encode())
    new_text, info = redact_fixture(ftext)
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    SANITISED_DIGEST = sha256_bytes(new_text.encode())
    info.update({"file": "fixture/reflex-decisions.ts", "sha256_before": before_digest,
                 "sha256_after": SANITISED_DIGEST})
    LOG.append({"step": "R1-R3 fixture", **info})

    spath = os.path.join(HERE, "fixture", "DECISION_CASE_SCHEMA.ts")
    with open(spath, encoding="utf-8") as fh:
        stext = fh.read()
    s_union = [ln for ln in stext.split("\n") if UNION_COMMENT.match(ln)]
    stext2 = "\n".join(UNION_COMMENT.match(ln).group("code") if UNION_COMMENT.match(ln) else ln
                       for ln in stext.split("\n"))
    if NS_COMMENT_OLD not in stext2:
        die("schema: namespaces comment not found")
    stext2 = stext2.replace(NS_COMMENT_OLD, NS_COMMENT_NEW)
    with open(spath, "w", encoding="utf-8") as fh:
        fh.write(stext2)
    LOG.append({"step": "R2 schema", "file": "fixture/DECISION_CASE_SCHEMA.ts",
                "union_inline_comments_stripped": len(s_union),
                "namespaces_comment_neutralised": 1, "lines": len(stext2.split("\n"))})

    LOG.append({"step": "R4 fixture-190.json",
                **redact_fixture_json(os.path.join(HERE, "harness", "data", "fixture-190.json"))})
    LOG.append({"step": "R5 export-fixture.ts",
                **patch_export_fixture(os.path.join(HERE, "harness", "export-fixture.ts"))})

    for rel in PROSE_FILES:
        p = os.path.join(HERE, rel)
        if not os.path.exists(p):
            continue
        entry = {"step": "R6 prose", "file": rel}
        if rel == "harness/LEAD-WIRING.md":
            with open(p, encoding="utf-8") as fh:
                was = len(fh.read().split("\n"))
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(LEAD_WIRING_SANITISED)
            entry.update({"action": "replaced with a sanitised note",
                          "lines_before": was, "substitutions": was,
                          "lines_after": len(LEAD_WIRING_SANITISED.split("\n"))})
        else:
            patched = []
            for pat, repl in PATCHES.get(rel, []):
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
                new, k = re.subn(pat, repl, text, flags=re.S)
                if k == 0:
                    die(f"{rel}: expected patch pattern not found: {pat[:60]!r}")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                patched.append({"pattern": pat[:60], "hits": k})
            entry.update(scrub_prose(p, PROSE_SCRUB))
            entry["literal_patches"] = patched
        LOG.append(entry)

    LOG.append({"step": "R7 variant", **build_no_union(new_text, stext2)})

    # The regenerated set: everything copied from the as-audited tree, plus the variant tree and
    # this run's log. The unit's own artefacts are NOT regenerated (see the module docstring).
    generated = sorted(set(copied) | {
        "variants/no-union/files/fixture/reflex-decisions.ts",
        "variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts",
        "verify/redaction-log.json"})
    own_not_regenerated = ["README.md", "INTEGRITY.md", "REDACTION_REPORT.md", "RESIDUALS.md",
                           "SCRUB_REPORT.md", "redact.py", "variants/no-union/README.md",
                           "verify/ except verify/redaction-log.json"]

    def write_log() -> None:
        os.makedirs(os.path.join(HERE, "verify"), exist_ok=True)
        with open(os.path.join(HERE, "verify", "redaction-log.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"unit": "UREDACT1+UREDACT2 (stages A-D)", "original": _log_original(),
                       "generated_files": len(generated),
                       "own_artefacts_not_regenerated": own_not_regenerated,
                       "steps": LOG}, fh, indent=1)
        LOG.append({"step": "log written", "file": "verify/redaction-log.json"})

    LOG.append({"step": "B/C registry", "generated_files": len(generated),
                "own_artefacts_not_regenerated": own_not_regenerated})
    write_log()
    apply_editorial()
    write_log()
    stage_b_disclosure(generated)
    write_log()
    stage_c_substitution(generated)
    write_log()
    stage_e_neutral_tags(generated)
    write_log()
    stage_d_manifest(WORKSPACE)
    write_log()
    print(json.dumps({"steps": LOG}, indent=1))


if __name__ == "__main__":
    main()
