# Load the Python Standard and DesignScript Libraries
import re
import os
import csv
import ctypes
import clr
import random

# Add Assemblies for AutoCAD and Civil3D
clr.AddReference('AcMgd')
clr.AddReference('AcCoreMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AecBaseMgd')
clr.AddReference('AecPropDataMgd')
clr.AddReference('AeccDbMgd')

# Import references from AutoCAD
from Autodesk.AutoCAD.Runtime import *
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.EditorInput import *
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.AutoCAD.Geometry import *
from Autodesk.AutoCAD.Colors import *

# Import references from Civil3D
from Autodesk.Civil.ApplicationServices import *
from Autodesk.Civil.DatabaseServices import *

# Import references for PropertySets
from Autodesk.Aec.PropertyData import *
from Autodesk.Aec.PropertyData.DatabaseServices import *

# Import references for ListDefinitions
from Autodesk.Aec.DatabaseServices import ListDefinition, ListItem, DictionaryListDefinition

adoc = Application.DocumentManager.MdiActiveDocument
editor = adoc.Editor

#INPUT
CSVMap = IN[0]

foutgevonden = 0
message = ""
m = ctypes.windll.user32
nl = '\n'

#coomsg = "Kijk aub na of je dwg hetzelfde coordinatenstelsel gebruikt als de WKTs in de CSV"
#m.MessageBoxW(0, coomsg , "OTL objecten uit CSV omzetting", 0)



def getCoo(wktstring):
    nums = re.findall(r'\d+(?:\.\d*)?', wktstring)
    coords = zip(*[iter(nums)] * 3)
    #strings uit tuple omzetten naar getallen in lijst
    coord_numbers = [] 
    for c in coords:
        x = float(c[0])
        y = float(c[1])
        z = float(c[2])
        coord_numbers.append([x,y,z])
    return list(coord_numbers)

def psetnaam(typeURI):
    """Maakt de unieke propertysetnaam voor een object"""
    objectsoort = typeURI.split('/')[-1].split('#')[0] #objectsoort afleiden uit typeURI
    objectnaam = typeURI.split('#')[1]
    propertysetnaam = "OTL_" + objectnaam
    return propertysetnaam
    
#DICTS maken uit CSVs
csv_dicts = []
filecount = 0

if CSVMap:
    for root, dirs, files in os.walk(CSVMap):
        for file in files:
            if file.endswith(".csv"):
                filecount = filecount + 1
                filedir= CSVMap + "\\" + file
                with open(filedir, encoding='utf-8') as csvfile:
                    ingelezen_csv = csv.DictReader(csvfile, delimiter=";")
                    csv_dicts.append(list(ingelezen_csv))
    if filecount == 0:
        foutgevonden = 1
        if message == "":
            message = f"Kon geen CSV bestanden vinden in de folder: {nl}{str(CSVMap)}"
else:
    foutgevonden = 1
    if message == "":
        message = f"Ongeldige input folder: {nl}{str(CSVMap)}"


#Lege items skippen
lijstdictszonderlege = []
lijstdictszondergeom = []
OTLobjecten = 0
legacyobjecten = 0

for l in csv_dicts:
    for dict_a in l:
        #trailing .0 fix
        for sleutel, waarde in dict_a.items():
            if waarde.endswith(".0"):
                dict_a[sleutel] = waarde[:-2]        
    
        #enkel attributen met ingevulde waarde behouden in nieuwe dict
        res = {k: v for k, v in dict_a.items() if v}
        if "typeURI" in res:
            if ("//lgc.data") in res["typeURI"]: #check op legacy objecten
                legacyobjecten = legacyobjecten + 1
            else:            
                if "assetId.identificator" in res:
                    if "geometry" in res:
                        OTLobjecten = OTLobjecten + 1
                        lijstdictszonderlege.append(res) #enkel de objecten met een geometrie attribuut toevoegen aan resultaatlijst
                    else:
                        lijstdictszondergeom.append(res)

if OTLobjecten == 0:
    foutgevonden = 1
    if message == "":
        message = f"GEEN objecten aangemaakt in dwg: Kon geen OTL objecten met geometrie vinden in de CSV bestanden in de folder: {nl}{str(CSVMap)}"                        

if OTLobjecten > 2000:
    veelobjectenmsg = "Er worden meer dan 2000 objecten verwerkt, dit kan even tijd in beslag nemen.."
    m.MessageBoxW(0, str(veelobjectenmsg), "OTL objecten uit CSV omzetting", 0)

