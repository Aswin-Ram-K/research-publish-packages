#!/usr/bin/env python3
"""Campaign ledger: exclusive, append-only 1500-call authority."""
import argparse
import fcntl
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

DEFAULT_CAMPAIGN_JSON = "/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/ledger/campaign.json"
VALID_PHASES = ("preflight", "context", "prompt_format", "serving", "holdout", "contingency")
VALID_OUTCOMES = ("ok", "failed", "retry", "no_row")
LOCK_TIMEOUT_SEC = 10.0


class LedgerError(Exception):
    pass


def _campaign_json_path(args):
    p = getattr(args, "campaign_json", None)
    if p:
        return p
    env = os.environ.get("CAMPAIGN_JSON")
    if env:
        return env
    return DEFAULT_CAMPAIGN_JSON


def load_campaign(args):
    p = _campaign_json_path(args)
    if not os.path.isfile(p):
        raise LedgerError("campaign json not found: %s" % p)
    try:
        with open(p, "rb") as f:
            raw = f.read()
        c = json.loads(raw)
    except Exception as e:
        raise LedgerError("unreadable campaign json %s: %s" % (p, e))
    if not isinstance(c, dict):
        raise LedgerError("campaign json not an object")
    if "total_cap" not in c or "phase_caps" not in c:
        raise LedgerError("campaign json missing caps")
    try:
        c["total_cap"] = int(c["total_cap"])
        c["phase_caps"] = {k: int(v) for k, v in c["phase_caps"].items()}
    except Exception as e:
        raise LedgerError("bad cap types: %s" % e)
    c["_path"] = p
    c["_base_dir"] = os.path.dirname(os.path.abspath(p))
    # allow ledger_dir override
    ld = getattr(args, "ledger_dir", None) or os.environ.get("CAMPAIGN_LEDGER_DIR")
    if ld:
        c["_base_dir"] = os.path.abspath(ld)
    # lock path
    lp = getattr(args, "lock_path", None) or os.environ.get("CAMPAIGN_LOCK_PATH")
    if lp:
        c["_lock_path"] = os.path.abspath(lp)
    else:
        lb = c.get("lock_basename", "campaign.lock")
        c["_lock_path"] = os.path.join(c["_base_dir"], lb)
    jb = c.get("journal_basename", "journal.jsonl")
    c["_journal_path"] = os.path.join(c["_base_dir"], jb)
    c["_index_path"] = os.path.join(c["_base_dir"], "journal.index.json")
    return c


def acquire_lock(lock_path):
    if not os.path.exists(lock_path):
        raise LedgerError("lock file missing: %s" % lock_path)
    try:
        f = open(lock_path, "r+")
    except Exception as e:
        raise LedgerError("cannot open lock file %s: %s" % (lock_path, e))
    deadline = time.time() + LOCK_TIMEOUT_SEC
    while True:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return f
        except (BlockingIOError, OSError):
            if time.time() >= deadline:
                try:
                    f.close()
                except Exception:
                    pass
                raise LedgerError("lock timeout: %s" % lock_path)
            time.sleep(0.05)


def read_journal(journal_path):
    if not os.path.exists(journal_path):
        return []
    events = []
    try:
        with open(journal_path, "r") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if line.strip() == "":
                    continue
                try:
                    obj = json.loads(line)
                except Exception as e:
                    raise LedgerError("corrupted journal line: %s" % e)
                if not isinstance(obj, dict):
                    raise LedgerError("journal line not an object")
                if "type" not in obj:
                    raise LedgerError("journal line missing type")
                events.append(obj)
    except LedgerError:
        raise
    except Exception as e:
        raise LedgerError("cannot read journal %s: %s" % (journal_path, e))
    return events


