# Importeer de benodigde modules
import clr
import ctypes

clr.AddReference('AcMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AecBaseMgd')
clr.AddReference('AecPropDataMgd')
clr.AddReference('AeccDbMgd')

from Autodesk.Civil.DatabaseServices import *
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.Civil.Runtime import *
from Autodesk.Aec.PropertyData.DatabaseServices import *
from Autodesk.Aec.DatabaseServices import ListDefinition, ListItem, DictionaryListDefinition

m = ctypes.windll.user32

geometrieobjecten = IN[0] #(lijst van Dynamo geometrie objecten)
OTL_datadict = IN[1] #lijst van dictionaries met OTL data, bijv. "psetnaam" en andere eigenschappen

#niet otl data verwijderen uit dict
for d in OTL_datadict:
    del d["coordinates"]
    del d["geometry"]
        
# Haal het actieve document en de database op
adoc = Application.DocumentManager.MdiActiveDocument
db = adoc.Database
editor = adoc.Editor

# Lijst om de ID's van de output in op te slaan
eindlijst = []
messagelist = []
success_count = 0
prop_count = 0
ontbrekende_prop = 0
foutekeyvaluelijst = []
toegevoegdeKLopties = []
nl = '\n'

# Start een transactie
if geometrieobjecten:
    with db.TransactionManager.StartTransaction() as tr:
        try:
            # Haal de PropertySetDefinitionManager op
            dpsd = DictionaryPropertySetDefinitions(db)
            dld = DictionaryListDefinition(db)
            
            # Loop door elk object en de bijbehorende data
            for i, obj in enumerate(geometrieobjecten):
                # Haal de data op die hoort bij het huidige object
                if i >= len(OTL_datadict):
                    message = "FOUT: Onvoldoende data in OTL_datadict voor alle objecten."
                    messagelist.append(message)
                    break
                
                OTLdata = OTL_datadict[i]
                psetnaam = OTLdata.get("psetnaam")
                
                if psetnaam is None:
                    message = f"FOUT: Geen 'psetnaam' gevonden voor object {i}."
                    messagelist.append(message)
                    continue
    
                # Zoek de PropertySetDefinition op
                psdefid = dpsd.GetAt(psetnaam)
                psdef = tr.GetObject(psdefid, OpenMode.ForRead)
                propertydefinitions = psdef.Definitions
                
                if psdefid.IsNull:
                    message = f"FOUT: PropertySetDefinition {psetnaam} niet gevonden."
                    messagelist.append(message)
                    continue
    
                # haal id uit dynamo object
                try:
                    h = obj.Handle
                    ObjId = obj.InternalObjectId
                    aeccObj = tr.GetObject(ObjId, OpenMode.ForWrite)    
    
                except Exception as e:
                    message = f"FOUT: Ongeldige object met handle {h}: {str(e)}"
                    messagelist.append(message)
                    continue
                
                if aeccObj:
                    # Koppel de PropertySet aan het Civil 3D object
                    PropertyDataServices.AddPropertySet(aeccObj, psdefid)                                 
                    # Haal de gekoppelde pset op voor dit object
                    propertyset = PropertyDataServices.GetPropertySet(aeccObj, psdefid)
                    psetn = propertyset.Open(OpenMode.ForWrite)
                    propertysetnaam = psetn.PropertySetDefinitionName
                    psetdatacoll = psetn.PropertySetData
                        
                    if psetdatacoll is not None:
                        # Loop door de dictionary en stel de waarden in
                        for propNaam, value in OTLdata.items():
                            # Sla 'psetnaam' over, deze is al verwerkt
                            if propNaam == "psetnaam":
                                continue
                            # Sla lege waarden over
                            if not value:
                                continue
                            # Stel default lege waarde in
                            convertvalue = ""
                            
                            # Kijk of property bestaat
                            try:
                                propId = psetn.PropertyNameToId(propNaam)
                            except Exception as e:
                                ontbrekende_prop += 1
                                if [psetnaam,propNaam,"property ontbreekt"] not in foutekeyvaluelijst: 
                                    foutekeyvaluelijst.append([psetnaam,propNaam,"property ontbreekt"])
                                continue
                                
                            try:
                                prop = psetdatacoll[propId]
                                propType = prop.DataType
                                #waarde omzetten obv datatype van property in propertyset
                                if propType == 0:
                                    #integer
                                    convertvalue = int(value)
                                elif propType == 1:
                                    #getal
                                    convertvalue = float(value)
                                elif propType == 6:
                                    #keuzelijst
                                    if value == "":
                                        convertvalue = "-"
                                    elif value == "true":
                                        convertvalue = "True"
                                    elif value == "false":
                                        convertvalue = "False"
                                    elif value == True:
                                        convertvalue = "True"
                                    elif value == False:
                                        convertvalue = "False"
                                    else: 
                                        convertvalue = str(value)
    
    
                                    #haal de mogelijke keuzes op uit de listdefinitie
                                    #als de keuzelijstoptie niet bestaat, creer een nieuwe
                                    propdef = propertydefinitions[propId]
                                    ldefid = propdef.ListDefinitionId
                                    #open de lijstdefinitie en voeg toe indien nodig
                                    ld = tr.GetObject(ldefid, OpenMode.ForWrite)
                                    first = True                               
                                    for oid in ld.GetListItems(): #loop door de keuzelijstopties
                                        li = tr.GetObject(oid, OpenMode.ForRead)
                                        if li.Name == convertvalue:
                                            first = False
                                            break
                                    if first: #Als de opties niet bestaat, maak een nieuwe aan
                                        if convertvalue:
                                            if [psetnaam,propNaam,convertvalue] not in toegevoegdeKLopties:
                                                toegevoegdeKLopties.append([psetnaam,propNaam,convertvalue])
                                                ld.AddListItem(value)
                                    
                                else:
                                    convertvalue = str(value)
                                    
                                #Value invullen
                                prop.SetData(convertvalue)
                                prop_count += 1
                                
                            except Exception as e:
                                if [psetnaam,value,propNaam,"Ongeldige waarde"] not in foutekeyvaluelijst:
                                    foutekeyvaluelijst.append([psetnaam,value,propNaam,"Ongeldige waarde"])
                                continue
                    
                    eindlijst.append(obj)
                    success_count += 1
                    
            if toegevoegdeKLopties:
                printableklo = nl.join([str(ele) for ele in toegevoegdeKLopties])
                m.MessageBoxW(0, f"Volgende keuzelijstopties werden toegevoegd: {nl}{printableklo}", "KeuzelijstOpties toegevoegd", 0)
                
            if foutekeyvaluelijst:
                printablekvl = nl.join([str(ele) for ele in foutekeyvaluelijst])
                if ontbrekende_prop:
                    message = f"Volgende attributen konden NIET worden ingevuld, {nl}kijk na of deze bestaan in de propertyset definities:{nl}{nl}{printablekvl}"
                else:
                    message = f"Volgende attributen konden NIET worden ingevuld:{nl}{nl}{printablekvl}"
                messagelist.append(message)
                
            if success_count > 0:
                message = f"{nl}TAAK VOLTOOID. {success_count} objecten aangemaakt en {prop_count} properties ingevuld."
                messagelist.append(message)                
                    
        except Exception as ex:
            message = f"Er is een FOUT opgetreden: {str(ex)}"
            messagelist.append(message)
    
        tr.Commit()

else:#indien geen geometrieobjecten
    m.MessageBoxW(0, "GEEN objecten aangemaakt", "OTL attributen invullen", 0)
    
if messagelist:
    m.MessageBoxW(0, str(nl.join(messagelist)), "OTL attributen invullen", 0)
    
# Wijs de output toe aan de OUT variabele
OUT = eindlijst