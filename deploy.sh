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

python3 -m twine upload aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl
