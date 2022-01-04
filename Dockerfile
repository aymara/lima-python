FROM aymara/lima-manylinux_2_24

ENV DEBIAN_FRONTEND=noninteractive

# Setup
RUN apt --fix-broken install
WORKDIR /
#RUN git clone https://github.com/python/cpython
#WORKDIR /cpython
#RUN git checkout 3.8

RUN python3.8 -m pip install scikit-build cmake ninja
ENV PATH="/opt/python/cp38-cp38/bin:${PATH}"
RUN cmake --version

ARG QT_VERSION=5.15.2
ENV QMAKESPEC=linux-g++ \
    QT_PATH=/opt/qt \
    QT_PLATFORM=gcc_64

ENV \
    PATH=${QT_PATH}/${QT_VERSION}/${QT_PLATFORM}/bin:$PATH
RUN python3.8 -m pip install aqtinstall
RUN aqt install-qt linux desktop ${QT_VERSION} ${QT_PLATFORM} -O ${QT_PATH}

WORKDIR /
RUN wget -q https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-13.0.0.tar.gz
RUN tar xf llvmorg-13.0.0.tar.gz
WORKDIR /llvm-project-llvmorg-13.0.0
RUN cmake -S llvm -B build -G Ninja -DLLVM_PARALLEL_LINK_JOBS=1 -DCMAKE_BUILD_TYPE=Release -DLLVM_BUILD_LLVM_DYLIB=ON -DLLVM_ENABLE_PROJECTS="clang"
# -DLLVM_USE_LINKER=gold -DLLVM_USE_SPLIT_DWARF=ON
RUN cmake --build build
RUN cmake --install build


# Install PySide2 and shiboken2 from source as binary installs are broken
# Done in /home/gael/Logiciels/
WORKDIR /
RUN git clone https://code.qt.io/cgit/pyside/pyside-setup.git
WORKDIR /pyside-setup
RUN git checkout 5.15.2
RUN install -d /opt/_internal/cpython-3.8.12/lib/x86_64-linux-gnu/
RUN touch /opt/_internal/cpython-3.8.12/lib/x86_64-linux-gnu/libpython3.8.a

RUN apt-get update -y -qq && apt-get install -y libpulse-mainloop-glib0
RUN python3.8 setup.py install --cmake=/opt/python/cp38-cp38/bin/cmake --build-type=all


# Build LIMA wheel
RUN mkdir /lima-python
COPY . /lima-python
WORKDIR /lima-python
RUN python3.8 setup.py bdist_wheel
