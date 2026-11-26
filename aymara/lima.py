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
    Span
    Token

"""


# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import argparse
import os
import pathlib
import shutil
import sys
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
        assert type(token) == aymaralima.cpplima.Token
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
    def __init__(self, doc: aymaralima.cpplima.Doc):
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

    def to_conllu(self) -> str:
        """The document in CoNLL-U format (one line per token, word ids per
        sentence), as repr(doc)."""
        return repr(self)

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
        """Analyze the texts one after the other, as spaCy's nlp.pipe: yields one
        Doc per text, in order. batch_size and n_process are accepted for
        compatibility and ignored (one LIMA analyzer per process)."""
        for text in texts:
            yield self(text, lang=lang, pipeline=pipeline, meta=meta)

    lang = property(
        fget=lambda self: self.langs[0] if self.langs else "ud-eng",
        doc="The first language of the analyzer (e.g. ud-eng).")

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

                    import aymara.lima
                    nlp = aymara.lima.Lima(
                        "ud-eng", "empty",
                        meta={"udlang": "eng-UD_English-EWT"})
                    group = {
                        "name": "rnntokenizer",
                        "class": "RnnTokenizer",
                        "model_prefix": "tokenizer-$udlang"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group)
                    group = {
                        "name": "rnntokensanalyzer",
                        "class": "RnnTokensAnalyzer",
                        "tagger_model_prefix": "tagger-$udlang",
                        "lemmatizer_model_prefix": "lemmatizer-$udlang"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group)
                    group = {
                        "name": "conllDumper",
                        "class": "ConllDumper",
                        "handler": "simpleStreamHandler"
                        "fakeDependencyGraph": "false"
                    }
                    nlp.add_pipeline_unit("empty", "ud-eng", json.dumps(group)

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
        :type dir: pathlib.Path
        :param lang: the language whose configuration must be exported. If `None`, the
            whole configuration is exported (Default value = None)
        :type lang: str
        :return: True if the configuration is correctly exported and False otherwise.
        :rtype: bool
        """
        # Verify thar dir exists and is writable or create it
        if not dir:
            dir = _get_data_dir("lima")
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
