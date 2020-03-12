from classes import Distributor
from multiprocessing.pool import ThreadPool
import requests
from bs4 import BeautifulSoup
import csv
import pysftp


class ARN(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(ARN, self).__init__('ARN', "Ariens Gravely")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.username = '78919678'
        self.password = '3622ELMSTR'
        self.updated_products = []

    def inventory_from_default(self, products):
        updated_product_objects = self.inventory_from_ftp(products)
        return updated_product_objects

    def inventory_from_api(self, product_objects):
        updated_product_objects = self.inventory(product_objects)
        return [product for product in updated_product_objects if product.warehouse_with_inventory_dicts['WH_ARN-WI']]

    def inventory_from_ftp(self, product_objects):
        self.get_inventory_from_ftp(product_objects)
        return [product for product in product_objects if 'WH_ARN-WI' in product.warehouse_with_inventory_dicts.keys()]

    def inventory(self, product_objects):
        with ThreadPool(25) as inventory_pool:
            inventory_pool.map(self.inventory_inquiry, product_objects)
        return self.updated_products

    def inventory_inquiry(self, product_object):
        inventory_object = AriensProductPage()
        try:
            inventory_object.set_from_api(product_object)
        except:
            self.log_distributor_event(
                self.get_log_dict(
                    product_object.sku,
                    'Error - No Inventory',
                    'Catalogue Product not available at distributor'
                )
            )
        product_object.warehouse_with_inventory_dicts = {'WH_ARN-WI': inventory_object.total_qty_available,
                                                         'WH_McHenry Inbound': inventory_object.total_qty_available}
        self.updated_products.append(product_object)

    def get_inventory_from_ftp(self, inventory_objects):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        file_output = 'T:/ebay/arn/inventory/ftp/ARNInventory_' + self.get_time_to_minute() + '.csv'
        with pysftp.Connection("files.ariensco.com", username='mchenry', password='AriensFTP1!', cnopts=cnopts) as ftp:
            ftp.get('/PartsList/partspricelist.csv', file_output)
        inventory = {product['ProductID']: dict(product) for product in self.parse_ftp_file(file_output)}
        for inventory_object in inventory_objects:
            ariens_object = AriensProductPage()
            product_id = inventory_object.sku.split('~')[1]
            if product_id in inventory:
                try:
                    matched_item = inventory[product_id]
                    ariens_object.from_file_dict(matched_item)
                    inventory_object.warehouse_with_inventory_dicts = {
                        'WH_ARN-WI': ariens_object.total_qty_available,
                        'WH_McHenry Inbound': ariens_object.total_qty_available
                    }
                    inventory_object.cost = ariens_object.cost
                    inventory_object.list_price = ariens_object.list_price
                except KeyError:
                    if inventory_object.sku[4] == '0':
                        print(inventory_object.sku + ' not found')
                    else:
                        print(inventory_object.sku)

                    self.log_distributor_event(
                        self.get_log_dict(
                            inventory_object.sku,
                            'Error - Product',
                            'Catalogue Product not available at distributor'
                        )
                    )
                except ValueError:
                    inventory_object.warehouse_with_inventory_dicts = {
                        'WH_ARN-WI': '0',
                        'WH_McHenry Inbound': '0'
                    }
                    self.log_distributor_event(
                        self.get_log_dict(
                            inventory_object.sku,
                            'Error - File',
                            'File Format Issue'
                        )
                    )
            else:
                inventory_object.warehouse_with_inventory_dicts = {
                    'WH_ARN-WI': '0',
                    'WH_McHenry Inbound': '0'
                }
                self.log_distributor_event(
                    self.get_log_dict(
                        inventory_object.sku,
                        'Error - Unhandle Exception',
                        'Catalogue Product not available at distributor'
                    )
                )

    def parse_ftp_file(self, file):
        with open(file) as inventory_file:
            inventory = list(csv.DictReader(
                inventory_file,
                fieldnames=['ProductID', 'PartDescription', 'Qty', 'ListPrice', 'DiscountCode']
            ))
            return inventory


class AriensProductPage(object):

    def __init__(self):
        self.part_number = None
        self.part_description = None
        self.brand = None
        self.total_qty_available = None
        self.list_price = None
        self.discount_code = None
        self.stocking_code = None
        self.service_status = None
        self.standard_pack = None
        self.kenosha_qty = None
        self.part_number_replaces = []
        self.discount_percentage = .4
        self.cost = None
        
    def as_dict(self):
        return {
            'PartNumber': self.part_number,
            'PartDescription': self.part_description,
            'Brand': self.brand,
            'TotalQuantity': self.total_qty_available,
            'ListPrice': self.list_price,
            'DiscountCode': self.discount_code,
            'StockingCode': self.stocking_code,
            'ServiceStatus': self.service_status,
            'StandardPack': self.standard_pack,
            'KenoshaQuantity': self.kenosha_qty,
            'Uses': self.part_number_replaces,
            'DiscountPercentage': self.discount_percentage
        }

    def set_from_api(self, product_obj):
        product_id = product_obj.sku.split('~')[1]
        part_inquiry_url = 'https://connect.ariens.com/cgibin/gprg0248'
        data = {
            'dmcust': '78919678',
            'pswrd': '3622ELMSTR',
            'cnumber': '78919678',
            'part': product_id,
            'partid': 'A',
            'qtyrqx': '10',
            'browser': 'Netscape',
            'version': '5.0',
            'svlevl': '',
            'btn': 'Submit--%3E'
        }
        part_response = requests.post(part_inquiry_url, data=data)
        soup_list = BeautifulSoup(part_response.content, features='lxml').select('body > table')
        td_list = [td.text.strip() for td_list in [table.select('td') for table in [soup for soup in soup_list]] for td
                  in td_list]
        try:
            self.parse_td_list(td_list)
        except IndexError:
            data['partid'] = 'G'
            part_response = requests.post(part_inquiry_url, data=data)
            soup_list = BeautifulSoup(part_response.content, features='lxml').select('body > table')
            td_list = [td.text.strip() for td_list in [table.select('td') for table in [soup for soup in soup_list]] for
                       td in td_list]
            self.parse_td_list(td_list)

    def parse_td_list(self, td_list):
        part_number_field = td_list[4]
        self.part_number = part_number_field.split('\xa0')[0]
        self.part_description = part_number_field[1]
        self.brand = td_list[6]
        self.total_qty_available = td_list[10].strip('+').strip()
        self.list_price = td_list[12].strip('USD').strip()

    def from_file_dict(self, file_dict):
        if file_dict['DiscountCode'] == '':
            file_dict['DiscountCode'] = 'blank'
        discount = {
            'blank': .6,
            'A': .75,
            'E': 1
        }
        self.part_number = file_dict['ProductID']
        self.brand = 'Ariens'
        self.total_qty_available = file_dict['Qty']
        self.list_price = file_dict['ListPrice']
        self.cost = str(float(file_dict['ListPrice']) * discount[file_dict['DiscountCode']])
