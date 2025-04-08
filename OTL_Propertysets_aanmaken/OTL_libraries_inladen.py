import urllib.request
import sys
from zipfile import ZipFile
import os.path
import ctypes
import os

totalmessage = []

#FUNCTIE VOOR AFLADEN MODULES
def moduleDownloadenViaZiplink(naam,link,doelpath):
    """Gebruikt een Github link om python modules af te laden en bruikbaar te maken"""
    ziplocatie = f'{doelpath}\\{naam}.zip'
    urllib.request.urlretrieve(link,ziplocatie)
    downloadmsg = f'De package {naam} werd gedownload naar locatie {ziplocatie}'
    ctypes.windll.user32.MessageBoxW(0, downloadmsg , "Donwload library", 0)
    with ZipFile(ziplocatie, 'r') as zObject: 
        zObject.extractall(path=doelpath)
    if not os.path.isdir(doelpath): #kijken of de folder bestaat
        message = f'FOUT in downloaden of unzippen van {naam} python library'
        totalmessage.append(message)               


#FUNCTIE VOOR MODULE TOEVOEGEN AAN PATH
def moduleToevoegenAanPath(modulefolder,naam):
    if os.path.isdir(modulefolder): #kijken of de folder bestaat
        try:
            if modulefolder not in sys.path:
                sys.path.insert(0, modulefolder)
                #sys.path.append(modulefolder)
            message = f'De {naam} python library werd gevonden'
            totalmessage.append(message)
        except:
            message = f'FOUT in toevoegen van {naam} python library'
            totalmessage.append(message)      
    else:
        message = f'FOUT in toevoegen van python libraries, folder {modulefolder} bestaat niet, mogelijk zijn ze nog niet gedownload'
        totalmessage.append(message) 


def getOTLmodules(doelpath,downloadcheck):
    """referentie welke modules waar opgehaald moeten worden. Toevoeging aan het python Path en testing"""
    totalmessage = []

    if not os.path.isdir(doelpath): #kijken of de folder bestaat
        message = f'Het doelpath kon niet worden gevonden {doelpath}'
        totalmessage.append(message)

    else:
        if downloadcheck: #voor het geval de libs gedownload moeten worden
            
            #OTLMOW MODEL
            naam = "otlmow_model"
            #subfolder = "OTLMOW-Model-master"
            #modulefolder = f'{doelpath}\\{subfolder}'
            #if not os.path.isdir(modulefolder):
            #    os.mkdir(modulefolder)
            githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Model/refs/heads/master/source.zip'
            moduleDownloadenViaZiplink(str(naam),githublink,doelpath)
            moduleToevoegenAanPath(doelpath,naam)
            
            #OTLMOW CONVERTER
            naam = "otlmow_converter"
            #subfolder = "OTLMOW-Converter-master"
            #modulefolder = f'{doelpath}\\{subfolder}'
            #if not os.path.isdir(modulefolder):
            #    os.mkdir(modulefolder)
            githublink = r'https://raw.githubusercontent.com/davidvlaminck/OTLMOW-Converter/refs/heads/master/source.zip'
            moduleDownloadenViaZiplink(str(naam),githublink,doelpath)
            moduleToevoegenAanPath(doelpath,naam)

        else: #voor het geval de libs reeds gedownload zijn:
            #OTLMOW MODEL
            naam = "otlmow_model"
            #subfolder = "OTLMOW-Model-master"
            #modulefolder = f'{doelpath}\\{subfolder}'
            moduleToevoegenAanPath(doelpath,naam)

            #OTLMOW CONVERTER
            naam = "otlmow_converter"
            #subfolder = "OTLMOW-Converter-master"
            #modulefolder = f'{doelpath}\\{subfolder}'
            moduleToevoegenAanPath(doelpath,naam)

        try:
            from otlmow_model.OtlmowModel.Classes.Onderdeel.Camera import Camera
            camera = Camera()
            from otlmow_converter.DotnotationDictConverter import DotnotationDictConverter
            totalmessage = ["geldig","OTL MOW libraries zijn succesvol ingeladen"]
            #totalmessage.append(message) 

        except:
            message = "fout bij inladen OTL MOW libraries."
            totalmessage.append(message) 

    totalstringmessage = ""
    for message in totalmessage:
        if totalstringmessage == "":
            totalstringmessage = message
        else:
            totalstringmessage = totalstringmessage + "\n" + "\n" + message

    ctypes.windll.user32.MessageBoxW(0, totalstringmessage, "Inladen libraries", 0)

    return totalmessage

#Voor testing script buiten dynamo:
#test = print(getOTLmodules(r'tempDoelPath',True))