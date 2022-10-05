import aymara.lima
import sys

lima = aymara.lima.Lima("ud-eng", pipes="deepud")
doc = lima("Give it back! He pleaded.")
span = doc[1:4]
assert span[1:3].text == "back!"

#lima = aymara.lima.Lima("ud-eng")
#doc = lima("I like to read books. And you, Jane Doe? I went to Paris last year.")
#for token in doc:
#    print(repr(token))
#print(doc, file=sys.stderr)

