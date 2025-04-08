import importlib
import sqlite3
from sqlite3 import Error
from os.path import exists
import ctypes

#NODIGE MODULES UIT OTLMOW CONVERTER INLADEN
# OPM > Te bekijken of we deze helemaal nodig hebben
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

#FUNCTIES
def create_connection(db_file):
        """ maak connectie naar de SQLite database"""
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            ctypes.windll.user32.MessageBoxW(0, str(e), "SQlite lezen gefaald", 1)
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
            ctypes.windll.user32.MessageBoxW(0, "Verwerking van meer dan 100 OTL types, dit kan enkele minuten duren..", "Inlezen OTL SQLite", 1)

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
        attr = DotnotationHelper.get_attribute_by_dotnotation(obj,attribute) #haalt het attribuut-object op voor de laatste stap van de dotnotatie

        #DEFINTIE
        attribuutdict["attribuutdefinitie"] = (attr.definition[:250] + '..') if len(attr.definition) > 250 else attr.definition
        
        if type(attr) == OTLAttribuut:
            OTL_datatype = attr.field
            
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

def create_psetnaam(obj, objectenlijst, objectsoort):
    """Maakt de unieke propertysetnaam voor een object"""

    #Naam van de klasse
    objectnaam = obj.__class__.__name__
    
    #DEPRECATION label toevoegen
    if hasattr(obj, 'deprecated_version'):
        depr = "_DEPR-" + str(obj.deprecated_version)
    else:
        depr = ""

    #Controle of naam reeds voorkomt
    if sum(s.endswith('#' + objectnaam) for s in objectenlijst) == 1:
        propertysetnaam = "OTL_" + objectnaam + depr
    else: 
        propertysetnaam = "OTL_" + objectnaam + "_" + objectsoort + depr 

    return propertysetnaam

#MAIN FUNCTION
def OTL_to_dict(OTL_subset, filter_subsetattributen:bool):
    """Gebruikt de OTLMOW model om info uit een OTL subset te vertalen naar een dict bruikbaar voor het opmaken van civil3D propertysets"""

    if exists(OTL_subset):
        objectenlijst = []
        urilijst = select_klasses(OTL_subset)
        for uri in urilijst:
            objectenlijst.append(str(uri.split('/')[-1]))
            
        eindlijst = []      
        
        for objectnaam in objectenlijst:
            #split voor hastag in variabele steken, deze gebruiken in locatie (ondedeel/installatie/andere..)
            objectsoort = str(objectnaam.partition('#')[0].title())
            if objectsoort == "Implementatieelement": #workaround hoofdletter E in namespace, niet in uri
                objectsoort = "ImplementatieElement"

            objectnaam = str(objectnaam.partition('#')[-1])
            locatie = "otlmow_model.OtlmowModel.Classes." + str(objectsoort) + "." + objectnaam
            # ALTERNATIEF: object aanmaken obv namespace:
                # in OTL object in baseclass -> functie= dynamic create instance from namespace / uri
            OTL_Onderdeel = importlib.import_module(locatie,objectnaam) #haalt de juiste module op (cfr: import otlmow_model.OtlmowModel.Classes.Onderdeel.Camera)
            Obj_klasse = getattr(OTL_Onderdeel,objectnaam) #haalt de klasse uit de module (cfr: from otlmow_model.OtlmowModel.Classes.Onderdeel.Camera import Camera )
            obj = Obj_klasse() #instantieert deze klasse (cfr: obj = Camera())

            propertysetnaam = create_psetnaam(obj, objectenlijst, objectsoort)

            onderdeeldict = {} #een dict om alle info voor een bepaalde propertyset in te verzamelen

            onderdeeldict["propertysetnaam"] = propertysetnaam
            onderdeeldict["definitie"] = (obj.__doc__[:250] + '..') if len(obj.__doc__) > 250 else obj.__doc__
            onderdeeldict["typeURI"] = obj.typeURI
            onderdeeldict["attributen"] = []

            obj.fill_with_dummy_data() #Vul het object met dummy data

            if obj.typeURI == "https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#Toegangsprocedure": 
                obj.bijlage = None #List of List error vermijden bij dotnotatie creatie

            try:
                d_dict = DotnotationDictConverter.to_dict(obj) #Vertaal alle attributen naar dotnotatie
            except Error as e:
                ctypes.windll.user32.MessageBoxW(0, str(e), "Dotnotatie aanmaken gefaald", 1)
                pass        

            subsetattributen = select_attributen(OTL_subset, obj.typeURI)

            for attribute in d_dict:
                if filter_subsetattributen: #Enkel de attributen uit de subset meenemen
                    if attribute.split(".")[0] in subsetattributen:
                        attribuutdict = attribute_info_to_dict(obj,attribute)
                    else:
                        attribuutdict = {}
                else: attribuutdict = attribute_info_to_dict(obj,attribute) #Alle attributen uit het OTL model meenemen

                if attribuutdict:
                    onderdeeldict["attributen"].append(attribuutdict) #Voeg de attribuutinfo toe aan de dict voor dit onderdeel

            eindlijst.append(onderdeeldict)


    else: #Als er geen gebruikersinput gegeven is
        #EEN DUMMY MAKEN
        eindlijst = []
        onderdeeldict = dummydict()

    eindlijst.append(onderdeeldict)
    return eindlijst


#Voor testing script buiten dynamo:
OTL_to_dict('OTL_212.db',False)
#print(select_attributen('testsubset.db','https://wegenenverkeer.data.vlaanderen.be/ns/installatie#HorizontaleConstructieplaat'))