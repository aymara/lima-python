import aymara.lima
import json

lima = aymara.lima.Lima("ud-eng", pipes="empty")

pipeline = {
    "tokenizer": {
        "name": "cpptftokenizer",
        "class": "CppUppsalaTensorFlowTokenizer",
        "model_prefix": "tokenizer-eng"
            },
    "morphosyntax": {
        "name": "tfmorphosyntax",
        "class": "TensorFlowMorphoSyntax",
        "model_prefix": "morphosyntax-eng",
        "embeddings": "fasttext-eng.bin"
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
