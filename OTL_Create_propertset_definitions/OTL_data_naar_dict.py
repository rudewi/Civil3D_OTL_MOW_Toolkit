import sqlite3
from sqlite3 import Error
from os.path import exists
import ctypes
import json
import urllib.request
import ssl

# Main variables
nl = "\n"

#FUNCTIES
def create_connection(db_file):
        """ maak connectie naar de SQLite database"""
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            ctypes.windll.user32.MessageBoxW(0, str(e), "SQlite lezen gefaald", 0)
        return conn
    
    
def select_klasses(conn):
    """klasses uit sqlite ophalen"""
    conn = create_connection(conn)
    try:
        with conn:
            cur = conn.cursor()
            #klassen selecteren en daarbij abstracten, agents,bijlagen en relaties weglaten
            cur.execute("""
                SELECT k.uri FROM OSLOClass k 
                    WHERE abstract = '0' 
                    AND name NOT LIKE 'Agent' 
                    AND name NOT LIKE 'Bijlage' 
                    AND uri NOT LIKE 'https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#%'
                    AND k.uri NOT IN (
                    SELECT DISTINCT uri
                    FROM OSLORelaties
                    );""")
            klasses_onderdelen_tuple = cur.fetchall()
            klasses_onderdelen = []
            for k in klasses_onderdelen_tuple:
                klasses_onderdelen.append(k[0])

            if len(klasses_onderdelen) > 100:
                ctypes.windll.user32.MessageBoxW(0, "Verwerking van meer dan 100 OTL types, dit kan enkele minuten duren..", "Inlezen OTL SQLite", 0)
    finally:
        if conn:
            conn.close()    
    return(klasses_onderdelen)

def select_attributen(conn, klasse_uri):
    """attributen voor klasse uit SQlite halen"""
    conn = create_connection(conn)
    try:
        with conn:
            cur = conn.cursor()
            #attributen voor bepaalde klasse ophalen
            cur.execute("""
                        SELECT a.name FROM OSLOAttributen a
                        WHERE class_uri = ?
                        """, (klasse_uri,))
            attributen_tuple = cur.fetchall()
            attributen = []
            for attr in attributen_tuple:
                attributen.append(attr[0])
    finally:
        if conn:
            conn.close()

    return(attributen)


def dummydict():
    onderdeeldict = {} #een dict om alle info voor een bepaalde propertyset in te verzamelen
    
    onderdeeldict["propertysetnaam"] = "OTL_dummy"
    onderdeeldict["definitie"] = "Een dummy object"
    onderdeeldict["typeURI"] = "dummyURI"
    onderdeeldict["attributen"] = []
    
    attribuutdict = {} # een dict per dotnotatie-attribuut
    
    attribuutdict["dotnotatie_attribuutnaam"] = "dummy.attribuut"
    attribuutdict["attribuutdefinitie"] = "Een dummy attribuut"
    attribuutdict["datatype_attribuut"] = 'keuzelijst'
    attribuutdict["default_value"] = '-'
    attribuutdict["keuzelijstopties"] = ['dummywaarde-A','dummywaarde-B','-']
    attribuutdict["keuzelijstnaam"] = 'dummy-lijst'
    
    onderdeeldict["attributen"].append(attribuutdict) #Voeg de attribuutinfo toe aan de dict voor dit onderdeel
    return onderdeeldict



def create_psetnaam(obj, urilijst):
    """Maakt de unieke propertysetnaam voor een object"""

    #Naam en soort van de klasse
    objectnaam = obj.__class__.__name__
    objectsoort = obj.typeURI.split('/')[-1].split('#')[0] #objectsoort afleiden uit typeURI

    #Deprecation label toevoegen
    if hasattr(obj, 'deprecated_version'):
        depr = "_DEPR-" + str(obj.deprecated_version)
    else:
        depr = ""

    #Controle of naam reeds voorkomt
    if sum(s.endswith('#' + objectnaam) for s in urilijst) == 1:
        propertysetnaam = "OTL_" + objectnaam + depr
    else: 
        propertysetnaam = "OTL_" + objectnaam + "_" + objectsoort + depr 

    return propertysetnaam



