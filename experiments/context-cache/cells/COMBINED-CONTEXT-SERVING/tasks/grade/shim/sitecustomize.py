import os
import sys

FORBIDDEN = {"socket", "urllib", "http.client", "requests", "httpx"}
# normalize top-level names
TOP = {"socket", "urllib", "requests", "httpx", "http"}

LOG = os.environ.get("NETWORK_LOG")

def _log(module):
    if LOG:
        try:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(module + "\n")
        except Exception:
            pass

class _Hook:
    def find_spec(self, name, path, target=None):
        top = name.split(".")[0]
        # detect forbidden top-level or http.client submodule
        fired = False
        mod = None
        if name in FORBIDDEN:
            fired = True
            mod = name
        elif top in ("socket", "urllib", "requests", "httpx"):
            fired = True
            mod = top
        elif name == "http.client" or name.startswith("http.client"):
            fired = True
            mod = "http.client"
        elif top == "http" and (name == "http.client" or "client" in name.split(".")):
            # catch http.client specifically
            if "client" in name.split("."):
                fired = True
                mod = "http.client"
        if fired:
            _log(mod)
            raise ImportError(f"network module forbidden: {mod}")
        return None

sys.meta_path.insert(0, _Hook())
PYTHONDONTWRITEBYTECODE = True
PYTHONDONTWRITEBYTECODE = True
