#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
import pyconll
import tempfile
import pathlib
import requests
import sys
import tarfile
import unix_ar
import urllib.request

from distutils.dir_util import copy_tree
from tqdm import tqdm
from os import listdir
from os.path import isfile, join
from pydantic import (parse_obj_as, ValidationError)
from typing import (Dict, Tuple, Union)

import aymaralima.cpplima


class Token:
    """
    A token
    """
    def __init__(self, token: aymaralima.cpplima.Token):
        assert type(token) == aymaralima.cpplima.Token
        self.token = token

    def __repr__(self):
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
        """
        return (f"{self.i}\t{self}\t{self.lemma}\t{self.pos}\t_\t_\t"
                f"{self.head if self.head > 0 else '_'}\t{self.dep}\t_\t"
                f"Pos={self.idx}|Len={len(self)}")

    def __len__(self):
        """Return the length of the token in UTF-8 code points"""
        return self.token.len

    def __str__(self):
        """Return the original text of the token."""
        return self.token.text

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
            fget=lambda self: self.token.pos,
            doc="Syntactic dependency relation.")


class DocIterator:
    """Doc Iterator class"""
    def __init__(self, doc):
        # Doc object reference
        self._doc = doc
        # index variable to keep track
        self._index = 0

    def __next__(self):
        """'Returns the next value from doc object's lists"""
        if self._index < len(self._doc):
            result = self._doc[self._index]
            self._index += 1
            return result
        # Iteration ends
        raise StopIteration


class Doc:
    def __init__(self, doc: aymaralima.cpplima.Doc):
        self.doc = doc

    def __iter__(self):
        """Returns Iterator object"""
        return DocIterator(self)

    def __len__(self):
        """'Returns the number of tokens of this document"""
        return self.doc.len()

    def __getitem__(self, i: Union[int, slice]):
        if isinstance(i, slice):
            return Span(self, i.start, i.stop)
        if i < 0:
            i = self.length + i
        return Token(self.doc.at(i))

    def __repr__(self):
        return "\n".join([token.__repr__() for token in self])

    def __str__(self):
        return self.text

    text = property(
            fget=lambda self: self.doc.text(),
            doc="The original text.")


class SpanIterator:
    """Doc Iterator class"""
    def __init__(self, span):
        # Doc object reference
        self._span = span
        # index variable to keep track
        self._index = 0

    def __next__(self):
        """'Returns the next value from doc object's lists"""
        if self._index < self._span.len():
            result = self._span.at(self._index)
            self._index += 1
            return result
        # Iteration ends
        raise StopIteration


class Span:
    def __init__(self, doc: Doc, begin: int, end: int):
        self.doc = doc
        self.begin = begin
        self.end = end


    def __iter__(self):
        """Returns Iterator object"""
        return DocIterator(self)

    def __len__(self):
        """'Returns the number of tokens of this document"""
        return self.end - self.begin

    def __getitem__(self, i: Union[int, slice]):
        # if isinstance(i, slice):
        #     start, stop = util.normalize_slice(len(self), i.start, i.stop, i.step)
        #     return Span(self, start, stop, label=0)
        if i < 0:
            i = len(self) + i
        return self.doc[self.begin+i]


def get_data_dir(appname):
    if sys.platform == "win32":
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        dir_, _ = winreg.QueryValueEx(key, "Local AppData")
        ans = pathlib.Path(dir_).resolve(strict=False)
    elif sys.platform == 'darwin':
        ans = pathlib.Path('~/Library/Application Support/').expanduser()
    else:
        ans = pathlib.Path(os.getenv('XDG_DATA_HOME', "~/.local/share")).expanduser()
    return ans.joinpath(appname)


class Lima:
    def __init__(self,
                 langs: str = "fre,eng",
                 pipes: str = "main,deepud",
                 user_config_path: str = "",
                 user_resources_path: str = "",
                 meta: Dict[str, str] = {}):
        self.analyzer = aymaralima.cpplima.LimaAnalyzer(
            langs,
            pipes,
            list(aymaralima.__path__)[-1],
            user_config_path,
            user_resources_path,
            ",".join([f"{k}:{v}" for k, v in meta.items()])
            )
        self.langs = langs
        self.pipes = pipes

    def __call__(self,
                 text: str,
                 lang: str = None,
                 pipeline: str = None,
                 meta: Dict[str, str] = {}) -> Doc:
        if lang is None:
            lang = self.langs.split(",")[0] if self.langs else "eng"
        if pipeline is None:
            pipeline = self.pipes.split(",")[0] if self.pipes else "main"
        if not isinstance(text, str):
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        try:
            parse_obj_as(Dict[str, str], meta)
        except ValidationError as e:
            raise TypeError(f"Lima.analyzeText meta parameter must be Dict[str, str], "
                            f"not {type(meta)}")
        if pipeline is None:
            if lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        return Doc(self.analyzer(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()])))

    def analyzeText(self,
                    text: str,
                    lang: str = None,
                    pipeline: str = None,
                    meta: Dict[str, str] = {}) -> str:
        if lang is None:
            lang = self.langs.split(",")[0] if self.langs else "eng"
        if pipeline is None:
            pipeline = self.pipes.split(",")[0] if self.pipes else "main"
        if not isinstance(text, str):
            raise TypeError(f"Lima.analyzeText text parameter must be str, "
                            f"not {type(text)}")
        if not isinstance(lang, str):
            raise TypeError(f"Lima.analyzeText lang parameter must be str, "
                            f"not {type(lang)}")
        if not isinstance(pipeline, str):
            raise TypeError(f"Lima.analyzeText pipeline parameter must be str, "
                            f"not {type(pipeline)}")
        try:
            parse_obj_as(Dict[str, str], meta)
        except ValidationError as e:
            raise TypeError(f"Lima.analyzeText meta parameter must be Dict[str, str], "
                            f"not {type(meta)}")
        if pipeline is None:
            if lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        return self.analyzer.analyzeText(
            text, lang=lang, pipeline=pipeline,
            meta=",".join([f"{k}:{v}" for k, v in meta.items()]))

    @staticmethod
    def ExportSystemConf(dir: pathlib.Path = None, lang: str = None) -> bool:
        """
        Export LIMA configuration files from the module system path to the given
        @ref dir in order to be able to easily change configuration files.
        If @ref lang is given, only the configuration files concerning this language
        are exported (NOT IMPLEMENTED).
        @return True if the export is succesful and False otherwise.
        """
        # Verify thar dir exists and is writable or create it
        if not dir:
            dir = get_data_dir("lima")
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
    def GetSystemPaths() -> Tuple[str, str]:
        """
        @return LIMA config and resources paths from the aymara module
        """
        return (str(pathlib.Path(list(aymaralima.__path__)[-1]) / "config"),
                str(pathlib.Path(list(aymaralima.__path__)[-1]) / "resources"))
