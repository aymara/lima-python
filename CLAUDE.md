# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python bindings for **LIMA**, a multilingual linguistic analyzer written in C++/Qt by CEA LIST. The package is published on PyPI as **`aymara`** (the import name is also `aymara`). It is **Linux x86_64 only**, Python >=3.7,<4.

The public Python API deliberately mirrors spaCy (`Lima` ≈ `nlp`, `Doc`, `Span`, `Token`), including parts of its documentation.

## Architecture

The codebase has two layers that are easy to confuse:

1. **C++ analyzer + shiboken bindings** (repo root). C++ wrapper classes (`lima.cpp/.h` → `LimaAnalyzer`, `Doc.*`, `Span.*`, `Token.*`) wrap the underlying LIMA C++ library. `bindings.h` + `bindings.xml` (a shiboken *typesystem*) drive Qt's **shiboken6** generator, which produces a native Python extension module imported as **`aymaralima.cpplima`**. `CMakeLists.txt` builds this; it expects a very specific manylinux container layout (hardcoded `/opt/_internal/...` shiboken paths) and a `QT_FULL_VERSION` env var — it is **not** meant to be built on a normal dev machine, only inside the build Docker image.

2. **Pure-Python API layer** (`aymara/`). `aymara/lima.py` is the hand-written, user-facing, spaCy-like wrapper. Its `Token`/`Span`/`Doc`/`Lima` classes are thin adapters over the generated `aymaralima.cpplima.*` objects (note: `aymara.lima.Token` wraps `aymaralima.cpplima.Token`, etc.). This is the file to edit for API behavior changes.

So the dependency direction is: user code → `aymara.lima` (Python) → `aymaralima.cpplima` (generated C++ ext) → LIMA C++ library.

### Models are separate from code
LIMA ships **no language models** in the wheel. Users download them at runtime:
- `aymara/lima_models.py` (`lima_models` console script) — legacy + UD pipeline models.
- `aymara/deeplima_models.py` (`deeplima_models` console script) — experimental deeplima models.
Language naming: the media are `ud-eng`/`ud-fra`/`ud-<code>` (UD tagset, deeplima backend; `ud-eng`/`ud-fra` also run the ModEx named entities). The legacy codes `eng`/`fre`/`por` and pipelines (`main`...) are deprecated and no longer in the wheel: `aymara.lima` maps them to `ud-eng`/`ud-fra`/`ud-por` and `deepud` (`_media`, `_pipeline`) with a DeprecationWarning. One deeplima model (`udlang`) per `Lima` instance.

### Console entry points (from setup.py)
- `lima = aymara.lima:main`
- `lima_models = aymara.lima_models:main`
- `deeplima_models = aymara.deeplima_models:main`

## Common commands

### Tests
```bash
pytest                      # full suite (configured via pytest.ini: tests/, -v, coverage xml)
pytest tests/test_aymara.py # one file
pytest tests/test_aymara.py::test_several_instances   # one test
```
Note there are **two pytest configs** (`pytest.ini` and the `[tool.pytest.ini_options]` block in `pyproject.toml`) with different `addopts`; `pytest.ini` is the one that takes effect. Tests require an installed wheel **and** at least the `eng`/`fre`/UD models downloaded — they actually run the analyzer.

### Lint
```bash
flake8        # max-line-length=88, ignores E203 (see .flake8)
black .       # line-length 88
isort .       # config in pyproject.toml
```
`.pre-commit-config.yaml` wires these up.

### Build the wheel (Docker only)
```bash
./gbuild-manylinux_2_28.sh   # Qt6 build: sources python_env_qt6.sh, builds in manylinux_2_28 container,
                             # copies the wheel out, pip-installs it, then runs pytest
```
`python_env_qt6.sh` / `python_env.sh` set the Qt/PySide/Python version env vars consumed by the build. `gbuild.sh` is the older variant.

### Deploy
```bash
./deploy-manylinux_2_28.sh   # twine upload to PyPI
```

## Working notes

- **Version** lives in `aymara/version.py` (`__version__`); `python aymara/version.py` prints it and the build scripts rely on that.
- When changing the Python API, edit `aymara/lima.py`. Changing the C++ surface (new methods on `LimaAnalyzer`/`Doc`/`Span`/`Token`) requires editing the matching `.cpp/.h` **and** `bindings.xml`, then rebuilding in the container.
- The large `aymara-0.5.0b6-*.whl` checked into the repo root is a prebuilt artifact, not source.
- README documents the user-facing install/usage flow and is the source of truth for supported platforms and the spaCy-derived license notice.
