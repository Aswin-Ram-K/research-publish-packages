#!/usr/bin/env python3
"""failed_column.py - turn the board's `failed` column into a work list.

WHAT IT DOES (stdlib only, offline, read-only on the tree)
  For every card the UNSTAMPED-104 census put in the failed column, decide from the
  artefacts *and a fresh run today* which of four reclaim classes it is:

    finished_once_and_still_green  declared artefacts exist AND the card's own recorded
                                   acceptance command exits 0 against the current tree
    finished_once_but_red_today    artefacts exist, the command now exits non-zero
    not_runnable                   no recorded command, or one that cannot run today
                                   (reason named: no handoff, network, mutating, missing file)
    no_artifacts                   nothing on disk from that unit: genuinely unfinished

  Plus `superseded` for the five cards the census already answered with a successor.

COMMAND SELECTION (stated, not guessed)
  A handoff's `evidence.commands` is a narrative, not an argv: entries arrive as strings
  with "  ->  output" tails, as {'cmd':..,'output':..} dicts, and as prose ("ssh ... 'free -m'").
  Each entry is normalised to its base command, then commands that cannot be re-run offline
  and read-only are dropped: network (ssh/curl/wget/docker), mutating (redirects, --out,
  git commit|checkout|apply, rm/mv), and placeholders ("...").  Of what remains the highest
  scoring entry is chosen: pytest/test_ (3) > --check/verify/audit/grade (2) > other (1).
  The chosen string is recorded verbatim in the JSON so a reader can audit the pick.

SAFETY
  Commands run with cwd = repo root, shell=True, timeout 120 s, PYTHONDONTWRITEBYTECODE=1.
  Nothing is run that the filter above did not clear as offline + non-mutating.  A command
  the tool refuses to run is `not_runnable` with the refusal reason, never a silent skip.

    python3 experiments/ptr-engine/tools/failed_column.py            # classify + write JSON
    python3 experiments/ptr-engine/tools/failed_column.py --no-run   # classify, do not execute
    python3 experiments/ptr-engine/tools/failed_column.py --check    # verify an existing JSON

--check exits 1 iff a card is unclassified, a finished_once_and_still_green card's command
now exits non-zero, or the class totals do not sum to the in-scope count.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.normpath(os.path.join(HERE, os.pardir))
ROOT = os.path.normpath(os.path.join(ENGINE, os.pardir, os.pardir))
MEASURE = os.path.join(ENGINE, "measure")
DEFAULT_CENSUS = os.path.join(MEASURE, "UNSTAMPED-CENSUS.json")
DEFAULT_OUT = os.path.join(MEASURE, "FAILED-COLUMN-RECLAIM.json")
DEFAULT_LEDGER = os.path.expanduser("~/.dsh/task-board/ledger-v2.json")

CLASSES = (
    "finished_once_and_still_green",
    "finished_once_but_red_today",
    "not_runnable",
    "no_artifacts",
    "superseded",
)
NEXT_ACTION = {
    "finished_once_and_still_green": "record_a_row",
    "finished_once_but_red_today": "repair",
    "not_runnable": "re_run",
    "no_artifacts": "leave",
    "superseded": "drop_as_superseded",
}

NET = re.compile(r"^\s*(ssh|scp|curl|wget|docker|systemctl|sudo)\b")
MUTATE = re.compile(r"(>>?\s*\S|--out\b|\bgit\s+(commit|checkout|apply|push|add|reset)\b|\brm\s|\bmv\s|\bmkdir\b|--write\b)")
PLACEHOLDER = re.compile(r"(\.\.\.|<[^>]+>|\bR\.jsonl\b|\bF\.json\b|\bO\.json\b|\bcmd\b|"
                         r"^(same|the|this|that|then|see)\b|same command)")
# Tools measured to write on their own run path (open(...,'w'|'a') / write_text / append):
# re-running them would edit a measurement record, which this unit may not do.
WRITER = re.compile(r"(run_longrun\.py(?!.*--self-test)|_cell\.py|cx_corpus\.py|cx_harness\.py|"
                    r"run_cx2\.py(?!.*--dry-run)|grader_fitness\.py|det_verify\.py|"
                    r"avalanche/probe\.py|best_config_build\.py|grade_v[34]\.py)")
INSPECT = re.compile(r"^\s*(wc|grep|head|tail|cat|ls|sha256sum|hostname|date|whoami|free|df|uptime|uname|echo|nvidia-smi|nvcc|ps|top)\b")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def handoff_index():
    """unit name -> handoff path.  The handoff's own `unit` field wins over its filename."""
    idx = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "orchestration", "handoffs", "*.json"))):
        try:
            d = load_json(p)
        except Exception:
            continue
        u = d.get("unit")
        if isinstance(u, str) and u not in idx:
            idx[u] = p
    return idx


