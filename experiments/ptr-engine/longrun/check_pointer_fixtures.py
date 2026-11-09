import json, sys, glob, os

REQUIRED_FIELDS = [
    "schema", "task_id", "generation", "N", "turns",
    "wall_tokens", "wall_tokens_basis", "fetch_budget_tokens",
    "fetch_budget_tokens_basis", "documents", "revision_schedule",
    "checkpoints", "fetch_scenarios",
]
OUTCOMES = ("OK", "NOT_FOUND", "STALE_OR_REVOKED", "SCOPE_UNGRANTED")

try:
    import grade_v5 as _g5
except Exception:
    _g5 = None


def _load_input(path_or_data):
    if isinstance(path_or_data, dict):
        return path_or_data
    with open(path_or_data, encoding="utf-8") as fh:
        return json.load(fh)


def _squash(text):
    return " ".join(str(text or "").split()).lower()


def validate(fx, disabled=None):
    disabled = set(disabled or ())
    errs = []
    # basic required fields
    for f in REQUIRED_FIELDS:
        if f not in fx:
            errs.append(f"missing field {f}")
    if fx.get("generation") != "gen-7":
        errs.append(f"generation != gen-7: {fx.get('generation')!r}")
    N = fx.get("N")
    if not isinstance(N, int) or not (40 <= N <= 200):
        errs.append(f"N not in [40,72]: {N!r}")
    turns = fx.get("turns")
    if not isinstance(turns, list) or len(turns) != N:
        errs.append(f"len(turns)={len(turns) if isinstance(turns,list) else None} != N={N}")
    basis = fx.get("wall_tokens_basis") or {}
    if not isinstance(basis, dict) or "basis" not in basis:
        errs.append("wall_tokens_basis must be dict with 'basis'")
    if basis.get("basis") == "UNMEASURED":
        if fx.get("wall_tokens") is not None:
            errs.append("UNMEASURED basis requires wall_tokens null")
    else:
        if not isinstance(fx.get("wall_tokens"), int):
            errs.append("measured basis but wall_tokens not int")
    fbt = fx.get("fetch_budget_tokens")
    if not isinstance(fbt, int) or fbt <= 0:
        errs.append("fetch_budget_tokens must be a positive int")
    fbtb = fx.get("fetch_budget_tokens_basis")
    if not (isinstance(fbtb, str) and fbtb.strip()):
        errs.append("fetch_budget_tokens_basis must be a non-empty provenance string")

    # outcomes reachable
    scenarios = fx.get("fetch_scenarios") or []
    seen = set()
    for s in scenarios:
        if isinstance(s, dict) and "expected_outcome" in s:
            seen.add(s["expected_outcome"])
    docs = fx.get("documents") or []
    has_revoked = any(isinstance(d, dict) and (d.get("revoked") is True or d.get("revoked_at_turn") is not None) for d in docs)
    has_ungranted = any(isinstance(d, dict) and d.get("scope") != "granted" for d in docs)
    has_multirev = any(isinstance(d, dict) and len(d.get("revisions") or []) >= 2 for d in docs)
    doc_ids = {d.get("doc_id") for d in docs if isinstance(d, dict)}
    not_found_scenario = "NOT_FOUND" in seen
    missing_ref_ok = False
    for s in scenarios:
        if not isinstance(s, dict):
            continue
        ref = s.get("ref")
        if not isinstance(ref, str):
            continue
        did = ref.split("@", 1)[0]
        if did not in doc_ids:
            if s.get("expected_outcome") == "NOT_FOUND":
                missing_ref_ok = True
        else:
            if s.get("expected_outcome") == "NOT_FOUND":
                errs.append(f"fetch_scenarios ref {ref!r} resolves to document {did!r} but expected_outcome is NOT_FOUND")
    if "NOT_FOUND" in seen and not missing_ref_ok:
        errs.append("NOT_FOUND outcome declared but no fetch_scenario references an unknown document (missing_ref_ok false)")
    for o in OUTCOMES:
        if o not in seen:
            errs.append(f"outcome not reachable (no scenario): {o}")
    if not has_revoked:
        errs.append("no revoked document (STALE_OR_REVOKED support)")
    if not has_ungranted:
        errs.append("no ungranted-scope document (SCOPE_UNGRANTED support)")
    if not has_multirev:
        errs.append("no document with >=2 revisions (stale support)")

    # checkpoints
    cps = fx.get("checkpoints") or []
    if not isinstance(cps, list) or len(cps) == 0:
        errs.append("checkpoints empty")
    # duplicate checkpoint turns
    seen_cp_turns = {}
    for cp in cps:
        if not isinstance(cp, dict):
            continue
        try:
            tn = int(cp.get("turn"))
        except (TypeError, ValueError):
            continue
        if tn in seen_cp_turns:
            errs.append(f"checkpoint {cp.get('id')} duplicate checkpoint turn {tn} (also {seen_cp_turns[tn]})")
        else:
            seen_cp_turns[tn] = cp.get("id")
    for cp in cps:
        if not isinstance(cp, dict):
            errs.append("checkpoint not dict")
            continue
        gt = cp.get("ground_truth")
        if not isinstance(gt, dict):
            errs.append(f"checkpoint {cp.get('id')} missing ground_truth")
            continue
        if "doc" not in gt or "revision" not in gt:
            errs.append(f"checkpoint {cp.get('id')} ground_truth missing doc/revision")
            continue
        if "value" not in gt:
            errs.append(f"checkpoint {cp.get('id')} ground_truth missing value")
            continue
        stale = cp.get("stale_value")
        live = gt.get("value")
        if stale == live:
            errs.append(f"checkpoint {cp.get('id')} stale_value == live value")
        if gt["doc"] not in doc_ids:
            errs.append(f"checkpoint {cp.get('id')} ground_truth doc {gt['doc']!r} not in documents")
        matching = [d for d in docs if isinstance(d, dict) and d.get("doc_id") == gt["doc"]]
        if matching:
            revs = [r.get("revision") for r in (matching[0].get("revisions") or [])]
            if gt["revision"] not in revs:
                errs.append(f"checkpoint {cp.get('id')} revision {gt['revision']} not in doc {gt['doc']} revisions {revs}")

    # tool_outputs consistency
    doc_map = {d.get("doc_id"): d for d in docs if isinstance(d, dict)}
    has_tool_outputs = False
    for idx, turn in enumerate(turns or []):
        if not isinstance(turn, dict):
            continue
        tos = turn.get("tool_outputs", None)
        if tos is None:
            continue
        has_tool_outputs = True
        if not isinstance(tos, list):
            errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs not a list")
            continue
        for to in tos:
            if not isinstance(to, dict):
                errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs entry not dict")
                continue
            did = to.get("doc_id")
            if did not in doc_map:
                errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs unknown doc_id {did!r}")
                continue
            try:
                rev = int(to.get("revision"))
            except (TypeError, ValueError):
                errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs bad revision {to.get('revision')!r}")
                continue
            revs = [r.get("revision") for r in (doc_map[did].get("revisions") or [])]
            if rev not in revs:
                errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs revision {rev} not in {did} {revs}")
                continue
            rev_obj = next((r for r in (doc_map[did].get("revisions") or []) if r.get("revision") == rev), None)
            if rev_obj is not None and "body" in to:
                if str(to.get("body")) != str(rev_obj.get("value")):
                    errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs body != revision value for {did}@{rev}")
            if "doc_id" not in to or "revision" not in to or "body" not in to:
                errs.append(f"turn {turn.get('turn', idx+1)} tool_outputs entry missing doc_id/revision/body")
    if not has_tool_outputs:
        errs.append("no turn declares tool_outputs")

    # ---- new checks for distance/leakage/gradability/uniqueness ----
    # duplicate expected values
    if "duplicate_expected" not in disabled:
        seen_exp = {}
        for cp in cps:
            if not isinstance(cp, dict):
                continue
            e = str(cp.get("expected"))
            if e in seen_exp:
                errs.append(f"duplicate expected value {e!r} (checkpoints {seen_exp[e]!r} and {cp.get('id')!r})")
            else:
                seen_exp[e] = cp.get("id")

    turn_by_num = {}
    for t in (turns or []):
        if isinstance(t, dict):
            try:
                turn_by_num[int(t.get("turn"))] = t
            except (TypeError, ValueError):
                pass

    system_prompt = fx.get("system_prompt") or ""
    items = fx.get("items") or []

    for cp in cps:
        if not isinstance(cp, dict):
            continue
        expected = cp.get("expected")
        if expected is None:
            continue
        ev = str(expected)
        has_dist_fields = any(k in cp for k in ("fact_introduction_turn", "introduction_turn", "intro_turn", "distance"))

        # gradability
        if "gradability" not in disabled:
            af = cp.get("answer_form")
            parsed = None
            if _g5 is not None:
                try:
                    parsed = _g5.parse_answer_contract(af or "")
                except Exception:
                    parsed = {"answer_kind": None, "answer_parse_error": "exception"}
            if parsed is None or parsed.get("answer_kind") is None or parsed.get("answer_parse_error"):
                errs.append(f"checkpoint {cp.get('id')} ungradable answer_form {af!r}")
            else:
                kind = parsed.get("answer_kind")
                pv = parsed.get("answer_value")
                # answer kind must match expected value type
                evs = str(expected)
                try:
                    int(evs)
                    expected_type = "NUM"
                except (TypeError, ValueError):
                    if "(" in evs and ")" in evs:
                        expected_type = "CALL"
                    else:
                        expected_type = "TEXT"
                if kind is not None and kind != expected_type:
                    errs.append(f"checkpoint {cp.get('id')} answer kind {kind!r} does not match expected value type {expected_type!r} (kind/type mismatch)")

                try:
                    if kind == "NUM":
                        if int(pv) != int(expected):
                            errs.append(f"checkpoint {cp.get('id')} answer_form value {pv!r} != expected {expected!r}")
                    elif kind == "TEXT":
                        if str(pv) != str(expected):
                            errs.append(f"checkpoint {cp.get('id')} answer_form value {pv!r} != expected {expected!r}")
                except (TypeError, ValueError):
                    errs.append(f"checkpoint {cp.get('id')} answer_form value {pv!r} != expected {expected!r}")

        # injected question identity: the checkpoint question must be the one the runner injects
        if "injected_question" not in disabled:
            try:
                tn = int(cp.get("turn"))
            except (TypeError, ValueError):
                tn = None
            if tn is not None:
                iturn = turn_by_num.get(tn)
                if iturn is None:
                    errs.append(f"checkpoint {cp.get('id')} turn {tn} not found in turns")
                else:
                    if str(cp.get("question", "")).strip() != str(iturn.get("question", "")).strip():
                        errs.append(f"checkpoint {cp.get('id')} question {cp.get('question')!r} is not the one the runner would inject (injected question mismatch)")

        # distance
        if "distance" not in disabled and has_dist_fields:
            intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
            dist = cp.get("distance")
            if intro is not None and dist is not None:
                try:
                    if int(cp.get("turn")) - int(intro) != int(dist):
                        errs.append(f"checkpoint {cp.get('id')} distance mismatch: {int(cp.get('turn')) - int(intro)} != {dist}")
                except (TypeError, ValueError):
                    errs.append(f"checkpoint {cp.get('id')} invalid distance/intro types")

        # reachability (only for distance fixtures)
        if "reachability" not in disabled and has_dist_fields:
            intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
            # must be in introduction turn tool output
            if intro is not None:
                iturn = turn_by_num.get(int(intro))
                bodies_intro = []
                if iturn:
                    for to in (iturn.get("tool_outputs") or []):
                        if isinstance(to, dict):
                            bodies_intro.append(str(to.get("body", "")))
                intro_text = _squash("\n".join(bodies_intro))
                if _squash(ev) not in intro_text:
                    errs.append(f"checkpoint {cp.get('id')} fact value {ev!r} not found in introduction turn {intro} tool output")
            # not in system prompt
            if _squash(ev) in _squash(system_prompt):
                errs.append(f"checkpoint {cp.get('id')} fact value {ev!r} leaked into system_prompt")
            # not in items
            for it in items:
                if isinstance(it, dict) and _squash(ev) in _squash(it.get("body", "")):
                    errs.append(f"checkpoint {cp.get('id')} fact value {ev!r} leaked into items")
            # not in any turn question
            for t in (turns or []):
                if isinstance(t, dict) and _squash(ev) in _squash(t.get("question", "")):
                    errs.append(f"checkpoint {cp.get('id')} fact value {ev!r} leaked into a turn question")
                    break
            # not in other tool outputs
            for t in (turns or []):
                if not isinstance(t, dict):
                    continue
                try:
                    tn = int(t.get("turn"))
                except (TypeError, ValueError):
                    continue
                if intro is not None and tn == int(intro):
                    continue
                for to in (t.get("tool_outputs") or []):
                    if isinstance(to, dict) and _squash(ev) in _squash(to.get("body", "")):
                        errs.append(f"checkpoint {cp.get('id')} fact value {ev!r} leaked into another turn's tool output (turn {tn})")
                        break

    return errs


