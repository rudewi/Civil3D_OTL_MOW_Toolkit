# Load the Python Standard and DesignScript Libraries
import re
from os import path
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
inputveld = IN[0]
hoofdingfilter = IN[1]
dwg_objecten_handles = IN[2]
dwg_objecten_ids = IN[3]
dwg_objecten_typeURIs = IN[4]
filepath_rapport = IN[5]

#Variabelen
message = ""
m = ctypes.windll.user32
nl = '\n'
objectenlijst = []
filecount = 0
filter_oke = 1
te_selecteren_handles = []
handlezoeker = 0
alle_OTL = 0
rapportlijst = []

#functies
def selectieopdracht(handles):
    """Selecteer en isoleer objecten obv een lijst van handles"""
    if handles:
        #bestaande selectie en isolate wegdoen en nieuwe selectie starten   
        dwgcommando = f"SELECT{nl}none{nl}UNISOLATE{nl}SELECT{nl}"
        #selecteer elke handle uit de lijst
        for h in handles:
            dwgcommando = f'{dwgcommando}(handent"{h}"){nl}'
        #isoleer de geselecteerde objecten
        dwgcommando = f"{dwgcommando}{nl}ISOLATE{nl}"
    
        #commando uitvoeren in dwgfile
        adoc = Application.DocumentManager.MdiActiveDocument
        with adoc.LockDocument():
            adoc.SendStringToExecute(dwgcommando, True, False, False)
        
    return len(handles)

def csv_schrijven(data,filepath):
    """CSV wegschrijven"""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(data)
        filename = filepath.split("\\")[-1]
        message = f"{(len(data)-1)} rijen geschreven in {filename}"    
    except Exception as e:
        message = f"Er is een fout opgetreden bij het schrijven naar het bestand: {e}"
    return message

#main
if dwg_objecten_handles:
    if inputveld:
        if hoofdingfilter == "assetType":
            message = "Objecten werden gezocht obv assetType"
            zoeklijst = dwg_objecten_typeURIs                    
        elif hoofdingfilter == "assetId.identificator":
            message = "Objecten werden gezocht obv assetId.identificator"
            zoeklijst = dwg_objecten_ids                 
        elif hoofdingfilter == "handle":
            message = "Objecten werden gezocht obv handle"
            zoeklijst = dwg_objecten_handles
            handlezoeker = 1
        elif hoofdingfilter == "OTL":
            message = "Alle Objecten met een OTL propertyset werden gezocht"
            alle_OTL = 1
        else:
            message = f"Geen correcte filter, je kan objecten zoeken op een van de volgende eigenschappen: {nl}assetType (typeURI){nl}assetId.identificator{nl}handle (de Autocad entity handle){nl}OTL (alle objecten met een OTL propertyset){nl}"
            zoeklijst = []
            filter_oke = 0
            
        if alle_OTL:
            objectenlijst = dwg_objecten_handles
            zoeklijst = dwg_objecten_handles
            
        elif inputveld.endswith(".csv"):
            filedir = inputveld
            try:
                with open(filedir, encoding='utf-8') as csvfile:
                    ingelezen_csv = csv.DictReader(csvfile, delimiter=";")
                    csv_dicts = (list(ingelezen_csv))
    
            except Exception as e:
                message = f"Kon CSV bestand niet openen: {nl}{str(inputveld)}{e}"
            
            if filter_oke:
                for d in csv_dicts:
                    if hoofdingfilter in d:#check of key bestaat
                        if d[hoofdingfilter]:#check of er een waarde is voor deze key
                            objectenlijst.append(d[hoofdingfilter])
                    else:
                        message = f"Kon de opgegeven attribuut: {hoofdingfilter} niet terugvinden als hoofding in de csv file"
                if len(objectenlijst) == 0:
                    message = f"Geen waarden gevonden voor het attribuut {hoofdingfilter} in de opgegeven csv"
                
        else:#indien er een waarde werd opgegeven ipv een csv
            objectenlijst = [inputveld]
            
        ongevonden_waardes = []
        for o in objectenlijst:
            if handlezoeker:#handles in caps omzetten
                o = o.upper()
                
            if zoeklijst:
                if o in zoeklijst:
                    #meerdere indices mogelijk, bv bij donut polygons    
                    indices = [i for i, x in enumerate(zoeklijst) if x == o]
                    for i in indices:
                        te_selecteren_handles.append(dwg_objecten_handles[i])
                        
                        r = {
                        "handle":dwg_objecten_handles[i],
                        "objectType":dwg_objecten_typeURIs[i],
                        "assetId.identificator":dwg_objecten_ids[i]
                        }
                        rapportlijst.append(r)
                        #rapport_dict maken en toevegen aan rapport dict lijst
                           
                else:
                    ongevonden_waardes.append(o)
                    
                if len(ongevonden_waardes) > 0:
                    message = f"Kon volgende {hoofdingfilter} waardes niet vinden in dwg file:{nl}{nl.join(ongevonden_waardes)}"
            
    else:
        message = f"Geen input: Voer een waarde of een csv file met waardes in"
    
    #selecteer de gevonden objecten
    if te_selecteren_handles:
        try:
            selectie = selectieopdracht(te_selecteren_handles)
            message = f"Er werden {selectie} objecten geselecteerd en geisoleerd.{nl}Open de dwg om het resultaat te bekijken.{nl}Gebruik het commando UNISOLATE om terug alle objecten te tonen.{nl}{nl}{message}"
        except:
            message = f"Selectieopdracht niet gelukt voor de gevonden handles:{nl}{nl.join(te_selecteren_handles)}"
    else:
        message = f"{message}{nl}{nl}GEEN selectie gemaakt, er werden geen objecten gevonden om te selecteren.{nl}"
    
    #raport wegschrijven
    if rapportlijst:#Check of er te raporteren data is
        try:
            data = [["handle","objectType","assetId.identificator"]]#hoofding
            for d in rapportlijst: #lijn per object
                data.append([d["handle"],d["objectType"],d["assetId.identificator"]])
                
            if path.isdir(filepath_rapport):
                filenaam = "OTL_Select_objects_result"
                filepath = filepath_rapport + "\\" + filenaam + ".csv"
                result = csv_schrijven(data,filepath)
                message = f"{message}{nl}{nl}CSV overzicht van selectie werd aangemaakt:{nl}{filepath}"
        except:
            message = f"{message}{nl}{nl}Geen CSV overzicht aangemaakt. Mogelijks heeft dynamo geen toegang tot de folder:{filepath_rapport}"
else:
    message = f"Kon OTL objecten in dwg niet correct inlezen"

#Bericht popup
if message:
    m.MessageBoxW(0, str(message), "OTL Select Objects", 0)


# OUT variable.
OUT = rapportlijst