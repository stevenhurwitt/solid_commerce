import Distributor_GE as dge


print('Billy Goat')
bil = dge.GE('BIL', 'Billy Goat')
print('ran distributor...')
bil.inventory_from_default_to_solid()
print('ran inventory.')
print('Echo')
ech = dge.GE('ECH', 'Echo')
print('ran distributor...')
ech.inventory_from_default_to_solid()
print('ran inventory.')