def check(path_or_data, disabled=None):
    try:
        fx = _load_input(path_or_data)
    except Exception as exc:
        label = path_or_data if isinstance(path_or_data, str) else "<in-memory>"
        print(f"{label}: FAIL")
        print(f"  - cannot load: {exc}")
        return False
    errs = validate(fx, disabled=disabled)
    label = path_or_data if isinstance(path_or_data, str) else "<in-memory>"
    status = "OK" if not errs else "FAIL"
    print(f"{label}: {status}")
    for e in errs:
        print(f"  - {e}")
    return len(errs) == 0


def main():
    args = sys.argv[1:]
    if not args:
        args = ["experiments/ptr-engine/longrun/tasks-v6/PT-*.v9.json"]
    paths = []
    for a in args:
        if "*" in a or "?" in a:
            paths.extend(sorted(glob.glob(a)))
        else:
            paths.append(a)
    all_ok = True
    for p in paths:
        ok = check(p)
        if not ok:
            all_ok = False
    print("---")
    print(f"files checked: {len(paths)}")
    print(f"all four outcomes per file: {all_ok}")
    for p in paths:
        fx = json.load(open(p))
        seen = {s.get("expected_outcome") for s in (fx.get("fetch_scenarios") or []) if isinstance(s, dict)}
        print(f"{os.path.basename(p)}: outcomes={sorted(seen)} checkpoints={len(fx.get('checkpoints') or [])} N={fx.get('N')}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
