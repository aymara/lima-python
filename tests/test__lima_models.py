
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

import aymara.lima
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
    assert (aymara.lima_models._find_lang_code("no such language")
            == (None, None, None))


def test_install_model():
    """Test installation of models for a language. We use Wolof because it is currently
    the smallest in file size."""
    assert aymara.lima_models.install_language("pcm", force=True)


# @pytest.mark.depends(on=['test_install_model'])
def test_installed_model():
    # lima = aymara.lima.Lima("ud-uig", pipes="deepud")
    # result = lima("بۇ ئۇيغۇردىكى بىر مىسال.")

    # lima = aymara.lima.Lima("ud-wol")
    # result = lima("Wolof làkk la wu ñuy wax ci Gàmbi (Gàmbi Wolof), "
    #               "Gànnaar (Gànnaar Wolof), ak Senegaal (Senegaal Wolof).",
    #               pipeline="deepud")

    lima = aymara.lima.Lima("ud-pcm", pipes="deepud")
    result = lima("Rivers and soakaways don overflow, roads don become "
                  "waterways and homes don destroy.",
                  pipeline="deepud")

    print(repr(result))
    assert len(result) > 0


@pytest.mark.depends(on=['test_install_model'])
def test_install_already_installed_model():
    # Test 2 things: trying to reinstall a model without forcing and use the
    # complete language name instead of the trigram code
    # TODO Understand why the error is not the one expected
    assert aymara.lima_models.install_language("naija", force=False) is False


@pytest.mark.depends(on=['test_install_model'])
def test_install_inexistent_language():
    # Test trying to install a non-existent language
    assert aymara.lima_models.install_language("auieauieuia",
                                               force=False) is False


@pytest.mark.depends(on=['test_install_model'])
def test_list_installed_models(capsys):
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(pcm)" in captured.out


@pytest.mark.depends(on=['test_installed_model', 'test_list_installed_models',
                         'test_install_already_installed_model'])
def test_remove_model(capsys):
    # target = aymara.lima_models._get_target_dir()
    # mask = oct(os.stat(target).st_mode)[-3:]
    # # remove write permission to the destination dir…
    # os.chmod(target, 0o444)
    # #… such that remove fails
    # assert not aymara.lima_models.remove_language("pcm", force=True)
    # # set back initial permissions…
    # os.chmod(target, mask)
    # # … such that we can (hopfully) remove the language
    assert aymara.lima_models.remove_language("pcm", force=True)
    aymara.lima_models.list_installed_models()
    captured = capsys.readouterr()
    assert "(wol)" not in captured.out


def test_remove_model_say_no(monkeypatch):
    answers = iter(["n"])
    monkeypatch.setattr('builtins.input', lambda name: next(answers))
    assert aymara.lima_models.remove_language("not_installed") is False


def test_remove_non_installed_model(monkeypatch):
    answers = iter(["y"])
    monkeypatch.setattr('builtins.input', lambda name: next(answers))
    assert aymara.lima_models.remove_language("not_installed") is False


def test_info():
    aymara.lima_models.info()
    assert True