def ledger_executions():
    """card id -> (execution id of the last failed execution, last result)."""
    if not os.path.exists(DEFAULT_LEDGER):
        return {}
    try:
        data = load_json(DEFAULT_LEDGER)
    except Exception:
        return {}
    out = {}
    for t in data.get("tasks") or []:
        ex = t.get("executions") or []
        if not ex:
            continue
        failed = [e for e in ex if e.get("result") == "failed"]
        pick = (failed or ex)[-1]
        out[t.get("id")] = (pick.get("id"), pick.get("result"))
    return out


def names_on_disk(unit, limit=6):
    """Files anywhere under a few artefact dirs whose basename carries the unit token."""
    hits = []
    token = unit.strip().lower().replace(" ", "-")
    if len(token) < 3:
        return hits
    for base in ("measure", "docs", "orchestration/units", "state/logs"):
        root = os.path.join(ROOT, base)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for fn in filenames:
                if token in fn.lower():
                    hits.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
                    if len(hits) >= limit:
                        return hits
    return hits


def base_command(entry):
    """Normalise one evidence.commands entry to a base command string (or '')."""
    if isinstance(entry, dict):
        entry = entry.get("cmd") or entry.get("command") or ""
    if not isinstance(entry, str):
        return ""
    cmd = entry.split(" -> ")[0].split("  ->  ")[0].strip()
    cmd = re.sub(r"\s+\((#|exit|via|red|green|after|before|offline|holds).*$", "", cmd)
    return cmd.strip().rstrip(";").strip()


def runnable(cmd):
    """(ok, reason).  ok means: offline, non-mutating, and the referenced script exists."""
    if not cmd or PLACEHOLDER.search(cmd):
        return False, "placeholder/prose, not an executable command"
    if NET.search(cmd):
        return False, "network or container command; offline session cannot re-run it"
    if MUTATE.search(cmd):
        return False, "mutating command (redirect/--out/git write); not re-run outside /tmp"
    if WRITER.search(cmd):
        return False, "the tool writes on its own run path; re-running would edit a measurement record"
    if INSPECT.search(cmd):
        return False, "inspection only (wc/grep/host/nvidia-smi), not an acceptance command"
    if re.match(r"^\s*(python3?|\.venv/bin/python) -c ", cmd) and not re.search(r"assert|raise|sys\.exit|exit\(", cmd):
        return False, "python -c that only prints; inspection, not an acceptance command"
    for tok in cmd.split():
        if "/" in tok and not tok.startswith("-"):
            cand = tok.strip("'\"")
            if cand.endswith((".py", ".sh", ".jsonl", ".json")) and not os.path.exists(os.path.join(ROOT, cand)):
                return False, "referenced path absent today: %s" % cand
    return True, ""


def pick_command(handoff):
    """(best runnable command, first reason each candidate was rejected)."""
    ev = handoff.get("evidence") or {}
    entries = ev.get("commands") or []
    rejected = []
    best, best_score = "", 0
    for e in entries:
        cmd = base_command(e)
        ok, why = runnable(cmd)
        if not ok:
            if why:
                rejected.append(why)
            continue
        score = 1
        if re.search(r"pytest|test_", cmd):
            score = 3
        elif re.search(r"--check|verify|audit|grade", cmd):
            score = 2
        if score > best_score:
            best, best_score = cmd, score
    return best, rejected


