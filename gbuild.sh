#!/bin/bash

#Fail if anything goes wrong
set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace

LIMA_PYTHON_VERSION="0.3.3"

docker build . -t lima-python:latest --build-arg LIMA_PYTHON_VERSION=${LIMA_PYTHON_VERSION}
docker create -ti --name dummy lima-python:latest bash
docker cp dummy:/lima-python/wheelhouse/aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl .
docker rm -f dummy
scp aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl gdechalendar@combava:/data/HTTP_FileServer/data/lima
