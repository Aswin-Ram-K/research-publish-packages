#!/usr/bin/env python3
"""SYS-OPT-R1B — V0 quality probe: the same 20 questions, P1 form, quote_tokens=0.

Why this exists: the pinned `cells/R2-PROMPT/{O1,O4}/quality.json` files kept only the
P0-vs-P1 *form-divergence* aggregates (no completions), so V0's mismatch under the
frozen **correctness** grader cannot be re-derived from them. This probe measures it
directly: same salt, same scaffold, same delta stream, same questions as V1 — the only
difference is the missing `q:` column (`quote_tokens = 0`), which is exactly V0.

20 questions x P1 form x 2 models = 40 live requests. Holds the lineage lock.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))

import sysopt_r1 as m  # noqa: E402


def no_quote_index(rc):
    def pointer_index(up_to_turn, compacted=False):
        lines = ["id | span | sha8 | summary"]
        for t in range(1, up_to_turn + 1):
            block = rc.delta_block(t)
            if compacted and t % rc.SUMMARY_EVERY == 0:
                lines.append(rc.folded_summary(t, max(1, t - rc.SUMMARY_EVERY + 1)))
                continue
            lines.append("t%03d | %d | %s | %s" % (t, len(block), rc.sha8(block), rc.summarise(block)))
        return "\n".join(lines)
    rc.pointer_index = pointer_index


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="moe,dense")
    args = ap.parse_args(argv)
    models = [x.strip() for x in args.models.split(",") if x.strip()]
    rc = m.load_renderer()
    no_quote_index(rc)
    qf = json.loads((REPO / "state" / "sys-opt-quality.json").read_text())
    handle = m.acquire_lock("SYS-OPT-R1B-quality-before")
    out = {"unit": "SYS-OPT-R1B", "measurement": "V0 quality (quote_tokens=0), P1 form",
           "salt": m.SALT, "quality_set_content_sha256": qf["content_sha256"],
           "at": m.utc_now(), "models": {}}
    used = 0
    try:
        for name in models:
            host = m.MODELS[name]
            per_q, bad = [], 0
            for q in qf["questions"]:
                msgs = m.quality_form(rc, q["question"], "P1")
                res = m.post(host["url"], host["model"], msgs, m.QUALITY_MAX_TOKENS)
                used += 1
                g = m.grade_answer(res["text"], q["key"])
                bad += 0 if g["ok"] else 1
                per_q.append({"id": q["id"], "t": q["key"]["t"], "grader": g})
            out["models"][name] = {"n": len(per_q), "mismatches": bad,
                                   "mismatch_rate": round(bad / len(per_q), 6),
                                   "per_question": per_q}
            print("%s V0 P1-form mismatch %d/%d" % (name, bad, len(per_q)), flush=True)
    finally:
        m.release_lock(handle)
    out["requests_used"] = used
    (HERE / "quality-before.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"requests_used": used,
                      "rates": {k: v["mismatch_rate"] for k, v in out["models"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
