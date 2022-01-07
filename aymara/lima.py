#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
import pyconll
import tempfile
import unix_ar
import tarfile
import requests
import urllib.request
from tqdm import tqdm
from os import listdir
from os.path import isfile, join

import aymaralima.lima
import aymaralima


class Lima:
    def __init__(self, langs: str = "fre,eng", pipes: str = "main,deepud"):
        self.analyzer = aymaralima.lima.LimaAnalyzer(langs, pipes,
                                                     aymaralima.__path__[-1])

    def analyzeText(self,
                    text: str,
                    lang: str = "eng",
                    pipeline: str = None) -> pyconll.unit.conll.Conll:
        if not pipeline:
            if lang.startswith("ud-"):
                pipeline = "deepud"
            else:
                pipeline = "main"
        return pyconll.load.load_from_string(
            self.analyzer.analyzeText(text, lang=lang, pipeline=pipeline))
