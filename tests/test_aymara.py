
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima
import pytest
import sys
from pathlib import Path


def test__get_data_dir():
    print(f"test__get_data_dir", file=sys.stderr)
    assert aymara.lima._get_data_dir("lima").is_dir()


def test_unknownLanguage():
    print(f"test_unknownLanguage", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima(langs="this_is_not_a_language_name")


def test_lang_no_prefix():
    print(f"test_lang_no_prefix", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima(langs="cym")

# TODO test with several ud languages


text = "Give it back! He pleaded."


def test_several_instances():
    # Test with several analyzer instantiated and called alternatively
    print(f"test_several_instances", file=sys.stderr)
    lima1 = aymara.lima.Lima("eng", pipes="main")
    doc1 = lima1(text)
    assert doc1 is not None and type(doc1) == aymara.lima.Doc
    lima2 = aymara.lima.Lima("fre", pipes="main")
    doc2 = lima2("Et maintenant, du français.")
    assert doc2 is not None and type(doc2) == aymara.lima.Doc


def test_analyzeText_lang_not_str():
    print(f"test_analyzeText_lang_not_str", file=sys.stderr)
    with pytest.raises(TypeError):
        aymara.lima.Lima().analyzeText("This is a text on 02/05/2022.",
                                       lang=dict(), pipeline="main")


def test_functor_lang_not_str():
    print(f"test_functor_lang_not_str", file=sys.stderr)
    with pytest.raises(TypeError):
        aymara.lima.Lima()("This is a text on 02/05/2022.", lang=dict(),
                           pipeline="main")


def test_analyzeText_lang_not_init():
    print(f"test_analyzeText_lang_not_init", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima().analyzeText("This is a text on 02/05/2022.",
                                       lang="wol", pipeline="main")


def test_functor_lang_not_init():
    print(f"test_functor_lang_not_init", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima()("This is a text on 02/05/2022.",
                           lang="wol", pipeline="main")


def test_analyzeText_pipeline_none_lang_ud():
    print(f"test_analyzeText_pipeline_none_lang_ud", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        thelima = aymara.lima.Lima("ud-eng", pipes="")
        thelima.analyzeText("This is a text on 02/05/2022.", lang="ud-eng",
                            pipeline=None)


def test_functor_pipeline_none_lang_ud():
    print(f"test_functor_pipeline_none_lang_ud", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        thelima = aymara.lima.Lima("ud-eng", pipes="")
        thelima("This is a text on 02/05/2022.", lang="ud-eng", pipeline=None)


def test_analyzeText_pipeline_none_lang_eng():
    print(f"test_analyzeText_pipeline_none_lang_eng", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        thelima = aymara.lima.Lima("eng", pipes="")
        thelima.analyzeText("This is a text on 02/05/2022.", lang="eng", pipeline=None)


def test_functor_pipeline_none_lang_eng():
    print(f"test_functor_pipeline_none_lang_eng", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        thelima = aymara.lima.Lima("eng", pipes="")
        thelima("This is a text on 02/05/2022.", lang="eng", pipeline=None)


def test_functor_not_text():
    print(f"test_functor_not_text", file=sys.stderr)
    with pytest.raises(TypeError):
        result = aymara.lima.Lima("ud-eng", pipes="deepud")(dict())


def test_analyzeText_init_with_lang_and_pipe():
    print(f"test_analyzeText_init_with_lang_and_pipe", file=sys.stderr)
    thelima = aymara.lima.Lima("ud-eng", pipes="deepud")
    result = thelima.analyzeText("This is a text on 02/05/2022.")
    assert True


def test_analyzeText_init_with_lang():
    print(f"test_analyzeText_init_with_lang", file=sys.stderr)
    thelima = aymara.lima.Lima("ud-eng")
    result = thelima.analyzeText("This is a text on 02/05/2022.",
                                 pipeline="deepud")
    assert True


lima = aymara.lima.Lima("ud-eng", pipes="deepud")


def test_analyzeText_pipeline_not_avail():
    print(f"test_analyzeText_pipeline_not_avail", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        lima.analyzeText("This is a text on 02/05/2022.", pipeline="other")


def test_functor_pipeline_not_avail():
    print(f"test_functor_pipeline_not_avail", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        lima("This is a text on 02/05/2022.", pipeline="other")


def test_functor_meta_not_dict():
    print(f"test_functor_meta_not_dict", file=sys.stderr)
    with pytest.raises(TypeError):
        lima("This is a text on 02/05/2022.", pipeline="deepud",
             meta="wrong metadata")


def test_analyzeText_meta_not_dict():
    print(f"test_functor_meta_not_dict", file=sys.stderr)
    with pytest.raises(TypeError):
        lima.analyzeText("This is a text on 02/05/2022.", pipeline="deepud",
                         meta="wrong metadata")


def test_analyzeText_pipeline_not_str():
    print(f"test_analyzeText_pipeline_not_str", file=sys.stderr)
    with pytest.raises(TypeError):
        lima.analyzeText("This is a text on 02/05/2022.",
                         pipeline=["main", "deepud"])
    with pytest.raises(TypeError):
        lima("This is a text on 02/05/2022.", pipeline=["main", "deepud"])


def test_analyzeText_not_text():
    print(f"test_analyzeText_not_text", file=sys.stderr)
    with pytest.raises(TypeError):
        print(f"test_analyzeText_not_text in with", file=sys.stderr)
        result = lima.analyzeText(dict())
    with pytest.raises(TypeError):
        print(f"test_analyzeText_not_text in with", file=sys.stderr)
        result = lima(dict())


def test_analyzeText():
    print(f"test_analyzeText", file=sys.stderr)
    result = lima.analyzeText("This is a text on 02/05/2022.",
                              pipeline="deepud")
    assert True


doc = lima(text)


def test_functor():
    print(f"test_functor", file=sys.stderr)
    assert doc is not None and type(doc) == aymara.lima.Doc


def test_doc_size():
    print(f"test_doc_size", file=sys.stderr)
    assert len(doc) == 7


def test_doc_str():
    print(f"test_doc_str", file=sys.stderr)
    assert str(doc) == text


def test_doc_repr():
    print(f"test_doc_repr", file=sys.stderr)
    assert len(repr(doc).split("\n")) == 7


def test_doc_iter():
    print(f"test_doc_iter", file=sys.stderr)
    assert len(list(doc)) == 7


def test_doc_token_access():
    print(f"test_doc_token_access", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    assert doc[0].text == "Give"
    assert doc[-1].text == "."
    span = doc[1:3]
    assert span.text == "it back"


def test_token_properties():
    print(f"test_token_properties", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    token = doc[5]
    print(repr(token))
    assert repr(token) == '6\tpleaded\tplead\tVERB\t_\tMood:Ind|Tense:Past|VerbForm:Fin\t_\troot\t_\tPos=17|Len=7'
    assert str(token) == "pleaded" == token.text
    assert len(token) == 7
    assert token.i == 6
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
    print(f"test_doc_sents", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("This is a sentence. Here's another...")
    sents = list(doc.sents)
    assert len(sents) == 2
    # # TODO impjement s.root
    # assert [s.root.text for s in sents] == ["is", "'s"]


def test_doc_ents():
    print(f"test_doc_ents", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    ndoc = lima("John Doe lives in New York. And Jane Smith will meet him on Friday.")
    ents = list(ndoc.ents)
    assert len(ents) == 4


def test_span_size():
    print(f"test_span_size", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == 3


def test_span_text():
    print(f"test_span_text", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert span[1].text == "back"
    assert span[1:3].text == "back!"


def test_span_len():
    print(f"test_span_len", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == 3


def test_span_iter():
    print(f"test_span_iter", file=sys.stderr)
    # lima = aymara.lima.Lima("ud-eng", pipes="deepud")
    # doc = lima("Give it back! He pleaded.")
    span = doc[1:4]
    assert len(span) == len(list(iter(span)))


def test_span_get_item():
    print(f"test_span_get_item", file=sys.stderr)
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
    assert len(span[0:0]) == 0
    assert len(span[1:1]) == 0
    assert len(span[1:10]) == 2
    assert len(span[-12:1]) == 1
    assert len(span[1:-8]) == 0
    assert len(span[1:0]) == 0
    assert len(span[10:1]) == 0
    assert len(span[10:8]) == 0
    assert len(span[-2:-1]) == 1
    assert len(span[-21:-20]) == 0
    assert len(span[20:21]) == 0
    with pytest.raises(IndexError):
        span[-12]
    with pytest.raises(IndexError):
        span[12]


def test_span_properties():
    print(f"test_span_properties", file=sys.stderr)
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
    print(f"test_export_system_conf", file=sys.stderr)
    assert aymara.lima.Lima.export_system_conf(Path("/tmp/test_lima"))


def test_export_system_conf_none():
    print(f"test_export_system_conf", file=sys.stderr)
    assert aymara.lima.Lima.export_system_conf()


def test_get_system_paths():
    """
    TODO add tests
    """
    print(f"test_get_system_paths", file=sys.stderr)
    conf, ress = aymara.lima.Lima.get_system_paths()
    assert conf is not None
    assert ress is not None


