# Copyright 2019-2022 CEA LIST
# SPDX-FileCopyrightText: 2019-2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

FROM aymara/lima-manylinux_2_24:latest AS lima-python

ENV DEBIAN_FRONTEND=noninteractive

# Setup
RUN apt --fix-broken install
RUN apt-get install -y libxslt1.1 zip
WORKDIR /
#RUN git clone https://github.com/python/cpython
#WORKDIR /cpython
#RUN git checkout 3.8

RUN python3.8 -m pip install scikit-build cmake ninja
ENV PATH="/opt/python/cp38-cp38/bin:${PATH}"
RUN cmake --version

# Build LIMA wheel
RUN install -d /lima-python/scripts
COPY scripts/linuxdeploy.py /lima-python/scripts
WORKDIR /lima-python
RUN install -d clib/lib
RUN install -d /lima-python/aymaralima
RUN cp -R /usr/share/apps/lima/resources /lima-python/aymaralima
RUN install -d /lima-python/aymaralima/config
RUN cp -R /usr/share/config/lima/* /lima-python/aymaralima/config
RUN python3.8 /lima-python/scripts/linuxdeploy.py /usr/lib/liblima*.so -d clib -o clib/libs.json
RUN /usr/bin/strip --strip-unneeded clib/lib/*.so
ARG LIMA_PYTHON_VERSION
COPY . /lima-python
RUN python3.8 setup.py bdist_wheel
ENV LD_LIBRARY_PATH=/lima-python/_skbuild/linux-x86_64-3.8/cmake-build:$LD_LIBRARY_PATH
RUN auditwheel repair /lima-python/dist/aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-linux_x86_64.whl
WORKDIR /lima-python/wheelhouse
RUN unzip aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl
RUN rm aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl
WORKDIR /lima-python/wheelhouse/aymaralima
RUN rm -f liblima-* libgomp* libQt* libboost* libicu* libfasttext-lima.so  libtensorflow-for-lima.so
WORKDIR /lima-python/wheelhouse
RUN zip aymara-${LIMA_PYTHON_VERSION}-cp38-cp38-manylinux_2_24_x86_64.whl -r *
WORKDIR /lima-python

# WORKDIR /
