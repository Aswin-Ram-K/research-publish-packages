#!/usr/bin/env python3
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LONGRUN = ROOT / "experiments/ptr-engine/longrun"
SCORER = LONGRUN / "score_longrun.py"
FIXTURE = LONGRUN / "tasks-v4/runtime-v4/LR-01.v5.json"
DIGEST = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

def score(log_path):
    proc = subprocess.run([sys.executable, str(SCORER), "--fixture", str(FIXTURE), "--run", str(log_path)],
                          capture_output=True, text=True)
    card = {}
    for line in proc.stdout.splitlines():
        line=line.strip()
        if line.startswith("{"):
            card = json.loads(line)
    return proc.returncode, card

def make_log(answer):
    rows = [{"fixture_sha256": DIGEST, "task_id": "LR-01", "arm": "B", "rep": 1}]
    for turn in range(1, 49):
        content = "work turn %d" % turn
        if turn == 48:
            content = answer
        rows.append({"turn": turn, "arm": "B", "rep": 1, "content": content})
    p = Path(tempfile.mkdtemp()) / "run.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p

good = ("read experiments/ptr-engine/tests/test_scope.py and tests/test_negative_controls.py: 9 def test_ entries; read experiments/ptr-engine/ptr_engine/resolve.py: the isinstance guard sits after the recorded block; "
        "tests/test_scope.py has 9 def test_ entries; PtrNotAReferenceError / PTR_NOT_A_REFERENCE raised; read established all.")
p = make_log(good)
rc, card = score(p)
print("positive rc", rc)
# check acc.2-4 pass
for c in card.get("checks", []):
    if c.get("id") in ("acc.2","acc.3","acc.4","check.2","check.3","check.4"):
        print(c.get("id"), c.get("verdict"))
assert rc in (0,1)

bad = "I guess everything is fine, no reads performed."
p2 = make_log(bad)
rc2, card2 = score(p2)
print("negative rc", rc2)
print("OK")
