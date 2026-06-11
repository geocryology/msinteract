"""
conftest.py – pytest configuration for msinteract tests.

The ``parameters`` and ``conversion`` modules (imported via
``msinteract/__init__.py``) depend on the optional ``groundmodel`` package,
which may not be installed in all environments.  Mock it out here so that
importing ``msinteract.run_options`` does not fail in those environments.
"""
import sys
from unittest.mock import MagicMock

_groundmodel_mods = [
    "groundmodel",
    "groundmodel.core",
    "groundmodel.core.geometry",
    "groundmodel.core.column",
    "groundmodel.core.layer",
    "groundmodel.lexicon",
    "groundmodel.logic",
]
for _mod in _groundmodel_mods:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
