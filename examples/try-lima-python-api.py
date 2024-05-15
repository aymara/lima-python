import aymara.lima
import json

lima = aymara.lima.Lima("ud-eng", pipes="deepud")

text = "Give it back! He pleaded."
doc = lima(text)

print(f"Type of a document: {type(doc)}")
print(f"Lemma of the first word: {doc[0].lemma}")
print(f"CoNLL-U representation of the document:\n{repr(doc)}")
