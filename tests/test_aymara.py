
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima
import pytest
import sys


def test_unknownLanguage():
    with pytest.raises(Exception):
        lima = aymara.lima.Lima(lang="this_is_not_a_language_name")


def test_analyzeText():
    lima = aymara.lima.Lima()
    result = lima.analyzeText("This is a text on 02/05/2022.", lang="eng",
                              pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_analyzeText_init_with_lang():
    lima = aymara.lima.Lima("eng")
    result = lima.analyzeText("This is a text on 02/05/2022.", pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_functor():
    lima = aymara.lima.Lima("eng")
    result = lima("This is a text on 02/05/2022.")
    assert result is not None and type(result) == aymara.lima.Doc


def test_doc_size():
    lima = aymara.lima.Lima("eng")
    result = lima("This is a text on 02/05/2022.")
    assert len(result) > 0

