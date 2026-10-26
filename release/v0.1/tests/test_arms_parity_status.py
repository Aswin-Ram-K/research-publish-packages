"""Red/green guard for tools/audit/arms_parity_status.py (unit ARMS-PARITY-WITHDRAW).

The point of the guard is that ARMS-PARITY's falsified verdict cannot come back by
accident. Three layers are pinned, and each is demonstrated red as well as green:

  1. GREEN  the real tree passes: the record is marked WITHDRAWN, the restored corpus
            gives R = 583.1408 / A - R = -53.8451, and no claim-bearing surface states
            a falsified figure.
  2. RED    remove the status mark from state/logs/arms-parity.json           -> C1 fails.
  3. RED    swap the *repaired* corpus in as rows.jsonl (the re-apply-the-repair
            mutation OFFLINE-REPAIR once performed for real)                  -> C2 fails
            on A - R = +137.8 and on 40 off-grid cached values.
  4. RED    put "+133.3 (pointer layout helps)" on a published surface        -> C5 fails,
            unless the same line marks it withdrawn.

Deliberate-failure run (proves the green is load-bearing):

    .venv/bin/python - <<'PY'
    import json; p='state/logs/arms-parity.json'; d=json.load(open(p))
    del d['status']; json.dump(d, open(p,'w'), indent=1)
    PY
    .venv/bin/python tools/audit/arms_parity_status.py    # MUST exit 1
    (restore: git checkout -- state/logs/arms-parity.json is NOT available for this
     workspace; the withdrawal record is state/logs/arms-parity-withdraw.json)

Read-only: every fixture outside tmp_path is opened for reading.
"""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import arms_parity_status as aps  # noqa: E402

O1 = os.path.join(ROOT, aps.CELL_REL, "PROMPT-O1")


# ------------------------------------------------------------------- 1. GREEN on disk
def test_green_on_the_real_tree():
    report = aps.audit(ROOT)
    assert report["ok"], report["problems"]
    assert report["surfaces_scanned"] >= 25
    assert report["standing"]["A_minus_R"] == pytest.approx(-53.8451, abs=1e-3)


def test_record_marks_the_verdict_withdrawn():
    log = json.load(open(os.path.join(ROOT, aps.LOG_REL)))
    assert log["status"] == "WITHDRAWN"
    assert log["withdrawn"]["by_unit"] == "ARMS-PARITY-WITHDRAW"
    # the inverted prescription must be disclosable, not silently rewritten
    assert log["withdrawn"]["inversion_disclosed"] is True
    # history preserved verbatim
    assert "PROMPT-O1" in log["per_cell"] and "R2-P1-O1" in log["per_cell"]
    assert "390.80" in log["verdict"]  # the original verdict text is still readable


def test_standing_figure_is_negative_a_cheaper():
    rows = aps.load_rows(os.path.join(O1, "rows.jsonl"))
    means = aps.arm_means(rows)
    a_minus_r = means["A"][0] - means["R"][0]
    assert means["R"][0] == pytest.approx(583.1408, abs=1e-3)
    assert a_minus_r == pytest.approx(-53.8451, abs=1e-3)
    assert a_minus_r < 0, "A cheaper: the sign ARMS-PARITY promoted is the corrupted one"


# -------------------------------------------------------- 2. RED: record un-marked
def _tmp_root(tmp_path, status_present=True, a_minus_r=-53.8451):
    root = tmp_path / "root"
    logs = root / "state" / "logs"
    logs.mkdir(parents=True)
    shutil.copy(os.path.join(ROOT, aps.LOG_REL), logs / "arms-parity.json")
    shutil.copy(os.path.join(ROOT, aps.WITHDRAW_REL), logs / "arms-parity-withdraw.json")
    log = json.load(open(logs / "arms-parity.json"))
    if not status_present:
        log.pop("status", None)
        log.pop("withdrawn", None)
    json.dump(log, open(logs / "arms-parity.json", "w"), indent=1)
    rec = json.load(open(logs / "arms-parity-withdraw.json"))
    rec["superseded_by"]["standing_figure"]["A_minus_R"] = a_minus_r
    json.dump(rec, open(logs / "arms-parity-withdraw.json", "w"), indent=1)
    return str(root)


def test_red_record_without_withdrawal_mark(tmp_path):
    problems = aps.check_record(_tmp_root(tmp_path, status_present=False))
    assert problems, "an un-marked ARMS-PARITY record must fail the guard"
    assert any("WITHDRAWN" in p for p in problems)


def test_red_standing_figure_altered(tmp_path):
    problems = aps.check_record(_tmp_root(tmp_path, a_minus_r=138.5))
    assert any("standing" in p.lower() for p in problems)


# --------------------------------------------- 3. RED: the repair swapped back in
def test_red_repaired_corpus_swapped_in(tmp_path):
    cells = tmp_path / "cells"
    o1 = cells / "PROMPT-O1"
    o1.mkdir(parents=True)
    shutil.copy(os.path.join(O1, "rows.repaired-DO-NOT-USE.jsonl"), o1 / "rows.jsonl")
    for name in ("rows.pre-correction.jsonl", "rows.repaired-DO-NOT-USE.jsonl"):
        shutil.copy(os.path.join(O1, name), o1 / name)

    problems = aps.check_corpus(str(o1.parent))
    assert any("A - R = +137" in p for p in problems), problems
    assert any("off the 64-token grid" in p for p in problems), problems


def test_repaired_corpus_is_the_impossible_one():
    rows = aps.load_rows(os.path.join(O1, "rows.repaired-DO-NOT-USE.jsonl"))
    off = aps.offgrid_cached(rows)
    assert len(off) == 40
    assert [c for _a, _t, c in off][:3] == [1409, 1793, 2433]
    means = aps.arm_means(rows)
    assert means["A"][0] - means["R"][0] == pytest.approx(137.8169, abs=1e-3)


# ------------------------------------------------------- 4. RED: a surface resurrects it
def test_red_surface_states_falsified_figure_as_live(tmp_path):
    doc = tmp_path / "claims.md"
    doc.write_text(
        "The publishable contrast is A-R = +133.3 [123.7, 143.0], i.e. A costlier, "
        "pointer layout helps.\n",
        encoding="utf-8",
    )
    problems = aps.check_surfaces([str(doc)])
    assert problems and "falsified figure stated as live" in problems[0]


def test_surface_may_quote_it_when_marking_it_dead(tmp_path):
    doc = tmp_path / "correction.md"
    doc.write_text(
        "Earlier claim A-R = +133.3 (pointer layout helps) is withdrawn and falsified; "
        "A-R = -53.8451 stands.\n",
        encoding="utf-8",
    )
    assert aps.check_surfaces([str(doc)]) == []


# ---------------------------------------------------------------------------- CLI
def test_cli_exit_codes(tmp_path):
    assert aps.main(["--root", ROOT]) == 0
    broken = _tmp_root(tmp_path, status_present=False)
    assert aps.main(["--root", broken, "--json"]) == 1
