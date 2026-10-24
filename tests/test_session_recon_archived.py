"""Guard: an archived card must never make ``session_recon.py`` exit non-zero.

Why this test exists
--------------------
The reconciler's exit code is only worth something if ``exit=1`` always means an
*actionable* violation.  On 2026-10-23 it did not: two cards (``GATE-RUNNER``,
``FIX-PROSE2``) had been **archived** while still reading ``status = "todo"`` —
the archive action does not rewrite ``status`` — and ``find_settled_lag`` graded
their frozen column as a live lag.  The run printed::

    session-recon: ... offenders=2 lagging=2 archived-unaware ... exit=1

for cards nobody could act on, and the same session ids were then counted a
second time because the settled-lag branch appended the raw ``session-<uuid>``
key to an offender list that already held the normalized ``<uuid>``.  A false red
teaches the operator to ignore the exit code, which is the same as deleting the
check.

What is pinned
--------------
1. An archived card whose latest execution ended is **recorded**
   (``archivedWithSettledExecution``) and is **not** a lag / offender.
2. A live (non-archived) card in the same shape **is** a lag and fails.
3. The exit-code contract itself, driven end-to-end through ``main()`` on a
   synthetic ledger.
4. One lagging card yields exactly one offender entry (the double-count).
5. Scheduled cards keep their lifecycle and are not lags (unchanged behaviour
   the archived fix must not disturb).

Red -> green
------------
Reverting ``find_settled_lag`` to its pre-fix body (skip only ``t.get("schedule")``,
return a bare list) makes ``test_archived_card_is_not_a_lag`` fail with
``AssertionError: archived card 7a74... reported as a settled-lag`` and
``test_cli_exit_code_ignores_archived_cards`` fail with ``assert 1 == 0``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RECON_PATH = REPO_ROOT / "tools" / "board" / "session_recon.py"


def _load_recon() -> ModuleType:
    """Import tools/board/session_recon.py by path (``tools/`` is not a package)."""
    spec = importlib.util.spec_from_file_location("session_recon_under_test", RECON_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def recon() -> ModuleType:
    return _load_recon()


def _card(
    card_id: str,
    *,
    status: str = "todo",
    ended: bool = True,
    archived: bool = False,
    schedule: bool | None = None,
    session: str | None = None,
) -> dict:
    """A ledger card shaped like DSH's task board (subset the reconciler reads)."""
    sid = session or f"session-{card_id}"
    card: dict = {
        "id": card_id,
        "title": f"card {card_id}",
        "status": status,
        "createdAt": 1_700_000_000_000,
        "derivations": [],
        "executions": [
            {
                "id": f"exec-{card_id}",
                "sessionId": sid,
                "startedAt": 1_792_700_000_000,
                "endedAt": 1_792_700_100_000 if ended else None,
                "result": "cancelled",
            }
        ],
    }
    if archived:
        card["archivedAt"] = 1_792_746_000_000
    if schedule is not None:
        card["schedule"] = schedule
    return card


# --------------------------------------------------------------------------- #
# Unit level: find_settled_lag's contract
# --------------------------------------------------------------------------- #


def test_archived_card_is_not_a_lag(recon: ModuleType) -> None:
    card = _card("7a7424d4-fbcd-49af-b0aa-c095bf83bf7a", archived=True)
    lagging, archived = recon.find_settled_lag([card])

    assert lagging == [], f"archived card {card['id']} reported as a settled-lag"
    assert [a["cardId"] for a in archived] == [card["id"]]
    assert archived[0]["status"] == "todo"
    assert "archived" in archived[0]["reason"]


def test_live_card_still_lags(recon: ModuleType) -> None:
    """The guard must not be satisfied by turning settled-lag off."""
    card = _card("live-card-0001", archived=False)
    lagging, archived = recon.find_settled_lag([card])

    assert [c["cardId"] for c in lagging] == [card["id"]]
    assert archived == []


def test_archived_scheduled_card_is_never_a_lag(recon: ModuleType) -> None:
    """Archived + scheduled: each exemption holds on its own, so neither may lag."""
    card = _card("arch-sched-0001", archived=True, schedule={"enabled": False, "mode": "cron"})
    lagging, archived = recon.find_settled_lag([card])

    assert lagging == [], "an archived scheduled card was graded as a live lag"
    assert [a["cardId"] for a in archived] in ([card["id"]], [])


