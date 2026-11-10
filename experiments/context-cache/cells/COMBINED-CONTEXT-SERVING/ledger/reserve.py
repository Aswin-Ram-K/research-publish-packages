#!/usr/bin/env python3
"""Reserve a model-request allowance for the COMBINED-CONTEXT-SERVING experiment.

Atomic across worktrees/processes: an exclusive flock is taken on the authoritative
ledger file itself (absolute path). Remaining is read from the ledger; a shared
reservation registry beside the ledger tracks already-reserved counts so two
processes cannot both reserve against the same balance. The local cell copy is a
mirror of the authoritative per-run record.

Usage:
  python3 reserve.py --run-id <id> --count <n> [--dry-run]
"""
import argparse
import fcntl
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_LEDGER = "/home/zer0null/research extractor/experiments/ptr-engine/measure/REQUEST-LEDGER.json"
OPERATOR_CAP = 2000
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def ledger_path():
    return os.environ.get("CCS_LEDGER_PATH", DEFAULT_LEDGER)


def shared_registry_path(lp):
    return os.path.join(os.path.dirname(os.path.abspath(lp)), "RESERVATIONS.json")


def shared_record_path(lp, run_id):
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in run_id)
    return os.path.join(os.path.dirname(os.path.abspath(lp)), "RESERVATION-%s.json" % safe)


def read_json(path, default):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        return default
    except Exception:
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lp = ledger_path()
    if args.count <= 0:
        print("refused: count must be > 0", file=sys.stderr)
        sys.exit(3)

    # lock on the authoritative ledger path itself
    with open(lp, "r") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            with open(lp, "rb") as f:
                ledger_bytes = f.read()
            ledger = json.loads(ledger_bytes)
            ledger_sha = hashlib.sha256(ledger_bytes).hexdigest()
            remaining = int(ledger.get("remaining", 0))

            reg_path = shared_registry_path(lp)
            registry = read_json(reg_path, {"reservations": []})
            if not isinstance(registry, dict) or "reservations" not in registry:
                registry = {"reservations": []}
            reservations = registry.get("reservations", [])
            if not isinstance(reservations, list):
                reservations = []

            # refuse duplicate run id in shared registry
            for r in reservations:
                if isinstance(r, dict) and r.get("run_id") == args.run_id:
                    print("refused: run_id already reserved: %s" % args.run_id, file=sys.stderr)
                    sys.exit(4)

            reserved_total = 0
            for r in reservations:
                if isinstance(r, dict):
                    reserved_total += int(r.get("granted_count", 0) or 0)
            available = remaining - reserved_total
            if available < args.count:
                print("refused: ledger available %d < requested %d (remaining=%d reserved=%d)" % (
                    available, args.count, remaining, reserved_total), file=sys.stderr)
                sys.exit(4)

            granted = min(args.count, OPERATOR_CAP, available, remaining)
            if remaining <= OPERATOR_CAP and remaining <= args.count:
                bound = "ledger_remaining"
            elif OPERATOR_CAP <= remaining and OPERATOR_CAP <= args.count:
                bound = "operator_cap_2000"
            else:
                bound = "requested_count"

            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            record = {
                "run_id": args.run_id,
                "requested_count": args.count,
                "granted_count": granted,
                "bound_applied": bound,
                "operator_cap": OPERATOR_CAP,
                "ledger_path": lp,
                "ledger_sha256": ledger_sha,
                "ledger_remaining_at_reservation": remaining,
                "reserved_total_before": reserved_total,
                "available_before": available,
                "timestamp_utc": now,
                "dry_run": bool(args.dry_run),
            }

            if args.dry_run:
                print("dry-run: granted=%d bound=%s remaining=%d available=%d" % (granted, bound, remaining, available))
                sys.exit(0)

            # write authoritative per-run record beside the ledger
            auth_path = shared_record_path(lp, args.run_id)
            if os.path.exists(auth_path):
                print("refused: reservation record already exists: %s" % auth_path, file=sys.stderr)
                sys.exit(4)
            with open(auth_path, "w") as f:
                json.dump(record, f, indent=2)
                f.write("\n")

            # update shared registry
            reservations.append(record)
            registry["reservations"] = reservations
            with open(reg_path, "w") as f:
                json.dump(registry, f, indent=2)
                f.write("\n")

            # mirror to local cell copy
            out_path = os.path.join(OUT_DIR, "RESERVATION-%s.json" % args.run_id)
            if os.path.exists(out_path):
                # overwrite mirror to keep authoritative truth
                pass
            with open(out_path, "w") as f:
                json.dump(record, f, indent=2)
                f.write("\n")

            print(granted)
            sys.exit(0)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    main()
