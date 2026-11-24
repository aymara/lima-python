# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""LIMA native libraries (Windows).

The cpplima module needs shiboken6's DLL, from the shiboken6 package (not
vendored: there must be a single shiboken runtime in the process). Importing
shiboken6 adds its directory to the DLL search path. The other DLLs, LIMA's
included, are vendored in aymara.libs by delvewheel, which adds that directory
to the DLL search path.
"""

import shiboken6  # noqa: F401
