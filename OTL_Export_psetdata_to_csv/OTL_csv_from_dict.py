import collections
import csv
import ctypes
from os import path
m = ctypes.windll.user32

#variabelen
nl = "\n"
messagelist = []

def csv_schrijven(data,filepath):
    """CSV wegschrijven"""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(data)
        filename = filepath.split("\\")[-1]
        message = f"{(len(data)-1)} rijen geschreven in {filename}"    
    except Exception as e:
        message = f"Er is een fout opgetreden bij het schrijven naar het bestand: {e}"
    return message

def create_otl_datalist(dictlijst,headerkeys):
    """lijst deconstrueren & defaults overschrijven"""

    totalvaluelist = [headerkeys]

    for d in dictlijst:
        itemvaluelist = [] 
        for header in headerkeys:
            if header in d:
                if d[header] == -999999999 or d[header] == "-":
                    itemvaluelist.append("")
                else:
                    itemvaluelist.append(d[header])
            else:
                itemvaluelist.append("")
        totalvaluelist.append(itemvaluelist)
    return totalvaluelist 
    

def file_per_OTL_type(pset_dicts,folderpath):
    """maakt een aparte lijst van pset_dicts per typeURI waarde, en schrijf voor elk een file als csv"""
    result = collections.defaultdict(list)
    for d in pset_dicts:
        if 'typeURI' in d.keys():
            result[d['typeURI']].append(d)
        else:
            pass
    result_list = list(result.values())
    
    objectnamen = [] #om te checken op dubbele namen
    filepaths = []
    
    for l in result_list:
        """filepaden aanmaken"""
        laatste_deel_uri = l[0]['typeURI'].split('/')[-1]
        objectnaam = str(laatste_deel_uri.partition('#')[-1])
        objectsoort = str(objectnaam.partition('#')[0].title())
        if objectnaam in objectnamen:
            objectnaam = objectnaam + "_" + objectsoort
        objectnamen.append(objectnaam)
            
        filepath = folderpath + "\\" + objectnaam + ".csv"
        filepaths.append(filepath)
        
        dl = create_otl_datalist(l,list(l[0].keys()))
        c = csv_schrijven(dl,filepath)
        messagelist.append(c)
        
    m.MessageBoxW(0, f"{nl.join(messagelist)}", "OTL_Export psetdata to CSV", 0)
    return messagelist

def alles_in_een_OTL_file(pset_dicts,filepath):
    """zet alles in 1 lijst en schrijft naar een file in csv"""
    headerkeys = ["assetId.identificator","typeURI"]
    for d in pset_dicts:
        for k in d.keys():
            if k not in headerkeys:
                headerkeys.append(k)
    
    dl = create_otl_datalist(pset_dicts,headerkeys)
    c = csv_schrijven(dl,filepath)
    messagelist.append(c)
    m.MessageBoxW(0, f"{nl.join(messagelist)}", "OTL_Export psetdata to CSV", 0)
    return messagelist
