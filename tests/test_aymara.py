
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima
import pytest
import sys
from pathlib import Path

lima = aymara.lima.Lima("ud-eng", pipes="deepud")
doc = lima("Give it back! He pleaded.")


def test__get_data_dir():
    assert ".local/share" in str(aymara.lima._get_data_dir("lima"))


def test_unknownLanguage():
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima(langs="this_is_not_a_language_name")


def test_analyzeText_lang_not_init():
    with pytest.raises(aymara.lima.LimaInternalError):
        result = aymara.lima.Lima().analyzeText("This is a text on 02/05/2022.",
                                                lang="wol", pipeline="main")
        print(result, file=sys.stderr)
        assert True


def test_analyzeText_pipeline_not_avail():
    with pytest.raises(aymara.lima.LimaInternalError):
        result = aymara.lima.Lima("ud-eng").analyzeText("This is a text on 02/05/2022.",
                                                        pipeline="other")
        print(result, file=sys.stderr)
        assert Truess


def test_analyzeText():
    result = aymara.lima.Lima().analyzeText("This is a text on 02/05/2022.", lang="eng",
                                            pipeline="main")
    print(result, file=sys.stderr)
    assert True


def test_analyzeText_init_with_lang():
    result = aymara.lima.Lima("ud-eng").analyzeText("This is a text on 02/05/2022.",
                                                    pipeline="deepud")
    print(result, file=sys.stderr)
    assert True


def test_analyzeText_init_with_lang_and_pipe():
    result = lima.analyzeText("This is a text on 02/05/2022.")
    print(result, file=sys.stderr)
    assert True


def test_functor():
    assert doc is not None and type(doc) == aymara.lima.Doc


def test_doc_size():
    assert len(doc) > 0


def test_doc_token_access():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    assert doc[0].text == "Give"
    assert doc[-1].text == "."
    span = doc[1:3]
    assert span.text == "it back"


def test_token_properties():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    token = doc[5]
    print(repr(token), file=sys.stderr)
    assert repr(token) == '5\tpleaded\tplead\tVERB\t_\tMood:Ind|Tense:Past|VerbForm:Fin\t_\troot\t_\tPos=17|Len=7'
    assert str(token) == "pleaded" == token.text
    assert len(token) == 7
    assert token.i == 5
    assert token.idx == 17
    assert token.ent_iob == "O"
    assert token.ent_type == "_"
    assert token.lemma == "plead"
    assert token.pos == "VERB"
    assert token.head == 0
    assert token.dep == "root"
    assert token.features == {'Mood': 'Ind', 'Tense': 'Past', 'VerbForm': 'Fin'}
    assert token.t_status == 't_small'
    assert token.is_alpha is True
    assert token.is_digit is False
    assert token.is_lower is True
    assert token.is_upper is False
    assert token.is_punct is False
    assert token.is_sent_start is False
    assert token.is_sent_end is False
    assert token.is_space is False
    assert token.is_bracket is False
    assert token.is_quote is False


def test_doc_sents():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("This is a sentence. Here's another...")
    sents = list(doc.sents)
    assert len(sents) == 2
    # # TODO impjement s.root
    # assert [s.root.text for s in sents] == ["is", "'s"]

def test_doc_ents():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    print("before", file=sys.stderr)
    doc = lima("John Doe lives in New York. And Jane Smith will meet him on Friday.")
    print("after", file=sys.stderr)
    ents = list(doc.ents)
    print("listed", file=sys.stderr)
    assert len(ents) == 4


def test_span_size():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == 3


def test_span_text():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert span[1].text == "back"
    assert span[1:3].text == "back!"


def test_span_len():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == 3


def test_span_iter():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == len(list(iter(span)))


def test_span_at():
    # doc = lima("Give it back! He pleaded.")
    # span = "it back!"
    span = doc[1:4]
    token = span[1]
    assert str(token) == "back"
    token = span[-1]
    assert str(token) == "!"
    subspan = span[:2]
    assert subspan.text == "it back"
    subspan = span[-2:-1]
    assert subspan.text == "back"


def test_span_properties():
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert span.text == "it back!"
    assert span.doc == doc
    assert span.start == 1
    assert span.end == 4
    assert span.start_char == 5
    assert span.end_char == 13
    assert span.label == ""


def test_export_system_conf():
    assert aymara.lima.Lima.export_system_conf(Path("/tmp/test_lima"))


def test_get_system_paths():
    """
    TODO add tests
    """
    conf, ress =  aymara.lima.Lima.get_system_paths()
    assert conf is not None
    assert ress is not None


