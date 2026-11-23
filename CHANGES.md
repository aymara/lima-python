## 0.7.0 - 20261123

* A second Linux wheel, manylinux_2_34 with Qt 6.12: Python 3.10 to 3.15 on
  glibc >= 2.34 (Ubuntu 22.04+, Debian 12+, RHEL 9+...). pip chooses: the
  manylinux_2_28 wheel (Qt 6.9, Python 3.9 to 3.13) remains for older systems
  and Python 3.9
* LIMA without its legacy rule-based pipelines (deprecated, aymara/lima#211): the
  whole analysis uses the deeplima backend
* `Lima()` defaults to `ud-eng` and the `deepud` pipeline (was `fre,eng` and
  `main,deepud`)
* The legacy languages `eng`, `fre` and `por` are replaced by `ud-eng`, `ud-fra`
  and `ud-por`, and the legacy pipelines (`main`, `ner-rules`...) by `deepud` (or
  `deepud-pretok`), with a `DeprecationWarning`
* French named entities: the `deepud` pipeline of `ud-fra` runs the French ModEx
  rules (LIMA)
* Named entities recognized after the deeplima analysis: correct dependency heads
  in the documents (they were shifted after an entity) and nested entities (a
  number in a date) are part of the enclosing one; complete dates and times and
  normalized values (LIMA)
* A warning when several `ud-<code>` languages share an analyzer: they use the
  same deeplima model
* `examples/build-pipeline.py` uses the libtorch units

## 0.6.0 - 20261122

* Qt 6.9.3: Python 3.9 to 3.13 (3.7 and 3.8 are no longer supported), on the same
  Linux distributions as before (glibc >= 2.28)
* `import aymara` is enough: `aymara.lima`, `aymara.lima_models`... are imported on
  first use
* No distutils (removed in Python 3.12): `export_system_conf` uses shutil
* The version is set in `aymara/version.py` only: the build, the CI, the PyPI
  publishing and the documentation read it there
* `repr()` of a document or span: the root of a sentence after the first one
  had a negative head instead of 0

## 0.5.0 - 20261121

* LIMA built from the current code: libtorch-based neural pipeline, multiword
  tokens, multithreaded dependency parsing, lemmatizer, parser and tagger fixes
* New models release (aymaralima/deeplima on Hugging Face, tag v0.3.0): 2026
  campaign models, one default model per language, more accurate variants and
  treebank-specific models, licenses and scores in models.json
* `lima_models` rewritten: installs from the models.json manifest (checksums,
  shared embeddings, per-language defaults); `deeplima_models` is now a synonym
  and the former TensorFlow models are no longer supported
* `Lima("ud-<code>")` uses the default model installed for the language when
  no udlang is given
* Correct token offsets (spans cut words after a space or a non-ASCII
  character) and the missing dependency trees of the ud-eng pipeline (LIMA)
* All the languages of the models release have a `ud-<code>` language, `ud-amh`,
  `ud-ben`, `ud-ekk`, `ud-isl` and `ud-nor` included (LIMA)
* Dependencies: requests and unix_ar are no longer needed
* Releases: a version tag publishes the tested wheel to PyPI
* Known issue: each `Lima` analyzer with a deep pipeline uses about 3 GB, not
  released when it is deleted: create one per process and reuse it

## 0.5.0b6 - 20240430

* Update to latest Lima
* Switch to deepud-based Lima
* Switch to Qt 6.5.2

## 0.5.0b5 - 20230623

* Update to latest Lima
* Correct ud languages init

## 0.5.0b4 - 20221222

* Update to latest Lima

## 0.5.0b3 - 20221012

* More unit tests with several analyzers

## 0.5.0b2 - 20221012

* Unit tests with coverage at 100% for main API

## 0.5.0b1 - 20221006

* New API inspired by spaCy
  Most important parts of Lima (equivalent to Language), Doc, Span and Token are implemented.
* Complete model management API
* API documentation on readthedocs (https://lima-python.readthedocs.io/en/port-to-qt6/)
* Unit tests with coverage (currently 80%)

## 0.4.1 - 20220728

* abi3-based wheel usable on all python >= 3.7, < 4

## 0.4.0 - 20220720

* Switch to MIT license

## 0.3.5 - 20220217

* Make Lima class a callable which returns a PyCoNLL object
* analyzeText now returns a string to allow the use of dumpers other than the CoNLL one
* version number now centralized in a file

## 0.3.4 - 20220205

* Add meta parameter to API

## 0.3.3 - 20220205

* Named entities features in output
* Export and use user configuration
* Improve packaging process

## 0.3.2

* Named entities in UD languages

## 0.3.1

* Change API to allow separated config and resources user dirs

## 0.3.0

* First working C++ binding
