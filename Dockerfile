FROM aymara/lima-manylinux_2_24 AS lima-python

ENV DEBIAN_FRONTEND=noninteractive

# Setup
RUN apt --fix-broken install
RUN apt-get install -y libxslt1.1
WORKDIR /
#RUN git clone https://github.com/python/cpython
#WORKDIR /cpython
#RUN git checkout 3.8

RUN python3.8 -m pip install scikit-build cmake ninja
ENV PATH="/opt/python/cp38-cp38/bin:${PATH}"
RUN cmake --version

# Build LIMA wheel
WORKDIR /lima-python
COPY . /lima-python
RUN install -d clib/lib
RUN cp -R /usr/share/apps/lima/resources /lima-python/aymara
RUN install -d /lima-python/aymara/config
RUN cp -R /usr/share/config/lima/* /lima-python/aymara/config
RUN python3 /lima-python/scripts/linuxdeploy.py /usr/lib/liblima*.so -d clib -o clib/libs.json
RUN python3.8 setup.py bdist_wheel
ENV LD_LIBRARY_PATH=/lima-python/_skbuild/linux-x86_64-3.8/cmake-build:$LD_LIBRARY_PATH
RUN auditwheel repair /lima-python/dist/aymara-0.3.0-cp38-cp38-linux_x86_64.whl

