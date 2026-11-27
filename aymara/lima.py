#!/usr/bin/env python3

"""
The LIMA python bindings.

This python API gives access to the major features of the LIMA linguistic analyzer. To
make it easier to handle, it largely reproduces that of spaCy, including parts of the
documentation. See the GitHub project for spaCy's copyright notice.

Example::

    import aymara.lima
    nlp = aymara.lima.Lima()
    doc = nlp("Mr. Best flew to New York on Saturday morning.")
    print(doc)

Classes:

    Doc
    Lima
    PhraseMatcher
    Span
    Token

"""


# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import argparse
import bisect
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import warnings

from tqdm import tqdm
from typing import (Dict, Iterable, Iterator, List, Optional, Tuple, Union)

import aymaralima.cpplima


def _get_data_dir(appname: str):
    """
    This private function returns the user data dir of LIMA (and of the models).

    :param appname: the name of the application.
    :type appname: str
    :return: the application's data dir.
    :rtype: str
    """
    # The same directory as the one LIMA itself reads (getDataHome in its
    # FileUtils.cpp) and lima_models installs the models in, on all platforms
    ans = pathlib.Path(os.getenv('XDG_DATA_HOME', "~/.local/share")).expanduser()
    return ans.joinpath(appname)


def _copy_tree(src, dst) -> None:
    """Copies the directory src into dst, which may exist, merging them, as
    distutils.dir_util.copy_tree did (distutils is gone since Python 3.12;
    shutil.copytree's dirs_exist_ok needs Python 3.8)."""
    src, dst = pathlib.Path(src), pathlib.Path(dst)
    if sys.version_info >= (3, 8):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return
    for root, _dirs, files in os.walk(src):  # pragma: no cover
        target = dst / pathlib.Path(root).relative_to(src)
        target.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), target / f)


# ISO 639-3 (LIMA's UD media "ud-<code>") -> ISO 639-1, the codes of spaCy and of
# the stop word lists
_ISO639_3_TO_1 = {
    "afr": "af", "amh": "am", "ara": "ar", "bel": "be", "ben": "bn", "bul": "bg",
    "cat": "ca", "ces": "cs", "cym": "cy", "dan": "da", "deu": "de", "ell": "el",
    "eng": "en", "est": "et", "ekk": "et", "eus": "eu", "fao": "fo", "fas": "fa",
    "fin": "fi", "fra": "fr", "gle": "ga", "gla": "gd", "glg": "gl", "guj": "gu",
    "heb": "he", "hin": "hi", "hrv": "hr", "hun": "hu", "hye": "hy", "ind": "id",
    "isl": "is", "ita": "it", "jpn": "ja", "kan": "kn", "kat": "ka", "kaz": "kk",
    "kir": "ky", "kor": "ko", "lat": "la", "lav": "lv", "lit": "lt", "ltz": "lb",
    "mal": "ml", "mar": "mr", "mkd": "mk", "mlt": "mt", "nep": "ne", "nld": "nl",
    "nor": "nb", "nob": "nb", "nno": "nn", "pol": "pl", "por": "pt", "ron": "ro",
    "rus": "ru", "san": "sa", "sin": "si", "slk": "sk", "slv": "sl", "spa": "es",
    "sqi": "sq", "srp": "sr", "swe": "sv", "tam": "ta", "tat": "tt", "tel": "te",
    "tgl": "tl", "tha": "th", "tir": "ti", "tsn": "tn", "tur": "tr", "ukr": "uk",
    "urd": "ur", "vie": "vi", "yor": "yo", "zho": "zh",
}


def _iso639_1(lang: str) -> str:
    """The ISO 639-1 code of a LIMA language ("ud-eng" -> "en"), or its own code
    without "ud-" if there is none."""
    code = lang[3:] if lang.startswith("ud-") else lang
    return _ISO639_3_TO_1.get(code, code)


_stop_words_cache: Dict[str, frozenset] = {}


def _stop_words(lang: str) -> frozenset:
    """The stop words of a LIMA language (from spaCy's lists, vendored in
    aymara.stop_words); empty for a language without list."""
    code = _iso639_1(lang)
    if code not in _stop_words_cache:
        from aymara.stop_words import STOP_WORDS
        words = STOP_WORDS.get(code, "")
        _stop_words_cache[code] = frozenset(words.split("\n")) if words else frozenset()
    return _stop_words_cache[code]


class _PyToken:
    """A token of a document built in Python (Doc.from_conllu, Span.as_doc),
    with the fields of the C++ token (aymaralima.cpplima.Token)."""
    __slots__ = ("len", "text", "i", "lemma", "pos", "tag", "head", "dep",
                 "features", "neIOB", "neType", "tStatus")

    def __init__(self, **fields):
        for name in self.__slots__:
            setattr(self, name, fields.get(name))


class _PySentence:
    """The bounds of a sentence, as the C++ ones: the first one covers the tokens
    [start, end], the next ones [start+1, end] (start is the previous end)."""
    __slots__ = ("start", "end")

    def __init__(self, start: int, end: int):
        self.start, self.end = start, end


class _PyDoc:
    """A document built in Python, with the interface of the C++ document
    (aymaralima.cpplima.Doc) that Doc uses."""

    def __init__(self, text: str, tokens: List[_PyToken],
                 sentences: List[Tuple[int, int]], language: str = ""):
        """sentences: the [start, end) token bounds of each sentence"""
        self._text, self._tokens, self._language = text, tokens, language
        self._sentences = [_PySentence(0 if k == 0 else start - 1, end - 1)
                           for k, (start, end) in enumerate(sentences)]

    def at(self, k: int) -> _PyToken:
        return self._tokens[k]

    def len(self) -> int:
        return len(self._tokens)

    def sentences(self) -> List[_PySentence]:
        return self._sentences

    def text(self) -> str:
        return self._text

    def language(self) -> str:
        return self._language

    def error(self) -> bool:
        return False

    def errorMessage(self) -> str:
        return ""


class MorphAnalysis:
    """The morphological features of a token, as spaCy's MorphAnalysis.

    Example::

        morph = doc[5].morph
        str(morph)            # "Mood=Ind|Number=Sing|...", sorted as CoNLL-U
        morph.get("Number")   # ["Sing"]
        morph.to_dict()       # {"Mood": "Ind", "Number": "Sing", ...}
    """
    def __init__(self, features: Dict[str, str]):
        self._features = dict(sorted(features.items(), key=lambda kv: kv[0].lower()))

    def get(self, field: str) -> List[str]:
        """The values of the feature field (a list, empty if absent; a feature may
        have several values, separated by commas in CoNLL-U)."""
        value = self._features.get(field)
        return value.split(",") if value else []

    def to_dict(self) -> Dict[str, str]:
        """The features as a dict, e.g. {"Number": "Sing"}."""
        return dict(self._features)

    def __str__(self) -> str:
        return "|".join(f"{k}={v}" for k, v in self._features.items())

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self) -> Iterator[str]:
        """The features as "Field=Value" strings."""
        return iter(f"{k}={v}" for k, v in self._features.items())

    def __len__(self) -> int:
        return len(self._features)

    def __contains__(self, feature: str) -> bool:
        """Whether the "Field=Value" feature is present."""
        return feature in set(self)

    def __eq__(self, other) -> bool:
        if isinstance(other, MorphAnalysis):
            return self._features == other._features
        if isinstance(other, str):
            return str(self) == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(str(self))


