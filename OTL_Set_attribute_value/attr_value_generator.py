# Load the Python Standard uuid Library
import uuid
import ctypes

lijst_ids = []
aantal_ids = IN[0]#Hoeveel IDs aan te maken
inputwaarde = IN[1]
propertynamelist = IN[2]
nl = "\n"

check = []#controleren of er zeker geen dubbels worden aangemaakt

if propertynamelist:
    propertyname = propertynamelist[0][0]
    
    for l in aantal_ids:
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
                
    psetnames = []
    for p in IN[0]:
        if p[0] not in psetnames:
            psetnames.append(p[0])
        
    
    if check:
        if inputwaarde == "random":
            message = f"Er werden {len(check)} waardes gegenereerd om in te vullen bij '{propertyname}' in de volgende propertysets: {nl}{nl.join(psetnames)}"
        else:
            message = f"De waarde: '{inputwaarde}' werd {len(check)} ingevuld bij '{propertyname}' in de volgende propertysets: {nl}{nl.join(psetnames)}"
    else:
        message = "GEEN objecten gevonden om attributen voor te wijzigen"

else: message = "GEEN objecten gevonden om attributen voor te wijzigen"

ctypes.windll.user32.MessageBoxW(0, message, "OTL_Bulk_update", 0)

OUT = lijst_ids