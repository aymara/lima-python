# SPDX-FileCopyrightText: 2022-2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""Python bindings to the LIMA linguistic analyzer.

``import aymara`` is enough: its submodules (``aymara.lima``,
``aymara.lima_models``, ...) are imported on first use, so that
``aymara.lima.Lima("ud-eng")`` works as ``import aymara.lima`` then
``aymara.lima.Lima("ud-eng")`` does, and ``import aymara`` alone does not
load LIMA's libraries.
"""

import importlib

_SUBMODULES = ("lima", "lima_models", "deeplima_models", "version")


def __getattr__(name):
    """Imports a submodule on its first access (PEP 562, Python >= 3.7)."""
    if name in _SUBMODULES:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + list(_SUBMODULES))
