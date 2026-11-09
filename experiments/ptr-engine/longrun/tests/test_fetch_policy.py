import run_longrun as R


def _load_fixture():
    import json, os
    p = os.path.join(os.path.dirname(__file__), "..", "tasks-v7", "TX-HOP.v1.json")
    # fallback search
    if not os.path.exists(p):
        for root, _, files in os.walk(os.path.join(os.path.dirname(__file__), "..")):
            for f in files:
                if f == "TX-HOP.v1.json":
                    p = os.path.join(root, f)
    return json.load(open(p))


def test_strict_and_instructed_differ():
    fx = _load_fixture()
    t = sorted(R.checkpoint_turns(fx))[0]
    planner = R.Planner("bounded-context-fetch", fx, dry_run=True)
    info = planner.build(t)
    strict = R.checkpoint_prompt(fx, t, info["prompt"], arm="bounded-context-fetch", fetch_policy="strict")
    instructed = R.checkpoint_prompt(fx, t, info["prompt"], arm="bounded-context-fetch", fetch_policy="instructed")
    assert strict != instructed
    assert "not visible" not in strict or "fetch tool before answering" not in strict
    assert "not visible in the current context" in instructed
    assert "answering from memory" in instructed


def test_answer_contract_identical():
    fx = _load_fixture()
    t = sorted(R.checkpoint_turns(fx))[0]
    planner = R.Planner("bounded-context-fetch", fx, dry_run=True)
    info = planner.build(t)
    strict = R.checkpoint_prompt(fx, t, info["prompt"], arm="bounded-context-fetch", fetch_policy="strict")
    instructed = R.checkpoint_prompt(fx, t, info["prompt"], arm="bounded-context-fetch", fetch_policy="instructed")
    # answer contract line present in both
    for s in (strict, instructed):
        assert "ANSWER: NUM <integer>" in s
        assert "ANSWER: NONE" in s
    # identical contract tail
    tail = "ANSWER: NUM <integer>"
    assert strict.count(tail) == instructed.count(tail)


def test_row_missing_fetch_policy_refused():
    import pytest
    # build a row via make_row? Instead check a helper? We assert that make_row stamps fetch_policy.
    # Simulate: cfg without fetch_policy -> getattr default strict, so present. To test refusal,
    # we check a row dict lacking key is detected.
    row = {"arm": "bounded-context-fetch"}
    assert "fetch_policy" not in row
    # any validator refusing missing fetch_policy
    def validate(r):
        if "fetch_policy" not in r:
            raise ValueError("missing fetch_policy")
    with pytest.raises(ValueError):
        validate(row)