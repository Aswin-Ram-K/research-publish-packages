"""Generate the red->green transcript for VLLM-CELL. Writes state/logs/VLLM-CELL-redgreen.txt.

Each RED case reverts one behaviour in a throwaway copy under /tmp and shows the
matching test fail. No network, no live calls.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/zer0null/reserach extarctor")
CELL_DIR = ROOT / "experiments/context-cache/cells/VLLM-CELL"
OUT = ROOT / "state/logs/VLLM-CELL-redgreen.txt"
PY = str(ROOT / ".venv/bin/python")

CASES = [
    ("R1", "details absent -> 0 instead of null",
     'cached, cache_report = None, "unavailable"',
     'cached, cache_report = 0, "reported"',
     "test_details_absent_is_null_not_zero"),
    ("R2", "cached_tokens dropped to None",
     'cached, cache_report = int(details["cached_tokens"]), "reported"',
     'cached, cache_report = None, "unavailable"',
     "test_cached_tokens_reported"),
    ("R3", "500 no longer raises",
     'if resp.status_code != 200:\n        raise RuntimeError("http %d" % resp.status_code)',
     'if resp.status_code != 200:\n        pass',
     "test_http_500_raises"),
    # H's marker covers turns 1..8 only; from turn 9 the fold is what distinguishes
    # it. So "remove the marker" alone is NOT a red case: after turn 8 the fold
    # keeps H distinct and the suite correctly stays green. That collapse is
    # produced by reverting the fold itself -- see redgreen R4a-collapse below.
    ("R4a", "H collapses onto A (marker removed AND fold reverted)",
     'text = (SCAFFOLD + "INDEX (hybrid; folds=%02d):\\n" % folds',
     'text = (SCAFFOLD + "INDEX:\\n"',
     "test_four_arms_pairwise_distinct_every_turn",
     ('lines.append(folded_summary(t, max(1, t - SUMMARY_EVERY + 1)))',
      'lines.append("t%03d | %d | %s | %s" % (t, len(block), sha8(block), summarise(block)))')),
    ("R4b", "H no longer compresses (fold emits a plain clipped summary)",
     'lines.append(folded_summary(t, max(1, t - SUMMARY_EVERY + 1)))',
     'lines.append("t%03d | %d | %s | %s" % (t, len(block), sha8(block), summarise(block)))',
     "test_hybrid_compacts_at_summary_boundary"),
    ("R5", "R collapses onto the A rendering",
     'text = SCAFFOLD + "HISTORY:\\n" + body_upto(turn) + "\\n" + CANARY',
     'text = (SCAFFOLD + pointer_index(turn - 1)\n                + "\\nNEWEST DELTA:\\n" + delta_block(turn) + "\\n" + CANARY)',
     "test_R_and_A_differ"),
]


def run_pytest(path):
    proc = subprocess.run([PY, "-m", "pytest", path, "-q"],
                          capture_output=True, text=True, cwd=str(ROOT),
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    return (proc.stdout + proc.stderr).strip().splitlines()


def fresh_copy():
    tmp = Path(tempfile.mkdtemp(prefix="vc-redgreen-"))
    dst = tmp / "cell"
    shutil.copytree(CELL_DIR, dst)
    return tmp, dst


def main():
    lines = [
        "VLLM-CELL red->green transcript",
        "cell : experiments/context-cache/cells/VLLM-CELL/vllm_cell.py",
        "tests: experiments/context-cache/cells/VLLM-CELL/tests/test_cell.py",
        "mode : offline, transport stubbed; the POST is monkeypatched in every test",
        "",
        "== BASELINE (unmodified copy) ==",
    ]
    tmp, dst = fresh_copy()
    lines += run_pytest(str(dst / "tests"))[-2:]
    shutil.rmtree(tmp)

    for case in CASES:
        name, desc, pat, rep, test = case[:5]
        extra = case[5] if len(case) > 5 else None
        tmp, dst = fresh_copy()
        src = dst / "vllm_cell.py"
        text = src.read_text()
        if pat not in text:
            lines.append("== %s RED: %s ==\n   PATTERN NOT FOUND -- case invalid" % (name, desc))
            shutil.rmtree(tmp)
            continue
        text = text.replace(pat, rep, 1)
        if extra:
            assert extra[0] in text, "extra pattern missing: %r" % extra[0][:50]
            text = text.replace(extra[0], extra[1], 1)
        src.write_text(text)
        lines.append("")
        lines.append("== %s RED: %s ==" % (name, desc))
        lines.append("   revert -> %r" % rep[:90])
        if extra:
            lines.append("   revert -> %r" % extra[1][:90])
        lines += ["   " + line for line in run_pytest(str(dst / "tests"))[-2:]]
        lines.append("   targeted test: %s" % test)
        shutil.rmtree(tmp)

    lines += ["", "== RESTORED (workspace original, untouched) =="]
    lines += run_pytest(str(CELL_DIR / "tests"))[-2:]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
