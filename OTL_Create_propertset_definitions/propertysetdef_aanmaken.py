# Load the Python Standard and DesignScript Libraries
import clr
import ctypes

# Add Assemblies for AutoCAD and Civil3D
clr.AddReference('AcMgd')
clr.AddReference('AcCoreMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AecBaseMgd')
clr.AddReference('AecPropDataMgd')
clr.AddReference('AeccDbMgd')

# Import references from AutoCAD
from Autodesk.AutoCAD.Runtime import *
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.EditorInput import *
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.AutoCAD.Geometry import *

# Import references from Civil3D
from Autodesk.Civil.ApplicationServices import *
from Autodesk.Civil.DatabaseServices import *

# Import references for PropertySets
from Autodesk.Aec.PropertyData import *
from Autodesk.Aec.PropertyData.DatabaseServices import *

# Import references for ListDefinitions
from Autodesk.Aec.DatabaseServices import ListDefinition, ListItem, DictionaryListDefinition

adoc = Application.DocumentManager.MdiActiveDocument
editor = adoc.Editor

def listdef_uit_keuzelijstoptie(lijstnaam,lijstopties):
    with adoc.LockDocument():
        with adoc.Database as db:
            ld = None
            ldid = None
            newld = False            
            with db.TransactionManager.StartTransaction() as t:
                dld = DictionaryListDefinition(db)
                try:
                    lname = lijstnaam
                    
                    if not dld.Has(lname, t):
                        ld = ListDefinition()
                        ld.AppliesToAll = True
                        ld.AlternateName = lname
                        ld.AllowToVary = False
                        ld.Description = lname

                        dld.AddNewRecord(lname, ld)
                        newld = True
                    else:
                        ldid = dld.GetAt(lname)
                        ld = t.GetObject(ldid, OpenMode.ForWrite)
                    if newld:
                        t.AddNewlyCreatedDBObject(ld, True)

                    for optie in lijstopties:
                        first = True
                        for oid in ld.GetListItems():
                            li = t.GetObject(oid, OpenMode.ForRead)
                            if li.Name == optie:
                                first = False
                                break
                        if first:
                            ld.AddListItem(optie)
                    message = ld
                    t.Commit()
                except:
                    message = "er ging iets mis met het aanmaken van lijst" + lijstnaam
    return ld.Name
    
def dict_to_psetdef(OTL_psetinfoDict):
    """OTL Data uit een dict wegschrijven naar de propertyset definitions"""
    with adoc.LockDocument():
        with adoc.Database as db:
            with db.TransactionManager.StartTransaction() as t:
                dpsd = DictionaryPropertySetDefinitions(db)
                outputlijst = []
                psetdef_count = -1
                pdn_count = -1
                for onderdeeldict in OTL_psetinfoDict:
                    od = onderdeeldict                    
                    
                    try:
                        if od["propertysetnaam"] == "OTL_dummy":
                            pass                      
                        else:
                            if not dpsd.Has(od["propertysetnaam"], t): #propertysetnaam bestaat nog niet, maak een nieuwe
                                psdef = PropertySetDefinition()
                                psdefid = psdef.Id
                                dpsd.AddNewRecord(od["propertysetnaam"], psdef)
                                newps = True #?
                                t.AddNewlyCreatedDBObject(psdef, True)
                                    
                            else: #de propertysetnaam bestaat al in de definitions, open deze
                                psdefid = dpsd.GetAt(od["propertysetnaam"])
                                psdef = t.GetObject(psdefid, OpenMode.ForWrite)
                                
                            psdef.SetToStandard(db)
                            psdef.SubSetDatabaseDefaults(db)
                            psdef.AppliesToAll = True
                            psdef.Description = od["definitie"]
                            
                            outputlijst.append(psdef.Name)
                            
                            definitions = psdef.Definitions
                            
                            psetdef_count = psetdef_count + 1                        
                                                    
                            for attribuutdict in od["attributen"]:
                                ad = attribuutdict
                                pdn_count = pdn_count + 1
                                
                                if ad["dotnotatie_attribuutnaam"]:
                                    try:
                                        if ad["datatype_attribuut"] == "keuzelijst": #voor de keuzelijst attributen
                                            listdef_uit_keuzelijstoptie(ad["keuzelijstnaam"],ad["keuzelijstopties"])
                                            
                                            pd = PropertyDefinition()
                                            pd.Name = ad["dotnotatie_attribuutnaam"]
                                            pd.Description = ad["attribuutdefinitie"]
                                            pd.DataType = DataType.Parse(DataType, "List", True)
                                            
                                            dld = DictionaryListDefinition(db)
                                            ldid = dld.GetAt(ad["keuzelijstnaam"])
                                            pd.ListDefinitionId = ldid
                                            
                                            ldef = t.GetObject(ldid, OpenMode.ForRead)
                                            default = t.GetObject(ldef.GetListItems()[0], OpenMode.ForRead)
                                            pd.DefaultData = default.Name
                                            
                                        
                                        else: #voor alle niet keuzelijst attributen                            
                                            pd = PropertyDefinition()
                                            pd.Name = ad["dotnotatie_attribuutnaam"]
                                            pd.Description = ad["attribuutdefinitie"]
                                            pd.DataType = DataType.Parse(DataType, ad["datatype_attribuut"], True)
                                            #pd.DefaultData = ad["default_value"]
                                            
                                            if pd.DataType == DataType.Real:
                                                pd.DefaultData = -999999999.000000
                                            if pd.DataType == DataType.Integer:
                                                pd.DefaultData = -999999999
                                            elif ad["dotnotatie_attribuutnaam"] == "typeURI":
                                                pd.DefaultData = od["typeURI"]
                                            
                                        if not definitions.Contains(pd): #dubbele keys vermijden
                                            definitions.Add(pd)
                                        
                                    except:
                                        outputlijst = ["attribuut: er ging iets mis ", ad["dotnotatie_attribuutnaam"], od["propertysetnaam"],ad["attribuutdefinitie"],ad["datatype_attribuut"],ad["default_value"]]                    
                        
                    except:
                        outputlijst = ["onderdeel: er ging iets mis bij het aanmaken van volgend item: ", od["propertysetnaam"]]
                        
                t.Commit()

    info = str(pdn_count+1) + " Properties aangemaakt in " + str(psetdef_count+1) + " Propertysets"
    
    nl = "\n"
    if len(outputlijst) < 30:
        message = f"{info}{nl}Volgende sets werden aangemaakt:{nl}{nl.join(outputlijst)}"
    else:
        message = f"{info}{nl}Onder meer volgende sets werden aangemaakt:{nl}{nl.join(outputlijst[:30])}{nl}..."
        outputlijst = outputlijst[:30]
    ctypes.windll.user32.MessageBoxW(0, message, "Propertysets aangemaakt", 0)
    return [info,outputlijst]


#UITVOEREN
OUT = "GEEN propertysets aangemaakt"
OTL_datadict = IN[0]
if OTL_datadict:
    OUT = dict_to_psetdef(OTL_datadict)
    