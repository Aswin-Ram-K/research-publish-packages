#!/usr/bin/env bash
# verify/run-verification.sh — the acceptance test for the UREDACT1 redaction.
#
# RUNS NOTHING AGAINST THE ORIGINAL SUBSET. It copies the as-audited subset and the sanitised
# subset into a scratch tree and runs the SAME commands in both, then diffs. The as-audited
# original on disk is never written to (nothing is ever executed inside it).
#
# Usage: bash verify/run-verification.sh [scratch-dir]      (default /tmp/uredact1-verify)
set -uo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)"
O="$(dirname "$S")/encoder-crossover-190"
W="${1:-/tmp/uredact1-verify}"
rm -rf "$W"; mkdir -p "$W"
cp -r "$O" "$W/orig"; cp -r "$S" "$W/san"
rm -rf "$W/san/verify" "$W/san/variants" "$W/san/redact.py" "$W/san/README.md" \
       "$W/san/REDACTION_REPORT.md" "$W/san/INTEGRITY.md"
LOG="$S/verify/VERIFICATION.txt"
mkdir -p "$S/verify"
exec > >(tee "$LOG") 2>&1

echo "=============================================================="
echo "UREDACT1 acceptance test   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "as-audited : repro/encoder-crossover-190"
echo "sanitised  : repro/encoder-crossover-190-SANITISED"
echo "scratch    : $W"
echo "=============================================================="

echo; echo "### 1. T1 instrument digest (EXPECTED TO CHANGE — declared, not silent)"
sha256sum "$W/orig/fixture/reflex-decisions.ts" "$W/san/fixture/reflex-decisions.ts"
TARGET_REPO="${TARGET_REPO:-}"
echo "-- target HEAD (read-only) --"
if [ -n "$TARGET_REPO" ]; then
  git -C "$TARGET_REPO" rev-parse HEAD
  echo "-- target git status --porcelain --"
  git -C "$TARGET_REPO" status --porcelain
else
  echo "  not supplied - export TARGET_REPO to the path of the read-only target repository to re-run this check"
fi

