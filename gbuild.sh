#!/bin/bash

#Fail if anything goes wrong
set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace

python setup.py bdist_wheel
# install -d build
# pushd build
# cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_GENERATOR=Ninja ..
# ninja
# popd
