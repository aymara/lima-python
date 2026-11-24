#!/bin/bash
# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT
#
# Builds the macOS wheel of aymara (abi3, Python >= 3.10) against an installed
# (or extracted) LIMA, and makes it self-contained (scripts/prepare_wheel_macos.py).
#
# Usage, from the root of lima-python, with a Python having the build
# requirements installed (setuptools wheel scikit-build cmake ninja
# shiboken6==<Qt version> shiboken6_generator==<Qt version>
# PySide6_Essentials==<Qt version>):
#   scripts/build-wheel-macos.sh <LIMA installation> <Qt dir> [out dir] [include dirs...]
# - Qt dir: Qt for macOS, e.g. ~/Qt/6.12.0/macos (its version must be shiboken6's)
# - include dirs: of the third-party headers LIMA's include (Boost, ICU)
# MACOSX_DEPLOYMENT_TARGET (default 15.0) must not be lower than the one of the
# libraries LIMA was built with (e.g. Homebrew's).
set -euo pipefail

LIMA_DIST=$(cd "$1" && pwd)
QT_DIR=$(cd "$2" && pwd)
OUT_DIR=${3:-wheelhouse}
shift 3 || shift $#
for inc in "$@"; do
    export CPATH="$inc${CPATH:+:$CPATH}"
done

export LIMA_DIST
export QT_FULL_VERSION=$(basename "$(dirname "$QT_DIR")")
export Qt_INSTALL_DIR="$QT_DIR"
export CMAKE_PREFIX_PATH="$QT_DIR"
export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-15.0}
site_packages=$(python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")

rm -rf _skbuild dist
echo "Building the wheel (Qt $QT_FULL_VERSION, LIMA in $LIMA_DIST, macOS >= $MACOSX_DEPLOYMENT_TARGET)"
python setup.py bdist_wheel --py-limited-api=cp310
python scripts/prepare_wheel_macos.py dist/*.whl "$LIMA_DIST/lib" "$site_packages/PySide6" "$OUT_DIR"
ls -l "$OUT_DIR"/*.whl
