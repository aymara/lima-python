
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima_models
import pytest
import sys

def test___yesnoconfirm(monkeypatch):
    answers = iter(["y", "Y", "n", "other"])
    monkeypatch.setattr('builtins.input', lambda name: next(answers))
    assert aymara.lima_models._yesnoconfirm("A test") == True
    assert aymara.lima_models._yesnoconfirm("A test") == True
    assert aymara.lima_models._yesnoconfirm("A test") == False
    assert aymara.lima_models._yesnoconfirm("A test") == False

def test_install_model():
    """Test installation of models for a language. We use Wolof because it is currently
    the smallest in file size."""
    assert aymara.lima_models.install_language("wol", force=True)


# def test_installed_model():
#     lima = aymara.lima.Lima("wol")
#     result = lima("Wolof làkk la wu ñuy wax ci Gàmbi (Gàmbi Wolof), Gànnaar (Gànnaar Wolof), ak Senegaal (Senegaal Wolof).")
#     assert result.len() > 0

def test_list_installed_models(capsys):
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(wol)" in captured.out

def test_remove_model(capsys):
    assert aymara.lima_models.remove_language("wol", force=True)
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(wol)" not in captured.out

def test_info():
    aymara.lima_models.info()
    assert True
