import aymara.lima

import gc
import sys
import threading

# try:
#     lima = aymara.lima.Lima("cym")
# except aymara.lima.LimaInternalError as e:
#     print(f"Catched expected LimaInternalError {e}", file=sys.stderr)

def f1():
    text = "Give it back! He pleaded."
    for _ in range(10):
        gc.collect()
        lima = aymara.lima.Lima("ud-eng")
        doc = lima(text)
        print(repr(doc))
# doc = lima("John Doe lives in New York. And Jane Smith will meet him on Friday.")
# print(f"after {repr(doc)}")
# ents = list(doc.ents)
# print("listed")
# assert len(ents) == 4


def f2():
    for _ in range(10):
        gc.collect()
        lima = aymara.lima.Lima("ud-wol")
        doc = lima("Wolof làkk la wu ñuy wax ci Gàmbi (Gàmbi Wolof), "
                "Gànnaar (Gànnaar Wolof), ak Senegaal (Senegaal Wolof).")
        print(repr(doc))


if __name__ == "__main__":
    t1 = threading.Thread(name="T1", target=f1)
    t2 = threading.Thread(name="T1", target=f2)
    t3 = threading.Thread(name="T3", target=f1)
    t4 = threading.Thread(name="T4", target=f2)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
