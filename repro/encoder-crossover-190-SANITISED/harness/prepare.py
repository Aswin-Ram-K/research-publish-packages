#!/usr/bin/env python3
"""
prepare.py — EXP#12 step 1: verify the inputs, freeze the family split, render the examples.

Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §4 (frozen).

WHAT IT DOES, IN ORDER, REFUSING AT EVERY STEP
  1. Verify the corpus digest is the frozen c78681d6... and the fixture digest is 076164ac... .
  2. Verify the F4 lint report exists, that its train->fixture lint is SILENT in both directions, and
     that its seeded-copy control actually FIRED. A run whose detector has not answered both ways is
     refused here rather than trained on (pre-registration §7.4, AGENTS.md "validate the instrument").
  3. Split BY FAMILY: train = the 600 revision + 200 H-A cases; dev = the 200 H-B cases. Assert that
     no family appears in both sides, and report clan overlap as a measured fact rather than assuming
     it away.
  4. Write data/train.jsonl and data/dev.jsonl through `tccommon.render` — the split files hold the
     very strings the model is trained on, so what was trained on is auditable.
  5. Never read the fixture's `question` for anything but the render at evaluation time. This script
     touches `data/fixture-190.json` only to hash it and count it, and writes no fixture example.

RUN
  python3 tools/typed-channel/prepare.py
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tccommon as tc  # noqa: E402


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    corpus_hash = tc.sha256_file(tc.CORPUS_PATH)
    fixture_hash = tc.sha256_file(tc.FIXTURE_PATH)
    print(f"corpus   {tc.CORPUS_PATH}\n  sha256 {corpus_hash}\n  expected {tc.CORPUS_SHA256}")
    if corpus_hash != tc.CORPUS_SHA256:
        fail(f"corpus digest mismatch — expected {tc.CORPUS_SHA256}, got {corpus_hash}")
    print("  MATCH")

    # The fixture's own source-of-truth digest is verified in export-fixture.ts and in lint.ts; here we
    # verify the exported JSON is present and has the right shape.
    fixture = tc.load_fixture()
    if len(fixture) != 190:
        fail(f"fixture-190.json holds {len(fixture)} cases, expected 190")
    print(f"fixture  {tc.FIXTURE_PATH}\n  cases {len(fixture)} (exported from the source whose sha256 is {tc.INSTRUMENT_190_SHA256})")

    if not tc.LINT_REPORT_PATH.exists():
        fail(f"no lint report at {tc.LINT_REPORT_PATH} — run ./scripts/run.sh tools/typed-channel/lint.ts --demo first")
    lint = __import__("json").loads(tc.LINT_REPORT_PATH.read_text(encoding="utf8"))
    f4 = lint["falsifier"] if "falsifier" in lint else "F4"
    if lint["trainVsFixture"]["silent"] is not True:
        fail(f"{f4} FIRED: the training split overlaps the sealed fixture — RUN VOID")
    demo = lint.get("demo")
    if not demo or not demo.get("ok"):
        fail("the lint's seeded-copy control did not answer both ways — the lint may not be trusted")
    fired = [p["name"] for p in demo["probes"] if p["fired"]]
    silent = [p["name"] for p in demo["probes"] if not p["fired"]]
    print(
        f"lint     F4 did not fire: train800 vs sealed190 is SILENT in both directions "
        f"({lint['trainVsFixture']['forward']['pairsCompared']} pairs); control fired on {fired} "
        f"and stayed silent on {silent}"
    )

    corpus = tc.load_corpus()
    cases = corpus["cases"]
    train_cases = [c for c in cases if c["stratum"] in ("revision", "H-A")]
    dev_cases = [c for c in cases if c["stratum"] == "H-B"]
    if (len(train_cases), len(dev_cases)) != (800, 200):
        fail(f"split sizes are {len(train_cases)}/{len(dev_cases)}, expected 800/200")

    train_fams = {c["familyId"] for c in train_cases}
    dev_fams = {c["familyId"] for c in dev_cases}
    straddle = train_fams & dev_fams
    if straddle:
        fail(f"{len(straddle)} families straddle train and dev: {sorted(straddle)[:10]}")
    train_clans = {c["clanId"] for c in train_cases}
    dev_clans = {c["clanId"] for c in dev_cases}
    clan_straddle = train_clans & dev_clans

    # every train case's family must be in exactly one stratum, and same for dev
    fam_strata = collections.defaultdict(set)
    for c in cases:
        fam_strata[c["familyId"]].add(c["stratum"])
    multi = {f: sorted(s) for f, s in fam_strata.items() if len(s) > 1}
    if multi:
        fail(f"{len(multi)} families span more than one stratum (e.g. {list(multi.items())[:3]})")

    print(
        f"\nsplit (by family, asserted)\n"
        f"  train {len(train_cases)} cases / {len(train_fams)} families / {len(train_clans)} clans"
        f"  (revision {sum(1 for c in train_cases if c['stratum'] == 'revision')}, "
        f"H-A {sum(1 for c in train_cases if c['stratum'] == 'H-A')})\n"
        f"  dev   {len(dev_cases)} cases / {len(dev_fams)} families / {len(dev_clans)} clans  (H-B, unseen families)\n"
        f"  family straddle: {len(straddle)}  (must be 0)\n"
        f"  clan overlap train/dev: {len(clan_straddle)} shared clans — reported, not a family leak"
    )

    train_examples = [tc.corpus_case_to_example(c) for c in train_cases]
    dev_examples = [tc.corpus_case_to_example(c) for c in dev_cases]

    def dump(path: Path, examples) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf8") as fh:
            for ex in examples:
                # store the rendered texts, so the exact model inputs are on disk
                out = dict(ex)
                out["texts"] = tc.texts_for_example(ex)
                fh.write(__import__("json").dumps(out, ensure_ascii=False) + "\n")

    dump(tc.DATA / "train.jsonl", train_examples)
    dump(tc.DATA / "dev.jsonl", dev_examples)

    kinds_train = collections.Counter(c["kind"] for c in train_cases)
    kinds_dev = collections.Counter(c["kind"] for c in dev_cases)
    kinds_fix = collections.Counter(c["kind"] for c in fixture)
    all_kinds = sorted(set(kinds_train) | set(kinds_dev) | set(kinds_fix))
    label_counts = collections.Counter()
    for c in train_cases:
        label_counts[c["gold"]] += 1
    fixtures_labels = {o for c in fixture for o in c["options"]}
    shared_labels = fixtures_labels & set(label_counts)

    manifest = {
        "experiment": "EXP#12",
        "preRegistration": "docs/research/experiments/EXP#12-typed-channel-comparison.md",
        "corpus": {"path": str(tc.CORPUS_PATH), "sha256": corpus_hash, "seed": corpus["seed"]},
        "fixture": {
            "path": str(tc.FIXTURE_PATH),
            "sourceSha256": tc.INSTRUMENT_190_SHA256,
            "cases": len(fixture),
        },
        "lint": {
            "report": str(tc.LINT_REPORT_PATH),
            "f4Fires": not lint["trainVsFixture"]["silent"],
            "trainVsFixturePairs": lint["trainVsFixture"]["forward"]["pairsCompared"],
            "controlOk": bool(demo and demo.get("ok")),
        },
        "rendering": {
            "module": "tccommon.render",
            "template": tc.TASK_PREFIX + "\\nKind: {kind}\\nSituation: {situation}\\nCandidate option: {option}",
            "corpusSituation": "state + ' ' + instructions",
            "fixtureSituation": "question",
            "criteriaIncluded": False,
            "kindAliasesUsed": tc.kind_aliases_used(all_kinds),
        },
        "split": {
            "rule": "by family; train = revision + H-A, dev = H-B",
            "train": {"cases": len(train_cases), "families": len(train_fams), "clans": len(train_clans)},
            "dev": {"cases": len(dev_cases), "families": len(dev_fams), "clans": len(dev_clans)},
            "familyStraddle": len(straddle),
            "clanOverlap": sorted(clan_straddle),
            "sealedTest": "the 190 fixture — never a training or selection input",
        },
        "kindCounts": {
            "train": dict(sorted(kinds_train.items())),
            "dev": dict(sorted(kinds_dev.items())),
            "fixture": dict(sorted(kinds_fix.items())),
        },
        "labelTransfer": {
            "trainGoldLabels": len(label_counts),
            "fixtureOptionLabels": len(fixtures_labels),
            "shared": sorted(shared_labels),
            "sharedCount": len(shared_labels),
            "fixtureCasesAllOptionsShared": sum(1 for c in fixture if set(c["options"]) <= set(label_counts)),
        },
    }
    tc.write_json(tc.DATA / "manifest.json", manifest)

    print(f"\nkind counts (train/dev/fixture):")
    for k in all_kinds:
        print(f"  {k:20s} {kinds_train.get(k,0):4d} {kinds_dev.get(k,0):4d} {kinds_fix.get(k,0):4d}")
    print(
        f"\nlabel transfer: {len(label_counts)} train gold labels, {len(fixtures_labels)} fixture option labels, "
        f"{len(shared_labels)} shared; {manifest['labelTransfer']['fixtureCasesAllOptionsShared']}/190 fixture cases "
        f"have every option inside the train vocabulary"
    )
    print(f"kind aliases applied: {manifest['rendering']['kindAliasesUsed']}")
    print(f"\nwrote {tc.DATA / 'train.jsonl'} ({len(train_examples)} rows)")
    print(f"wrote {tc.DATA / 'dev.jsonl'} ({len(dev_examples)} rows)")
    print(f"wrote {tc.DATA / 'manifest.json'}")
    print("\nexample rendered input (first train case, first option):")
    print("  " + tc.texts_for_example(train_examples[0])[0].replace("\n", "\n  "))


if __name__ == "__main__":
    main()
