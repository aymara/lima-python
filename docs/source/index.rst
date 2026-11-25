.. Lima documentation master file, created by
   sphinx-quickstart on Mon Oct  3 18:04:15 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

##################################
LIMA - Libre Multilingual Analyzer
##################################

.. image:: _static/lima-logo.png

.. toctree::
   :maxdepth: 3
   :caption: Contents:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



TL;DR
=====

LIMA python bindings are available under Linux (x86_64), Windows (x64) and
macOS (Apple Silicon).

With an **upgraded pip**, which picks the right wheel: under Linux with Python
>= 3.9, ``manylinux_2_34`` (Qt 6.12, Python 3.10 to 3.15, glibc >= 2.34) or
``manylinux_2_28`` (Qt 6.9, Python 3.9 to 3.13, glibc >= 2.28); ``win_amd64``
(Windows 10/11 x64, Python >= 3.10); ``macosx_15_0_arm64`` (macOS >= 15 on
Apple Silicon, Python >= 3.10).

Upgrading pip is fundamental in order to obtain the correct LIMA version

.. code-block:: bash

   $ pip install --upgrade pip
   $ pip install aymara
   $ lima_models -i eng

Either simply use the lima command to produce an analysis of a file in CoNLLU format:

.. code-block:: bash

   $ lima <path to the file to analyse>

Or use the python API:

.. code-block:: bash

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



Introducing LIMA
================

LIMA is a multilingual linguistic analyzer developed by the `CEA LIST <http://www-list.cea.fr/en>`_, `LASTI laboratory <http://www.kalisteo.fr/en/index.htm>`_ (French acronym for Text and Image Semantic Analysis Laboratory). LIMA is Free Software, available under the MIT license.

LIMA has `state of the art performance for more than 60 languages <https://huggingface.co/aymaralima/deeplima>`_ thanks to its recent deep learning (neural network) based modules. But it includes also a very powerful rules based mechanism called ModEx allowing to quickly extract information (entities, relations, events…) in new domains where annotated data does not exist.

For more information, installation instructions and documentation, please refer to `the LIMA documentation <https://aymara.github.io/lima/>`_.

