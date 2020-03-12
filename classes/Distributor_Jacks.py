from classes import Distributor
import requests
from multiprocessing.pool import ThreadPool


class JACKS(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        # noinspection SpellCheckingInspection
        super(STE, self).__init__('JACK', "JACKS")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.updated_products = []

    def inventory_from_default(self, products):
        inventory = self.inventory_from_api(products)
        return inventory

    def inventory_from_api(self, products):
        with ThreadPool(2) as inventory_pool:
            inventory_pool.map(self.inventory_inquiry, products)
        return self.updated_products

    def inventory_inquiry(self, product):
        ste_info = self.get_item_json(product.manufacturer_product_id)
        if ste_info is not None:
            cleaned_info = self.api_clean_item_for_inventory(ste_info)
            if cleaned_info is not None:
                product.list_price = cleaned_info['MSRP']
                product.total_quantity = cleaned_info['Qty']
                product.cost = cleaned_info['Cost']
                product.warehouse_with_inventory_dicts = {
                    'WH_STE-IN': cleaned_info['Qty'],
                    'WH_McHenry Inbound': cleaned_info['Qty']
                }
                self.updated_products.append(product)

    def generate_listings_from_file(self):
        csv_file, primary_key, filepath = self.open_selected_csv_with_primary_key()
        search_results = [self.get_item_json(product[primary_key]) for product in csv_file]
        listings = [self.api_clean_item_for_listing(product) for product in search_results if product is not None]
        self.write_odict_to_csv_to_filepath([listing for listing in listings if listing is not None], filepath.split('.')[0] + '_Listings.csv')

    def get_item_json(self, product_id):
        # noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
        product_url = ('https://www.jackssmallengines.com/manufacturer/ariens'
                       'country=US&'
                       'fieldset=search&'
                       'language=en&'
                       'limit=5&'
                       'pricelevel=19&'
                       'q=' + product_id.strip('[').strip(']') + '&'
                       'sort=custitem_sca_parttype%3Aasc%2Crelevance%3Aasc')
        try:
            response = requests.get(product_url)
            if len(response.json()['items']) > 0:
                product_json = response.json()['items'][0]
                try:
                    return product_json
                except KeyError:
                    product_json = response.json()['items'][1]
                    try:
                        return product_json
                    except KeyError:
                        # noinspection SpellCheckingInspection
                        print('KEYERROR ' + product_id)
            else:
                print(product_id + ' Not Found')
        except:
            print(product_id + ' No Response')

    def api_clean_item_for_inventory(self, item_dict):
        try:
            # noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
            return{
                'Cost': item_dict['pricelevel19'],
                'Qty': str(int(item_dict['quantityavailable'])),
                'MSRP': item_dict['onlinecustomerprice']
            }
        except KeyError:
            pass

    def api_clean_item_for_listing(self, item_dict):
        try:
            # noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
            return{
                'Cost': item_dict['pricelevel19'],
                'UPC': item_dict['upccode'],
                'MSRP': item_dict['onlinecustomerprice'],
                'Model Number': item_dict['itemid'],
                'Product Weight': '',
                'Product Height': '',
                'Product Width': '',
                'Product Length': '',
                'Product Name': 'Stens OEM Replacement ' + item_dict['displayname'] + ' part# ' + item_dict['itemid'],
                'Apply eBay Template': '',
                'PO Sources': '|McHenry Power|McHenry Inbound',
                'eBay Description': self.get_ebay_description_from_json(item_dict),
                'Description': self.get_ebay_description_from_json(item_dict),
                'Product Attribute:MPN': item_dict['itemid'],
                'Product Attribute:Brand': 'Stens',
                'Product Custom SKU': 'STE~' + item_dict['itemid'],
                'Warehouse ID': 'STE~' + item_dict['itemid'],
                'Manufacturer': 'Stens',
                'Image File': item_dict['itemimages_detail']['01']['Z']['url'],
                'Warehouse Name': 'McHenry Power',
                'List Name': 'eBayUS',
                'Fixed Price': '',
                'Fees': '',
                'Profit': '',
                'Results': ''
            }
        except KeyError:
            pass

    def get_ebay_description_from_json(self, item_dict):
        # noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
        return (
            '<h2>' + item_dict['displayname'] + '</h2><br /><br />'
            '<h2>Replaces Part numbers</h2><br />' +
            item_dict['custitem_sca_comp_part_no'] + ' ' + item_dict['custitem_sca_oem_part_no'] + '<br /><br />' +
            '<h2>Compatible Brands</h2><br />' +
            item_dict['custitem_sca_brand_search']
        )
