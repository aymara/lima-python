"""spaCy interoperability of aymara.lima (spaCy is an optional dependency:
``pip install aymara[spacy]``).

Two ways to use LIMA's analyses with spaCy's own objects and tools (displaCy,
Matcher, DocBin...):

- converting a LIMA document: ``lima_doc.to_spacy()`` (or ``doc_to_spacy``);
- a spaCy pipeline whose tokenizer is a LIMA analyzer, as spacy-stanza and
  spacy-udpipe do::

    import aymara.lima_spacy
    nlp = aymara.lima_spacy.spacy_pipeline("ud-eng")
    doc = nlp("Mr. Best flew to New York.")   # a spacy.tokens.Doc
    [(t.text, t.lemma_, t.pos_, t.dep_, t.head.text) for t in doc]

  It can also be built from a spaCy config: the tokenizer is registered as
  ``aymara.LimaTokenizer.v1``::

    [nlp.tokenizer]
    @tokenizers = "aymara.LimaTokenizer.v1"
    lang = "ud-eng"

Differences with spaCy's own pipelines:

- The tokens are LIMA's (UD) words. The words of a multiword token that do
  not spell it (French "du" -> "de" "le") are separate tokens, so that the
  spaCy document text is "de le" where the original text has "du" (the
  original text is in ``doc.user_data["lima_text"]``). The words that spell
  it (English "Apple's" -> "Apple" "'s") keep the original text.
- Dependency relations are UD ones: the root's is "root" (spaCy's English
  models use "ROOT").
- Entity labels are LIMA's, e.g. "Person.PERSON", "Location.CITY".
- ``tag_`` is empty: the deeplima models predict no language specific tag.
"""

# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, Optional

import spacy
from spacy.symbols import IDS as _SPACY_IDS
from spacy.tokens import Doc as SpacyDoc
from spacy.util import registry
from spacy.vocab import Vocab

import aymara.lima

_UPOS = {"ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART",
         "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"}

# ISO 639-3 (LIMA's UD media "ud-<code>") -> spaCy's language codes (mostly ISO
# 639-1); a language spaCy does not know uses its multi-language class "xx"
_ISO639_3_TO_1 = {
    "afr": "af", "amh": "am", "ara": "ar", "bel": "be", "ben": "bn", "bul": "bg",
    "cat": "ca", "ces": "cs", "cym": "cy", "dan": "da", "deu": "de", "ell": "el",
    "eng": "en", "est": "et", "ekk": "et", "eus": "eu", "fao": "fo", "fas": "fa",
    "fin": "fi", "fra": "fr", "gle": "ga", "gla": "gd", "glg": "gl", "guj": "gu",
    "heb": "he", "hin": "hi", "hrv": "hr", "hun": "hu", "hye": "hy", "ind": "id",
    "isl": "is", "ita": "it", "jpn": "ja", "kan": "kn", "kat": "ka", "kaz": "kk",
    "kir": "ky", "kor": "ko", "lat": "la", "lav": "lv", "lit": "lt", "ltz": "lb",
    "mal": "ml", "mar": "mr", "mkd": "mk", "mlt": "mt", "nep": "ne", "nld": "nl",
    "nor": "nb", "nob": "nb", "nno": "nn", "pol": "pl", "por": "pt", "ron": "ro",
    "rus": "ru", "san": "sa", "sin": "si", "slk": "sk", "slv": "sl", "spa": "es",
    "sqi": "sq", "srp": "sr", "swe": "sv", "tam": "ta", "tat": "tt", "tel": "te",
    "tgl": "tl", "tha": "th", "tir": "ti", "tsn": "tn", "tur": "tr", "ukr": "uk",
    "urd": "ur", "vie": "vi", "yor": "yo", "zho": "zh",
}


def spacy_lang(lang: str) -> str:
    """The spaCy language code of the LIMA language lang ("ud-eng" -> "en"),
    "xx" (multi-language) if spaCy has no class for it."""
    code = lang[3:] if lang.startswith("ud-") else lang
    for candidate in (_ISO639_3_TO_1.get(code), code):
        if not candidate:
            continue
        try:
            spacy.util.get_lang_class(candidate)
            return candidate
        except ImportError:
            continue
    return "xx"


def _words_and_spaces(doc: "aymara.lima.Doc"):
    """The words of the LIMA document and whether a space follows each one (the
    non-final words of a multiword token sharing its position are separated by
    spaces: "de le")."""
    words, spaces = [], []
    n = len(doc)
    for k in range(n):
        token = doc[k]
        words.append(token.text)
        if k + 1 < n and doc[k + 1].idx == token.idx:
            spaces.append(True)    # "de" of "du": "de le"
        else:
            spaces.append(bool(token.whitespace_))
    return words, spaces


