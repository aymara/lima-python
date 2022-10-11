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

import os
import pathlib
import sys

from distutils.dir_util import copy_tree
from pydantic import (parse_obj_as, ValidationError)
from typing import (Dict, Tuple, Union)

import aymaralima.cpplima


def _get_data_dir(appname: str):
    """
    This private function returns the application's data dir as defined by the OS.

    :param appname: the name of the application.
    :type appname: str
    :return: the application's data dir.
    :rtype: str
    """
    if sys.platform == "win32":  # pragma: no cover
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        dir_, _ = winreg.QueryValueEx(key, "Local AppData")
        ans = pathlib.Path(dir_).resolve(strict=False)
    elif sys.platform == 'darwin':  # pragma: no cover
        ans = pathlib.Path('~/Library/Application Support/').expanduser()
    else:
        ans = pathlib.Path(os.getenv('XDG_DATA_HOME', "~/.local/share")).expanduser()
    return ans.joinpath(appname)


class Token:
    """A token

    TODO
    Some parts of the API are still not implemented

        sent     The sentence span that this token is a part of.
        Span

        lang    Language of the parent document’s vocabulary.
        str


    """
    def __init__(self, token: aymaralima.cpplima.Token):
        """Token's constructor

        :param token: the C++ binding Token class
        :type token: aymaralima.cpplima.Token
        """
        assert type(token) == aymaralima.cpplima.Token
        self.token = token

    def __repr__(self) -> str:
        """
        The representation of this token in CoNLL-U format. Tab separated columns:
        ID: Word index, integer starting at 1 for each new sentence; may be a range for
            multiword tokens; may be a decimal number for empty nodes (decimal numbers
            can be lower than 1 but must be greater than 0).
        FORM: Word form or punctuation symbol.
        LEMMA: Lemma or stem of word form.
        UPOS: Universal part-of-speech tag.
        XPOS: always _ in LIMA. Language-specific part-of-speech tag; underscore if not
            available.
        FEATS: List of morphological features from the universal feature inventory or
            from a defined language-specific extension; underscore if not available.
        HEAD: Head of the current word, which is either a value of ID or zero (0).
        DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0) or a
            defined language-specific subtype of one.
        DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
        MISC: Any other annotation.

        :return: return the CoNLL-U representation of this token
        :rtype: str
        """
        return (f"{self.i}\t{self.token.text}\t{self.lemma}\t{self.pos}\t_\t"
                + ("|".join([f'{k}:{v}' for k, v in self.features.items()])
                   if self.features else "_")
                + "\t"
                + f"{self.head if self.head > 0 else '_'}\t"
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
            fget=lambda self: self.token.i,
            doc="The index of this token in its parent document.")

    lemma = property(
            fget=lambda self: self.token.lemma,
            doc="The token lemma.")

    pos = property(
            fget=lambda self: self.token.tag,
            doc="Coarse-grained part-of-speech from the Universal POS tag set.")

    head = property(
            fget=lambda self: self.token.head,
            doc="The syntactic parent, or “governor”, of this token.")

    dep = property(
            fget=lambda self: self.token.dep,
            doc="Syntactic dependency relation.")

    idx = property(
            fget=lambda self: self.token.pos-1,
            doc="Position of this token in its document text.")

    features = property(
            fget=lambda self:  ({} if self.token.features == "_"
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
        fget=lambda self: self.token.i == 0,
        # TODO give access to the document to be able to implemnt that:
        # or self.token.i in [s[0].i for s in self.doc.sents],
        doc=("Does the token start a sentence? bool or None if unknown. "
             "Default value = True for the first token in the Doc."
             "\nTODO: implement for sentences other than the first one."))

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
                          self._doc.limadoc.sentences()[self._index].start,
                          self._doc.limadoc.sentences()[self._index].end)
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

    TODO
    Some parts of the API are still not implemented

        ents    The named entities that fall completely within the span. Returns a tuple of
            Span objects.
            Example::

                import aymara.lima
                nlp = aymara.lima.Lima()
                doc = nlp("Mr. Best flew to New York on Saturday morning.")
                span = doc[0:6]
                ents = list(span.ents)
                assert ents[0].label == 346
                assert ents[0].label_ == "PERSON"
                assert ents[0].text == "Mr. Best"

            Name	Description
            RETURNS	Entities in the span, one Span per entity.
            Tuple[Span, …]

        sent    The sentence span that this span is a part of.
            This property is only available when sentence boundaries have been set on the
            document by the pipeline. It will raise an error otherwise.

            If the span happens to cross sentence boundaries, only the first sentence will be returned. If it is required that the sentence always includes the full span, the result can be adjusted as such:

            sent = span.sent
            sent = doc[sent.start : max(sent.end, span.end)]

            Example::

                import aymara.lima
                nlp = aymara.lima.Lima()
                doc = nlp("Give it back! He pleaded.")
                span = doc[1:3]
                assert span.sent.text == "Give it back!"

        Span

        sents   Returns a generator over the sentences the span belongs to.
            This property is only available when sentence boundaries have been set on the
            document by the pipeline. It will raise an error otherwise.

            If the span happens to cross sentence boundaries, all sentences the span overlaps with will be returned.
            Example::

                import aymara.lima
                nlp = aymara.lima.Lima()
                doc = nlp("Give it back! He pleaded.")
                span = doc[2:4]
                assert len(span.sents) == 2

        Iterable[Span]


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
        return self._end - self._start

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
            start = 0 if i.start is None else i.start
            stop = -1 if i.stop is None else i.stop

            if start < 0:
                start = len(self) + start
            if stop < 0:
                stop = len(self) + stop
            if start >= stop:
                return Span(self._doc, self._start+start, self._start+start)
            if start > len(self):
                return Span(self._doc, self._start+start, self._start+start)
            if start < 0:
                start = 0
            if stop < 0:
                stop = 0
            if stop > len(self):
                stop = len(self)
            return Span(self._doc, self._start+start, self._start+stop)
        else:
            if i < 0:
                i = len(self) + i
            if (i < 0 or i > len(self)
                    or self._start+i < 0 or self._start+i >= len(self._doc)):
                raise IndexError("Span index out of range")
            return self._doc[self._start+i]

    text = property(
            fget=lambda self: (self._doc.text[
                self._doc[self._start].idx:
                    self._doc[self._end-1].idx+len(self._doc[self._end-1])]),
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
            fget=lambda self: self[0].idx,
            doc="The character offset for the start of the span.")

    end_char = property(
            fget=lambda self: self[-1].idx+len(self[-1]),
            doc="The character offset for the end of the span.")

    label = property(
            fget=lambda self: self._label,
            doc="A label to attach to the span, e.g. for named entities.")


