#!/usr/bin/env python3
"""UTOK2 — extended token substitution: UTOK1's mapping PLUS the residuals UTOK1 deliberately protected.

Usage: python3 substitute2.py <work-tree-root>

SCOPE, stated exactly:

  .md/.txt/.markdown           : literal substitution (both rule groups).
  *.ts/*.tsx                   : literal substitution, EXCEPT fixture/reflex-decisions.ts where it is
                                 confined to the field spans question/options/rationale/namespaces
                                 (UTOK1 confined it to `question` only). id/kind/correct are never touched.
  .json/.jsonl                 : TEXT substitution, guarded by an object-level diff that ABORTS the file
                                 if any string under id/kind/_line/sha256/sourceSha256/sha256_16/
                                 correct/recorded_index/goldIndex/predIndex changed. Text substitution
                                 (not re-serialisation) so the frozen files' formatting and every
                                 untouched byte are preserved exactly.
  .py/.sh/.bash                : NEVER touched. These are instrumentation — redact.py,
                                 verify/run-verification.sh, second-labeller/parse_fixture.py and
                                 verify/recompute-claims.py must stay byte-faithful or the before/after
                                 comparison measures nothing.

EXTENSIONS OVER UTOK1 (each named in REPORT2.md):
  P. path neutralisation   /home/zer0null/Duval/ -> <target-repo>/   (manifest.json paths, .ts headers)
  O. option labels         the fixture span rule now covers options/rationale/namespaces too
  K. JSON dict KEYS        frozen results/*.json key per-option stats by the option-label string, so the
                           key — not just a value — has to move with the label.
  R. frozen results/*.json and every other .json/.jsonl in the tree are in scope (UTOK1 changed only
     question/situation/instructions/rationale value strings).
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1])

MAPPING = [
    ("src/broker-test.ts", "MODULE_7"),
    ("src/broker.ts", "MODULE_1"),
    ("src/scope.ts", "MODULE_2"),
    ("src/layer.ts", "MODULE_3"),
    ("src/loop.ts", "MODULE_4"),
    ("src/policy.ts", "MODULE_5"),
    ("src/state.ts", "MODULE_6"),
    ("materialiseGrants", "MATERIALISE_A"),
    ("StateClass", "TYPE_A"),
    ("grantPolicy", "POLICY_A"),
    ("expanded[]", "EXPANDED_A"),
    ("expanded[", "EXPANDED_A"),
    ("admit()", "ADMIT_A"),
    ("admit(", "ADMIT_A"),
]

PATH_RULES = [
    ("/home/zer0null/Duval/", "<target-repo>/"),
    ("/home/zer0null/Duval", "<target-repo>"),
    ("/home/zer0null", "<user-home>"),
]
RULES = PATH_RULES + MAPPING

SAFE_KEYS = {"id", "kind", "_line", "sha256", "sourceSha256", "sha256_16",
             "correct", "recorded_index", "goldIndex", "predIndex"}
SKIP_EXT = {".py", ".sh", ".bash"}
FIXTURE_TS = os.path.join("fixture", "reflex-decisions.ts")
FIXTURE_FIELDS = ("question", "options", "rationale", "namespaces")
FIELD_RE = re.compile(r"^    [a-z_]+:")

LOG = []
ABORT = []


def sub(text):
    for old, new in RULES:
        text = text.replace(old, new)
    return text


def diff_paths(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            if k in b:
                out += diff_paths(a[k], b[k], path + "/" + str(k))
            else:
                out.append(path + "/" + str(k) + " (KEY-VANISHED)")
        for k in b:
            if k not in a:
                out.append(path + "/" + str(k) + " (KEY-ADDED)")
    elif isinstance(a, list) and isinstance(b, list):
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_paths(x, y, path + "[%d]" % i)
        if len(a) != len(b):
            out.append(path + " (LENGTH-CHANGED)")
    else:
        if a != b:
            out.append(path)
    return out


def guard(rel, ch):
    """Refuse any change whose terminal key is a protected identity/label field."""
    bad = []
    for p in ch:
        leaf = p.split("/")[-1].split(" ")[0].split("[")[0]
        if leaf in SAFE_KEYS:
            bad.append(p)
    if bad:
        ABORT.append((rel, "SAFE-KEY CHANGE: " + ", ".join(bad[:6])))
        return False
    return True


def handle_json(full, raw, rel):
    try:
        before = json.loads(raw)
    except json.JSONDecodeError:
        LOG.append((rel, -1, "unparseable-json"))
        return
    txt = sub(raw)
    if txt == raw:
        return
    try:
        after = json.loads(txt)
    except json.JSONDecodeError:
        ABORT.append((rel, "text substitution broke JSON"))
        return
    ch = diff_paths(before, after)
    if not guard(rel, ch):
        return
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(txt)
    LOG.append((rel, len(ch), "ok"))


def handle_jsonl(full, raw, rel):
    rows, changed, nch = [], False, 0
    for line in raw.split("\n"):
        if not line.strip():
            rows.append(line)
            continue
        try:
            before = json.loads(line)
        except json.JSONDecodeError:
            ABORT.append((rel, "unparseable jsonl line"))
            return
        new = sub(line)
        if new != line:
            try:
                after = json.loads(new)
            except json.JSONDecodeError:
                ABORT.append((rel, "text substitution broke a jsonl line"))
                return
            ch = diff_paths(before, after)
            if not guard(rel, ch):
                return
            nch += len(ch)
            changed = True
        rows.append(new)
    if changed:
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows))
        LOG.append((rel, nch, "ok"))


def do_fixture(full, rel):
    lines = open(full, encoding="utf-8").read().split("\n")
    n, i = 0, 0
    while i < len(lines):
        m = re.match(r"^    ([a-z_]+):", lines[i])
        if m and m.group(1) in FIXTURE_FIELDS:
            end = i
            while end + 1 < len(lines) and not FIELD_RE.match(lines[end + 1]):
                end += 1
            for j in range(i, end + 1):
                new = sub(lines[j])
                if new != lines[j]:
                    n += 1
                lines[j] = new
            i = end + 1
        else:
            i += 1
    if n:
        with open(full, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    LOG.append((rel, n, "fixture-spans"))


def main():
    if not os.path.isdir(ROOT):
        sys.exit("not a directory: " + ROOT)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            rel = os.path.relpath(full, ROOT)
            try:
                raw = open(full, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if rel == FIXTURE_TS:
                do_fixture(full, rel)
            elif ext == ".json":
                handle_json(full, raw, rel)
            elif ext == ".jsonl":
                handle_jsonl(full, raw, rel)
            elif ext in (".md", ".txt", ".markdown", ".ts", ".tsx"):
                new = sub(raw)
                if new != raw:
                    with open(full, "w", encoding="utf-8") as fh:
                        fh.write(new)
                    LOG.append((rel, sum(raw.count(o) for o, _ in RULES), "global"))
    print("== CHANGED FILES ==")
    for rel, n, how in sorted(LOG):
        print("  %-58s %6s  %s" % (rel, n, how))
    print("== files changed: %d ==" % len(LOG))
    if ABORT:
        print("== ABORTS (file left UNCHANGED) ==")
        for rel, why in ABORT:
            print("  %s : %s" % (rel, why))
        print("== aborted files: %d ==" % len(ABORT))


if __name__ == "__main__":
    main()