def doc_to_spacy(doc: "aymara.lima.Doc", vocab: Optional[Vocab] = None) -> SpacyDoc:
    """Converts the LIMA document doc into a spaCy Doc, with its words, lemmas,
    universal parts of speech, morphological features, dependency tree, sentence
    boundaries and named entities.

    :param doc: the LIMA document
    :param vocab: the spaCy vocabulary to use (default: a blank pipeline's of the
        document's language)
    """
    if vocab is None:
        vocab = spacy.blank(spacy_lang(doc.lang_ or "")).vocab
    words, spaces = _words_and_spaces(doc)
    tokens = [doc[k] for k in range(len(doc))]
    heads = [t.head_i for t in tokens]
    deps = [t.dep_ if t.dep_ not in ("", "_") else "dep" for t in tokens]
    # A token without relation is its own head: spaCy would make it a sentence
    # of its own. It is attached to its sentence's root, with dep "dep"
    sent_of = {}
    for sent in doc.sents:
        root = next((t.token.i for t in sent if t.dep_ == "root"), sent.start)
        for k in range(sent.start, sent.end):
            sent_of[k] = (sent.start, root)
    for k, t in enumerate(tokens):
        if t.dep_ in ("", "_") and k in sent_of and sent_of[k][1] != k:
            heads[k] = sent_of[k][1]
    starts = {start for start, _ in sent_of.values()}
    sent_starts = [k in starts for k in range(len(tokens))]
    ents = []
    previous = "O"
    for t in tokens:
        if t.ent_iob_ in ("B", "I") and t.ent_type_:
            iob = "I" if (t.ent_iob_ == "I" and previous == t.ent_type_) else "B"
            ents.append(f"{iob}-{t.ent_type_}")
            previous = t.ent_type_
        else:
            ents.append("O")
            previous = "O"
    sdoc = SpacyDoc(vocab, words=words, spaces=spaces, heads=heads, deps=deps,
                    sent_starts=sent_starts, ents=ents)
    for st, t in zip(sdoc, tokens):
        if t.lemma_ and t.lemma_ != "_":
            st.lemma_ = t.lemma_
        if t.pos_ in _UPOS and t.pos_ in _SPACY_IDS:
            st.pos_ = t.pos_
        morph = str(t.morph)
        if morph:
            st.set_morph(morph)
    if sdoc.text != doc.text:
        sdoc.user_data["lima_text"] = doc.text
    return sdoc


class LimaTokenizer:
    """A spaCy tokenizer running a LIMA analyzer: it gives spaCy documents with
    all of LIMA's annotations (see doc_to_spacy)."""

    def __init__(self, vocab: Vocab, lang: str = "ud-eng", pipes: str = "deepud",
                 meta: Optional[Dict[str, str]] = None,
                 lima: Optional["aymara.lima.Lima"] = None):
        self.vocab = vocab
        self.lima = lima if lima is not None else aymara.lima.Lima(lang, pipes, meta=meta)

    def __call__(self, text: str) -> SpacyDoc:
        return doc_to_spacy(self.lima(text), self.vocab)

    def pipe(self, texts, batch_size: int = 1000):
        for text in texts:
            yield self(text)

    # The analyzer is not serializable: a saved pipeline gets a new one from its
    # config when loaded
    def to_bytes(self, **kwargs) -> bytes:
        return b""

    def from_bytes(self, _bytes_data: bytes, **kwargs) -> "LimaTokenizer":
        return self

    def to_disk(self, _path, **kwargs) -> None:
        return None

    def from_disk(self, _path, **kwargs) -> "LimaTokenizer":
        return self


@registry.tokenizers("aymara.LimaTokenizer.v1")
def create_tokenizer(lang: str = "ud-eng", pipes: str = "deepud",
                     meta: Optional[Dict[str, str]] = None
                     ) -> Callable[["spacy.language.Language"], LimaTokenizer]:
    """The factory of LimaTokenizer for spaCy configs."""
    def tokenizer_factory(nlp) -> LimaTokenizer:
        return LimaTokenizer(nlp.vocab, lang=lang, pipes=pipes, meta=meta)
    return tokenizer_factory


def spacy_pipeline(lang: str = "ud-eng", pipes: str = "deepud",
                   meta: Optional[Dict[str, str]] = None,
                   lima: Optional["aymara.lima.Lima"] = None) -> "spacy.language.Language":
    """A blank spaCy pipeline of the language lang whose tokenizer is a LIMA
    analyzer (lima, or a new one for lang, pipes and meta): nlp(text) gives a
    spaCy Doc with LIMA's annotations, and spaCy components can be added after
    it (nlp.add_pipe).

    :param lang: the LIMA language, e.g. "ud-eng"
    :param pipes: the LIMA pipeline (default "deepud")
    :param meta: LIMA analysis metadata, e.g. {"udlang": "eng-UD_English-EWT"}
    :param lima: an existing analyzer to use instead of creating one
    """
    if lima is not None:
        lang = lima.lang
    nlp = spacy.blank(spacy_lang(lang))
    nlp.tokenizer = LimaTokenizer(nlp.vocab, lang=lang, pipes=pipes, meta=meta, lima=lima)
    return nlp
