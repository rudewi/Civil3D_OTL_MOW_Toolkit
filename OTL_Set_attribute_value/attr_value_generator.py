# Load the Python Standard uuid Library
import uuid
import ctypes

lijst_ids = []
all_OTL_propsetnames = IN[0]#Hoeveel IDs aan te maken
inputwaarde = IN[1]
propertynamelist = IN[2]
propertyvaluelist = IN[3]
tezoekenvalue = IN[4]
nl = "\n"

check = []#controleren of er zeker geen dubbels worden aangemaakt
aantalwaarden = 0
propertyname = ""#Een dummy voor wanneer niks gevonden

if propertynamelist:
    psetnames = []
    i = -1
    for n in propertynamelist:
        i = i + 1
        if n[0] != "null":#de property bestaat in de pset
            if propertyvaluelist[i][0] == tezoekenvalue:
                    aantalwaarden = aantalwaarden + 1
                    propertyname = n[0]#pas toekennen wanneer gevonden
                    psetname = all_OTL_propsetnames[i][0]
                    #ctypes.windll.user32.MessageBoxW(0, f"index:{i}{nl}properyname:{n[0]}{nl}psetname:{psetname}", "OTL_Bulk_update", 0)
                    if psetname not in psetnames:
                        psetnames.append(psetname)
    
    for l in all_OTL_propsetnames:
        sublist = []
        for i in l:
            if inputwaarde == "random":
                id = "gen_"+str(uuid.uuid4()).split("-")[0]
                if id not in check:
                     sublist.append(id)
                     check.append(id)
                else:
                    id = id[-1]+"a"
                    sublist.append(id)
                    check.append(id)
                lijst_ids.append(sublist)
            else:#bij niet random waarde
                sublist.append(inputwaarde)
                lijst_ids.append(sublist)
                check.append(inputwaarde)
                
        
    
    if check:
        if inputwaarde == "random":
            message = f"Er werden {aantalwaarden} waardes gegenereerd om in te vullen bij '{propertyname}' in de plaats van '{tezoekenvalue}' in de volgende propertysets: {nl}{nl}{nl.join(psetnames)}"
        else:
            message = f"De waarde: '{inputwaarde}' werd {aantalwaarden} keer herhaald om in te vullen in de plaats van '{tezoekenvalue} bij '{propertyname}' in de volgende propertysets: {nl}{nl}{nl.join(psetnames)}"
    else:
        message = "GEEN objecten gevonden om attributen voor te wijzigen"

else:
    message = "GEEN objecten gevonden om attributen voor te wijzigen"

ctypes.windll.user32.MessageBoxW(0, message, "OTL_Bulk_update", 0)

OUT = lijst_ids