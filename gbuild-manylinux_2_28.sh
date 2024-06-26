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
source python_env_qt6.sh

echo "QT_VERSION=${QT_VERSION}"
echo "QT_FULL_VERSION=${QT_FULL_VERSION}"
echo "PYSIDE_VERSION=${PYSIDE_VERSION}"
echo "PYTHON_VERSION=${PYTHON_VERSION}"
echo "PYTHON_SHORT_VERSION=${PYTHON_SHORT_VERSION}"
echo "PYTHON_FULL_VERSION=${PYTHON_FULL_VERSION}"
echo "PYTHON_WHEEL_VERSION=${PYTHON_WHEEL_VERSION}"

docker pull aymara/lima-manylinux_2_28-qt${QT_VERSION}-python${PYTHON_VERSION}
#     --build-arg CACHE_BUST="$(date)" \
#     --no-cache \
docker build --progress=plain \
    --build-arg MANYLINUX_TAG="${MANYLINUX_TAG}" \
    --build-arg PYSIDE_VERSION="${PYSIDE_VERSION}" \
    --build-arg PYTHON_WHEEL_VERSION="${PYTHON_WHEEL_VERSION}" \
    --build-arg PYTHON_VERSION="${PYTHON_VERSION}" \
    --build-arg PYTHON_SHORT_VERSION="${PYTHON_SHORT_VERSION}" \
    --build-arg PYTHON_FULL_VERSION="${PYTHON_FULL_VERSION}" \
    --build-arg LIMA_PYTHON_VERSION="${LIMA_PYTHON_VERSION}" \
    --build-arg BRANCH="${BRANCH}" \
    --build-arg QT_FULL_VERSION="${QT_FULL_VERSION}" \
    --build-arg QT_VERSION_MAJOR="${QT_VERSION_MAJOR}" \
    --build-arg QT_VERSION_MINOR="${QT_VERSION_MINOR}" \
    --build-arg QT_VERSION_PATCH="${QT_VERSION_PATCH}" \
    --build-arg QT_VERSION="${QT_VERSION}" \
    -f Dockerfile-manylinux_2_28 -t aymara/lima-python${PYTHON_VERSION}:latest . 2>&1 | tee output.log

# docker pull docker.io/aymara/lima-python${PYTHON_VERSION}
docker create -ti --name dummy aymara/lima-python${PYTHON_VERSION}:latest bash
docker cp dummy:/lima-python/wheelhouse/aymara-${LIMA_PYTHON_VERSION}-${PYTHON_WHEEL_VERSION}-manylinux_2_28_x86_64.whl . || docker rm -f dummy && true
docker rm -f dummy

pip install ./aymara-0.5.0b6-cp37-abi3-manylinux_2_28_x86_64.whl --force-reinstall
pip install  pytest pytest-cov pytest-runner pytest-depends sphinx-test-reports
pytest

# docker build --no-cache -f Dockerfile-tests --build-arg PYTHON_VERSION=3.7 \
#     --build-arg LIMA_PYTHON_VERSION="${LIMA_PYTHON_VERSION}" .
