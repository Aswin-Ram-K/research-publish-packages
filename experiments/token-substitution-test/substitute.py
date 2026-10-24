#!/usr/bin/env python3
"""UTOK1 token substitution — apply a documented neutral-vocabulary mapping to a COPY.

Usage: python3 substitute.py <work-tree-root>

SCOPE, stated exactly (see mapping.json):

  IN  (.md/.txt/.markdown)            : global literal substitution of the mapping.
  IN  (*.ts/.tsx)                     : global, EXCEPT fixture/reflex-decisions.ts, where
                                        substitution is confined to `question:` value spans.
  IN  (*.json/.jsonl)                 : string values reached only under the keys in
                                        QUESTION_KEYS (question/situation/instructions/
                                        rationale) — never under option/answer/id keys.
  OUT (*.py/*.sh/*.bash)              : NEVER touched. These are instrumentation: their
                                        pattern lists and parsers must stay byte-faithful,
                                        or the before/after comparison measures nothing.

NEVER changed, by construction: case `id` values, `options` arrays / option label strings,
`correct` / `recorded_index` / `gold` / `predLabel` / any label field, and `_line` provenance.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1])

# Longest-first so `src/broker-test.ts` is not truncated by `src/broker`.
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

QUESTION_KEYS = {"question", "situation", "instructions", "rationale", "recorded_rationale"}
SKIP_EXT = {".py", ".sh", ".bash"}
FIXTURE_TS = os.path.join("fixture", "reflex-decisions.ts")
LOG = []


def sub(text):
    for old, new in MAPPING:
        text = text.replace(old, new)
    return text


def walk_json(obj, path=""):
    """Substitute only under QUESTION_KEYS. Everything else is returned untouched."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and k in QUESTION_KEYS:
                nv = sub(v)
                out[k] = nv
                if nv != v:
                    LOG.append((path + "/" + k, sum(v.count(o) for o, _ in MAPPING)))
            else:
                out[k] = walk_json(v, path + "/" + str(k))
        return out
    if isinstance(obj, list):
        return [walk_json(v, path + f"[{i}]") for i, v in enumerate(obj)]
    return obj


FIELD_RE = re.compile(r"^    [a-z_]+:")


def field_span(lines, start, name):
    """Same span rule as verify/run-verification.sh: a field runs to the next `    key:` line."""
    i = start
    while i + 1 < len(lines) and not FIELD_RE.match(lines[i + 1]):
        i += 1
    return i


def do_fixture(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    n = 0
    for idx, ln in enumerate(lines):
        if ln.startswith("    question:"):
            end = field_span(lines, idx, "question")
            for j in range(idx, end + 1):
                new = sub(lines[j])
                if new != lines[j]:
                    n += 1
                lines[j] = new
    if n:
        open(path, "w", encoding="utf-8").write("\n".join(lines))
    LOG.append((os.path.relpath(path, ROOT), n))


def main():
    if not os.path.isdir(ROOT):
        sys.exit(f"not a directory: {ROOT}")
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
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
                do_fixture(full)
                continue
            if ext == ".json":
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    LOG.append((rel, -1))
                    continue
                new = walk_json(obj)
                if new != obj:  # semantic compare: untouched files are never rewritten
                    open(full, "w", encoding="utf-8").write(
                        json.dumps(new, indent=2, ensure_ascii=False) + "\n")
                    LOG.append((rel, "json-keys-CHANGED"))
                continue
            if ext == ".jsonl":
                rows, changed = [], False
                for line in raw.split("\n"):
                    if not line.strip():
                        rows.append(line)
                        continue
                    o = json.loads(line)
                    n = walk_json(o)
                    changed = changed or (n != o)
                    rows.append(json.dumps(n, ensure_ascii=False))
                if changed:
                    open(full, "w", encoding="utf-8").write("\n".join(rows))
                    LOG.append((rel, "jsonl-keys-CHANGED"))
                continue
            if ext in (".md", ".txt", ".markdown", ".ts", ".tsx"):
                new = sub(raw)
                if new != raw:
                    open(full, "w", encoding="utf-8").write(new)
                    LOG.append((rel, sum(raw.count(o) for o, _ in MAPPING)))
                continue
    for rel, n in sorted(LOG):
        print(f"  {str(n):>10}  {rel}")


if __name__ == "__main__":
    main()
