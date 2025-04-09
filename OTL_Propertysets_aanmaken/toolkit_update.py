import urllib.request
import sys
from zipfile import ZipFile
import os.path
from os.path import exists
import xml.etree.ElementTree as et
import ctypes

#DE JUISTE FOLDERS OPHALEN VIA INPUT
downloadcheck = IN[0]
doelpath = IN[1][1]


#FUNCTIE VOOR AFLADEN MODULES
def moduleDownloadenViaZiplink(naam,link,doelpath):
    """Gebruikt een Github link om python modules af te laden en bruikbaar te maken"""
    ziplocatie = f'{doelpath}\{naam}.zip'
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
    """voegt de locatie toe aan het path"""
    totalmessage = ["Geen download van de toolkit gestart"]
    if os.path.isdir(modulefolder): #kijken of de folder bestaat
        try:
            if modulefolder not in sys.path:
                sys.path.insert(0, modulefolder)
                ctypes.windll.user32.MessageBoxW(0, (str(sys.path)), "PATH UPDATE", 0)
            message = f'De {naam} python library werd ge-update'
            totalmessage = ["geldig"]
            totalmessage.append(message)
        except:
            message = f'FOUT in toevoegen van {naam} python library'
            totalmessage = []
            totalmessage.append(message)      
    else:
        message = f'FOUT in toevoegen van python libraries, folder bestaat niet, mogelijk zijn ze nog niet gedownload'
        totalmessage.append(message) 

    return totalmessage

#Libraries inladen
totalmessage = []

if not os.path.isdir(doelpath): #kijken of de folder bestaat
    message = f'Het doelpath kon niet worden gevonden {doelpath}'
    totalmessage.append(message)

else:
    if downloadcheck: #voor het geval de libs gedownload moeten worden
        naam = "OTL_Propertysets_aanmaken"
        githublink = r'https://github.com/rudewi/Civil3D_OTL_MOW_Toolkit/raw/refs/heads/main/OTL_Propertysets_aanmaken/OTL_Propertysets_aanmaken.zip'
        moduleDownloadenViaZiplink(str(naam),githublink,doelpath)
        moduleToevoegenAanPath(doelpath,naam)
        
    else:
        naam = "OTL_Propertysets_aanmaken"
        moduleToevoegenAanPath(doelpath,naam)


try:
    from OTL_Propertysets_aanmaken.OTL_libraries_inladen import getOTLmodules
    totalmessage = ["geldig","OTL toolkit modules succesvol ingeladen"]
 
except:
    message = "fout bij inladen OTL toolkit modules."
    totalmessage.append(message) 

totalstringmessage = ""
for message in totalmessage:
    if totalstringmessage == "":
        totalstringmessage = message
    else:
        totalstringmessage = totalstringmessage + "\n" + "\n" + message

ctypes.windll.user32.MessageBoxW(0, str(totalstringmessage), "updaten toolkit", 0)

OUT = totalmessage