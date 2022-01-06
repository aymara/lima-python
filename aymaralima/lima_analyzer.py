#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
import tempfile
import unix_ar
import tarfile
import requests
import urllib.request
from tqdm import tqdm
from os import listdir
from os.path import isfile, join

import aymara.lima
import aymara


class Lima:
    def __init__(self):
        self.analyzer = aymara.lima.LimaAnalyzer(aymara.__path__[1])

    def analyzeText(self, text: str, lang: str = "eng", pipeline: str = "main"):
        return self.analyzer.analyzeText(text, lang=lang, pipeline=pipeline)
