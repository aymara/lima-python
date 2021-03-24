#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
import json
import pyconll
import requests
import sys
import time
from typing import List

client = None
debug = False

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

    def __init__(self, host="localhost", port="8080", container=True):
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
        global debug
        global client
        self.host = host
        self.port = port
        self.container = None
        if host == "localhost" and container:
            docker_client = docker.from_env()
            if not docker_client.images.list(name="aymara/lima"):
                docker_client.images.pull("aymara/lima")
            self.container = docker_client.containers.run(
                "aymara/lima",
                #"limaserver",
                detach=True,
                ports={"{}/tcp".format(self.port): self.port},
            )
            # wait a little time to let limaserver start in the container
            while True:
                logs = self.container.logs()
                logs = logs.decode('UTF-8')
                if debug:
                    print(f"[lima docker image logs] : {logs}",
                          file=sys.stderr)
                if "Server listening on host" in logs:
                    break
                elif "terminate called" in logs:
                    raise RuntimeError("LIMA server crashed.")
                time.sleep(1)

        if client is None:
            client = self

    def __del__(self):
        """
        If we own the docker container, we  must kill it
        """
        if self.container:
            self.container.kill()

    def analyzeText(self, text: str, lang: str="eng", pipeline: str="deep"):
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
        url = "http://{}:{}/?lang={}&pipeline={}".format(
            self.host, self.port, lang, pipeline
        )
        global debug
        if debug:
            print(f'encoded: {text.encode("utf-8")}', file=sys.stderr)
        answer = requests.post(
            url,
            data=text.encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
            },
        )
        if answer.status_code == 200:
            str = "\n".join(json.loads(answer.text)["tokens"])
            if debug:
                print(str, file=sys.stderr)
            return pyconll.load_from_string(str)
        else:
            print(
                "Got HTTP error {}: {}".format(answer.status_code, answer.text),
                file=sys.stderr,
            )
            return None

def word_tokenize(text: str, lang="eng", pipeline="deep") -> List[str]:
    global client
    if client is None:
        client = Client()
    conll = client.analyzeText(text, lang, pipeline)
    print(conll.conll())
    tokens = []
    if conll:
        for sent in conll:
            for tok in sent:
                tokens.append(tok.form)
        return tokens
    return tokens
