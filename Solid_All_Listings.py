from classes.SolidCommerce import API as SolidAPI


solid_api = SolidAPI()
items = list(solid_api.get_all_inventory_items_from_list('eBayUS'))
print(items[-1].as_dict())
