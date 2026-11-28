# Changes

## 0.11.0 - 20261128

Built on LIMA 3.2.0.

* `LimaAnalyzer` (C++): the handlers of an analysis are the ones its
  pipeline's dumpers need, created from the LIMA configuration (aymara/lima#3,
  aymara/lima#247), instead of five hard-coded ones; `analyzeText` still
  returns the output of `simpleStreamHandler`.

## 0.10.0 - 20261127

Phrase matching with spaCy's `PhraseMatcher` API, on LIMA's ModEx rules.

* `PhraseMatcher` (#5): spaCy's `PhraseMatcher` API (`add`, `remove`,
  `on_match`, `as_spans`, `attr="ORTH"|"LOWER"|"LEMMA"|"POS"`) on LIMA's
  ModEx rules, compiled at runtime and applied by the analyzer before its
  named entities rules. Needs aymara/lima's runtime rules compilation
  (installed `libautomatonCompiler` headers, `Recognizer::clearRules`).
* `LimaAnalyzer` (C++): `addResource`, `addProcessUnit`, `addPipeline`,
  `addEntityType` and `setRecognizerRules`, to configure an analyzer at
  runtime; `Lima.pipe_names` lists the units of these pipelines
* C++ `Token.neNested`: the named entities nested in the token's one (e.g. a
  PhraseMatcher match that a named entities rule included afterwards in a
  location), so that the matcher finds its matches hidden in `doc.ents`
