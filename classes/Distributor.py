from SolidCommerce import API as SolidAPI
import SolidCommerce
import Products
import Inventory
import eBay
from eBay import API as eBayAPI
import API_PartSmart
from abc import ABCMeta, abstractmethod
from Tkinter import *
import Tkinter as tk
import csv
import os.path
import time
from lxml import etree as element_tree
from collections import defaultdict
from bs4 import BeautifulSoup
import json
import re
import xlrd
from pathlib import Path
import requests
import ftplib
import ImageTools
from io import BytesIO


class Distributor():

    __metaclass__ = ABCMeta
    @abstractmethod
    def __init__(self, distributor_short_name, distributor_long_name):
        self.distributor_short_name = distributor_short_name
        self.distributor_long_name = distributor_long_name
        self.manufacturer_short_name = ''
        self.manufacturer_long_name = ''
        self.username = ''
        self.password = ''
        self.distributor_file_path_root = r'T:/ebay/' + self.distributor_short_name
        self.manufacturer_file_path_root = None
        self.temp_filepath = ''

    def get_manufacturer_file_path_root(self):
        return r'T:/ebay/' + self.manufacturer_short_name

    # Requires some form of Distributor Inventory Interface In Child Object
    def get_distributor_inventory(self, inventory_method):
        products = self.products_from_productids_csv_as_list_of_dicts()
        inventory_objects = [self.productids_csv_dict_as_inventory_object(product_dict)
                             for product_dict in products]
        inventory = inventory_method(inventory_objects)
        return inventory

    def get_distributor_inventory_for_solid(self, inventory_method):
        solid_api = SolidAPI()
        products = solid_api.get_products_from_file_by_mfr(self.manufacturer_short_name)
        inventory_objects = [
            self.productids_solid_csv_dict_as_inventory_object(product_dict) for product_dict in products
        ]
        inventory = inventory_method(inventory_objects)
        return inventory

    def inventory_from_file_to_csv(self):
        inventory = self.get_distributor_inventory(self.inventory_from_file)
        self.write_inventory_to_csv(inventory)

    def inventory_from_web_to_csv(self):
        inventory = self.get_distributor_inventory(self.inventory_from_web)
        self.write_inventory_to_csv(inventory)

    def inventory_from_api_to_csv(self):
        inventory = self.get_distributor_inventory(self.inventory_from_api)
        self.write_inventory_to_csv(inventory)

    def inventory_from_default_to_solid(self):
        inventory = self.get_distributor_inventory_for_solid(self.inventory_from_default)
        solid_api = SolidAPI()
        solid_api.upload_list_items([product.as_dict_for_solid() for product in inventory])

    # Implement in all children if possible
    def get_tracking(self):
        raise NotImplementedError

    def get_tracking_input_date(self):
        raise NotImplementedError

    def get_dealer_inventory(self):
        raise NotImplementedError

    def where_used_drop_menu(self):
        raise NotImplementedError

    def where_used_dealer_page(self, browser):
        raise NotImplementedError

    def dealer_login(self, browser):
        raise NotImplementedError

    # Implemented by Child Classes to interface with Parent Class for Sixbit
    def inventory_from_file(self, products):
        raise NotImplementedError

    def inventory_from_web(self, products):
        raise NotImplementedError

    def inventory_from_api(self, products):
        raise NotImplementedError

    # set this in child to return one of the above 3 methods that has already been implemented in child
    def inventory_from_default(self, products):
        raise NotImplementedError

    def get_products_from_file_by_mfr(self):
        solid_api = SolidAPI()
        products = solid_api.get_products_from_file_by_mfr(self.manufacturer_short_name)
        return products

    @staticmethod
    def get_time_to_second():
        return time.strftime('%m%d%Y%I%M%S')

    @staticmethod
    def get_time_to_minute():
        return time.strftime('%m%d%Y%I%M')

    @staticmethod
    def get_time_day():
        return time.strftime('%m%d%Y')

    @staticmethod
    def get_time_year():
        return time.strftime('%Y')

    def get_log_dict(self, sku, status, notes):
        return{
            'Timestamp': self.get_time_to_second(),
            'SKU': sku,
            'Status': status,
            'Notes': notes
        }

    @staticmethod
    def get_image_server_session():
        return ftplib.FTP('ftp.PowerEquipDeals.com', 'PEDAdmin', 'YardNeedsRaking10')

    def save_image_url_to_ftp(self, img_url, file_name, session):
        ftp_path = 'ImageLib/' + self.manufacturer_long_name + '/'
        try:
            file = ImageTools.resize_url_for_ebay(img_url)
            temp_picture = BytesIO()
            file.save(temp_picture, 'jpeg')
            temp_picture.seek(0)
            session.storbinary("STOR " + ftp_path + file_name, temp_picture)
            file.close()
            return 'content.powerequipdeals.com/ImageLib/' + self.manufacturer_long_name + '/' + file_name
        except:
            return ''

    def save_image_urls_to_ftp(self, list_of_image_urls):
        session = self.get_image_server_session()
        new_image_links = [
            self.save_image_url_to_ftp(image_url, image_url.split('/')[-1], session) for image_url in list_of_image_urls
        ]
        session.quit()
        return new_image_links

    def save_image_urls_update_dict(self, dict_headers, product_dict):
        session = self.get_image_server_session()
        for dict_header in dict_headers:
            if product_dict[dict_header] != '':
                product_dict[dict_header] = self.save_image_url_to_ftp(
                    product_dict[dict_header], product_dict[dict_header].split('/')[-1], session
                )
        return product_dict

    def load_csv_images_to_ftp(self):
        filepath = self.get_user_file_selection()
        products = self.get_csv_as_dicts_from_filepath(filepath)
        key_selections = []
        while True:
            key_selections.append(self.get_user_csv_key_selection(
                filepath, 'Select the Column Containing an Image URL: ')
            )
            keep_going = input('[1] Yes\n[2] No\nAdditional Selections?: ')
            if keep_going != '1':
                break
        updated_products = [self.save_image_urls_update_dict(key_selections, product) for product in products]
        self.write_list_of_dicts_to_csv(updated_products, filepath.split('.')[0] + '_updated.csv')

    def log_distributor_event(self, event_dict):
        distributor_error_filepath = self.distributor_file_path_root + '/logs/log_' + self.get_time_day() + '.csv'
        if not Path(distributor_error_filepath).is_file():
            with open(distributor_error_filepath, 'w', newline='') as log_file:
                keys = event_dict.keys()
                dict_writer = csv.DictWriter(log_file, keys)
                dict_writer.writeheader()
        with open(distributor_error_filepath, 'a', newline='') as log_file:
            keys = event_dict.keys()
            dict_writer = csv.DictWriter(log_file, keys)
            dict_writer.writerow(event_dict)

    @staticmethod
    def ebay_update_image_and_description_solid(updated_products):
        solid_api = SolidAPI()
        for updated_product in updated_products:
            solid_api.update_product(updated_product.as_product_xml_string)

    def ebay_api_competitor_inquiry_for_brand_for_zip(self, zip_code):
        solid_api = SolidAPI()
        ebay_api = eBayAPI()
        filepath = (
                self.get_manufacturer_file_path_root() + '/data/' + self.get_time_year() +
                '/ebay_competitor_scrape' + self.get_time_to_minute() + '.csv')
        solid_products = solid_api.get_products_from_file_by_mfr(self.manufacturer_short_name)
        cleaned_results = []
        for product in solid_products:
            try:
                cleaned_results.append(
                    self.clean_ebay_search_result(
                        ebay_api.search_item(
                            self.manufacturer_long_name + ' ' + product['Model Number'], zip_code)['Item']
                    )
                )
            except Exception as error:
                print(error)
        self.write_list_of_dicts_to_csv(cleaned_results, filepath)

    def ebay_api_competitor_inquiry_for_zip_from_file(self, zip_code):
        ebay_api = eBayAPI()
        filepath = (
                self.get_manufacturer_file_path_root() + '/data/' + self.get_time_year() +
                '/ebay_competitor_scrape' + self.get_time_to_minute() + '.csv')
        cleaned_results = []
        products, product_id, products_filepath = self.open_selected_csv_with_primary_key()
        for product in products:
            try:
                item = ebay_api.search_item(
                    self.manufacturer_long_name + ' ' + product[product_id], zip_code)
                if item is not None:
                    cleaned_results.append(self.clean_ebay_search_result(item['Item']))
                else:
                    continue
            except Exception as error:
                print(error)
        self.write_list_of_dicts_to_csv(cleaned_results, filepath)

    @staticmethod
    def ebay_api_get_shipping_cost(item_id, zip_code):
        ebay_api = eBayAPI()
        shipping_item = ebay_api.get_shipping_cost(item_id, zip_code)
        print(shipping_item)

    @staticmethod
    def clean_ebay_search_result(item_dict):
        clean_dict = {
            'ShippingServiceCost': item_dict['Shipping']['ShippingCostSummary']['ShippingServiceCost']['value'],
            'ShippingType': item_dict['Shipping']['ShippingCostSummary']['ShippingType'],
            'ConditionDisplayName': item_dict['ConditionDisplayName'],
            'ItemID': item_dict['ItemID'],
            'ViewItemURLForNaturalSearch': item_dict['ViewItemURLForNaturalSearch'],
            'ListingType': item_dict['ListingType'],
            'Seller': item_dict['Seller']['UserID'],
            'CurrentPrice': item_dict['CurrentPrice'],
            'QuantitySold': item_dict['QuantitySold'],
            'Title': item_dict['Title'],
            'ItemSpecifics': item_dict['ItemSpecifics']['NameValueList'],
            'Brand': None,
            'MPN': None
        }
        for specific in item_dict['ItemSpecifics']['NameValueList']:
            if specific['Name'].lower() == 'brand':
                clean_dict['Brand'] = specific['Value']
            if specific['Name'].lower() == 'mpn':
                clean_dict['MPN'] = specific['Value']
        return clean_dict

    @staticmethod
    def ebay_get_top_search_result_id(search_string):
        search_response = requests.get('https://www.ebay.com/sch/i.html?_nkw=' + '+'.join(search_string.split(' ')))
        soup = BeautifulSoup(search_response.text, features='lxml')
        top_search_result = soup.select('li.s-item')[0]
        item_number = top_search_result.select('a')[0]['href'].split('/')[5].split('?')[0]
        return item_number

    @staticmethod
    def ebay_get_shipping_from_id_and_zip(ebay_id, zip_code):
        request_url = (
                'https://www.ebay.com/itm/getrates?item=' +
                ebay_id +
                '&quantity=1&country=1&zipCode=' +
                zip_code +
                '&co=0&cb=jQuery1707594462671457922_1557170521467'
        )
        shipping_response = requests.get(request_url)
        shipping_soup = BeautifulSoup(shipping_response.text, features='lxml')
        try:
            script_txt = shipping_soup.script.text.replace('\\"', '')
            script_soup = BeautifulSoup(script_txt, features='lxml')
            try:
                shipping_element = script_soup.select('#fshippingCost span')[0]
                shipping = shipping_element.text.strip('$')
                return {'Shipping To ' + zip_code: shipping}
            except IndexError:
                return {'Shipping To ' + zip_code: 'Free'}
        except AttributeError:
            pass
        except TypeError:
            pass

    def ebay_parse_item_page(self, item_id):
        item_page_response = requests.get('https://www.ebay.com/itm/' + item_id)
        ebay_page = eBay.ProductPage()
        product_soup = BeautifulSoup(item_page_response.text, 'lxml')
        ebay_page.set_properties_from_soup(product_soup)
        shipping = {
            self.ebay_get_shipping_from_id_and_zip(item_id, '63101'),
            self.ebay_get_shipping_from_id_and_zip(item_id, '60050'),
            self.ebay_get_shipping_from_id_and_zip(item_id, '90210')
        }
        return {ebay_page.as_dict(), shipping}

    def ebay_search_for_products(self):
        products = self.get_products_from_file_by_mfr()
        scraped_products = []
        for product_dict in products:
            try:
                scraped_products.append(self.ebay_search_for_product(product_dict))
            except AttributeError:
                pass
            except TypeError:
                pass
            except IndexError:
                pass
        self.write_list_of_dicts_to_csv(
            scraped_products,
            'T:/ebay/' + self.manufacturer_short_name + '/data/ebay_scrapes/'
            'eBaySearchScrapes.' + self.get_time_day() + '.csv'
        )

    def ebay_search_for_product(self, product_dict):
        parsed_item_page = self.ebay_parse_item_page(
            self.ebay_get_top_search_result_id(
                self.manufacturer_long_name + ' ' + product_dict['SKU'].split('~')[1]
            )
        )
        return {product_dict, parsed_item_page}

    @staticmethod
    def get_order_from_solid_by_ebay_number(po_number):
        search_filter = SolidCommerce.OrderSearchFilter()
        search_filter.search_type = 'MarketOrderNumber'
        search_filter.search_value = po_number
        search_filter.page = '1'
        search_filter.records_per_page_count = '1000'
        search_filter_element = search_filter.as_element()
        solid_api = SolidAPI()
        order = solid_api.search_orders_v6(search_filter_element)
        return order

    def get_partsmart_part_where_used(self, product_id):
        partsmart_api = self.get_partsmart_session()
        return partsmart_api.get_part_where_used(product_id)

    def get_partsmart_part_where_used_from_file(self):
        partsmart_api = self.get_partsmart_session()
        filepath = self.get_user_file_selection()
        save_filepath = re.split('.csv', filepath)[0] + '_WhereUsed.csv'
        reader = csv.DictReader(open(filepath, encoding="utf8"))
        parts_with_where_used = partsmart_api.get_part_where_used_from_list(reader)
        parts_with_where_used_html = []
        for part in parts_with_where_used:
            part.update({'WhereUsed': self.get_where_used_html_from_list(part['WhereUsed'])})
            parts_with_where_used_html.append(part)
        self.write_odict_to_csv_to_filepath(parts_with_where_used_html, save_filepath)

    def get_partsmart_session(self):
        ids_filepath = os.path.abspath(os.pardir) + 'McHenryPowerEquipment/data/' + \
                       self.manufacturer_short_name + '_ids.txt'
        with open(ids_filepath, 'r') as text_file:
            ids = json.load(text_file)
        partsmart_api = API_PartSmart.API(ids['PS_StoreName'],
                                          ids['PS_App'],
                                          ids['PS_LoginID'],
                                          ids['PS_LoginPassword'],
                                          ids['PS_CatalogID'],
                                          ids['PS_DatabaseID'])
        partsmart_api.get_session()
        return partsmart_api

    @staticmethod
    def get_where_used_html_from_list(where_used_list):
        where_used_string = '"<div><h2>Where Used: </h2><br /><table><tbody>'
        cell_index = 1
        cells_per_row = 4
        if len(where_used_list) < 2:
            return '<div><h2>Where Used: </h2>' + where_used_list[0] + '</div>'
        for where_used in where_used_list:
            if cell_index == 1:
                where_used_string += '<tr>'
            where_used_string += '<td>' + where_used + '</td>'
            cell_index += 1
            if cell_index == cells_per_row:
                where_used_string += '</tr>'
                cell_index = 1
        if cell_index != 1:
            where_used_string += '</tr>'
        where_used_string += '</tbody></table></div>"'
        return where_used_string

    # Returns filepath of users file selection
    @staticmethod
    def get_user_file_selection():
        root = tk.Tk()
        root.withdraw()
        return filedialog.askopenfilename()

    @staticmethod
    def get_csv_as_dicts_from_filepath(filepath):
        return csv.DictReader(open(filepath, encoding="utf8", errors="ignore"))

    def open_selected_csv_with_primary_key(self):
        filepath = self.get_user_file_selection()
        primary_key = self.get_user_csv_key_selection(filepath, 'Pick Primary Column: ')
        csv_file = list(self.get_csv_as_dicts_from_filepath(filepath))
        return csv_file, primary_key, filepath

    @staticmethod
    def get_xls_as_dicts_from_filepath(file_path):
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]
        dict_list = []
        for row_index in range(1, sheet.nrows):
            d = {keys[col_index]: sheet.cell(row_index, col_index).value
                 for col_index in range(sheet.ncols)}
            dict_list.append(d)
        return dict_list

    # Return a user selected Product ID with weight
    @staticmethod
    def get_user_csv_key_selection(filepath, prompt_text):
        with open(filepath, encoding="utf8") as file:
            reader = csv.DictReader(file)
            field_names = reader.fieldnames
            field_names_as_menu_string = ''
            i = 1
            for field_name in field_names:
                field_names_as_menu_string = field_names_as_menu_string + '\n[' + str(i) + '] ' + field_name
                i += 1
            field_names_as_menu_string = field_names_as_menu_string + '\nSelection: '
            selection = field_names[int(input(prompt_text + ' ' + field_names_as_menu_string)) - 1]
            return selection

    @staticmethod
    def get_ebay_search_first_result_page_as_dict(search_string):
        search_url = (
                'https://www.ebay.com/sch/i.html?_from=R40&_nkw=' +
                '+'.join(search_string.split(' ')) +
                '&_sacat=0&LH_ItemCondition=3&LH_BIN=1&LH_PrefLoc=1&_sop=15&_stpos=60050&_fcid=1'
        )
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, features='lxml')
        top_result = soup.find('li', {'id': 'srp-river-results-listing1'})
        top_result_id = top_result.find('a')['href'].split('?')[0].split('/')[-1]
        new_link = 'https://www.ebay.com/itm/' + top_result_id
        product_page_response = requests.get(new_link)
        product_soup = BeautifulSoup(product_page_response.text, features='lxml')
        ebay_page_obj = eBay.ProductPage()
        ebay_page_obj.set_properties_from_soup(product_soup)
        return ebay_page_obj.as_dict()

    # Return Dict Keys Value Pair Where the Key is ProductIDs and the value is the object as dict
    @staticmethod
    def inventory_dict_from_objects(inventory_objects):
        inventory_as_dicts = {}
        for inventory_object in inventory_objects:
            inv_dict = inventory_object.as_dict_for_listing_generation()
            inventory_as_dicts[inv_dict['ProductID']] = inv_dict
        return inventory_as_dicts

    # Set Fixed Price based on Price File Cost of Items
    @staticmethod
    def get_fixed_price(raw_cost):
        cost = float(raw_cost)
        if cost <= 2:
            return (cost * 1.49) + .3
        elif cost <= 5:
            return (cost * 1.65) + .3
        elif cost <= 7:
            return (cost * 1.35) + .3
        elif cost <= 8:
            return (cost * 1.34) + .3
        elif cost <= 10:
            return (cost * 1.33) + .3
        elif cost <= 15:
            return (cost * 1.45) + .3
        elif cost <= 20:
            return (cost * 1.40) + .3
        elif cost <= 25:
            return (cost * 1.35) + .3
        elif cost <= 35:
            return (cost * 1.32) + .3
        elif cost <= 50:
            return (cost * 1.30) + .3
        elif cost <= 75:
            return (cost * 1.28) + 3
        elif cost <= 100:
            return (cost * 1.27) + 3
        elif cost <= 900:
            return (cost * 1.15) + 35
        else:
            return (cost * 1.15) + 100

    # Description Wrapper Based on Fixed Price
    @staticmethod
    def get_description_wrapper(fixed_price):
        price = float(fixed_price)
        if price <= 35:
            return'PARTS NO PHONE'
        elif price <= 100:
            return 'ENHANCED-PARTS'
        else:
            return 'ENHANCED-PARTS'

    # Set Shipping method based on weight
    @staticmethod
    def get_shipping_preset(raw_weight):
        weight = float(raw_weight)
        if weight < 1:
            return '1st class global'
        elif weight < 8:
            return 'global priority'
        elif weight < 75:
            return 'global ups'
        elif weight < 135:
            return 'UPS NO INTERNATIONAL'
        else:
            return 'freight pre set 135'

    # Payment Preset based on Fixed Price
    @staticmethod
    def get_payment_preset(fixed_price):
        price = float(fixed_price)
        if price >= 15:
            return 'PAYMENT 2'
        else:
            return 'PAYMENT 2'

    # Sets Manufacturer Root path
    def update_manufacturer_file_path_root(self):
        self.manufacturer_file_path_root = r'T:/ebay/' + self.manufacturer_short_name

    # Products from sixbit generated Product ID files
    def products_from_productids_csv_as_list_of_dicts(self):
        self.update_manufacturer_file_path_root()
        products = Products.Products(self.manufacturer_file_path_root + '/inventory/ProductIds.csv')
        products = products.products_as_list_of_dicts()
        return products

    # Inventory objects from sixbit ProductIDs CSV
    @staticmethod
    def productids_csv_dict_as_inventory_object(productids_dict):
        inventory_obj = Inventory.Inventory()
        inventory_obj.set_properties_from_productids_csv_dict(productids_dict)
        return inventory_obj

    # Inventory objects from sixbit ProductIDs CSV
    @staticmethod
    def productids_solid_csv_dict_as_inventory_object(productids_dict):
        inventory_obj = Inventory.Inventory()
        inventory_obj.from_solid_csv_dict(productids_dict)
        return inventory_obj

    @staticmethod
    def write_list_of_dicts_to_csv(list_of_dicts, save_file_path):
        keys = list_of_dicts[0].keys()
        with open(save_file_path, 'a', newline='', encoding='utf-8', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            data = [{k: v for k, v in record.items() if k in keys} for record in list_of_dicts]
            dict_writer.writerows(data)

    # Write inventory to CSV or XML
    def write_inventory_to_csv(self, inventory):
        save_file_path = self.manufacturer_file_path_root + \
                         '/inventory/' + self.manufacturer_short_name + time.strftime('_inventory.%m%d%Y.%I%M.csv')
        inventory = [product.as_dict_for_sixbit() for product in inventory]
        self.write_list_of_dicts_to_csv(inventory, save_file_path)

    # ------------------------------------------------------------------------------------------------

    def write_odict_to_csv(self, ordered_dicts):
        print('Writing File....')
        keys = ordered_dicts[0].keys()
        save_filepath = 'T:/ebay/' + self.manufacturer_short_name + '/data/' + self.manufacturer_short_name + \
                        '_where_used' + time.strftime('_inventory.%m%d%Y.%I%M.xml') + '.csv'
        with open(save_filepath, 'w', newline='') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(ordered_dicts)

    @staticmethod
    def write_odict_to_csv_to_filepath(ordered_dicts, save_filepath):
        ordered_dicts = [ordered_dict for ordered_dict in ordered_dicts if ordered_dict is not None]
        print('Writing File....')
        keys = ordered_dicts[0].keys()
        with open(save_filepath, 'w', newline='', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(ordered_dicts)

    @staticmethod
    def get_sixbit_update_xml_string(sixbit_shipment_id, shipping_service_id, tracking_number):
        xml_shipment_string_open = '<SixBitAPICalls><Shipment_Update><Shipments>'
        xml_shipment_string_close = '</Shipments></Shipment_Update></SixBitAPICalls>'
        xml_shipment_string = '<Shipment>' \
                              '<ShipmentID><![CDATA[' + sixbit_shipment_id + ']]></ShipmentID>' \
                              '<ShippingServiceID><![CDATA[' + shipping_service_id + ']]></ShippingServiceID>' \
                              '<TrackingNumber><![CDATA[' + tracking_number + ']]></TrackingNumber>' \
                              '</Shipment>'
        xml_shipment_string = xml_shipment_string_open + xml_shipment_string + xml_shipment_string_close
        return xml_shipment_string

    def parse_shipment_xml(self, xml_filepath_full):
        with open(xml_filepath_full, 'r', encoding='utf8') as xml_file:
            xml_string = xml_file.read()
            parser = element_tree.XMLParser(recover=True)
            tree = element_tree.fromstring(xml_string, parser=parser)
            for shipment in tree:
                shipment = self.etree_to_dict(shipment)['Shipment']
                return shipment['ShipmentID']

    def etree_to_dict(self, t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self.etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v
                         for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v)
                            for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d