def _derived(events):
    reserves = [e for e in events if e.get("type") == "reserve"]
    records = [e for e in events if e.get("type") == "record"]
    voids = [e for e in events if e.get("type") == "void"]
    # reject unknown types
    for e in events:
        if e.get("type") not in ("reserve", "record", "void"):
            raise LedgerError("unknown journal event type: %s" % e.get("type"))
    # validate void events
    for e in voids:
        aid = e.get("attempt_id")
        if not isinstance(aid, str) or not aid:
            raise LedgerError("void event missing attempt_id")
        if "reason" not in e:
            raise LedgerError("void event missing reason")
    # duplicate attempt ids among reserves
    ids = [e.get("attempt_id") for e in reserves]
    if any(not isinstance(x, str) or not x for x in ids):
        raise LedgerError("reserve event missing attempt_id")
    if len(set(ids)) != len(ids):
        raise LedgerError("duplicate attempt_id in journal")
    # records must reference known attempts
    known = set(ids)
    for e in records:
        aid = e.get("attempt_id")
        if aid not in known:
            raise LedgerError("record references unknown attempt_id: %s" % aid)
        if e.get("outcome") not in VALID_OUTCOMES:
            raise LedgerError("invalid outcome: %s" % e.get("outcome"))
    attempt_phase = {e.get("attempt_id"): e.get("phase") for e in reserves}
    known_ids = set(e.get("attempt_id") for e in reserves)
    voided_map = {}
    for e in voids:
        aid = e.get("attempt_id")
        if aid in known_ids:
            voided_map[aid] = e.get("reason")
    voided_ids = set(voided_map.keys())

    covered_all = set(e.get("attempt_id") for e in records)
    covered = set(aid for aid in covered_all if aid not in voided_ids)

    # phase reserved counts (excluding voided)
    phase_reserved = {p: 0 for p in VALID_PHASES}
    for e in reserves:
        if e.get("attempt_id") in voided_ids:
            continue
        ph = e.get("phase")
        if ph not in phase_reserved:
            raise LedgerError("unknown phase in journal: %s" % ph)
        phase_reserved[ph] += 1
    # phase spent (record events) by attempt phase (excluding voided)
    phase_spent = {p: 0 for p in VALID_PHASES}
    outcome_counts = {o: 0 for o in VALID_OUTCOMES}
    for e in records:
        aid = e.get("attempt_id")
        if aid in voided_ids:
            continue
        ph = attempt_phase.get(aid)
        if ph in phase_spent:
            phase_spent[ph] += 1
        outcome_counts[e.get("outcome")] += 1

    reserved_nonvoid = sum(1 for e in reserves if e.get("attempt_id") not in voided_ids)
    spent_nonvoid = sum(1 for e in records if e.get("attempt_id") not in voided_ids)

    # voided_by_reason breakdown
    voided_by_reason = {}
    for aid, reason in voided_map.items():
        voided_by_reason[reason] = voided_by_reason.get(reason, 0) + 1

    return {
        "events": events,
        "reserves": reserves,
        "records": records,
        "voids": voids,
        "reserved_total": reserved_nonvoid,
        "spent_events": spent_nonvoid,
        "covered_attempts": len(covered),
        "unrecorded": reserved_nonvoid - len(covered),
        "phase_reserved": phase_reserved,
        "phase_spent": phase_spent,
        "outcome_counts": outcome_counts,
        "attempt_phase": attempt_phase,
        "attempt_ids": sorted(ids),
        "voided_ids": sorted(voided_ids),
        "voided_map": voided_map,
        "voided_count": len(voided_ids),
        "voided_by_reason": voided_by_reason,
        "all_reserved_ids": sorted(known_ids),
    }


def index_check(c, derived):
    idx = c["_index_path"]
    if not os.path.exists(idx):
        return
    try:
        with open(idx, "r") as f:
            index = json.load(f)
    except Exception as e:
        raise LedgerError("unreadable index %s: %s" % (idx, e))
    if not isinstance(index, dict):
        raise LedgerError("index not an object")
    if index.get("reserved") != derived["reserved_total"]:
        raise LedgerError("index/journal count mismatch: reserved %s vs %s" % (index.get("reserved"), derived["reserved_total"]))
    if index.get("record_events") != derived["spent_events"]:
        raise LedgerError("index/journal count mismatch: record_events %s vs %s" % (index.get("record_events"), derived["spent_events"]))
    if set(index.get("attempt_ids", [])) != set(derived["attempt_ids"]):
        raise LedgerError("index/journal attempt_id set mismatch")


def write_index(c, derived):
    idx = c["_index_path"]
    payload = {
        "reserved": derived["reserved_total"],
        "record_events": derived["spent_events"],
        "covered": derived["covered_attempts"],
        "attempt_ids": derived["attempt_ids"],
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tmp = idx + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, idx)


def append_event(c, event):
    jp = c["_journal_path"]
    with open(jp, "a") as f:
        f.write(json.dumps(event) + "\n")
        f.flush()
        os.fsync(f.fileno())


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def cmd_reserve(args, c):
    lockf = acquire_lock(c["_lock_path"])
    try:
        events = read_journal(c["_journal_path"])
        derived = _derived(events)
        index_check(c, derived)
        phase = args.phase
        if phase not in VALID_PHASES:
            raise LedgerError("unknown phase: %s" % phase)
        # caps
        total_cap = c["total_cap"]
        phase_cap = c["phase_caps"].get(phase)
        if phase_cap is None:
            raise LedgerError("no phase cap for %s" % phase)
        reserved_total = derived["reserved_total"]
        phase_reserved = derived["phase_reserved"][phase]
        if reserved_total >= total_cap:
            raise LedgerError("total cap exhausted: %d/%d" % (reserved_total, total_cap))
        if phase_reserved >= phase_cap:
            raise LedgerError("phase cap exhausted for %s: %d/%d" % (phase, phase_reserved, phase_cap))
        # generate attempt id
        attempt_id = str(uuid.uuid4())
        ordinal = reserved_total + 1
        event = {
            "schema": "cs.ledger.intent/1",
            "type": "reserve",
            "attempt_id": attempt_id,
            "utc": now_utc(),
            "phase": phase,
            "label": args.label,
            "ordinal": ordinal,
        }
        if args.dry_run:
            # validate only; print would-be id
            print(attempt_id)
            return
        append_event(c, event)
        # recompute derived from file to be safe
        new_events = read_journal(c["_journal_path"])
        new_derived = _derived(new_events)
        write_index(c, new_derived)
        print(attempt_id)
    finally:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lockf.close()


