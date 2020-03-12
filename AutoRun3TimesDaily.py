from classes.Distributor_AIP import AIP
from classes import Database_Ideal


# try:
print('AIP Inventory')
aip = AIP('AIP', 'AIP')
aip.inventory_from_default_to_solid()
# except:
#     pass
# try:
#     print('McHenryPower')
#     ideal = Database_Ideal.Database()
#     ideal.inventory_from_database_to_solid()
# except:
#     pass
