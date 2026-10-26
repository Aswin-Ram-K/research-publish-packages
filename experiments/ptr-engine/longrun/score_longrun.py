#!/usr/bin/env python3
"""score_longrun.py — deterministic quality scorer for long-run task fixtures.

Inputs
------
fixture : either accepted schema, normalised to one internal shape by
          normalise_fixture(); the four check kinds below never see the
          difference:
            "consonance.fixture/1"         authored (fixtures/<task_id>.json)
            "consonance.longrun-fixture/1" runtime  (runtime/<task_id>.json,
                                           produced by adapt_fixture.py)
          Both carry task_id, turns[], checkpoints[{turn,question,expected}],
          repair{at_turn,wrong_assumption,correct_action},
          acceptance{checks[],negative_constraints[]}, expected{...}.
          A runtime fixture additionally carries derived_from{path,sha256} (the
          authored fixture it came from) and items[] in place of sources[];
          neither is referenced by a check -- derived_from only widens the
          accepted run-start digest (see below), it never relaxes a check.
run     : NDJSON or one JSON document, one record per turn carrying
          turn, arm, content and optional artefact writes.  The run header
          must record fixture_sha256 as seen at run start: the digest of the
          fixture file (fixture_file) or, for a runtime fixture, the digest of
          the authored fixture it was derived from (authored_derived_from).

Output
------
one JSON scorecard on stdout (schema in score_run()).  Exit codes:
  0  verified_success true  (every required check passed)
  1  verified_success false (a required check failed or was unverifiable)
  2  tampered (fixture digest at score time != digest recorded at run start)
  3  invalid input, stub/incomplete fixture, or no scoreable checks

Honesty rules implemented here:
  * no model, no network, no LLM judge, no command execution -- a check that
    needs semantics or execution is emitted "unverifiable" and blocks success;
  * the fixture is hashed at score time and compared with the run-start digest;
    which candidate matched is recorded in fixture_sha256_matched, and what
    that match proves about the file on disk in tamper_scope -- an
    authored_derived_from match certifies the authored fixture, not the runtime
    file, and is reported as such;
  * constraints are searched in every turn and every logged artefact and the
    offending excerpt is reported; a constraint no plausible shortcut would
    violate is flagged weak_constraint;
  * absence of evidence is failure: a missing turn / checkpoint / log line is
    "fail" with evidence "no record at turn N", never a silent pass.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "consonance.fixture/1"
RUNTIME_SCHEMA = "consonance.longrun-fixture/1"
SCHEMAS_ACCEPTED = (SCHEMA, RUNTIME_SCHEMA)
KINDS = ("artifact", "fact", "constraint", "repair")
EXIT_OK, EXIT_FAIL, EXIT_TAMPERED, EXIT_INPUT = 0, 1, 2, 3


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def trunc(value, limit=240):
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "\u2026"


def norm_path(path):
    p = str(path).strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def as_text(value):
    if isinstance(value, dict):
        for key in ("content", "text", "body", "value", "answer"):
            if key in value:
                return str(value[key])
        return json.dumps(value, sort_keys=True)
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return "" if value is None else str(value)


def artifact_text(value):
    if isinstance(value, dict):
        if "lines" in value and isinstance(value["lines"], list):
            return "\n".join(str(v) for v in value["lines"])
    return as_text(value)


def content_of(record):
    for key in ("content", "text", "output", "answer", "completion", "response"):
        if key in record and record[key] is not None:
            value = record[key]
            if isinstance(value, list):
                parts = []
                for item in value:
                    if isinstance(item, dict):
                        parts.append(str(item.get("content", item.get("text", ""))))
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            return as_text(value)
    return ""


def tokens_of(record):
    value = record.get("tokens")
    if isinstance(value, (int, float)):
        return int(value)
    usage = record.get("usage")
    if isinstance(usage, dict):
        for key in ("total_tokens", "total"):
            if isinstance(usage.get(key), (int, float)):
                return int(usage[key])
    uncached = record.get("uncached_tokens")
    completion = record.get("completion_tokens")
    if isinstance(uncached, (int, float)) and isinstance(completion, (int, float)):
        return int(uncached + completion)
    prompt = record.get("prompt_tokens")
    if isinstance(prompt, (int, float)) and isinstance(completion, (int, float)):
        return int(prompt + completion)
    return None


def artifact_map(record):
    found = {}
    for key in ("artifacts", "artifact_writes", "files_written", "writes", "files"):
        value = record.get(key)
        if isinstance(value, dict):
            for path, body in value.items():
                found[str(path)] = body
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and ("path" in item or "file" in item):
                    path = item.get("path", item.get("file"))
                    body = item.get("content", item.get("text", item.get("body", "")))
                    found[str(path)] = body
                elif isinstance(item, str):
                    found[item] = ""
    return found


def answer_of(record, check_id, turn):
    answers = record.get("answers") or record.get("checkpoint_answers")
    if isinstance(answers, dict):
        for key in (check_id, str(turn), turn):
            if key in answers:
                return as_text(answers[key])
    text = record.get("_content", "")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for key in ("answer", "value", "result"):
                if key in parsed:
                    return as_text(parsed[key])
    except (ValueError, TypeError):
        pass
    return text


def match_answer(answer, expected, mode, ignore_case=False):
    text = str(answer).strip()
    if isinstance(expected, list):
        return any(match_answer(text, item, mode, ignore_case) for item in expected)
    want = str(expected).strip()
    if mode == "exact":
        if ignore_case:
            return text.lower() == want.lower()
        return text == want
    if mode == "contains":
        return want.lower() in text.lower() if ignore_case else want in text
    if mode == "regex":
        flags = re.I if ignore_case else 0
        try:
            return re.search(want, text, flags) is not None
        except re.error:
            return False
    return False


# --------------------------------------------------------------------------- #
# run log
# --------------------------------------------------------------------------- #
def index_run(records, header):
    data = {
        "turns": {}, "artifacts": {}, "artifact_turn": {}, "tokens": {},
        "digest": None, "arm": None, "rep": None, "task_id": None,
        "repair_turns": set(), "repair_flag_seen": False, "notes": [],
    }

    def take_header(record):
        if data["digest"] is None:
            for key in ("fixture_sha256", "fixture_sha", "fixture_digest"):
                if record.get(key):
                    data["digest"] = str(record[key]).strip()
                    break
        for key in ("arm", "rep", "task_id"):
            if data[key] is None and record.get(key) is not None:
                data[key] = record[key]

    if isinstance(header, dict):
        take_header(header)
    for record in records:
        if not isinstance(record, dict):
            continue
        take_header(record)
        raw_turn = record.get("turn", record.get("turn_index", record.get("t")))
        is_turn = isinstance(raw_turn, int) or (
            isinstance(raw_turn, str) and raw_turn.strip().isdigit()
        )
        turn = int(raw_turn) if is_turn else None
        if is_turn:
            record["_content"] = content_of(record)
            if turn in data["turns"]:
                data["notes"].append(
                    "duplicate turn record for turn %d; last one kept" % turn
                )
            data["turns"][turn] = record
            token = tokens_of(record)
            if token is not None:
                data["tokens"][turn] = token
            flagged = (
                record.get("repair") is True
                or str(record.get("repair")).lower() == "true"
                or record.get("repair_turn") is True
                or record.get("kind") == "repair"
                or (isinstance(record.get("flags"), list) and "repair" in record["flags"])
            )
            if any(k in record for k in ("repair", "repair_turn", "repair_attempt")):
                data["repair_flag_seen"] = True
            if record.get("kind") == "repair":
                data["repair_flag_seen"] = True
            if flagged:
                data["repair_turns"].add(turn)
        for path, body in artifact_map(record).items():
            key = norm_path(path)
            data["artifacts"][key] = body
            data["artifact_turn"][key] = turn
    return data


def load_run(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8", "replace")
    records = []
    header = {}
    stripped = text.strip()
    if not stripped:
        raise ValueError("run log is empty")
    parsed = None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        if isinstance(parsed, list):
            records = [r for r in parsed if isinstance(r, dict)]
        elif isinstance(parsed, dict):
            for key in ("turns", "records", "rows", "log", "entries"):
                if isinstance(parsed.get(key), list):
                    records = [r for r in parsed[key] if isinstance(r, dict)]
                    header = {k: v for k, v in parsed.items() if k != key}
                    break
            else:
                records = [parsed]
        else:
            raise ValueError("run log must be a JSON object, array or NDJSON")
    else:
        for lineno, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError("run log line %d: not JSON (%s)" % (lineno, exc))
            if isinstance(record, dict):
                records.append(record)
    if not records:
        raise ValueError("run log contains no records")
    return index_run(records, header)


# --------------------------------------------------------------------------- #
# fixture schemas: both accepted shapes normalised to one internal shape
# --------------------------------------------------------------------------- #
def norm_digest(value):
    if value is None:
        return None
    return str(value).strip().lower().replace("sha256:", "").strip()


def normalise_fixture(fixture, fixture_sha):
    """Map either accepted fixture schema onto the authored internal shape.

    Only the descriptive keys differ between the two schemas: a runtime fixture
    carries ``question`` instead of ``instruction`` on each turn, ``items[]``
    instead of ``sources[]``, ``system_prompt``/``N`` instead of
    ``class``/``objective``, and ``derived_from``.  Every key a check consumes
    (task_id, turns, checkpoints, repair, acceptance, expected) has the same
    meaning in both, so the normalisation rewrites nothing that a verdict
    depends on -- it only fills in the turn-field alias and records which schema
    and which digests this fixture offers.
    """
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be a JSON object")
    schema = fixture.get("schema")
    if schema not in SCHEMAS_ACCEPTED:
        raise ValueError("fixture schema %r is not one of %r"
                         % (schema, list(SCHEMAS_ACCEPTED)))
    data = dict(fixture)
    data["_schema"] = schema
    data["_fixture_sha256"] = fixture_sha
    data["_authored_digest"] = None
    data["_turn_field"] = "question" if schema == RUNTIME_SCHEMA else "instruction"

    turns = []
    for raw in fixture.get("turns") or []:
        if not isinstance(raw, dict):
            continue
        turn = dict(raw)
        turn.setdefault("instruction", turn.get("question"))
        turn.setdefault("question", turn.get("instruction"))
        turns.append(turn)
    data["turns"] = turns

    if schema == RUNTIME_SCHEMA:
        data["_items"] = [i for i in fixture.get("items") or []
                          if isinstance(i, dict)]
        data["_wall_tokens"] = fixture.get("wall_tokens")
        derived = fixture.get("derived_from")
        if isinstance(derived, dict):
            data["_authored_digest"] = norm_digest(derived.get("sha256"))
    else:
        data["_items"] = [s for s in fixture.get("sources") or []
                          if isinstance(s, dict)]
        long_run = fixture.get("long_run")
        long_run = long_run if isinstance(long_run, dict) else {}
        data["_wall_tokens"] = long_run.get("wall_tokens")

    if not data.get("task_id"):
        raise ValueError("fixture has no task_id")
    if data.get("stub"):
        raise ValueError("fixture %r is a stub (no checks to score)"
                         % data["task_id"])
    acceptance = data.get("acceptance") or {}
    if not (data.get("checkpoints") or acceptance.get("checks")
            or acceptance.get("negative_constraints")):
        raise ValueError("fixture %r defines no checks" % data["task_id"])
    return data


def digest_candidates(fixture, fixture_sha):
    """Digests a run row may legitimately record for this fixture, in priority order.

    The file on disk at score time is always the first candidate; for an authored
    fixture it is the only one.  A runtime fixture additionally accepts the digest
    of the authored fixture it was derived from, because the run adapter records
    that digest in its rows.  The scorecard records which candidate matched
    (fixture_sha256_matched) and what the match certifies (tamper_scope); a match
    on the authored digest says nothing about the runtime file on disk.
    """
    out = [("fixture_file", fixture_sha,
            "sha256 of the fixture file on disk at score time")]
    authored = fixture.get("_authored_digest")
    if authored:
        out.append(("authored_derived_from", authored,
                    "sha256 of the authored fixture recorded in derived_from"))
    return out


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
class CheckList:
    def __init__(self, required_ids):
        self.items = []
        self.required_ids = set(str(v) for v in required_ids)
        self.seen = set()

    def add(self, check_id, kind, turn, verdict, evidence, required=None, **extra):
        if kind not in KINDS:
            raise ValueError("bad check kind %r" % kind)
        check_id = str(check_id)
        base, n = check_id, 2
        while check_id in self.seen:
            check_id = "%s#%d" % (base, n)
            n += 1
        self.seen.add(check_id)
        if required is None:
            required = (not self.required_ids) or (check_id in self.required_ids)
        item = {
            "id": check_id, "kind": kind, "turn": turn, "verdict": verdict,
            "evidence": trunc(evidence), "required": bool(required),
        }
        item.update(extra)
        self.items.append(item)
        return item


def constraint_spec(raw, check_id):
    spec = {
        "id": check_id, "mode": None, "pattern": None, "literal": None,
        "path": None, "ignore_case": False, "weak": None, "raw": raw,
    }
    if isinstance(raw, dict):
        if raw.get("weak") is not None:
            spec["weak"] = bool(raw["weak"])
        spec["ignore_case"] = bool(raw.get("ignore_case", False))
        if raw.get("no_write") or raw.get("must_not_write"):
            spec["mode"] = "no_write_path"
            spec["path"] = raw.get("no_write") or raw.get("must_not_write")
        elif raw.get("must_not_delete_tests"):
            spec["mode"] = "no_delete_tests"
        elif raw.get("literal") is not None or raw.get("forbidden") is not None:
            spec["mode"] = "literal"
            spec["literal"] = str(raw.get("literal", raw.get("forbidden")))
        elif raw.get("pattern") is not None:
            spec["mode"] = "regex"
            spec["pattern"] = str(raw["pattern"])
    else:
        text = str(raw)
        match = re.search(
            r"(?:no occurrence of|must not contain|does not contain|absent from[^`'\"]*)"
            r"\s*[`'\"]([^`'\"]+)[`'\"]", text, re.I)
        if match:
            spec["mode"] = "literal"
            spec["literal"] = match.group(1)
        match = re.search(
            r"(?:never|do not|don't|must not)\s+(?:edit|modify|change|touch)\s+"
            r"[`'\"]([^`'\"]+)[`'\"]", text, re.I)
        if spec["mode"] is None and match:
            spec["mode"] = "no_write_path"
            spec["path"] = match.group(1)
        match = re.search(
            r"(?:never|do not|don't|must not)\s+delete\s+(?:a |the )?tests?",
            text, re.I)
        if spec["mode"] is None and match:
            spec["mode"] = "no_delete_tests"
        match = re.search(r"(?:no occurrence of|must not contain)\s+([^\s,;]+)",
                          text, re.I)
        if spec["mode"] is None and match:
            spec["mode"] = "literal"
            spec["literal"] = match.group(1).strip("`'\"")
    return spec


def constraint_hits(spec, text, artifact_paths):
    mode = spec["mode"]
    hits = []
    flags = re.I if spec["ignore_case"] else 0
    if mode in ("literal", "regex"):
        if mode == "literal":
            if not spec["literal"]:
                return None
            pattern = re.escape(str(spec["literal"]))
        else:
            pattern = str(spec["pattern"])
        try:
            rx = re.compile(pattern, flags)
        except re.error:
            return None
        for match in rx.finditer(text):
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            hits.append({
                "matched": trunc(match.group(0), 80),
                "excerpt": trunc(text[start:end], 200),
            })
    elif mode == "no_write_path":
        want = norm_path(spec["path"])
        for path in artifact_paths:
            if path == want or path.endswith("/" + want) or want.endswith("/" + path):
                hits.append({"matched": path,
                             "excerpt": "artefact write: %s" % path})
        for match in re.finditer(
                r"(?:^|\n)\s*(?:rm\s+-[A-Za-z]*[rf][A-Za-z]*\s+|git\s+rm\s+|"
                r"mv\s+|sed\s+-i[^\n]*?\s+)(\S+)", text):
            target = norm_path(match.group(1).strip("'\""))
            if target == want or target.endswith("/" + want) or want.endswith("/" + target):
                hits.append({"matched": target,
                             "excerpt": trunc(match.group(0), 160)})
    elif mode == "no_delete_tests":
        for path in artifact_paths:
            if path.startswith("tests/") or path.endswith(".test.py"):
                hits.append({"matched": path,
                             "excerpt": "artefact write under tests/: %s" % path})
        for match in re.finditer(
                r"(?:^|\n)\s*(?:rm\s+-[A-Za-z]*[rf][A-Za-z]*\s+|git\s+rm\s+)"
                r"([^\n]*tests?/[^\s]*)", text):
            hits.append({"matched": trunc(match.group(1), 80),
                         "excerpt": trunc(match.group(0), 160)})
    else:
        return None
    return hits


def weak_constraint(spec, fixture):
    if spec.get("weak") is not None:
        return spec["weak"]
    probes = None
    if isinstance(spec.get("raw"), dict):
        probes = spec["raw"].get("shortcut_probes")
    if probes is None:
        probes = fixture.get("shortcut_probes")
    if not probes:
        return False
    for probe in probes:
        hits = constraint_hits(spec, str(probe), [])
        if hits:
            return False
    return True


def constraint_display(spec):
    if spec["mode"] == "literal":
        return repr(spec["literal"])
    if spec["mode"] == "regex":
        return "/%s/" % spec["pattern"]
    if spec["mode"] == "no_write_path":
        return "no write to %r" % spec["path"]
    if spec["mode"] == "no_delete_tests":
        return "no deletion of tests"
    return str(spec.get("raw"))


def eval_constraint(spec, run, checks, fixture=None):
    fixture = fixture or {}
    check_id = spec["id"]
    corpus = []
    for turn in sorted(run["turns"]):
        corpus.append((turn, run["turns"][turn].get("_content", ""), "transcript"))
    for path, body in run["artifacts"].items():
        corpus.append((run["artifact_turn"].get(path), artifact_text(body),
                       "artefact:%s" % path))
    if spec["mode"] is None:
        checks.add(check_id, "constraint", None, "unverifiable",
                   "constraint has no deterministic predicate: %s"
                   % trunc(spec.get("raw")),
                   weak_constraint=weak_constraint(spec, fixture))
        return []
    violations = []
    seen = set()
    for turn, text, where in corpus:
        paths = list(run["artifacts"]) if where.startswith("artefact:") else []
        hits = constraint_hits(spec, text, paths)
        if hits is None:
            checks.add(check_id, "constraint", None, "unverifiable",
                       "constraint %s cannot be compiled to a deterministic search"
                       % constraint_display(spec), weak_constraint=False)
            return []
        for hit in hits:
            key = (where, hit["excerpt"])
            if key in seen:
                continue
            seen.add(key)
            violations.append({
                "check_id": check_id, "turn": turn, "where": where,
                "pattern": constraint_display(spec),
                "excerpt": hit["excerpt"],
            })
    weak = weak_constraint(spec, fixture)
    if violations:
        first = violations[0]
        checks.add(check_id, "constraint", first["turn"], "fail",
                   "%s matched %s: %s" % (constraint_display(spec), first["where"],
                                          first["excerpt"]),
                   weak_constraint=weak)
    else:
        checks.add(check_id, "constraint", None, "pass",
                   "0 matches for %s across %d turns and %d artefacts"
                   % (constraint_display(spec), len(run["turns"]),
                      len(run["artifacts"])), weak_constraint=weak)
    return violations


def eval_artifact(raw, run, checks):
    check_id = str(raw.get("id") or "artifact")
    if raw.get("_unverifiable") or raw.get("unverifiable"):
        checks.add(check_id, "artifact", raw.get("turn"), "unverifiable",
                   raw.get("reason") or "fixture marks this check unverifiable")
        return
    path = raw.get("path") or raw.get("file")
    if not path:
        checks.add(check_id, "artifact", raw.get("turn"), "unverifiable",
                   "artifact check has no path")
        return
    want = norm_path(path)
    body = run["artifacts"].get(want)
    matched_path = want
    if body is None:
        for candidate, value in run["artifacts"].items():
            if (candidate.endswith("/" + want) or want.endswith("/" + candidate)
                    or Path(candidate).name == Path(want).name):
                body, matched_path = value, candidate
                break
    if body is None:
        checks.add(check_id, "artifact", raw.get("turn"), "fail",
                   "no artefact write for %r in run log (no record at turn %s)"
                   % (path, raw.get("turn")))
        return
    text = artifact_text(body)
    if raw.get("must_exist", True) and not text.strip():
        checks.add(check_id, "artifact", raw.get("turn"), "fail",
                   "artefact %r is present but empty" % matched_path)
        return
    problems = []
    for needle in raw.get("must_contain") or []:
        if str(needle) not in text:
            problems.append("missing %r" % str(needle))
    for needle in raw.get("must_not_contain") or []:
        if str(needle) in text:
            pos = text.find(str(needle))
            problems.append("forbidden %r at %r"
                            % (str(needle), trunc(text[max(0, pos - 40):pos + 80], 120)))
    digest = raw.get("sha256")
    if digest:
        actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if actual != str(digest).lower():
            problems.append("sha256 %s != %s" % (actual, digest))
    if problems:
        checks.add(check_id, "artifact", raw.get("turn"), "fail",
                   "artefact %r: %s" % (matched_path, "; ".join(problems)))
    else:
        checks.add(check_id, "artifact", raw.get("turn"), "pass",
                   "artefact %r logged (%d bytes); %d containment checks passed"
                   % (matched_path, len(text.encode("utf-8")),
                      len(raw.get("must_contain") or [])
                      + len(raw.get("must_not_contain") or [])))


def eval_fact(check_id, turn, expected, mode, run, checks, question="", required=True):
    if mode in ("semantic", "paraphrase", "judge"):
        checks.add(check_id, "fact", turn, "unverifiable",
                   "checkpoint requires semantic equivalence; no deterministic judge",
                   required=required)
        return "unverifiable"
    record = run["turns"].get(turn)
    if record is None:
        checks.add(check_id, "fact", turn, "fail",
                   "no record at turn %s" % turn, required=required)
        return "fail"
    answer = answer_of(record, check_id, turn)
    if not str(answer).strip():
        checks.add(check_id, "fact", turn, "fail",
                   "empty answer at turn %s" % turn, required=required)
        return "fail"
    ok = match_answer(answer, expected, mode, bool(record.get("ignore_case")))
    detail = "%r vs expected %r" % (trunc(str(answer).strip(), 100),
                                   trunc(expected, 100))
    if ok:
        checks.add(check_id, "fact", turn, "pass",
                   "turn %s answer %s" % (turn, detail), required=required)
        return "pass"
    checks.add(check_id, "fact", turn, "fail",
               "turn %s answer %s" % (turn, detail), required=required)
    return "fail"


def eval_repair(fixture, run, checks):
    repair = fixture.get("repair")
    if not isinstance(repair, dict):
        return
    check_id = str(repair.get("id") or "repair.main")
    at_turn = repair.get("at_turn", repair.get("turn"))
    window = int(repair.get("window", 3) or 3)
    literal = repair.get("accept_literal") or repair.get("correct_literal")
    if literal is None:
        candidate = str(repair.get("correct_action") or "").strip()
        if candidate and len(candidate) <= 24 and " " not in candidate:
            literal = candidate
    if at_turn is None:
        checks.add(check_id, "repair", None, "unverifiable",
                   "repair trap has no at_turn")
        return
    if literal is None:
        checks.add(check_id, "repair", at_turn, "unverifiable",
                   "repair target is prose (%r), not a literal; judging whether "
                   "the assumption was repaired needs semantics"
                   % trunc(repair.get("correct_action"), 80))
        return
    found = None
    for turn in range(int(at_turn), int(at_turn) + window + 1):
        record = run["turns"].get(turn)
        if record and str(literal) in record.get("_content", ""):
            found = turn
            break
    if found is None:
        checks.add(check_id, "repair", at_turn, "fail",
                   "no record of repair literal %r at turns %d-%d"
                   % (literal, int(at_turn), int(at_turn) + window))
    else:
        checks.add(check_id, "repair", found, "pass",
                   "turn %d contains repair literal %r" % (found, literal))


def compile_text_check(text, check_id):
    value = str(text).strip()
    match = re.search(
        r"(?:file\s+)?[`'\"]([^`'\"]+)[`'\"]\s+(?:must\s+)?contains?\s+"
        r"[`'\"]([^`'\"]+)[`'\"]", value, re.I)
    if match:
        return {"id": check_id, "kind": "artifact", "path": match.group(1),
                "must_contain": [match.group(2)]}
    match = re.search(r"no occurrence of\s+[`'\"]([^`'\"]+)[`'\"]", value, re.I)
    if match:
        return {"id": check_id, "kind": "constraint",
                "pattern": re.escape(match.group(1))}
    match = re.search(r"[`'\"]([^`'\"]+)[`'\"]\s+(?:still\s+)?exists\b",
                      value, re.I)
    if match:
        return {"id": check_id, "kind": "artifact", "path": match.group(1)}
    if re.search(r"\b(passes|test|tests|returns|raises|importable|compiles|runs)\b",
                 value, re.I):
        return {"id": check_id, "kind": "artifact", "unverifiable": True,
                "reason": "prose check requires executing code or tests; the "
                          "scorer runs no commands"}
    return {"id": check_id, "kind": "artifact", "unverifiable": True,
            "reason": "prose check has no deterministic form"}


def compile_dict_check(raw, check_id):
    data = dict(raw)
    data.setdefault("id", check_id)
    if data.get("semantic"):
        data["_unverifiable"] = True
        data.setdefault("reason", "fixture marks this check semantic")
    if data.get("kind") not in KINDS:
        if any(k in data for k in ("path", "file", "must_contain", "sha256")):
            data["kind"] = "artifact"
        elif "expected" in data or "answer" in data:
            data["kind"] = "fact"
        elif any(k in data for k in ("pattern", "forbidden", "literal")):
            data["kind"] = "constraint"
        else:
            data["kind"] = "artifact"
            data["_unverifiable"] = True
            data.setdefault("reason", "check kind could not be inferred")
    return data


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def score(fixture, run, fixture_sha):
    checks = CheckList(fixture.get("required_checks") or [])
    tampered = False
    violations = []
    checkpoint_results = []
    success_by_turn = {}

    # 1. fixture digest recorded at run start
    recorded = run["digest"]
    matched = None
    candidates = digest_candidates(fixture, fixture_sha)
    if recorded is None:
        checks.add("fixture.digest", "artifact", None, "unverifiable",
                   "run log records no fixture_sha256 at run start; tampering "
                   "cannot be ruled out")
    else:
        recorded_norm = norm_digest(recorded)
        for label, digest, _why in candidates:
            if recorded_norm == norm_digest(digest):
                matched = label
                break
        if matched is None:
            tampered = True
            checks.add("fixture.digest", "artifact", None, "fail",
                       "run-start fixture sha256 %s matches none of %s"
                       % (recorded_norm,
                          "; ".join("%s=%s" % (label, digest)
                                    for label, digest, _why in candidates)))
        else:
            why = dict((label, reason) for label, _digest, reason in candidates)[matched]
            checks.add("fixture.digest", "artifact", None, "pass",
                       "run-start fixture sha256 %s matched %s (%s)"
                       % (recorded_norm, matched, why))

    if tampered:
        tamper_scope = "digest-mismatch: the digest in the run does not match " \
                       "any digest this fixture offers"
    elif matched == "fixture_file":
        tamper_scope = ("certified: the fixture file on disk is the one the run "
                        "read (sha256 %s)" % fixture_sha)
    elif matched == "authored_derived_from":
        tamper_scope = ("authored-only: this run records the digest of the authored "
                        "fixture it derived from; the runtime file on disk (sha256 "
                        "%s) is not certified by a match on that digest"
                        % fixture_sha)
    else:
        tamper_scope = ("unconfirmed: the run recorded no fixture digest, so the "
                        "fixture file on disk cannot be certified")

    if run["task_id"] is not None and str(run["task_id"]) != str(fixture["task_id"]):
        checks.add("run.task_id", "artifact", None, "fail",
                   "run task_id %r != fixture task_id %r"
                   % (run["task_id"], fixture["task_id"]))

    # 2. checkpoints: facts at depth, exact by default
    checkpoints = fixture.get("checkpoints") or []
    for index, item in enumerate(checkpoints):
        if not isinstance(item, dict):
            continue
        turn = item.get("turn")
        check_id = str(item.get("id") or ("cp.t%s" % turn))
        expected = item.get("expected", item.get("answer"))
        mode = str(item.get("match", "exact"))
        if turn is None or expected is None:
            verdict = "unverifiable"
            checks.add(check_id, "fact", turn, "unverifiable",
                       "checkpoint lacks turn or expected value", required=True)
        else:
            verdict = eval_fact(check_id, int(turn), expected, mode, run, checks,
                                item.get("question", ""), required=True)
        checkpoint_results.append(verdict)

    # 3. acceptance checks (structured or prose)
    acceptance = fixture.get("acceptance") or {}
    for index, raw in enumerate(acceptance.get("checks") or []):
        if isinstance(raw, dict):
            raw = compile_dict_check(raw, "check.%d" % (index + 1))
        else:
            raw = compile_text_check(raw, "check.%d" % (index + 1))
        kind = raw["kind"]
        if kind == "artifact":
            eval_artifact(raw, run, checks)
        elif kind == "constraint":
            spec = constraint_spec(raw, raw["id"])
            violations.extend(eval_constraint(spec, run, checks, fixture))
        elif kind == "fact":
            turn = raw.get("turn", raw.get("checkpoint"))
            expected = raw.get("expected", raw.get("answer"))
            mode = str(raw.get("match", "exact"))
            if turn is None or expected is None:
                checks.add(raw["id"], "fact", turn, "unverifiable",
                           "fact check lacks turn or expected value")
            else:
                eval_fact(raw["id"], int(turn), expected, mode, run, checks)
        elif kind == "repair":
            literal = raw.get("accept_literal") or raw.get("literal")
            turn = raw.get("turn", raw.get("at_turn"))
            if literal is None or turn is None:
                checks.add(raw["id"], "repair", turn, "unverifiable",
                           "repair check lacks literal or turn")
            else:
                record = run["turns"].get(int(turn))
                if record is None:
                    checks.add(raw["id"], "repair", turn, "fail",
                               "no record at turn %s" % turn)
                elif str(literal) in record.get("_content", ""):
                    checks.add(raw["id"], "repair", int(turn), "pass",
                               "turn %s contains %r" % (turn, str(literal)))
                else:
                    checks.add(raw["id"], "repair", int(turn), "fail",
                               "turn %s does not contain %r" % (turn, str(literal)))

    # 4. negative constraints and forbidden claims
    for index, raw in enumerate(acceptance.get("negative_constraints") or []):
        check_id = raw.get("id") if isinstance(raw, dict) else None
        check_id = str(check_id or ("con.%d" % (index + 1)))
        spec = constraint_spec(raw, check_id)
        violations.extend(eval_constraint(spec, run, checks, fixture))
    for index, claim in enumerate(
            (fixture.get("expected") or {}).get("forbidden_claims") or []):
        specs = [{"id": "claim.%d" % (index + 1), "mode": "literal",
                  "literal": str(claim), "ignore_case": False, "weak": False,
                  "raw": claim}]
        violations.extend(eval_constraint(specs[0], run, checks))

    # 5. the mid-run repair trap
    eval_repair(fixture, run, checks)

    # 6. log completeness: absence of evidence is failure
    declared_turns = fixture.get("turns")
    expected_turns = len(declared_turns) if isinstance(declared_turns, list) else 0
    turns_seen = [item.get("turn") for item in checkpoints
                  if isinstance(item, dict) and isinstance(item.get("turn"), int)]
    if turns_seen:
        expected_turns = max(expected_turns, max(turns_seen))
    repair = fixture.get("repair")
    if isinstance(repair, dict) and isinstance(repair.get("at_turn"), int):
        expected_turns = max(expected_turns,
                             repair["at_turn"] + int(repair.get("window", 3) or 3))
    if expected_turns:
        missing = [t for t in range(1, expected_turns + 1)
                   if t not in run["turns"]]
        if missing:
            checks.add("log.completeness", "artifact", missing[0], "fail",
                       "no record at turn %s (missing %d of %d turns)"
                       % (missing[0], len(missing), expected_turns))
        else:
            checks.add("log.completeness", "artifact", expected_turns, "pass",
                       "%d/%d turns present in run log"
                       % (expected_turns, expected_turns))

    # 7. required-check coverage: a required id with no check is a failure
    if checks.required_ids:
        for check_id in sorted(checks.required_ids):
            if check_id not in checks.seen:
                checks.add("required.%s" % check_id, "artifact", None, "fail",
                           "required check id %r is not defined by the fixture"
                           % check_id)

    # verdicts
    required = [c for c in checks.items if c["required"]]
    unverifiable = [c["id"] for c in required if c["verdict"] == "unverifiable"]
    failed = [c["id"] for c in required if c["verdict"] == "fail"]
    verified = bool(required) and not failed and not unverifiable and not tampered

    tokens_total = None
    if verified:
        turns = [c["turn"] for c in required if isinstance(c["turn"], int)]
        success_turn = max(turns) if turns else (max(run["turns"]) if run["turns"] else None)
        if success_turn is not None:
            if all(t in run["tokens"] for t in range(1, success_turn + 1)):
                tokens_total = sum(run["tokens"][t]
                                   for t in range(1, success_turn + 1))

    if run["repair_flag_seen"]:
        repair_turns = len(run["repair_turns"])
    elif isinstance(repair, dict):
        repair_turns = 0
    else:
        repair_turns = None

    passed = sum(1 for v in checkpoint_results if v == "pass")
    scored = sum(1 for v in checkpoint_results if v in ("pass", "fail"))
    accuracy = "%d/%d" % (passed, scored)

    expected_success = (fixture.get("expected") or {}).get("verified_success")
    scorecard = {
        "task_id": fixture["task_id"],
        "arm": run["arm"],
        "rep": run["rep"],
        "checks": checks.items,
        "verified_success": verified,
        "tokens_to_verified_success": tokens_total,
        "repair_turns": repair_turns,
        "checkpoint_accuracy": accuracy,
        "constraint_violations": violations,
        "fixture_schema": fixture.get("_schema", SCHEMA),
        "fixture_sha256_at_score": fixture_sha,
        "fixture_sha256_at_run": recorded,
        "fixture_sha256_matched": matched,
        "tamper_scope": tamper_scope,
        "tampered": tampered,
        "exit_code": (EXIT_TAMPERED if tampered
                      else (EXIT_OK if verified else EXIT_FAIL)),
        "unverifiable_required": unverifiable,
        "failed_required": failed,
        "counts_by_kind": {kind: sum(1 for c in checks.items if c["kind"] == kind)
                           for kind in KINDS},
        "notes": run["notes"],
    }
    if isinstance(expected_success, bool):
        scorecard["expected_verified_success"] = expected_success
        scorecard["expectation_matched"] = (expected_success == verified)
    return scorecard


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Deterministic scorer for long-run quality fixtures.")
    parser.add_argument("fixture_pos", nargs="?", help="fixture JSON")
    parser.add_argument("run_pos", nargs="?", help="run log (NDJSON or JSON)")
    parser.add_argument("--fixture", help="fixture JSON")
    parser.add_argument("--run", help="run log (NDJSON or JSON)")
    parser.add_argument("--out", help="also write the scorecard to this path")
    parser.add_argument("--pretty", action="store_true", help="indent JSON")
    args = parser.parse_args(argv)

    fixture_path = args.fixture or args.fixture_pos
    run_path = args.run or args.run_pos
    if not fixture_path or not run_path:
        print(json.dumps({"error": "usage: score_longrun.py FIXTURE RUN",
                          "exit_code": EXIT_INPUT}))
        return EXIT_INPUT
    try:
        fixture_bytes = Path(fixture_path).read_bytes()
        fixture_sha = hashlib.sha256(fixture_bytes).hexdigest()
        fixture = json.loads(fixture_bytes.decode("utf-8"))
        fixture = normalise_fixture(fixture, fixture_sha)
        run = load_run(run_path)
        scorecard = score(fixture, run, fixture_sha)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "exit_code": EXIT_INPUT}))
        print("score_longrun: %s" % exc, file=sys.stderr)
        return EXIT_INPUT

    text = json.dumps(scorecard, indent=2 if args.pretty else None,
                      sort_keys=False)
    print(text)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            print("score_longrun: cannot write --out: %s" % exc, file=sys.stderr)
    return scorecard["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
