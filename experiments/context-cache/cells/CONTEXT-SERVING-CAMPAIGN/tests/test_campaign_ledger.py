import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

LEDGER_PY = "/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/ledger/ledger.py"

CAPS = {
    "total_cap": 10,
    "phase_caps": {
        "preflight": 2,
        "context": 3,
        "prompt_format": 1,
        "serving": 1,
        "holdout": 2,
        "contingency": 1,
    },
}


def make_env(tmp_path):
    d = tmp_path / "led"
    d.mkdir()
    cj = d / "campaign.json"
    cj.write_text(json.dumps({
        "total_cap": CAPS["total_cap"],
        "phase_caps": CAPS["phase_caps"],
        "lock_basename": "campaign.lock",
        "journal_basename": "journal.jsonl",
    }))
    (d / "campaign.lock").write_text("")
    return d, str(cj)


def run(d, cj, *args):
    cmd = [sys.executable, LEDGER_PY, "--campaign-json", cj, "--ledger-dir", str(d), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_concurrent_reserves_respect_cap(tmp_path):
    d, cj = make_env(tmp_path)
    # 4 processes each try to reserve 4 (total 16) against cap 10
    procs = []
    for i in range(4):
        p = subprocess.Popen(
            [sys.executable, LEDGER_PY, "--campaign-json", cj, "--ledger-dir", str(d),
             "reserve", "--phase", "context", "--label", "conc-%d" % i],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        procs.append(p)
    # stagger by having each process reserve multiple? single reserve per proc -> only 4 reserves, not enough to test cap
    # Instead: loop reserves in each process via a helper script
    # Use a python script that reserves until failure
    script = tmp_path / "worker.py"
    script.write_text("""
import subprocess, sys, os
d=os.environ['D']; cj=os.environ['CJ']
n=0
while True:
    r=subprocess.run([sys.executable, %r, '--campaign-json', cj, '--ledger-dir', d,
                      'reserve','--phase','context','--label','w'], capture_output=True, text=True)
    if r.returncode != 0:
        break
    n+=1
print(n)
""" % LEDGER_PY)
    envs = []
    ps = []
    for i in range(4):
        e = os.environ.copy()
        e["D"] = str(d)
        e["CJ"] = cj
        p = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=e)
        ps.append(p)
    for p in ps:
        p.communicate()
    jf = d / "journal.jsonl"
    ids = []
    for line in jf.read_text().splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        if o["type"] == "reserve":
            ids.append(o["attempt_id"])
    assert len(ids) <= CAPS["phase_caps"]["context"], len(ids)
    assert len(ids) == len(set(ids))


def test_phase_cap_raises_and_journal_unchanged(tmp_path):
    d, cj = make_env(tmp_path)
    # fill context phase cap (3)
    for i in range(3):
        r = run(d, cj, "reserve", "--phase", "context", "--label", "x%d" % i)
        assert r.returncode == 0, r.stderr
    before = (d / "journal.jsonl").read_bytes() if (d / "journal.jsonl").exists() else b""
    r = run(d, cj, "reserve", "--phase", "context", "--label", "overflow")
    assert r.returncode != 0
    after = (d / "journal.jsonl").read_bytes() if (d / "journal.jsonl").exists() else b""
    assert before == after


def test_killed_after_intent_leaves_unrowed(tmp_path):
    d, cj = make_env(tmp_path)
    r = run(d, cj, "reserve", "--phase", "preflight", "--label", "doomed")
    assert r.returncode == 0
    aid = r.stdout.strip()
    assert aid
    # no record -> unrowed
    r2 = run(d, cj, "status", "--json")
    assert r2.returncode == 0
    st = json.loads(r2.stdout)
    assert st["total_reserved"] == 1
    assert st["total_spent"] == 0
    assert st["total_unrecorded"] == 1
    assert st["total_remaining"] == CAPS["total_cap"] - 1


def test_corrupted_journal_fails_closed(tmp_path):
    d, cj = make_env(tmp_path)
    # create a valid reserve first
    r = run(d, cj, "reserve", "--phase", "preflight", "--label", "ok")
    assert r.returncode == 0
    jf = d / "journal.jsonl"
    # corrupt
    with open(jf, "a") as f:
        f.write("{not json}\n")
    # status nonzero
    r2 = run(d, cj, "status", "--json")
    assert r2.returncode != 0
    # reserve nonzero
    r3 = run(d, cj, "reserve", "--phase", "preflight", "--label", "x")
    assert r3.returncode != 0


def test_wrong_lock_path_or_missing_lock(tmp_path):
    d, cj = make_env(tmp_path)
    # wrong lock path (nonexistent)
    r = run(d, cj, "--lock-path", str(tmp_path / "nope" / "x.lock"), "status", "--json")
    assert r.returncode != 0
    # missing lock file: remove it
    (d / "campaign.lock").unlink()
    r2 = run(d, cj, "status", "--json")
    assert r2.returncode != 0


def test_status_totals_equal_recount(tmp_path):
    d, cj = make_env(tmp_path)
    # mix reserves and records
    aids = []
    for i in range(2):
        r = run(d, cj, "reserve", "--phase", "preflight", "--label", "a%d" % i)
        assert r.returncode == 0
        aids.append(r.stdout.strip())
    # second phase cap allows 1
    r = run(d, cj, "reserve", "--phase", "context", "--label", "c0")
    assert r.returncode == 0
    aids.append(r.stdout.strip())
    # record outcomes
    run(d, cj, "record", "--attempt-id", aids[0], "--outcome", "ok", "--usage-json", '{"prompt_tokens":5}')
    run(d, cj, "record", "--attempt-id", aids[1], "--outcome", "failed")
    # from-scratch recount via import
    sys.path.insert(0, str(d.parent)) if False else None
    # import ledger module from file
    import importlib.util
    spec = importlib.util.spec_from_file_location("ledger_mod", LEDGER_PY)
    mod = importlib.util.module_from_spec(spec)
    # need campaign args; call load_campaign via argparse? Use env approach by monkeypatch? Instead replicate read
    # Just recompute from journal directly
    events = [json.loads(l) for l in (d / "journal.jsonl").read_text().splitlines() if l.strip()]
    reserved = sum(1 for e in events if e["type"] == "reserve")
    spent = sum(1 for e in events if e["type"] == "record")
    r = run(d, cj, "status", "--json")
    assert r.returncode == 0
    st = json.loads(r.stdout)
    assert st["total_reserved"] == reserved
    assert st["total_spent"] == spent
    assert st["total_remaining"] == CAPS["total_cap"] - reserved
