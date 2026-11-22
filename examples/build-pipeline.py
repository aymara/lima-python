import aymara.lima
import json

# The deeplima models are selected by the udlang metadata (here the English
# default model, installed by "lima_models -i eng")
lima = aymara.lima.Lima("ud-eng", pipes="empty",
                        meta={"udlang": "eng-UD_English-MERGE"})

pipeline = {
    "tokenizer": {
        "name": "rnntokenizer",
        "class": "RnnTokenizer",
        "model_prefix": "tokenizer-$udlang"
            },
    "morphosyntax": {
        "name": "rnntokensanalyzer",
        "class": "RnnTokensAnalyzer",
        "tagger_model_prefix": "tagger-$udlang",
        "lemmatizer_model_prefix": "lemmatizer-$udlang"
            },
    "dumper": {
        "name": "conllDumper",
        "class": "ConllDumper",
        "handler": "simpleStreamHandler",
        "fakeDependencyGraph": "false"
            }
    }

lima.add_pipeline_unit("empty", "ud-eng",
                       json.dumps(pipeline["tokenizer"]))
lima.add_pipeline_unit("empty", "ud-eng",
                       json.dumps(pipeline["morphosyntax"]))
lima.add_pipeline_unit("empty", "ud-eng",
                       json.dumps(pipeline["dumper"]))

text = "Give it back! He pleaded."
doc = lima(text)

print(repr(doc))
