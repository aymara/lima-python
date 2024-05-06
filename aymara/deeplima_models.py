#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import requests
import sys
import tempfile
import urllib.request
import zipfile
from tqdm import tqdm
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import List


URL_HF = "https://huggingface.co/aymaralima/deeplima/resolve/main"
URL_C2LC = f"{URL_HF}/c2lc.txt"
URL_DEEP = f"{URL_HF}/%s-%s.zip"
LANGLIST = f"{URL_HF}/langlist.json"
C2LC = {"lang2code": {}, "code2lang": {}, "corpus2code": {}, "code2corpus": {}}


#############################################
# Private functions

def _yesnoconfirm(msg):
    """
    Asks the user to input y or n. Return True if the input is exactly 'y' and
    False otherwise.
    This function is private. It should not be used directly.
    """
    while True:
        try:
            answer = input(f"{msg} [y|N]: ").lower()
        except KeyboardInterrupt:  # pragma: no cover
            print()
            exit(0)

        if answer == 'y':
            return True
        else:
            return False


def _remove_deep_model(target_dir: str, code: str, corpus: str) -> bool:
    """Remove a DeepLima model.
    This function is private. It should not be used directly.

    :param target_dir: str: The target Lima resources directory
    :param code: str: The language code (ISO 639-2 or 639-3)
    :param corpus: str: The UD corpus name
    :param prefix_list: List[str]:

    """
    removed = True
    # for model in ["Tokenizer", "DependencyParser", "Lemmatizer", "Tagger"]:
    model_dir = os.path.join(target_dir, f"RnnTokenizer", "ud")
    if os.path.exists(model_dir):
        if not os.system(
                f"rm -f {model_dir}/tokenizer-{code}-{corpus}.pt") == 0:
            removed = False
            print(f"Failed to remove {model_dir}")  # pragma: no cover
    model_dir = os.path.join(target_dir, f"RnnTagger", "ud")
    if os.path.exists(model_dir):
        if not os.system(f"rm -f {model_dir}/tagger-{code}-{corpus}.pt") == 0:
            removed = False
            print(f"Failed to remove {model_dir}")  # pragma: no cover
    model_dir = os.path.join(target_dir, f"RnnLemmatizer", "ud")
    if os.path.exists(model_dir):
        if (not os.system(
                f"rm -f {model_dir}/lemmatizer-{code}-{corpus}.pt") == 0):
            removed = False
            print(f"Failed to remove {model_dir}")  # pragma: no cover
    model_dir = os.path.join(target_dir, f"RnnDependencyParser", "ud")
    if os.path.exists(model_dir):
        if (not os.system(
                f"rm -f {model_dir}/dependencyparser-{code}-{corpus}.pt")
                == 0):
            removed = False
            print(f"Failed to remove {model_dir}")  # pragma: no cover
    try:
        with open(os.path.join(target_dir, f"{corpus}.json")) as corpus_json_file:
            corpus_json = json.load(corpus_json_file)
            if ("tag" in corpus_json
                    and corpus_json["tag"] is not None
                    and "embd" in corpus_json["tag"]
                    and corpus_json["tag"]["embd"] is not None):
                embd_file_name = os.path.splitext(
                    corpus_json["tag"]["embd"].split("/")[-1])[0]
                try:
                    os.remove(
                        f"{os.path.join(target_dir,'embd',embd_file_name)}.bin")
                except FileNotFoundError as _:
                    try:
                        embd = os.path.join(target_dir, 'embd', embd_file_name)
                        os.remove(f"{embd}.ftz")
                    except FileNotFoundError as e:
                        removed = False
                        print(f"Failed to remove "
                            f"{os.path.join(target_dir,'embd',embd_file_name)}"
                            f".[bin|ftz]")  # pragma: no cover
            os.remove(os.path.join(target_dir, f"{corpus}.json"))
    except FileNotFoundError as e:
        removed = False
        # print(f"Failed to remove {os.path.join(target_dir, f'{corpus}.json')}")
    return removed


def _get_target_dir(dest=None):
    """

    :param dest:  (Default value = None)
    :returns: This function is private. It should not be used directly.

    """
    if not dest:
        if ("XDG_DATA_HOME" in os.environ
                and len(os.environ["XDG_DATA_HOME"]) > 0):
            target_dir_prefix = os.environ["XDG_DATA_HOME"]  # pragma: no cover
        else:
            home_dir = os.path.expanduser("~")
            target_dir_prefix = os.path.join(home_dir, ".local", "share")
        return os.path.join(target_dir_prefix, "lima", "resources")
    else:
        return dest


