"""Experiment package for the context-cache study (unit U1).

The directory name contains a hyphen, so it is not importable as a normal
Python package; the modules are standalone and loaded by path:

* ``client.py``  -- thin ``httpx`` wrapper around SGLang ``/chat/completions``.
* ``runner.py``  -- cell matrix executor with an injected ``send`` callable.
* ``analyze.py`` -- pure analysis functions over ``CacheRow`` lists.

This ``__init__`` exists so the directory is a declared artifact root, not to
be imported.
"""
