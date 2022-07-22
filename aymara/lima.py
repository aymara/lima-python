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
from typing import Dict, Tuple

import aymaralima.lima
import aymaralima


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
        self.analyzer = aymaralima.lima.LimaAnalyzer(
            langs,
            pipes,
            list(aymaralima.__path__)[-1],
            user_config_path,
            user_resources_path,
            ",".join([f"{k}:{v}" for k, v in meta.items()])
            )
        self.langs = langs
        self.pipes = pipes

    def __call__(self, text: str, *args, **kwargs) -> pyconll.unit.conll.Conll:
        analyze = self.analyzeText(text=text, *args, **kwargs)
        return pyconll.load.load_from_string(analyze)

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
