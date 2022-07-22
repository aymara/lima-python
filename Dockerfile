# Copyright 2019-2022 CEA LIST
# SPDX-FileCopyrightText: 2019-2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT
ARG PYTHON_VERSION=3.8
FROM aymara/lima-manylinux_2_24-python${PYTHON_VERSION}:latest
# FROM aymara/lima-manylinux_2_24:latest AS lima-python

RUN echo "PYTHON_VERSION=${PYTHON_VERSION}"

ARG PYTHON_VERSION=3.8
ARG PYTHON_SHORT_VERSION=38
# For python 3.7, it is 3.7.13
# For python 3.8, it is 3.8.12
ARG PYTHON_FULL_VERSION=3.8.12
ENV DEBIAN_FRONTEND=noninteractive


# ENV PYTHON_VERSION=$PYTHON_VERSION
# ENV PYTHON_SHORT_VERSION=$PYTHON_SHORT_VERSION
# ENV PYTHON_FULL_VERSION=$PYTHON_FULL_VERSION

# Setup
RUN apt --fix-broken install
RUN apt-get install -y libxslt1.1 zip
WORKDIR /
#RUN git clone https://github.com/python/cpython
#WORKDIR /cpython
#RUN git checkout 3.8

RUN python${PYTHON_VERSION} -m pip install scikit-build cmake ninja
ENV PATH="/opt/_internal/cpython-${PYTHON_FULL_VERSION}/bin:/opt/python/${PYTHON_SHORT_VERSION}/bin:${PATH}"
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
RUN python${PYTHON_VERSION} /lima-python/scripts/linuxdeploy.py /usr/lib/liblima*.so -d clib -o clib/libs.json
RUN /usr/bin/strip --strip-unneeded clib/lib/*.so
ARG LIMA_PYTHON_VERSION
COPY scripts tests utils bindings.h bindings.xml c2lc.txt CHANGES.md CMakeLists.txt deploy.sh LICENCE lima.h lima.cpp macros.h manageQt5.cmake MANIFEST.in python_env.sh README.md setup.py /lima-python/
RUN install -d /lima-python/aymara
COPY aymara/* /lima-python/aymara
ENV PATH=/opt/llvm/bin:$PATH
RUN python${PYTHON_VERSION} setup.py bdist_wheel
ENV LD_LIBRARY_PATH=/lima-python/_skbuild/linux-x86_64-${PYTHON_VERSION}/cmake-build:$LD_LIBRARY_PATH
RUN auditwheel repair /lima-python/dist/aymara-${LIMA_PYTHON_VERSION}-${PYTHON_SHORT_VERSION}-linux_x86_64.whl
WORKDIR /lima-python/wheelhouse
RUN unzip aymara-${LIMA_PYTHON_VERSION}-${PYTHON_SHORT_VERSION}-manylinux_2_24_x86_64.whl
RUN rm aymara-${LIMA_PYTHON_VERSION}-${PYTHON_SHORT_VERSION}-manylinux_2_24_x86_64.whl
WORKDIR /lima-python/wheelhouse/aymaralima
RUN rm -f liblima-* libgomp* libQt* libboost* libicu* libfasttext-lima.so  libtensorflow-for-lima.so
WORKDIR /lima-python/wheelhouse
RUN zip aymara-${LIMA_PYTHON_VERSION}-${PYTHON_SHORT_VERSION}-manylinux_2_24_x86_64.whl -r *
WORKDIR /lima-python

# WORKDIR /
