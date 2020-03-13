import sys
import os
import Dictionary_To_ETree
import Element_To_Dict
import requests
import re
from Tkinter import *
import Tkinter as tk
import csv
from lxml import etree as et
from lxml.etree import tostring
from xml.etree import ElementTree
import time


class API(object):

    def __init__(self):
        self.appKey = '8B732549C0274209'
        self.securityKey = ';!=q;W;V--.^_d5a;|55h.FEetr=h_:^|*;+G=|s.*||%RVl-I'
        self.base_url = 'http://webservices.solidcommerce.com/ws.asmx'

    # def get_all_products(self):

    def get_all_company_lists(self):
        call = '/GetAllCompanyLists'
        data = {
            'appKey': self.appKey,
            'securityKey': self.securityKey,
            'xslUri': '',
            'includeWarehouses': 'true'
        }
        url = self.base_url + call
        response = requests.post(url, data)
        tree = ElementTree.fromstring(response.text)
        company_lists_dicts = [
            Element_To_Dict.get_dict(company_list)['List'] for company_list in tree.findall('.//List')
        ]
        list_objects = [self.generate_list_object(company_lists_dict) for company_lists_dict in company_lists_dicts]
        return list_objects

    def generate_list_object(self, list_dict):
        company_list = CompanyList()
        company_list.from_dict(list_dict)
        return company_list

    def get_all_orders(self):
        save_filepath = '/home/steven/solid_commerce/data/orders.csv'
        order_search_filter = OrderSearchFilter()
        order_search_filter.page = '1'
        order_search_filter.records_per_page_count = '50000'
        order_search_filter.order_search_format = 'ByOrderItems'
        # order_search_filter.order_status = 'PAID'
        # order_search_filter.filter_by_order_status = 'true'
        orders = [order.as_dict() for order in self.search_orders_v6(order_search_filter.as_element())]
        # ordered_dicts = [ordered_dict for ordered_dict in orders if ordered_dict is not None]
        print('Writing File....')
        keys = orders[0].keys()
        with open(save_filepath, 'w', newline='', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(orders)

    @staticmethod
    def get_products_from_file():
        filepath = '/home/steven/solid_commerce/data/SolidCommerceProducts.csv'
        products = [dict(product) for product in csv.DictReader(open(filepath, 'r'))]
        return products

    def get_products_from_file_by_mfr(self, mfr):
        products_from_file = self.get_products_from_file()
        products = [product for product in products_from_file if product['SKU'].split('~')[0] == mfr]
        return products

    @staticmethod
    def get_soap_envelope(input_element):
        soap_ns = 'http://schemas.xmlsoap.org/soap/envelope/'
        xsi_ns = 'http://www.w3.org/2001/XMLSchema-instance'
        xsd_ns = 'http://www.w3.org/2001/XMLSchema'
        ns_map = {
            'soap': soap_ns,
            'xsi': xsi_ns,
            'web': xsd_ns
        }
        env = et.Element(et.QName(soap_ns, 'Envelope'), nsmap=ns_map)
        body = et.Element(et.QName(soap_ns, 'Body'), nsmap=ns_map)
        body.append(input_element)
        env.append(body)
        return env

    def update_insert_product(self, product_string):
        url = 'http://webservices.solidcommerce.com/ws.asmx'
        body = ('<?xml version="1.0" encoding="utf-8"?>'
                '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi='
                '"http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
                '<soap:Body>'
                '<InsertProductV2 xmlns="http://webservices.liquidatedirect.com/">'
                '<appKey>' + self.appKey + '</appKey>'
                '<xslUri />' +
                product_string
                + '</InsertProductV2>'
                  '</soap:Body>'
                  '</soap:Envelope>')
        headers = {
            'content-type': 'text/xml; charset=utf-8',
            'Content-Length': str(len(body.encode('utf-8'))),
            'SOAPAction': '"http://webservices.liquidatedirect.com/InsertProductV2"',
            'Host': 'webservices.solidcommerce.com'
        }
        print(body.encode(encoding='utf-8', errors='ignore'))
        response = requests.post(url, headers=headers, data=body.encode(encoding='utf-8', errors='ignore'))
        print(response)
        print(response.text)

    @staticmethod
    def update_product(product_string):
        url = 'http://webservices.solidcommerce.com/ws.asmx'
        body = ('<?xml version="1.0" encoding="utf-8"?>'
                '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi='
                '"http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
                '<soap:Body>'
                '<UpdateProduct xmlns="http://webservices.liquidatedirect.com/">'
                '<appKey>' + 'fwIu5s(wCm/K2j)c' + '</appKey>'
                                                  '<xslUri />' +
                product_string
                + '</UpdateProduct>'
                  '</soap:Body>'
                  '</soap:Envelope>')
        headers = {
            'content-type': 'text/xml; charset=utf-8',
            'Content-Length': str(len(body.encode('utf-8'))),
            'SOAPAction': '"http://webservices.liquidatedirect.com/UpdateProduct"',
            'Host': 'webservices.solidcommerce.com'
        }
        response = requests.post(url, headers=headers, data=body.encode(encoding='utf-8', errors='ignore'))
        print(response)
        print(response.text)

    def get_all_lists(self):
        url = 'http://webservices.solidcommerce.com/ws.asmx/GetAllCompanyLists'
        body = {'appKey': self.appKey,
                'securityKey': self.securityKey,
                'xslUri': '',
                'includeWarehouses': 'true'}
        response = requests.post(url, data=body)
        print(response)
        tree = ElementTree.fromstring(response.text)
        lists = [list_tag.text for list_tag in tree.findall('.//ListName') if list_tag.text != 'eBayUS']
        return lists

    def get_all_inventory_items_from_list(self, list_name):
        url = 'http://webservices.solidcommerce.com/ws.asmx/GetListItemsByListNameV4'
        i = 1
        while True:
            body = {'appKey': self.appKey,
                    'securityKey': self.securityKey,
                    'xslUri': '',
                    'listName': list_name,
                    'liidSKU': '',
                    'customSKU': '',
                    'page': str(i),
                    'recordsCount': '10000',
                    'fromDateTime': '',
                    'requestedColumnsSet': ''}
            response = requests.post(url, data=body)
            print(response)
            print(list_name + ' Page ' + str(i))
            tree = ElementTree.fromstring(response.text)
            item_elements = tree.findall('.//Item')
            if len(item_elements) < 1:
                break
            for item_element in item_elements:
                item_obj = Item()
                item_obj.from_tree(item_element)
                yield item_obj
            i += 1

    def get_all_item_listing_from_list(self, list_name):
        url = 'http://webservices.solidcommerce.com/ws.asmx/GetListItemsByListNameV4'
        i = 1
        while True:
            body = {'appKey': self.appKey,
                    'securityKey': self.securityKey,
                    'xslUri': '',
                    'listName': list_name,
                    'liidSKU': '',
                    'customSKU': '',
                    'page': str(i),
                    'recordsCount': '10000',
                    'fromDateTime': '',
                    'requestedColumnsSet': ''}
            response = requests.post(url, data=body)
            print(response)
            print(list_name + ' Page ' + str(i))
            tree = ElementTree.fromstring(response.text)
            item_elements = tree.findall('.//Item')
            if len(item_elements) < 1:
                break
            for item_element in item_elements:
                item_obj = Item()
                item_obj.from_tree(item_element)
                yield item_obj
            i += 1

    def qty_delta_for_all_warehouses(self):
        lists = self.get_all_lists()
        for wh_list in lists:
            try:
                items = self.get_all_inventory_items_from_list(wh_list)
                product_dicts = []
                for item in items:
                    product_dicts.append(
                        {
                            'WH_' + wh_list: '0',
                            'SKU': item.li_id_sku,
                            'StorageLocation': ''
                        }
                    )
                if len(product_dicts) > 0:
                    self.upload_list_items(product_dicts)
            except MemoryError:
                print(wh_list + ' too large of list')

    def get_catalogs(self):
        url = 'http://webservices.solidcommerce.com/ws.asmx/GetCatalogs?'
        data = {
            'appKey': self.appKey,
            'xslUri': ''
        }
        response = requests.post(url, data)
        print(response)
        print(response.text)

    def upload_list_items_from_file(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename()
        products = [dict(product) for product in csv.DictReader(open(filepath, 'r', errors='ignore'))]
        self.upload_list_items(products)

    def segment_list(self, product_list):
        for i in range(0, len(product_list), 5000):
            yield product_list[i:i + 5000]

    def upload_list_items(self, products):
        url = 'http://webservices.solidcommerce.com/ws.asmx'
        warehouses = [key for key, value in products[0].items() if 'WH_' in key]
        for warehouse in warehouses:
            j = 1
            for product_chunk in self.segment_list(products):
                items_string = ''
                for product in product_chunk:
                    try:
                        general_item_element = self.get_general_item_model_element(
                            product['SKU'],
                            re.sub('WH_', '', warehouse),
                            product[warehouse],
                            product['Cost']
                        )
                        try:
                            storage_location_element = self.get_storage_location_element(product['StorageLocation'])
                            general_item_element.find('.//InventoryDetails').append(storage_location_element)
                        except KeyError:
                            pass
                        items_string += str(tostring(general_item_element)).strip("'b'")
                    except KeyError:
                        pass
                app_key = self.appKey
                secret_key = self.securityKey
                body = (
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                    'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
                    '<soap12:Body>'
                    '<UploadListItems xmlns="http://webservices.liquidatedirect.com/">'
                    '<appKey>' + app_key + '</appKey>'
                    '<securityKey>' + secret_key + '</securityKey>'
                    '<itemsDetails>'
                    + items_string +
                    '</itemsDetails>'
                    '</UploadListItems>'
                    '</soap12:Body>'
                    '</soap12:Envelope>'
                    )
                headers = {
                    'Host': 'webservices.solidcommerce.com',
                    'content-type': 'application/soap+xml; charset=utf-8',
                    'Content-Length': str(len(body.encode('utf-8')))
                    }
                response = requests.post(
                    url,
                    headers=headers,
                    data=body.encode(
                        encoding='utf-8',
                        errors='ignore'
                    ),
                    timeout=300
                )
                i = 0
                while 'Error' in str(response.text) and i < 10:
                    print('Submission Error ')
                    response = requests.post(url, headers=headers, data=body.encode(encoding='utf-8', errors='ignore'))
                    i += 1
                if 'Error' not in str(response.text):
                    print('Location ' + warehouse + ' Updated Successfully ' + str(j))
                    j += 1
                    continue
                else:
                    mfr = products[0]['SKU'].split('~')[0]
                    request_name = mfr + '.' + warehouse
                    # self.log_api_error_response(request_name, body, response.text)
                    j += 1

    @staticmethod
    def log_api_error_response(request_name, request, response_text):
        log_dir = '/home/steven/Documents/solid_commerce/data/'
        request_file_name = time.strftime('%d%m%y.%H%M') + request_name + '.Request.xml'
        response_file_name = time.strftime('%d%m%y.%H%M') + request_name + '.Response.xml'
        with open(log_dir + request_file_name, 'w', errors='ignore') as request_file:
            request_file.writelines(request)
        with open(log_dir + response_file_name, 'w', errors='ignore') as response_file:
            response_file.writelines(response_text)

    def get_general_item_model_element(self, sku_string, list_name, qty, cost):
        general_item_model_element = et.Element('GeneralItemModel')
        inventory_details_element = et.Element('InventoryDetails')
        list_name_element = et.Element('ListName')
        list_name_element.text = list_name
        upload_type_element = et.Element('UploadType')
        upload_type_element.text = '0'
        warehouse_id_element = et.Element('WarehouseId')
        warehouse_id_element.text = sku_string
        sku_element = self.get_sku_element(sku_string)
        qty_element = self.get_qty_element(qty)
        cost_element = self.get_cost_element(cost)
        inventory_details_element.append(list_name_element)
        inventory_details_element.append(upload_type_element)
        inventory_details_element.append(warehouse_id_element)
        inventory_details_element.append(sku_element)
        inventory_details_element.append(qty_element)
        inventory_details_element.append(cost_element)
        general_item_model_element.append(inventory_details_element)
        return general_item_model_element

    @staticmethod
    def get_storage_location_element(location_string):
        storage_location_element = et.Element('storageLocation')
        value_element = et.Element('Value')
        if location_string is not None:
            value_element.text = str(location_string.encode('utf-8')).strip('b').strip("'")
        else:
            value_element.text = 'None'
        set_null_element = et.Element('SetNull')
        set_null_element.text = 'false'
        is_specified_element = et.Element('IsSpecified')
        is_specified_element.text = 'true'
        storage_location_element.append(value_element)
        storage_location_element.append(set_null_element)
        storage_location_element.append(is_specified_element)
        return storage_location_element

    @staticmethod
    def get_cost_element(cost_string):
        sku_element = et.Element('baseCost')
        value_element = et.Element('Value')
        try:
            value_element.text = str(float(str(cost_string).replace(',', '')))
        except TypeError:
            value_element.text = '0.00'
        except ValueError:
            value_element.text = '0.00'
        set_null_element = et.Element('SetNull')
        set_null_element.text = 'false'
        is_specified_element = et.Element('IsSpecified')
        is_specified_element.text = 'true'
        sku_element.append(value_element)
        sku_element.append(set_null_element)
        sku_element.append(is_specified_element)
        return sku_element

    @staticmethod
    def get_sku_element(sku_string):
        sku_element = et.Element('Sku')
        value_element = et.Element('Value')
        value_element.text = sku_string
        set_null_element = et.Element('SetNull')
        set_null_element.text = 'false'
        is_specified_element = et.Element('IsSpecified')
        is_specified_element.text = 'true'
        sku_element.append(value_element)
        sku_element.append(set_null_element)
        sku_element.append(is_specified_element)
        return sku_element

    @staticmethod
    def get_qty_element(qty):
        qty_element = et.Element('qty')
        value_element = et.Element('Value')
        value_element.text = str(qty)
        set_null_element = et.Element('SetNull')
        set_null_element.text = 'false'
        is_specified_element = et.Element('IsSpecified')
        is_specified_element.text = 'true'
        qty_element.append(value_element)
        qty_element.append(set_null_element)
        qty_element.append(is_specified_element)
        return qty_element

    def update_ebay_shipment(self, shipment):
        url = 'http://webservices.solidcommerce.com/ws.asmx/SaveShipmentRecord'
        data = {
            'appKey': self.appKey,
            'securityKey': self.securityKey,
            'xslUri': '',
            'shipmentDataXml': ElementTree.tostring(shipment)
        }
        response = requests.post(url, data=data)
        print(response)
        print(response.text)

    def get_app_key_element(self):
        app_key_element = et.Element('appKey')
        app_key_element.text = self.appKey
        return app_key_element

    def get_security_key_element(self):
        security_key_element = et.Element('securityKey')
        security_key_element.text = self.securityKey
        return security_key_element

    def search_orders_v6(self, search_filter_element):
        url = 'http://webservices.solidcommerce.com/ws.asmx'
        # search_orders_element_v6 = et.Element('SearchOrdersV6', xmlns='http://webservices.liquidatedirect.com/')
        # search_orders_element_v6.append(self.get_app_key_element())
        # search_orders_element_v6.append(self.get_security_key_element())
        # search_orders_element_v6.append(search_filter_element)
        # envelope = self.get_soap_envelope(search_orders_element_v6)
        data = ('<?xml version="1.0" encoding="utf-8"?>'
                '<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
                '<soap12:Body>'
                '<SearchOrdersV6 xmlns="http://webservices.liquidatedirect.com/">'
                '<appKey>' + self.appKey + '</appKey>'
                '<securityKey>' + self.securityKey + '</securityKey>' +
                tostring(search_filter_element).decode('utf-8') +
                '</SearchOrdersV6>'
                '</soap12:Body>'
                '</soap12:Envelope>')
        # data = et.tostring(envelope).decode('utf-8')
        # print(data)
        header = {
            'Host': 'webservices.solidcommerce.com',
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Content-Length': str(len(data))
        }
        response = requests.post(url, headers=header, data=data)
        # print(response.text)
        tree = ElementTree.fromstring(response.text)
        orders = tree.findall('.//Order')
        # print(orders)
        return [self.order_object_from_element(order) for order in orders]

    @staticmethod
    def save_xml_string(file_name, xml_string):
        with open('T:/ebay/SolidCommerce/XML Logs/' + file_name, 'wb') as file:
            file.write(xml_string)

    @staticmethod
    def order_object_from_element(order_element):
        order = Order()
        order.set_from_xml_element(order_element)
        return order

    def update_order_status(self, order_object):
        url = 'http://webservices.solidcommerce.com/ws.asmx'
        data = ('<?xml version="1.0" encoding="utf-8"?>'
                '<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
                '<soap12:Body>'
                '<UpdateOrderStatus xmlns="http://webservices.liquidatedirect.com/">'
                '<appKey>' + self.appKey + '</appKey>'
                '<securityKey>' + self.securityKey + '</securityKey>'
                '<xslUri></xslUri>'
                '<saleID>' + order_object.sale_id + '</saleID>'
                '<status>' + order_object.status + '</status>'
                '<isCustomStatus>1</isCustomStatus>'
                '<updateNotes></updateNotes>'
                '</UpdateOrderStatus>'
                '</soap12:Body>'
                '</soap12:Envelope>')
        header = {
            'Host': 'webservices.solidcommerce.com',
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Content-Length': str(len(data))
        }
        response = requests.post(url, headers=header, data=data)
        print(response)


class ExcelMarketItemDetailsClass(object):

    def __init__(self):
        self.marketplace = None
        self.product_id = None
        self.product_id_type = None
        self.condition = None
        self.condition_note = None
        self.lowest_price = None
        self.sales_rank = None
        self.seller_rank = None
        self.seller_feedback_count = None
        self.shipping_fee = None
        self.has_errors = None

    def as_dict(self):
        return{
            'marketplace': self.marketplace,
            'ProductID': self.product_id,
            'ProductIDType': self.product_id_type,
            'Condition': self.condition,
            'ConditionNote': self.condition_note,
            'LowestPrice': self.lowest_price,
            'SalesRank': self.sales_rank,
            'SellerRank': self.seller_rank,
            'SellerFeedbackCount': self.seller_feedback_count,
            'ShippingFee': self.shipping_fee,
            'HasErrors': self.has_errors,
        }

    def as_element(self):
        search_filter_element = et.Element('ExcelMarketItemDetailsClass')
        Dictionary_To_ETree.dicts_to_xml(search_filter_element, self.as_dict())
        return search_filter_element


class Order(object):

    def __init__(self):
        self.store_order_id = None
        self.sale_id = None
        self.product_name = None
        self.product_name_at_time_of_purchase = None
        self.total_sale = None
        self.qty = None
        self.item_cost = None
        self.item_sales_tax = None
        self.status = None
        self.manufacture = None
        self.sku = None
        self.warehouse_id = None
        self.weight = None
        self.alternate_order_id = None
        self.storage_location = None
        self.asin = None
        self.upc = None
        self.sales_tax_amount = None
        self.discount_amount = None
        self.sold_price = None
        self.warehouse_name = None
        self.market_local = None
        self.order_date = None
        self.sales_channel = None
        self.is_amazon_prime_order = None
        self.buyer_name = None
        self.buyer_email = None
        self.buyer_street1 = None
        self.buyer_street2 = None
        self.buyer_city = None
        self.buyer_country = None
        self.buyer_zip_code = None
        self.buyer_user_name = None
        self.payment_info = None
        self.ship_service = None
        self.ship_service_name = None
        self.ship_fee = None
        self.tax = None
        self.business_name = None
        self.ship_to_name = None
        self.ship_to_street1 = None
        self.ship_to_street2 = None
        self.ship_to_city = None
        self.ship_to_zip = None
        self.ship_to_state = None
        self.ship_to_country = None
        self.ship_to_phone = None
        self.ship_to_email = None
        self.sc_order_item_id = None

    def as_dict_for_errors(self):
        return {
            'StoreOrderID': self.store_order_id,
            'SKU': self.sku,
            'Qty': self.qty,
            'Weight': self.weight,
            'ShipFee': self.ship_fee
        }

    def as_dict(self):
        return{
            'StoreOrderID': self.store_order_id,
            'saleID': self.sale_id,
            'ProductName': self.product_name,
            'ProductNameAtTimeOfPurchase': self.product_name_at_time_of_purchase,
            'TotalSale': self.total_sale,
            'Qty': self.qty,
            'ItemCost': self.item_cost,
            'ItemSalesTax': self.item_sales_tax,
            'Status': self.status,
            'Manufacture': self.manufacture,
            'SKU': self.sku,
            'WarehouseID': self.warehouse_id,
            'Weight': self.weight,
            'AlternateOrderID': self.alternate_order_id,
            'StorageLocation': self.storage_location,
            'ASIN': self.asin,
            'UPC': self.upc,
            'SalesTaxAmount': self.sales_tax_amount,
            'DiscountAmount': self.discount_amount,
            'SoldPrice': self.sold_price,
            'WarehouseName': self.warehouse_name,
            'MarketLocal': self.market_local,
            'OrderDate': self.order_date,
            'SalesChannel': self.sales_channel,
            'IsAmazonPrimeOrder': self.is_amazon_prime_order,
            'BuyerName': self.buyer_name,
            'BuyerEmail': self.buyer_email,
            'BuyerStreet1': self.buyer_street1,
            'BuyerStreet2': self.buyer_street2,
            'BuyerCity': self.buyer_city,
            'BuyerCountry': self.buyer_country,
            'BuyerZipCode': self.buyer_zip_code,
            'BuyerUserName': self.buyer_user_name,
            'PaymentInfo': self.payment_info.as_dict(),
            'ShipService': self.ship_service,
            'ShipServiceName': self.ship_service_name,
            'ShipFee': self.ship_fee,
            'Tax': self.tax,
            'BusinessName': self.business_name,
            'ShipToName': self.ship_to_name,
            'ShipToStreet1': self.ship_to_street1,
            'ShipToStreet2': self.ship_to_street2,
            'ShipToCity': self.ship_to_city,
            'ShipToZip': self.ship_to_zip,
            'ShipToState': self.ship_to_state,
            'ShipToCountry': self.ship_to_country,
            'ShipToPhone': self.ship_to_phone,
            'ShipToEmail': self.ship_to_email,
            'SCOrderItemID': self.sc_order_item_id
        }

    def set_from_xml_element(self, order_element):
        element_as_dict = Element_To_Dict.get_dict(order_element)
        self.set_from_dict(element_as_dict['Order'])

    def set_from_dict(self, order_dict):
        self.store_order_id = order_dict['StoreOrderID']
        self.sale_id = order_dict['saleID']
        self.product_name = order_dict['ProductName']
        self.product_name_at_time_of_purchase = order_dict['ProductNameAtTimeOfPurchase']
        self.total_sale = order_dict['TotalSale']
        self.qty = order_dict['Qty']
        self.item_cost = order_dict['ItemCost']
        self.item_sales_tax = order_dict['ItemSalesTax']
        self.status = order_dict['Status']
        self.manufacture = order_dict['Manufacture']
        self.sku = order_dict['SKU']
        self.warehouse_id = order_dict['WarehouseID']
        self.weight = order_dict['Weight']
        self.alternate_order_id = order_dict['AlternateOrderID']
        self.storage_location = order_dict['StorageLocation']
        self.asin = order_dict['ASIN']
        self.upc = order_dict['UPC']
        self.sales_tax_amount = order_dict['SalesTaxAmount']
        self.discount_amount = order_dict['DiscountAmount']
        self.sold_price = order_dict['SoldPrice']
        self.warehouse_name = order_dict['WarehouseName']
        self.market_local = order_dict['MarketLocal']
        self.order_date = order_dict['OrderDate']
        self.sales_channel = order_dict['SalesChannel']
        self.is_amazon_prime_order = order_dict['IsAmazonPrimeOrder']
        self.buyer_name = order_dict['BuyerName']
        self.buyer_email = order_dict['BuyerEmail']
        self.buyer_street1 = order_dict['BuyerStreet1']
        self.buyer_street2 = order_dict['BuyerStreet2']
        self.buyer_city = order_dict['BuyerCity']
        self.buyer_country = order_dict['BuyerCountry']
        self.buyer_zip_code = order_dict['BuyerZipCode']
        self.buyer_user_name = order_dict['BuyerUserName']
        payment_info = Payment()
        payment_info.set_from_dict(order_dict['PaymentInfo'])
        self.payment_info = payment_info
        self.ship_service = order_dict['ShipService']
        self.ship_service_name = order_dict['ShipServiceName']
        self.ship_fee = order_dict['ShipFee']
        self.tax = order_dict['Tax']
        self.business_name = order_dict['BusinessName']
        self.ship_to_name = order_dict['ShipToName']
        self.ship_to_street1 = order_dict['ShipToStreet1']
        self.ship_to_street2 = order_dict['ShipToStreet2']
        self.ship_to_city = order_dict['ShipToCity']
        self.ship_to_zip = order_dict['ShipToZip']
        self.ship_to_state = order_dict['ShipToState']
        self.ship_to_country = order_dict['ShipToCountry']
        self.ship_to_phone = order_dict['ShipToPhone']
        self.ship_to_email = order_dict['ShipToEmail']
        self.sc_order_item_id = order_dict['SCOrderItemID']

    def as_element(self):
        search_filter_element = et.Element('Order')
        Dictionary_To_ETree.dicts_to_xml(search_filter_element, self.as_dict())
        return search_filter_element


class Payment(object):

    def __init__(self):
        self.payment_transaction_id = None
        self.payment_processor = None
        self.payment_method = None

    def as_dict(self):
        return{
            'Payment':
            {
                'PaymentTransactionId': self.payment_transaction_id,
                'PaymentProcessor': self.payment_processor,
                'PaymentMethod': self.payment_method,
            }
        }

    def as_element(self):
        payment_info_element = et.Element('PaymentInfo')
        payment_element = et.Element('Payment')
        Dictionary_To_ETree.dicts_to_xml(payment_element, self.as_dict())
        payment_info_element.append(payment_element)
        return payment_info_element

    def set_from_dict(self, payment_info_dict):
        payment_dict = payment_info_dict['Payment']
        self.payment_transaction_id = payment_dict['PaymentTransactionId']
        self.payment_processor = payment_dict['PaymentProcessor']
        self.payment_method = payment_dict['PaymentMethod']


class Item(object):

    def __init__(self):
        self.li_id = None
        self.qty = None
        self.name = None
        self.storage = None
        self.product_condition = None
        self.li_id_sku = None
        self.cost = None
        self.marketplace_id = None
        self.list_name = None
        self.last_apply_template_name = None
        self.last_apply_template_date = None
        self.serial_number_tracking_type = None
        self.warehouse_name = None
        self.product_data = None

    def as_dict(self):
        return{
            'liid': self.li_id,
            'Qty': self.qty,
            'Name': self.name,
            'Storage': self.storage,
            'ProductCondition': self.product_condition,
            'LIIDSKU': self.li_id_sku,
            'Cost': self.cost,
            'MarketplaceID': self.marketplace_id,
            'ListName': self.list_name,
            'LastApplyTemplateName': self.last_apply_template_name,
            'LastApplyTemplateDate': self.last_apply_template_date,
            'SerialNumberTrackingType': self.serial_number_tracking_type,
            'WarehouseName': self.warehouse_name,
            'ProductData': self.product_data.as_dict()
        }

    def from_tree(self, item_tree):
        self.li_id = item_tree.find('liid').text
        self.qty = item_tree.find('Qty').text
        self.name = item_tree.find('Name').text
        self.storage = item_tree.find('Storage').text
        self.product_condition = item_tree.find('ProductCondition').text
        self.li_id_sku = item_tree.find('LIIDSKU').text
        self.cost = item_tree.find('Cost').text
        self.marketplace_id = item_tree.find('MarketplaceID').text
        self.list_name = item_tree.find('ListName').text
        self.last_apply_template_name = item_tree.find('LastApplyTemplateName').text
        self.last_apply_template_date = item_tree.find('LastApplyTemplateDate').text
        self.serial_number_tracking_type = item_tree.find('SerialNumberTrackingType').text
        self.warehouse_name = item_tree.find('WarehouseName').text
        product = Product()
        product.from_item_tree(item_tree.find('ProductData'))
        self.product_data = product


class Product(object):

    def __init__(self):
        self.custom_sku = None  # (required) String- Product custom sku.
        self. ad_mid = None  # String- Adult DVD marketplace id.
        self.ep_id = None  # String- eBay product id.
        self.amazon_description = None  # String- Description for Amazon listings
        self.xiu_description = None  # String- Description for Xiu marketplace.
        self.as_in = None  # String- Amazon standard identification number.
        self.buy_id = None  # String- Buy.com (Rakuten) product id.
        self.commission = None  # Decimal- Commission dollar amount or decimal representing the commision as a
                                # percentage.
        self.commission_percent = None  # String- Values "True" or "False".
        self.declared_value = None  # Decimal- Used if you print customs forms through SolidShip.
        self.description = None  # String- General product description (Used as default).
        self.ean = None  # String- European Article Number.
        self.ebay_description = None  # String- Description for product on eBay.
        self.main_image = None  # String- Main product image URL. Image must already be hosted online.
        self.alternate_images = []
        self.image = None  # String- Image URL for alternate image. Image must already be hosted online.
        self.isbn = None  # String- International standard book number.
        self.buy_description = None  # String- Buy.com (Rakuten) product description.
        self.kit_type = None  # String- Valid values:  "Kit" or "Aggregate".
        self.kit_parent_sku = None  # String- This call does not create a kit parent sku, but affords the ability to
                                    # associate an existing sku to this sku. The kit parent sku must already be created
                                    # in solid commerce.
        self.remove_from_kit = None  # String- Valid values "Yes" or "No".
        self.manufacture = None  # String- Name of product manufacturer. Strongly recommended.
        self.model_number = None  # String- Model number. Strongly recommended if available.
        self.multiple_sku = None  # String- Product alternate sku.
        self.mystore_description = None  # String- Description for the product on your webstore.
        self.overstock_description = None  # String- Description of the product for Overstock.
        self.height = None  # Integer- Height of the product in inches.
        self.length = None  # Integer- Length of the product in inches.
        self.width = None  # Integer- Specify the product width as an integer in inches.
        self.weight = None  # Integer- Specify the product weight as an integer in ounces.
        self.product_name = None  # String- Name of the product.
        self.release_date = None  # Date- Specify the date after which the product is available. (if applicable)
        self.ship_class_id = None  # String- Provide the ID corresponding with the product ship class. Products in the
                                   # same ship class may be packaged together in a single shipment.
        self. ship_class_units = None  # String- Indicate how many units this product contains. This allows for ship
                                       # class rules to be applied.
        self.is_taxable = None  # String- Values "True" or "False"
        self.gallery_image = None  # String- Search result image.
        self.ubid_description = None  # String- Description for uBid marketplace.
        self.newegg_description = None  # String- Description for Newegg marketplace.
        self.etsy_description = None  # String-Description for Etsy marketplace.
        self.units_type = None  # String- Used to create aggregate kits.
                                # Must use one of the below values:  G  FL  OZ  LBS  PCS  ML  L
        self.units_quantity = None  # Integer- Quantity of units. (If populated, unitsType is required.)
        self.upc = None  # String-
        self.yahoo_description = None  # String- Description for Yahoo.
        self.msrp = None
        self.item_specifics = {}  # Dictionary of keys(labels): values(item specific value)

    def as_dict(self):
        return{
            'customsku': self.custom_sku,
            'productname': self.product_name,
            'admid': self. ad_mid,
            'epid': self.ep_id,
            'amazonDescription': self.amazon_description,
            'xiuDescription': self.xiu_description,
            'asin': self.as_in,
            'buyid': self.buy_id,
            'Commission': self.commission,
            'commisionIsPercent': self.commission_percent,
            'customsdeclaredValue': self.declared_value,
            'description': self.description,
            'ean': self.ean,
            'eBayDescription': self.ebay_description,
            'mainimage': self.main_image,
            'AlternateImages': [{'Image': picture_link} for picture_link in self.alternate_images],
            'Image': self.image,
            'isbn': self.isbn,
            'buyDescription': self.buy_description,
            'Kittype': self.kit_type,
            'kitParentSKU': self.kit_parent_sku,
            'removeFromKit': self.remove_from_kit,
            'manufacture': self.manufacture,
            'modelnumber': self.model_number,
            'multiplesku': self.multiple_sku,
            'mystoreDesciprtion': self.mystore_description,
            'overstockDescription': self.overstock_description,
            'height': self.height,
            'length': self.length,
            'width': self.width,
            'weight': self.weight,
            'releasedate': self.release_date,
            'shipClassID': self.ship_class_id,
            'shipClassunits': self.ship_class_units,
            'isTaxable': self.is_taxable,
            'galleryimage': self.gallery_image,
            'ubidDescription': self.ubid_description,
            'neweggDescription': self.newegg_description,
            'etsyDescription': self.etsy_description,
            'unitsType': self.units_type,
            'unitsQty': self.units_quantity,
            'upc': self.upc,
            'yahooDescription': self.yahoo_description,
            'CustomSpecifics': self.item_specifics
        }

    def as_update_dict(self):
        return{
            'CustomSKU': self.custom_sku,
            'ProductName': self.product_name,
            'ADMID': self. ad_mid,
            'ASIN': self.as_in,
            'EPID': self.ep_id,
            'ISBN': self.isbn,
            'UPC': self.upc,
            'DefaultDescription': self.description,
            'eBayDescription': self.ebay_description,
            'mystoreDesciprtion': self.mystore_description,
            'overstockDescription': self.overstock_description,
            'ubidDescription': self.ubid_description,
            'yahooDescription': self.yahoo_description,
            'mainimage': self.main_image,
            'AlternateImages': [{'Image': picture_link} for picture_link in self.alternate_images],
            'manufacture': self.manufacture,
            'MSRP': self.msrp,
            'Weight': self.weight,
            'Image': self.image,
            'height': self.height,
            'length': self.length,
            'width': self.width,
            'galleryimage': self.gallery_image,
            # 'CustomSpecifics': self.item_specifics
        }

    def from_sixbit_csv(self, csv_row):
        self.custom_sku = csv_row['SKU']
        # self.ebay_description = csv_row['eBay Description']
        self.manufacture = csv_row['Product Brand']
        self.model_number = csv_row['Product ID']
        self.height = csv_row['Dimension Depth']
        self.length = csv_row['Dimension Length']
        self.width = csv_row['Dimension Width']
        self.weight = csv_row['Weight']
        self.product_name = csv_row['Title']
        self.upc = csv_row['UPC']
        # self.item_specifics.update({re.sub('/', '', re.sub(' ', '', re.sub('IS_', '', key))): value for
        #                             key, value in csv_row.items() if 'IS_' in key and value is not None})

    def from_item_tree(self, product_tree):
        self.custom_sku = product_tree.find('ProductCustomSKU').text
        self.ep_id = product_tree.find('EPID').text
        self.as_in = product_tree.find('ASIN').text
        self.buy_id = product_tree.find('BuySKU').text
        self.declared_value = product_tree.find('CustomsDeclaredValue').text
        self.ean = product_tree.find('EAN').text
        self.main_image = product_tree.find('ImageFile').text
        self.isbn = product_tree.find('ISBN').text
        self.manufacture = product_tree.find('Manufacturer').text
        self.model_number = product_tree.find('ModelNumber').text
        self.height = product_tree.find('ProductHeight').text
        self.length = product_tree.find('ProductLength').text
        self.width = product_tree.find('ProductWidth').text
        self.weight = product_tree.find('ProductWeight').text
        self.product_name = product_tree.find('ProductName').text
        self.release_date = product_tree.find('ReleaseDate').text
        self.ship_class_id = product_tree.find('ShipClass').text
        self.ship_class_units = product_tree.find('ShipClassUnits').text
        self.is_taxable = product_tree.find('IsTaxable').text
        self.units_type = product_tree.find('UnitsType').text
        self.units_quantity = product_tree.find('UnitsQty').text
        self.upc = product_tree.find('UPC').text

    def as_update_product_xml_string(self):
        return (
            '<Product>'
            '<REQUEST xmlns="">'
            '<customsku>' + self.custom_sku + '</customsku>'
            '<productname/>'
            '<mainimage>' + self.main_image + '</mainimage>'
            '<AlternateImages><Image>' + '</Image><Image>'.join(self.alternate_images) + '</Image></AlternateImages>'
            '<scattributes/>'
            '<MarketplaceAttributes/>'
            '</REQUEST>'
            '</Product>'
        )

    def as_product_xml_string(self):
        self_dict = self.as_dict()
        product_element = et.Element('Product')
        request_element = et.Element('REQUEST', {'xmlns': ''})
        Dictionary_To_ETree.dicts_to_xml(request_element, self_dict)
        product_element.append(request_element)
        return ElementTree.tostring(product_element).decode("utf-8")


class Shipment(object):

    def __init__(self):
        self.sc_sale_id = None  # CONDITIONAL: One of the following must be included: POID, SCSaleID, StoreOrderID
        self.po_id = None  # CONDITIONAL
        self.store_order_id = None  # CONDITIONAL
        self.ship_date = None  # Date/Time: For example: 12/09/2017 00:00:00
        self.ship_cost = None  # Float
        self.package_type = None  # String
        # NotDefined = -1, CustomPackaging = 0, Fedex10KgBox = 1, Fedex25KgBox = 2, FedexBox = 3, FedexPak = 4,
        # FedexEnvelope = 5, FedexTube = 6, DHLLetter = 7, DHLPackage = 8, UPSLetter = 9, UPSTube = 10, UPSPAK = 11,
        # UPSExpressBox = 101, UPSPallet = 15, UPS25KGBox = 20, UPS10KGBox = 21,UPSSmallExpressBox = 102,
        # UPSMediumExpressBox = 103, UPSLargeExpressBox = 104, UPSFlats = 105, UPSParcels = 106, UPSBPM = 107,
        # UPSFirstClass = 108, UPSPriority = 109, UPSMachinables = 110, UPSIrregulars = 111, UPSParcelPost = 112,
        # UPSBPMParcel = 113, UPSMediaMail = 114, UPSBMPFlat = 115, UPSStandardFlat = 116, USPSLetter = 17,
        # USPSTube = 19, USPSFlat = 22, USPSRectParcel = 23, USPSNonRectParcel = 24, USPSFlatRateEnvelope = 25,
        # USPSFlatRateMediumBox = 26, USPSFlatRateLargeBox = 27, USPSFlatRateSmallBox = 28,
        # USPSFlatRatePaddedEnvelope = 29, USPSPostcard = 30, USPSEnvelope = 31, USPSRegionalRateBoxA = 32,
        # USPSRegionalRateBoxB = 33, USPSInternationalFlatRateDVDBox = 34,
        # USPSInternationalFlatRateLargeVideoBox = 35, USPSFlatRateLegalEnvelope = 36,
        # USPSFlatRateGiftCardEnvelope = 37, USPSFlatRateWindowEnvelope = 38, USPSFlatRateCardBoardEnvelope = 39,
        # USPSFlatRateSmallEnvelope = 40, USPSRegionalRateBoxC = 41, USPSFlatRateLargeBoardGameBox = 42,
        # USPSFlatRateRegularBox = 43
        self.shipping_type_code = None  # See shipping type code file
        self.tracking_number = None  # String
        self.quantity = None  # Int number of pieces included in shipment,
        # if left blank will default to all pieces of order.
        self.listing_id = None  # String listing ID associated with items(s) in shipment (optional)
        self.exchange_id = None  # String listing ID associated with items(s) in shipment (optional)
        self.warehouse_id = None  # String ID(sku) associated with items(s) in shipment (optional)
        self.marketplace = None  # String **required if** only the store_order_id is used
        # NotDefined = -1, Any = 0, Amazon = 1, Half = 2, eBay = 3, Yahoo = 4, MyStore = 5, AmazonCA = 6,
        # AmazonJP = 7, AmazonDE = 8, amazonUK = 9, ADM = 10, ADT = 11, ShoppingDotCom = 12, PriceGrabber = 13,
        # BarnesAndNoble = 14, Alibris = 15, AbeBooks = 16, amazonFR = 17, Overstock = 18, uBid = 19, Froogle = 20,
        # PriceWatch = 21, Shopzilla = 22, Cnet = 23, NexTag = 24, PriceTag = 25, LiveDeal = 26, Ciao = 27,
        # eBayMyStore = 28, YahooStore = 29, CactusComplete = 30, AmazonSilverSeller = 31, Buy = 32, Shop = 33,
        # Sears = 34, Newegg = 35, Etsy = 36, Xiu = 37, Jet = 38, Walmart = 39

    def as_dict(self):
        return{
            'SCSaleID': self.sc_sale_id,
            'POID': self.po_id,
            'StoreOrderID': self.store_order_id,
            'ShipDate': self.ship_date,
            'ShippingTypeCode': self.shipping_type_code,
            'ShipCost': self.ship_cost,
            'PackageType': self.package_type,
            'TrackingNumber': self.tracking_number,
            'Qty': self.quantity,
            'ListingID': self.listing_id,
            'ExchangeID': self.exchange_id,
            'WarehouseID': self.warehouse_id,
            'Marketplace': self.marketplace
        }

    def as_dict_for_errors(self):
        return {

        }

    def as_shipment_element(self):
        self_dict = self.as_dict()
        shipment_element = et.Element('Shipment')
        shipment_upload_details_element = et.Element('UploadShippingDetailsShipment')
        Dictionary_To_ETree.dicts_to_xml(shipment_upload_details_element, self_dict)
        shipment_element.append(shipment_upload_details_element)
        return shipment_element


class OrderSearchFilter(object):

    def __init__(self):
        self.page = None  # Int
        self.records_per_page_count = None  # Int
        self.filter_by_item_store_notification_status = None  # Boolean
        self.item_store_notification_status = None  # [NotDefined, OrderProcessingConfirmed, ShippingConfirmed,
        # ShippingConfirmationSent, CancellationSent, CancellationConfirmed, OrderProcessingSent, ShippedToBuyer,
        # Unfulfillable, OrderProcessingSentToThirdPartyShipping, ShippingConfirmedFromThirdPartyShipping, PickedUp,
        # ReadyForPickup, ReadyForPickupFailed]
        self.filter_by_order_status = None  # Boolean
        self.order_status = None  # [NOTAVAILABLE, COMPLETED, PAID, WAITINGFORBUYER, WAITINGFORSELLER, CANCELLED,
        # PARTIALLYCOMPLETED]
        self.filter_by_custom_order_status = None  # Boolean
        self.custom_order_status = None  # String
        self.filter_by_address_verification_failed = None  # Boolean
        self.filter_by_dates = None  # Boolean
        self.start_date = None  # Date/Time
        self.end_date = None  # Date/Time
        self.search_type = None  # [ByProductName, ByManufacture, BySKU, ByUPC, ByASIN, ByISBN, ByBuyerName,
        # ByBuyerEmail, ByBuyerLastName, ScreenName, ByShipToName, ByShipToLastName, ByShipToEmail, ByShipZipCode,
        # ByShipToStreet1, ByShipToCity, ByShipToCountry, ByShipToState, ByShipToCompany, MarketOrderNumber,
        # InvoiceNumber, ManufactureModelNumber, PackageID, ListingID, BySCOrderID, ByStorage, ByPO, ByPartialSKU,
        # BySalesChannel, ByStoreReturnID, ByRMANumber, ListingSKU, BySerialNumber, ByAlternateOrderId]
        self.search_value = None  # String
        self.sort_by = None  # String
        self.sort_descend = None  # Boolean
        self.order_search_format = None  # [ByOrder, ByOrderItems, ByTrackingNumbers]
        self.last_order_status_change_date = None  # Date/Time
        self.show_order_status_last_change_last_change_dt = None  # Boolean
        self.filter_by_warehouse = None  # Boolean
        self.warehouse_list = None  # String
        self.view_options = None  # String
        
    def as_dict(self):
        return{
            'page': self.page,
            'recordsPerPageCount': self.records_per_page_count,
            'filterByItemStoreNotificationStatus': self.filter_by_item_store_notification_status,
            'ItemStoreNotificationStatus': self.item_store_notification_status,
            'FilterByOrderStatus': self.filter_by_order_status,
            'OrderStatus': self.order_status,
            'FilterByCustomOrderStatus': self.filter_by_custom_order_status,
            'CustomOrderStatus': self.custom_order_status,
            'filterAddressVerificationFailed': self.filter_by_address_verification_failed,
            'FilterByDates': self.filter_by_dates,
            'fromDate': self.start_date,
            'toDate': self.end_date,
            'SearchType': self.search_type,
            'SearchValue': self.search_value,
            'SortBy': self.sort_by,
            'SortDescend': self.sort_descend,
            'OrdersSearchFormat': self.order_search_format,
            'LastOrderStatusChangedDate': self.last_order_status_change_date,
            'ShowOrderStatusLastChangeDT': self.show_order_status_last_change_last_change_dt,
            'FilterByWarehouse': self.filter_by_warehouse,
            'WarehousesList': self. warehouse_list
        }

    def as_element(self):
        search_filter_element = et.Element('searchFilter')
        Dictionary_To_ETree.dicts_to_xml(search_filter_element, self.as_dict())
        return search_filter_element


class CompanyList(object):

    def __init__(self):
        self.type = None
        self.list_name = None
        self.list_id = None

    def as_dict(self):
        return {
            'type': self.type,
            'ListName': self.list_name,
            'ListID': self.list_id
        }

    def from_dict(self, list_dict):
        self.list_name = list_dict['ListName']
        self.list_id = list_dict['ListID']
