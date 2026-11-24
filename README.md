# LIMA python bindings

[![Downloads](https://static.pepy.tech/personalized-badge/aymara?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/aymara)

## Introducing LIMA

LIMA is a multilingual linguistic analyzer developed by the [CEA LIST](http://www-list.cea.fr/en), [LASTI laboratory](http://www.kalisteo.fr/en/index.htm) (French acronym for Text and Image Semantic Analysis Laboratory). LIMA is Free Software, available under the MIT license.

LIMA has [state of the art performance for more than 60 languages](https://huggingface.co/aymaralima/deeplima) thanks to its recent deep learning (neural network) based modules. But it includes also a very powerful rules based mechanism called ModEx allowing to quickly extract information (entities, relations, events…) in new domains where annotated data does not exist.

For more information, detailed installation instructions and documentation, please refer to [the LIMA documentation](https://aymara.github.io/lima/).


## Installation

LIMA python bindings are currently available **under Linux only** (x86_64).

Under Linux with Python >= 3.9 and an **upgraded pip**, which picks the right
one of the two wheels of each release:

| Wheel | Qt | Python | Systems |
| --- | --- | --- | --- |
| `manylinux_2_34` | 6.12 | 3.10 to 3.15 | glibc >= 2.34 (Ubuntu 22.04+, Debian 12+, RHEL 9+...) |
| `manylinux_2_28` | 6.9 | 3.9 to 3.13 | glibc >= 2.28 (older systems, and Python 3.9) |


```bash
# Upgrading pip is fundamental in order to obtain the correct LIMA version
$ pip install --upgrade pip
$ pip install aymara
$ lima_models -i eng
# Either simply use the lima command to produce an analysis of a file in CoNLLU format:
$ lima <path to the file to analyse>
# Or use the python API:
$ python
>>> import aymara.lima
>>> nlp = aymara.lima.Lima("ud-eng")
>>> doc = nlp('Hello, World!')
>>> print(doc[0].lemma)
hello
>>> print(repr(doc))
1       Hello   hello   INTJ    _       _               0       root    _       Pos=0|Len=5
2       ,       ,       PUNCT   _       _               1       punct   _       Pos=5|Len=1
3       World   World   PROPN   _       Number:Sing     1       vocative        _       Pos=7|Len=5
4       !       !       PUNCT   _       _               1       punct   _       Pos=12|Len=1
```

`lima_models -i eng` installs the default English model, which
`aymara.lima.Lima("ud-eng")` then uses (`lima_models -a` lists the languages
and models available). Check the [language models documentation](https://aymara.github.io/lima/usage/models/) for more information about using these models.

## Running


```python
$ lima <utf-8 text file to analyze>
# OR
$ python
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

Create a `Lima` analyzer once and reuse it: initialization loads the models,
and an analyzer with a neural pipeline (`deepud`) uses about 3 GB of memory. Up
to aymara 0.7.1, this memory is not freed when the analyzer is deleted, so
avoid creating several in one process. From the next version, deleting the last
analyzer of a language frees its models.

For French, use `ud-fra` (after `lima_models -i fra`). The `deepud` pipeline of
`ud-eng` and `ud-fra` also recognizes named entities (persons, locations,
organizations, dates, amounts...), available as `doc.ents`:

```python
>>> nlp = aymara.lima.Lima("ud-fra")
>>> doc = nlp("Jean Dupont a visité Paris le 12 janvier 2021.")
>>> [(ent.text, ent.label) for ent in doc.ents]
```

The legacy rule-based languages `eng`, `fre` and `por` and their pipelines
(`main`...) are deprecated and no longer distributed: these names now select
`ud-eng`, `ud-fra` and `ud-por` and the `deepud` pipeline, with a
`DeprecationWarning`.


## Python bindings API documentation

The Lima python API documentation is [part of the LIMA documentation](https://aymara.github.io/lima/reference/python-api/),
along with a [user guide for Python](https://aymara.github.io/lima/usage/python/).

## Configuration and customization

To configure finely LIMA for your needs, follow the same instructions as for the native C++ tools, described in [Configuring LIMA](https://aymara.github.io/lima/usage/configuration/).


# PySide LIMA python bindings build and deploy instructions

## Building the wheel

The CI (`.github/workflows/build-qt6.yml`) builds both wheels, on the LIMA
images of the same configuration (built by aymara/lima's own `build-qt6.yml`):

- `manylinux_2_28`, Qt 6.9.3, built with Python 3.9 (`cp39-abi3`), tested on
  Python 3.9 and 3.13;
- `manylinux_2_34`, Qt 6.12.0, built with Python 3.10 (`cp310-abi3`), tested on
  Python 3.10 and 3.15.

The wheels of the `master` branch are published in the
[`continuous` prerelease](https://github.com/aymara/lima-python/releases/tag/continuous).

To build the `manylinux_2_28` wheel locally, with Docker:

```bash
./gbuild-manylinux_2_28.sh
```

## Releasing

The version is set in `aymara/version.py` only. Update it and `CHANGES.md`, then
push a `v<version>` tag (e.g. `v0.7.1`): the CI builds and tests both wheels and
publishes them to PyPI. The tag must match `aymara/version.py`.

# Developer Notes
To see the wheels accepted on current system:

```
>>> from packaging.tags import sys_tags
>>> [str(t) for t in sys_tags()]
```

See: 
  * https://cibuildwheel.readthedocs.io/en/stable/
  * https://wiki.qt.io/Qt_for_Python
  * https://www.qt.io/blog/2018/05/31/write-python-bindings


# License notes

Some part of this API are largely inspired by the spaCy one and some text of the documentation are reproduced from the
spaCy documentation. spaCy is also released under the MIT license. We thus reproduce its copyright notice below:

```
The MIT License (MIT)

Copyright (C) 2016-2022 ExplosionAI GmbH, 2016 spaCy GmbH, 2015 Matthew Honnibal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
