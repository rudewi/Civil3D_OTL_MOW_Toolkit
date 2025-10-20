# Load the Python Standard and DesignScript Libraries
import sys
import os.path
from System.Reflection import Assembly
import xml.etree.ElementTree as et
import ctypes
import sqlite3

# The inputs to this node will be stored as a list in the IN variables.
toolkit_update = IN[0]
inputpad = IN[1]
subset_db = IN[2]
subset_filter = IN[3]

# Main variables
nl = "\n"

# Functies
def check_pad_geldigheid(pad):
    """kijkt of het pad naar een bruikbare folder wijst"""
    
    message = ""

    if isinstance(pad, str):
        if os.path.isdir(pad):
            message = f"{pad}{nl}Zal worden gebruikt om de OTLMOW libraries op te slaan"
        else:
            message = f"{pad}{nl}Kan NIET worden gebruikt om de OTLMOW libraries op te slaan:{nl}Folder bestaat niet"
            pad = "ongeldig_pad"
    else:
        message = f"{pad}{nl} kan NIET worden gebruikt om de OTLMOW libraries op te slaan:{nl}Geef het pad op als tekstwaarde"
        pad = "ongeldig_pad"

    return pad,message

def packagefolderfinder():
    """Zoekt de folder waar het package is opgeslagen"""
    
    folderstring_na_version = r'\packages\OTL_MOW_Toolkit\extra' #einde van het pad
    message = ""

    try:    
        appDataPath = os.getenv('APPDATA') #de appdata locatie
        dynamo = Assembly.Load('DynamoCore')
        civil_version = str(dynamo.CodeBase).split("AutoCAD", 1)[1][1:5] #Civil versie opzoeken adhv locatie van dyn assembly
        dynamo_version = ".".join(str(dynamo.GetName().Version).split(".", 2)[:2]) #dynamo versie ophalen
        found_dynpath = appDataPath + r'\Autodesk\C3D ' + civil_version + r'\Dynamo' + '\\' + dynamo_version
        
        if os.path.isdir(found_dynpath):
            #Open de dynamo settings XML en bekijk de folders waar packages zijn opgeslagen:
            pad = found_dynpath + r'\packages' #voor wanneer OTL_MOW_Toolkit package folder niet bestaat
            root = et.parse(found_dynpath + "\DynamoSettings.xml").getroot()
            for child in root:
                if child.tag == "CustomPackageFolders":
                    for path in child:
                        path_packages = path.text + folderstring_na_version
                        if os.path.isdir(path_packages):
                            pad = path_packages
    
            message = f"{pad}{nl} zal worden gebruikt om de OTLMOW libraries op te slaan"
        
        else:
            pad = "ongeldig_pad"
            message = f"Het gezochte package pad:{nl}{pad}{nl}kan NIET worden gebruikt om de OTLMOW libraries op te slaan. Gelieve een ander pad te kiezen"
    
    except Exception as e:
        pad = "ongeldig_pad"
        message = f"Het gezochte package pad:{nl}{pad}{nl}kan NIET worden gebruikt om de OTLMOW libraries op te slaan.{nl}{e}{nl} Gelieve een ander pad te kiezen"

    return pad,message

def doelpad_opzoeken(user_input_path):
    """Zoekt het juiste pad om de OTLMOW library naar te downloaden en op te slaan"""
    if user_input_path and user_input_path != "null" and user_input_path != "":
        #Er werd een pad opgegeven door de user
        doelpad, foldermessage = check_pad_geldigheid(user_input_path)       
    else:
        doelpad, foldermessage = packagefolderfinder()
    return doelpad,foldermessage

def create_connection(db_file):
    """ maak connectie naar de SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

def select_klasses(conn):
    """klasses uit sqlite ophalen"""
    conn = create_connection(conn)
    klasses_in_subset = []
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OSLOClass';")
        bestaat_klassetabel = cur.fetchall()
        if bestaat_klassetabel:
            cur.execute("SELECT uri FROM OSLOClass WHERE abstract = '0';")
            klasses_in_subset = cur.fetchall()
            klasses_in_subset = klasses_in_subset[0]
    return klasses_in_subset

def check_subset_geldigheid(db_pad):
    """Kijkt na of de input een geldige OTL db is"""
    geldige_db_pad = ""
    message = ""
    if isinstance(db_pad, str):
        if os.path.exists(db_pad) and db_pad:
            extensie = db_pad.split(".")[-1]
            if extensie == "db":
                geldige_db_pad = db_pad
                message = f"Geldige subset input:{nl}{db_pad}"
            else:
                message = f"ONGELDIGE subset input: Bestand is geen .db bestand:{nl}{db_pad}"
        else:
            message = f"ONGELDIGE subset input: bestand is geen geldige subset gevonden:{nl}{db_pad}"
    else:
        message = f"ONGELDIGE subset input: bestand kon niet worden gevonden:{nl}{db_pad}"

    if geldige_db_pad:
        onderdelen = select_klasses(geldige_db_pad)
        if len(onderdelen) == 0:
            message = f"ONGELDIGE subset input: Geen OTL klassen gevonden in db file:{nl}{db_pad}"
            geldige_db_pad = ""

    return geldige_db_pad,message


# MAIN
doelpad, foldermessage = doelpad_opzoeken(inputpad)
subsetpad, subsetmessage = check_subset_geldigheid(subset_db)

endmessage = f"{foldermessage}{nl}{nl}{subsetmessage}"
ctypes.windll.user32.MessageBoxW(0, endmessage, "OTL_propertysetdefinitions_aanmaken", 0)

# OUT variable
OUT = doelpad,subsetpad,subset_filter,toolkit_update