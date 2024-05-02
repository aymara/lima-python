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

.. code-block:: bash

   # Upgrading pip is fundamental in order to obtain the correct LIMA version
   $ pip install --upgrade pip
   $ pip install aymara==0.4.2
   $ lima_models.py -i eng
   $ python

.. code-block:: bash

   >>> import aymara.lima
   >>> lima = aymara.lima.Lima("ud-eng")
   >>> doc = lima('Hello, World!')
   >>> print(doc[0].lemma)
   hello
   >>> print(repr(doc))
   # sent_id = 1
   # text = Hello, World!
   1       Hello   hello   INTJ    _       _               0       root      _ Len=5|Pos=1|SpaceAfter=No
   2       ,       ,       PUNCT   _       _               1       punct     _ Len=1|Pos=6
   3       World   World   PROPN   _       Number=Sing     1       vocative  _ Len=5|Pos=8|SpaceAfter=No
   4       !       !       PUNCT   _       _               1       punct     _ Len=1|Pos=13

Introducing LIMA
================

LIMA is a multilingual linguistic analyzer developed by the `CEA LIST <http://www-list.cea.fr/en>`_, `LASTI laboratory <http://www.kalisteo.fr/en/index.htm>`_ (French acronym for Text and Image Semantic Analysis Laboratory). LIMA is Free Software, available under the MIT license.

LIMA has `state of the art performance for more than 60 languages <https://github.com/aymara/lima-models/blob/master/eval.md>`_ thanks to its recent deep learning (neural network) based modules. But it includes also a very powerful rules based mechanism called ModEx allowing to quickly extract information (entities, relations, events…) in new domains where annotated data does not exist.

For more information, installation instructions and documentation, please refer to `the LIMA Wiki <https://github.com/aymara/lima/wiki>`_.

