#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
import json
import pyconll
import requests
import subprocess
import sys
import time
from typing import List

client = None
debug = True


class DockerClient:
    """
    """

    def __init__(self, port="8080"):
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
        self.port = port
        self.container = None
        self.docker_client = docker.from_env()
        try:
            self.volume = self.docker_client.volumes.list(
              filters={"name": "lima_models"})[0]
        except IndexError as e:
            self.volume = self.docker_client.volumes.create(name='lima_models',
                                                       driver='local')
        running_limas = self.docker_client.containers.list(
          filters={"status": "running",
                   "ancestor": "aymara/lima"})
        if running_limas:
            self.container = running_limas[0]
        else:
            if not self.docker_client.images.list(name="aymara/lima"):
                self.docker_client.images.pull("aymara/lima")
            self.container = self.docker_client.containers.run(
                "aymara/lima",
                # "limaserver",
                detach=True,
                auto_remove=False,
                stdin_open=True,
                ports={f"{self.port}/tcp": self.port},
                volumes={
                    'lima_models':
                        {'bind': '/root/.local/share/lima/', 'mode': 'rw'}
                }
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
        self.container.kill()

    def _start_container(self):
        global debug
        if debug:
            print("starting container", file=sys.stderr)
        self.container = self.docker_client.containers.run(
            "aymara/lima",
            # "limaserver",
            detach=True,
            auto_remove=False,
            stdin_open=True,
            ports={f"{self.port}/tcp": self.port},
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

    def install_model(self, language: str) -> None:
        global debug
        _, stream = self.container.exec_run(
            cmd=f"lima_models.py -l {language}", stream=True)
        output = ""
        for data in stream:
            d = data.decode()
            output += d
            print(d, end='', file=sys.stderr)
        print(file=sys.stderr)
        succes = "Traceback" not in output
        if succes:
            # stop and restart the container to make the new language available
            if debug:
                print("stoping container", file=sys.stderr)
            self.container.kill()
            self._start_container()
        else:
            raise RuntimeError(f"Failed to install model for language "
                               f"{language}.")

    def list_models(self) -> None:
        _, stream = self.container.exec_run(
            cmd=f"lima_models.py -i", stream=True)
        for data in stream:
            print(data.decode(), end='')
        print()


class HostedClient:
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

    def __init__(self, host="localhost", port="8080"):
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
        client = self

    def __del__(self):
        """
        """
        pass

    def install_model(self, language: str) -> None:
        global debug
        result = subprocess.run(["lima_models.py", "-l", language])

    def list_models(self) -> None:
        result = subprocess.run(["lima_models.py", "-i"])
        print()


class Client:
    """
    A simple client for the LIMA REST server

    Attributes
    ----------
    host : str
        the host where the LIMA server is listening
    port : int
        the port on which the LIMA server is listening
    container : bool
        if True, will manage its own docker container. Othewise, we suppose a
        local installation with an already running LIMA server

    Methods
    -------
    analyzeText(text, lang='eng', pipeline='deep')
        Analyze text in lang with the given pipeline
    install_model(language: str)
        Install the model for the given language
    list_models()
        List the existing models
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
        if container:
            client = DockerClient(port)
        else:
            client = HostedClient(host, port)

    def __del__(self):
        """
        If we own the docker container, we  must kill it
        """
        global client
        del client
        client = None

    def analyzeText(self,
                    text: str,
                    lang: str = "eng",
                    pipeline: str = "deep",
                    meta: str = ""):
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
        if meta:
            url += f"&meta={meta}"
        global debug
        if debug:
            print(f'encoded: {text.encode("utf-8")}', file=sys.stderr)
        answer = requests.post(
            url,
            data=text.encode("utf-8"),
            headers={
                "Content-Type":
                    "application/x-www-form-urlencoded; charset=utf-8"
            },
        )
        if answer.status_code == 200:
            str = "\n".join(json.loads(answer.text)["tokens"])
            if debug:
                print(str, file=sys.stderr)
            return pyconll.load_from_string(str)
        else:
            print(
                f"Got HTTP error {answer.status_code}: {answer.text}",
                file=sys.stderr,
            )
            print(f"URL was: {url}", file=sys.stderr)
            return None

    def install_model(self, language: str) -> None:
        global debug
        global client
        client.install_model(language)

    def list_models(self) -> None:
        global client
        client.list_models()


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