class _DocEntitiesIterator:
    """Doc Entities Iterator class"""

    def __init__(self, doc):
        # Doc object reference
        self._doc = doc
        # index variable to keep track
        self._index = 0

    def __iter__(self):
        """Returns Iterator object"""
        return self

    def __next__(self) -> Span:
        """'Returns the next Span defining an entity in the document"""
        while self._index < len(self._doc):
            print(f"doc entities loop {self._index}, {len(self._doc)}", file=sys.stderr)
            if self._doc[self._index].ent_iob == "B":
                start = self._doc[self._index].i
                end = start
                label = self._doc[self._index].ent_type
                while self._index < len(self._doc):
                    print(f"doc entities inner loop {self._index}, {len(self._doc)}", file=sys.stderr)
                    self._index += 1
                    if self._index < len(self._doc):
                        if self._doc[self._index].ent_iob == "I":
                            end = self._index
                        else:
                            return Span(self._doc, start, end, label=label)
            self._index += 1
        # Iteration ends
        raise StopIteration


class _DocIterator:
    """Doc Iterator class"""

    def __init__(self, doc):
        # Doc object reference
        self._doc = doc
        # index variable to keep track
        self._index = 0

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
            return Span(self, i.start, i.stop)
        if i < 0:
            i = len(self) + i
        return Token(self.limadoc.at(i))

    def __repr__(self) -> str:
        """
        The representation of a document is one line for each token represented in the
        CoNLL-U format.
        """
        return "\n".join([token.__repr__() for token in self])

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
                 "          assert [s.root.text for s in sents] == [\"is\", \"'s\"]\n"
                 "\n"
                 "        :yields:	Sentences in the document.\n"
                 "        :type: Span\n"))

    lang = property(
            fget=lambda self: self.limadoc.language(),
            doc="Language of the document.")

    ents = property(
            fget=lambda self: _DocEntitiesIterator(self),
            doc=("Iterate over the entites in the document. Returns an iterator yielding"
                 "named entity Span objects.\n"
                 "        Example::\n"
                 "\n"
                 "          import aymara.lima\n"
                 "          nlp = aymara.lima.Lima()\n"
                 "          doc = nlp(\"John Doe lives in New York\")\n"
                 "          ents = list(doc.ents)\n"
                 "          assert ents[0].label == \"Person.PERSON\"\n"
                 "          assert ents[0].text == \"John Doe\"\n"
                 "\n"
                 "        :yields:	Entities in the document.\n"
                 "        :type: Span\n"))


