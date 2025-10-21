import urllib.request
import sys
from zipfile import ZipFile
import os.path
import ctypes


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
        #downloadmsg = f'De package {naam} werd gedownload naar locatie {ziplocatie}'
        #ctypes.windll.user32.MessageBoxW(0, downloadmsg , "Donwload library", 0)
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
        if modulefolder not in sys.path:
            try:
                sys.path.insert(0, modulefolder)
                message = f'Toevoegen van {naam} aan PATH geslaagd'
    
            except:
                message = f'FOUT in toevoegen van {naam} python library'
        else:
            message = f'modulefolder met {naam} reeds toegevoegd aan sys.path'
   
    else:
        message = f'FOUT in toevoegen van python libraries, folder {modulefolder} bestaat niet, mogelijk zijn ze nog niet gedownload'
    
    return message


def checkOTLmodules(message):
    """controleer of de modules correct zijn ingeladen"""
    try:
        from otlmow_model.OtlmowModel.Classes.ImplementatieElement import AIMObject
        from otlmow_converter.DotnotationDictConverter import DotnotationDictConverter
        finalmessage = f"{nl}OTL modules en libraries zijn succesvol ingeladen{nl}{message}"
        go = 1

    except:
        finalmessage = f"{nl}FOUT bij inladen OTL modules en libraries:{nl}{message}"
        go = 0

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
    ctypes.windll.user32.MessageBoxW(0, outputmessage, "Inladen OTLMOW libraries", 0)

else:
    go = 0

OUT = [subsetpad,subset_filter,go]