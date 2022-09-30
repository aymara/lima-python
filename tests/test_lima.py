#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-


# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymaralima.lima
import sys


def test_analyzeText():
    lima = aymaralima.lima.LimaAnalyzer()
    result = lima.analyzeText("This is a text on 02/05/2022.", lang="eng",
                              pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_analyzeText_init_with_lang():
    lima = aymaralima.lima.LimaAnalyzer("eng")
    result = lima.analyzeText("This is a text on 02/05/2022.", pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_functor():
    lima = aymaralima.lima.LimaAnalyzer("eng")
    result = lima("This is a text on 02/05/2022.")
    assert result is not None and type(result) == aymaralima.lima.Doc


def test_doc_size():
    lima = aymaralima.lima.Lima("eng")
    result = lima("This is a text on 02/05/2022.")
    assert len(result) > 0


# def test_install_model():
#     assert aymara.lima_models.install_language("end", force=True)
#
#
# def test_installed_model():
#     lima = aymara.lima.Lima("ud-eng")
#     result = lima("This is a text on 02/05/2022.")
#     assert result.len() > 0

