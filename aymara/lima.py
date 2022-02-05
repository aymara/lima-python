#!/usr/bin/env python3
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
from typing import Tuple

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
        ans = pathlib.Path(getenv('XDG_DATA_HOME', "~/.local/share")).expanduser()
    return ans.joinpath(appname)


class Lima:
    def __init__(self, langs: str = "fre,eng", pipes: str = "main,deepud",
                 user_config_path: str = None,
                 user_resources_path: str = None):
        self.analyzer = aymaralima.lima.LimaAnalyzer(langs, pipes,
                                                     aymaralima.__path__[-1],
                                                     user_config_path,
                                                     user_resources_path)

    def analyzeText(self,
                    text: str,
                    lang: str = "eng",
                    pipeline: str = None) -> pyconll.unit.conll.Conll:
        if pipeline is None:
            if lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        return pyconll.load.load_from_string(
            self.analyzer.analyzeText(text, lang=lang, pipeline=pipeline))

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

        fromDirectory = pathlib.Path(aymaralima.__path__[-1]) / "config"
        toDirectory = dir / "config"
        copy_tree(str(fromDirectory), str(toDirectory))

        fromDirectory = pathlib.Path(aymaralima.__path__[-1]) / "resources"
        toDirectory = dir / "resources"
        copy_tree(str(fromDirectory), str(toDirectory))
        return True

    @staticmethod
    def GetSystemPaths() -> Tuple[str, str]:
        """
        @return LIMA config and resources paths from the aymara module
        """
        return (str(pathlib.Path(aymaralima.__path__[-1]) / "config"),
                str(pathlib.Path(aymaralima.__path__[-1]) / "resources"))
