# Load the Python Standard and DesignScript Libraries
import os.path
import ctypes
import sqlite3

# The inputs to this node will be stored as a list in the IN variables.
subset_db = IN[0]
subset_filter = IN[1]#filter op de attributen
objecten_filter = IN[2]#filter op de objecten of full OTL

# Main variables
nl = "\n"

# Functies
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
if objecten_filter:
    subsetpad, subsetmessage = check_subset_geldigheid(subset_db)
    go = True
    
    if subsetmessage:
        ctypes.windll.user32.MessageBoxW(0, subsetmessage, "OTL_propertysetdefinitions_aanmaken", 0)
        go = False

else:
    go = True
    subsetpad = ""
    no_objfilter_message = f"Geen filtering op subset objecten:{nl}Er worden propertyset definitions aangemaakt voor alle instantieerbare OTL objecten. Dit kan even duren"
    ctypes.windll.user32.MessageBoxW(0, no_objfilter_message, "OTL_propertysetdefinitions_aanmaken", 0)

# OUT variable
OUT = subsetpad,subset_filter,objecten_filter,go