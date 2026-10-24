#!/usr/bin/env python3
"""neutralise.py -- injective, case-sensitive, longest-first token -> tag rename.

The token -> tag MAP IS HELD IN MEMORY ONLY: it is never written to disk, never printed, never
shipped.  Only aggregate counts are printed (NEUTRAL-TAG/v1, scratch/uneutral9/rename.py).

Schemes
  neutral-tag  fixed ROLES/ENUMS/FRAGS vocabulary -> G01.. (scratch/uneutral9/rename.py)
  bij          kinds discovered from the fixture, ordered by sha256("BIJ/v1\\0" + kind) -> N01..
               (scratch/ubij1/bij_one.py): JSON prose values of question/options/situation are
               MASKED before substitution and restored after, and the masked-prose hit count must
               be identical before and after -- a rename that corrupts surrounding prose is
               REJECTED, not silently applied.

Fidelity guarantees
  * longest-first: a shorter token that is a prefix of a longer one can never split it;
  * case-sensitive: exact tokens only;
  * injective: assert len(set(tags)) == len(tokens);
  * a diagnostic that MOVES under the rename (``--diagnostic CMD``, repeatable) is REPORTED and
    the rename is NOT applied (exit 4).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

ROLES = ["editor", "attached", "reasoner", "detached", "topology", "verifier", "researcher",
         "critic", "broker", "escalation"]
ENUMS = ["ESCALATE", "ANSWER", "DROP", "EPHEMERAL", "EPISODIC", "PROCEDURAL", "PERSISTENT",
         "DISCARD", "RETAIN_REF", "EXPAND", "CONTRADICTION_CHECK", "SINGLE", "PARALLEL",
         "SEQUENCE", "RETURN", "CONTINUE", "AMEND", "GRANT", "REPLAY", "STEP"]
FRAGS = ["expanded[", "admit("]
BIJ_PROSE_KEYS = {"question", "options", "situation", "state", "instructions", "criteria",
                  "constructionRule"}
BIJ_TEXT_EXT = {".json", ".jsonl", ".md", ".txt", ".ts", ".tsx", ".yml", ".yaml", ".bib", ".cff",
                ".css", ".html"}
BIJ_TOOL_EXT = {".py", ".sh", ".bash"}
BIJ_FIXTURES = ["harness/data/fixture-190.json", "harness/data/corpus.json"]
BIJ_LIVE = os.path.join(_pkg.WORKSPACE, "repro", "encoder-crossover-190-SANITISED")
BIJ_SRC = os.path.join(_pkg.WORKSPACE, "scratch", "uneutral3", "tree-stripped")


def load_tokens(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]


def build_map(tokens):
    tokens = sorted(set(tokens), key=lambda t: (-len(t), t))
    mapping = {t: "G%02d" % (i + 1) for i, t in enumerate(tokens)}
    assert len(set(mapping.values())) == len(tokens), "tag map is not injective"
    return tokens, mapping


def digest_commands(cmds, tree):
    """(rc, sha256(stdout), sha256(stderr)) per diagnostic, run with cwd=tree."""
    out = []
    for cmd in cmds:
        r = subprocess.run(cmd, shell=True, cwd=tree, capture_output=True)
        out.append((cmd, r.returncode, hashlib.sha256(r.stdout).hexdigest(),
                    hashlib.sha256(r.stderr).hexdigest()))
    return out


def neutral_tag(tree, tokens):
    mapping = {t: "G%02d" % (i + 1) for i, t in enumerate(tokens)}
    word = {t: re.compile(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])")
            for t in tokens if t not in FRAGS}
    occ = {t: 0 for t in tokens}
    tot, files = 0, 0
    for root, dirs, fs in os.walk(tree):
        dirs.sort()
        for fn in sorted(fs):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, tree).replace(os.sep, "/")
            if rel == "MANIFEST.json":
                continue
            try:
                s = open(p, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            for t in tokens:
                n = len(word[t].findall(s)) if t in word else s.count(t)
                if n:
                    occ[t] += n
                    tot += n
            new = s
            for t in tokens:
                new = word[t].sub(mapping[t], new) if t in word else new.replace(t, mapping[t])
            if new != s:
                open(p, "w", encoding="utf-8").write(new)
                files += 1
    return tokens, tot, files


def discover_kinds(fixture_paths):
    kinds = set()
    for rel, root in fixture_paths:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            d = json.load(fh)
        cases = d if isinstance(d, list) else d["cases"]
        kinds |= {c["kind"] for c in cases}
    return sorted(kinds)


def pinned_strings(fixture_paths):
    out = set()

    def rec(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in BIJ_PROSE_KEYS:
                    if isinstance(v, str):
                        out.add(v)
                    elif isinstance(v, list):
                        out.update(x for x in v if isinstance(x, str))
                else:
                    rec(v)
        elif isinstance(o, list):
            for x in o:
                rec(x)
    for rel, root in fixture_paths:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            rec(json.load(fh))
    return out


class Masker:
    """Two representations per pinned value: JSON dump and the JS-escaped variant."""

    def __init__(self, values):
        reps = set()
        for v in values:
            if not v:
                continue
            d = json.dumps(v, ensure_ascii=False)
            reps.add(d)
            reps.add(d.replace("'", "\\'"))
        self.enc = sorted(reps, key=len, reverse=True)
        self.n = 0

    def mask(self, text):
        self.n = 0
        for i, e in enumerate(self.enc):
            if e and e in text:
                ph = "\ue000M%05d\ue001" % i
                self.n += text.count(e)
                text = text.replace(e, ph)
        return text

    def unmask(self, text):
        for i, e in enumerate(self.enc):
            text = text.replace("\ue000M%05d\ue001" % i, e)
        return text


def bij(dst, live, src, fixture_rels, salt):
    """Faithful port of scratch/ubij1/bij_one.py: kinds pinned from LIVE, prose pinned from SRC,
    SRC copied to dst and walked in place."""
    kinds = discover_kinds([(r, live) for r in fixture_rels])
    ordered = sorted(kinds, key=lambda k: hashlib.sha256((salt + k).encode()).hexdigest())
    kmap = {k: "N%02d" % (i + 1) for i, k in enumerate(ordered)}
    assert len(set(kmap.values())) == len(kinds), "kind tag map is not injective"
    pat = re.compile(r"(?<![A-Za-z0-9_.])(" +
                     "|".join(re.escape(k) for k in sorted(kmap, key=len, reverse=True)) +
                     r")(?![A-Za-z0-9_])")
    sub = lambda s: pat.sub(lambda m: kmap[m.group(1)], s)
    print("kind tokens discovered from LIVE:", len(kinds))
    print("tag->kind class counts:", {t: sum(1 for v in kmap.values() if v == t)
                                      for t in sorted(set(kmap.values()))})
    pinned = pinned_strings([(r, src) for r in fixture_rels])
    print("pinned prose values:", len(pinned), "files-mask-needles:", len(Masker(pinned).enc))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    changed, prose_fail, per_class = [], [], {}
    for dirpath, dirnames, filenames in os.walk(dst):
        dirnames[:] = [d for d in dirnames if d not in _pkg.SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, dst)
            in_verify = rel.split(os.sep)[0] == "verify"
            if ext not in BIJ_TEXT_EXT and ext not in BIJ_TOOL_EXT and not in_verify:
                continue
            try:
                txt = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            mk = Masker(pinned)
            masked = mk.mask(txt)
            n_before = mk.n
            new = mk.unmask(sub(masked))
            mk2 = Masker(pinned)
            mk2.mask(new)
            if mk2.n != n_before:
                prose_fail.append((rel, n_before, mk2.n))
            if new != txt:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed.append(rel)
                if ext in (".py", ".sh", ".bash") or in_verify:
                    cls = "tooling"
                elif ext == ".ts":
                    cls = "ts"
                elif ext in (".json", ".jsonl"):
                    cls = "data"
                else:
                    cls = "prose"
                per_class[cls] = per_class.get(cls, 0) + 1
    print("files changed:", len(changed), "by class:", per_class)
    for r in sorted(changed):
        print("   ", r)
    print("prose-integrity failures:", prose_fail if prose_fail else "none")
    print("map_shipped: false")
    if prose_fail:
        print("BUILD REJECTED: prose mask lost occurrences", file=sys.stderr)
        return 3
    return 0


def main():
    ap = argparse.ArgumentParser(description="in-memory longest-first token neutralisation")
    _pkg.add_package_arg(ap)
    ap.add_argument("--scheme", choices=("neutral-tag", "bij"), default="neutral-tag")
    ap.add_argument("--out", help="destination tree (default: <package>-neutralised)")
    ap.add_argument("--tokens", help="optional token list (one per line) for neutral-tag")
    ap.add_argument("--fixture", action="append", default=None,
                    help="fixture path relative to the tree (bij); default fixture-190.json+corpus.json")
    ap.add_argument("--live", default=BIJ_LIVE, help="tree the bij kinds are discovered from")
    ap.add_argument("--src", default=None,
                    help="tree copied to --out before the bij walk (default: --package)")
    ap.add_argument("--salt", default="BIJ/v1\0", help="kind-ordering salt (bij)")
    ap.add_argument("--diagnostic", action="append", default=[],
                    help="shell command whose (rc, stdout, stderr) must not move; repeatable")
    a = ap.parse_args()
    src = _pkg.resolve_package(a.package)
    out = a.out or (src.rstrip("/") + "-neutralised")
    out = os.path.abspath(out) if os.path.isabs(out) else os.path.join(_pkg.WORKSPACE, out)
    if os.path.abspath(out) == os.path.abspath(src):
        _pkg.die("--out must differ from --package (the source must stay pristine)", 2)

    before = digest_commands(a.diagnostic, src) if a.diagnostic else None
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(src, out, dirs_exist_ok=True)

    if a.scheme == "neutral-tag":
        tokens, mapping = build_map(load_tokens(a.tokens) if a.tokens
                                    else ROLES + ENUMS + FRAGS)
        tokens, tot, files = neutral_tag(out, tokens)
        print("scheme: injective, prefix G, longest-first, case-sensitive")
        print("renamed_tokens:", len(tokens))
        print("renamed_occurrences:", tot)
        print("files_changed:", files)
        print("tag_shape: G + two digits, %d tags used" % len(tokens))
        rc = 0
    else:
        rc = bij(out, a.live, a.src or src, a.fixture or BIJ_FIXTURES, a.salt)

    if a.diagnostic:
        after = digest_commands(a.diagnostic, out)
        if before != after:
            sys.stderr.write("DIAGNOSTIC MOVED under neutralisation -- rename NOT applied; "
                             "output left at %s for inspection\n" % out)
            for b, f in zip(before, after):
                if b != f:
                    sys.stderr.write("  %s: %r -> %r\n" % (b[0], b[1:], f[1:]))
            return 4
    return rc


if __name__ == "__main__":
    sys.exit(main())
