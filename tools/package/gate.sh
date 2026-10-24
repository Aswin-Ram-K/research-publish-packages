#!/usr/bin/env bash
# =============================================================================
# gate.sh -- the POSITIVE VOCABULARY checker (acceptance test) for a package tree.
#
# Content carried from scratch/ugate1/gate_scoped.sh and the corrected
# scratch/ugate2/gate_scoped_v2.sh (whose own header names it gate.sh -- the path
# scratch/ugate2/gate.sh itself is ABSENT; see tools/package/README.md "Provenance").
#
# This file carries NO denylist.  It carries an allowlist and is a POSITIVE check: a token passes
# only if it is a declared member of THIS tree's own vocabulary.
#
#   * prose and source: strict -- vocabulary/{english,code,public}.txt only;
#   * data files (.json/.jsonl): additionally vocabulary/data.txt, which holds JSON object KEYS
#     only (derived in KEYS MODE ONLY), so free text is never declared and a mechanism name inside
#     a data VALUE still fails;
#   * THE OFFENDER LIST IS COMPLETE (no cap): every counted token is printed with file:line;
#   * the checker NEVER SCANS ITS OWN vocabulary/ directory;
#   * FAIL-CLOSED: a missing or EMPTY vocabulary file -> exit 2 with a FATAL: line.  Never PASS.
#
#   exit 0  every token is a declared member of this tree's own vocabulary
#   exit 1  out-of-vocabulary tokens (every one printed with file:line)
#   exit 2  FAIL-CLOSED -- a required input cannot be read or is empty
#   exit 3  --package could not be resolved
#
# NOT A LEAK DETECTOR: gate.sh counts tokens MISSING FROM A GENERAL ENGLISH WORD LIST.  Its number
# is a vocabulary-coverage count, NOT a confidential-content finding.
# =============================================================================
set -uo pipefail

PKG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --package) PKG="${2:-}"; shift 2 ;;
    --package=*) PKG="${1#*=}"; shift ;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "FATAL: unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$PKG" ]; then
  echo "FATAL: --package is required" >&2
  exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(python3 - "$HERE" "$PKG" <<'RESOLVE'
import os, sys
here, pkg = sys.argv[1], sys.argv[2]
ws = os.path.abspath(os.path.join(here, "..", ".."))
cands = [pkg] if os.path.isabs(pkg) else []
cands += [os.path.join(ws, pkg), os.path.join(ws, "papers", pkg)]
for c in cands:
    if os.path.isdir(c):
        print(os.path.abspath(c))
        sys.exit(0)
sys.stderr.write("FATAL: --package %r is not an existing directory and papers/%s is absent\n" % (pkg, pkg))
sys.exit(3)
RESOLVE
)" || exit $?

exec python3 -u - "$ROOT" "${GATE_JSON:-0}" <<'GATE_PY'
import json
import os
import re
import string
import sys

ROOT = sys.argv[1]
JSON_MODE = len(sys.argv) > 2 and sys.argv[2] == "1"
VOCAB_DIR = os.path.join(ROOT, "vocabulary")
VOCAB_REL = os.path.relpath(VOCAB_DIR, ROOT)
DATA_SUFFIXES = (".json", ".jsonl")


def load(name):
    out = set()
    path = os.path.join(VOCAB_DIR, name)
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for word in line.split():
                    out.add(word)
    except (OSError, ValueError):
        sys.stderr.write("FATAL: cannot read vocabulary file: %s\n" % path)
        sys.exit(2)
    if not out:
        sys.stderr.write("FATAL: vocabulary file has no declared terms: %s\n" % path)
        sys.exit(2)
    return out


ENGLISH = load("english.txt")
CODE = load("code.txt")
DECLARED = load("public.txt")
DATA_WORDS = load("data.txt")

DECLARED_LOWER = set(d.lower() for d in DECLARED)
WORDS = ENGLISH | CODE
DATA_LOWER = set(d.lower() for d in DATA_WORDS)
WORDS_DATA = WORDS | DATA_WORDS