class Token:
    """A token

    TODO
    Some parts of the API are still not implemented

        sent     The sentence span that this token is a part of.
        Span

        lang    Language of the parent document’s vocabulary.
        str


    """
    def __init__(self, token: aymaralima.cpplima.Token, doc: "Doc" = None):
        """Token's constructor

        :param token: the C++ binding Token class
        :type token: aymaralima.cpplima.Token
        :param doc: the document of this token (Default value = None)
        :type doc: Doc
        """
        assert isinstance(token, (aymaralima.cpplima.Token, _PyToken))
        self.token = token
        self._doc = doc

    def __repr__(self) -> str:
        """
        The representation of this token in CoNLL-U format. Tab separated
        columns:
        ID: Word index, integer starting at 1 for each new sentence; may be a
            range for multiword tokens; may be a decimal number for empty
            nodes (decimal numbers can be lower than 1 but must be greater
            than 0).
        FORM: Word form or punctuation symbol.
        LEMMA: Lemma or stem of word form.
        UPOS: Universal part-of-speech tag.
        XPOS: (always _ in LIMA) Language-specific part-of-speech tag;
            underscore if not available.
        FEATS: List of morphological features from the universal feature
            inventory or from a defined language-specific extension; underscore
            if not available.
        HEAD: Head of the current word, which is either a value of ID or
            zero (0).
        DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0)
            or a defined language-specific subtype of one.
        DEPS: Enhanced dependency graph in the form of a list of head-deprel
            pairs.
        MISC: Any other annotation.

        :return: return the CoNLL-U representation of this token
        :rtype: str
        """
        head = (0 if self.dep == 'root'
                else self.token.head+1 if self.token.head >= 0
                else '_')
        return (f"{self.i}\t{self.token.text}\t{self.lemma}\t{self.pos}\t_\t"
                + ("|".join([f'{k}={v}' for k, v in self.features.items()])
                   if self.features else "_")
                + "\t"
                + f"{head}\t"
                + f"{self.dep if self.dep else '_'}\t_\t"
                + f"Pos={self.idx}|Len={len(self)}"
                + (f"" if self.token.neIOB == 'O'
                   else f"|NE={self.token.neIOB}-{self.token.neType}"))

    def __len__(self) -> int:
        """Return the length of the token in UTF-8 code points

        :return: the length of the token
        :rtype: int
        """
        return self.token.len

    def __str__(self):
        """Return the original text of the token.

        :return: the original text of the token
        :rtype: str
        """
        return self.token.text

    text = property(
            fget=lambda self: self.token.text,
            doc="The original text of the token.")

    i = property(
            fget=lambda self: self.token.i+1,
            doc=("The index of this token in its parent document, starting at 1 "
                 "(spaCy's starts at 0: doc[token.i - 1] == token)."))

    doc = property(
            fget=lambda self: self._doc,
            doc="The parent document (None for a token built without it).")

    lemma = property(
            fget=lambda self: self.token.lemma,
            doc="The token lemma.")

    pos = property(
            fget=lambda self: self.token.tag,
            doc="Coarse-grained part-of-speech from the Universal POS tag set.")

    @property
    def head_i(self) -> int:
        """The index in its document (from 0, as doc[k]) of the syntactic parent of
        this token: doc[token.head_i] == token.head. The root's is its own index,
        as the one of a token without dependency relation (dep "_").
        """
        if (self.dep in ("root", "_", "") or self.token.head < 0
                or (self._doc is not None and self.token.head >= len(self._doc))):
            return self.token.i
        return self.token.head

    @property
    def head(self) -> "Token":
        """The syntactic parent, or “governor”, of this token, a Token (the root's
        is itself, as in spaCy). Its index is head_i."""
        if self._doc is None:
            raise ValueError("Token.head needs the token's document (doc[k])")
        return self._doc[self.head_i]

    dep = property(
            fget=lambda self: self.token.dep,
            doc="Syntactic dependency relation.")

    idx = property(
            fget=lambda self: self.token.pos-1,
            doc="Position of this token in its document text.")

    features = property(
            fget=lambda self:  (
                {} if self.token.features == "_"
                else dict(x.split("=")
                          for x in self.token.features.split("|"))),
            doc="Morphlogical features of this token .")

    ent_type = property(
            fget=lambda self: self.token.neType,
            doc="Named entity type.")

    ent_iob = property(
            fget=lambda self: self.token.neIOB,
            doc=("IOB code of named entity tag. “B” means the token begins an entity, "
                 "“I” means it is inside an entity, “O” means it is outside an entity, "
                 "and \"\" means no entity tag is set."))

    t_status = property(
            fget=lambda self: self.token.tStatus,
            doc=("The tokenization status of this token. Can also be explored with the "
                 "is_* properties. The possible values are::\n"
                 "\n"
                 "  t_alphanumeric\n"
                 "  t_abbrev\n"
                 "  t_acronym\n"
                 "  t_capital\n"
                 "  t_capital_1st\n"
                 "  t_capital_small\n"
                 "  t_cardinal_roman\n"
                 "  t_comma_number\n"
                 "  t_dot_number\n"
                 "  t_fraction\n"
                 "  t_integer\n"
                 "  t_ordinal_integer\n"
                 "  t_ordinal_roman\n"
                 "  t_sentence_brk\n"
                 "  t_small\n"
                 "  t_word_brk\n"
                 "\n"
                 ))

    is_alpha = property(
        fget=lambda self: self.token.tStatus in ["t_alphanumeric", "t_capital",
                                                 "t_capital_1st", "t_capital_small",
                                                 "t_small"],
        doc=("Does the token consist of alphabetic characters? "
             "Equivalent to token.text.isalpha()."))

    is_digit = property(
        fget=lambda self: self.token.tStatus == "t_integer",
        doc=("Does the token consist of digits? "
            "Equivalent to token.text.isdigit()."))

    is_lower = property(
        fget=lambda self: self.token.text.islower(),
        doc=("Is the token in lowercase? Equivalent to token.text.islower()."))

    is_upper = property(
        fget=lambda self: self.token.text.isupper(),
        doc=("Is the token in lowercase? Equivalent to token.text.isupper()."))

    is_punct = property(
        fget=lambda self: self.token.tStatus in ["t_sentence_brk", "t_word_brk"],
        doc=("Is the token punctuation?"))

    is_sent_start = property(
        fget=lambda self: (self.token.i == 0 if self._doc is None
                           else self.token.i in self._doc._sentence_starts()),
        doc=("Does the token start a sentence? Without its document, only the "
             "first token of the document is known to."))

    is_sent_end = property(
        fget=lambda self: self.token.tStatus == "t_sentence_brk",
        doc=("Does the token end a sentence? bool or None if unknown."))

    is_space = property(
        fget=lambda self: self.token.text.isspace(),
        doc=("Does the token consist of whitespace characters? "
            "Equivalent to token.text.isspace(). "
            "Should always be False in LIMA as there is no space tokens"))

    is_bracket = property(
        fget=lambda self: self.token.text in "()[]{}",
        doc=("Is the token a bracket?"))

    is_quote = property(
        fget=lambda self: self.token.text in "\"'«»`",
        doc=("Is the token a quotation mark?"))

    # spaCy's string attributes (spaCy's attributes without "_" are hashes, LIMA's
    # are the strings themselves)

    lemma_ = property(fget=lambda self: self.token.lemma, doc="The token lemma.")

    pos_ = property(fget=lambda self: self.token.tag,
                    doc="Coarse-grained part-of-speech (Universal POS tag).")

    tag_ = property(fget=lambda self: "_",
                    doc=("Fine-grained (language specific) part-of-speech: not "
                         "provided by the deeplima models, always \"_\"."))

    dep_ = property(fget=lambda self: self.token.dep,
                    doc="Syntactic dependency relation.")

    ent_type_ = property(
        fget=lambda self: "" if self.token.neType in ("_", "") else self.token.neType,
        doc="Named entity type, \"\" outside entities (ent_type is \"_\" there).")

    ent_iob_ = property(fget=lambda self: self.token.neIOB,
                        doc="IOB code of the named entity tag: \"B\", \"I\" or \"O\".")

    morph = property(fget=lambda self: MorphAnalysis(self.features),
                     doc="Morphological features, a MorphAnalysis.")

    lower_ = property(fget=lambda self: self.token.text.lower(),
                      doc="Lowercase form of the token text.")

    norm_ = property(fget=lambda self: self.token.text.lower(),
                     doc="The token's norm: its lowercase form.")

    prefix_ = property(fget=lambda self: self.token.text[:1],
                       doc="The first character of the token text.")

    suffix_ = property(fget=lambda self: self.token.text[-3:],
                       doc="The last three characters of the token text.")

    @property
    def shape_(self) -> str:
        """Transform of the token text showing its orthographic features, as spaCy
        does: letters become x or X, digits d, the same character at most 4 times in
        a row ("Apple" -> "Xxxxx", "C3PO-42" -> "XdXX-dd")."""
        shape = []
        last, run = "", 0
        for c in self.token.text:
            shape_c = ("X" if c.isupper() else "x" if c.isalpha()
                       else "d" if c.isdigit() else c)
            run = run + 1 if shape_c == last else 1
            last = shape_c
            if run <= 4:
                shape.append(shape_c)
        return "".join(shape)

    @property
    def like_num(self) -> bool:
        """Does the token resemble a number? Digits (with separators), fractions,
        or a NUM part-of-speech."""
        text = self.token.text.lstrip("+-±~")
        text = text.replace(",", "").replace(".", "").replace(" ", "")
        if text.isdigit():
            return True
        if text.count("/") == 1:
            num, denom = text.split("/")
            if num.isdigit() and denom.isdigit():
                return True
        return self.token.tag == "NUM"

    @property
    def is_stop(self) -> bool:
        """Is the token a stop word of its document's language? From spaCy's stop
        lists (vendored in aymara.stop_words: no spaCy needed); False for a
        language without list or a token without document."""
        if self._doc is None:
            return False
        return self.token.text.lower() in _stop_words(self._doc.lang_ or "")

    @property
    def whitespace_(self) -> str:
        """The whitespace character following the token in the text, or \"\"."""
        if self._doc is None:
            return ""
        end = self.idx + len(self)
        text = self._doc.text
        k = self.token.i
        if k + 1 < len(self._doc) and self._doc[k + 1].idx < end:
            return ""  # a word of a multiword token followed by another one
        if end < len(text) and text[end].isspace():
            return text[end]
        return ""

    text_with_ws = property(fget=lambda self: self.token.text + self.whitespace_,
                            doc="The token text with its trailing whitespace.")

    def nbor(self, i: int = 1) -> "Token":
        """The token at the offset i (default 1, the next one) from this token.

        :raises IndexError: outside the document
        """
        k = self.token.i + i
        if self._doc is None or k < 0 or k >= len(self._doc):
            raise IndexError("Token.nbor: no token at this offset")
        return self._doc[k]

    def _needs_doc(self, name: str) -> "Doc":
        if self._doc is None:
            raise ValueError(f"Token.{name} needs the token's document (doc[k])")
        return self._doc

    @property
    def children(self) -> Iterator["Token"]:
        """The syntactic children of the token, in the text order."""
        doc = self._needs_doc("children")
        return (doc[k] for k in doc._children()[self.token.i])

    @property
    def lefts(self) -> Iterator["Token"]:
        """The children before the token, in the text order."""
        return (t for t in self.children if t.token.i < self.token.i)

    @property
    def rights(self) -> Iterator["Token"]:
        """The children after the token, in the text order."""
        return (t for t in self.children if t.token.i > self.token.i)

    n_lefts = property(fget=lambda self: sum(1 for _ in self.lefts),
                       doc="The number of children before the token.")

    n_rights = property(fget=lambda self: sum(1 for _ in self.rights),
                        doc="The number of children after the token.")

    def _subtree_indices(self) -> List[int]:
        children = self._needs_doc("subtree")._children()
        result, todo = [], [self.token.i]
        while todo:
            k = todo.pop()
            result.append(k)
            todo.extend(children[k])
        return sorted(result)

    @property
    def subtree(self) -> Iterator["Token"]:
        """The token and all its descendants, in the text order."""
        return (self._doc[k] for k in self._subtree_indices())

    left_edge = property(fget=lambda self: self._doc[self._subtree_indices()[0]],
                         doc="The leftmost token of the token's subtree.")

    right_edge = property(fget=lambda self: self._doc[self._subtree_indices()[-1]],
                          doc="The rightmost token of the token's subtree.")

    @property
    def ancestors(self) -> Iterator["Token"]:
        """The heads of the token, from its own one to the root of its sentence."""
        token = self
        seen = {self.token.i}
        while True:
            head = token.head
            if head.token.i in seen:
                return
            seen.add(head.token.i)
            yield head
            token = head

    def is_ancestor(self, descendant: "Token") -> bool:
        """Whether this token is an ancestor of the token descendant."""
        return any(a == self for a in descendant.ancestors)

    @property
    def sent(self) -> "Span":
        """The sentence span that this token is a part of."""
        doc = self._needs_doc("sent")
        for sent in doc.sents:
            if sent.start <= self.token.i < sent.end:
                return sent
        raise ValueError("Token.sent: the token is in no sentence")

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self._doc is other._doc and self.token.i == other.token.i

    def __hash__(self) -> int:
        return hash((id(self._doc), self.token.i))


