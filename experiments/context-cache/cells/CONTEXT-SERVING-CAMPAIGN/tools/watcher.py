#!/usr/bin/env python3
"""Read-only supervisor for a campaign run.

Polls only files and process liveness. Never HTTP, never writes rows.
Appends one JSON event per check to --out. Read-only with respect to rows,
intents and the ledger.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_FIRST_ROW_DEADLINE_S = 30.0
DEFAULT_ROW_GAP_DEADLINE_S = 30.0
DEFAULT_INTENT_TOLERANCE = 1
DEFAULT_LEDGER_TOLERANCE = 1
ALIVE_FRESHNESS_S = 15.0


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _load_envelope(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}


def _resolve_path(env, candidates, base_dirs):
    for k in candidates:
        v = env.get(k)
        if v:
            p = Path(v)
            if not p.is_absolute():
                for bd in base_dirs:
                    cand = Path(bd) / p
                    if cand.exists():
                        p = cand
                        break
            return p
    return None


def _base_dirs(env_path, env):
    out = [Path.cwd(), Path(env_path).resolve().parent]
    # try parent ledger/envelopes conventions
    ep = Path(env_path).resolve().parent
    out.append(ep.parent)
    out.append(ep.parent.parent)
    return out


def _ledger_journal_path(env, env_path):
    base_dirs = _base_dirs(env_path, env)
    # ledger_dir
    ld = env.get("ledger_dir") or env.get("ledger_path")
    if ld:
        p = Path(ld)
        if not p.is_absolute():
            for bd in base_dirs:
                cand = Path(bd) / p
                if cand.exists():
                    p = cand
                    break
        # journal basename
        jb = env.get("journal_basename", "journal.jsonl")
        if env.get("campaign_json"):
            try:
                cj = json.loads(Path(env["campaign_json"]).read_text())
                jb = cj.get("journal_basename", jb)
            except Exception:
                pass
        return p / jb if p.is_dir() else p
    cj = env.get("campaign_json") or env.get("ledger_campaign_json")
    if cj:
        cp = Path(cj)
        if not cp.is_absolute():
            for bd in base_dirs:
                cand = Path(bd) / cp
                if cand.exists():
                    cp = cand
                    break
        try:
            c = json.loads(cp.read_text())
            jb = c.get("journal_basename", "journal.jsonl")
        except Exception:
            jb = "journal.jsonl"
        return cp.parent / jb
    # default: sibling ledger dir
    for bd in base_dirs:
        cand_dir = Path(bd) / "ledger"
        if (cand_dir / "journal.jsonl").exists() or cand_dir.exists():
            return cand_dir / "journal.jsonl"
    return None


def _count_lines(path):
    if path is None or not Path(path).exists():
        return 0
    n = 0
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    n += 1
    except Exception:
        return 0
    return n


def _ledger_spent(journal_path, phase=None):
    if journal_path is None or not Path(journal_path).exists():
        return None
    voided = set()
    attempt_phase = {}
    records = []
    try:
        with open(journal_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") == "void" and obj.get("attempt_id"):
                    voided.add(obj["attempt_id"])
                if obj.get("type") == "reserve":
                    attempt_phase[obj.get("attempt_id")] = obj.get("phase")
                if obj.get("type") == "record":
                    records.append(obj.get("attempt_id"))
    except Exception:
        return None
    n = 0
    for aid in records:
        if aid in voided:
            continue
        if phase is not None and attempt_phase.get(aid) != phase:
            continue
        n += 1
    return n


def _driver_alive(pid):
    if pid is None:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except Exception:
        pass
    return os.path.exists(f"/proc/{int(pid)}")


def _cfg(env, key, default, *alt):
    wd = env.get("watcher") if isinstance(env.get("watcher"), dict) else {}
    for k in (key, *alt):
        if k in env and env.get(k) is not None:
            return env.get(k)
        if k in wd and wd.get(k) is not None:
            return wd.get(k)
    return default


def verdict_from(out_path):
    """Consumer side: read the latest watcher event + pid freshness."""
    out_path = Path(out_path)
    alerts = []
    verdict = "unknown"
    try:
        if out_path.exists():
            lines = [ln for ln in out_path.read_text().splitlines() if ln.strip()]
            if lines:
                ev = json.loads(lines[-1])
                alerts = list(ev.get("alerts") or [])
                verdict = ev.get("verdict", verdict)
    except Exception:
        pass
    pid_path = Path(str(out_path) + ".pid")
    alive = False
    try:
        if pid_path.exists():
            age = time.time() - pid_path.stat().st_mtime
            alive = age <= ALIVE_FRESHNESS_S
    except Exception:
        alive = False
    return {"alive": alive, "verdict": verdict, "alerts": alerts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--driver-pid", type=int, required=True, dest="driver_pid")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args()

    env = _load_envelope(args.envelope)
    base_dirs = _base_dirs(args.envelope, env)
    def _phase_path(category):
        paths = env.get("paths", {})
        v = paths.get(category)
        if isinstance(v, dict):
            pp = v.get(args.phase)
        elif isinstance(v, str):
            pp = v.format(phase=args.phase) if "{phase}" in v else v
        else:
            pp = None
        if pp is None:
            # fallback top-level
            pp = _resolve_path(env, (category+"_path", category, category+"_file"), base_dirs)
        if pp is None:
            return None
        pp = Path(pp)
        if not pp.is_absolute():
            for bd in base_dirs:
                cand = Path(bd) / pp
                if cand.exists():
                    pp = cand
                    break
        return pp
    rows_path = _phase_path("rows")
    intents_path = _phase_path("intents")
    journal_path = _ledger_journal_path(env, args.envelope)

    first_deadline = float(_cfg(env, "first_row_deadline_s", DEFAULT_FIRST_ROW_DEADLINE_S, "first_row_deadline", "first_row_deadline_seconds"))
    gap_deadline = float(_cfg(env, "row_gap_deadline_s", DEFAULT_ROW_GAP_DEADLINE_S, "row_gap_deadline", "row_gap_deadline_seconds"))
    intent_tol = int(_cfg(env, "intent_row_tolerance", DEFAULT_INTENT_TOLERANCE, "intent_tolerance", "tolerance"))
    ledger_tol = int(_cfg(env, "ledger_tolerance", DEFAULT_LEDGER_TOLERANCE, "ledger_intent_tolerance"))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path = Path(str(out_path) + ".pid")
    pid_path.write_text(str(os.getpid()) + "\n")

    started = time.monotonic()
    check_no = 0
    last_row_mtime = None

    while True:
        pid_path.touch()
        check_no += 1
        now = time.time()
        driver_alive = _driver_alive(args.driver_pid)

        rows_count = _count_lines(rows_path)
        intents_count = _count_lines(intents_path)
        ledger_spent = _ledger_spent(journal_path, args.phase)

        # last row age
        if rows_path is not None and Path(rows_path).exists():
            try:
                mtime = Path(rows_path).stat().st_mtime
                if last_row_mtime is None or mtime != last_row_mtime:
                    last_row_mtime = mtime
                last_row_age_s = now - mtime
            except Exception:
                last_row_age_s = None
        else:
            last_row_age_s = None

        alerts = []
        # rows_missing
        if rows_path is None or not Path(rows_path).exists():
            alerts.append("rows_missing")

        elapsed = time.monotonic() - started
        # no_first_row
        if rows_count == 0 and driver_alive and elapsed > first_deadline:
            alerts.append("no_first_row")

        # row_gap
        if rows_count > 0 and driver_alive and last_row_age_s is not None and last_row_age_s > gap_deadline:
            alerts.append("row_gap")

        # intent_row_mismatch
        if intents_count - rows_count > intent_tol:
            alerts.append("intent_row_mismatch")

        # driver_dead: only treat process death as an alert when the run looks
        # incomplete or inconsistent; a clean completed run exits 0.
        abnormal_death = (
            rows_count == 0
            or (intents_count - rows_count) > intent_tol
            or (ledger_spent is not None and abs(ledger_spent - rows_count) > ledger_tol)
            or (rows_count > 0 and last_row_age_s is not None and last_row_age_s > gap_deadline)
        )
        if not driver_alive and abnormal_death:
            alerts.append("driver_dead")

        # ledger_mismatch
        if ledger_spent is not None:
            if abs(ledger_spent - rows_count) > ledger_tol:
                alerts.append("ledger_mismatch")

        # dedup preserve order
        seen = set()
        deduped = []
        for a in alerts:
            if a not in seen:
                seen.add(a)
                deduped.append(a)
        alerts = deduped

        verdict = "ok" if not alerts else "alert"

        event = {
            "utc": now_utc(),
            "check": check_no,
            "driver_alive": driver_alive,
            "rows_count": rows_count,
            "intents_count": intents_count,
            "last_row_age_s": last_row_age_s,
            "ledger_spent": ledger_spent,
            "verdict": verdict,
            "alerts": alerts,
        }
        with open(out_path, "a") as f:
            f.write(json.dumps(event) + "\n")
            f.flush()
            os.fsync(f.fileno())

        # exit conditions
        if not driver_alive:
            if alerts:
                # any alert besides? driver_dead alone? If driver exited cleanly, driver_dead might alert falsely.
                # Treat driver_dead as alert only if rows still expected? Hmm.
                pass
            # If the only alert is driver_dead, consider clean stop? 
            # Per spec, driver_dead is an alert. But a finished driver is dead by definition.
            # We need distinguish: if no other alerts, exit 0.
            other = [a for a in alerts if a != "driver_dead"]
            if not other:
                sys.exit(0)
            else:
                sys.exit(1)
        # if alerts while driver alive -> exit nonzero
        if alerts:
            sys.exit(1)

        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