def _install_deep_model(dir, fn, code, corpus, prefix_list):
    """Install an individual model to its destination.
    This function is private. It should not be used directly.

    :param dir:
    :param fn:
    :param code:
    :param prefix_list:

    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(fn, "r") as zip_ref:
        zip_ref.extractall(dir)


def _download_binary_file(url, dir):
    """Download the file at the given url to the give directory.
    This function is private. It should not be used directly.

    :param url:
    :param dir:

    """
    print(f"Downloading {url}")
    Path(dir).mkdir(parents=True, exist_ok=True)
    chunk_size = 4096
    local_filename = os.path.join(dir, url.split("/")[-1])
    totalbytes = 0
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size_in_bytes = int(response.headers.get("content-length", 0))
        progress_bar = tqdm(total=total_size_in_bytes, unit="iB",
                            unit_scale=True)
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                progress_bar.update(len(chunk))
                if chunk:
                    totalbytes += chunk_size
                    f.write(chunk)
        progress_bar.close()


def _init_c2lc():
    """
    """
    if len(list(C2LC["lang2code"].keys())) == 0:
        with urllib.request.urlopen(URL_C2LC) as f:
            for line in f.read().decode("utf-8").split("\n"):
                line.strip()
                if len(line) > 0:
                    corpus, code = line.split(" ")
                    lang, _ = corpus.split("-")
                    _, lang = lang.split("_", 1)
                    C2LC["lang2code"][lang] = code
                    C2LC["code2lang"][code] = lang
        langlist = _load_lang_list_()
        for code, corpus_list in langlist.items():
            for corpus in corpus_list:
                C2LC["corpus2code"][corpus] = code
                if code not in C2LC["code2corpus"]:
                    C2LC["code2corpus"][code] = []
                C2LC["code2corpus"][code].append(corpus)


def _find_corpus_code(corpus_or_code):
    """

    :param corpus_or_code: either the corpus name or the code
    :returns: trigram, [corpus_name].
    On the first call, the mapping is downloaded from an external source. So,
    you need to be able to access the Internet to use this function.
    This function is private. It should not be used directly.

    """
    if corpus_or_code in C2LC["corpus2code"]:
        # corpus_or_code is a corpus name
        code = C2LC["corpus2code"][corpus_or_code]
        corpora = [corpus_or_code]
        return (code, corpora)
    elif corpus_or_code in C2LC["code2corpus"]:
        # corpus_or_code is a trigram
        code = corpus_or_code
        corpora = C2LC["code2corpus"][code]
        return (code, corpora)
    return None, None


def _list_installed_languages(target_dir):
    """List the models currently available in target_dir.
    This function is private. It should not be used directly.

    :param target_dir:

    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    langs = {
        "tokenizer": _list_installed_languages_per_module(
            join(target_dir, "RnnTokenizer", "ud"), ["tokenizer"]
        ),
        "lemmatizer": _list_installed_languages_per_module(
            join(target_dir, "RnnLemmatizer", "ud"), ["lemmatizer"]
        ),
        "tagger": _list_installed_languages_per_module(
            join(target_dir, "RnnTagger", "ud"), ["tagger"],
        ),
        "embd": _list_installed_languages_per_module(
            join(target_dir, "embd"), ["embd"],
        ),
    }
    return langs


