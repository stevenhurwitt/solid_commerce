from classes.Distributor_GE import GE

print('Echo')
ech = GE('ECH', 'Echo')
ech.inventory_from_file_to_xml()
print('Billy Goat')
bil = GE('BIL', 'Billy Goat')
bil.inventory_from_file_to_xml()