if legacyobjecten > 0:
    lgcmsg = "Enkel OTL objecten kunnen verwerkt worden, De legacy objecten uit de CSVs worden GENEGEERD. Aantal legacy objecten: " + str(legacyobjecten)
    m.MessageBoxW(0, str(lgcmsg), "OTL objecten uit CSV omzetting", 0)
    
if lijstdictszondergeom:
    nogeomtypes = set([psetnaam(d['typeURI']) for d in lijstdictszondergeom])
    nogeommsg = f"De OTL objecten ZONDER geometrie (zoals oa relaties) worden GENEGEERD. Aantal objecten zonder geometrie: {len(lijstdictszondergeom)} {nl}Van volgende types:{nl}{nl}{nl.join(nogeomtypes)}"
    m.MessageBoxW(0, str(nogeommsg), "OTL objecten uit CSV omzetting", 0)
    
ongevonden_psets = []
puntobjecten = []
lijnobjecten = []
single_polygoonobjecten = []
donut_polygoonobjecten = []

#PROPERTSET DEFINITIONS CHECKEN
with adoc.LockDocument():
    with adoc.Database as db:
        with db.TransactionManager.StartTransaction() as t:
            dpsd = DictionaryPropertySetDefinitions(db)
            for dict_y in lijstdictszonderlege:
                #controle of propertysetnaam  bestaat in de huidige dwg
                propertysetnaam = psetnaam(dict_y['typeURI'])   
                if not dpsd.Has(propertysetnaam, t): #propertysetnaam bestaat nog niet
                    if propertysetnaam not in ongevonden_psets: #maar 1 keer toevoegen
                        ongevonden_psets.append(propertysetnaam)


# LAYERS AANMAKEN
with adoc.LockDocument():
    with adoc.Database as db:
        with db.TransactionManager.StartTransaction() as t:
            layertable = t.GetObject(db.LayerTableId,OpenMode.ForRead)
            for dict_y in lijstdictszonderlege:
                layernaam = psetnaam(dict_y['typeURI']) #de naam van de layer afleiden uit typeURI
                if not layertable.Has(layernaam):
                    newlayer = LayerTableRecord()
                    newlayer.Name = layernaam
                    newlayer.Color = Color.FromColorIndex(ColorMethod.ByAci, random.randint(1, 249))
                    layertable = t.GetObject(db.LayerTableId,OpenMode.ForWrite)
                    layertable.Add(newlayer)
                    t.AddNewlyCreatedDBObject(newlayer, True)
            t.Commit()


if len(ongevonden_psets) == 0: #bij alles gevonden
    if message == "":
        gevonden_types = set([psetnaam(d['typeURI']) for d in lijstdictszonderlege])
        message = f"De nodige OTL Propertysetdefinitions werden gevonden in de dwg:{nl}{nl}{nl.join(gevonden_types)}"
    for dict_b in lijstdictszonderlege:
    #opsplitsing maken per mogelijk geotype
        dict_b["psetnaam"] = psetnaam(dict_b['typeURI']) #psetnaam toevoegen
        if dict_b['geometry'].startswith("POINT Z"):
            dict_b["coordinates"] = getCoo(dict_b['geometry'])
            puntobjecten.append(dict_b)
        elif dict_b['geometry'].startswith("LINESTRING Z"):
            dict_b["coordinates"] = getCoo(dict_b['geometry'])
            lijnobjecten.append(dict_b)
        elif dict_b['geometry'].startswith("POLYGON Z"):
            donutsplit = dict_b['geometry'].split('),(')
            if len(donutsplit) == 1:
                dict_b["coordinates"] = getCoo(dict_b['geometry'])
                single_polygoonobjecten.append(dict_b)
            else:
                donutcoolist = []
                for polygon in donutsplit:
                    donutcoolist.append(getCoo(polygon))
                dict_b["coordinates"] = donutcoolist
                donut_polygoonobjecten.append(dict_b)
else:
   foutgevonden = 1
   if message == "":
        message = f"Kon objecten niet aanmaken omdat de nodige propertysetdefinitie niet bestaat in de dwg. Voeg volgende propertysetdefinities toe: {nl}{nl}{nl.join(ongevonden_psets)}"   



m.MessageBoxW(0, str(message), "OTL objecten uit CSV omzetting", 0)

# OUT variable.

if foutgevonden == 1:
    OUT = [[],[],[],[]]
else:   
    OUT = [puntobjecten,lijnobjecten,single_polygoonobjecten,donut_polygoonobjecten]
    