def cmd_record(args, c):
    lockf = acquire_lock(c["_lock_path"])
    try:
        events = read_journal(c["_journal_path"])
        derived = _derived(events)
        index_check(c, derived)
        aid = args.attempt_id
        if aid not in derived["attempt_ids"]:
            raise LedgerError("unknown attempt_id: %s" % aid)
        outcome = args.outcome
        if outcome not in VALID_OUTCOMES:
            raise LedgerError("invalid outcome: %s" % outcome)
        usage = None
        if args.usage_json:
            try:
                usage = json.loads(args.usage_json)
            except Exception as e:
                raise LedgerError("bad usage-json: %s" % e)
        event = {
            "schema": "cs.ledger.outcome/1",
            "type": "record",
            "attempt_id": aid,
            "utc": now_utc(),
            "outcome": outcome,
            "usage": usage,
        }
        if args.dry_run:
            return
        append_event(c, event)
        new_events = read_journal(c["_journal_path"])
        new_derived = _derived(new_events)
        write_index(c, new_derived)
    finally:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lockf.close()


def _ledger_label(c):
    base = c["_base_dir"]
    default_base = os.path.dirname(os.path.abspath(DEFAULT_CAMPAIGN_JSON))
    if os.path.abspath(base) == os.path.abspath(default_base):
        return "campaign:" + base
    return "tmp:" + base


def build_status(c, include_voided=False):
    events = read_journal(c["_journal_path"])
    derived = _derived(events)
    index_check(c, derived)
    total_cap = c["total_cap"]
    reserved_total = derived["reserved_total"]
    phase_status = {}
    for p in VALID_PHASES:
        cap = c["phase_caps"].get(p, 0)
        r = derived["phase_reserved"][p]
        s = derived["phase_spent"][p]
        phase_status[p] = {
            "cap": cap,
            "reserved": r,
            "spent": s,
            "remaining": cap - r,
        }
    st = {
        "schema": "cs.ledger.status/1",
        "ledger": _ledger_label(c),
        "total_cap": total_cap,
        "total_reserved": reserved_total,
        "total_spent": derived["spent_events"],
        "total_remaining": total_cap - reserved_total,
        "total_unrecorded": derived["unrecorded"],
        "covered_attempts": derived["covered_attempts"],
        "voided": derived["voided_count"],
        "voided_by_reason": derived["voided_by_reason"],
        "per_phase": phase_status,
        "outcomes": derived["outcome_counts"],
        "journal_lines": len(events),
    }
    if include_voided:
        st["voided_attempt_ids"] = derived["voided_ids"]
        st["voided_details"] = [
            {"attempt_id": aid, "reason": derived["voided_map"][aid],
             "utc": next((e.get("utc") for e in derived["voids"] if e.get("attempt_id") == aid), None)}
            for aid in derived["voided_ids"]
        ]
    return st


def cmd_status(args, c):
    lockf = acquire_lock(c["_lock_path"])
    try:
        st = build_status(c, include_voided=getattr(args, "include_voided", False))
    finally:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lockf.close()
    if args.json:
        print(json.dumps(st, indent=2))
    else:
        print("ledger=%s reserved=%d spent=%d remaining=%d unrecorded=%d voided=%d" % (
            st["ledger"], st["total_reserved"], st["total_spent"], st["total_remaining"], st["total_unrecorded"], st["voided"]))


