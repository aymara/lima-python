import aymara.lima
import sys

# try:
#     lima = aymara.lima.Lima("cym")
# except aymara.lima.LimaInternalError as e:
#     print(f"Catched expected LimaInternalError {e}", file=sys.stderr)

lima = aymara.lima.Lima("ud-eng")
text = "Give it back! He pleaded."
doc = lima(text)
print(f"after {repr(doc)}")
doc = lima("John Doe lives in New York. And Jane Smith will meet him on Friday.")
print(f"after {repr(doc)}")
ents = list(doc.ents)
print("listed")
assert len(ents) == 4
