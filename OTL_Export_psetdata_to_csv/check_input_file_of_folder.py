# Load the Python Standard and DesignScript Libraries
import os
import ctypes


#INPUT
input_file_of_folder = IN[0]

go = 0
message = ""
m = ctypes.windll.user32
nl = '\n'


if input_file_of_folder:
    if os.path.isdir(input_file_of_folder):#bij folder
        message = f"Correcte input, CSV bestanden worden geschreven in de folder: {nl}{str(input_file_of_folder)}"
        go = 1
                
    elif os.path.isfile(input_file_of_folder):#bij file
        message = f"Opgegeven pad is het pad naar een file: {nl}{str(input_file_of_folder)}{nl}{nl}Geef een folder waar de file mag worden geschreven,{nl}gebruik daarvoor de 'Directory Path' node"
        
    else:
        message = f"Geen bruikbare input:{nl}{str(input_file_of_folder)}{nl}{nl}Geef een locatie op om de csv files naar te schrijven,{nl}gebruik daarvoor de 'Directory Path' node"

else:
    message = f"Geen bruikbare input:{nl}{str(input_file_of_folder)}{nl}{nl}Geef een locatie op om de csv files naar te schrijven,{nl}gebruik daarvoor de 'Directory Path' node"

m.MessageBoxW(0, message, "OTL_Export psetdata to CSV", 0)
OUT = go