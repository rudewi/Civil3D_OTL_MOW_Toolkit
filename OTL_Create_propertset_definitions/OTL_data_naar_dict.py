import importlib
import sqlite3
from sqlite3 import Error
from os.path import exists
import ctypes

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

    return(klasses_onderdelen)

def select_attributen(conn, klasse_uri):
    """attributen voor klasse uit SQlite halen"""
    conn = create_connection(conn)
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


def attribute_info_to_dict(obj, attribute):
    """verzamelt de info van het attribuut (in dotnatatie) in een dict"""

    attribuutdict = {} # een dict per dotnotatie-attribuut

    #SPECIALE ATTRIBUTEN
    if attribute == "typeURI": #kan geen attr ophalen voor typeURI
        #attr = getattr(obj,"_typeURI")
        attribuutdict["attribuutdefinitie"] = "De URI van het object"
        attribuutdict["datatype_attribuut"] = "Text"
        attribuutdict["default_value"] = obj.typeURI
        attribuutdict["dotnotatie_attribuutnaam"] = attribute

    elif attribute == "geometry": 
        attribuutdict = {} #Geometrie attribuut niet nodig in civil3D, 

    #NORMALE ATTRIBUTEN
    else:
        #ATTRIBUUTNAAM
        attribuutdict["dotnotatie_attribuutnaam"] = attribute
        attr = DotnotationHelper.get_attribute_by_dotnotation(obj,attribute,waarde_shortcut=False) #haalt het attribuut-object op
        attr_ws = DotnotationHelper.get_attribute_by_dotnotation(obj,attribute,waarde_shortcut=True)

        #DEFINTIE
        attribuutdict["attribuutdefinitie"] = (attr.definition[:250] + '..') if len(attr.definition) > 250 else attr.definition
        
        if type(attr) == OTLAttribuut:
            OTL_datatype = attr_ws.field
            
        #DATATYPE & DEFAULT VALUE(civil3D datatypes)
        if OTL_datatype == StringField:
            attribuutdict["datatype_attribuut"] = "Text"
            attribuutdict["default_value"] = ""
        elif OTL_datatype == FloatOrDecimalField:
            attribuutdict["datatype_attribuut"] = "Real"
            attribuutdict["default_value"] = -999999999.000000
        elif OTL_datatype == NonNegIntegerField or OTL_datatype == IntegerField: 
            attribuutdict["datatype_attribuut"] = "Integer"
            attribuutdict["default_value"] = -999999999
        elif OTL_datatype == BooleanField:
            if attribute == "isActief":
                attribuutdict["datatype_attribuut"] = 'keuzelijst'
                attribuutdict["default_value"] = 'True'
                attribuutdict["keuzelijstopties"] = ['True','False','-']
                attribuutdict["keuzelijstnaam"] = 'booleanlijst-true-default'
            else:
                attribuutdict["datatype_attribuut"] = 'keuzelijst'
                attribuutdict["default_value"] = '-'
                attribuutdict["keuzelijstopties"] = ['-','True','False']
                attribuutdict["keuzelijstnaam"] = 'booleanlijst'

        #KEUZELIJSTOPTIES
        elif OTL_datatype.naam.startswith("Kl"):
            attribuutdict["datatype_attribuut"] = 'keuzelijst'
            attribuutdict["default_value"] = '-'
            keuzelijstopties = ["-"] #Default value voor keuzelijst moet in lijst voorkomen
            for i, k in enumerate(attr.field.options.keys()):
                keuzelijstopties.append(k)
            attribuutdict["keuzelijstopties"] = keuzelijstopties
            attribuutdict["keuzelijstnaam"] = str(attr.field.naam)       
        else: #DateField, URIField, ..
            attribuutdict["datatype_attribuut"] = "Text"
            attribuutdict["default_value"] = ""

    return attribuutdict

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


def get_dotnotation(obj):
    """creer de dotnotatie weergave voor de attributen"""
    
    obj.fill_with_dummy_data() #Vul het object met dummy data, zodat deze bruikbaar is voor dotnotationdict

    #Workaround voor ListOfList error bij dotnotatie creatie:
    if obj.typeURI == "https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#Toegangsprocedure": 
        obj.bijlage = None

    try:
        d_dict = DotnotationDictConverter.to_dict(obj) #Vertaal alle attributen naar dotnotatie
    except Error as e:
        ctypes.windll.user32.MessageBoxW(0, str(e), "Dotnotatie aanmaken gefaald", 0)
        pass

    return d_dict
    