ALNUM = string.ascii_letters + string.digits
DIGITS = string.digits
TOKEN_RE = re.compile("[" + ALNUM + "_.$/@-]+")
EDGE_CHARS = "-_.$/@"
CAMEL_RE = re.compile("[a-z][A-Z]")
SPLIT_RE = re.compile("[^" + ALNUM + "]+")
TAG_RE = re.compile("^(?:K|F|S|C|R|D|N|P)[" + DIGITS + "][" + DIGITS + "]$"
                    "|^TAG_[" + DIGITS + "][" + DIGITS + "]$")
HEX_RE = re.compile("^[" + DIGITS + "abcdef]{8,}$")
DIGIT_RE = re.compile("[" + DIGITS + "]+")
SKIP_DIRS = {".git"}

# Declared generated-id grammars -- patterns, not discovered tokens. Every one
# of them REQUIRES digits, so no mechanism word can match them.
ID_GRAMMARS = [
    re.compile(r"^fam(?:a|b|r)[" + DIGITS + "]{3,6}$"),
    re.compile(r"^ex1[12](?:a|b)[" + DIGITS + "]{3,6}$"),
    re.compile(r"^[^\W\d_][" + DIGITS + "]{2,4}-[" + DIGITS + "]{3}$"),
    re.compile(r"^(?:N|K|F|S)(?:[A-Z])?[" + DIGITS + "]{2,4}$"),
]


def classify(tok, is_data):
    tok = tok.strip(EDGE_CHARS)
    if not tok:
        return ""
    low = tok.lower()
    if TAG_RE.match(tok) or tok in DECLARED or low in DECLARED_LOWER or HEX_RE.match(tok):
        return ""
    for g in ID_GRAMMARS:
        if g.match(tok):
            return ""
    if is_data and (tok in DATA_WORDS or low in DATA_LOWER):
        return ""
    words = WORDS_DATA if is_data else WORDS
    if CAMEL_RE.search(tok):
        return "identifier-shaped, not a declared public identifier"
    for chunk in SPLIT_RE.split(low):
        for word in DIGIT_RE.split(chunk):
            if not word or len(word) == 1:
                continue
            if word not in words:
                return "word not in the declared vocabulary"
    return ""


print("=" * 70)
print("SCOPED POSITIVE VOCABULARY CHECK -- " + ROOT)
print("rule: every token must be a declared member of this tree's own vocabulary")
print("      prose/source: english+code+public (strict, unchanged)")
print("      data (.json/.jsonl): + vocabulary/data.txt (declared JSON keys)")
print("      vocabulary/ is not scanned; the offender list is complete")
print("=" * 70)

flagged = 0
printed = 0
by_class = {}
by_file = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in sorted(filenames):
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, ROOT)
        if rel.split(os.sep)[0] == VOCAB_REL:
            continue        # never scan the checker's own vocabulary inputs
        is_data = rel.endswith(DATA_SUFFIXES)
        kind = "data" if is_data else "prose-source"
        try:
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    for match in TOKEN_RE.finditer(line):
                        tok = match.group(0)
                        why = classify(tok, is_data)
                        if why:
                            flagged = flagged + 1
                            by_class[kind] = by_class.get(kind, 0) + 1
                            by_file[rel] = by_file.get(rel, 0) + 1
                            printed = printed + 1
                            print("%s:%d: %s  [%s]" % (rel, number, tok, why))
        except (OSError, ValueError):
            continue

print("")
print("flagged tokens: %d" % flagged)
print("out-of-vocabulary token lines shown: %d" % printed)
if JSON_MODE:
    print(json.dumps({"flagged": flagged, "printed": printed,
                      "by_class": by_class, "by_file": by_file}))
if flagged:
    print("GATE RESULT: FAIL -- %d out-of-vocabulary token(s)." % flagged)
    print("Do NOT hand-edit shipped evidence to make this pass; report and let the author decide.")
    sys.exit(1)
print("GATE RESULT: PASS -- every token is a declared member of this tree's own vocabulary.")
GATE_PY
