#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022-2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""Former name of lima_models: the deep learning models are now the only LIMA
models, installed by aymara.lima_models (the lima_models command)."""

from aymara.lima_models import (default_udlang, info, install_language,  # noqa: F401
                                list_installed_models, main, remove_language)

if __name__ == "__main__":  # pragma: no cover
    main()
