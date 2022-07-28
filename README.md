# LIMA python bindings

[![Downloads](https://static.pepy.tech/personalized-badge/aymara?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/aymara)

## Introducing LIMA

LIMA is a multilingual linguistic analyzer developed by the [CEA LIST](http://www-list.cea.fr/en), [LASTI laboratory](http://www.kalisteo.fr/en/index.htm) (French acronym for Text and Image Semantic Analysis Laboratory). LIMA is Free Software, available under the MIT license.

LIMA has [state of the art performance for more than 60 languages](https://github.com/aymara/lima-models/blob/master/eval.md) thanks to its recent deep learning (neural network) based modules. But it includes also a very powerful rules based mechanism called ModEx allowing to quickly extract information (entities, relations, events…) in new domains where annotated data does not exist.

For more information, detailed installation instructions and documentation, please refer to [the LIMA Wiki](https://github.com/aymara/lima/wiki).


## Installation

LIMA python bindings are currently available for python >= 3.7 and < 4, under Linux. Install with:

```bash
$ pip install --upgrade pip # IMPORTANT: LIMA needs a recent pip
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


```python
$ python
Python 3.8.10 (default, Nov 26 2021, 20:14:08)
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import aymara.lima
>>> l = aymara.lima.Lima("ud-eng")
>>> r = l.analyzeText("The author wrote a novel.", lang="ud-eng")
>>> print(r)
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

Note that some error messages could be displayed during the Lima object instantiation. If you get a valid result, you can ignore them. Most of them are debug messages that will be removed in a later version.

You can replace the language (`ud-eng`) used by `eng` to use the legacy pipeline. This is the same for `ud-fra` and `fre`. Note that legacy pipelines do not use the Universal Dependencies tagset, but a proprietary one.

## Configuration and customization

To configure finely LIMA for your needs, follow the same instructions as for the native C++ tools, available here: [[https://github.com/aymara/lima/wiki/LIMA-User-Manual]].


# PySide LIMA python bindings build and deploy instructions

## Building the wheel

Use docker using the `gbuild-manylinux_2_28.sh` script:

```bash
./gbuild-manylinux_2_28.sh.sh
```

## Deploying the wheel

Use Twine (`pip install twine`) to deploy the whell to PyPI with the help of the `deploy.sh` script.

```bash
./deploy-manylinux_2_28.sh
```

# Developper Notes
To see the wheels accepted on current system:

```
>>> from packaging.tags import sys_tags
>>> [str(t) for t in sys_tags()]
```

See: 
  * https://cibuildwheel.readthedocs.io/en/stable/
  * https://wiki.qt.io/Qt_for_Python
  * https://www.qt.io/blog/2018/05/31/write-python-bindings