#MAIN FUNCTION
def OTL_to_dict(OTL_subset, filter_subsetattributen:bool):
    """Gebruikt de OTLMOW model om info uit een OTL subset te vertalen naar een dict bruikbaar voor het opmaken van civil3D propertysets"""

    if exists(OTL_subset):
        eindlijst = [] 

        urilijst = select_klasses(OTL_subset) #haal een lijst van object uris op uit de OTL subset

        for uri in urilijst:

            obj = dynamic_create_instance_from_uri(uri) #Instantieer de klasse via het OTLMOW model
            dotnotatie_attributen = get_dotnotation(obj) #Haalt alle dotnotatie attributen op voor het object 
            subsetattributen = select_attributen(OTL_subset, obj.typeURI) #haal een lijst van de attributen voor het object uit de subset

            #Verzamel info over het onderdeel (of installatie, implemenatieelement, ...)
            onderdeeldict = {} #een dict om alle info voor een bepaalde propertyset in te verzamelen
            onderdeeldict["propertysetnaam"] = create_psetnaam(obj, urilijst) #creert een unieke propertysetnaam
            onderdeeldict["definitie"] = (obj.__doc__[:250] + '..') if len(obj.__doc__) > 250 else obj.__doc__
            onderdeeldict["typeURI"] = obj.typeURI
            onderdeeldict["attributen"] = []
    
            #Verzamel info per attribuut, indien gevraagd volgens subset
            for attribute in dotnotatie_attributen:
                if filter_subsetattributen: #Enkel de attributen uit de subset meenemen
                    if attribute.split(".")[0] in subsetattributen:
                        attribuutdict = attribute_info_to_dict(obj,attribute)
                    else:
                        attribuutdict = {}

                else: attribuutdict = attribute_info_to_dict(obj,attribute) #Alle attributen uit het OTL model meenemen

                if attribuutdict: #Voegt enkel toe aan attributenlijst in dict als er een attribuutdict werd gemaakt.
                    onderdeeldict["attributen"].append(attribuutdict) #Voeg de attribuutinfo toe aan de dict voor dit onderdeel

            eindlijst.append(onderdeeldict)


    else: #Een dummy maken als er geen gebruikersinput gegeven is, zodat dynamo geen 'none' krijgt
        eindlijst = []
        onderdeeldict = dummydict()

    return eindlijst


#UITVOEREN
subsetpad = IN[0]
subset_filter = IN[1]
go = IN[2]

OUT = ""
if go:
    try:
        #NODIGE MODULES UIT OTLMOW CONVERTER INLADEN
        from otlmow_converter.DotnotationDictConverter import DotnotationDictConverter
        from otlmow_converter.DotnotationHelper import DotnotationHelper
        
        #NODIGE MODULES UIT OTLMOW MODEL INLADEN
        from otlmow_model.OtlmowModel.BaseClasses.KeuzelijstField import KeuzelijstField
        from otlmow_model.OtlmowModel.BaseClasses.StringField import StringField
        from otlmow_model.OtlmowModel.BaseClasses.BooleanField import BooleanField
        from otlmow_model.OtlmowModel.BaseClasses.FloatOrDecimalField import FloatOrDecimalField
        from otlmow_model.OtlmowModel.BaseClasses.NonNegIntegerField import NonNegIntegerField
        from otlmow_model.OtlmowModel.BaseClasses.IntegerField import IntegerField
        from otlmow_model.OtlmowModel.BaseClasses.OTLObject import OTLAttribuut
        from otlmow_model.OtlmowModel.BaseClasses.OTLObject import dynamic_create_instance_from_uri
        
        #OMZETTING STARTEN
        OUT = OTL_to_dict(subsetpad,subset_filter)
        
    except:
        ctypes.windll.user32.MessageBoxW(0, "Er liep iets mis in het omzetten van de OTL data naar dynamo", "OTL data naar dict", 0)        
