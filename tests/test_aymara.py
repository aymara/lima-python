
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima
import json
import pytest
import sys
from pathlib import Path


def test__get_data_dir():
    print(f"test__get_data_dir", file=sys.stderr)
    assert aymara.lima._get_data_dir("lima").is_dir()


# TODO test with several ud languages


text = "Give it back! He pleaded."

# A registered UD media such as "ud-eng" does not auto-select a treebank, so the
# deeplima models (installed by `deeplima_models -i eng`) must be selected
# explicitly through the "udlang" metadata (the <code>-<corpus> stem of the
# installed model, e.g. tokenizer-eng-UD_English-EWT.pt). This value must be
# provided at construction time because the pipeline (and thus the model path)
# is instantiated then.
UD_ENG_META = {"udlang": "eng-UD_English-EWT"}


# One deepud analyzer for most of the tests below: each new instance loads the
# English models and embeddings again (about 3.5 GB) and its memory is not
# released, which exhausted the 16 GB of the CI runners (exit code 137)
lima = aymara.lima.Lima("ud-eng", pipes="deepud", meta=UD_ENG_META)


def test_legacy_names_mapping():
    # The legacy media and pipelines are deprecated: their names select the
    # deeplima-backed UD media and pipelines
    with pytest.warns(DeprecationWarning):
        assert aymara.lima._media("eng") == "ud-eng"
    with pytest.warns(DeprecationWarning):
        assert aymara.lima._media("fre") == "ud-fra"
    with pytest.warns(DeprecationWarning):
        assert aymara.lima._media("por") == "ud-por"
    assert aymara.lima._media("ud-fra") == "ud-fra"
    with pytest.warns(DeprecationWarning):
        assert aymara.lima._pipeline("main") == "deepud"
    with pytest.warns(DeprecationWarning):
        assert aymara.lima._pipeline("ner-rules-pretok") == "deepud-pretok"
    assert aymara.lima._pipeline("deepud") == "deepud"


def test_several_ud_languages_warning():
    # The deeplima model (udlang) is shared by the languages of an analyzer
    with pytest.warns(UserWarning):
        with pytest.raises(aymara.lima.LimaInternalError):
            aymara.lima.Lima("ud-eng,ud-fra", pipes="")


def test_several_instances():
    # Test with several analyzer instantiated and called alternatively, the
    # French one through the deprecated legacy names (French default model,
    # installed by "lima_models -i fra")
    print(f"test_several_instances", file=sys.stderr)
    with pytest.warns(DeprecationWarning):
        lima2 = aymara.lima.Lima("fre", pipes="main")
    assert lima2.langs == ["ud-fra"] and lima2.pipes == ["deepud"]
    doc1 = lima(text)
    assert doc1 is not None and type(doc1) == aymara.lima.Doc
    doc2 = lima2("Jean Dupont a visité Paris le 12 janvier 2021.")
    assert doc2 is not None and type(doc2) == aymara.lima.Doc
    # The French ModEx rules run after the deeplima analysis
    assert [ent.label for ent in doc2.ents] == ["Person.PERSON", "Location.CITY",
                                                "DateTime.DATE"]


def test_analyzeText_lang_not_str():
    print(f"test_analyzeText_lang_not_str", file=sys.stderr)
    with pytest.raises(TypeError):
        lima.analyzeText("This is a text on 02/05/2022.", lang=dict(),
                         pipeline="deepud")


def test_functor_lang_not_str():
    print(f"test_functor_lang_not_str", file=sys.stderr)
    with pytest.raises(TypeError):
        lima("This is a text on 02/05/2022.", lang=dict(), pipeline="deepud")


