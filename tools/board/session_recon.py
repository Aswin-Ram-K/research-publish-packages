#!/usr/bin/env python3
"""session_recon.py — read-only reconnaissance of DSH sessions for the current workspace.

Classifies every session under ~/.dsh/sessions/<encoded-cwd>/ by walking its
parentSession chain and cross-referencing the task-board ledger. Writes a JSON
report to state/logs/session-recon.json. Never writes under ~/.dsh.

Exit code: 0 iff no offender of any kind is found:
  - delegated-from-card: a subagent whose root ancestor is a board execution
    (card-subagent) that is not attached to its own card and not waived.
  - settled-lag: a live (non-archived), non-scheduled card whose latest
    execution has ended but the card is not settled (still todo/running/backlog).
  - uncarded board execution: a root non-subagent session with no card mapping
    that has a card-subagent descendant.

Archived cards are off the board — the archive action never rewrote `status`, so
an archived card may still read todo/running/failed after its last execution
ended. That is the archive doing its job, not a lagging card: archived cards are
reported under `archivedWithSettledExecution` and never raise the exit code.
A false red makes the exit code meaningless, which is worse than no check.

Scheduled cards keep their own lifecycle (pending next run) and are likewise not
settled-lag.
Otherwise 1.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

DSH_HOME = os.path.expanduser("~/.dsh")
SESSIONS_ROOT = os.path.join(DSH_HOME, "sessions")
LEDGER_PATH = os.path.join(DSH_HOME, "task-board", "ledger-v2.json")
REPORT_PATH = os.path.join("state", "logs", "session-recon.json")
WAIVER_PATH = os.path.join("state", "logs", "session-recon-waivers.json")

STALE_MINUTES = 30


def norm_id(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if s.startswith("session-"):
        s = s[len("session-"):]
    return s


def read_session_jsonl(path):
    """Return dict of first record (session header) via zstd CLI."""
    if not os.path.isfile(path):
        return None
    try:
        out = subprocess.run(
            ["zstd", "-dc", path],
            capture_output=True,
            timeout=30,
        )
        if out.returncode != 0:
            return None
        for line in out.stdout.split(b"\n"):
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        return None
    except Exception:
        return None


def find_encoded_dir(cwd):
    """Find the encoded sessions directory whose sessions report cwd == given."""
    if not os.path.isdir(SESSIONS_ROOT):
        return None
    for d in os.listdir(SESSIONS_ROOT):
        p = os.path.join(SESSIONS_ROOT, d)
        if not os.path.isdir(p):
            continue
        subdirs = [x for x in os.listdir(p) if os.path.isdir(os.path.join(p, x))]
        if not subdirs:
            continue
        sample = os.path.join(p, subdirs[0], "session.v4.jsonl.zstd")
        rec = read_session_jsonl(sample)
        if rec and rec.get("cwd") == cwd:
            return d
    return None


def load_ledger(path=LEDGER_PATH):
    tasks = []
    if os.path.isfile(path):
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                tasks = data.get("tasks", []) or []
            elif isinstance(data, list):
                tasks = data
        except Exception:
            tasks = []
    return tasks


def build_card_maps(tasks):
    """Return (session_to_cards dict, card_lookup dict).

    session_to_cards: normalized session id -> list of {cardId, title, via}
    card_lookup: card id -> title
    """
    session_to_cards = {}
    card_lookup = {}
    for t in tasks:
        card_id = t.get("id") or t.get("taskId")
        title = t.get("title") or t.get("name") or ""
        card_lookup[card_id] = title
        for e in (t.get("executions") or []):
            sid = e.get("sessionId")
            if sid:
                n = norm_id(sid)
                session_to_cards.setdefault(n, []).append(
                    {"cardId": card_id, "title": title, "via": "sessionId"}
                )
            ib = e.get("initiatedBy")
            if isinstance(ib, str) and (ib.startswith("session-") or "-" in ib):
                if ib.startswith("session-") or len(ib) >= 32:
                    n = norm_id(ib)
                    if n:
                        session_to_cards.setdefault(n, []).append(
                            {"cardId": card_id, "title": title, "via": "initiatedBy"}
                        )
    return session_to_cards, card_lookup


def has_session_id_mapping(mappings):
    return any(m.get("via") == "sessionId" for m in (mappings or []))


def load_waivers(path):
    result = {}
    if not os.path.isfile(path):
        return result
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return result
    entries = []
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        if isinstance(data.get("waivers"), list):
            entries = data["waivers"]
        elif isinstance(data.get("sessions"), list):
            entries = data["sessions"]
        else:
            for k, v in data.items():
                if isinstance(v, dict):
                    e = dict(v)
                    e.setdefault("session", k)
                    entries.append(e)
                else:
                    entries.append({"session": k, "reason": str(v), "date": ""})
    for e in entries:
        if not isinstance(e, dict):
            continue
        sid = e.get("session") or e.get("id") or e.get("sessionId")
        if not sid:
            continue
        n = norm_id(sid)
        result[n] = {
            "reason": str(e.get("reason", "") or ""),
            "date": str(e.get("date", "") or ""),
            "raw": e,
        }
    return result


def waiver_valid(w):
    return bool(w.get("reason", "").strip()) and bool(w.get("date", "").strip())


SETTLED_STATUSES = ("done", "failed", "cancelled", "completed")
# Why: an archived card is off the board, so its column value is frozen at
# whatever it read when it was archived. Grading that frozen value as a live
# lag made the reconciler red on cards nobody can act on.
# Note: `archivedAt` is truthy (epoch ms); text/null are falsy. Either way the
# key's presence with a truthy value means the card is archived.
ARCHIVED_REASON = (
    "archived card: off the board, its column is frozen at archive time; "
    "the archive action does not rewrite status"
)


def is_archived(task):
    return bool(task.get("archivedAt"))


def latest_execution(task):
    execs = task.get("executions") or []
    if not execs:
        return None
    return max(execs, key=lambda e: (e.get("startedAt") or e.get("endedAt") or 0))


def find_settled_lag(tasks):
    """Return (lagging, archived) lists.

    lagging: live, non-scheduled cards whose latest execution ended but which are
             not settled -> a real violation, counted in the exit code.
    archived: archived cards in the same shape -> recorded, never a violation.
    """
    lagging = []
    archived = []
    for t in tasks:
        card_id = t.get("id") or t.get("taskId")
        title = t.get("title") or t.get("name") or ""
        status = (t.get("status") or t.get("column") or "").lower()
        latest = latest_execution(t)
        if latest is None or not latest.get("endedAt"):
            continue
        if status in SETTLED_STATUSES:
            continue
        entry = {
            "cardId": card_id,
            "title": title,
            "status": status,
            "sessionId": latest.get("sessionId"),
        }
        # Scheduled cards have their own lifecycle (pending next run); not settled-lag.
        if t.get("schedule"):
            continue
        if is_archived(t):
            entry["reason"] = ARCHIVED_REASON
            entry["archivedAt"] = t.get("archivedAt")
            archived.append(entry)
            continue
        lagging.append(entry)
    return lagging, archived


def main():
    ap = argparse.ArgumentParser(description="Read-only session reconnaissance.")
    ap.add_argument("--cwd", default=None, help="Workspace cwd (default: os.getcwd())")
    ap.add_argument("--report", default=REPORT_PATH, help="Report output path")
    ap.add_argument("--waivers", default=WAIVER_PATH, help="Waivers file path")
    ap.add_argument("--ledger", default=LEDGER_PATH, help="Ledger file path")
    ap.add_argument("--live-minutes", type=int, default=30, dest="live_minutes",
                    help="Minutes within which a session transcript mtime counts as live (default 30)")
    ap.add_argument("--strict", action="store_true",
                    help="Also fail on historical (closed) card-subagent descendants")
    args = ap.parse_args()

    cwd = args.cwd or os.getcwd()
    report_path = args.report
    waiver_path = args.waivers
    ledger_path = args.ledger
    live_minutes = args.live_minutes
    strict = args.strict
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)

    encoded = find_encoded_dir(cwd)
    if encoded is None:
        print("session-recon: no encoded sessions dir found for cwd", file=sys.stderr)
        report = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "workspace": cwd,
            "encodedDir": None,
            "summary": {"total": 0, "byClass": {}, "attached": 0, "waived": 0,
                        "offenders": 0, "laggingCards": 0, "archived": 0, "exitCode": 0},
            "sessions": [],
            "offenders": [],
            "offenderDetails": [],
            "laggingCards": [],
            "archivedWithSettledExecution": [],
            "historicalDescendants": [],
        }
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print("session-recon: 0 sessions offenders=0 lagging=0 historical=0 exit=0")
        return 0

    base = os.path.join(SESSIONS_ROOT, encoded)

    records = {}
    session_dirs = []
    for d in os.listdir(base):
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        session_dirs.append(d)

    for d in session_dirs:
        p = os.path.join(base, d)
        fpath = os.path.join(p, "session.v4.jsonl.zstd")
        if not os.path.isfile(fpath):
            cands = [x for x in os.listdir(p) if x.endswith(".zstd")]
            if not cands:
                continue
            fpath = os.path.join(p, cands[0])
        rec = read_session_jsonl(fpath)
        if not rec:
            continue
        sid_raw = rec.get("id")
        sid_norm = norm_id(sid_raw)
        if not sid_norm:
            continue
        try:
            mtime = os.path.getmtime(fpath)
        except OSError:
            mtime = 0.0
        records[sid_norm] = {
            "rawId": sid_raw,
            "normId": sid_norm,
            "createdAt": rec.get("createdAt"),
            "cwd": rec.get("cwd"),
            "parentSession": rec.get("parentSession"),
            "origin": rec.get("origin"),
            "delegationDepth": rec.get("delegationDepth"),
            "mtime": mtime,
            "dir": d,
            "file": fpath,
        }

    tasks = load_ledger(ledger_path)
    session_to_cards, card_lookup = build_card_maps(tasks)
    waivers = load_waivers(waiver_path)

    now = time.time()
    stale_cutoff = now - STALE_MINUTES * 60

    def parent_norm(rec):
        return norm_id(rec.get("parentSession"))

    def walk_chain(start_norm):
        chain = []
        seen = set()
        cur = start_norm
        while cur is not None and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            rec = records.get(cur)
            if rec is None:
                break
            pn = parent_norm(rec)
            if not pn:
                break
            cur = pn
        return chain

    # First pass: classify each session.
    classifications = {}
    chains = {}
    for sid_norm in sorted(records.keys()):
        rec = records[sid_norm]
        chain = walk_chain(sid_norm)
        chains[sid_norm] = chain

        card_ancestor_pos = None
        card_ancestor_id = None
        for i, cid in enumerate(chain):
            mappings = session_to_cards.get(cid, [])
            if has_session_id_mapping(mappings):
                card_ancestor_pos = i
                card_ancestor_id = cid
                break

        stale = bool(rec["mtime"]) and rec["mtime"] < stale_cutoff

        if rec.get("origin") == "subagent" and card_ancestor_id is not None:
            cls = "card-subagent"
        elif stale:
            cls = "stale"
        elif rec.get("origin") == "subagent":
            cls = "user-subagent"
        else:
            mappings = session_to_cards.get(sid_norm, [])
            if has_session_id_mapping(mappings):
                cls = "board-execution"
            else:
                cls = "interactive"
        classifications[sid_norm] = cls

    # Second pass: settled-lag cards (live) and archived cards (recorded only).
    lagging_cards, archived_with_settled = find_settled_lag(tasks)

    # Third pass: uncarded board execution = root non-subagent session with no
    # card mapping (via sessionId) that has a card-subagent descendant.
    uncarded_offenders = set()
    for sid_norm in records:
        cls = classifications[sid_norm]
        if cls not in ("interactive", "board-execution"):
            continue
        mappings = session_to_cards.get(sid_norm, [])
        if has_session_id_mapping(mappings):
            continue
        # any descendant that is a card-subagent?
        has_card_sub = False
        for other, other_cls in classifications.items():
            if other == sid_norm or other_cls != "card-subagent":
                continue
            if sid_norm in chains.get(other, []):
                has_card_sub = True
                break
        if has_card_sub:
            uncarded_offenders.add(sid_norm)

    sessions_out = []
    offenders = []
    offender_details = []
    historical_descendants = []
    by_class = {"interactive": 0, "board-execution": 0, "card-subagent": 0,
                "user-subagent": 0, "stale": 0}
    attached_count = 0
    waived_count = 0

    for sid_norm in sorted(records.keys()):
        rec = records[sid_norm]
        chain = chains[sid_norm]
        cls = classifications[sid_norm]

        by_class[cls] = by_class.get(cls, 0) + 1

        attached = sid_norm in session_to_cards
        if attached:
            attached_count += 1

        w = waivers.get(sid_norm)
        waived = False
        if w is not None and waiver_valid(w):
            waived = True
            waived_count += 1

        card_ancestor_id = None
        for cid in chain:
            mappings = session_to_cards.get(cid, [])
            if has_session_id_mapping(mappings):
                card_ancestor_id = cid
                break

        resolved_cards = session_to_cards.get(card_ancestor_id, []) if card_ancestor_id else []
        if not resolved_cards and cls == "board-execution":
            resolved_cards = session_to_cards.get(sid_norm, [])
        card_obj = None
        if resolved_cards:
            c = resolved_cards[0]
            card_obj = {"id": c["cardId"], "title": c["title"]}

        mtime_iso = None
        if rec["mtime"]:
            try:
                mtime_iso = datetime.fromtimestamp(rec["mtime"], tz=timezone.utc).isoformat()
            except Exception:
                mtime_iso = None

        live = bool(rec["mtime"]) and rec["mtime"] >= (now - live_minutes * 60)

        # Determine offender status.
        offender_kind = None
        if cls == "card-subagent" and not attached and not waived:
            if live:
                offender_kind = "delegated-from-card"
            elif strict:
                offender_kind = "delegated-from-card"
        elif sid_norm in uncarded_offenders and not waived:
            offender_kind = "uncarded-board-execution"
        if offender_kind is not None:
            offenders.append(sid_norm)
            action = {
                "delegated-from-card": "re-card this work as its own board card; a unit must not spawn subagents",
                "uncarded-board-execution": "attach this session to a card or add a dated waiver",
            }[offender_kind]
            offender_details.append({
                "sessionId": sid_norm,
                "class": cls,
                "kind": offender_kind,
                "chain": chain,
                "card": card_obj,
                "action": action,
            })

        # Historical (closed) card-subagent descendants: recorded, not offenders
        # (unless --strict, in which case they are already in offenders above).
        if cls == "card-subagent" and not live:
            card_id = card_obj["id"] if card_obj else None
            historical_descendants.append({
                "sessionId": sid_norm,
                "class": cls,
                "chain": chain,
                "card": card_obj,
                "lastWrite": mtime_iso,
                "note": "covered by {}".format(card_id) if card_id else "covered by (unknown card)",
            })

        sessions_out.append({
            "id": rec["rawId"],
            "normalizedId": sid_norm,
            "createdAt": rec["createdAt"],
            "cwd": rec["cwd"],
            "parentSession": rec["parentSession"],
            "origin": rec["origin"],
            "delegationDepth": rec["delegationDepth"],
            "mtime": rec["mtime"],
            "mtimeIso": mtime_iso,
            "live": live,
            "chain": chain,
            "class": cls,
            "card": card_obj,
            "resolvedCards": resolved_cards,
            "attached": attached,
            "waived": waived,
            "waiver": w if w else None,
        })

    # Add lagging-card session ids to offenders? Track separately; exit code covers both.
    # Normalize before deduping: offenders already holds normalized ids, so a raw
    # "session-<uuid>" key here double-counted the same session (2 lagging cards
    # printed 4 offender lines).
    lagging_session_ids = []
    for lc in lagging_cards:
        sid = lc.get("sessionId")
        if sid:
            n = norm_id(sid)
            if n and n not in offenders:
                offenders.append(n)
                offender_details.append({
                    "sessionId": n,
                    "class": "settled-lag",
                    "kind": "settled-lag",
                    "chain": [n],
                    "card": {"id": lc["cardId"], "title": lc["title"]},
                    "action": "settle the card (move done/failed) in the same pass",
                })
            lagging_session_ids.append(n)

    exit_code = 0 if (len(offenders) == 0 and len(lagging_cards) == 0) else 1

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "workspace": cwd,
        "encodedDir": encoded,
        "staleMinutes": STALE_MINUTES,
        "liveMinutes": live_minutes,
        "strict": strict,
        "summary": {
            "total": len(sessions_out),
            "byClass": by_class,
            "attached": attached_count,
            "waived": waived_count,
            "offenders": len(offenders),
            "laggingCards": len(lagging_cards),
            "archived": len(archived_with_settled),
            "historical": len(historical_descendants),
            "exitCode": exit_code,
        },
        "sessions": sessions_out,
        "offenders": offenders,
        "offenderDetails": offender_details,
        "laggingCards": lagging_cards,
        "archivedWithSettledExecution": archived_with_settled,
        "historicalDescendants": historical_descendants,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(
        "session-recon: {} sessions (interactive {} board-execution {} card-subagent {} "
        "user-subagent {} stale {}) attached={} waived={} offenders={} lagging={} archived={} historical={} exit={}".format(
            len(sessions_out),
            by_class.get("interactive", 0),
            by_class.get("board-execution", 0),
            by_class.get("card-subagent", 0),
            by_class.get("user-subagent", 0),
            by_class.get("stale", 0),
            attached_count,
            waived_count,
            len(offenders),
            len(lagging_cards),
            len(archived_with_settled),
            len(historical_descendants),
            exit_code,
        )
    )

    if archived_with_settled:
        print("ARCHIVED (not offenders — off the board):")
        for a in archived_with_settled:
            print("  card={}  status={}  archivedAt={}  {}".format(
                a["cardId"], a["status"], a.get("archivedAt"), a["title"]))

    if historical_descendants:
        print("HISTORICAL:")
        for h in historical_descendants:
            print("  {}  class=card-subagent  lastWrite={}  {}  card={}".format(
                h["sessionId"], h["lastWrite"], h["note"],
                (h["card"]["id"] if h["card"] else "null")))

    if exit_code != 0:
        print("OFFENDERS:")
        # offender_details already carries one settled-lag entry per lagging card;
        # re-listing lagging_cards here printed every one of them twice.
        for od in offender_details:
            print("  {}  class={}  chain={}  card={}  action={}".format(
                od["sessionId"], od["class"], " -> ".join(od["chain"]),
                (od["card"]["id"] if od["card"] else "null"), od["action"]))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
