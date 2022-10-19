#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

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
from pathlib import Path
from typing import List


URL_DEB = (
    "https://github.com/aymara/lima-models/releases/download/v0.1.5/"
    "lima-deep-models-%s-%s_0.1.5_all.deb"
)
URL_C2LC = "https://raw.githubusercontent.com/aymara/lima-models/master/c2lc.txt"
C2LC = {"lang2code": {}, "code2lang": {}}


#############################################
# Private functions

def _yesnoconfirm(msg):
    """
    Asks the user to input y or n. Return True if the input is exactly 'y' and False
    otherwise.
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


def _remove_model(target_dir: str, code: str, prefix_list: List[str]) -> bool:
    """Remove a model.
    This function is private. It should not be used directly.

    :param target_dir: str:
    :param code: str:
    :param prefix_list: List[str]:

    """
    removed = False
    for prefix in prefix_list:
        model_dir = os.path.join(target_dir, f"TensorFlow{prefix}", "ud")
        if os.path.exists(model_dir):
            # print(f"Removing *-{code}.* in {model_dir}", file=sys.stderr)
            if os.system(f"rm -f {model_dir}/*-{code}.*") == 0:
                removed = True
            else:
                print(f"Failed to remove {model_dir}")  # pragma: no cover
    return removed


def _get_target_dir(dest=None):
    """

    :param dest:  (Default value = None)
    :returns: This function is private. It should not be used directly.

    """
    if not dest:
        if "XDG_DATA_HOME" in os.environ and len(os.environ["XDG_DATA_HOME"]) > 0:
            target_dir_prefix = os.environ["XDG_DATA_HOME"]  # pragma: no cover
        else:
            home_dir = os.path.expanduser("~")
            target_dir_prefix = os.path.join(home_dir, ".local", "share")
        return os.path.join(target_dir_prefix, "lima", "resources")
    else:
        return dest


def _install_model(dir, fn, code, prefix_list):
    """Install an individual model to its destination. This function is private. It should
    not be used directly.
    This function is private. It should not be used directly.

    :param dir:
    :param fn:
    :param code:
    :param prefix_list:

    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    ar_file = unix_ar.open(fn)
    tarball = ar_file.open("data.tar.gz")
    tar_file = tarfile.open(fileobj=tarball)
    members = tar_file.getmembers()
    for m in members:
        if m.size > 0:
            file = tar_file.extractfile(m)
            if file is not None:
                full_dir, name = os.path.split(m.name)
                if len(prefix_list) > 0:
                    name_prefix, _ = name.split("-")
                    if name_prefix not in prefix_list:
                        continue
                mo = re.match(
                    r"./usr/share/apps/lima/resources/(TensorFlow[A-Za-z\/\-\.0-9]+)",
                    full_dir,
                )
                if mo:
                    subdir = mo.group(1)
                    if subdir is None or len(subdir) == 0:  # pragma: no cover
                        print(f"Error: can't parse '{full_dir}'\n", file=sys.stderr)
                        sys.exit(1)
                    target_dir = os.path.join(dir, subdir)
                    os.makedirs(target_dir, exist_ok=True)
                    with open(os.path.join(target_dir, name), "wb") as f:
                        while True:
                            chunk = file.read(4096)
                            if len(chunk) == 0:
                                break
                            f.write(chunk)
                    # Lets deprecate this old usage:
                    # # LIMA historically uses 'fre' for French.
                    # # This workaround adds symlinks 'fre' -> 'fra' to support
                    # # this.
                    # if code in ["fra"]:
                    #     src_name = os.path.join(target_dir, name)
                    #     symlink_name = re.sub(
                    #         r"-fra.(conf|model|bin)$", r"-fre.\1", name, 1
                    #     )
                    #     symlink_name = os.path.join(target_dir, symlink_name)
                    #     if not os.path.isfile(symlink_name):
                    #         os.symlink(src_name, symlink_name)


