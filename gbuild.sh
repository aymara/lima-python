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

docker build --progress=plain --build-arg GCC_VERSION="${GCC_VERSION}" --build-arg LLVM_VERSION="${LLVM_VERSION}" --build-arg QT_FULL_VERSION="${QT_FULL_VERSION}" --build-arg QT_VERSION_MAJOR="${QT_VERSION_MAJOR}" --build-arg QT_VERSION_MINOR="${QT_VERSION_MINOR}" --build-arg QT_VERSION_PATCH="${QT_VERSION_PATCH}" --build-arg QT_VERSION="${QT_VERSION}" --build-arg PYTHON_VERSION="${PYTHON_VERSION}" --build-arg PYTHON_SHORT_VERSION=${PYTHON_SHORT_VERSION} --build-arg PYTHON_FULL_VERSION=${PYTHON_FULL_VERSION} --build-arg LIMA_PYTHON_VERSION=${LIMA_PYTHON_VERSION} -t aymara/lima-qt${QT_VERSION}-python${PYTHON_VERSION}:latest .
docker create -ti --name dummy aymara/lima-qt${QT_VERSION}-python${PYTHON_VERSION}:latest bash
docker cp dummy:/lima-python/wheelhouse/aymara-${LIMA_PYTHON_VERSION}-${PYTHON_SHORT_VERSION}-manylinux_2_24_x86_64.whl .
docker rm -f dummy
docker push aymara/lima-python${PYTHON_VERSION}:latest
