
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import os
import sys

from distutils.util import convert_path
from skbuild import setup  # This line replaces 'from setuptools import setup'

main_ns = {}
ver_path = convert_path('aymara/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

PYTHON_VERSION = os.environ.get("PYTHON_VERSION", "3.8")
PYTHON_SHORT_VERSION = os.environ.get("PYTHON_SHORT_VERSION", "cp38-cp38")
# For python 3.7, it is 3.7.13
# For python 3.8, it is 3.8.12
PYTHON_FULL_VERSION = os.environ.get("PYTHON_FULL_VERSION", "3.8.12")

include_dir = f"/opt/python/{PYTHON_SHORT_VERSION}/include/python{PYTHON_VERSION}"
if PYTHON_VERSION == "3.6" or PYTHON_VERSION == "3.7":
    include_dir = f"/opt/python/{PYTHON_SHORT_VERSION}/include/python{PYTHON_VERSION}m"
library_dir = f"/opt/python/{PYTHON_SHORT_VERSION}/lib/python{PYTHON_VERSION}"


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths


print(f"PYTHON_VERSION: {PYTHON_VERSION}", file=sys.stderr)
print(f"PYTHON_SHORT_VERSION: {PYTHON_SHORT_VERSION}", file=sys.stderr)
print(f"PYTHON_FULL_VERSION: {PYTHON_FULL_VERSION}", file=sys.stderr)
setup(
    name="aymara",
    version=main_ns['__version__'],
    author="Gaël de Chalendar",
    author_email="gael.de-chalendar@cea.fr",
    description="Python bindings to the LIMA linguistic analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aymara/lima",
    project_urls={
        "Bug Tracker": "https://github.com/aymara/lima/issues",
        "Wiki": "https://github.com/aymara/lima/wiki"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=f">={PYTHON_VERSION}",
    packages=['aymara', 'aymaralima'],
    install_requires=[
        'pip>=22.0',
        'pyconll',
        'pydantic',
        'requests',
        'shiboken6',
        'tqdm',
        'unix_ar',
        ],
    include_package_data=True,

    # A dictionary mapping package names to lists of glob patterns. For a complete description and examples, see the setuptools documentation section on Including Data Files. You do not need to use this option if you are using include_package_data, unless you need to add e.g. files that are generated by your setup script and build process. (And are therefore not in source control or are files that you don’t want to include in your source distribution.)
    #package_data={'aymaralima': extra_files},
    #package_data={},

    # Dictionary mapping package names to lists of glob patterns that should be excluded from the package directories. You can use this to trim back any excess files included by include_package_data. For a complete description and examples, see the setuptools documentation section on Including Data Files.
    exclude_package_data={},

    # Sequence of (directory, files) pairs. Each (directory, files) pair in the sequence specifies the installation directory and the files to install there. More details in the Installing Additional Files section of the setuptools documentation.
    #data_files=[('aymaralima', extra_files)],
    #data_files=[('aymaralima', ['aymaralima/lima_models.py', 'aymaralima/lima.py'])],

    #    cmake_install_dir= 'aymara/',
    cmake_minimum_required_version='3.15',
    setup_requires=['cmake', 'pytest', 'pytest-cov', 'pytest-runner', 'pytest-depends'],
    tests_require=['pytest', 'pytest-cov', 'pytest-depends', 'sphinx-test-reports',
                   'pyconll', 'pydantic', 'shiboken6'],
    cmake_args=['-DCMAKE_BUILD_TYPE=RelWithDebInfo',
                '-DCMAKE_GENERATOR=Ninja',
                f"-DPython3_INCLUDE_DIR={include_dir}",
                f"-DPython3_LIBRARY={library_dir}"],
    scripts=['aymara/lima_models.py'],
)