def execute(cmd, timeout=120):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    try:
        p = subprocess.run(cmd, shell=True, cwd=ROOT, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", "replace")
        return p.returncode, out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else ""
        return 124, out
    except Exception as e:  # noqa: BLE001 - a non-launchable command is a result, not a crash
        return 2, "launch failed: %s" % e


def first_failure(out):
    for pat in (r"AssertionError", r"Assertion", r"ModuleNotFoundError", r"FAILED", r"No such file", r"Error|error:"):
        for line in out.splitlines():
            if re.search(pat, line):
                return line.strip()[:200]
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    return lines[-1][:200] if lines else ""


def classify(census_row, handoff, exec_info, do_run):
    unit = census_row["title"]
    entry = {
        "card": census_row["card_id"],
        "unit": unit,
        "execution_id": exec_info[0] if exec_info else None,
        "class": None,
        "artifacts_present": [],
        "command": None,
        "exit_today": None,
        "first_failure_line": "",
        "next_action": None,
        "reason": "",
    }
    def declared_paths(h):
        """Artefacts a handoff declares: `artifacts` plus `write_paths`, minus bookkeeping."""
        out = []
        for a in (h.get("artifacts") or []) + (h.get("write_paths") or []):
            if not isinstance(a, str):
                continue
            if a.startswith("orchestration/handoffs/") or a.startswith("orchestration/journals/"):
                continue
            out.append(a)
        return out

    if census_row.get("classification") == "superseded_or_duplicate":
        entry["class"] = "superseded"
        entry["reason"] = "answered by a later card: %s" % (census_row.get("successor") or "successor named in census")
        if handoff:
            entry["artifacts_present"] = [a for a in declared_paths(handoff) if os.path.exists(os.path.join(ROOT, a))]
        entry["next_action"] = NEXT_ACTION["superseded"]
        return entry

    rejected = []
    if handoff:
        entry["artifacts_present"] = [a for a in declared_paths(handoff) if os.path.exists(os.path.join(ROOT, a))]
    else:
        entry["artifacts_present"] = names_on_disk(unit)
    entry["declared"] = declared_paths(handoff) if handoff else []

    cmd = ""
    if handoff:
        cmd, rejected = pick_command(handoff)
    if not cmd and census_row.get("command"):
        cand = base_command(census_row["command"])
        ok, why = runnable(cand)
        if ok:
            cmd = cand
        else:
            rejected.append(why)
    entry["command"] = cmd or None

    if not handoff and cmd:
        entry["artifacts_present"] = sorted({
            p for p in re.findall(r"/[A-Za-z0-9_./-]+\.(?:json|md|mdx|txt|jsonl)", cmd)
            if os.path.exists(p)})
        for dpath in re.findall(r"/[A-Za-z0-9_./-]+/", cmd):
            if os.path.isdir(dpath):
                entry["artifacts_present"] = sorted(set(entry["artifacts_present"]) | {dpath})

    if not entry["artifacts_present"] and census_row.get("row_present") and cmd:
        # A card with a measuring row but no handoff: its row's command is the only
        # statement about its artefacts, so run it.  Green here is a row re-recordable
        # for free; the command itself validated the files it names.
        if do_run:
            code, out = execute(cmd)
            entry["exit_today"] = code
            if code == 0:
                entry["class"] = "finished_once_and_still_green"
                entry["reason"] = "measuring row exists; its own command exits 0 today (no handoff declares artefacts)"
                entry["next_action"] = NEXT_ACTION["finished_once_and_still_green"]
                return entry
            entry["first_failure_line"] = first_failure(out)
            entry["class"] = "not_runnable"
            entry["reason"] = "measuring row exists but its command exits %s today; no handoff declares artefacts" % code
            entry["next_action"] = NEXT_ACTION["not_runnable"]
            return entry
        entry["class"] = "not_runnable"
        entry["reason"] = "not executed (--no-run)"
        entry["next_action"] = NEXT_ACTION["not_runnable"]
        return entry

    if not entry["artifacts_present"]:
        entry["class"] = "no_artifacts"
        entry["reason"] = ("declared artefacts listed by the handoff are all absent"
                           if handoff else "no handoff and no file on disk carries this unit")
        entry["next_action"] = NEXT_ACTION["no_artifacts"]
        return entry

    if not cmd:
        entry["class"] = "not_runnable"
        if not handoff:
            entry["reason"] = "no handoff, so no recorded acceptance command"
        else:
            entry["reason"] = "handoff records no runnable command (%s)" % ("; ".join(sorted(set(rejected))[:2]) or "no commands at all")
        entry["next_action"] = NEXT_ACTION["not_runnable"]
        return entry

    if not do_run:
        entry["class"] = "not_runnable"
        entry["reason"] = "not executed (--no-run)"
        entry["next_action"] = NEXT_ACTION["not_runnable"]
        return entry

    code, out = execute(cmd)
    entry["exit_today"] = code
    if code == 127 or ("not found" in out and code != 0 and "not found" in out.splitlines()[0]):
        entry["class"] = "not_runnable"
        entry["reason"] = "command is not resolvable in this shell (exit 127): %s" % (first_failure(out) or "not found")
        entry["next_action"] = NEXT_ACTION["not_runnable"]
        return entry
    if code == 0:
        entry["class"] = "finished_once_and_still_green"
        entry["next_action"] = NEXT_ACTION["finished_once_and_still_green"]
        entry["reason"] = "declared artefacts present and the recorded acceptance command exits 0 today"
    else:
        entry["class"] = "finished_once_but_red_today"
        entry["first_failure_line"] = first_failure(out)
        entry["next_action"] = NEXT_ACTION["finished_once_but_red_today"]
        entry["reason"] = "command exits %s today" % code
        if code == 124:
            entry["reason"] += " (timeout; exit 124 is outside EXIT_TABLE, recorded not guessed)"
    return entry


def build(do_run, census_path=DEFAULT_CENSUS):
    census = load_json(census_path)
    idx = handoff_index()
    execs = ledger_executions()
    rows = []
    for r in census["rows"]:
        unit = r["title"]
        hp = idx.get(unit) or os.path.join(ROOT, "orchestration", "handoffs", unit + ".json")
        handoff = None
        if os.path.exists(hp):
            try:
                handoff = load_json(hp)
            except Exception:
                handoff = None
        rows.append(classify(r, handoff, execs.get(r["card_id"]), do_run))
    counts = {c: sum(1 for x in rows if x["class"] == c) for c in CLASSES}
    in_scope = len(rows) - counts["superseded"]
    return {
        "unit": "FAILED-COLUMN-RECLAIM",
        "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "scope": {
            "census": os.path.relpath(DEFAULT_CENSUS, ROOT),
            "census_total": len(rows),
            "superseded_excluded": counts["superseded"],
            "in_scope": in_scope,
            "arithmetic": "104 census = 96 never_had_a_row + 5 superseded + 2 verified_fail(exit 0, drift) "
                          "+ 1 unstamped_refusal(124). In scope = 96 + 2 + 1 = %d. The card's 94 subtracted "
                          "the 5 superseded twice (the 96 already excludes them)." % in_scope,
        },
        "counts": counts,
        "rows": rows,
    }


