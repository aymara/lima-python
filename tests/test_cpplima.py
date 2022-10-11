#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-


# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymaralima.cpplima
import pytest
import sys


def test_analyzeText():
    lima = aymaralima.cpplima.LimaAnalyzer("ud-eng", "deepud",
                                           list(aymaralima.__path__)[-1])

    result = lima.analyzeText("This is a text on 02/05/2022.", lang="eng",
                              pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_functor():
    lima = aymaralima.cpplima.LimaAnalyzer("ud-eng", "deepud",
                                           list(aymaralima.__path__)[-1])
    result = lima("This is a text on 02/05/2022.")
    assert result is not None and type(result) == aymaralima.cpplima.Doc


# def test_doc_text():
#     lima = aymaralima.cpplima.LimaAnalyzer("ud-eng", "deepud",
#                                            list(aymaralima.__path__)[-1])
#     doc = lima("This is a text on 02/05/2022.")
#     print(doc.text())
#     if doc.error:
#         assert False, doc.errorMessage()
#     assert len(doc.text()) > 0
#
#
# def test_doc_size():
#     lima = aymaralima.cpplima.LimaAnalyzer("ud-eng", "deepud",
#                                            list(aymaralima.__path__)[-1])
#     doc = lima("This is a text on 02/05/2022.")
#     assert doc.len() > 0

