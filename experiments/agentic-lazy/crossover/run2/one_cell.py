import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_cx2 as R
import cx_harness as H

def have(model, n, s, arm, cs):
    if not R.RUNS.exists(): return False
    for r in json.loads(R.RUNS.read_text()):
        if (r["model"], r["n_items"], r["size"], r["arm"], r["cache_state"]) == (model, n, s, arm, cs):
            return True
    return False

model, n, s, arm, cs = "qwen3.5-9b", 30, 30000, "l1", "warm"
if have(model, n, s, arm, cs):
    print("already recorded"); sys.exit(0)
items = H.load_items(n, s); index = H.item_index(items)
task, needed = H.task_for(n), H.needed_for(n)
print(f"running {model} n={n} size={s} {arm} {cs}", flush=True)
r = R.run_one(model, R.ENDPOINTS[model], arm, n, s, cs, 1, items, index, task, needed)
sums = json.loads(R.RUNS.read_text()) if R.RUNS.exists() else []
sums.append(r); R.save_runs(sums)
print("correct=%s facts=%s/%s rounds=%s prompt=%s cached=%s fetch=%s err=%s" % (
    r["correct"], r["facts_present"], r["facts_required"], r["rounds"],
    r["prompt_tokens"], r["cached_tokens"], r["fetch_count"], r["error"]), flush=True)
