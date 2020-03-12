from classes.Distributor_PED import PED


print('Briggs')
brs = PED('BRS', 'Briggs & Stratton')
brs.inventory_from_default_to_solid()
print('Oregon')
oep = PED('OEP', 'Oregon')
oep.inventory_from_default_to_solid()
