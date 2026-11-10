import json, urllib.request
_orig = urllib.request.urlopen
def _patched(url, *a, **kw):
    try:
        if isinstance(url, urllib.request.Request) and str(url.full_url).endswith("/v1/chat/completions") and getattr(url, "data", None):
            obj = json.loads(url.data.decode("utf-8"))
            if obj.get("model") is None:
                obj["model"] = "occamy-1.0"
                url.data = json.dumps(obj).encode("utf-8")
                if "Content-length" in (url.headers or {}):
                    url.headers["Content-length"] = str(len(url.data))
    except Exception:
        pass
    return _orig(url, *a, **kw)
urllib.request.urlopen = _patched
