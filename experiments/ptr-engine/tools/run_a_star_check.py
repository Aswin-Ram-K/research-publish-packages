#!/usr/bin/env python3
"""RUN-A* acceptance check: the card's acceptance is 10 completed cells with rc 0.

Exit 0 only if all ten cells ran and none exited non-zero. It exits 1 on this grid because
cell 1 exited 6 (stop rule 7), which is the truthful verdict for the tranche.
"""
import json, os, sys
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "measure", "run-a-star.json")
d = json.load(open(p))
cells = d.get("cells") or []
ok = len(cells) == 10
bad = [c for c in cells if c.get("rc") != 0]
print("cells completed %d of 10; non-zero exits %d; stops %s"
      % (len(cells), len(bad), json.dumps(d.get("stops"))))
print("requests billed %d; remaining %s" % (d.get("new_requests") or 0, d.get("remaining")))
sys.exit(0 if (ok and not bad) else 1)