def _download_binary_file(url, dir):
    """Download the file at the given url to the give directory. This function is private.
    It should not be used directly.
    This function is private. It should not be used directly.

    :param url:
    :param dir:

    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    chunk_size = 4096
    local_filename = os.path.join(dir, url.split("/")[-1])
    totalbytes = 0
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size_in_bytes = int(response.headers.get("content-length", 0))
        progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                progress_bar.update(len(chunk))
                if chunk:
                    totalbytes += chunk_size
                    f.write(chunk)
        progress_bar.close()


def _find_lang_code(lang_str):
    """

    :param lang_str:
    :returns: either the code or the name.
    On the first call, the mapping is downloaded from an external source. So, you need
    to be able to access the Internet to use this function.
    This function is private. It should not be used directly.

    """
    if len(list(C2LC["lang2code"].keys())) == 0:
        with urllib.request.urlopen(URL_C2LC) as f:
            for line in f.read().decode("utf-8").lower().split("\n"):
                line.strip()
                if len(line) > 0:
                    corpus, code = line.split(" ")
                    lang, corp_id = corpus.split("-")
                    C2LC["lang2code"][lang] = code
                    C2LC["code2lang"][code] = lang

    if lang_str in C2LC["lang2code"]:
        return C2LC["lang2code"][lang_str], lang_str
    elif lang_str in C2LC["code2lang"]:
        return lang_str, C2LC["code2lang"][lang_str]
    return None, None


def _list_installed_languages(target_dir):
    """List the models currently available in target_dir.
    This function is private. It should not be used directly.

    :param target_dir:

    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    langs = {
        "tok": _list_installed_languages_per_module(
            join(target_dir, "TensorFlowTokenizer", "ud"), ["tokenizer"]
        ),
        "lemm": _list_installed_languages_per_module(
            join(target_dir, "TensorFlowLemmatizer", "ud"), ["lemmatizer"]
        ),
        "ms": _list_installed_languages_per_module(
            join(target_dir, "TensorFlowMorphoSyntax", "ud"),
            ["morphosyntax", "fasttext"],
        ),
    }
    return langs


def _list_installed_languages_per_module(target_dir: str, prefix_list: List[str]):
    """List the installation status of the models from prefix_list for all languages in
    target_dir. Allows also to check the correct installation of the models.
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
            mo = re.match(r"%s-([^\.]+)\.([a-z]+)$" % prefix, f)
            if mo and len(mo.groups()) == 2:
                lang, ext = mo.group(1), mo.group(2)
                if lang not in d:
                    d[lang] = []
                if ext in d[lang]:
                    print(f'Error: something wrong with "{f}"', file=sys.stderr)
                d[lang].append(ext)

    r = {}
    for lang in d:
        if lang in r:  # pragma: no cover
            print(f'Error: model for lang "{lang}" is installed twice?',
                  file=sys.stderr)
        if "morphosyntax" in prefix_list:
            if (
                len(d[lang]) != 3
                or "model" not in d[lang]
                or "conf" not in d[lang]
                or "bin" not in d[lang]
            ):
                print(
                    f'Error: model ({",".join(prefix_list)}) '
                    f'for lang "{lang}" is installed incorrectly',
                    file=sys.stderr,
                )
            else:
                r[lang] = "installed"
        else:
            if len(d[lang]) != 2 or "model" not in d[lang] or "conf" not in d[lang]:
                if "lemmatizer" not in prefix_list or "conf" not in d[lang]:
                    print(
                        f'Error: model ({",".join(prefix_list)}) '
                        f'for lang "{lang}" is installed incorrectly',
                        file=sys.stderr,
                    )
                if (
                    "lemmatizer" in prefix_list
                    and "conf" in d[lang]
                    and "model" not in d[lang]
                ):
                    r[lang] = "  empty  "
            else:
                r[lang] = "installed"

    return r

#############################################
# Public functions


def info() -> None:
    """Print the mapping between language codes and language names"""
    _find_lang_code("eng")
    for code in C2LC["code2lang"]:
        print("%-10s\t%s" % (code, C2LC["code2lang"][code]))


def list_installed_models(dest: str = None) -> None:
    """Print the list of the models currently available in dest or in a default
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
        if _find_lang_code(code)[0] is not None:
            lang = _find_lang_code(code)[1]
            max_lang_len = max(len(lang), max_lang_len)

    print(
        f'Language {" " * (max_lang_len - len("Language"))}(id ) \t '
        f"Tokenizer Lemmatizer Morphosyntax"
    )
    print("---")
    for code in all_installed:
        lang = "Unknown"
        if _find_lang_code(code)[0] is not None:
            lang = _find_lang_code(code)[1]
        lang = lang + " " * (max_lang_len - len(lang) + 1)
        marks = {
            "tok": langs["tok"][code] if code in langs["tok"] else "   ---   ",
            "lemm": (langs["lemm"][code] if code in langs["lemm"] else "   ---   "),
            "ms": langs["ms"][code] if code in langs["ms"] else "   ---   ",
        }
        print(f"{lang} ({code}) \t {marks['tok']} {marks['lemm']}  " f"{marks['ms']}")


