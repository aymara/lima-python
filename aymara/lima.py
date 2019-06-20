#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pyconll
import requests

class Lima:
    """
    A simple wrapper around the LIMA REST server
    """

    def __init__(self, host='localhost', port='8080'):
        self.host = host
        self.port = port

    def  analyzeText(self, text, lang='eng', pipeline='deep'):
        url = 'http://{}:{}/?lang={}&pipeline={}'.format(self.host,
                                                         self.port,
                                                         lang,
                                                         pipeline)
        answer = requests.post(url, data = text)
        str = '\n'.join(json.loads(answer.text)['tokens'])
        return pyconll.load_from_string(str)



