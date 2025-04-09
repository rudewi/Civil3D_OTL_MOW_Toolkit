#Deze codeblock zit ingewerkt in het script
import os.path
from System.Reflection import Assembly
import xml.etree.ElementTree as et
import ctypes

user_input_path = IN[0]

if user_input_path:
    if isinstance(user_input_path, str):
        if os.path.isdir(user_input_path):
            OUT = ["geldig",user_input_path]
        else:
            user_input_path = "ongeldig"
    else:
        user_input_path = "ongeldig"
        
else:
    #Er werd geen user waarde opgegeven
    #ZOEKT DE FOLDER ZOEKEN WAAR PACKAGE IS OPGESLAGEN
    folderstring_na_version = r'\packages\OTL_MOW_Toolkit\extra' #einde van het pad
    
    try:    
        appDataPath = os.getenv('APPDATA') #de appdata locatie
        #de dynamo & civil versie ophalen
        dynamo = Assembly.Load('DynamoCore')   
        civil_version = str(dynamo.CodeBase).split("AutoCAD", 1)[1][1:5] #Civil versie opzoeken adhv locatie van dyn assembly
        dynamo_version = ".".join(str(dynamo.GetName().Version).split(".", 2)[:2]) #dynamo versie ophalen
        ctypes.windll.user32.MessageBoxW(0, str(civil_version), "Gevonden civilversie", 0)
        
        found_dynpath = appDataPath + r'\Autodesk\C3D ' + civil_version + r'\Dynamo' + '\\' + dynamo_version
        
        if os.path.isdir(found_dynpath):
            #Open de dynamo settings XML en bekijk de folders waar packages zijn opgeslagen:
            doelpath = found_dynpath + r'\packages' #voor wanneer OTL_MOW_Toolkit package folder niet bestaat
            root = et.parse(found_dynpath + "\DynamoSettings.xml").getroot()
            for child in root:
                if child.tag == "CustomPackageFolders":
                    for path in child:
                        path_packages = path.text + folderstring_na_version
                        if os.path.isdir(path_packages):
                            doelpath = path_packages
    
            OUT = OUT = ["geldig",doelpath] #juiste folder naar output
        
        else:
            user_input_path = "ongeldig"
    
    except:
        user_input_path = "ongeldig"
        
if user_input_path == "ongeldig":
    ctypes.windll.user32.MessageBoxW(0, "Geen geldige folder gevonden om libraries op te slaan", "Fout", 0)
    OUT = ["FOUT","Geen geldige folder gevonden om libraries op te slaan"]

