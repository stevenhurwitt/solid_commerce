from classes import Distributor
import csv
from classes import SolidCommerce


class OW(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(OW, self).__init__('OW', "Oscar Wilson")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.manufacturer_file_path_root = r'T:/ebay/' + manufacturer_short_name
        self.inventory_file_path = r'T:/eBay/Oscar_Wilson/Inventory/McHenry.csv'

    def inventory_from_default(self, products):
        return self.inventory_from_file(products)

    def inventory_from_file(self, products):
        data_set_from_ow = self.parse_file_to_dictionary()
        for product in products:
            try:
                product.warehouse_with_inventory_dicts = {'WH_OW-MO': data_set_from_ow[product.sku]['Qty on Hand'],
                                                          'WH_McHenry Inbound': data_set_from_ow[product.sku]['Qty on Hand']}
                product.selective_quantity = data_set_from_ow[product.sku]['Qty on Hand']
                product.fulfillment_source = 'DropShipper'
                product.cost = data_set_from_ow[product.sku]['Cost']
                if product.sku.split('~')[0] == 'OEP':
                    del product.warehouse_with_inventory_dicts['WH_McHenry Inbound']
            except KeyError:
                self.log_distributor_event(
                    self.get_log_dict(
                        product.sku,
                        'Error - No Inventory',
                        'Catalogue Product not available at distributor'
                    )
                )
                product.warehouse_with_inventory_dicts = {'WH_OW-MO': '0',
                                                          'WH_McHenry Inbound': '0'}

                if product.sku.split('~')[0] == 'OEP':
                    del product.warehouse_with_inventory_dicts['WH_McHenry Inbound']
        return products

    def parse_file_to_dictionary(self):
        ow_dict = {}
        csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)
        with open(self.inventory_file_path, 'r', encoding='utf-8', errors='replace') as f:
            ow_products = []
            for row in csv.reader(f, dialect='piper'):
                try:
                    if row[0] == 'HOP':
                        row[0] = 'AYP'
                    elif row[0] == 'HYG':
                        row[0] = 'HYD'
                    elif row[0] == 'ORE':
                        row[0] = 'OEP'
                    product_dict = {
                        'OW Vendor Code': row[0].strip(),
                        'Manufacturer Item No': str(row[1].strip()),
                        'OW Item Number': row[2],
                        'temp_sku': row[0].strip() + '~' + str(row[1].strip()),
                        'Description': row[3],
                        'Cost': row[4],
                        'MSRP': row[5],
                        'Qty on Hand': row[6],
                        'Sub To Manufacturer Item number': row[7],
                        'Sub To Vendor Code': row[8],
                        'Status': row[9],
                        'Manufacturer Code': row[10],
                        'Manufacturer': row[11],
                        'OW Sub Number': row[12]}
                    ow_products.append(product_dict)
                except Exception as inst:
                    self.log_distributor_event(self.get_log_dict(row, 'Error - Distributor Inventory File', inst))
            for item in list(ow_products):
                ow_dict[item['temp_sku']] = item
            return ow_dict

    def shipping_from_file(self):
        ow_tracking_filepath = 'T:/ebay/Oscar_Wilson/Tracking/McHenryTracking.csv'
        dropships = [
            order for order in csv.DictReader(open(ow_tracking_filepath)) if
            order['Ship To Name '] != 'MCHENRY POWER EQUIPMENT'
        ]
        for dropship in dropships:
            self.update_shipping(dropship)

    @staticmethod
    def get_pending_dropship_orders():
        solid_api = SolidCommerce.API()
        order_search_filter = SolidCommerce.OrderSearchFilter()
        order_search_filter.page = '1'
        order_search_filter.records_per_page_count = '1000'
        order_search_filter.filter_by_custom_order_status = 'true'
        order_search_filter.custom_order_status = 'Waiting For OW'
        order_search_filter.order_search_format = 'ByOrderItems'
        return solid_api.search_orders_v6(order_search_filter.as_element())

    def update_shipping(self, order_record):
        solid_api = SolidCommerce.API()
        shipper_code = order_record['Tracking Number '][0:2]
        shipping_type_cases = {'1Z': 'UPSGround',
                               'SP': 'ShippingTypeCode'}
        shipping_package_type_cases = {'1Z': '0', 'SP': '0'}
        shipment_api_update = SolidCommerce.Shipment()
        shipment_api_update.sc_sale_id = order_record['P.O. ']
        shipment_api_update.tracking_number = order_record['Tracking Number ']
        shipment_api_update.marketplace = '3'
        try:
            shipment_api_update.shipping_type_code = shipping_type_cases[shipper_code]
            shipment_api_update.package_type = shipping_package_type_cases[shipper_code]
            solid_api_shipping_update_call = SolidCommerce.API()
            solid_api_shipping_update_call.update_ebay_shipment(shipment_api_update.as_shipment_element())
            try:
                order_object = self.get_order_from_solid_by_ebay_number(order_record['P.O. '])[0]
                order_object.status = 'Drop Shipped OW'
                solid_api.update_order_status(order_object)
            except IndexError:
                print('Order ' + order_record['P.O. '] + ' Does Not Exist')
        except KeyError:
            print('Unknown Tracking Number format for order# ' + order_record['P.O. '])


