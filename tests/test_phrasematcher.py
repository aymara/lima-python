# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""PhraseMatcher: spaCy's PhraseMatcher API on LIMA's ModEx rules."""

import pytest

import aymara.lima
from aymara.lima import PhraseMatcher, _modex_escape

try:
    from tests.test_aymara import lima
except ImportError:  # pragma: no cover
    from test_aymara import lima


@pytest.fixture
def nlp():
    """The analyzer shared by the tests, its pipeline restored afterwards (a
    matcher makes it use a new pipeline)."""
    pipes = list(lima.pipes)
    yield lima
    lima.pipes[:] = pipes


def test_modex_escape():
    assert _modex_escape("Obama") == "Obama"
    assert _modex_escape("état") == "état"
    assert _modex_escape("AT&T") == "AT\\&T"
    assert _modex_escape("U.S.") == "U\\.S\\."
    assert _modex_escape("$") == "\\$"
    assert _modex_escape("t_x") == "\\t_x"
    assert _modex_escape("T_A1") == "\\T_A1"
    with pytest.raises(ValueError):
        _modex_escape("a\\b")


def test_arguments(nlp):
    with pytest.raises(TypeError):
        PhraseMatcher("vocab")
    with pytest.raises(ValueError):
        PhraseMatcher(nlp, attr="SHAPE")
    assert PhraseMatcher(nlp, attr="text").attr == "ORTH"
    matcher = PhraseMatcher(nlp)
    with pytest.raises(ValueError):
        matcher.add("KEY", nlp("Barack Obama"))
    with pytest.raises(TypeError):
        matcher.add("KEY", [42])
    with pytest.raises(TypeError):
        matcher("Barack Obama")
    with pytest.raises(KeyError):
        matcher.remove("KEY")
    # Nothing installed yet
    assert len(matcher) == 0 and "KEY" not in matcher
    assert nlp.pipes[0] == "deepud"


def test_orth(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("OBAMA", [nlp("Barack Obama")])
    assert len(matcher) == 1 and "OBAMA" in matcher
    # The analyzer uses a new pipeline, with the matcher before the named
    # entities rules
    assert nlp.pipes[0] != "deepud"
    names = nlp.pipe_names
    unit = next(name for name in names if name.startswith("PhraseMatcher"))
    if "SpecificEntitiesModexAfterPos" in names:
        assert names.index(unit) < names.index("SpecificEntitiesModexAfterPos")
    doc = nlp("Barack Obama lifts America one last time in emotional farewell")
    assert matcher(doc) == [("OBAMA", 0, 2)]
    spans = matcher(doc, as_spans=True)
    assert [(span.text, span.label_) for span in spans] == [("Barack Obama", "OBAMA")]
    # The match is an entity of the document
    assert any(ent.text == "Barack Obama" and ent.label_.endswith(".OBAMA")
               for ent in doc.ents)
    # Case sensitive
    assert matcher(nlp("barack obama lifts America.")) == []


def test_several_keys_and_patterns(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("CITY", ["New York", "Paris"])
    matcher.add("ML", [nlp("machine learning")])
    doc = nlp("She studies machine learning in New York and in Paris.")
    matches = matcher(doc)
    assert [(key, doc[s:e].text) for key, s, e in matches] == [
        ("ML", "machine learning"), ("CITY", "New York"), ("CITY", "Paris")]
    # Adding patterns to a key keeps the former ones
    matcher.add("CITY", ["London"])
    doc = nlp("From Paris to London.")
    assert [doc[s:e].text for _, s, e in matcher(doc)] == ["Paris", "London"]
    # Matching in a span
    span = doc[2:]
    assert [doc[s:e].text for _, s, e in matcher(span)] == ["London"]


def test_longest_first(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("SHORT", ["New York"])
    matcher.add("LONG", ["New York City"])
    doc = nlp("New York City is big.")
    assert matcher(doc) == [("LONG", 0, 3)]


def test_remove(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("A", ["machine learning"])
    matcher.add("B", ["deep learning"])
    text = "machine learning and deep learning"
    assert [key for key, _, _ in matcher(nlp(text))] == ["A", "B"]
    matcher.remove("A")
    assert "A" not in matcher and len(matcher) == 1
    assert [key for key, _, _ in matcher(nlp(text))] == ["B"]
    # A key can be added again
    matcher.add("A", ["machine learning"])
    assert [key for key, _, _ in matcher(nlp(text))] == ["A", "B"]


def test_on_match(nlp):
    calls = []

    def on_match(matcher, doc, i, matches):
        calls.append((i, matches[i]))

    matcher = PhraseMatcher(nlp)
    matcher.add("ML", [nlp("machine learning")], on_match=on_match)
    matcher(nlp("I like machine learning."))
    assert calls == [(0, ("ML", 2, 4))]
    # spaCy v2 signature
    with pytest.warns(DeprecationWarning):
        matcher.add("DL", on_match, nlp("deep learning"))
    assert "DL" in matcher


def test_lower(nlp):
    matcher = PhraseMatcher(nlp, attr="LOWER")
    matcher.add("ML", ["machine learning"])
    doc = nlp("Machine Learning is fun. MACHINE LEARNING is loud.")
    assert [doc[s:e].text for _, s, e in matcher(doc)] == [
        "Machine Learning", "MACHINE LEARNING"]


def test_lemma(nlp):
    matcher = PhraseMatcher(nlp, attr="LEMMA")
    matcher.add("RUN", [nlp("runs fast")])
    doc = nlp("They ran fast.")
    assert [doc[s:e].text for _, s, e in matcher(doc)] == ["ran fast"]


def test_special_characters(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("ATT", [nlp("AT&T")])
    matcher.add("US", [nlp("U.S.")])
    doc = nlp("AT&T is a U.S. company.")
    assert [key for key, _, _ in matcher(doc)] == ["ATT", "US"]


def test_two_matchers(nlp):
    first = PhraseMatcher(nlp)
    first.add("ML", ["machine learning"])
    second = PhraseMatcher(nlp)
    second.add("DL", ["deep learning"])
    doc = nlp("machine learning and deep learning")
    assert [key for key, _, _ in first(doc)] == ["ML"]
    assert [key for key, _, _ in second(doc)] == ["DL"]


def test_conllu_column(nlp):
    matcher = PhraseMatcher(nlp)
    matcher.add("ML", ["machine learning"])
    conllu = nlp("I like machine learning.").to_conllu()
    assert ".ML" in conllu
    assert isinstance(aymara.lima.Doc.from_conllu(conllu), aymara.lima.Doc)
