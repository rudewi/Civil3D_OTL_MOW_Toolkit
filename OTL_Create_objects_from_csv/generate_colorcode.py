import random

objectenlijst = IN[0]

kleurenlijst = []
for o in objectenlijst:
    donutlijst = []
    kleurcode = {'r':random.randint(1, 249),'g':random.randint(1, 249),'b':random.randint(1, 249)}

    for d in o:
        donutlijst.append(kleurcode)
    kleurenlijst.append(donutlijst)

OUT = kleurenlijst