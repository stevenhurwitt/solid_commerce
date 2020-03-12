from classes import Distributor
from multiprocessing.pool import ThreadPool
from selenium.webdriver.common.action_chains import ActionChains
import requests
import os
import json
import time
from bs4 import BeautifulSoup
from classes.API_PartSmart import API as PartSmart
from threading import Lock


class KAW(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(KAW, self).__init__('KAW', "Kawasaki")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.manufacturer_file_path_root = r'T:/ebay/' + self.manufacturer_short_name
        self.user_id = None
        self.dealer_id = None
        self.password = None
        self.set_ids()
        self.updated_products = []
        self.lock = Lock()

    def set_ids(self):
        kaw_ids_filepath = os.path.abspath(os.pardir) + "McHenryPowerEquipment/data/kaw_ids.txt"
        with open(kaw_ids_filepath, 'r') as text_file:
            kaw_ids = json.load(text_file)
            self.dealer_id = kaw_ids['DealerID']
            self.user_id = kaw_ids['UserID']
            self.password = kaw_ids['Password']

    # noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
    def scrape_kawasaki_product_page(self, product_id):
        url = 'https://kawasakipower.com/ProductDetail?DealerID=' + self.dealer_id + '&UserID=' + \
                             self.user_id + '&SessionID=556425548563129&ProductID=' + product_id + '&ProductQlfr=KWE'
        data = {'DealerID': '51948',
                'UserID': 'kmc51948',
                'SessionID': '556425548563129',
                'ProductID': product_id,
                'ProductQlfr': 'KWE'}
        try:
            page = requests.post(url, data=data)
            soup = BeautifulSoup(page.text, 'lxml')
            fields = {field.get('id').split('.')[2]: field.text for field in
                      soup.find_all('span', id=lambda value: value and value.startswith('Lstd.Fields'))
                      if field.text is not ''}
            avail_dict = {'G': '5',
                          'Y': '1',
                          'R': '0'}

            product_page_object = ProductPage()
            try:
                product_page_object.base_sku = 'KAW~' + product_id
                product_page_object.product_id = product_id
                product_page_object.description = fields['LW3IDESC']
                product_page_object.cost = fields['W_PRICE']
                product_page_object.msrp = fields['FXPRICE1']
                product_page_object.ship_quantity = fields['FXQTY']
                product_page_object.tx_warehouse = int(avail_dict[fields['W_WHN']])
                product_page_object.nv_warehouse = int(avail_dict[fields['W_WHV']])
                product_page_object.ky_warehouse = int(avail_dict[fields['W_WHQ']])
                product_page_object.fl_warehouse = int(avail_dict[fields['W_WHO']])
                product_page_object.default_warehouse = fields['W_WHN']
                return product_page_object
            except KeyError:
                # try:
                #     self.log_distributor_event(
                #         self.get_log_dict(
                #             'KAW~' + product_id,
                #             'Error - No Inventory',
                #             'Catalogue Product not available at distributor'
                #         )
                #     )
                # except:
                #     print('Unable to log error for part# ' + product_id)
                print('error ' + product_id)
                return None
        except:
            return None

    # set a default inventory source to create a standardization in Distributor class for automated inventory updates
    # just set it to run one of the implemented inventory methods
    def inventory_from_default(self, inventory_objects):
        return self.inventory_from_api(inventory_objects)

    # turns inventory kawasakipower.com into inventory objects
    def inventory_from_api(self, inventory_objects):
        object_chunks = [inventory_objects[len(inventory_objects)//2:], inventory_objects[:len(inventory_objects)//2]]
        for object_chunk in object_chunks:
            with ThreadPool(25) as inventory_pool:
                inventory_pool.map(self.inventory_inquiry, object_chunk)
            print('finished threading')
        return self.updated_products

    def inventory_inquiry(self, inventory_obj):
        try:
            distributor_part = self.scrape_kawasaki_product_page(inventory_obj.sku.split('~')[1])
            if distributor_part is not None:
                inventory_obj.list_price = distributor_part.msrp
                inventory_obj.selective_quantity = distributor_part.default_warehouse
                inventory_obj.total_quantity = distributor_part.availability
                inventory_obj.minimum_order_qty = distributor_part.ship_quantity
                inventory_obj.fulfillment_source = 'DropShipper'
                inventory_obj.cost = distributor_part.cost
                inventory_obj.minimum_order_qty = distributor_part.ship_quantity
                inventory_obj.warehouse_with_inventory_dicts = distributor_part.warehouse_inventory_as_dict()
                if float(distributor_part.ship_quantity) > 1:
                    inventory_obj.unit_type = 'pack'
                else:
                    inventory_obj.unit_type = 'each'
                # with self.lock:
                self.updated_products.append(inventory_obj)
        except IndexError:
            # self.log_distributor_event(
            #     self.get_log_dict(
            #         inventory_obj.sku,
            #         'Error - No Inventory',
            #         'Catalogue Product not available at distributor'
            #     )
            # )
            print('error mapping ' + inventory_obj.sku)
            pass

    def where_used_from_api(self):
        kaw_api = API()
        product_dicts, product_id_key, filepath = self.open_selected_csv_with_primary_key()
        for product_dict in product_dicts:
            where_used = kaw_api.get_part_where_used(product_dict[product_id_key])
            product_dict['WhereUsed'] = [used.split(' ')[0] for used in where_used]
        self.write_list_of_dicts_to_csv(product_dicts, filepath.split('.')[0] + 'where_used.csv')

    def ebay_scrape_from_file(self):
        product_dicts, product_id_key, filepath = self.open_selected_csv_with_primary_key()
        ebay_scrape_dicts = [
            self.get_ebay_search_first_result_page_as_dict('kawasaki ' + product_dict[product_id_key])
            for product_dict in product_dicts
        ]
        self.write_list_of_dicts_to_csv(ebay_scrape_dicts, filepath.split('.')[0] + 'eBay_Scrape.csv')

    # noinspection SpellCheckingInspection
    def dealer_login(self, browser):
        login_page = 'https://kawasakipower.com/'
        username_xpath = 'W_USERNAME'
        password_xpath = 'LW3USRPAS'
        login_btn_xpath = 'Login'
        browser.get(login_page)
        browser.find_element_by_id(username_xpath).send_keys(self.user_id)
        browser.find_element_by_id(password_xpath).send_keys(self.password)
        browser.find_element_by_id(login_btn_xpath).click()

    def where_used_dealer_page(self, browser):
        # browser.get('https://kawasaki.partsmartweb.com/scripts/EmpartISAPI.dll?MF')
        time.sleep(3)
        element_to_hover_xpath = '/html/body/form[2]/header/nav/div/section/div/div/ul/li[2]'
        element_to_hover_over = browser.find_element_by_xpath(element_to_hover_xpath)
        hover = ActionChains(browser).move_to_element(element_to_hover_over)
        hover.perform()
        browser.find_element_by_xpath('/html/body/form[2]/header/nav/div/section/div/div/ul/li[2]/ul/li[1]/a').click()

    def where_used_drop_menu(self):
        pass

    def get_inventory_of_csv(self):
        filepath = self.get_user_file_selection()
        save_filepath = filepath.split('.')[0] + 'Inventory.csv'
        user_selection = self.get_user_csv_key_selection(filepath, 'Which field contains Product IDs? \n')
        items = self.get_csv_as_dicts_from_filepath(filepath)
        inventory = [self.scrape_kawasaki_product_page(item[user_selection]) for item in items]
        self.write_list_of_dicts_to_csv([item.as_dict() for item in inventory if item is not None], save_filepath)


class API(PartSmart):

    def __init__(self):
        super(API, self).__init__('kawasaki', 'Kawasaki', 'Kawasaki', 'test', '32', '23')
        self.session_id = 'd1f6f581-8045-414c-a454-4da9080fe23a'


class ProductPage(object):

    def __init__(self):
        self.base_sku = None
        self.product_id = None
        self.description = None
        self.cost = None
        self.msrp = None
        self.ship_quantity = None
        self.availability = None
        self.default_warehouse = None
        self.tx_warehouse = None
        self.nv_warehouse = None
        self.ky_warehouse = None
        self.fl_warehouse = None

    def as_dict(self):
        return {'Product ID': self.product_id,
                'Base SKU': self.base_sku,
                'Description': self.description,
                'Cost': self.cost,
                'MSRP': self.msrp,
                'ShipQuantity': self.ship_quantity,
                'Availability': self.availability,
                'Default': self.default_warehouse,
                'WH_KAW-TX': self.tx_warehouse,
                'WH_KAW-NV': self.nv_warehouse,
                'WH_KAW-KY': self.ky_warehouse,
                'WH_KAW-FL': self.fl_warehouse
                }

    def warehouse_inventory_as_dict(self):
        return {
            'WH_KAW-TX': self.tx_warehouse,
            'WH_KAW-NV': self.nv_warehouse,
            'WH_KAW-KY': self.ky_warehouse,
            'WH_KAW-FL': self.fl_warehouse,
            'WH_McHenry Inbound': str(int(self.ky_warehouse) + int(self.tx_warehouse))
        }