* CI: the tests use the wheel of their own run (a concurrent run could
  replace the shared `latest` image meanwhile) (#45)

## 0.9.0 - 20261127

Much closer to spaCy's API, spaCy interoperability, and faster analysis of
short texts. **Breaking**: `Token.head` is now a `Token` (see below).

* `Doc.from_conllu(text, lang)`: a document from CoNLL-U (a UD treebank's,
  multiword tokens included, or LIMA's), with all the `Doc`/`Span`/`Token`
  features and no analysis; `Span.as_doc()`: a new document of a span
* `Doc.to_conllu()` writes standard CoNLL-U: `# sent_id` and `# text`
  comments, `SpaceAfter=No`, and N-M lines for multiword tokens (it was
  `repr(doc)`, still available)
* `Token.is_stop`, from spaCy's stop word lists for 76 languages, vendored in
  `aymara.stop_words` (MIT; spaCy is not needed)
* `Lima.pipe_names` (the units of the pipeline, from its configuration) and
  `Lima.meta`
* `Lima.pipe(texts, batch_size=n)` with `n > 1` analyzes the texts of a batch
  together: about 3 times faster for one-sentence texts (25 ms -> 7 ms per
  text, with aymara/lima#238), a text's analysis then possibly differing
  slightly from `nlp(text)` (sentences and context across texts); the
  default `batch_size=1` analyzes each text alone
* The docstring examples are run by the tests (they were partly wrong);
  `Lima.export_system_conf` accepts a `str`, as its example does
* spaCy interoperability (optional: `pip install aymara[spacy]`), in the new
  module `aymara.lima_spacy`:
  - `doc.to_spacy()` converts a LIMA document into a `spacy.tokens.Doc` with
    its lemmas, universal parts of speech, morphology, dependency tree,
    sentences and named entities, for displaCy, `Matcher`, `DocBin`...
  - `aymara.lima_spacy.spacy_pipeline("ud-eng")`: a spaCy pipeline whose
    tokenizer is a LIMA analyzer (`nlp(text)` gives a spaCy `Doc`; spaCy
    components can be added after it). Also available in spaCy configs as
    the tokenizer `aymara.LimaTokenizer.v1`
  - the words of a multiword token that do not spell it (French "du" ->
    "de" "le") are separate spaCy tokens: the spaCy text is then "de le", the
    original one is in `doc.user_data["lima_text"]`
* Python 3.13: iterating over a `Doc` in a comprehension no longer raises
  `TypeError: '_DocIterator' object is not iterable`
* **Breaking**: `Token.head` is a `Token`, as in spaCy (the root's head is
  itself, as the one of a token without relation). The former integer, the
  0-based document index of the head, is `Token.head_i`
  (`doc[token.head_i] == token.head`)
* spaCy naming and navigation layer (pure Python):
  - `Token`: `lemma_`, `pos_`, `tag_` (always `_`: no XPOS), `dep_`,
    `ent_type_`, `ent_iob_`, `morph` (a `MorphAnalysis`: `str()`, `get()`,
    `to_dict()`), `whitespace_`, `text_with_ws`, `lower_`, `norm_`, `shape_`,
    `prefix_`, `suffix_`, `like_num`, `nbor()`, `children`, `lefts`, `rights`,
    `n_lefts`, `n_rights`, `subtree`, `left_edge`, `right_edge`, `ancestors`,
    `is_ancestor()`, `sent`; tokens compare equal (and hash) by document and
    index
  - `Span`: `root`, `sent`, `sents`, `ents`, `lemma_`, `text_with_ws`; spans
    compare equal by document, bounds and label
  - `Doc`: `noun_chunks` (from the UD relations), `char_span()`,
    `has_annotation()`, `to_json()` (spaCy's format), `to_conllu()`,
    `text_with_ws`, `lang_`
  - `Lima.pipe(texts)` and `Lima.lang`
* `doc.ents` is a tuple of `Span`s (was a one-shot iterator), and its spans are
  right: their `text` was empty or cut (the start was the 1-based `Token.i`),
  and an entity ending on the last token was dropped
* Slices with omitted or negative bounds work on `Doc` (`doc[:3]`, `doc[5:]`
  raised `TypeError`) and on `Span` (`span[1:]` dropped the last token);
  `doc[i]` and `span[i]` raise `IndexError` out of range (`span[len(span)]`
  returned the token after the span)
* `Token.doc`; `Token.is_sent_start` is right for every sentence (it was only
  True for the first token of the document)
* `Span.label_`, the same string as `Span.label` (spaCy's name for the label
  string; LIMA has no label hashes)
* `repr(token)` writes the features as CoNLL-U does (`Number=Sing`, was
  `Number:Sing`)
* `Token.i` is unchanged: it starts at 1 (spaCy's starts at 0)
* No more pydantic dependency; no more mutable default `meta` arguments; no
  more messages on stderr before raising exceptions
* Fixes in LIMA:
  - no more crash on a named entity followed by a multiword token
    (`Apple's CEO.` with the English MERGE model), and the words of a
    multiword token that spell it have their own positions (`'s` of `Apple's`
    at 5, was 0) (aymara/lima#229)
  - the dependency heads and relations of every analysis after the first one
    of an analyzer were wrong: those of earlier analyses were reused
    (aymara/lima#234)
  - the arcs whose relation was unknown to LIMA (73 UD 2.18 relations, such
    as `obl:unmarked`) were dropped (head 0, relation `_`) (aymara/lima#231)
  - the analysis of a text no longer depends on the texts analyzed before
    it, and short texts are analyzed much faster: 140 ms -> 24 ms for one
    sentence (aymara/lima#238)
  - less stderr noise when creating an analyzer (aymara/lima#233)

## 0.8.1 - 20261125

* Windows: creating a `Lima` analyzer no longer crashes the interpreter when the
  `HOME` environment variable is not set, as in a normal Windows console
  (LIMA, aymara/lima#227). Workaround with 0.8.0: set `HOME`, e.g.
  `$env:HOME = $env:USERPROFILE` in PowerShell
* macOS: the wheel no longer depends on the install names of the LIMA package
  it is built against

## 0.8.0 - 20261125

* Windows and macOS wheels, besides the two Linux ones:
  - Windows x64 (`win_amd64`), Qt 6.12, Python 3.10 to 3.13 tested; built
    against the native Windows build of LIMA (aymara/lima#219). The DLLs it
    bundles are renamed, so that it works in the same process as PyTorch
  - macOS on Apple Silicon (`macosx_15_0_arm64`, macOS >= 15), Qt 6.12,
    Python 3.10 to 3.13 tested (aymara/lima#221)
* `Lima.export_system_conf` (and `_get_data_dir`) use the directory LIMA reads
  and `lima_models` installs the models into (`$XDG_DATA_HOME/lima` or
  `~/.local/share/lima`) on all platforms
* Multiword tokens: a token the tokenizer flags as multiword but missing from
  the language's dictionary is split by affix rules learned from that
  dictionary (LIMA, aymara/lima#217): more correct words and dependencies in
  Amharic, Tamil, Marathi, Arabic, Polish... The rules are stored in the
  tokenizer's `.mwt` file, which the v0.3.0 models have without rules: they
  need a models release that includes them

* Memory: deleting a `Lima` instance frees its models (about 3 GB for a deepud
  analyzer) once no other instance uses its language, and creating a new
  instance of a language replaces the models of the previous one instead of
  adding to them (they were never freed). Needs the LIMA fix of
  `MediaProcessors` (initMedia releases the former process units; new
  `releaseMedia`). Memory is returned to glibc: the process RSS may stay high
  until it is reused or `malloc_trim` is called.

## 0.7.1 - 20261123

* Python 3.9 gets the manylinux_2_28 wheel again: 0.7.0 required Python >= 3.10
  on PyPI (the Requires-Python of its manylinux_2_34 wheel), so pip installed
  0.6.0 on Python 3.9

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