def _list_installed_languages_per_module(target_dir: str,
                                         prefix_list: List[str]):
    """List the installation status of the models from prefix_list for all
    languages in target_dir. Allows also to check the correct installation of
    the models.
    This function is private. It should not be used directly.

    :param target_dir: where the models are installed
    :type target_dir: str
    :param prefix_list: the submodels to check
    :type prefix_list: List[str]

    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    files = [f for f in listdir(target_dir) if isfile(join(target_dir, f))]
    d = {}
    for f in files:
        for prefix in prefix_list:
            corpus_regex = fr"{prefix}-(...)-(UD_[A-Z][a-z]+-[A-Za-z]+)\.pt$"
            mo = re.match(corpus_regex, f)
            if mo and len(mo.groups()) == 2:
                lang, udlang = mo.group(1), mo.group(2)
                if lang not in d:
                    d[lang] = []
                if udlang in d[lang]:
                    print(f'Error: something wrong with "{f}"',
                          file=sys.stderr)
                d[lang].append(udlang)

    r = {}
    for lang in d:
        if lang in r:  # pragma: no cover
            print(f'Error: model for lang "{lang}" is installed twice?',
                  file=sys.stderr)
        for udlang in d[lang]:
            r[udlang] = "installed"

    return r


def _load_lang_list_():
    result = {}
    with tempfile.TemporaryDirectory() as tmpdirname:
        _download_binary_file(LANGLIST, tmpdirname)
        with open(os.path.join(tmpdirname, "langlist.json")) as langlist_file:
            langlist = json.load(langlist_file)
            for lang in langlist:
                for tri in langlist[lang]:
                    for q in langlist[lang][tri]:
                        if "ud" not in langlist[lang][tri][q]:
                            print(f"Error: no ud in {lang}/{tri}/{q}",
                                  file=sys.stderr)
                        elif len(langlist[lang][tri][q]["ud"]) > 0:
                            result[tri] = langlist[lang][tri][q]["ud"]
    return result


def _remove_code(code: str, dest: str = None, force: bool = False) -> bool:
    target_dir = _get_target_dir(dest)
    thecode, corpora = _find_corpus_code(code)
    if not corpora or not code:
        print(f"There is no such language {language}")
        return False
    assert thecode == code
    if not force and not _yesnoconfirm(
            f"Do you really want to remove the {len(corpora)} corpora "
            f"for {code} ?"):
        return False
    prefix_list = ["RnnTokenizer", "RnnTagger", "RnnLemmatizer"]
    removed_something = False
    for corpus in corpora:
        if _remove_deep_model(target_dir, code, corpus):
            removed_something = True
    return removed_something


def _remove_corpus(corpus: str, dest: str = None, force: bool = False) -> bool:
    target_dir = _get_target_dir(dest)
    code, corpora = _find_corpus_code(corpus)
    if not corpora or not code:
        print(f"There is no such language {corpus}")
        return False
    prefix_list = ["RnnTokenizer", "RnnTagger", "RnnLemmatizer"]
    if not force and not _yesnoconfirm(
            f"Do you really want to remove corpus {corpus} ?"):
        return False
    return _remove_deep_model(target_dir, code, corpus)

#############################################
# Public functions


def info() -> None:
    """Print the mapping between language codes and language names"""
    for code, corpora in C2LC["code2corpus"].items():
        print(f"{code:10s}\t{', '.join(corpora)}")


def list_installed_models(dest: str = None) -> None:
    """
    Print the list of models currently available in dest or in a default
    directory if dest is None.

    :param dest: the directory where to search installed models. a default
    directory will be used if dest is None. (Default value = None)
    :type dest: str
    """
    target_dir = _get_target_dir(dest)
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    langs = _list_installed_languages(target_dir)
    all_installed = []
    for k in langs:
        for lang in langs[k]:
            if lang not in all_installed:
                all_installed.append(lang)
    all_installed.sort()

    max_lang_len = 0
    for code in all_installed:
        lang = "Unknown"
        if _find_corpus_code(code)[1] is not None:
            lang = _find_corpus_code(code)[1]
            max_lang_len = max(len(lang), max_lang_len)

    print(
        f'Language {" " * (max_lang_len - len("Language") + 1)}(id ) \t '
        f"Tokenizer Lemmatizer Tagger Embeddings"
    )
    print("---")
    for code in all_installed:
        corpora = ["Unknown"]
        if _find_corpus_code(code)[1] is not None:
            corpora = _find_corpus_code(code)[1]
        for lang in corpora:
            lang = lang + " " * (max_lang_len - len(lang) + 1)
            marks = {
                "tokenizer": (langs["tokenizer"][code]
                              if code in langs["tokenizer"] else "   ---   "),
                "lemmatizer": (langs["lemmatizer"][code]
                               if code in langs["lemmatizer"]
                               else "   ---   "),
                "tagger": (langs["tagger"][code]
                           if code in langs["tagger"] else "   ---   "),
                "embd": (langs["embd"][code]
                         if code in langs["embd"] else "   ---   "),
            }
            print(f"{lang} ({_find_corpus_code(code)[0]}) \t "
                  f"{marks['tokenizer']} {marks['lemmatizer']} "
                  f"{marks['tagger']} {marks['embd']}")


def install_language(language: str, dest: str = None,
                     force: bool = False) -> bool:
    """Install models for the given language.

    :param language: str: the language to install
    :param dest: str: the directory where to save the language data. Use a
        system default if `None` (Default value = None)
    :param force: bool: if False, only models not already present are
        installed. Otherwise, they are replaced by new ones.
        (Default value = False)
    :return: True if installation is successful and False otherwise.
    :rtype: bool
    """
    target_dir = _get_target_dir(dest)
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    code, corpora = _find_corpus_code(language)
    for corpus in corpora:
        print(f"install_language code: {code}, corpus: {corpus}")
        if code is None:
            print(f"There is no such language: {language}", file=sys.stderr)
            print(f"You can check available ones with lima_models.info()",
                file=sys.stderr)
            return False
        deep_url = URL_DEEP % (code, corpus)

        prefix_list = ["tokenizer", "tagger", "lemmatizer", "embd"]

        if not force:
            new_prefix_list = []
            installed = _list_installed_languages(target_dir)
            if "tokenizer" in prefix_list and code not in installed["tokenizer"]:
                new_prefix_list.append("tokenizer")
            if "lemmatizer" in prefix_list and code not in installed["lemmatizer"]:
                new_prefix_list.append("lemmatizer")
            if "tagger" in prefix_list and code not in installed["tagger"]:
                new_prefix_list.append("tagger")
            if "embd" in prefix_list and code not in installed["embd"]:
                new_prefix_list.append("embd")
            prefix_list = new_prefix_list

        if len(prefix_list) > 0:
            print(f"Code: {code}, corpus: {corpus}")
            print(f"Installation dir: {target_dir}")

            if len(prefix_list) < 4:
                print(f"Installing only: {', '.join(prefix_list)}")

            with tempfile.TemporaryDirectory() as tmpdirname:
                _download_binary_file(deep_url, tmpdirname)
                _install_deep_model(
                    target_dir,
                    os.path.join(tmpdirname, deep_url.split("/")[-1]),
                    code,
                    corpus,
                    prefix_list,
                )
                return True
        else:
            print(f"Language: {corpus}, code: {code}")
            print(f"Installation dir: {target_dir}")
            print("All requested models are already installed")
            return False
    return False


def remove_language(language: str, dest: str = None,
                    force: bool = False) -> bool:
    """
    Remove all the resources for a language or corpus from the system.
    Confirmation is asked by default before removing anything.

    :param language: str: the language to remove. If it is a language code,
        models learnt from all corpora for this code are removed, otherwise it
        must be a corpus name and only models for this corpus are removed
    :param dest: str: if given, remove from this directory. Otherwise, search
        in default directories (Default value = None)
    :param force: bool: If False, confirmation will be asked before removing
        the language (Default value = False)
    :return: True if removing is successful and False otherwise.
    :rtype: bool
    """
    if len(language) == 3:
        return _remove_code(language, dest, force)
    else:
        return _remove_corpus(language, dest, force)


def main():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--avail",
        help="print list of available languages and exit",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--install",
        type=str,
        help="install model for the given corpus name or "
        "language code (example: 'UD_English-EWT' or 'eng')",
    )
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        help="destination directory")
    parser.add_argument(
        "-r",
        "--remove",
        type=str,
        help="delete models for the given corpus name or "
        "language code (example: 'UD_English-EWT' or 'eng')",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="destructive actions (overwriting, removing) without confirmation",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="list installed models"
    )
    args = parser.parse_args()

    dest = _get_target_dir(args.dest)
    Path(dest).mkdir(parents=True, exist_ok=True)
    _init_c2lc()
    if args.avail:
        info()
        sys.exit(0)
    elif args.list is not None and args.list:
        list_installed_models(args.dest)
        sys.exit(0)
    elif args.install:
        install_language(args.install, args.dest, args.force)
        sys.exit(0)
    elif args.remove:
        removed = remove_language(args.remove)
        if not removed:
            print(f"Nothing was removed language {args.remove}")
            # sys.exit(1)
        sys.exit(0)
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    """
    This script is used to manage models for the deeplima version of LIMA.
    These models are stored on HuggingFace.
    """
    main()
