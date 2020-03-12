from classes.Distributor_KAW import KAW
from classes.Distributor_ARN import ARN
from classes.Distributor_CPD import CPD
from classes.Distributor_AIP import AIP
from classes import Database_Ideal


print('McHenryPower')
ideal = Database_Ideal.Database()
ideal.inventory_from_database_to_solid()
