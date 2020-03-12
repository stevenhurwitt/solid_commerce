from classes.Distributor_OW import OW

print('OW - Maruyama')
ow_mar = OW('MAR', 'Maruyama')
ow_mar.inventory_from_file_to_xml()
print('OW - AYP')
ow_ayp = OW('AYP', 'AYP')
ow_ayp.inventory_from_file_to_xml()
print('OW - Hydro-Gear')
ow_hyd = OW('HYD', 'Hydro-Gear')
ow_hyd.inventory_from_file_to_xml()
print('OW - MTD')
ow_mtd = OW('MTD', 'MTD')
ow_mtd.inventory_from_file_to_xml()