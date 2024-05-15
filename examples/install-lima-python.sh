#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# You should first create a virtual environment for lima-python
# If using virtualenvwrapper, this could be done with
mkvirtualenv aymara

# At time of writing, you have to download the lima-python wheel instead of
# using directly pip
wget https://github.com/aymara/lima-python/releases/download/continuous/aymara-0.5.0b6-cp37-abi3-manylinux_2_28_x86_64.whl

# Then install lima-python
pip install ./aymara-0.5.0b6-cp37-abi3-manylinux_2_28_x86_64.whl