def _select_void_targets(args, c, events, derived):
    reserves = derived["reserves"]
    by_id = {e.get("attempt_id"): e for e in reserves}
    targets = set()
    # attempt-id
    aids = getattr(args, "attempt_id", None) or []
    if isinstance(aids, str):
        aids = [aids]
    for a in aids:
        if a not in by_id:
            raise LedgerError("unknown attempt_id: %s" % a)
        targets.add(a)
    # label-prefix (guarded: never void a non-already-voided, non-synthetic attempt)
    prefixes = getattr(args, "label_prefix", None) or []
    if isinstance(prefixes, str):
        prefixes = [prefixes]
    voided_ids = set(derived["voided_ids"])
    for p in prefixes:
        for e in reserves:
            if str(e.get("label", "")).startswith(p):
                aid = e.get("attempt_id")
                label = str(e.get("label", ""))
                synthetic_marked = "synthetic" in label.lower()
                if aid not in voided_ids and not synthetic_marked:
                    raise LedgerError("refusing to void non-voided non-synthetic attempt via label-prefix: %s (%s)" % (aid, label))
                targets.add(aid)
    # select json
    sel = getattr(args, "select", None)
    if sel:
        try:
            obj = json.loads(sel)
        except Exception as e:
            raise LedgerError("bad --select json: %s" % e)
        # normalize to object
        if isinstance(obj, list):
            # each item: attempt id or label or prefix
            for item in obj:
                if isinstance(item, str):
                    if item in by_id:
                        targets.add(item)
                    else:
                        # label exact or prefix
                        matched = False
                        for e in reserves:
                            if e.get("label") == item:
                                targets.add(e.get("attempt_id"))
                                matched = True
                        if not matched:
                            for e in reserves:
                                if str(e.get("label", "")).startswith(item):
                                    targets.add(e.get("attempt_id"))
                elif isinstance(item, dict):
                    _apply_select_obj(item, reserves, by_id, targets)
        elif isinstance(obj, dict):
            _apply_select_obj(obj, reserves, by_id, targets)
        else:
            raise LedgerError("bad --select json: expected list or object")
    return targets


def _apply_select_obj(obj, reserves, by_id, targets):
    # attempt ids
    for key in ("attempt_ids", "attempt_id", "ids", "id"):
        val = obj.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            val = [val]
        for a in val:
            if a not in by_id:
                raise LedgerError("unknown attempt_id: %s" % a)
            targets.add(a)
    # labels exact
    for key in ("labels", "label"):
        val = obj.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            val = [val]
        for lab in val:
            for e in reserves:
                if e.get("label") == lab:
                    targets.add(e.get("attempt_id"))
    # label prefixes
    for key in ("label_prefixes", "label_prefix", "prefixes", "prefix"):
        val = obj.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            val = [val]
        for p in val:
            for e in reserves:
                if str(e.get("label", "")).startswith(p):
                    targets.add(e.get("attempt_id"))


def cmd_void(args, c):
    reason = args.reason
    if not reason:
        raise LedgerError("missing --reason")
    lockf = acquire_lock(c["_lock_path"])
    try:
        events = read_journal(c["_journal_path"])
        derived = _derived(events)
        index_check(c, derived)
        targets = _select_void_targets(args, c, events, derived)
        if not targets:
            # nothing to void
            pass
        voided_ids = set(derived["voided_ids"])
        to_void = [aid for aid in sorted(targets) if aid not in voided_ids]
        for aid in to_void:
            event = {
                "schema": "cs.ledger.void/1",
                "type": "void",
                "attempt_id": aid,
                "reason": reason,
                "utc": now_utc(),
            }
            append_event(c, event)
        # recompute
        new_events = read_journal(c["_journal_path"])
        new_derived = _derived(new_events)
        write_index(c, new_derived)
        print(json.dumps({"voided_now": len(to_void), "already_voided": len(targets) - len(to_void), "total_voided": new_derived["voided_count"]}))
    finally:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lockf.close()


def main():
    ap = argparse.ArgumentParser(description="Campaign ledger")
    ap.add_argument("--campaign-json", default=None)
    ap.add_argument("--ledger-dir", default=None)
    ap.add_argument("--lock-path", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("reserve")
    r.add_argument("--phase", required=True)
    r.add_argument("--label", required=True)
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=cmd_reserve)

    rec = sub.add_parser("record")
    rec.add_argument("--attempt-id", required=True)
    rec.add_argument("--outcome", required=True)
    rec.add_argument("--usage-json", default=None)
    rec.add_argument("--dry-run", action="store_true")
    rec.set_defaults(func=cmd_record)

    st = sub.add_parser("status")
    st.add_argument("--json", action="store_true")
    st.add_argument("--include-voided", action="store_true")
    st.set_defaults(func=cmd_status)

    vo = sub.add_parser("void")
    vo.add_argument("--attempt-id", action="append", default=None)
    vo.add_argument("--label-prefix", action="append", default=None)
    vo.add_argument("--select", default=None)
    vo.add_argument("--reason", required=True)
    vo.set_defaults(func=cmd_void)

    args = ap.parse_args()
    try:
        c = load_campaign(args)
        args.func(args, c)
    except LedgerError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
