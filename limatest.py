import aymara.lima
import sys

lima = aymara.lima.Lima("ud-eng", pipes="deepud")
# doc = lima("The cat eats the mouse. He likes it.")
# doc = lima("Give it back! He pleaded.")
# lima = aymara.lima.Lima("eng", pipes="main")
doc = lima("John Doe lives in New York. And Jane Smith will meet him on Friday.")
print(repr(doc))
token = doc[5]
# print(repr(token), file=sys.stderr)
# assert repr(token) == '5\tpleaded\tplead\tVERB\t_\tMood:Ind|Tense:Past|VerbForm:Fin\t_\troot\t_\tPos=17|Len=7'
# assert str(token) == "pleaded" == token.text
# assert len(token) == 7
# assert token.i == 5
# assert token.idx == 17
# assert token.ent_iob == "O"
# assert token.ent_type == "_"
# assert token.lemma == "plead"
# assert token.pos == "VERB"
# assert token.head == 0
# assert token.dep == "root"
# assert token.features == {'Mood': 'Ind', 'Tense': 'Past', 'VerbForm': 'Fin'}
# assert token.t_status == 't_small'
# assert token.is_alpha is True
# assert token.is_digit is False
# assert token.is_lower is True
# assert token.is_upper is False
# assert token.is_punct is False
# assert token.is_sent_start is False
# assert token.is_sent_end is False
# assert token.is_space is False
# assert token.is_bracket is False
# assert token.is_quote is False
