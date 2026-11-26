# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""Runs the "Example::" blocks of aymara.lima's docstrings, so that they stay
true. The examples creating a default analyzer (aymara.lima.Lima()) use the
analyzer shared by the tests (a deepud analyzer costs about 3.5 GB); "nlp" and
"doc" (the analysis of "Give it back! He pleaded.") are predefined."""

import inspect
import re
import textwrap

import pytest

import aymara.lima

try:
    from tests.test_aymara import lima as shared_lima
except ImportError:  # pragma: no cover
    from test_aymara import lima as shared_lima


def _example_blocks(doc: str):
    """The code blocks following "Example::" in the docstring doc."""
    lines = doc.expandtabs().split("\n")
    k = 0
    while k < len(lines):
        if lines[k].strip().endswith("Example::"):
            indent = len(lines[k]) - len(lines[k].lstrip())
            k += 1
            block = []
            while k < len(lines) and (not lines[k].strip()
                                      or len(lines[k]) - len(lines[k].lstrip()) > indent):
                block.append(lines[k])
                k += 1
            code = textwrap.dedent("\n".join(block)).strip()
            if code:
                yield code
        else:
            k += 1


def _documented_objects():
    """(name, docstring) of aymara.lima, its classes and their members."""
    yield "aymara.lima", aymara.lima.__doc__ or ""
    for cname, cls in vars(aymara.lima).items():
        if not inspect.isclass(cls) or cls.__module__ != "aymara.lima" \
                or cname.startswith("_"):
            continue
        yield cname, cls.__doc__ or ""
        for mname, member in vars(cls).items():
            if isinstance(member, (staticmethod, classmethod)):
                member = member.__func__
            if isinstance(member, property) or inspect.isfunction(member):
                yield f"{cname}.{mname}", member.__doc__ or ""


EXAMPLES = [(f"{name}#{n}", code)
            for name, doc in _documented_objects()
            for n, code in enumerate(_example_blocks(doc))]


def test_examples_found():
    assert len(EXAMPLES) >= 10


@pytest.mark.parametrize("name,code", EXAMPLES, ids=[name for name, _ in EXAMPLES])
def test_docstring_example(name, code, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))   # export_system_conf("~/MyLima")
    monkeypatch.chdir(tmp_path)
    code = re.sub(r"aymara\.lima\.Lima\(\)", "shared_lima", code)
    namespace = {"shared_lima": shared_lima, "nlp": shared_lima,
                 "doc": shared_lima("Give it back! He pleaded.")}
    exec(compile(code, f"<{name}>", "exec"), namespace)
