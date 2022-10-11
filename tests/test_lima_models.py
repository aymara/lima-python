
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima_models
import os
import pytest
import sys


def test___yesnoconfirm(monkeypatch):
    answers = iter(["y", "Y", "n", "other"])
    monkeypatch.setattr('builtins.input', lambda name: next(answers))
    assert aymara.lima_models._yesnoconfirm("A test") is True
    assert aymara.lima_models._yesnoconfirm("A test") is True
    assert aymara.lima_models._yesnoconfirm("A test") is False
    assert aymara.lima_models._yesnoconfirm("A test") is False


def test__get_target_dir():
    assert aymara.lima_models._get_target_dir("/x/y/z") == "/x/y/z"


def test__find_lang_code():
    assert aymara.lima_models._find_lang_code("no such language") == (None, None)


def test_install_model():
    """Test installation of models for a language. We use Wolof because it is currently
    the smallest in file size."""
    assert aymara.lima_models.install_language("wol", force=True)
    # Test 2 thing: trying to reinstall a model without forcing and use the complete
    # language name instead of the trigram code
    # TODO Understand while the error is not the one expected
    # assert aymara.lima_models.install_language("wolof", force=False) is False
    # Test trying to install a non-exsistent language
    assert aymara.lima_models.install_language("auieauieuia", force=False) is False


# def test_installed_model():
#     import aymara.lima
#     lima = aymara.lima.Lima("wol")
#     result = lima("Wolof làkk la wu ñuy wax ci Gàmbi (Gàmbi Wolof), "
#                   "Gànnaar (Gànnaar Wolof), ak Senegaal (Senegaal Wolof).")
#     assert result.len() > 0


def test_list_installed_models(capsys):
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(wol)" in captured.out


def test_remove_model(capsys):
    # target = aymara.lima_models._get_target_dir()
    # mask = oct(os.stat(target).st_mode)[-3:]
    # # remove write permission to the destination dir…
    # os.chmod(target, 0o444)
    # #… such that remove fails
    # assert not aymara.lima_models.remove_language("wol", force=True)
    # # set back initial permissions…
    # os.chmod(target, mask)
    # # … such that we can (hopfully) remove the language
    assert aymara.lima_models.remove_language("wol", force=True)
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(wol)" not in captured.out


def test_info():
    aymara.lima_models.info()
    assert True
