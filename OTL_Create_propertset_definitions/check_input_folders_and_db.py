# Load the Python Standard and DesignScript Libraries
import os.path
import ctypes
import sqlite3

from Autodesk.AutoCAD.ApplicationServices import *

# The inputs to this node will be stored as a list in the IN variables.
toolkit_update = IN[0]
inputpad = IN[1]
subset_db = IN[2]
subset_filter = IN[3]

# Main variables
nl = "\n"

# Functies
def downloadfolder_in_dwg_folder():
    """Haal de foldernaam van de huidge dwg file op"""
    try:
        adoc = Application.DocumentManager.MdiActiveDocument
        editor = adoc.Editor
        with adoc.LockDocument():
            with adoc.Database as db:
                dwg_filepath = db.OriginalFileName
                filepath = dwg_filepath.rsplit('\\',1)[0]#filenaam weglaten
        
        
        if filepath.endswith(r'enu\Template'):
            downloadfolder = "dwg templade folder"
        else:
            downloadfolder = filepath + r'\OTLmodelDownload'
            if not os.path.isdir(downloadfolder):
                os.mkdir(downloadfolder)
        
    except:
        downloadfolder = "ongeldig pad"
    
    return downloadfolder

def check_pad_geldigheid(pad):
    """kijkt of het pad naar een bruikbare folder wijst"""
    message = ""
    if isinstance(pad, str):
        if not os.path.isdir(pad):
            message = f"{pad}{nl}Kan NIET worden gebruikt om de OTLMOW libraries op te slaan:{nl}Geef een ander pad op aub"
            pad = "ongeldig_pad"
    else:
        message = f"{pad}{nl} kan NIET worden gebruikt om de OTLMOW libraries op te slaan:{nl}Geef het pad op aub"
        pad = "ongeldig_pad"

    return pad,message

def doelpad_opzoeken(user_input_path):
    """Zoekt het juiste pad om de OTLMOW library naar te downloaden en op te slaan"""
    if user_input_path and user_input_path != "null" and user_input_path != "":
        #Er werd een pad opgegeven door de user
        doelpad, foldermessage = check_pad_geldigheid(user_input_path)       
    else:
        doelpad, foldermessage = check_pad_geldigheid(downloadfolder_in_dwg_folder())
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
                #message = f"Geldige subset input:{nl}{db_pad}"
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

# Enkel bij probleem pop-up geven
if foldermessage and subsetmessage:
    endmessage = f"{foldermessage}{nl}{nl}{subsetmessage}"
elif foldermessage:
    endmessage = foldermessage
elif subsetmessage:
    endmessage = subsetmessage
else:
    endmessage = ""

if endmessage:
    ctypes.windll.user32.MessageBoxW(0, endmessage, "OTL_propertysetdefinitions_aanmaken", 0)

# OUT variable
OUT = doelpad,subsetpad,subset_filter,toolkit_update