#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
import json
import pyconll
import requests
import sys

class Client:
    """
    A simple client for the LIMA REST server

    Attributes
    ----------
    host : str
        the host where the LIMA server is listening
    port : int
        the port on which the LIMA server is listening

    Methods
    -------
    analyzeText(text, lang='eng', pipeline='deep')
        Analyze text in lang with the given pipeline
    """

    def __init__(self, host='localhost', port='8080', container=True):
        """
        Parameters
        ----------
        host : str
            the host where the LIMA server is listening
        port : int
            the port on which the LIMA server is listening
        container : bool
            if True and host is localhost, then start a docker container
            running limaserver. If the LIMA docker image is not available,
            pull it beforehand
        """
        self.host = host
        self.port = port
        self.container = None
        if host == 'localhost' and container:
            client = docker.from_env()
            if not client.images.list(name="aymara/lima"):
                client.images.pull("aymara/lima")
            #client.containers.list(filters={'ancestor':'aymara/lima'})
            #for container in client.containers.list(filters={'ancestor':'aymara/lima'}):
                #container.exec_run('pidof limaserver')

            self.container = client.containers.run("aymara/lima", "limaserver",
                                                   detach=True,
                                                   ports={'{}/tcp'.format(self.port): self.port})

    def __del__(self):
        """
        If we own the docker container, we  must kill it
        """
        if self.container:
              self.container.kill()

    def analyzeText(self, text, lang='eng', pipeline='deep'):
        """
        Analyze text in language lang with the given pipeline.

        Parameters
        ----------
        text : str
            The text to analyze (default is None)
        lang : str, optional
            The language of the text (default is 'eng')
        text : str, optional
            The pipeline to use to analyze the text (default is 'deep')

        Returns
        -------
        pyconll.unit.conll.Conll
            A representation in CoNLL-U format of the text. None if an
            error occur.
        """
        url = 'http://{}:{}/?lang={}&pipeline={}'.format(self.host,
                                                         self.port,
                                                         lang,
                                                         pipeline)
        answer = requests.post(url, data = text)
        if answer.status_code == 200:
            str = '\n'.join(json.loads(answer.text)['tokens'])
            return pyconll.load_from_string(str)
        else:
            print('Got HTTP error {}: {}'.format(answer.status_code,
                                                 answer.text),
                  file=sys.stderr)
            return None
