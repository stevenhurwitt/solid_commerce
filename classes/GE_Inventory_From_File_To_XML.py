import Distributor_GE as dge

print('Echo')
ech = dge.GE('ECH', 'Echo')
print('ran distributor...')
ech.inventory_from_file_to_xml()
print('ran inventory.')

print('Billy Goat')
bil = dge.GE('BIL', 'Billy Goat')
print('ran distributor...')
bil.inventory_from_file_to_xml()
print('ran inventory.')