def test_analyzeText_lang_not_init():
    print(f"test_analyzeText_lang_not_init", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        lima.analyzeText("This is a text on 02/05/2022.", lang="wol",
                         pipeline="deepud")


def test_functor_lang_not_init():
    print(f"test_functor_lang_not_init", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        lima("This is a text on 02/05/2022.", lang="wol", pipeline="deepud")


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
    # The deprecated "eng" is "ud-eng"
    print(f"test_analyzeText_pipeline_none_lang_eng", file=sys.stderr)
    with pytest.warns(DeprecationWarning):
        with pytest.raises(aymara.lima.LimaInternalError):
            thelima = aymara.lima.Lima("eng", pipes="")
            thelima.analyzeText("This is a text on 02/05/2022.", lang="eng",
                                pipeline=None)


def test_functor_pipeline_none_lang_eng():
    print(f"test_functor_pipeline_none_lang_eng", file=sys.stderr)
    with pytest.warns(DeprecationWarning):
        with pytest.raises(aymara.lima.LimaInternalError):
            thelima = aymara.lima.Lima("eng", pipes="")
            thelima("This is a text on 02/05/2022.", lang="eng", pipeline=None)


def test_analyzeText_legacy_names():
    # The deprecated legacy language and pipeline names still work
    with pytest.warns(DeprecationWarning):
        result = lima.analyzeText("This is a text on 02/05/2022.", lang="eng",
                                  pipeline="main")
    assert "02/05/2022" in result


def test_functor_not_text():
    print(f"test_functor_not_text", file=sys.stderr)
    with pytest.raises(TypeError):
        result = lima(dict())


def test_analyzeText_init_with_lang_and_pipe():
    print(f"test_analyzeText_init_with_lang_and_pipe", file=sys.stderr)
    # lima was initialized with a language and a pipeline
    result = lima.analyzeText("This is a text on 02/05/2022.")
    assert True


def test_analyzeText_init_with_lang():
    print(f"test_analyzeText_init_with_lang", file=sys.stderr)
    # The pipeline is chosen at analyze time
    result = lima.analyzeText("This is a text on 02/05/2022.",
                              pipeline="deepud")
    assert True


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
    print(f"test_doc_repr '{repr(doc)}'", file=sys.stderr)
    # There is 7 tokens and an empty line separating the 2 sentences
    assert len(repr(doc).split("\n")) == 8
    # Sentence roots have head 0, in the second sentence too (it was -4)
    lines = [line.split("\t") for line in repr(doc).split("\n") if line]
    assert all(cols[6] == "0" for cols in lines if cols[7] == "root")


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
    assert repr(token) == '6\tpleaded\tplead\tVERB\t_\tMood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin\t0\troot\t_\tPos=17|Len=7'
    assert str(token) == "pleaded" == token.text
    assert len(token) == 7
    assert token.i == 6
    assert token.idx == 17
    assert token.ent_iob == "O"
    assert token.ent_type == "_"
    assert token.lemma == "plead"
    assert token.pos == "VERB"
    # The root's head is itself, as in spaCy; head_i is its index
    assert token.head == token
    assert token.head_i == 5
    assert token.dep == "root"
    assert token.features == {'Mood': 'Ind', 'Number': 'Sing', 'Person': '3', 'Tense': 'Past',
                              'VerbForm': 'Fin'}
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
    ents = ndoc.ents
    assert isinstance(ents, tuple)
    assert len(ents) == 4
    # Not consumed by a first iteration
    assert len(list(ndoc.ents)) == 4
    for ent in ents:
        assert ent.text == ndoc.text[ent.start_char:ent.end_char]
        assert ent.text != ""
        assert ent.label_ == ent.label
        assert all(t.ent_type == ent.label for t in ent)
    assert ents[0].text == "John Doe"


def test_doc_ents_last_token():
    # An entity ending on the last token of the document
    ndoc = lima("He met John Doe")
    assert [ent.text for ent in ndoc.ents][-1:] == ["John Doe"]


def test_doc_slices():
    # doc = lima("Give it back! He pleaded.")
    assert doc[:3].text == "Give it back"
    assert doc[4:].text == "He pleaded."
    assert len(doc[:]) == len(doc)
    assert doc[-2:].text == "pleaded."
    assert len(doc[10:20]) == 0
    with pytest.raises(IndexError):
        doc[len(doc)]
    with pytest.raises(ValueError):
        doc[::2]


def test_token_doc_and_sent_start():
    # doc = lima("Give it back! He pleaded.")
    assert doc[0].doc is doc
    assert [t.text for t in doc if t.is_sent_start] == ["Give", "He"]


def test_span_get_item_end():
    span = doc[1:4]
    assert span[2].text == "!"
    with pytest.raises(IndexError):
        span[3]
    assert span[:].text == "it back!"
    assert span[1:].text == "back!"


def test_meta_type():
    with pytest.raises(TypeError):
        lima("A text.", meta={"udlang": 1})
    with pytest.raises(TypeError):
        lima("A text.", meta=["udlang"])


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


def test_add_pipeline_unit():
    # The former TensorFlow units (CppUppsalaTensorFlowTokenizer,
    # TensorFlowMorphoSyntax) were removed with the TF backend; rebuild the same
    # tokenize+tag+lemma pipeline from the libtorch units used by "deepud"
    # (RnnTokenizer, RnnTokensAnalyzer). udlang must be supplied so the
    # "$udlang" model prefixes resolve (see UD_ENG_META).
    new_lima = aymara.lima.Lima("ud-eng", pipes="empty", meta=UD_ENG_META)
    group = {
        "name": "rnntokenizer",
        "class": "RnnTokenizer",
        "model_prefix": "tokenizer-$udlang"
    }
    assert new_lima.add_pipeline_unit("empty", "ud-eng", json.dumps(group))
    group = {
        "name": "rnntokensanalyzer",
        "class": "RnnTokensAnalyzer",
        "tagger_model_prefix": "tagger-$udlang",
        "lemmatizer_model_prefix": "lemmatizer-$udlang"
    }
    assert new_lima.add_pipeline_unit("empty", "ud-eng", json.dumps(group))
    group = {
        "name": "conllDumper",
        "class": "ConllDumper",
        "handler": "simpleStreamHandler",
        "fakeDependencyGraph": "false"
    }
    assert new_lima.add_pipeline_unit("empty", "ud-eng", json.dumps(group))

    doc = new_lima(text)
    assert doc is not None and type(doc) == aymara.lima.Doc
    assert doc[0].text == "Give"


def test_unknownLanguage():
    print(f"test_unknownLanguage", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima(langs="this_is_not_a_language_name")


def test_lang_no_prefix():
    print(f"test_lang_no_prefix", file=sys.stderr)
    with pytest.raises(aymara.lima.LimaInternalError):
        aymara.lima.Lima(langs="cym")



def test_lazy_submodules():
    # import aymara is enough to reach aymara.lima (PEP 562 __getattr__)
    import importlib
    package = importlib.import_module("aymara")
    assert package.lima is aymara.lima
    assert package.lima_models.default_udlang is not None
    with pytest.raises(AttributeError):
        package.no_such_submodule


def test_multiword_tokens_fra():
    # "du" and "au" are multiword tokens: their words share the surface's
    # position
    from aymara.lima_models import default_udlang
    if not default_udlang("fra"):
        pytest.skip("no French model installed")
    lima_fra = aymara.lima.Lima("ud-fra")
    fdoc = lima_fra("Jean Dupont vient du Japon et parle au directeur.")
    assert [t.text for t in fdoc][:6] == ["Jean", "Dupont", "vient", "de", "le",
                                         "Japon"]
    assert fdoc[3].idx == fdoc[4].idx == fdoc.text.index("du ")
    assert [ent.text for ent in fdoc.ents][:2] == ["Jean Dupont", "Japon"]


def test_named_entity_before_clitic():
    # "Apple's" is a multiword token of the English MERGE model: "Apple" "'s".
    # It crashed (segfault in LIMA's ConllDumper) when "Apple" is an entity
    from aymara.lima_models import _get_target_dir, _installed_stems
    if "eng-UD_English-MERGE" not in _installed_stems(_get_target_dir(), "eng"):
        pytest.skip("the eng-UD_English-MERGE model is not installed")
    lima_merge = aymara.lima.Lima("ud-eng",
                                  meta={"udlang": "eng-UD_English-MERGE"})
    mdoc = lima_merge("Apple's CEO met Microsoft's.")
    assert [t.text for t in mdoc][:3] == ["Apple", "'s", "CEO"]
    # The words that spell the surface have their own positions
    assert [t.idx for t in mdoc][:3] == [0, 5, 8]
    assert mdoc[:2].text == "Apple's"


def test_token_spacy_names():
    # doc = lima("Give it back! He pleaded.")
    token = doc[5]
    assert token.lemma_ == "plead" and token.pos_ == "VERB" and token.dep_ == "root"
    assert token.tag_ == "_"
    assert token.ent_type_ == "" and token.ent_iob_ == "O"
    assert str(token.morph) == "Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin"
    assert token.morph.get("Number") == ["Sing"] and token.morph.get("Case") == []
    assert "Tense=Past" in token.morph
    assert token.morph.to_dict()["Mood"] == "Ind"
    assert doc[0].shape_ == "Xxxx" and doc[0].lower_ == "give"
    assert [t.whitespace_ for t in doc] == [" ", " ", "", " ", " ", "", ""]
    assert "".join(t.text_with_ws for t in doc) == doc.text
    assert doc[0].nbor().text == "it" and doc[1].nbor(-1).text == "Give"
    with pytest.raises(IndexError):
        doc[-1].nbor()


def test_token_navigation():
    # doc = lima("Give it back! He pleaded.")
    give, it, he, pleaded = doc[0], doc[1], doc[4], doc[5]
    assert it.head == give and it.head_i == 0
    assert doc[it.head_i] == it.head
    assert [t.text for t in give.children] == ["it", "back", "!"]
    assert [t.text for t in pleaded.lefts] == ["He"]
    assert [t.text for t in pleaded.rights] == ["."]
    assert pleaded.n_lefts == 1 and pleaded.n_rights == 1
    assert [t.text for t in give.subtree] == ["Give", "it", "back", "!"]
    assert give.left_edge == give and give.right_edge == doc[3]
    assert list(he.ancestors) == [pleaded]
    assert pleaded.is_ancestor(he) and not he.is_ancestor(pleaded)
    assert he.sent.text == "He pleaded."
    assert len({doc[0], doc[0], doc[1]}) == 2


def test_span_navigation():
    # doc = lima("Give it back! He pleaded.")
    sents = list(doc.sents)
    assert [s.root.text for s in sents] == ["Give", "pleaded"]
    assert doc[1:3].root.text == "it" or doc[1:3].root.text == "back"
    assert doc[4:6].sent == sents[1]
    assert len(list(doc[2:5].sents)) == 2
    assert doc[0:3].text_with_ws == "Give it back"
    assert doc[4:7].lemma_ == "he plead."


def test_doc_spacy_api():
    # doc = lima("Give it back! He pleaded.")
    assert doc.text_with_ws == doc.text
    assert doc.char_span(5, 12).text == "it back"
    assert doc.char_span(5, 11) is None
    assert doc.char_span(5, 11, alignment_mode="contract").text == "it"
    assert doc.char_span(6, 11, alignment_mode="expand").text == "it back"
    assert doc.has_annotation("DEP") and doc.has_annotation("POS")
    assert not doc.has_annotation("TAG")
    data = doc.to_json()
    assert data["text"] == doc.text
    assert [t["head"] for t in data["tokens"]] == [0, 0, 0, 0, 5, 5, 5]
    assert data["sents"] == [{"start": 0, "end": 13}, {"start": 14, "end": 25}]
    assert json.dumps(data)
    assert doc.to_conllu().startswith("# sent_id = 1\n# text = Give it back!\n")


def test_noun_chunks():
    ndoc = lima("The big dog chased a small cat in the garden.")
    assert [c.text for c in ndoc.noun_chunks] == ["The big dog", "a small cat",
                                                  "the garden"]


def test_ents_in_span():
    ndoc = lima("John Doe lives in New York.")
    assert [e.text for e in ndoc[0:3].ents] == ["John Doe"]
    assert ndoc.ents[0].root.text in ("John", "Doe")


def test_pipe():
    docs = list(lima.pipe(["Give it back!", "He pleaded."]))
    assert [d.text for d in docs] == ["Give it back!", "He pleaded."]
    assert lima.lang == "ud-eng"


# spaCy interoperability (aymara.lima_spacy), skipped without spaCy

def test_to_spacy():
    spacy = pytest.importorskip("spacy")
    # doc = lima("Give it back! He pleaded.")
    sdoc = doc.to_spacy()
    assert isinstance(sdoc, spacy.tokens.Doc)
    assert sdoc.text == doc.text
    assert sdoc.lang_ == "en"
    assert [t.text for t in sdoc] == [t.text for t in doc]
    assert [t.lemma_ for t in sdoc] == [t.lemma_ for t in doc]
    assert [t.pos_ for t in sdoc] == [t.pos_ for t in doc]
    assert [t.dep_ for t in sdoc] == [t.dep_ for t in doc]
    assert [t.head.i for t in sdoc] == [t.head_i for t in doc]
    assert str(sdoc[5].morph) == str(doc[5].morph)
    assert [s.text for s in sdoc.sents] == ["Give it back!", "He pleaded."]
    assert [t.idx for t in sdoc] == [t.idx for t in doc]


def test_to_spacy_entities_and_tools():
    spacy = pytest.importorskip("spacy")
    from spacy.matcher import Matcher
    ndoc = lima("John Doe lives in New York.")
    sdoc = ndoc.to_spacy()
    assert [(e.text, e.label_) for e in sdoc.ents] == [(e.text, e.label_)
                                                       for e in ndoc.ents]
    matcher = Matcher(sdoc.vocab)
    matcher.add("CITY", [[{"ENT_TYPE": "Location.CITY", "OP": "+"}]])
    assert any(sdoc[s:e].text == "New York" for _, s, e in matcher(sdoc))
    html = spacy.displacy.render(sdoc, style="dep", page=False)
    assert "lives" in html
    from spacy.tokens import DocBin
    restored = list(DocBin(docs=[sdoc], store_user_data=True).get_docs(sdoc.vocab))[0]
    assert [t.dep_ for t in restored] == [t.dep_ for t in sdoc]


def test_spacy_pipeline():
    pytest.importorskip("spacy")
    import aymara.lima_spacy
    nlp = aymara.lima_spacy.spacy_pipeline(lima=lima)
    assert nlp.lang == "en"
    sdoc = nlp("Give it back! He pleaded.")
    assert [t.dep_ for t in sdoc][5] == "root"
    docs = list(nlp.pipe(["Give it back!", "He pleaded."]))
    assert [d.text for d in docs] == ["Give it back!", "He pleaded."]
    # spaCy components run after LIMA
    nlp.add_pipe("sentencizer")
    assert len(list(nlp("He pleaded. Give it back!").sents)) == 2


def test_spacy_lang_codes():
    pytest.importorskip("spacy")
    from aymara.lima_spacy import spacy_lang
    assert spacy_lang("ud-eng") == "en"
    assert spacy_lang("ud-fra") == "fr"
    assert spacy_lang("ud-zzz") == "xx"


def test_to_spacy_multiword_tokens():
    pytest.importorskip("spacy")
    from aymara.lima_models import default_udlang
    if not default_udlang("fra"):
        pytest.skip("no French model installed")
    fdoc = aymara.lima.Lima("ud-fra")("Il vient du Japon.")
    sdoc = fdoc.to_spacy()
    assert sdoc.lang_ == "fr"
    # "du" -> "de le": separate spaCy tokens, the original text kept aside
    assert [t.text for t in sdoc][2:4] == ["de", "le"]
    assert sdoc.text == "Il vient de le Japon."
    assert sdoc.user_data["lima_text"] == "Il vient du Japon."


def test_is_stop():
    # doc = lima("Give it back! He pleaded.")
    assert [t.text for t in doc if t.is_stop] == ["Give", "it", "back", "He"]
    assert aymara.lima._stop_words("ud-zzz") == frozenset()


def test_pipe_names_and_meta():
    assert lima.pipe_names[0] == "RnnTokenizer"
    assert "RnnDependencyParser" in lima.pipe_names
    meta = lima.meta
    assert meta["lang"] == "ud-eng" and meta["pipeline"] == "deepud"
    assert meta["udlang"] == "eng-UD_English-EWT"
    assert meta["version"] == aymara.version.__version__


def test_conllu_round_trip():
    # doc = lima("Give it back! He pleaded.")
    conllu = doc.to_conllu()
    lines = conllu.split("\n")
    assert lines[:2] == ["# sent_id = 1", "# text = Give it back!"]
    assert lines[2].startswith("1\tGive\tgive\tVERB\t")
    assert "SpaceAfter=No" in lines[4]       # back!
    assert conllu.endswith("\n\n")
    back = aymara.lima.Doc.from_conllu(conllu, lang="ud-eng")
    assert back.text == doc.text
    for t1, t2 in zip(doc, back):
        assert (t1.text, t1.idx, t1.lemma_, t1.pos_, t1.dep_, t1.head_i, str(t1.morph),
                t1.ent_type_) == (t2.text, t2.idx, t2.lemma_, t2.pos_, t2.dep_, t2.head_i,
                                  str(t2.morph), t2.ent_type_)
    assert [s.text for s in back.sents] == [s.text for s in doc.sents]
    assert [t.text for t in back[5].children] == ["He", "."]
    assert back.to_conllu() == conllu


def test_from_conllu_ud():
    # A UD treebank sentence with a multiword token and no "# text"
    conllu = ("1\tIl\til\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
              "2\tvient\tvenir\tVERB\t_\t_\t0\troot\t_\t_\n"
              "3-4\tdu\t_\t_\t_\t_\t_\t_\t_\t_\n"
              "3\tde\tde\tADP\t_\t_\t5\tcase\t_\t_\n"
              "4\tle\tle\tDET\t_\t_\t5\tdet\t_\t_\n"
              "5\tJapon\tJapon\tPROPN\t_\t_\t2\tobl\t_\tSpaceAfter=No|NE=B-Location.COUNTRY\n"
              "6\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n")
    fdoc = aymara.lima.Doc.from_conllu(conllu, lang="ud-fra")
    assert fdoc.text == "Il vient du Japon."
    assert [t.idx for t in fdoc] == [0, 3, 9, 9, 12, 17]
    assert fdoc[5].head.text == "vient" and fdoc[1].dep_ == "root"
    assert [(e.text, e.label) for e in fdoc.ents] == [("Japon", "Location.COUNTRY")]
    assert fdoc[2].is_stop
    out = fdoc.to_conllu()
    assert "\n3-4\tdu\t" in out


def test_span_as_doc():
    # doc = lima("Give it back! He pleaded.")
    sub = doc[4:7].as_doc()
    assert isinstance(sub, aymara.lima.Doc)
    assert sub.text == "He pleaded."
    assert [t.idx for t in sub] == [0, 3, 10]
    assert sub[0].head.text == "pleaded" and sub[1].head == sub[1]
    assert len(list(sub.sents)) == 1
    part = doc[1:3].as_doc()          # "it back": heads outside the span
    assert all(t.head == t for t in part)
    assert doc[0:0].as_doc().text == ""


def test_pipe_batched():
    texts = ["Give it back!", "", "He pleaded.\n\nShe left.", "John Doe lives in New York."]
    single = list(lima.pipe(texts))
    batched = list(lima.pipe(texts, batch_size=3))
    assert len(batched) == len(texts)
    for text, s, b in zip(texts, single, batched):
        assert b.text == text
        assert [t.text for t in b] == [t.text for t in s]
        assert [t.idx for t in b] == [t.idx for t in s]
        assert [x.text for x in b.sents] == [x.text for x in s.sents]
        for t in b:
            assert 0 <= t.head_i < len(b)
    assert len(batched[1]) == 0
    assert [e.text for e in batched[3].ents] == ["John Doe", "New York"]
    with pytest.raises(TypeError):
        list(lima.pipe(["a", 1], batch_size=2))
