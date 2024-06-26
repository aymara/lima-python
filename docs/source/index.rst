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

LIMA python bindings are currently available **under Linux only** (x86_64).

Under Linux with python >= 3.7 and < 4, and **upgraded pip**:

Upgrading pip is fundamental in order to obtain the correct LIMA version

.. code-block:: bash

   $ pip install --upgrade pip
   $ pip install aymara==0.5.0b6
   $ lima_models -l eng

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

LIMA has `state of the art performance for more than 60 languages <https://github.com/aymara/lima-models/blob/master/eval.md>`_ thanks to its recent deep learning (neural network) based modules. But it includes also a very powerful rules based mechanism called ModEx allowing to quickly extract information (entities, relations, events…) in new domains where annotated data does not exist.

For more information, installation instructions and documentation, please refer to `the LIMA Wiki <https://github.com/aymara/lima/wiki>`_.

