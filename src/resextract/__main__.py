"""``python -m resextract`` — the module form of the console script.

U6.9 found that this invocation had no ``__main__`` at all
(``No module named resextract.__main__``, exit 1), so the packaging exposed the
console script and ``python -m resextract.cli`` but not ``python -m
resextract``.  This module deliberately does nothing but hand off to
``resextract.cli.main``: the bind decision is ``dashboard.app.check_bind_host``
and is reached through exactly the same dispatcher as ``.venv/bin/resextract``,
so this path cannot disagree with it.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
