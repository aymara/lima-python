import aymara.lima
import sys


lima = aymara.lima.Lima()
result = lima("This is a text on 02/05/2022.", lang="eng", pipeline="main")
for token in result:
    print(token.lemma)
print(result, file=sys.stderr)