def check(out_path=DEFAULT_OUT, census_path=DEFAULT_CENSUS):
    """Recompute and fail on an unclassified card, a green card that is now red, or bad totals."""
    if not os.path.exists(out_path):
        print("CHECK FAIL: %s missing" % out_path)
        return 1
    stored = load_json(out_path)
    bad = []
    rows = stored.get("rows") or []
    seen = set()
    for r in rows:
        seen.add(r.get("card"))
        if r.get("class") not in CLASSES:
            bad.append("%s: unclassified (class=%r)" % (r.get("unit"), r.get("class")))
        if r.get("class") == "finished_once_and_still_green":
            cmd = r.get("command")
            code, out = execute(cmd or "", timeout=120)
            if code != 0:
                bad.append("%s: green card's command now exits %s (%s)" % (r.get("unit"), code, first_failure(out)))
    census = load_json(census_path)
    missing = sorted({x["title"] for x in census["rows"]} - {r.get("unit") for r in rows})
    for m in missing:
        bad.append("%s: not in the reclaim file" % m)
    counts = stored.get("counts") or {}
    in_scope = (stored.get("scope") or {}).get("in_scope")
    total = sum(counts.get(c, 0) for c in CLASSES)
    if total != (stored.get("scope") or {}).get("census_total"):
        bad.append("totals do not reach the census: %d != %s" % (total, (stored.get("scope") or {}).get("census_total")))
    if in_scope != total - counts.get("superseded", 0):
        bad.append("in_scope %r != non-superseded total %d" % (in_scope, total - counts.get("superseded", 0)))
    if bad:
        print("CHECK FAIL (%d)" % len(bad))
        for b in bad:
            print("  -", b)
        return 1
    print("RECLAIM OK %d cards: %s; in scope %s" % (total, json.dumps(counts, sort_keys=True), in_scope))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-run", action="store_true")
    ap.add_argument("--census", default=DEFAULT_CENSUS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if args.check:
        return check(args.out, args.census)
    result = build(do_run=not args.no_run, census_path=args.census)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("WROTE %s" % os.path.relpath(args.out, ROOT))
    print(json.dumps(result["counts"], sort_keys=True))
    for r in result["rows"]:
        if r["class"] == "finished_once_and_still_green":
            print("GREEN", r["unit"], "|", (r["command"] or "")[:90])
    return 0


if __name__ == "__main__":
    sys.exit(main())
