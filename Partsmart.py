from classes import Distributor_KAW
from classes import Distributor_PED
from classes import Distributor_GE
from classes import Distributor_ARN


# kaw = Distributor_KAW.KAW('KAW', 'Kawasaki')
# kaw.get_partsmart_part_where_used_from_file()
# ech = Distributor_GE.GE('ECH', 'Echo/Shindaiwa')
# ech.get_partsmart_part_where_used_from_file()
brs = Distributor_PED.PED('BRS', 'Briggs & Stratton')
brs.get_partsmart_part_where_used_from_file()
# arn = Distributor_ARN.ARN('ARN', 'Ariens')
# arn.get_partsmart_part_where_used_from_file()