echo; echo "### 2. T5 chance floor (mean 1/k over the 190) recomputed from the fixture, both trees"
for tag in orig san; do
  ( cd "$W/$tag/harness" && python3 -c "
import tccommon as tc
f = tc.load_fixture()
print('$tag  cases', len(f), ' chanceFloorMean1overK', repr(sum(1.0/len(c['options']) for c in f)/len(f)), ' options_total', sum(len(c['options']) for c in f))
" )
done

echo; echo "### 3. T4 second-labeller re-run (shipped readers, unmodified) + scoring-projection digest"
for tag in orig san; do
  ( cd "$W/$tag/second-labeller"
    cp ../fixture/reflex-decisions.ts ./reflex-decisions.sandbox.ts
    python3 parse_fixture.py > "parse-$tag.stdout" 2>"parse-$tag.stderr"
    echo "  parse_fixture.py [$tag] exit=$? stderr=[$(cat parse-$tag.stderr)]"
    python3 compare.py > "compare-$tag.stdout" 2>"compare-$tag.stderr"
    echo "  compare.py       [$tag] exit=$? stderr=[$(cat compare-$tag.stderr)]"
    python3 -c "
import hashlib, json
cases = json.load(open('cases.json', encoding='utf-8'))
proj = [{k: c[k] for k in ('id','kind','question','options','correct')} for c in cases]
blob = json.dumps(proj, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()
print('  scoring-projection (id,kind,question,options,correct) sha256 [$tag]', hashlib.sha256(blob).hexdigest())
print('  cases [$tag]', len(cases), ' empty_rationales', sum(1 for c in cases if c['rationale']==''), ' empty_namespaces', sum(1 for c in cases if c['namespaces']==[]))
print('  _line values preserved [$tag]', [c['_line'] for c in cases[:3]], '...', [c['_line'] for c in cases[-2:]])
"
  )
done

echo; echo "### 4. T3 prepare.py re-run (steps 3-4; no torch, no network)"
for tag in orig san; do
  ( cd "$W/$tag/harness" && python3 prepare.py > "$W/prepare-$tag.stdout" 2>&1; echo "  prepare.py [$tag] exit=$?" )
done
echo "-- diff of the two stdout logs (paths normalised) --"
sed -E 's#/[^ ]*/harness#<harness>#g' "$W/prepare-orig.stdout" > "$W/prepare-orig.norm"
sed -E 's#/[^ ]*/harness#<harness>#g' "$W/prepare-san.stdout"  > "$W/prepare-san.norm"
if diff -u "$W/prepare-orig.norm" "$W/prepare-san.norm"; then echo "  PREPARE STDOUT IDENTICAL"; fi
echo "-- rendered split digests --"
sha256sum "$W/orig/harness/data/train.jsonl" "$W/san/harness/data/train.jsonl" \
          "$W/orig/harness/data/dev.jsonl"   "$W/san/harness/data/dev.jsonl"

echo; echo "### 5. T2 metrics.json: sanitised regeneration vs as-audited regeneration"
cp "$W/orig/second-labeller/metrics.json" "$W/metrics-orig.json"
cp "$W/san/second-labeller/metrics.json"  "$W/metrics-san.json"
cp "$O/second-labeller/metrics.json"      "$W/metrics-shipped.json"
python3 - "$W" <<'PY'
import json, sys
W = sys.argv[1]

def strip(d):
    """Drop the four keys UFIX4 added by hand AFTER the frozen scripts were run (metrics.json
    records that the scripts 'still regenerate the pre-correction bytes')."""
    d = json.loads(json.dumps(d))
    d.pop("limitation", None); d.pop("_correction", None)
    for k in ("routeB_primary",):
        if isinstance(d.get(k), dict): d[k].pop("limitation", None)
    if isinstance(d.get("passes", {}).get("labelsB.json"), dict):
        d["passes"]["labelsB.json"].pop("limitation", None)
    return d

o = json.load(open(f"{W}/metrics-orig.json"))
s = json.load(open(f"{W}/metrics-san.json"))
sh = strip(json.load(open(f"{W}/metrics-shipped.json")))
print("  orig-regenerated == san-regenerated :", o == s)
print("  san-regenerated  == shipped (hand-added keys stripped) :", s == sh)
print("  HEADLINE NUMBERS from the sanitised regeneration:")
for label, v in (("comparison cases", s["cases"]), ("options_total", s["options_total"]),
                 ("routeA kappa (CLAIMS 0.3252)", s["routeA"]["kappa"]),
                 ("routeB agreement (0.9052631578947369)", s["passes"]["labelsB.json"]["agreement"]),
                 ("routeB kappa (0.9013584840356494)", s["passes"]["labelsB.json"]["kappa"]),
                 ("n_disagreements (18)", s["passes"]["labelsB.json"]["n_disagreements"]),
                 ("AB mutual agreement (CLAIMS 0.3526)", s["passes"]["labelsB.json"]["AB_mutual_agreement"]),
                 ("closed-subset kappa (CLAIMS 0.8837)", s["stratification"]["closed_subset"]["labelsB.json"]["kappa"]),
                 ("roster/bespoke kappa (CLAIMS 0.9140)", s["stratification"]["roster_and_bespoke_subset"]["labelsB.json"]["kappa"]),
                 ("disagreements_count_routeB", s["disagreements_count_routeB"])):
    print(f"    {label:52s} {v}")
PY

echo; echo "### 6. disagreements.jsonl: only recorded_rationale may differ"
python3 - "$W" <<'PY'
import json, sys
W = sys.argv[1]
o = [json.loads(l) for l in open(f"{W}/orig/second-labeller/disagreements.jsonl", encoding="utf-8")]
s = [json.loads(l) for l in open(f"{W}/san/second-labeller/disagreements.jsonl", encoding="utf-8")]
print("  rows", len(o), len(s))
assert len(o) == len(s), "row count changed"
diffs = set()
for a, b in zip(o, s):
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            diffs.add(k)
print("  keys that differ:", sorted(diffs))
print("  every other key identical:", diffs <= {"recorded_rationale"})
print("  sanitised recorded_rationale values all empty:",
      all(r["recorded_rationale"] == "" for r in s))
PY

echo; echo "### 7. RESIDUAL STRICT-MECHANISM SCAN (sanitised vs as-audited), per file"
STRICT='StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle'
for tag in orig san; do
  echo "-- $tag --"
  ( cd "$W/$tag" && grep -rIlE "$STRICT" . | while read f; do
      n=$(grep -cE "$STRICT" "$f"); printf '%5d  %s\n' "$n" "$f"; done | sort -rn )
  ( cd "$W/$tag" && printf 'TOTAL LINES: %s\n' "$(grep -rIE "$STRICT" . | wc -l)" )
done

echo; echo "### 8. RESIDUAL HITS IN THE SANITISED TREE, with the matching text (for classification)"
( cd "$W/san" && grep -rInE "$STRICT" . | grep -v '^./fixture/reflex-decisions.ts' | cut -c1-165 | head -40 )
echo "-- fixture residue, by field class --"
python3 - "$W/san/fixture/reflex-decisions.ts" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
spans, cur = [], None
for i, ln in enumerate(lines, 1):
    if ln == "  {": cur = i
    elif cur is not None and ln in ("  },", "  }"): spans.append((cur, i)); cur = None
STRICT = re.compile(r'StateClass|grantPolicy|admit\(|src/(?:broker|scope|layer|loop|policy|state)\.ts|content-addressed|expanded\[\]|Needle')
def fspan(s, e, name):
    st = next(i for i in range(s-1, e) if re.match(r"^    "+name+r":", lines[i]))
    j = st
    while j+1 < e and not re.match(r"^    [a-z]+:", lines[j+1]): j += 1
    return st, j
for cls in ("question", "options", "rationale", "namespaces"):
    n = occ = 0
    for s, e in spans:
        blk = "\n".join(lines[fspan(s, e, cls)[0]:fspan(s, e, cls)[1]+1])
        c = len(STRICT.findall(blk))
        if c: n += 1; occ += c
    print(f"  {cls:12s} cases_with_hit={n:3d} occurrences={occ}")
PY
echo; echo "VERIFICATION COMPLETE. Log: verify/VERIFICATION.txt"
