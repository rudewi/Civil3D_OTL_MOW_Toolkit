import urllib.request
import sys
from zipfile import ZipFile
import os.path
import ctypes


#DE JUISTE FOLDERS OPHALEN VIA INPUT

downloadcheck = IN[0]
doelpath = IN[1][1]
doelpathceck = IN[1][0]

#FUNCTIE VOOR AFLADEN MODULES
def moduleDownloadenViaZiplink(naam,link,doelpath):
    """Gebruikt een Github link om python modules af te laden en bruikbaar te maken"""
    ziplocatie = f'{doelpath}\\{naam}.zip'

    try:
        urllib.request.urlretrieve(link,ziplocatie)
        #downloadmsg = f'De package {naam} werd gedownload naar locatie {ziplocatie}'
        #ctypes.windll.user32.MessageBoxW(0, downloadmsg , "Donwload library", 0)
        with ZipFile(ziplocatie, 'r') as zObject: 
            zObject.extractall(path=doelpath)
            message = f'Download van {naam} geslaagd'
        if not os.path.isdir(doelpath): #kijken of de folder bestaat
            message = f'FOUT in downloaden of unzippen van {naam} python library'
    except:
        message = f'FOUT in downloaden of unzippen van {naam} python library'

    return message
                  
#FUNCTIE VOOR MODULE TOEVOEGEN AAN PATH
def moduleToevoegenAanPath(modulefolder,naam):
    if os.path.isdir(modulefolder): #kijken of de folder bestaat
        try:
            if modulefolder not in sys.path:
                sys.path.insert(0, modulefolder)
            message = f'Toevoegen van {naam} aan PATH geslaagd'

        except:
            message = f'FOUT in toevoegen van {naam} python library'
   
    else:
        message = f'FOUT in toevoegen van python libraries, folder {modulefolder} bestaat niet, mogelijk zijn ze nog niet gedownload'
    
    return message


def getOTLmodules(doelpath,downloadcheck):
    """referentie welke modules waar opgehaald moeten worden. Toevoeging aan het python Path en testing"""

    if not os.path.isdir(doelpath): #kijken of de folder bestaat
        outputmessage = ["FOUT", f'Het doelpath kon niet worden gevonden {doelpath}']

    else:
        if downloadcheck: #voor het geval de libs gedownload moeten worden
            message = ""
            #OTL dynamo for civil toolkit
            naam = "otlmow_toolkit"
            githublink = r'https://raw.githubusercontent.com/rudewi/Civil3D_OTL_MOW_Toolkit/refs/heads/main/Civil3D_OTL_MOW_Toolkit.zip'
            message = message + "\n" + moduleDownloadenViaZiplink(str(naam),githublink,doelpath)

            #OTLMOW MODEL
            naam = "otlmow_model"
            githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Model/refs/heads/master/source.zip'
            message = message + "\n" + moduleDownloadenViaZiplink(str(naam),githublink,doelpath)
            
            #OTLMOW CONVERTER
            naam = "otlmow_converter"
            githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Converter/refs/heads/master/source.zip'
            message = message + "\n" + moduleDownloadenViaZiplink(str(naam),githublink,doelpath)


        #PAD TOEVOEGEN
        message = message + "\n" + moduleToevoegenAanPath(doelpath,"OTL modules en libraries")


        try:
            from otlmow_model.OtlmowModel.Classes.ImplementatieElement import AIMObject
            from otlmow_converter.DotnotationDictConverter import DotnotationDictConverter
            from OTL_Propertysets_aanmaken.OTL_data_naar_dict import OTL_to_dict

            outputmessage = ["geldig", "OTL modules en libraries zijn succesvol ingeladen: " + "\n" + message + "\n" + f'locatie: {doelpath}' ]

        except:
            outputmessage = ["FOUT", "FOUT bij inladen OTL OTL modules en libraries: " + "\n" + message + "\n" + f'locatie: {doelpath}']


    ctypes.windll.user32.MessageBoxW(0, outputmessage[1], "Inladen libraries", 0)

    return outputmessage

#Uitvoeren
if doelpathceck == "geldig":
    OUT = getOTLmodules(doelpath,downloadcheck)
else:
    OUT = "ongeldig doelpad"
