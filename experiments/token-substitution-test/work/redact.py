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

WHAT IS NOT TOUCHED, BY CONSTRUCTION (and cannot be — see report §7): every case `id`, `kind`,
`question` and `options`, and every `correct`. The questions themselves name internal mechanism
(StateClass 30x, grantPolicy 19x, private src/ paths 10x). They ARE the model input, so editing them
would change the rendered situation and therefore every reported accuracy. They are a bounded,
irreducible residue — reported, not silently rewritten.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(os.path.dirname(HERE), "encoder-crossover-190")
LOG: list[dict] = []
SANITISED_DIGEST = ""

# Strict mechanism vocabulary. A line matching this is a disclosure candidate; the report splits its
# hits by field class so the reader can see which are redactable and which are load-bearing.
STRICT = re.compile(
    r"StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|"
    r"src/(?:broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|"
    r"expanded\[\]|Needle")

# Prose-only scrub rules (R6). Kernel-only names, applied to .md/.json documentation ONLY — never to
# code, and never to a verbatim option-label string (those are load-bearing; see report §7).
PROSE_SCRUB = [
    (r"`src/(?:broker|scope|layer|loop|policy|state)\.ts`(?:'s `invoke\(\)`)?", "`[redacted path]`"),
    (r"`admit\(\)`", "`[redacted]()`"),
    (r"`grantPolicy`", "`[redacted]`"),
    (r"`materialiseGrants`", "`[redacted]`"),
    (r"`grantKey`", "`[redacted]`"),
    (r"`StateClass`", "`[redacted]`"),
    (r"`expanded\[\]`", "`[redacted]`"),
    (r"\bgrantPolicy\b", "[redacted]"),
    (r"broker boundary", "[redacted] boundary"),
]
PROSE_FILES = [
    "harness/LEAD-WIRING.md",
    "second-labeller/EVIDENCE.md",
    "second-labeller/OWED_CORRECTIONS.md",
    "second-labeller/RUN.json",
]
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

    os.makedirs(os.path.join(HERE, "verify"), exist_ok=True)
    with open(os.path.join(HERE, "verify", "redaction-log.json"), "w", encoding="utf-8") as fh:
        json.dump({"unit": "UREDACT1", "original": ORIG, "steps": LOG}, fh, indent=1)
    print(json.dumps({"steps": LOG}, indent=1))


if __name__ == "__main__":
    main()
