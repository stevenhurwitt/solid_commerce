from classes.Distributor_STE import STE as Distributor
import json


distributor = Distributor('STE', 'Stens')
distributor.inventory_from_default_to_solid()
