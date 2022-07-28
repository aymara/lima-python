#!/bin/bash
# Copyright 2019-2022 CEA LIST
# SPDX-FileCopyrightText: 2019-2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

#Fail if anything goes wrong
set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace


LIMA_PYTHON_VERSION=$(python aymara/version.py)

python3 -m twine upload aymara-${LIMA_PYTHON_VERSION}-*-manylinux_2_28_x86_64.whl