class _SentencesIterator:
    """Doc Sentences Iterator class"""

    def __init__(self, doc):
        # Doc object reference
        self._doc = doc
        # index variable to keep track
        self._index = 0

    def __iter__(self):
        """Returns Iterator object"""
        return self

    def __next__(self):
        """'Returns the next value from doc object's lists"""
        if self._index < len(self._doc.limadoc.sentences()):
            result = Span(self._doc,
                          self._doc.limadoc.sentences()[self._index].start+(
                              1 if self._index > 0 else 0),
                          self._doc.limadoc.sentences()[self._index].end+1)
            self._index += 1
            return result
        # Iteration ends
        raise StopIteration


class _SpanIterator:
    """Span Iterator class"""

    def __init__(self, span):
        # Span object reference
        self._span = span
        # index variable to keep track
        self._index = 0

    def __iter__(self):
        """Returns Iterator object"""
        return self

    def __next__(self):
        """'Returns the next value from span object's lists"""
        if self._index < len(self._span):
            result = self._span[self._index]
            self._index += 1
            return result
        # Iteration ends
        raise StopIteration


class Span:
    """Represents a continuous span of tokens in a Doc.

    Its tokens are doc[start:end] (end excluded), as in spaCy.
    """
    def __init__(self, doc, start: int, end: int, label: str = ""):
        """
        Constructor of a Span

        :param doc: The document on which is built the span.
        :type doc: Doc
        :param start: The id of the fist token of the span.
        :type start: int
        :param start: The id of past the last token of the span.
        :type start: int
        :param label: A label to attach to the span, e.g. for named entities.
        :type start: str
        """
        self._doc = doc
        self._start = start
        self._end = end
        self._label = label

    def __iter__(self) -> _SpanIterator:
        """Returns Iterator object"""
        return _SpanIterator(self)

    def __len__(self) -> int:
        """
        Returns the number of tokens of this span

        Example::

            import aymara.lima
            nlp = aymara.lima.Lima()
            doc = nlp("Give it back! He pleaded.")
            span = doc[1:4]
            assert len(span) == 3

        :return: the number of tokens in this span
        :rtype: int
        """
        return max(0, self._end - self._start)

    def __getitem__(self, i: Union[int, slice]):
        """
        Returns either the Token at position i in the span or the subspan defined by
        the slice i.

        Example::

            import aymara.lima
            nlp = aymara.lima.Lima()
            doc = nlp("Give it back! He pleaded.")
            span = doc[1:4]
            assert span[1].text == "back"
            assert span[1:3].text == "back!"

        :param i: the position in the span of the item to retrieve or a slice defining
            the subspan to retriev.
        :type i: int
        :return: either the Token at position i in the span or the subspan defined by
        the slice i.
        :rtype: Union[int, slice]
        """
        if isinstance(i, slice):
            start, stop = _slice_bounds(i, len(self))
            return Span(self._doc, self._start+start, self._start+stop)
        if i < 0:
            i = len(self) + i
        if i < 0 or i >= len(self):
            raise IndexError("Span index out of range")
        return self._doc[self._start+i]

    def __repr__(self) -> str:
        """
        The representation of a span is one line for each token represented in the
        CoNLL-U format.
        """
        if len(self) == 0:
            return ""
        first_tid = self[0].i - 1
        id = 1
        tokens_repr = [token.__repr__() for token in self]
        tokens_repr_reindexed = []
        for token_repr in tokens_repr:
            cols = token_repr.split("\t")
            cols[0] = str(id)
            # 0 is the root: not renumbered (it was negative in the sentences
            # after the first one)
            if cols[6] not in ("_", "0"):
                cols[6] = str(int(cols[6]) - first_tid)
            id += 1
            token_repr = "\t".join(cols)
            tokens_repr_reindexed.append(token_repr)
        return "\n".join(tokens_repr_reindexed)

    text = property(
            fget=lambda self: (self._doc.text[self.start_char:self.end_char]
                               if len(self) > 0 else ""),
            doc="A string representation of the span text.")

    doc = property(
            fget=lambda self: self._doc,
            doc="The parent document.")

    start = property(
            fget=lambda self: self._start,
            doc="The token offset for the start of the span.")

    end = property(
            fget=lambda self: self._end,
            doc="The token offset for the end of the span.")

    start_char = property(
            fget=lambda self: self[0].idx if len(self) > 0 else 0,
            doc="The character offset for the start of the span.")

    end_char = property(
            fget=lambda self: (max(t.idx + len(t) for t in self)
                               if len(self) > 0 else 0),
            doc="The character offset for the end of the span.")

    label = property(
            fget=lambda self: self._label,
            doc=("A label to attach to the span, e.g. for named entities "
                 "(a string: LIMA has no label hashes, unlike spaCy)."))

    label_ = property(
            fget=lambda self: self._label,
            doc="The span's label, as spaCy's label_ (the same as label).")

    @property
    def text_with_ws(self) -> str:
        """The span text with the trailing whitespace of its last token."""
        return self.text + (self[-1].whitespace_ if len(self) > 0 else "")

    @property
    def lemma_(self) -> str:
        """The lemmas of the span's tokens, separated as the tokens are."""
        return "".join(t.lemma_ + t.whitespace_ for t in self).strip()

    @property
    def root(self) -> Token:
        """The token of the span whose head is outside it (or itself): the
        highest one in the dependency tree. If there are several (the span is not
        a subtree), the first of the highest ones."""
        if len(self) == 0:
            raise IndexError("Span.root of an empty span")

        def depth(token):
            return sum(1 for _ in token.ancestors)

        candidates = [t for t in self
                      if t.head_i == t.token.i
                      or not (self._start <= t.head_i < self._end)]
        return min(candidates, key=depth)

    @property
    def sents(self) -> Iterator["Span"]:
        """The sentences that the span overlaps with."""
        return (s for s in self._doc.sents
                if s.start < max(self._end, self._start + 1) and s.end > self._start)

    @property
    def sent(self) -> "Span":
        """The sentence of the span's first token (the span may cross sentence
        boundaries)."""
        return next(iter(self.sents))

    @property
    def ents(self) -> Tuple["Span", ...]:
        """The named entities that fall completely within the span."""
        return tuple(e for e in self._doc.ents
                     if e.start >= self._start and e.end <= self._end)

    def as_doc(self) -> "Doc":
        """A new document with the tokens of the span and their annotations. The
        tokens whose head is outside the span are their own heads (roots), and
        the sentences are cut at the span's bounds."""
        if len(self) == 0:
            return Doc(_PyDoc("", [], [], self._doc.lang_))
        return _sub_doc(self._doc, self._start, self._end, self.text, self.start_char)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Span):
            return NotImplemented
        return (self._doc is other._doc and self._start == other._start
                and self._end == other._end and self._label == other._label)

    def __hash__(self) -> int:
        return hash((id(self._doc), self._start, self._end, self._label))


def _slice_bounds(i: slice, length: int) -> Tuple[int, int]:
    """The [start, stop) bounds of the slice i of a sequence of the given length,
    as Python sequences do (None, negative and out of range bounds)."""
    start, stop, step = i.indices(length)
    if step != 1:
        raise ValueError("Slices of tokens must be contiguous (step 1)")
    return start, max(start, stop)


def _doc_entities(doc) -> Tuple["Span", ...]:
    """The named entities of the document doc, as spans built from the IOB
    tags of its tokens."""
    entities = []
    start, label = None, None
    for k in range(len(doc)):
        token = doc[k]
        iob = token.ent_iob
        if start is not None and (iob != "I" or token.ent_type != label):
            entities.append(Span(doc, start, k, label=label))
            start = None
        if iob == "B" or (iob == "I" and start is None):
            start, label = k, token.ent_type
    if start is not None:
        entities.append(Span(doc, start, len(doc), label=label))
    return tuple(entities)


def _sub_doc(doc: "Doc", start: int, end: int, text: str, offset: int,
             sentence_bounds: Optional[List[Tuple[int, int]]] = None) -> "Doc":
    """A new document of the tokens [start, end) of doc, whose text is text,
    the characters of doc's text from offset: the token positions are shifted
    by offset, the heads outside the tokens become their own tokens (roots), and
    the sentences are cut at the bounds. sentence_bounds: the [start, end) of
    doc's sentences, if already known (they are computed otherwise)."""
    if sentence_bounds is None:
        sentence_bounds = [(sent.start, sent.end) for sent in doc.sents]
    tokens = []
    for k in range(start, end):
        t = doc[k]
        c = t.token
        head = t.head_i - start
        inside = 0 <= head < end - start
        tokens.append(_PyToken(
            len=c.len, text=c.text, i=k - start, lemma=c.lemma, pos=c.pos - offset,
            tag=c.tag, head=head if inside else k - start,
            dep=c.dep, features=c.features, neIOB=c.neIOB, neType=c.neType,
            tStatus=c.tStatus))
    sentences = []
    # The sentences overlapping [start, end) (sentence_bounds are sorted)
    first = bisect.bisect_right([e for _, e in sentence_bounds], start)
    for sent_start, sent_end in sentence_bounds[first:]:
        if sent_start >= end:
            break
        s, e = max(sent_start, start) - start, min(sent_end, end) - start
        if e > s:
            sentences.append((s, e))
    return Doc(_PyDoc(text, tokens, sentences, doc.lang_))


