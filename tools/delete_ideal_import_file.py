import os
import datetime

# ideal_import_directory = '\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks'
ideal_import_directory = 'S:/ideal for windows/ShipWorks/'
ideal_import_name = 'IdealImport.csv'
ideal_processed_filepath = ('S:/ideal for windows/ShipWorks/Imported Orders/IdealImport_' +
                            str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + '.csv')
# ideal_processed_filepath = ('\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks/Imported Orders/IdealImport_' +
#                             str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + '.csv')
file_names = os.listdir(ideal_import_directory)
if ideal_import_name in file_names:
    os.rename(ideal_import_directory + ideal_import_name, ideal_processed_filepath)
