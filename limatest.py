import aymara.lima
import sys

lima = aymara.lima.Lima()
doc = lima("I like to read books. And you, Jane Doe? I went to Paris last year.")
for token in doc:
    print(repr(token))
print(doc, file=sys.stderr)