class _DocIterator:
    """Doc Iterator class"""

    def __init__(self, doc):
        # Doc object reference
        self._doc = doc
        # index variable to keep track
        self._index = 0

    def __iter__(self):
        """Returns Iterator object (an iterator must also be iterable: without
        this, comprehensions over a Doc raise TypeError with Python 3.13)"""
        return self

    def __next__(self) -> Token:
        """'Returns the next value from doc object's lists"""
        if self._index < len(self._doc):
            result = self._doc[self._index]
            self._index += 1
            return result
        # Iteration ends
        raise StopIteration


class Doc:
    """A document.

    This is mainly an iterable of tokens.

    Example::

        import aymara.lima
        nlp = aymara.lima.Lima()
        doc = nlp("Give it back! He pleaded.")

    TODO
    Some parts of the API are still not implemented:

        compounds   The compounds found into the document text by the
            CompoundsBuilderFromSyntacticData LIMA pipeline unit
            List[Compound]


    """
    def __init__(self, doc: Union[aymaralima.cpplima.Doc, _PyDoc]):
        self.limadoc = doc

    def __iter__(self) -> _DocIterator:
        """Returns Iterator object"""
        return _DocIterator(self)

    def __len__(self) -> int:
        """'Returns the number of tokens of this document

        :return: the number of tokens of this document.
        :rtype:int
        """
        return self.limadoc.len()

    def __getitem__(self, i: Union[int, slice]) -> Union[Token, Span]:
        """Returns the token at position i or a contiguous slice of tokens.

        Example::

            doc = nlp("Give it back! He pleaded.")
            assert doc[0].text == "Give"
            assert doc[-1].text == "."
            span = doc[1:3]
            assert span.text == "it back"

        :param i: a position i or a contiguous slice of token to retrieve
        :type i: Union[int, slice]
        :return: the token at position i or a contiguous slice of tokens.
        :rtype: Union[int, slice]
        """
        if isinstance(i, slice):
            start, stop = _slice_bounds(i, len(self))
            return Span(self, start, stop)
        if i < 0:
            i = len(self) + i
        if i < 0 or i >= len(self):
            raise IndexError("Doc index out of range")
        return Token(self.limadoc.at(i), self)

    def _sentence_starts(self) -> frozenset:
        """The C++ indices (Token.i - 1) of the first tokens of the sentences."""
        if getattr(self, "_sent_starts", None) is None:
            self._sent_starts = frozenset(s.start for s in self.sents)
        return self._sent_starts

    def __repr__(self) -> str:
        """
        The representation of a document is one line for each token represented in the
        CoNLL-U format.
        """
        return "\n\n".join([repr(sent) for sent in self.sents])
        # return "\n".join([token.__repr__() for token in self])

    def __str__(self) -> str:
        """
        The string of a document is its original text.
        """
        return self.text

    text = property(
            fget=lambda self: self.limadoc.text(),
            doc=("The original text.\n"
                 ":type: str\n"))

    sents = property(
            fget=lambda self: _SentencesIterator(self),
            doc=("    Iterate over the sentences in the document.\n"
                 "        This property is only available when sentence boundaries have"
                 " been set on the\n"
                 "        document by the pipeline. It will raise an error otherwise.\n"
                 "        Example::\n"
                 "sents = list(doc.sents)\n"
                 "          import aymara.lima\n"
                 "          nlp = aymara.lima.Lima()\n"
                 "          doc = nlp(\"This is a sentence. Here's another...\")\n"
                 "          sents = list(doc.sents)\n"
                 "          assert len(sents) == 2\n"
                 "\n"
                 "        :yields:	Sentences in the document.\n"
                 "        :type: Span\n"))

    lang = property(
            fget=lambda self: self.limadoc.language(),
            doc="Language of the document.")

    ents = property(
            fget=lambda self: _doc_entities(self),
            doc=("The named entities in the document, a tuple of Span objects.\n"
                 "        Example::\n"
                 "\n"
                 "          import aymara.lima\n"
                 "          nlp = aymara.lima.Lima()\n"
                 "          doc = nlp(\"John Doe lives in New York\")\n"
                 "          ents = list(doc.ents)\n"
                 "          assert ents[0].label == \"Person.PERSON\"\n"
                 "          assert ents[0].text == \"John Doe\"\n"
                 "\n"
                 "        :type: Tuple[Span, ...]\n"))

    lang_ = property(fget=lambda self: self.limadoc.language(),
                     doc="Language of the document (the LIMA media, e.g. ud-eng).")

    text_with_ws = property(fget=lambda self: self.text,
                            doc="The original text (the same as text).")

    def _children(self) -> Dict[int, List[int]]:
        """The indices of the syntactic children of each token, by token index."""
        if getattr(self, "_children_cache", None) is None:
            children = {k: [] for k in range(len(self))}
            for k in range(len(self)):
                token = self.limadoc.at(k)
                if token.dep not in ("root", "_", "") \
                        and 0 <= token.head < len(self) and token.head != k:
                    children[token.head].append(k)
            self._children_cache = children
        return self._children_cache

    def char_span(self, start_idx: int, end_idx: int, label: str = "",
                  alignment_mode: str = "strict") -> Optional[Span]:
        """The span of the characters [start_idx, end_idx) of the text.

        :param alignment_mode: "strict" (None unless the bounds are token bounds),
            "contract" (the tokens completely inside) or "expand" (the tokens
            overlapping it)
        :return: the span, or None if it does not fit the tokens
        """
        if alignment_mode not in ("strict", "contract", "expand"):
            raise ValueError(f"Unknown alignment_mode {alignment_mode}")
        tokens = [self[k] for k in range(len(self))]
        if alignment_mode == "expand":
            inside = [t.token.i for t in tokens
                      if t.idx < end_idx and t.idx + len(t) > start_idx]
        else:
            inside = [t.token.i for t in tokens
                      if t.idx >= start_idx and t.idx + len(t) <= end_idx]
        if not inside:
            return None
        span = Span(self, inside[0], inside[-1] + 1, label=label)
        if alignment_mode == "strict" and (span.start_char != start_idx
                                           or span.end_char != end_idx):
            return None
        return span

    def has_annotation(self, attr: str) -> bool:
        """Whether some token has the annotation attr: "POS", "TAG", "LEMMA",
        "MORPH", "DEP", "HEAD", "ENT_IOB", "ENT_TYPE", "SENT_START"."""
        attr = attr.upper().rstrip("_")
        tokens = [self.limadoc.at(k) for k in range(len(self))]
        checks = {
            "POS": lambda t: t.tag not in ("", "_"),
            "TAG": lambda t: False,
            "LEMMA": lambda t: t.lemma not in ("", "_"),
            "MORPH": lambda t: t.features not in ("", "_"),
            "DEP": lambda t: t.dep not in ("", "_"),
            "HEAD": lambda t: t.dep not in ("", "_"),
            "ENT_IOB": lambda t: t.neIOB in ("B", "I"),
            "ENT_TYPE": lambda t: t.neType not in ("", "_"),
            "SENT_START": lambda t: True,
            "IS_SENT_START": lambda t: True,
        }
        if attr not in checks:
            raise ValueError(f"Unknown annotation {attr}")
        return any(checks[attr](t) for t in tokens)

    def to_json(self) -> Dict:
        """The document as JSON-serializable data, in spaCy's Doc.to_json format
        (token ids from 0)."""
        return {
            "text": self.text,
            "ents": [{"start": e.start_char, "end": e.end_char, "label": e.label}
                     for e in self.ents],
            "sents": [{"start": s.start_char, "end": s.end_char} for s in self.sents],
            "tokens": [{"id": t.token.i, "start": t.idx, "end": t.idx + len(t),
                        "tag": t.tag_, "pos": t.pos_, "morph": str(t.morph),
                        "lemma": t.lemma_, "dep": t.dep_, "head": t.head_i}
                       for t in self],
        }

    def to_spacy(self, vocab=None):
        """The document as a spaCy Doc (spacy.tokens.Doc), with its lemmas,
        universal parts of speech, morphology, dependency tree, sentences and named
        entities, for spaCy's tools (displaCy, Matcher, DocBin...). Needs spaCy
        (pip install aymara[spacy]); see aymara.lima_spacy.

        :param vocab: the spaCy vocabulary to use (default: a blank pipeline's of
            the document's language)
        """
        from aymara.lima_spacy import doc_to_spacy
        return doc_to_spacy(self, vocab)

    def to_conllu(self) -> str:
        """The document in CoNLL-U format: a "# sent_id" and a "# text" comment per
        sentence, word ids from 1 in each sentence, SpaceAfter=No, and an N-M
        line for the words of a multiword token sharing its position (French
        "du" -> "de" "le"). Doc.from_conllu reads it back.

        :return: the CoNLL-U text, ending with an empty line
        """
        lines = []
        text = self.text
        for n, sent in enumerate(self.sents, start=1):
            lines.append(f"# sent_id = {n}")
            lines.append("# text = " + " ".join(sent.text.split()))
            tokens = list(sent)
            k = 0
            while k < len(tokens):
                # The words sharing the position of the first one
                group = [tokens[k]]
                while (k + len(group) < len(tokens)
                       and tokens[k + len(group)].idx == tokens[k].idx):
                    group.append(tokens[k + len(group)])
                if len(group) > 1:
                    start = group[0].idx
                    end = (tokens[k + len(group)].idx if k + len(group) < len(tokens)
                           else sent.end_char)
                    surface = text[start:end].rstrip()
                    misc = "_" if text[start + len(surface):start + len(surface) + 1].isspace() \
                        or start + len(surface) >= len(text) else "SpaceAfter=No"
                    lines.append(f"{k + 1}-{k + len(group)}\t{surface}\t_\t_\t_\t_\t_\t_\t_\t{misc}")
                for j, t in enumerate(group):
                    in_group = len(group) > 1
                    cols = repr(t).split("\t")
                    cols[0] = str(k + j + 1)
                    if cols[6] not in ("_", "0"):
                        cols[6] = str(int(cols[6]) - sent.start)
                    misc = [m for m in cols[9].split("|") if m and m != "_"]
                    if not in_group and not t.whitespace_ and t.idx + len(t) < len(text):
                        misc.append("SpaceAfter=No")
                    cols[9] = "|".join(misc) if misc else "_"
                    lines.append("\t".join(cols))
                k += len(group)
            lines.append("")
        return "\n".join(lines) + "\n"

    @classmethod
    def from_conllu(cls, conllu: str, lang: str = "") -> "Doc":
        """A document from a CoNLL-U text (e.g. a UD treebank's, or to_conllu's),
        with all the Doc, Span and Token features, without analyzing anything.

        The text is the one of the "# text" comments (joined by spaces), or else
        rebuilt from the forms and SpaceAfter=No. The NE=B-<type> / NE=I-<type>
        MISC values (LIMA's) give the named entities.

        :param conllu: the CoNLL-U text
        :param lang: the language of the document, e.g. "ud-eng" (for is_stop,
            to_spacy...)
        """
        tokens: List[_PyToken] = []
        sentences: List[Tuple[int, int]] = []
        text_parts: List[str] = []

        def misc_value(misc: str, key: str) -> Optional[str]:
            for item in misc.split("|"):
                if item.startswith(key + "="):
                    return item[len(key) + 1:]
            return None

        for block in conllu.strip("\n").split("\n\n"):
            lines = [line for line in block.split("\n") if line.strip()]
            if not lines:
                continue
            sent_text = None
            words, ranges = [], {}
            for line in lines:
                if line.startswith("#"):
                    if line.startswith("# text = "):
                        sent_text = line[len("# text = "):]
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) != 10:
                    raise ValueError(f"Not a CoNLL-U line: {line!r}")
                if "-" in cols[0]:
                    first, last = (int(x) for x in cols[0].split("-"))
                    ranges[first] = (last, cols[1], cols[9])
                elif "." not in cols[0]:
                    words.append(cols)
            if not words:
                continue
            if sent_text is None:
                parts, skip_until = [], 0
                for cols in words:
                    wid = int(cols[0])
                    if wid in ranges:
                        last, form, misc = ranges[wid]
                        parts.append(form + ("" if "SpaceAfter=No" in misc else " "))
                        skip_until = last
                    elif wid > skip_until:
                        parts.append(cols[1] + ("" if "SpaceAfter=No" in cols[9] else " "))
                sent_text = "".join(parts).rstrip()
            base = sum(len(p) + 1 for p in text_parts)   # sentences joined by " "
            text_parts.append(sent_text)
            first_token = len(tokens)
            cursor, mwt_end, mwt_start, mwt_last = 0, 0, 0, 0
            for cols in words:
                wid = int(cols[0])
                if wid in ranges:
                    last, form, _ = ranges[wid]
                    found = sent_text.find(form, cursor)
                    mwt_start = found if found >= 0 else cursor
                    mwt_end, mwt_last = mwt_start + len(form), last
                    cursor = mwt_start
                in_mwt = mwt_end > 0 and wid <= mwt_last
                found = sent_text.find(cols[1], cursor, mwt_end if in_mwt else None)
                if found >= 0:
                    start = found
                    cursor = found + len(cols[1])
                else:
                    start = mwt_start if in_mwt else cursor
                if in_mwt and wid == mwt_last:
                    cursor, mwt_end = max(cursor, mwt_end), 0
                head = int(cols[6]) if cols[6].isdigit() else 0
                dep = cols[7]
                ne = misc_value(cols[9], "NE")
                tokens.append(_PyToken(
                    len=len(cols[1]), text=cols[1], i=len(tokens),
                    lemma=cols[2], pos=base + start + 1, tag=cols[3],
                    head=first_token + head - 1 if head > 0 else 0,
                    dep="root" if head == 0 and dep.lower() == "root" else dep,
                    features=cols[5],
                    neIOB=ne[0] if ne and ne[:2] in ("B-", "I-") else "O",
                    neType=ne[2:] if ne and ne[:2] in ("B-", "I-") else "_",
                    tStatus=""))
            sentences.append((first_token, len(tokens)))
        return cls(_PyDoc(" ".join(text_parts), tokens, sentences, lang))

    @property
    def noun_chunks(self) -> Iterator[Span]:
        """Base noun phrases: a nominal head (NOUN, PROPN, PRON) in a nominal
        relation, with its determiners, modifiers and compounds before it, from the
        UD dependencies (as spaCy's syntax iterators for UD-labelled languages).
        """
        nominal = {"NOUN", "PROPN", "PRON"}
        relations = {"nsubj", "obj", "iobj", "obl", "nmod", "appos", "root",
                     "conj", "dislocated", "vocative", "expl", "compound"}
        before = {"det", "amod", "compound", "nummod", "nmod:poss", "flat",
                  "fixed", "case:poss"}
        after = {"flat", "fixed", "compound"}
        prev_end = 0
        for k in range(len(self)):
            token = self[k]
            if token.pos_ not in nominal:
                continue
            dep = token.dep_.split(":")[0]
            if dep not in relations or (dep == "compound"
                                        and token.head.pos_ in nominal):
                continue
            if dep == "conj" and token.head.pos_ not in nominal:
                continue
            start, end = k, k + 1
            for child in token.lefts:
                if child.dep_ in before or child.dep_.split(":")[0] in before:
                    start = min(start, child.left_edge.token.i)
            for child in token.rights:
                if child.dep_.split(":")[0] in after:
                    end = max(end, child.right_edge.token.i + 1)
            if start < prev_end:
                continue
            prev_end = end
            yield Span(self, start, end, label="NP")


