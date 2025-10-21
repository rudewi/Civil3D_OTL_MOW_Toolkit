import urllib.request
import sys
from zipfile import ZipFile
import os.path
import ctypes
import imp


#DE JUISTE FOLDERS OPHALEN VIA INPUT
doelpad = IN[0]
subsetpad = IN[1]
subset_filter = IN[2]
toolkit_update = IN[3]

nl = '\n'


#FUNCTIE VOOR AFLADEN MODULES
def moduleDownloadenViaZiplink(naam,link,doelpad):
    """Gebruikt een Github link om python modules af te laden en bruikbaar te maken"""
    ziplocatie = f'{doelpad}\\{naam}.zip'

    try:
        urllib.request.urlretrieve(link,ziplocatie)
        with ZipFile(ziplocatie, 'r') as zObject: 
            zObject.extractall(path=doelpad)
            message = f'Download van {naam} geslaagd'
        if not os.path.isdir(doelpad): #kijken of de folder bestaat
            message = f'FOUT in downloaden of unzippen van {naam} python library'
    except:
        message = f'FOUT in downloaden of unzippen van {naam} python library'

    return message
                  
#FUNCTIE VOOR MODULE TOEVOEGEN AAN PATH
def moduleToevoegenAanPath(modulefolder,naam):
    if os.path.isdir(modulefolder): #kijken of de folder bestaat
        if os.path.isdir(modulefolder + r'/otlmow_model'): #kijken of de otl model in de folder staat

            if modulefolder in sys.path:
                sys.path.remove(modulefolder) #Verwijderen om opniew te kunnen inladen, bv na nieuwe download

            try:
                sys.path.insert(0, modulefolder)
                #message = f'Toevoegen van {naam} aan PATH geslaagd'
                message = ""
    
            except:
                message = f'FOUT in toevoegen van {naam} python library'

        else:
            message = f'De OTL library werd niet gevonden in de folder {modulefolder}, mogelijk zijn ze nog niet gedownload'
   
    else:
        message = f'FOUT in toevoegen van python libraries, folder {modulefolder} bestaat niet'
    
    return message


def checkOTLmodules(message):
    """controleer of de modules correct zijn ingeladen"""
    try:
        from otlmow_model.OtlmowModel.Classes.ImplementatieElement import AIMObject
        from otlmow_converter.DotnotationDictConverter import DotnotationDictConverter
        
        finalmessage = f"{nl}OTL modules en libraries zijn succesvol ingeladen{nl}{message}"
        go = 1

    except Exception as e:
        go = 0
        # Controleer of de gebruikte python versie lager is dan 3.9
        MIN_MAJOR = 3
        MIN_MINOR = 9
        current_major = sys.version_info.major
        current_minor = sys.version_info.minor

        if current_major < MIN_MAJOR or (current_major == MIN_MAJOR and current_minor < MIN_MINOR):
            finalmessage = f"{nl}FOUT bij inladen OTL modules en libraries:{nl}De gebruikte python versie ({current_major}.{current_minor}) is te laag {nl}Minimum vereist = 3.9{nl}Probeer een recentere versie van Dynamo voor Civil3D, bv. 2025 of nieuwer"
    
        else:
            finalmessage = f"{nl}FOUT bij inladen OTL modules en libraries:{nl}{message}{nl}fout:{e}"


    return finalmessage,go
    


def getOTLmodules(doelpad,downloadcheck):
    """referentie welke modules waar opgehaald moeten worden. Toevoeging aan het python Path en testing"""

    message = ""
    if downloadcheck: #voor het geval de libs gedownload moeten worden
        #OTLMOW MODEL
        naam = "otlmow_model"
        githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Model/refs/heads/master/source.zip'
        message = message + "\n" + moduleDownloadenViaZiplink(str(naam),githublink,doelpad)
        
        #OTLMOW CONVERTER
        naam = "otlmow_converter"
        githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Converter/refs/heads/master/source.zip'
        message = message + "\n" + moduleDownloadenViaZiplink(str(naam),githublink,doelpad)

    #PAD TOEVOEGEN
    message = message + "\n" + "\n" + moduleToevoegenAanPath(doelpad,"OTL modules en libraries")
    
    #CHECK OF MODULES WERKEN
    outputmessage,go = checkOTLmodules(message)

    return outputmessage,go

#UITVOEREN
if doelpad and doelpad != "ongeldig_pad":
    outputmessage, go = getOTLmodules(doelpad,toolkit_update)
    if outputmessage:
        ctypes.windll.user32.MessageBoxW(0, outputmessage, "Inladen OTLMOW libraries", 0)

else:
    go = 0

OUT = [doelpad,subsetpad,subset_filter,go]