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
source python_env.sh

echo "PYTHON_VERSION=${PYTHON_VERSION}"
echo "PYTHON_SHORT_VERSION=${PYTHON_SHORT_VERSION}"
echo "PYTHON_FULL_VERSION=${PYTHON_FULL_VERSION}"
echo "PYTHON_WHEEL_VERSION=${PYTHON_WHEEL_VERSION}"

# --no-cache
docker build --progress=plain \
    --build-arg PYTHON_WHEEL_VERSION="${PYTHON_WHEEL_VERSION}" \
    --build-arg PYTHON_VERSION="${PYTHON_VERSION}" \
    --build-arg PYTHON_SHORT_VERSION=${PYTHON_SHORT_VERSION} \
    --build-arg PYTHON_FULL_VERSION=${PYTHON_FULL_VERSION} \
    --build-arg LIMA_PYTHON_VERSION=${LIMA_PYTHON_VERSION} \
    -f Dockerfile-manylinux_2_28 -t lima-python${PYTHON_VERSION}:latest .

docker create -ti --name dummy lima-python${PYTHON_VERSION}:latest bash
docker cp dummy:/lima-python/wheelhouse/aymara-${LIMA_PYTHON_VERSION}-${PYTHON_WHEEL_VERSION}-manylinux_2_28_x86_64.whl .
docker rm -f dummy