class LimaInternalError(Exception):
    pass


def _check_meta(meta: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Returns the analysis metadata meta (an empty dict for None), or raises a
    TypeError if it is not a dict of strings."""
    if meta is None:
        return {}
    if (not isinstance(meta, dict)
            or not all(isinstance(k, str) and isinstance(v, str)
                       for k, v in meta.items())):
        raise TypeError(f"Lima.analyzeText meta parameter must be Dict[str, str], "
                        f"not {type(meta)}")
    return meta


# The legacy rule-based media (eng, fre, por) are deprecated and no longer built
# in LIMA: their codes select the media analyzing with the deeplima backend
# (tokenization, tagging, lemmatization, parsing) and, for ud-eng and ud-fra,
# the ModEx named entities.
_LEGACY_MEDIA = {"eng": "ud-eng", "fre": "ud-fra", "por": "ud-por"}
# Legacy pipelines and the deeplima pipeline doing the same analysis
_LEGACY_PIPELINES = {
    "main": "deepud",
    "ner-rules": "deepud",
    "ner-deep": "deepud",
    "ner-fusion": "deepud",
    "ner-rules-pretok": "deepud-pretok",
    "ner-deep-pretok": "deepud-pretok",
    "ner-fusion-pretok": "deepud-pretok",
}


def _media(lang: str) -> str:
    """Returns the LIMA media for the language code lang: a legacy code (eng, fre,
    por) is replaced, with a deprecation warning, by the matching UD media."""
    if lang in _LEGACY_MEDIA:
        warnings.warn(f"The legacy LIMA language '{lang}' is deprecated: using "
                      f"'{_LEGACY_MEDIA[lang]}' instead", DeprecationWarning,
                      stacklevel=3)
        return _LEGACY_MEDIA[lang]
    return lang


def _pipeline(pipeline: str) -> str:
    """Returns the pipeline to use for pipeline: a legacy pipeline name is
    replaced, with a deprecation warning, by the matching deeplima pipeline."""
    if pipeline in _LEGACY_PIPELINES:
        warnings.warn(f"The legacy LIMA pipeline '{pipeline}' is deprecated: using "
                      f"'{_LEGACY_PIPELINES[pipeline]}' instead",
                      DeprecationWarning, stacklevel=3)
        return _LEGACY_PIPELINES[pipeline]
    return pipeline


def _unique(items):
    """The items, without duplicates, in their order."""
    return list(dict.fromkeys(items))


class Lima:
    """A text-processing pipeline

    Usually you’ll load this once per process as nlp and pass the instance around your
    application. The Lima class is a wrapper around the LimaAnalyzer class which is
    itself a binding around the C++ classes necessary to analyze text.

    Example::

                import aymara.lima
                nlp = aymara.lima.Lima()
                doc = nlp("Give it back! He pleaded.")
                print(doc)

    """
    def __init__(self,
                 langs: str = "ud-eng",
                 pipes: str = "deepud",
                 user_config_path: str = "",
                 user_resources_path: str = "",
                 meta: Optional[Dict[str, str]] = None):
        """
        Initialize the Lima analyzer

        :param langs: a comma-separated list of languages to initialize, e.g. "ud-eng"
            or "ud-fra" (Default value = "ud-eng"). The deprecated legacy codes "eng",
            "fre" and "por" are replaced by "ud-eng", "ud-fra" and "ud-por". The
            deeplima model ("udlang" metadata) is shared by all the languages of an
            analyzer: use one analyzer per registered UD language.
        :type langs: str
        :param pipes: a comma-separated list of Lima pipelines to analyze (Default value =
            "deepud"). The deprecated legacy pipelines ("main", "ner-rules"...) are
            replaced by "deepud" (or "deepud-pretok").
        :type pipes: str
        :param user_config_path: a path where Lima configuration files will be searched
            for. This allows to override default configurations. (Default value = an empty
            string)
        :type user_config_path: str
        :param user_resources_path: a path where Lima resource files will be searched
            for. This allows to override default configurations (Default value = an empty
            string)
        :type user_resources_path: str
        :param meta: a list of named metadata values that will be used for each
            analysis.They can be completed or overriden at analysis time (Default value = an
            empty dictionary)
        :type meta:  Dict[str, str]
        """
        # print(f"Lima __init__: calling LimaAnalyzer constructor {langs}, {pipes}",
        #       file=sys.stderr)
        meta = dict(meta or {})
        langs = ",".join(_unique(_media(lang) for lang in langs.split(",") if lang))
        pipes = ",".join(_unique(_pipeline(pipe) for pipe in pipes.split(",")))
        ud_codes = _unique(lang[3:] for lang in langs.split(",")
                           if lang.startswith("ud-"))
        if "udlang" not in meta and len(ud_codes) > 1:
            warnings.warn(f"The languages {langs} share one deeplima model (the "
                          f"default one of '{ud_codes[0]}'): use one Lima "
                          f"instance per language", UserWarning, stacklevel=2)
        # A "ud-<code>" language without an explicit udlang uses the default
        # model installed for it by lima_models (its model paths are set here,
        # when the pipeline is built)
        if "udlang" not in meta:
            from aymara.lima_models import default_udlang
            for lang in langs.split(","):
                udlang = (default_udlang(lang[3:], user_resources_path or None)
                          if lang.startswith("ud-") else None)
                if udlang:
                    meta = {**meta, "udlang": udlang}
                    break
        self.analyzer = aymaralima.cpplima.LimaAnalyzer(
            langs,
            pipes,
            list(aymaralima.__path__)[-1],
            user_config_path,
            user_resources_path,
            ",".join([f"{k}:{v}" for k, v in meta.items()])
            )
        if self.analyzer.error():
            raise LimaInternalError(self.analyzer.errorMessage())

        self.langs = langs.split(",")
        self.pipes = pipes.split(",")
        self._user_config_path = user_config_path
        self._meta = meta
        # The units of the pipelines added at runtime (by PhraseMatcher)
        self._pipeline_units: Dict[str, List[str]] = {}

    def __call__(self,
                 text: str,
                 lang: str = None,
                 pipeline: str = None,
                 meta: Optional[Dict[str, str]] = None) -> Doc:
        """
        Just 'call' your Lima instance to analyze the given text in the given language.
        The lang language must have been initialized when instantiating this object.

        Example::

                    import aymara.lima
                    nlp = aymara.lima.Lima()
                    doc = nlp("Give it back! He pleaded.")
                    print(doc)

        :param text: the text to analyze
        :type text: str
        :param lang: the language of the text. If none, will backup to the first element
            of the langs member or to ud-eng if empty (Default value = `None`). A
            language code without the "ud-" prefix gets it ("fra" is "ud-fra"); the
            deprecated legacy codes "eng", "fre" and "por" are replaced by "ud-eng",
            "ud-fra" and "ud-por".
        :type lang: str
        :param pipeline: the Lima pipeline to use for analysis. If none, will backup to
            the first element of the pipelines member or to deepud if empty (Default
            value = `None`). The deprecated legacy pipelines ("main"...) are replaced
            by "deepud".
        :type pipeline: str
        :param meta: a dict of named metadata values (Default value = an empty dictionary).
        :type meta: Dict[str, str]

        :return: a Doc object representing the result of the analysis.
        :rtype: Doc
        """
        if lang is None:
            lang = self.langs[0] if self.langs else "ud-eng"
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        lang = _media(lang)
        if not lang.startswith("ud-") and lang != "ud":
            lang = "ud-" + lang
        if pipeline is None:
            pipeline = self.pipes[0] if self.pipes else "deepud"
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        pipeline = _pipeline(pipeline)
        if not isinstance(text, str):
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        meta = _check_meta(meta)
        lima_doc = self.analyzer(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()]))
        if self.analyzer.error() or lima_doc.error():
            raise LimaInternalError(self.analyzer.errorMessage()
                                    + " / " + lima_doc.errorMessage())
        return Doc(lima_doc)

    def pipe(self, texts: Iterable[str], batch_size: int = 1, n_process: int = 1,
             lang: str = None, pipeline: str = None,
             meta: Optional[Dict[str, str]] = None) -> Iterator[Doc]:
        """Analyze the texts, as spaCy's nlp.pipe: yields one Doc per text, in
        order.

        With batch_size > 1, the texts of a batch are analyzed together (joined
        by blank lines), which is much faster for short texts (about 5 times for
        one-sentence texts), and the result is cut into one Doc per text. The
        analysis of a text may then differ slightly from nlp(text): a text
        without final punctuation may end a sentence with the beginning of the
        next one (its sentence is cut, the relations crossing the cut become
        roots). With the default batch_size of 1, each text is analyzed alone.
        n_process is accepted for compatibility and ignored (one analyzer per
        process).
        """
        if batch_size <= 1:
            for text in texts:
                yield self(text, lang=lang, pipeline=pipeline, meta=meta)
            return
        batch = []
        for text in texts:
            if not isinstance(text, str):
                raise TypeError(f"Lima.pipe texts must be str, not {type(text)}")
            batch.append(text)
            if len(batch) == batch_size:
                yield from self._analyze_batch(batch, lang, pipeline, meta)
                batch = []
        if batch:
            yield from self._analyze_batch(batch, lang, pipeline, meta)

    def _analyze_batch(self, texts: List[str], lang, pipeline, meta) -> Iterator[Doc]:
        """The Docs of texts, analyzed together (see pipe)."""
        separator = "\n\n"
        starts, position = [], 0
        for text in texts:
            starts.append(position)
            position += len(text) + len(separator)
        doc = self(separator.join(texts), lang=lang, pipeline=pipeline, meta=meta)
        bounds = [(sent.start, sent.end) for sent in doc.sents]
        n = len(doc)
        positions = [doc.limadoc.at(k).pos - 1 for k in range(n)]
        k = 0
        for text, start in zip(texts, starts):
            end = start + len(text)
            first = k
            while k < n and positions[k] < end:
                k += 1
            yield _sub_doc(doc, first, k, text, start, bounds)

    lang = property(
        fget=lambda self: self.langs[0] if self.langs else "ud-eng",
        doc="The first language of the analyzer (e.g. ud-eng).")

    @property
    def pipe_names(self) -> List[str]:
        """The names of the units of the analyzer's (first) pipeline, as in its
        LIMA configuration file, e.g. ["RnnTokenizer", "RnnTokensAnalyzer",
        "RnnDependencyParser", "SpecificEntitiesModexAfterPos", "conllDumper"];
        empty if the file is not found. Units added by add_pipeline_unit are not
        listed, the ones of the PhraseMatchers are."""
        pipeline = self.pipes[0] if self.pipes else "deepud"
        if pipeline in self._pipeline_units:
            return list(self._pipeline_units[pipeline])
        return self._configured_units(pipeline)

    def _configured_units(self, pipeline: str) -> List[str]:
        """The units of the pipeline, as in the LIMA configuration file of the
        analyzer's language (empty if the file is not found)."""
        import xml.etree.ElementTree as ET
        file_name = f"lima-lp-{self.lang}.xml"
        dirs = [d for d in str(self._user_config_path or "").replace(",", ":").split(":") if d]
        dirs += [str(_get_data_dir("lima") / "config"),
                 os.path.join(list(aymaralima.__path__)[-1], "config")]
        for d in dirs:
            path = os.path.join(d, file_name)
            if not os.path.isfile(path):
                continue
            for group in ET.parse(path).getroot().iter("group"):
                if group.get("name") == pipeline and group.get("class") == "ProcessUnitPipeline":
                    for lst in group.iter("list"):
                        if lst.get("name") == "processUnitSequence":
                            return [item.get("value") for item in lst.iter("item")]
        return []

    @property
    def meta(self) -> Dict[str, str]:
        """Information about the analyzer, as spaCy's nlp.meta: its language,
        pipeline, deeplima models (udlang) and aymara version."""
        from aymara.version import __version__
        pipeline = self.pipes[0] if self.pipes else "deepud"
        return {"name": f"lima_{pipeline}", "lang": self.lang, "pipeline": pipeline,
                "udlang": self._meta.get("udlang", ""), "version": __version__,
                "pipes": ",".join(self.pipes)}

    def analyzeText(self,
                    text: str,
                    lang: str = None,
                    pipeline: str = None,
                    meta: Optional[Dict[str, str]] = None) -> str:
        """Analyze the given text in the given language. The lang language must have been
        initialized when instantiating this object.

        Example::

                    import aymara.lima
                    nlp = aymara.lima.Lima()
                    result = nlp.analyzeText("Give it back! He pleaded.")
                    print(result)

        :param text: the text to analyze
        :type text: str
        :param lang: the language of the text. If none, will backup to the first element
            of the langs member or to ud-eng if empty (Default value = `None`). The
            deprecated legacy codes "eng", "fre" and "por" are replaced by "ud-eng",
            "ud-fra" and "ud-por".
        :type lang: str
        :param pipeline: the Lima pipeline to use for analysis. If none, will backup to
            the first element of the pipelines member or to deepud if empty (Default
            value = `None`). The deprecated legacy pipelines ("main"...) are replaced
            by "deepud".
        :type pipeline: str
        :param meta: a dict of named metadata values (Default value = an empty
            dictionary).
        :type meta: Dict[str, str]
        :return: the content of the text written by the text dumper of Lima if any. An
            empty string otherwise
        :rtype: str
        """
        # print(f"Lima.analyzeText {text}, {lang}, {pipeline}, {meta}", file=sys.stderr)
        if self.analyzer.error():
            # Not covering line below because it is not easy to make lima fail at will
            raise LimaInternalError(self.analyzer.errorMessage())  # pragma: no cover
        if lang is None:
            lang = self.langs[0] if self.langs else "ud-eng"
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        lang = _media(lang)
        if not lang.startswith("ud-") and lang != "ud":
            lang = "ud-" + lang
        if pipeline is None:
            pipeline = self.pipes[0] if self.pipes else "deepud"
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        pipeline = _pipeline(pipeline)
        if not isinstance(text, str):
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        meta = _check_meta(meta)
        result = self.analyzer.analyzeText(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()]))
        if self.analyzer.error():
            raise LimaInternalError(self.analyzer.errorMessage())
        return result

    def add_pipeline_unit(self, pipeline: str, language: str, group: str):
        """Add a pipeline unit defined by the group json string to the given
        pipeline of the given language.
        Media and pipeline must be already instantiated (defined in the LIMA
        confiuration files). See LIMA documentation for the content of the
        group.
        The new pipeline unit is added at the end of the pipeline.

        Example::

                    import json
                    import aymara.lima
                    nlp = aymara.lima.Lima(
                        "ud-eng", "empty",
                        meta={"udlang": "eng-UD_English-EWT"})
                    group = {
                        "name": "rnntokenizer",
                        "class": "RnnTokenizer",
                        "model_prefix": "tokenizer-$udlang"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group))
                    group = {
                        "name": "rnntokensanalyzer",
                        "class": "RnnTokensAnalyzer",
                        "tagger_model_prefix": "tagger-$udlang",
                        "lemmatizer_model_prefix": "lemmatizer-$udlang"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group))
                    group = {
                        "name": "conllDumper",
                        "class": "ConllDumper",
                        "handler": "simpleStreamHandler",
                        "fakeDependencyGraph": "false"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group))

                    result = nlp.analyzeText("Give it back! He pleaded.")
                    print(result)

        :param pipeline: the pipeline to edit. Use "empty" to change the
            initialy empty pipeline. It is currently not possible to create a
            pipeline from scratch. You must add to a pipeline defined in
            confiuration files
        :type pipeline: str
        :param language: the language to edit
        :type language: str
        :param group: a string dump of a json object representing the
            configuration of the pipeline unit, as defined in XML in LIMA's
            configuration files.
        :type group: str
        :return: True if successful and False otherwise
        :rtype: bool

        """
        result = self.analyzer.addPipelineUnit(pipeline, language, group)
        if self.analyzer.error():
            raise LimaInternalError(self.analyzer.errorMessage())
        return result

    @staticmethod
    def export_system_conf(dir: pathlib.Path = None, lang: str = None) -> bool:
        """Export LIMA configuration files from the module system path to the given
        dir in order to be able to easily change configuration files.

        If lang is given, only the configuration files concerning this language
        are exported (NOT IMPLEMENTED).

        Use this function to initiate a user configuration. For LIMA to take into
        account the configuration in the new path, you will have to add it in front of
        the LIMA_CONF environment variable (or define it if it does not exist).

        Please refer to the
        `LIMA documentation <https://aymara.github.io/lima/usage/configuration/>`_
        for how to configure the analysis:

        Example::

            import aymara.lima
            aymara.lima.Lima.export_system_conf("~/MyLima")

        :param dir: the directory were to export the configuration (Default value =
            None)
        :type dir: Union[str, pathlib.Path]
        :param lang: the language whose configuration must be exported. If `None`, the
            whole configuration is exported (Default value = None)
        :type lang: str
        :return: True if the configuration is correctly exported and False otherwise.
        :rtype: bool
        """
        # Verify thar dir exists and is writable or create it
        # A str (the documented "~/MyLima") as well as a pathlib.Path
        dir = pathlib.Path(dir).expanduser() if dir else _get_data_dir("lima")
        dir.mkdir(parents=True, exist_ok=True)

        fromDirectory = pathlib.Path(list(aymaralima.__path__)[-1]) / "config"
        toDirectory = dir / "config"
        print(f"Copying {str(fromDirectory)} to {str(toDirectory)}")
        _copy_tree(fromDirectory, toDirectory)

        fromDirectory = pathlib.Path(list(aymaralima.__path__)[-1]) / "resources"
        toDirectory = dir / "resources"
        print(f"Copying {str(fromDirectory)} to {str(toDirectory)}")
        _copy_tree(fromDirectory, toDirectory)
        return True

    @staticmethod
    def get_system_paths() -> Tuple[str, str]:
        """
        Get the system configuration and resoures paths.

        Example::

            import aymara.lima
            aymara.lima.Lima.get_system_paths()

        :return: the colon (; under Windows) -separated list of the paths that are
            searched by LIMA to load its configuration files and linguistic resources.
            This function is useful to understand from which dirs data are loaded to
            debug configuration errors. It can also be used to know where to put or edit
            files.
        :rtype: Tuple[str, str]

        """
        return (str(pathlib.Path(list(aymaralima.__path__)[-1]) / "config"),
                str(pathlib.Path(list(aymaralima.__path__)[-1]) / "resources"))