def install_language(language: str, dest: str = None, select: List[str] = None,
                     force: bool = False) -> bool:
    """Install models for the given language.

    :param language: str: the language to install
    :param dest: str: the directory where to save the language data. Use a system
        default if `None` (Default value = None)
    :param select: List[str]: the language submodels to install, a list of strings from
        "tokenizer", "morphosyntax" and "lemmatizer". If `None`, all will be installed
        (Default value = None)
    :param force: bool: if False, only models not already present are installed.
        Otherwise, they are replaced by new ones. (Default value = False)
    :return: True if installation is successful and False otherwise.
    :rtype: bool
    """
    target_dir = _get_target_dir(dest)
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    code, lang = _find_lang_code(language.lower())
    if code is None or lang is None:
        print(f"There is no such language: {language}", file=sys.stderr)
        print(f"You can check available ones with lima_models.info()", file=sys.stderr)
        return False
    deb_url = URL_DEB % (code, lang)

    prefix_list = ["tokenizer", "morphosyntax", "lemmatizer"]
    if select is not None:
        prefix_list = [x.lower().strip() for x in args.select.split(",")]
    if "morphosyntax" in prefix_list:
        prefix_list.append("fasttext")

    if not force:
        new_prefix_list = []
        installed = _list_installed_languages(target_dir)
        if "tokenizer" in prefix_list and code not in installed["tok"]:
            new_prefix_list.append("tokenizer")
        if "lemmatizer" in prefix_list and code not in installed["lemm"]:
            new_prefix_list.append("lemmatizer")
        if "morphosyntax" in prefix_list and code not in installed["ms"]:
            new_prefix_list.append("morphosyntax")
            new_prefix_list.append("fasttext")
        prefix_list = new_prefix_list

    if len(prefix_list) > 0:
        print("Language: %s, code: %s" % (lang, code))
        print("Installation dir: %s" % target_dir)
        print("Downloading %s" % deb_url)

        if len(prefix_list) < 3:
            print("Installing only: %s" % (", ".join(prefix_list)))

        with tempfile.TemporaryDirectory() as tmpdirname:
            _download_binary_file(deb_url, tmpdirname)
            _install_model(
                target_dir,
                os.path.join(tmpdirname, deb_url.split("/")[-1]),
                code,
                prefix_list,
            )
            return True
    else:
        print("All requested models are already installed")
    return False


def remove_language(language: str, dest: str = None, force: bool = False) -> bool:
    """Remove all the resources for a language from the system. Confirmation is asked by
    default before removing anything.

    :param language: str: the language to remove
    :param dest: str: if given, remove from this directory. Otherwise, search in default
        directories (Default value = None)
    :param force: bool: If False, confirmation will be asked before removing the
    language (Default value = False)
    :return: True if removing is successful and Fales otherwise.
    :rtype: bool
    """
    if not force and not _yesnoconfirm(f"Do you really want to remove language {language} ?"):
        return False
    target_dir = _get_target_dir(dest)
    code, lang = _find_lang_code(language.lower())
    if not lang:
        print(f"There is no such language {language}")
        return False
    prefix_list = ["Tokenizer", "MorphoSyntax", "Lemmatizer"]
    return _remove_model(target_dir, code, prefix_list)


if __name__ == "__main__":  # pragma: no cover
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
        help="install model for the given language name or "
        "language code (example: 'english' or 'eng')",
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
        help="delet model for the given language name or "
        "language code (example: 'english' or 'eng')",
    )
    parser.add_argument(
        "-s",
        "--select",
        type=str,
        help="select particular models to install: tokenizer, "
        "morphosyntax, lemmatizer (comma-separated list)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force reinstallation of existing files",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="list installed models"
    )
    args = parser.parse_args()

    dest = _get_target_dir(args.dest)
    Path(dest).mkdir(parents=True, exist_ok=True)
    if args.avail:
        info()
        sys.exit(0)
    elif args.list is not None and args.list:
        list_installed_models(args.dest)
        sys.exit(0)
    elif args.install:
        install_language(args.install, args.dest, args.select, args.force)
        sys.exit(0)
    elif args.remove:
        removed = remove_language(args.remove)
        if not removed:
            print(f"Failed to remove language {args.remove}")
            sys.exit(1)
        sys.exit(0)
    parser.print_help()
    sys.exit(0)