def test_scheduled_card_is_not_a_lag(recon: ModuleType) -> None:
    card = _card("sched-live-0001", schedule={"enabled": True, "mode": "cron"})
    lagging, archived = recon.find_settled_lag([card])

    assert lagging == []
    assert archived == []


def test_running_execution_is_not_a_lag(recon: ModuleType) -> None:
    card = _card("running-0001", status="running", ended=False)
    lagging, archived = recon.find_settled_lag([card])

    assert lagging == []
    assert archived == []


def test_settled_archived_card_is_reported_nowhere(recon: ModuleType) -> None:
    card = _card("settled-0001", status="done", archived=True)
    lagging, archived = recon.find_settled_lag([card])

    assert lagging == []
    assert archived == []


# --------------------------------------------------------------------------- #
# CLI level: the exit code means something
# --------------------------------------------------------------------------- #


def _write_ledger(path: Path, tasks: list[dict]) -> Path:
    path.write_text(json.dumps({"schemaVersion": 2, "revision": 1, "tasks": tasks}))
    return path


def _run(recon: ModuleType, tmp_path: Path, ledger: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[int, dict]:
    """Drive main() against a synthetic ledger; return (exit code, report).

    The sessions root points at an existing but *empty* encoded dir: that takes
    the real code path (no short-circuit) without reading any live transcript.
    """
    report = tmp_path / "report.json"
    sessions_root = tmp_path / "sessions"
    (sessions_root / "encoded").mkdir(parents=True)
    monkeypatch.setattr(recon, "SESSIONS_ROOT", str(sessions_root), raising=True)
    monkeypatch.setattr(recon, "find_encoded_dir", lambda cwd: "encoded", raising=True)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "session_recon.py",
            "--cwd", str(tmp_path),
            "--ledger", str(ledger),
            "--report", str(report),
            "--waivers", str(tmp_path / "no-waivers.json"),
        ],
    )
    code = recon.main()
    return code, json.loads(report.read_text())


def test_cli_exit_code_ignores_archived_cards(
    recon: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = _write_ledger(
        tmp_path / "ledger.json",
        [_card("7a7424d4-fbcd-49af-b0aa-c095bf83bf7a", archived=True)],
    )
    code, report = _run(recon, tmp_path, ledger, monkeypatch)

    assert code == 0, "an archived card alone must not fail the reconciler"
    assert report["summary"]["laggingCards"] == 0
    assert report["summary"]["archived"] == 1
    assert report["summary"]["offenders"] == 0
    assert [a["cardId"] for a in report["archivedWithSettledExecution"]] == [
        "7a7424d4-fbcd-49af-b0aa-c095bf83bf7a"
    ]


def test_cli_exit_code_still_fails_a_live_lag(
    recon: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = _write_ledger(tmp_path / "ledger.json", [_card("live-card-0002")])
    code, report = _run(recon, tmp_path, ledger, monkeypatch)

    assert code == 1, "a genuinely unsettled live card must still fail"
    assert report["summary"]["laggingCards"] == 1


def test_cli_counts_one_offender_per_lagging_card(
    recon: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The settled-lag branch used to add the raw ``session-<uuid>`` key beside
    the normalized one, so two lagging cards printed four offender lines."""
    ledger = _write_ledger(
        tmp_path / "ledger.json",
        [_card("live-card-0003"), _card("live-card-0004")],
    )
    code, report = _run(recon, tmp_path, ledger, monkeypatch)

    assert code == 1
    assert report["offenders"] == sorted(report["offenders"])
    assert len(report["offenders"]) == 2, report["offenders"]
    assert len(report["offenderDetails"]) == 2, report["offenderDetails"]
    assert not any(o.startswith("session-") for o in report["offenders"])


def test_offender_list_prints_each_card_once(
    recon: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``main()`` printed ``offenderDetails`` and then re-printed ``laggingCards``,
    so a single lagging card showed up twice in OFFENDERS on the terminal."""
    ledger = _write_ledger(tmp_path / "ledger.json", [_card("live-card-0005")])
    code, _ = _run(recon, tmp_path, ledger, monkeypatch)
    out = capsys.readouterr().out

    assert code == 1
    lines = [ln for ln in out.splitlines() if "class=settled-lag" in ln]
    assert len(lines) == 1, out
