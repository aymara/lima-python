
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


def test_doc_token_access():
    doc = nlp("Give it back! He pleaded.")
    assert doc[0].text == "Give"
    assert doc[-1].text == "."
    span = doc[1:3]
    assert span.text == "it back"


def test_doc_sents():
    nlp = aymara.lima.Lima("eng")
    doc = nlp("This is a sentence. Here's another...")
    sents = list(doc.sents)
    assert len(sents) == 2
    ## TODO impjement s.root
    # assert [s.root.text for s in sents] == ["is", "'s"]


def test_span_size():
    nlp = aymara.lima.Lima("eng")
    doc = nlp("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == 3


def test_span_text():
    nlp = aymara.lima.Lima("eng")
    doc = nlp("Give it back! He pleaded.")
    span = doc[1:4]
    assert span[1].text == "back"
    assert span[1:3].text == "back!"


