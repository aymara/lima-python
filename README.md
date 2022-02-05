# LIMA python bindings


## Installation

LIMA python bindings are currently available for python 3.8 only. Install with:
```bash
$ pip install aymara
```

You can use it like that in English (eng) or French (fre) but it is preferable to use deep-learning based models. To install them, use the `lima_models.py` script:

```bash
$ lima_models.py -h
usage: lima_models.py [-h] [-i] [-l LANG] [-d DEST] [-s SELECT] [-f] [-L]

optional arguments:
  -h, --help            show this help message and exit
  -i, --info            print list of available languages and exit
  -l LANG, --lang LANG  install model for the given language name or language code (example: 'english'
                        or 'eng')
  -d DEST, --dest DEST  destination directory
  -s SELECT, --select SELECT
                        select particular models to install: tokenizer, morphosyntax, lemmatizer
                        (comma-separated list)
  -f, --force           force reinstallation of existing files
  -L, --list            list installed models
```

For example:
```bash
$ lima_models.py -l eng
```

## Running


```
$ python
Python 3.8.10 (default, Nov 26 2021, 20:14:08)
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import aymara.lima
>>> l = aymara.lima.Lima("ud-eng")
>>> r = l.analyzeText("The author wrote a novel.", lang="ud-eng")
>>> print(r.conll())
# sent_id = 1
# text = The author wrote a novel.
1       The     the     DET     _       Definite=Def|PronType=Art       2       det     _       Len=3|Pos=1
2       author  author  NOUN    _       Number=Sing     3       nsubj   _       Len=6|Pos=5
3       wrote   write   VERB    _       Mood=Ind|Tense=Past|VerbForm=Fin        0       root    _       Len=5|Pos=12
4       a       a       DET     _       Definite=Ind|PronType=Art       5       det     _       Len=1|Pos=18
5       novel   novel   NOUN    _       Number=Sing     3       obj     _       Len=5|Pos=20|SpaceAfter=No
6       .       .       PUNCT   _       _       3       punct   _       Len=1|Pos=25

>>>
```

Note that some error messages could be displayed during the Lima object instantiation. If you get a valid object, you can ignore them. Most of them are debug messages that will be removed in a later version.

You can replace the language (`ud-eng`) used by `eng` to use the legacy pipeline. This is the same for `ud-fra` and `fre`. Note that legacy pipelines do not use the Universal Dependencies tagset, but a proprietary one.

## Configuration and customization

To configure finely LIMA for your needs, follow the same instructions as for the native C++ tools, available here: [[https://github.com/aymara/lima/wiki/LIMA-User-Manual]].



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

# Building and deploying the wheel

```bash
docker build . -t lima-python:latest
docker create -ti --name dummy lima-python:latest bash
docker cp dummy:/lima-python/wheelhouse/aymara-0.3.3-cp38-cp38-manylinux_2_24_x86_64.whl .
docker rm -f dummy
scp aymara-0.3.3-cp38-cp38-manylinux_2_24_x86_64.whl gdechalendar@combava:/data/HTTP_FileServer/data/lima
```