def OTL_info_json_afladen():
    """Laadt de json met OTL info (dotnotatie, datatypes, defaultvalues, keuzelijsten, ...) van github"""

    # De link naar het JSON bestand (met https:// toegevoegd)
    url = "https://raw.githubusercontent.com/rudewi/OTL_DotnotationMaker/refs/heads/main/OTL_Dotnotation_all_objects.json"

    # Bypass voor SSL-certificaat fouten (een veelvoorkomend probleem in Dynamo/Revit)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Haal de ruwe data op van de URL
        response = urllib.request.urlopen(url, context=ctx, timeout=30)
        ruwe_data = response.read().decode('utf-8')
        
        # Zet de ruwe tekst om naar een bruikbaar Python dictionary (JSON)
        json_data = json.loads(ruwe_data)


    except Exception as e:
        # Als er iets misgaat, stuur de foutmelding naar de uitgang
        ctypes.windll.user32.MessageBoxW(0, f"Fout bij het online ophalen van de OTL info. Controleer je internet of firewall. {nl}Kon de data niet ophalen vanop:{nl}{url}{nl}{nl}Foutcode:{nl}{e}", "OTL_propertysetdefinitions_aanmaken", 0)
        raise Exception(f"Fout bij ophalen OTL json van Github. Controleer je internet of firewall.\nFoutcode: {e}")
    return json_data



def OTL_dict_filter(OTL_subset, filter_subsetattributen:bool, OTL_data_dict:dict):
    """Gebruikt de OTLMOW model om info uit een OTL subset te vertalen naar een dict bruikbaar voor het opmaken van civil3D propertysets"""

    eindlijst = [] 
    try:
        if exists(OTL_subset):
            
            urilijst = select_klasses(OTL_subset) #haal een lijst van object uris op uit de OTL subset
            for uri in urilijst:
                #filter de nodige klasses uit de json
                for onderdeeldict in OTL_data_dict:
                    if onderdeeldict['typeURI'] == uri:
                        eindlijst.append(onderdeeldict)
                        break

            if filter_subsetattributen: #filter de attributen van de klasses in de subset
                for onderdeeldict in eindlijst:
                    klasse_uri = onderdeeldict['typeURI']
                    attributen_in_subset = select_attributen(OTL_subset, klasse_uri) #haal de attributen op voor deze klasse uit de subset
                    attributenlijst = onderdeeldict['attributen'] #haal de attributenlijst op uit de json
                    attributenlijst_filtered = [] #maak een nieuwe lijst voor de gefilterde attributen
                    for attribuutdict in attributenlijst:
                        attribuutnaam = attribuutdict['dotnotatie_attribuutnaam'].split('.')[-1] #pak enkel de naam van het attribuut (zonder dotnotatie)
                        if attribuutnaam in attributen_in_subset: #check of het attribuut voorkomt in de subset
                            attributenlijst_filtered.append(attribuutdict) #voeg het toe aan de nieuwe lijst
                        elif attribuutdict['dotnotatie_attribuutnaam'] == "assetId.identificator": #voeg het assetId attribuut altijd toe, ook al staat het niet in de subset
                            if attribuutdict not in attributenlijst_filtered: #check of het attribuut al toegevoegd is
                                attributenlijst_filtered.append(attribuutdict)
                        elif attribuutnaam == "typeURI": #voeg het typeURI attribuut altijd toe, ook al staat het niet in de subset
                            if attribuutdict not in attributenlijst_filtered: #check of het attribuut al toegevoegd is
                                attributenlijst_filtered.append(attribuutdict)
                    onderdeeldict['attributen'] = attributenlijst_filtered #vervang de oude lijst door de gefilterde lijst
            
        else: #Een dummy maken als er geen gebruikersinput gegeven is, zodat dynamo geen 'none' krijgt
            eindlijst = []
            onderdeeldict = dummydict()
            print("Geen OTL subset gevonden, een dummy wordt aangemaakt.")

    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"Er liep iets mis in het filteren van de OTL data adhv de subset:{e}", "OTL_propertysetdefinitions_aanmaken", 0)        


    return eindlijst


#UITVOEREN

#subsetpad = IN[0]
#subset_filter = IN[1]
#objecten_filter = IN[2]
#go = IN[3]

subsetpad = r'seinbrug_en_dynbord.db'
subset_filter = True
objecten_filter = True
go = 1

OUT = ""
if go:
    #De json met OTL info (dotnotatie, datatypes, defaultvalues, keuzelijsten, ...) ophalen van github.
    OTL_data_dict = OTL_info_json_afladen()
    if objecten_filter:
        OUT = OTL_dict_filter(subsetpad,subset_filter, OTL_data_dict)
    else:
        OUT = OTL_data_dict
    print(OUT)