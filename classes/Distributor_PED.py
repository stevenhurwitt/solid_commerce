from classes import Distributor
from classes import SolidCommerce
import csv
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
from os import listdir
from os.path import isfile
from os.path import join
import os


class PED(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(PED, self).__init__('PED', "Power Equipment Distributors")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.manufacturer_file_path_root = r'T:/ebay/' + self.manufacturer_short_name

    def get_dealer_inventory(self):
        file_path = self.distributor_file_path_root + '/inventory/Mchenry.csv'
        with open(file_path, encoding="utf-8", errors="ignore")as file:
            distributor_inventory = csv.DictReader(file)
            distributor_inventory = [dict(product) for product in distributor_inventory]
            for product in distributor_inventory:
                if product['Manufacturer Code'] == 'BS':
                    product['Manufacturer Code'] = 'BRS'
                product['SKU'] = product['Manufacturer Code'] + '~' + product['Part Number']
            return distributor_inventory

    # set a default inventory source to create a standardization in Distributor class for automated inventory updates
    # just set it to run one of the implemented inventory methods
    def inventory_from_default(self, inventory_objects):
        return self.inventory_from_file(inventory_objects)

    # turns inventory file from t:\ebay\ped\inventory into inventory objects
    def inventory_from_file(self, inventory_objects):
        distributor_inventory = self.get_dealer_inventory()
        distributor_inventory = {product['SKU']: product for product in distributor_inventory}
        i = 0
        for inventory_obj in inventory_objects:
            try:
                distributor_part = distributor_inventory[inventory_obj.sku]
                if int(distributor_part['OnHand Quantity']) > 0:
                    ca_inventory = int(distributor_part['CA'])
                    or_inventory = int(distributor_part['OR'])
                    ut_inventory = int(distributor_part['UT'])
                    oh_inventory = int(distributor_part['OH'])
                    ny_inventory = int(distributor_part['NY'])
                    nc_inventory = int(distributor_part['NC'])
                    ga_inventory = int(distributor_part['GA'])
                    tx_inventory = int(distributor_part['TX'])
                    ia_inventory = int(distributor_part['IA'])
                    select_inventory = int(distributor_part['OnHand Quantity']) - ca_inventory - or_inventory - ut_inventory
                    all_inventory_dict = {
                        'WH_PED-CA': ca_inventory,
                        'WH_PED-UT': ut_inventory,
                        'WH_PED-OR': or_inventory,
                        'WH_PED-OH': oh_inventory,
                        'WH_PED-NY': ny_inventory,
                        'WH_PED-NC': nc_inventory,
                        'WH_PED-GA': ga_inventory,
                        'WH_PED-TX': tx_inventory,
                        'WH_PED-IA': ia_inventory,
                        'WH_McHenry Inbound': select_inventory
                    }
                    for key, value in all_inventory_dict.items():
                        if value < 0:
                            all_inventory_dict[key] = 0
                    try:
                        if int(distributor_part['Std Buy Pack Qty']) > 1:
                            inventory_obj.unit_type = 'pack'
                        else:
                            inventory_obj.unit_type = 'each'
                    except ValueError:
                        inventory_obj.unit_type = 'each'
                    inventory_obj.cost = str(round(float(distributor_part['Copy of COST']), 2))
                    inventory_obj.list_price = distributor_part['Copy of List Price']
                    inventory_obj.selective_quantity = str(select_inventory)
                    inventory_obj.total_quantity = distributor_part['OnHand Quantity']
                    inventory_obj.upc = distributor_part['UPC Each']
                    inventory_obj.minimum_order_qty = distributor_part['Std Buy Pack Qty']
                    inventory_obj.fulfillment_source = 'DropShipper'
                    inventory_obj.warehouse_with_inventory_dicts = all_inventory_dict
                else:
                    all_inventory_dict = {
                        'WH_PED-CA': 0,
                        'WH_PED-UT': 0,
                        'WH_PED-OR': 0,
                        'WH_PED-OH': 0,
                        'WH_PED-NY': 0,
                        'WH_PED-NC': 0,
                        'WH_PED-GA': 0,
                        'WH_PED-TX': 0,
                        'WH_PED-IA': 0,
                        'WH_McHenry Inbound': 0
                    }
                    inventory_obj.selective_quantity = '0'
                    inventory_obj.total_quantity = '0'
                    inventory_obj.minimum_order_qty = '0'
                    inventory_obj.fulfillment_source = 'DropShipper'
                    inventory_obj.warehouse_with_inventory_dicts = all_inventory_dict
            except KeyError:
                all_inventory_dict = {
                    'WH_PED-CA': 0,
                    'WH_PED-UT': 0,
                    'WH_PED-OR': 0,
                    'WH_PED-OH': 0,
                    'WH_PED-NY': 0,
                    'WH_PED-NC': 0,
                    'WH_PED-GA': 0,
                    'WH_PED-TX': 0,
                    'WH_PED-IA': 0,
                    'WH_McHenry Inbound': 0
                }
                inventory_obj.selective_quantity = '0'
                inventory_obj.total_quantity = '0'
                inventory_obj.minimum_order_qty = '0'
                inventory_obj.fulfillment_source = 'DropShipper'
                inventory_obj.warehouse_with_inventory_dicts = all_inventory_dict
                self.log_distributor_event(
                    self.get_log_dict(
                        inventory_obj.sku,
                        'Error - No Inventory',
                        'Catalogue Product not available at distributor'
                    )
                )
            i += 1
        return inventory_objects

    def scrape_oregon_crosses(self):
        root = tk.Tk()
        root.withdraw()
        product_ids_filepath = filedialog.askopenfilename()
        save_filepath = product_ids_filepath.split('.')[0] + '_CrossInfo.csv'
        products = csv.DictReader(open(product_ids_filepath, encoding="utf8"))
        scraped_info = [product for product in [self.scrape_oregon_part_crosses(product) for product in products if not None] if product is not None]
        collapsed_scraped_info = [cross for product in scraped_info for cross in product]
        self.write_odict_to_csv_to_filepath(collapsed_scraped_info, save_filepath)

    def scrape_oregon_part_crosses(self, product):
        product_search_url = 'https://www.oregonproducts.com/en/carburetor-honda/p/' + product['ProductID']
        page = requests.get(product_search_url)
        soup = BeautifulSoup(page.text, 'lxml')
        try:
            product_name = soup.select('div.name')[0].text.strip()
        except IndexError:
            product_name = {}
        try:
            details = self. get_product_details(soup)
        except KeyError:
            details = {}
        product['Details'] = details
        try:
            crosses = [{'OEP PartNumber': product['ProductID'],
                        'OEM PartNumber': "'" + product_id,
                        'OEM Brand': brand,
                        'ProductName': product_name}
                       for brand, product_ids in details['Part Mapping'].items()
                       for product_id in product_ids]
            return crosses
        except KeyError:
            return None

    def scrape_oregon_parts(self):
        root = tk.Tk()
        root.withdraw()
        product_ids_filepath = filedialog.askopenfilename()
        save_filepath = product_ids_filepath.split('.')[0] + '_ProductInfo.csv'
        # group_number = input('Group Number: ')
        products = csv.DictReader(open(product_ids_filepath, encoding="utf8"))
        scraped_info = [self.scrape_oregon_part(product) for product in products]
                        # if product['Group #'].strip("'") == group_number]
        scraped_info_html = [self.get_ebay_html_tabs(product) for product in scraped_info]
        for product in scraped_info_html:
            try:
                product['Length'] = product['Specifications']['General']['Packaged Length']
                product['Width'] = product['Specifications']['General']['Packaged Width']
                product['Height'] = product['Specifications']['General']['Packaged Height']
                product['PFWeight'] = product['Specifications']['General']['Weight (with Packaging)']
            except:
                pass
            del product['Specifications']
            del product['Details']
        self.write_odict_to_csv_to_filepath(scraped_info_html, save_filepath)

    def scrape_oregon_part(self, product):
        product_search_url = 'https://www.oregonproducts.com/en/carburetor-honda/p/' + product['Part #']
        product['Length'] = None
        product['Width'] = None
        product['Height'] = None
        product['PFWeight'] = None
        page = requests.get(product_search_url)
        soup = BeautifulSoup(page.text, 'lxml')
        try:
            product_name = soup.select('div.name')[0].text.strip()
        except IndexError:
            product_name = {}
        try:
            images = ['https://www.oregonproducts.com' + img.attrs['data-zoom-image']
                      for img in soup.select('div.item img.lazyOwl')]
        except KeyError:
            images = []
        try:
            details = self. get_product_details(soup)
        except KeyError:
            details = {}
        try:
            specifications = self.get_product_specifications(soup)
        except KeyError:
            specifications = {}
        product['ProductName'] = product_name
        product['ImageURLs'] = images
        product['Details'] = details
        product['Specifications'] = specifications
        return product

    def get_tab_box_html(self, dictionary):
        html = ''
        for brand, content in dictionary.items():
            content_html = '<span>' + ', '.join(content) + '</span>'
            brand_html = '<h3>' + brand + ': </h3>' \
                         + content_html + ''
            html += brand_html
        return html

    def get_specifications_html(self, dictionary):
        html = ''
        for category, content in dictionary.items():
            table_html = '<h3>' + category + '</h3>' \
                          '<table><tbody>'
            for label, value in content.items():
                row = '<tr><td>' + label + '</td><td>' + value + '</td></tr>'
                table_html += row
            table_html += '</tbody></table>'
            html += table_html
        return html

    def get_ebay_html_tabs(self, product):
        try:
            html = ''
            css = '.tabs { list-style: none;}' \
                  '.tabs li { display: inline;}' \
                  '.tabs li a { color: black; float: left; display: block; padding: 4px 10px; margin-left: -1px;' \
                  'position: relative; left: 1px; background: white; text-decoration: none;}' \
                  '.tabs li a:hover { background: #ccc;}' \
                  '.group:after { visibility: hidden;' \
                  'display: block;' \
                  'font-size: 0;' \
                  'content: " "; ' \
                  'clear: both; ' \
                  'height: 0;}' \
                  '.box-wrap { position: relative;}' \
                  '.tabbed-area div div { background: white; padding: 20px; min-height: 250px;' \
                  'top: -1px; left: 0; width: 100%;}' \
                  '.tabbed-area div div, .tabs li a { border: 1px solid #ccc;}' \
                  '#box-one:target, #box-two:target {z-index: 1;}' \
                  '#box-one:not(:target), #box-two:not(:target) {display: none;}' \
                  '.clk_hdr {color: red;}'
            item_specifications = product['Specifications']
            item_details = product['Details']
            item_details_list = item_details.pop('Detail List', None)
            if item_details_list is not None:
                details_list_string = '<h3>Details</h3><ul>' + \
                                      ''.join(['<li>' + item + '</li>' for item in item_details_list]) + \
                                      '</ul>'
            else:
                details_list_string = ''
            try:
                fit_html = self.get_tab_box_html(item_details['Fit Guide'])
            except KeyError:
                fit_html = None
            try:
                mapping_html = self.get_tab_box_html(item_details['Part Mapping'])
            except KeyError:
                mapping_html = None
            if fit_html and mapping_html:
                tabbed_html = '<h2 class="clk_hdr">Click these tabs for additional compatibility information.</h2>' \
                              '<div class="tabbed-area">' \
                              '    <ul class="tabs group">' \
                              '        <li><a href="#box-one">Replaces</a></li>' \
                              '        <li><a href="#box-two">Compatible Models</a></li>' \
                              '    </ul>' \
                              '    <div class="box-wrap">' \
                              '        <div id="box-one">' \
                              '        <h2>Replaces</h2>' \
                              '          ' + mapping_html + \
                              '        </div>' \
                              '        <div id="box-two">' \
                              '        <h2>Compatible Models</h2>' \
                              '          ' + fit_html + \
                              '        </div>' \
                              '    </div>' \
                              '</div>'
            elif fit_html:
                tabbed_html = '<h2>Compatible Models</h2><div>' + fit_html + '</div>'
            elif mapping_html:
                tabbed_html = '<h2>Replaces</h2><div>' + mapping_html + '</div>'
            else:
                tabbed_html = ''
            specifications_html = self.get_specifications_html(item_specifications)
            html += '<style>' + css + '</style>' + details_list_string + specifications_html + tabbed_html
            product['html'] = html
            return product
        except KeyError:
            pass

    @staticmethod
    def get_product_specifications(soup):
        product_info_heads = soup.select('div.tabs div.tabhead a')
        product_info_bodys = soup.select('div.tabs div.tabbody')
        product_info_dict = {}
        for head, body in dict(zip(product_info_heads, product_info_bodys)).items():
            product_info_dict[head.text.strip()] = body
        specifications = product_info_dict['Specifications']
        headlines = specifications.select('div.headline')
        classification_lists = specifications.select('div.classifications-list')
        headlines_dict = {}
        for headline, classification_list in dict(zip(headlines, classification_lists)).items():
            attributes = classification_list.select('div.attrib')
            values = classification_list.select('div.multiple-values')
            attributes_dict = {}
            for attribute, value in dict(zip(attributes, values)).items():
                attributes_dict[attribute.text.strip()] = value.text.strip().replace(u'\xa0', u' ')
            headlines_dict[headline.text.strip()] = attributes_dict
        return headlines_dict

    @staticmethod
    def get_product_details(soup):
        product_info_heads = soup.select('div.tabs div.tabhead a')
        product_info_bodys = soup.select('div.tabs div.tabbody')
        product_info_dict = {}
        for head, body in dict(zip(product_info_heads, product_info_bodys)).items():
            product_info_child_heads = body.select('div.child-tabs div.child-tabhead a')
            product_info_child_bodys = body.select('div.child-tabs div.child-tabbody')
            product_info_panel_list = body.select('ul.tab-details-list li')
            product_info_children_dict = {'Detail List': [list_item.text.strip() for list_item in product_info_panel_list]}
            for child_head, child_body in dict(zip(product_info_child_heads, product_info_child_bodys)).items():
                product_info_panel_heads = child_body.select('div.tab-details div.panel-heading div.panel-title a')
                product_info_panel_bodys = child_body.select('div.tab-details div.panel-group')
                panel_dict = {}
                for panel_head, panel_body in dict(zip(product_info_panel_heads, product_info_panel_bodys)).items():
                    brand_info = [item.strip() for item in panel_body.text.split(',')]
                    panel_dict[panel_head.text.strip()] = brand_info
                product_info_children_dict[child_head.text.strip()] = panel_dict
            product_info_dict[head.text.strip()] = product_info_children_dict
        return product_info_dict['Product details']

    def process_tracking_files(self):
        origin_folder = 'T:/ebay/PED/Tracking/Pending Processing'
        processed_folder = 'T:/ebay/PED/Tracking/Processed'
        tracking_file_paths = [origin_folder + '/' + f for f in listdir(origin_folder) if isfile(join(origin_folder, f))]
        for tracking_filepath in tracking_file_paths:
            tracking_file_dicts = self. get_xls_as_dicts_from_filepath(tracking_filepath)
            for row in tracking_file_dicts:
                self.update_shipping(row)
                self.write_list_of_dicts_to_csv([row], processed_folder + '/PED_' + row['PO Number'] + '.csv')
            os.remove(tracking_filepath)

    def update_shipping(self, order_record):
        solid_api = SolidCommerce.API()
        shipper_code = order_record['Carrier']
        shipping_type_cases = {'UPSSurePost>1lb': 'UPSGround',
                               'UPSSurePost<1lb': 'UPSSurePostLessThanLB',
                               'UPS Ground Residential': 'UPSGround',
                               'Consumer Drop Ship': 'UPSGround'
                               }
        shipping_package_type_cases = {'UPSSurePost>1lb': '0',
                                       'UPSSurePost<1lb': '0',
                                       'UPS Ground Residential': '0',
                                       'Consumer Drop Ship': '0'
                                       }
        shipment_api_update = SolidCommerce.Shipment()
        shipment_api_update.sc_sale_id = order_record['PO Number']
        shipment_api_update.tracking_number = order_record['Tracking Number']
        shipment_api_update.marketplace = '3'
        shipment_api_update.shipping_type_code = shipping_type_cases[shipper_code]
        shipment_api_update.package_type = '0'  # shipping_package_type_cases[shipper_code]
        solid_api_shipping_update_call = SolidCommerce.API()
        solid_api_shipping_update_call.update_ebay_shipment(shipment_api_update.as_shipment_element())
        try:
            order_object = self.get_order_from_solid_by_ebay_number(order_record['PO Number'])[0]
            order_object.status = 'Drop Shipped PED'
            solid_api.update_order_status(order_object)
        except:
            print(shipment_api_update.as_dict())