class LimaInternalError(Exception):
    pass


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
                 langs: str = "fre,eng",
                 pipes: str = "main,deepud",
                 user_config_path: str = "",
                 user_resources_path: str = "",
                 meta: Dict[str, str] = {}):
        """
        Initialize the Lima analyzer

        :param langs: a comma-separated list of language trigrams to initialize
            (Default value = "fre,eng")
        :type langs: str
        :param pipes: a comma-separated list of Lima pipelines to analyze (Default value =
            "main, deepud")
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

        self.langs = langs
        self.pipes = pipes

    def __call__(self,
                 text: str,
                 lang: str = None,
                 pipeline: str = None,
                 meta: Dict[str, str] = {}) -> Doc:
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
            of the langs member or to eng if empty (Default value = `None`).
        :type lang: str
        :param pipeline: the Lima pipeline to use for analysis. If none, will backup to
            the first element of the pipelines member or to main if empty (Default value =
            `None`).
        :type pipeline: str
        :param meta: a dict of named metadata values (Default value = an empty dictionary).
        :type meta: Dict[str, str]

        :return: a Doc object representing the result of the analysis.
        :rtype: Doc
        """
        if lang is None:
            lang = self.langs.split(",")[0] if self.langs else "eng"
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        if lang not in ["eng", "fre", "por"] and not lang.startswith("ud-"):
            lang = "ud-" + lang
        if pipeline is None:
            if self.pipes:
                pipeline = self.pipes.split(",")[0]
            elif lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        if not isinstance(text, str):
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        try:
            parse_obj_as(Dict[str, str], meta)
        except ValidationError as e:
            raise TypeError(f"Lima.analyzeText meta parameter must be Dict[str, str], "
                            f"not {type(meta)}")
        lima_doc = self.analyzer(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()]))
        if self.analyzer.error() or lima_doc.error():
            raise LimaInternalError(self.analyzer.errorMessage()
                                    + " / " + lima_doc.errorMessage())
        return Doc(lima_doc)

    def analyzeText(self,
                    text: str,
                    lang: str = None,
                    pipeline: str = None,
                    meta: Dict[str, str] = {}) -> str:
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
            of the langs member or to eng if empty (Default value = `None`).
        :type lang: str
        :param pipeline: the Lima pipeline to use for analysis. If none, will backup to
            the first element of the pipelines member or to main if empty (Default
            value = `None`).
        :type pipeline: str
        :param meta: a dict of named metadata values (Default value = an empty
            dictionary).
        :type meta: Dict[str, str]
        :return: the content of the text written by the text dumper of Lima if any. An
            empty string otherwise
        :rtype: str
        """
        print(f"Lima.analyzeText {text}, {lang}, {pipeline}, {meta}", file=sys.stderr)
        if self.analyzer.error():
            # Not covering line below because it is not easy to make lima fail at will
            raise LimaInternalError(self.analyzer.errorMessage())  # pragma: no cover
        if lang is None:
            lang = self.langs.split(",")[0] if self.langs else "eng"
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        if lang not in ["eng", "fre", "por"] and not lang.startswith("ud-"):
            lang = "ud-" + lang
        if pipeline is None:
            if self.pipes:
                pipeline = self.pipes.split(",")[0]
            elif lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        if not isinstance(text, str):
            print(f"Lima.analyzeText text ({text}) is not a string. Raising.", file=sys.stderr)
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        try:
            parse_obj_as(Dict[str, str], meta)
        except ValidationError as e:
            raise TypeError(f"Lima.analyzeText meta parameter must be Dict[str, str], "
                            f"not {type(meta)}")
        result = self.analyzer.analyzeText(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()]))
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
        `LIMA documentation <https://github.com/aymara/lima/wiki/LIMA-User-Manual#configuring-lima>`_
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
        copy_tree(str(fromDirectory), str(toDirectory))

        fromDirectory = pathlib.Path(list(aymaralima.__path__)[-1]) / "resources"
        toDirectory = dir / "resources"
        print(f"Copying {str(fromDirectory)} to {str(toDirectory)}")
        copy_tree(str(fromDirectory), str(toDirectory))
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

