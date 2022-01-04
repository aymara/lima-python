# LIMA poetry package build instructions

Build, install and deploy this Pypi package using poetry

```bash
$ pip install poetry
$ poetry build
$ poetry install
$ poetry publish
```

More information: https://python-poetry.org/



# PySide2 LIMA python bindings build instructions (in progress)

First install pyside
```bash
# Install PySide2 and shiboken2 from source as binary installs are broken
# Done in /home/gael/Logiciels/
sudo apt install qtbase5-private-dev qtdeclarative5-private-dev
git clone https://code.qt.io/cgit/pyside/pyside-setup.git
cd pyside-setup
python setup.py install --cmake=/usr/bin/cmake --build-type=all
# fail with rcc execution error
cp /usr/bin/rcc /home/gael/Logiciels/pyside-setup/lima3_install/py3.8-qt5.15.3-64bit-release/bin/rcc
python setup.py install --cmake=/usr/bin/cmake --build-type=all
```


# To collect external shared libraries dependencies and include them in a wheel

https://github.com/pypa/auditwheel

# pybind11 based bindings
https://github.com/yssource/pybind11-qt-foo


https://scikit-build.readthedocs.io/en/latest/
https://discuss.python.org/t/notes-on-binary-wheel-packaging-for-c-library-wrappers/2609
https://github.com/riddell-stan/poetry-install-shared-lib-demo

Important information concerning the handling of dependencies between manylinux (debian image is docker 9), which only has GCC 6
while C++17 requires at least GCC 8, and glibc versions:
http://catherineh.github.io/programming/2021/11/16/python-binary-distributions-whls-with-c17-cmake-auditwheel-and-manylinux
Based on: https://martinopilia.com/posts/2018/09/15/building-python-extension.html

General information on python wheels
https://docs.python.org/3.7/distutils/setupscript.html
https://setuptools.pypa.io/en/latest/

A project that includes all what we seem to need
https://github.com/palaimon/fastfm2

# TODO

* Allow to find libraries inside the wheel without touching to LD_LIBRARY_PATH

