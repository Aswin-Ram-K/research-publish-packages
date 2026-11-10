#!/usr/bin/env python3
"""Read-only supervisor for a live experiment run.

Polls only files and process liveness. Never HTTP, never writes rows.
Appends one JSON event per check to --out.
"""
import argparse, json, os, sys, time, datetime, subprocess


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def count_rows(path):
    n = 0
    statuses = []
    if not os.path.exists(path):
        return 0, []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                n += 1
                try:
                    obj = json.loads(line)
                    st = obj.get("status")
                    if st is not None:
                        statuses.append(st)
                except Exception:
                    pass
    except Exception:
        pass
    err = sum(1 for s in statuses[-3:]) if False else 0
    # count error rows among last 3 new
    return n, statuses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--expect-exit", type=int, default=None)
    ap.add_argument("--stall-minutes", type=float, default=10.0)
    ap.add_argument("--deadline-utc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval-seconds", type=float, default=120.0)
    args = ap.parse_args()

    # process liveness mode
    expect_exit = args.expect_exit is not None
    target_pid = args.pid

    last_rows = None
    last_change_time = time.time()
    consecutive_err = 0
    last_statuses_len = 0
    seen_statuses = []
    terminal_marker_seen = False
    deadline = datetime.datetime.fromisoformat(args.deadline_utc.replace("Z", "+00:00"))

    # ensure out dir
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    while True:
        ts = now_utc()
        rcount, statuses = count_rows(args.rows)
        # delta since last check
        if last_rows is None:
            delta = rcount
        else:
            delta = rcount - last_rows

        # track error rows (status != 200) among NEW rows
        new_statuses = statuses[last_statuses_len:] if len(statuses) >= last_statuses_len else statuses
        # simpler: recompute consecutive trailing non-200
        trailing = []
        for s in reversed(statuses):
            if s != 200:
                trailing.insert(0, s)
            else:
                break
        # consecutive non-200 at tail
        consec = 0
        for s in reversed(statuses):
            if s != 200:
                consec += 1
            else:
                break

        # error-row count total
        err_count = sum(1 for s in statuses if s != 200)

        # process exit
        exit_status = None
        alive = True
        if target_pid is not None:
            try:
                os.kill(target_pid, 0)
                alive = True
            except ProcessLookupError:
                alive = False
            except Exception:
                alive = True
            # check /proc
            if not os.path.exists(f"/proc/{target_pid}"):
                alive = False
        # if expect-exit mode, no pid; treat process as "the driver job" unknown -> exit via marker only
        # We'll handle exit status via log marker or external; here if pid given and gone, mark vanished

        # log marker
        log_text = ""
        if os.path.exists(args.log):
            try:
                with open(args.log) as f:
                    log_text = f.read()
            except Exception:
                pass
        if "DONE" in log_text or "terminal" in log_text.lower():
            terminal_marker_seen = True
        # also common markers
        if "COMPLETE" in log_text.upper():
            terminal_marker_seen = True

        # determine exit status of pid if not alive
        if target_pid is not None and not alive:
            # try to get exit code? unknown
            exit_status = "gone"

        alerts = []
        if not os.path.exists(args.rows):
            alerts.append("NO_ROWS_YET")
        # PROCESS_EXIT_NONZERO: if pid gone and we expected nonzero? We can't know code. Handle scenario where process exits 1: simulate by log marker? 
        # The spec: fire PROCESS_EXIT_NONZERO when process exits nonzero. We detect via pid gone AND a sentinel file? 
        # For offline proof, scenario provides a pid that exits 1. We'll detect process gone + a ".exitcode" sidecar or check.
        # Support sidecar: <log>.exitcode containing code.
        exit_code = None
        sidecar = args.log + ".exitcode"
        if os.path.exists(sidecar):
            try:
                exit_code = int(open(sidecar).read().strip())
            except Exception:
                pass
        if exit_code is not None and exit_code != 0:
            alerts.append("PROCESS_EXIT_NONZERO")
        # PROCESS_VANISHED: pid disappeared without exit code recorded
        if target_pid is not None and not alive and exit_code is None:
            alerts.append("PROCESS_VANISHED")
        # STALL_NO_ROWS (including before any row exists, once driver is known running)
        if rcount == 0:
            alerts.append("NO_ROWS_YET")
            if last_change_time is None:
                last_change_time = time.time()
            # driver known to be running: pid given and alive, or no pid (assume running)
            driver_running = True
            if target_pid is not None:
                driver_running = alive
            if driver_running and (time.time() - last_change_time >= args.stall_minutes * 60):
                alerts.append("STALL_NO_ROWS")
        elif delta == 0 and rcount > 0:
            if last_change_time is None:
                last_change_time = time.time()
            if time.time() - last_change_time >= args.stall_minutes * 60:
                alerts.append("STALL_NO_ROWS")
        else:
            if delta != 0:
                last_change_time = time.time()
        # ERROR_RATE
        if consec >= 3:
            alerts.append("ERROR_RATE")
        # DEADLINE
        if datetime.datetime.now(datetime.timezone.utc) >= deadline:
            alerts.append("DEADLINE")
        # DONE
        if terminal_marker_seen:
            alerts.append("DONE")
        # process exited zero
        if exit_code == 0:
            alerts.append("DONE")

        # update state
        if last_rows is None or rcount != last_rows:
            last_change_time = last_change_time if (rcount == last_rows) else time.time()
        last_rows = rcount
        last_statuses_len = len(statuses)

        event = {
            "timestamp": ts,
            "rows": rcount,
            "delta": delta,
            "error_rows": err_count,
            "exit_status": exit_status if exit_status is not None else ("alive" if (target_pid is None or alive) else "gone"),
            "alerts": alerts,
        }
        with open(args.out, "a") as f:
            f.write(json.dumps(event) + "\n")

        # decide stop
        if alerts and alerts != ["NO_ROWS_YET"]:
            # if DONE alone, exit 0; else exit 1
            if alerts == ["DONE"]:
                sys.exit(0)
            # for any alert, stop polling
            sys.exit(0)

        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