def _modex_escape(text: str) -> str:
    """text as a word of a ModEx rule: its characters other than letters, digits
    and "_" are escaped, as its first one if it begins as a tokenizer status
    (t_..., T_...)."""
    if "\\" in text:
        raise ValueError(f"A ModEx rule cannot match the backslash of {text!r}")
    escaped = "".join(c if c.isalnum() or c == "_" else "\\" + c for c in text)
    if escaped[:2] in ("t_", "T_"):
        escaped = "\\" + escaped
    return escaped


class PhraseMatcher:
    """Matches sequences of tokens, based on their texts (or lemmas, or POS) as
    spaCy's PhraseMatcher, with LIMA's ModEx rules.

    The patterns are turned into ModEx rules, compiled and applied by the
    analyzer itself, after the dependency parsing and before the named
    entities rules: adding the first pattern makes the given Lima instance use
    a new pipeline including the matcher, and only the documents it analyzes
    afterwards contain the matches. Calling the matcher on such a document
    gives its matches.

    The differences with spaCy:

    - the matcher is created with the Lima instance (nlp), not its vocabulary,
      and the documents must be analyzed after the patterns are added;
    - the match ids are the keys, not their hashes;
    - the matches do not overlap: as the other ModEx entities, a match is an
      entity of the document (in doc.ents and the NE CoNLL-U column, with the
      label "PhraseMatcher<n>_<k>.<KEY>"), the longest one starting first is
      kept, and the named entities rules do not apply on its tokens (they
      may include the match, a proper noun for them, in a larger entity,
      which then hides it);
    - LOWER matches the original, lowercase, uppercase, capitalized and title
      forms of the pattern's words; LEMMA matches the lemma and POS of the
      pattern's words; TAG, NORM, SHAPE... are not available.

    Example::

        import aymara.lima
        nlp = aymara.lima.Lima()
        matcher = aymara.lima.PhraseMatcher(nlp)
        matcher.add("OBAMA", [nlp("Barack Obama")])
        doc = nlp("Barack Obama lifts America one last time in emotional farewell")
        assert matcher(doc) == [("OBAMA", 0, 2)]
        assert [span.text for span in matcher(doc, as_spans=True)] == ["Barack Obama"]
    """

    _ATTRS = ("ORTH", "LOWER", "LEMMA", "POS")
    # The units before which the matcher is inserted in the pipeline
    _BEFORE_UNITS = ("SpecificEntitiesModexAfterPos",)
    _count = 0

    def __init__(self, nlp: "Lima", attr: str = "ORTH", validate: bool = False):
        """
        :param nlp: the analyzer which applies the matcher (instead of spaCy's
            vocabulary)
        :type nlp: Lima
        :param attr: the token attribute to match on: "ORTH" (or "TEXT", the
            default), "LOWER", "LEMMA" or "POS"
        :type attr: str
        :param validate: accepted for compatibility with spaCy, ignored
        :type validate: bool
        """
        if not isinstance(nlp, Lima):
            raise TypeError(f"PhraseMatcher needs the Lima instance applying its "
                            f"rules, not {type(nlp)}")
        attr = str(attr).upper()
        if attr == "TEXT":
            attr = "ORTH"
        if attr not in self._ATTRS:
            raise ValueError(f"PhraseMatcher attr must be one of "
                             f"{', '.join(self._ATTRS)} (or TEXT), not {attr!r}")
        PhraseMatcher._count += 1
        self.nlp = nlp
        self.attr = attr
        self.lang = nlp.lang
        self._name = f"PhraseMatcher{PhraseMatcher._count}"
        self._recognizer = f"{self._name}Rules"
        self._installed = False
        # key -> list of patterns, a pattern being the list of the
        # alternative ModEx transitions of each of its words
        self._patterns: Dict[Union[str, int], List[List[List[str]]]] = {}
        self._callbacks = {}
        # key -> entity type (group.type), and back
        self._labels: Dict[Union[str, int], str] = {}
        self._keys: Dict[str, Union[str, int]] = {}

    def __len__(self) -> int:
        """The number of keys (rules) of the matcher."""
        return len(self._patterns)

    def __contains__(self, key) -> bool:
        """Whether the matcher has patterns for key."""
        return key in self._patterns

    def __repr__(self) -> str:
        return (f"PhraseMatcher({self._name}, attr={self.attr!r}, "
                f"keys={list(self._patterns)!r})")

    def _check(self, ok: bool, what: str):
        """Raises the analyzer's error if ok is false."""
        if not ok or self.nlp.analyzer.error():
            raise LimaInternalError(f"PhraseMatcher {what}: "
                                    f"{self.nlp.analyzer.errorMessage()}")

    def _install(self):
        """Adds to the analyzer the recognizer of the matcher, the unit
        applying it, and a pipeline made of the analyzer's one with this unit
        before the named entities rules, which becomes the analyzer's
        default."""
        analyzer, lang = self.nlp.analyzer, self.lang
        base = self.nlp.pipes[0] if self.nlp.pipes else "deepud"
        units = (self.nlp._pipeline_units.get(base)
                 or self.nlp._configured_units(base))
        if not units:
            raise LimaInternalError(f"PhraseMatcher: the units of the pipeline "
                                    f"'{base}' of {lang} are not found")
        unit = f"{self._name}Recognition"
        position = next((k for k, u in enumerate(units)
                         if u in self._BEFORE_UNITS or u.endswith("Dumper")),
                        len(units))
        units = units[:position] + [unit] + units[position:]
        pipeline_unit = f"{self._name}Pipeline"
        pipeline = f"{base}-{self._name.lower()}"
        self._check(analyzer.addResource(lang, json.dumps({
            "name": self._recognizer, "class": "AutomatonRecognizer",
            "rules": ""})), "recognizer")
        self._check(analyzer.addProcessUnit(lang, json.dumps({
            "name": unit, "class": "ApplyRecognizer",
            "automaton": self._recognizer, "applyOnGraph": "PosGraph",
            "useSentenceBounds": "no"})), "unit")
        self._check(analyzer.addProcessUnit(lang, json.dumps({
            "name": pipeline_unit, "class": "ProcessUnitPipeline",
            "processUnitSequence": units})), "pipeline unit")
        self._check(analyzer.addPipeline(pipeline, lang, pipeline_unit),
                    "pipeline")
        self.nlp._pipeline_units[pipeline] = units
        if self.nlp.pipes:
            self.nlp.pipes[0] = pipeline
        else:
            self.nlp.pipes.append(pipeline)
        self._installed = True

    def _declare(self, key):
        """Declares the entity type of the matches of key (one entity group by
        key, for its micro-categories resource)."""
        if key in self._labels:
            return
        group = f"{self._name}_{len(self._labels)}"
        name = re.sub(r"\W", "_", str(key), flags=re.ASCII) or "MATCH"
        self._check(self.nlp.analyzer.addEntityType(group, name), "entity type")
        label = f"{group}.{name}"
        # The micro-category of the token merging the match in the PosGraph
        self._check(self.nlp.analyzer.addResource(self.lang, json.dumps({
            "name": f"{group}Micros", "class": "SpecificEntitiesMicros",
            label: ["PROPN"]})), "micro-categories")
        self._labels[key] = label
        self._keys[label] = key

    def _transitions(self, token: Token) -> List[str]:
        """The alternative ModEx transitions matching token for the attribute
        of the matcher."""
        if self.attr == "ORTH":
            return [_modex_escape(token.text)]
        if self.attr == "LOWER":
            text = token.text
            return [_modex_escape(form) for form in _unique(
                [text, text.lower(), text.upper(), text.capitalize(), text.title()])]
        pos = token.pos_
        if not pos or pos == "_":
            raise ValueError(f"PhraseMatcher {self.attr}: the pattern's word "
                             f"{token.text!r} has no POS")
        if self.attr == "POS":
            return [f"${pos}"]
        lemma = token.lemma_
        if not lemma or lemma == "_":
            raise ValueError(f"PhraseMatcher LEMMA: the pattern's word "
                             f"{token.text!r} has no lemma")
        return [f"{_modex_escape(lemma)}${pos}"]

    def _rules(self) -> str:
        """The ModEx rules of the patterns."""
        labels = [self._labels[key] for key in self._patterns]
        lines = ["set encoding=utf8"]
        if labels:
            lines.append("using groups " + ",".join(
                label.split(".")[0] for label in labels))
        lines.append("set defaultAction=>CreateSpecificEntity()")
        # The first rule matching at a trigger is applied: the longest
        # patterns first
        rules = sorted(((key, pattern) for key, patterns in self._patterns.items()
                        for pattern in patterns), key=lambda rule: -len(rule[1]))
        for key, pattern in rules:
            right = " ".join(alternatives[0] if len(alternatives) == 1
                             else "(" + "|".join(alternatives) + ")"
                             for alternatives in pattern[1:])
            for trigger in pattern[0]:
                lines.append(f"{trigger}::{right}:{self._labels[key]}:")
        return "\n".join(lines) + "\n"

    def _compile(self):
        """Replaces the rules of the recognizer by the ones of the patterns."""
        fd, path = tempfile.mkstemp(prefix=f"{self._name}-", suffix=".rules")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as rules:
                rules.write(self._rules())
            self._check(self.nlp.analyzer.setRecognizerRules(
                self.lang, self._recognizer, path), "rules")
        finally:
            os.remove(path)

    def add(self, key: Union[str, int], docs=None, *_docs, on_match=None):
        """Adds patterns to the matcher, as spaCy's PhraseMatcher.add. The
        documents analyzed afterwards contain their matches.

        :param key: the match id of the patterns (e.g. "OBAMA")
        :type key: Union[str, int]
        :param docs: the patterns: documents (or spans) analyzed by the matcher's
            Lima instance, or strings, which are analyzed by it
        :type docs: List[Union[Doc, Span, str]]
        :param on_match: a callback, called with the matcher, the document, the
            index of a match and the matches, for each match of key
        """
        if docs is None or callable(docs):
            # spaCy v2 signature: add(key, on_match, *docs)
            warnings.warn("PhraseMatcher.add(key, on_match, *docs) is deprecated: "
                          "use add(key, docs, on_match=on_match)",
                          DeprecationWarning, stacklevel=2)
            on_match, docs = docs, list(_docs)
        elif _docs or not isinstance(docs, (list, tuple)):
            raise ValueError("PhraseMatcher.add: the patterns must be a list of "
                             "Doc (add(key, [doc1, doc2]))")
        if not isinstance(key, (str, int)):
            raise TypeError(f"PhraseMatcher key must be str or int, not {type(key)}")
        texts = _unique(d for d in docs if isinstance(d, str))
        if self.attr in ("ORTH", "LOWER"):
            analyzed = list(self.nlp.pipe(texts, batch_size=64))
        else:
            analyzed = [self.nlp(text) for text in texts]
        analyzed = dict(zip(texts, analyzed))
        patterns = []
        for d in docs:
            if isinstance(d, str):
                d = analyzed[d]
            elif not isinstance(d, (Doc, Span)):
                raise TypeError(f"PhraseMatcher patterns must be Doc, Span or str, "
                                f"not {type(d)}")
            pattern = [self._transitions(token) for token in d if not token.is_space]
            if not pattern:
                warnings.warn(f"PhraseMatcher: empty pattern for {key!r} ignored",
                              UserWarning, stacklevel=2)
            elif pattern not in patterns:
                patterns.append(pattern)
        if not self._installed:
            self._install()
        self._declare(key)
        previous = list(self._patterns.get(key, []))
        self._patterns[key] = previous + [p for p in patterns if p not in previous]
        try:
            self._compile()
        except Exception:
            if previous:
                self._patterns[key] = previous
            else:
                del self._patterns[key]
            self._compile()
            raise
        self._callbacks[key] = on_match

    def remove(self, key: Union[str, int]):
        """Removes the patterns of key from the matcher (KeyError if it has
        none): the documents analyzed afterwards do not contain their matches."""
        if key not in self._patterns:
            raise KeyError(key)
        del self._patterns[key]
        self._callbacks.pop(key, None)
        self._compile()

    def __call__(self, doclike: Union[Doc, Span], *, as_spans: bool = False):
        """The matches of the matcher in the document (or the span) doclike,
        analyzed by the matcher's Lima instance after the patterns were added.

        :param doclike: the document or span to search in
        :param as_spans: return Span objects, labelled with the keys, instead of
            (key, start, end) tuples
        :return: the matches, in the order of the document, as (key, start, end)
            tuples (start and end are token indexes in the document, end excluded),
            or as spans
        """
        if isinstance(doclike, Doc):
            doc, start, end = doclike, 0, len(doclike)
        elif isinstance(doclike, Span):
            doc, start, end = doclike.doc, doclike.start, doclike.end
        else:
            raise TypeError(f"PhraseMatcher applies on a Doc or a Span, not "
                            f"{type(doclike)}")
        matches = []
        for entity in doc.ents:
            key = self._keys.get(entity.label_, None)
            if key in self._patterns and start <= entity.start and entity.end <= end:
                matches.append((key, entity.start, entity.end))
        for i, (key, _, _) in enumerate(matches):
            on_match = self._callbacks.get(key)
            if on_match is not None:
                on_match(self, doc, i, matches)
        if as_spans:
            return [Span(doc, s, e, label=key) for key, s, e in matches]
        return matches


def main():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config-path",
        type=str,
        default="",
        help="set the user configuration path to use",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="ud-eng",
        help="set the language to initialize",
    )
    parser.add_argument(
        "-m",
        "--meta",
        type=str,
        help="set metadata for the analyzer",
    )
    parser.add_argument(
        "-p",
        "--pipeline",
        type=str,
        default="deepud",
        help="set the pipeline to initialize",
    )
    parser.add_argument(
        "-r",
        "--resources-path",
        type=str,
        default="",
        help="set the user resources path to use",
    )
    parser.add_argument(
        "file",
        type=str,
        nargs="*",
        help="the file to analyze",
    )
    args = parser.parse_args()
    metadata = {}
    if args.meta:
        meta_list = args.meta.split(",")
        for meta in meta_list:
            k, v = meta.split(":")
            metadata[k] = v
    nlp = Lima(langs=args.language,
               pipes=args.pipeline,
               user_config_path=args.config_path,
               user_resources_path=args.resources_path,
               meta=metadata)
    for file_name in tqdm(args.file):
        with open(file_name) as text_file:
            text = text_file.read()
            r = nlp(text)
            print(repr(r))
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
