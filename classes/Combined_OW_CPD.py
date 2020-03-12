from classes.Distributor_CPD import CPD
from classes.Distributor_OW import OW
from classes import Distributor
import copy


class Combined(Distributor.Distributor):

    def __init__(self, mfr_short_name, mfr_long_name):
        super(Combined, self).__init__('CMB', 'Combined')
        self.manufacturer_short_name = mfr_short_name
        self.manufacturer_long_name = mfr_long_name

    def get_cpd_inventory_from_default(self, product_objects):
        cpd = CPD(self.manufacturer_short_name, self.manufacturer_long_name)
        return cpd.inventory_from_default(product_objects)

    def get_ow_inventory_from_default(self, product_objects):
        ow = OW(self.manufacturer_short_name, self.manufacturer_long_name)
        return ow.inventory_from_default(product_objects)

    def inventory_from_default(self, inventory_objects):
        ow_inventory = self.get_ow_inventory_from_default(copy.deepcopy(inventory_objects))
        cpd_inventory = self.get_cpd_inventory_from_default(copy.deepcopy(inventory_objects))
        combined_inventory = self.combine_inventory(ow_inventory, cpd_inventory)
        return combined_inventory

    def combine_inventory(self, ow_inventory, cpd_inventory):
        return [
            self.combine_inventory_dicts(
                ow_product,
                [cpd_product for cpd_product in cpd_inventory if cpd_product.sku == ow_product.sku][0]
            ) for ow_product in ow_inventory
        ]

    def combine_inventory_dicts(self, ow_inventory_obj, cpd_inventory_obj):
        try:
            combined_dict = {
                'WH_OW-MO': ow_inventory_obj.warehouse_with_inventory_dicts['WH_OW-MO'],
                'WH_CPD-WI': cpd_inventory_obj.warehouse_with_inventory_dicts['WH_CPD-WI'],
                'WH_McHenry Inbound': str(
                    int(ow_inventory_obj.warehouse_with_inventory_dicts['WH_OW-MO']) +
                    int(cpd_inventory_obj.warehouse_with_inventory_dicts['WH_CPD-WI'])
                )
            }
            ow_inventory_obj.warehouse_with_inventory_dicts = combined_dict
            return ow_inventory_obj
        except KeyError:
            combined_dict = {
                'WH_OW-MO': ow_inventory_obj.warehouse_with_inventory_dicts['WH_OW-MO'],
                'WH_CPD-WI': '0',
                'WH_McHenry Inbound': ow_inventory_obj.warehouse_with_inventory_dicts['WH_OW-MO']
            }
            ow_inventory_obj.warehouse_with_inventory_dicts = combined_dict
            return ow_inventory_obj
