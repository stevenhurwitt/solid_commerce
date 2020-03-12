from classes.Distributor_OW import OW


print('OW - Hydro-Gear')
ow_hyd = OW('HYD', 'Hydro-Gear')
ow_hyd.inventory_from_default_to_solid()
print('OW - OEP')
ow_oep = OW('OEP', 'Oregon')
ow_oep.inventory_from_default_to_solid()
print('OW - Maruyama')
ow_mar = OW('MAR', 'Maruyama')
ow_mar.inventory_from_default_to_solid()
print('OW - AYP')
ow_ayp = OW('AYP', 'AYP')
ow_ayp.inventory_from_default_to_solid()
print('OW - MTD')
ow_mtd = OW('MTD', 'MTD')
ow_mtd.inventory_from_default_to_solid()
