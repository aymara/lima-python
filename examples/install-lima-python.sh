#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# You should first create a virtual environment for lima-python
# If using virtualenvwrapper, this could be done with
mkvirtualenv aymara

# Install lima-python from PyPI (a recent pip is needed to get the wheel)
pip install --upgrade pip
pip install aymara


