from classes import SolidCommerce
from classes import Distributor
from lxml import etree as et
from tools.Dictionary_To_ETree import dicts_to_xml
from xml.etree import ElementTree
from lxml import etree as element_tree
import requests
import csv
from bs4 import BeautifulSoup
import re
import datetime


class CPD(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(CPD, self).__init__('CPD', "Central Power Distributors")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.manufacturer_file_path_root = r'T:/ebay/' + manufacturer_short_name

    def inventory_from_default(self, products):
        return self.inventory_from_api(products)

    # turns inventory response from CPD inquiry API into inventory objects
    def inventory_from_api(self, inventory_objects):
        end_point_url = "http://2cpdonline.com/mh/inquiry.asp"
        item_element = et.Element('inventory_request')
        inquiries = []
        parts = {}
        inquiry_count = 1
        i = 0
        for inventory_object in inventory_objects:
            inventory_inquiry = InventoryInquiry()
            item_element.append(
                inventory_inquiry.as_xml_item_element_from_inventory_object(
                    inventory_object, self.manufacturer_short_name))
            i += 1
            if i > 999:
                inquiries.append(item_element)
                item_element = et.Element('inventory_request')
                i = 0
        inquiries.append(item_element)
        responses = []
        for inquiry in inquiries:
            print('Inquiry ' + str(inquiry_count))
            response = requests.post(end_point_url, data=ElementTree.tostring(inquiry))
            responses.append(response)
            inquiry_count += 1
        parser = element_tree.XMLParser(recover=True, encoding='latin1')
        # print(inquiries[0].text)
        # print(responses[0].text)
        for response in responses:
            tree = element_tree.fromstring(response.content, parser=parser)
            for part in tree:
                parts[part.find('PartNumberInquired').text] = {'ItemID': part.find('CustomerInternalSKU').text,
                                                               'Quantity': part.find('QuantityAvailable').text,
                                                               # 'MNQuantity': part.find('MNQuantityAvailable').text,
                                                               # 'WIQuantity': part.find('WIQuantityAvailable').text,
                                                               'Cost': part.find('UnitPrice').text,
                                                               'MSRP': part.find('RetailPrice').text,
                                                               'UPC': part.find('UpcCode').text}
        for inventory_object in inventory_objects:
            try:
                product_id = inventory_object.sku.split('~')[1]
                inventory_object.fulfillment_source = 'DropShipper'
                inventory_object.cost = parts[product_id]['Cost']
                inventory_object.list_price = parts[product_id]['MSRP']
                inventory_object.selective_quantity = parts[product_id]['Quantity']
                inventory_object.total_quantity = parts[product_id]['Quantity']
                inventory_object.upc = parts[product_id]['UPC']
                inventory_object.minimum_order_qty = '1'
                if parts[product_id]['Quantity'] is not None:
                    inventory_object.warehouse_with_inventory_dicts = {
                        # 'WH_CPD-MN': parts[product_id]['MNQuantity'],
                        'WH_CPD-WI': parts[product_id]['Quantity'],
                        'WH_McHenry Inbound': parts[product_id]['Quantity']
                    }
                else:
                    self.log_distributor_event(
                        self.get_log_dict(
                            inventory_object.sku,
                            'Error - No Inventory',
                            'Catalogue Product not available at distributor'
                        )
                    )
                    inventory_object.warehouse_with_inventory_dicts = {'WH_CPD-WI': '0',
                                                                       # 'WH_CPD-MN': '0',
                                                                       'WH_McHenry Inbound': '0'}
            except KeyError:
                self.log_distributor_event(
                    self.get_log_dict(
                        inventory_object.sku,
                        'Error - No Inventory',
                        'Catalogue Product not available at distributor'
                    )
                )
        return inventory_objects
        
    def get_dealer_inventory(self):
        end_point_url = "http://2cpdonline.com/mh/inquiry.asp"
        item_element = et.Element('inventory_request')
        inquiries = []
        parts = []
        inquiry_count = 1
        i = 0
        with open(self.temp_filepath, encoding="utf-8", errors="ignore")as file:
            products = csv.DictReader(file)
            for product in products:
                product['ProductID'] = product['SKU'].split('~')[1].rstrip('s').rstrip('-')
                inventory_inquiry = InventoryInquiry()
                inventory_inquiry.customer_number = None
                inventory_inquiry.manufacturer_code = self.manufacturer_short_name
                inventory_inquiry.part_number = product['ProductID']
                inventory_inquiry.quantity = '10'
                inventory_inquiry.inquiry_sequence_number = str(inquiry_count)
                inventory_inquiry.customer_internal_sku = self.manufacturer_short_name + '~' + \
                    product['ProductID']
                item_element.append(inventory_inquiry.as_xml_item_element())
                i += 1
                if i > 999:
                    inquiries.append(item_element)
                    item_element = et.Element('inventory_request')
                    i = 0
        inquiries.append(item_element)
        responses = []
        for inquiry in inquiries:
            print('Inquiry ' + str(inquiry_count))
            responses.append(requests.post(end_point_url, data=ElementTree.tostring(inquiry)))
            inquiry_count += 1
        parser = element_tree.XMLParser(recover=True, encoding='latin1')
        for response in responses:
            # print(response)
            # print(response.content)
            tree = element_tree.fromstring(response.content, parser=parser)
            for part in tree:
                inventory_reply = InventoryReply()
                inventory_reply.from_part_element(part)
                parts.append(inventory_reply)
        return [part.as_dict() for part in parts]

    def inventory_file_from_api(self):
        file_path = self.get_user_file_selection()
        self.temp_filepath = file_path
        save_filepath = file_path.split('.')[0] + '_CPDResponse.csv'
        dealer_inventory = self.get_dealer_inventory()
        self.write_odict_to_csv_to_filepath(dealer_inventory, save_filepath)

    def shipping_from_api(self):
        solid_api = SolidCommerce.API()
        pending_dropships = self.get_pending_dropship_orders()
        session = self.get_session()
        orders_url = 'https://ezone.cpdonline.com/cgi-bin/edmas_order_review.mac/CurrentOrders?p1=&p2=C&p3=999&p4=*&p5='
        cpd_orders_html = session.get(orders_url).text
        orders_dicts = self.get_orders_dicts(cpd_orders_html)
        for pending_dropship in pending_dropships:
            try:
                order_page_dict = self.get_order_page_dict(
                    session.get(orders_dicts[pending_dropship.sale_id]['href']).text
                )
                self.update_shipping(order_page_dict)
                pending_dropship.status = 'Drop Shipped CPD'
                solid_api.update_order_status(pending_dropship)
            except IndexError:
                print('No Shipping Info Available for Order ' + pending_dropship.as_dict()['saleID'])
            except KeyError:
                try:
                    invoice_page_dict = self.shipping_from_invoice_api(session, pending_dropship)
                    self.update_shipping(invoice_page_dict)
                    pending_dropship.status = 'Drop Shipped CPD'
                    solid_api.update_order_status(pending_dropship)
                except KeyError:
                    print('cannot find order ' + pending_dropship.as_dict()['saleID'])
                except IndexError:
                    print('No Shipping Info Available for Order ' + pending_dropship.as_dict()['saleID'])

    def raw_shipping_from_api(self):
        solid_api = SolidCommerce.API()
        session = self.get_session()
        orders_url = 'https://ezone.cpdonline.com/cgi-bin/edmas_order_review.mac/CurrentOrders?p1=&p2=C&p3=999&p4=*&p5='
        cpd_orders_html = session.get(orders_url).text
        orders_dicts = self.get_orders_dicts(cpd_orders_html)
        for order_number, order_dict in orders_dicts.items():
            try:
                order_page_html = session.get(order_dict['href']).text
                order_page_dict = self.get_order_page_dict(order_page_html)
                self.update_shipping(order_page_dict)
                search_filter = SolidCommerce.OrderSearchFilter()
                search_filter.page = '1'
                search_filter.records_per_page_count = '1000'
                search_filter.order_search_format = 'ByOrderItems'
                search_filter.search_type = 'BySCOrderID'
                search_filter.search_value = order_dict['P/O #']
                solid_order = solid_api.search_orders_v6(search_filter.as_element())[0]
                solid_order.status = 'Drop Shipped CPD'
                solid_api.update_order_status(solid_order)
            except IndexError:
                pass

    def shipping_from_invoice_api(self, session, pending_dropship):
        order_url = ('https://ezone.cpdonline.com/cgi-bin/edmas_InvoiceHistoryReview.mac/'
                     'InvoiceHistory?p1=' + pending_dropship.sale_id + '&p2=&p3=999&p4=*%20&p5=&p6=')
        cpd_orders_html = session.get(order_url).text
        order_dict = self.get_orders_dicts(cpd_orders_html)
        order_page_dict = self.get_order_page_dict(
            session.get(order_dict[pending_dropship.sale_id]['href']).text
        )
        return order_page_dict

    def shipping_from_invoice_api_by_ebay_order_number(self, session, order_id):
        order_url = ('https://ezone.cpdonline.com/cgi-bin/edmas_InvoiceHistoryReview.mac/'
                     'InvoiceHistory?p1=' + order_id + '&p2=&p3=999&p4=*%20&p5=&p6=')
        cpd_orders_html = session.get(order_url).text
        order_dict = self.get_orders_dicts(cpd_orders_html)
        order_page_dict = self.get_order_page_dict(
            session.get(order_dict[order_id]['href']).text
        )
        return order_page_dict

    def shipping_from_7_day_invoice_api(self):
        solid_api = SolidCommerce.API()
        pending_dropships = self.get_all_paid_orders()
        session = self.get_session()
        orders_url = ('https://ezone.cpdonline.com/cgi-bin/edmas_order_review.mac'
                     '/CurrentOrders?p1=&p2=&p3=007&p4=*%20&p5=&p6=')
        cpd_orders_html = session.get(orders_url).text
        orders_dicts = self.get_orders_dicts(cpd_orders_html)
        for pending_dropship in pending_dropships:
            try:
                order_page_dict = self.get_order_page_dict(
                    session.get(orders_dicts[pending_dropship.store_order_id]['href']).text
                )
                self.update_shipping(order_page_dict)
                pending_dropship.status = 'Drop Shipped CPD'
                solid_api.update_order_status(pending_dropship)
            except KeyError:
                pass
            except IndexError:
                print(pending_dropship.store_order_id)

    @staticmethod
    def update_shipping(order_record):
        shipper_code = order_record['ShippingCarrier']
        shipping_type_cases = {
            'USPS-Priority Mail': 'USPSFirstClass',
            'USPS-First Class M': 'USPSPriorityMail',
            'USPS-First Class P': 'USPSPriorityMail',
            'UPS-UPS® Ground-COL': 'UPSGround',
            'UPS-UPS® Groun': 'UPSGround',
            'R & L CAR-LTL': 'RLCarriersFreight',
            'SPDY-Ground': 'SpeeDeeDelivery',
            'SPDY-Groun': 'SpeeDeeDelivery',
            'Metro Ground': 'SpeeDeeDelivery'
        }
        shipment_api_update = SolidCommerce.Shipment()
        try:
            shipment_api_update.sc_sale_id = order_record['Your Order #']
        except KeyError:
            shipment_api_update.sc_sale_id = order_record['Your Order No']
        shipment_api_update.tracking_number = order_record['TrackingNumber']
        shipment_api_update.shipping_type_code = shipping_type_cases[order_record['ShippingService']]
        shipment_api_update.package_type = '0'
        shipment_api_update.marketplace = '3'
        shipment_api_update.ship_cost = order_record['SHIPPING']
        solid_api_shipping_update_call = SolidCommerce.API()
        solid_api_shipping_update_call.update_ebay_shipment(shipment_api_update.as_shipment_element())

    def get_order_page_dict(self, order_page_html):
        order_page_dict = {}
        soup = BeautifulSoup(order_page_html, features='lxml')
        order_portions = soup.select('#mainFull')[0].select('table')
        order_specifics = order_portions[2]
        order_addresses = order_portions[3]
        order_shipment_details = order_portions[4]
        order_shipment_total = order_portions[5]
        order_specifics_labels = [
            td.text.strip().strip(':') for td in order_specifics.select('td.classTableCellHdg')
        ]
        order_specifics_fields = [
            td.text.strip() for td in order_specifics.select('td.classTableCellvAlign') if td.text.strip() is not ''
        ]
        order_page_dict.update(dict(zip(order_specifics_labels, order_specifics_fields)))
        order_address1_fields = [
            td.text.strip() for td in order_addresses.select('td.classTableCellvAlignTop') if
            td.text.strip() is not ''
        ]
        order_address2_fields = [
            td.text.strip() for td in order_addresses.select('td.classTableCellvAlignCenter') if
            td.text.strip() is not ''
        ]
        order_address3_fields = [
            ', '.join(re.sub(' +', ' ', td.text.strip()).split(' ')) for td in
            order_addresses.select('td.classTableCellvAlignBottom') if td.text.strip() is not ''
        ]
        order_page_dict.update({'ShipToPhone': order_address2_fields.pop(0)})
        order_page_dict.update({
            'ShipToName': order_address1_fields[1],
            'ShipToAddress1': order_address2_fields[1],
            'ShipToAddress2': order_address3_fields[1]
        })
        order_page_dict.update({
            'BillToName': order_address1_fields[0],
            'BillToAddress1': order_address2_fields[0],
            'BillToAddress2': order_address3_fields[0]
        })
        order_shipment_details_header_row = [
            th.text.strip() for th in order_shipment_details.select('th.classTableCellHdg')
        ]
        order_shipment_details_items = order_shipment_details.select('tr')[2:-2]
        order_item_dicts = []
        for order_shipment_details_item in order_shipment_details_items:
            order_item_dicts.append(dict(zip(order_shipment_details_header_row,
                                             [td.text.strip() for td in order_shipment_details_item.select('td')]
                                             )))
        order_page_dict.update({'OrderItems': order_item_dicts})
        order_shipment_details_shipping_cost = [
            td.text.strip().strip('&nbsp').strip('$') for td in order_shipment_details.select('tr')[-2].select('td') if
            td.text.strip() is not ''
        ]
        order_page_dict.update({order_shipment_details_shipping_cost[0]: order_shipment_details_shipping_cost[1]})
        order_shipment_details_shipping_details = order_shipment_details.select('tr')[-1]
        tracking_string = [
            ', '.join(str(td).split('<br/>')).split('>')[1] for
            td in order_shipment_details_shipping_details.select('td') if
            td.text.strip() is not ''
        ][0]
        tracking_fields = [field.strip('&amp;nbsp').strip('</td').strip() for field in tracking_string.split(',')]
        order_page_dict.update({
            'TrackingDate': tracking_fields[0],
            'ShippingCarrier': tracking_fields[1].split('-')[0],
            'ShippingService': tracking_fields[1],
            'TrackingNumber': tracking_fields[2],
            'PackageWeight': tracking_fields[3]
        })
        estimated_total = [td.text.strip() for td in order_shipment_total.select('td') if td.text.strip() is not '']
        order_page_dict.update({estimated_total[1]: estimated_total[2].strip('$')})
        return order_page_dict

    def get_orders_dicts(self, orders_html):
        soup = BeautifulSoup(orders_html, features='lxml')
        orders = soup.select('#tInvHistListColHdrs')[0].select('tr')
        header_row = [td.text.strip() for td in orders[0].select('th')]
        orders_dicts = {}
        for order in orders[1:]:
            order_dict = dict(zip(header_row, [field.text.strip() for field in order.select('td')]))
            order_dict_href = order.select('td')[1].select('a')[0]['href']
            order_dict.update({'href': order_dict_href})
            orders_dicts[order_dict['P/O #']] = order_dict
        return orders_dicts

    @staticmethod
    def get_pending_dropship_orders():
        solid_api = SolidCommerce.API()
        order_search_filter = SolidCommerce.OrderSearchFilter()
        order_search_filter.page = '1'
        order_search_filter.records_per_page_count = '1000'
        order_search_filter.order_search_format = 'ByOrderItems'
        # order_search_filter.filter_by_custom_order_status = 'true'
        # order_search_filter.custom_order_status = 'Waiting For CPD'
        order_search_filter.order_status = 'PAID'
        order_search_filter.filter_by_order_status = 'true'
        order_search_filter.warehouse_list = '42191'
        order_search_filter.filter_by_warehouse = 'true'
        return solid_api.search_orders_v6(order_search_filter.as_element())

    @staticmethod
    def get_all_paid_orders():
        solid_api = SolidCommerce.API()
        order_search_filter = SolidCommerce.OrderSearchFilter()
        order_search_filter.page = '1'
        order_search_filter.records_per_page_count = '1000'
        order_search_filter.custom_order_status = '2'
        order_search_filter.order_search_format = 'ByOrderItems'
        return solid_api.search_orders_v6(order_search_filter.as_element())

    def get_dropshipped_errors_previous_month(self):
        solid_api = SolidCommerce.API()
        search_filter = SolidCommerce.OrderSearchFilter()
        search_filter.page = '1'
        search_filter.records_per_page_count = '10000'
        search_filter.order_search_format = 'ByOrderItems'
        search_filter.custom_order_status = 'Drop Shipped CPD'
        search_filter.filter_by_custom_order_status = 'true'
        search_filter.filter_by_dates = '1'
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        search_filter.start_date = last_month.strftime("%m/01/%Y")
        search_filter.end_date = last_month.strftime("%m/%d/%Y")
        dropshipped_orders = [
            order.as_dict() for order in solid_api.search_orders_v6(search_filter.as_element()) if
            int(order.order_date.split('/')[0]) == int(last_month.strftime("%m/01/%Y").split('/')[0])
        ]
        print(len(dropshipped_orders))
        session = self.get_session()
        combined_order_errors = []
        for order in dropshipped_orders:
            order['ReasonOfError'] = ''
            try:
                shipping_info = self.shipping_from_invoice_api_by_ebay_order_number(session, order['saleID'])
                shipping_info['PackageWeight'] = str(float(shipping_info['PackageWeight'].split(' ')[0]) * 16)
                combined_dict = {**order, **shipping_info}
                combined_dict['CustomerTotal'] = float(combined_dict['TotalSale']) + float(combined_dict['ShipFee'])
                if float(combined_dict['SHIPPING']) > float(combined_dict['ShipFee']):
                    combined_dict['ReasonOfError'] = 'Cost greater than charged'
                    combined_order_errors.append(combined_dict)
                elif combined_dict['ShippingCarrier'] == 'UPS' and float(combined_dict['SHIPPING']) > 1.75:
                    combined_dict['ReasonOfError'] = 'UPS not Charged Correctly'
                    combined_order_errors.append(combined_dict)
                elif float(combined_dict['PackageWeight']) > (
                        float(combined_dict['Weight'] * float(combined_dict['QTY']))):
                    combined_dict['ReasonOfError'] = 'Shipped Weight Higher'
                    combined_order_errors.append(combined_dict)
                elif .88 * combined_dict['CustomerTotal'] - float(combined_dict['Invoice Total'].replace(',', '')) < 0:
                    combined_dict['ReasonOfError'] = 'Net Sale Loss'
                    combined_order_errors.append(combined_dict)
                else:
                    continue
            except IndexError:
                pass
            except KeyError:
                pass
        self.write_list_of_dicts_to_csv(
            combined_order_errors,
            'T:/ebay/CPD/Tracking/Tracking Errors/CPD_Errors' + last_month.strftime("%B.%Y") + '.csv'
        )

    def get_session(self):
        # url = 'https://ezone.cpdonline.com/cgi-bin/edmas8a.mac/CheckUserIdPassword'
        # data = {
        #     'userid': '22462',
        #     'userpassword': '3622elmst',
        #     'x': '0',
        #     'y': '0'
        # }
        # headers = {
        #     'Host': 'ezone.cpdonline.com',
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        #     'Referer': 'https://ezone.cpdonline.com/cgi-bin/edmas8a.mac/CheckUserIdPassword',
        #     'Content-Type': 'application/x-www-form-urlencoded',
        #     'Connection': 'keep-alive',
        #     'Upgrade-Insecure-Requests': '1',
        # }
        session = requests.session()
        # response = session.post(url, data, headers=headers)
        # print(response)
        # print(response.text)
        session.cookies.update({
            'CPD_USERID': '22462',
            'EZONE_USERID': '22462'
        })
        return session

    def shipping_check_for_errors(self):
        pass

    def api_submit_dropship_order(self):
        solid_api = SolidCommerce.API()
        order_number = '206066'  # input('Enter Order Number: ')
        search_filter_element = SolidCommerce.OrderSearchFilter()
        search_filter_element.search_type = 'BySCOrderID'
        search_filter_element.search_value = order_number
        search_filter_element.order_search_format = 'ByOrderItems'
        search_filter_element.page = '1'
        search_filter_element.records_per_page_count = '1000'
        order_items = solid_api.search_orders_v6(search_filter_element.as_element())
        order_items_dicts = [order_item.as_dict() for order_item in order_items]
        shipment_orders = []
        print('\nConfirm Quantity To Ship\n-----------------')
        for order_item_dict in order_items_dicts:
            qty = self.get_order_quantity_selection(order_item_dict)
            order_item_dict['ShipQuantity'] = str(qty)
            cpd_availability = self.make_inventory_inquiry([{
                'SKU': order_item_dict['SKU'],
                'Qty': order_item_dict['ShipQuantity']
            }])
            if qty > 0:
                shipment_orders.append(order_item_dict)
        print(shipment_orders)

    def make_inventory_inquiry(self, item_dicts):
        end_point_url = "http://2cpdonline.com/mh/inquiry.asp"
        inventory_request_element = et.Element('inventory_request')
        for item_dict in item_dicts:
            inventory_request_element.append(self.get_inventory_inquiry_item_element(item_dict))
            data = ElementTree.tostring(inventory_request_element)
            print(data)
            response = requests.post(end_point_url, data=data)
            print(response)
            print(response.content)
            return ''

    @staticmethod
    def verify_manufacturer_code(mfr_code):
        if mfr_code == 'AYP':
            return 'HOP'
        else:
            return mfr_code

    def get_inventory_inquiry_item_element(self, item_dict):
        inventory_inquiry = InventoryInquiry()
        parsed_sku = item_dict['SKU'].split('~')
        inventory_inquiry.manufacturer_code = self.verify_manufacturer_code(parsed_sku[0])
        inventory_inquiry.part_number = parsed_sku[1]
        inventory_inquiry.quantity = item_dict['Qty']
        inventory_inquiry.customer_internal_sku = item_dict['SKU']
        return inventory_inquiry.as_xml_item_element()

    def get_order_quantity_selection(self, order_items_dict):
        try:
            qty = int(input('Quantity: ' + order_items_dict['Qty'] + ' SKU: ' + order_items_dict['SKU'] + ': '))
            if qty != int(order_items_dict['Qty']):
                confirmation = input('Confirm shipment quantity different than order quantity [y/n]: ')
                if confirmation == 'y':
                    return qty
                elif confirmation == 'n':
                    return self.get_order_quantity_selection(order_items_dict)
                else:
                    print('Not a valid selection please try again: ')
                    self.get_order_quantity_selection(order_items_dict)
            else:
                return qty
            print('There was an unknown error please try again: ')
            self.get_order_quantity_selection(order_items_dict)
        except ValueError:
            print('Not a valid quantity, please enter a valid number: ')
            return self.get_order_quantity_selection(order_items_dict)


class InventoryInquiry(object):

    def __init__(self):
        self.customer_number = None
        self.manufacturer_code = None
        self.part_number = None
        self.quantity = None
        self.client_no_sup_nla = None
        self.upc_code = None
        self.inquiry_sequence_number = None
        self.customer_internal_sku = None

    def as_dict(self):
        return {'CustomerNumber': self.customer_number,
                'CustomerInternalSKU': self.customer_internal_sku,
                'InquirySequence_number': self.inquiry_sequence_number,
                'ManufacturerCode': self.manufacturer_code,
                'PartNumber': self.part_number,
                'Quantity': self.quantity,
                'UpcCode': self.upc_code,
                'ClientNoSupNLA': self.client_no_sup_nla}

    def as_xml_item_element(self):
        item_element = et.Element('SmartOrder')
        properties_dict = self.as_dict()
        dicts_to_xml(item_element, properties_dict)
        return item_element

    def as_xml_item_element_from_inventory_object(self, inventory_object, mfr_short_name):
        if mfr_short_name == 'MART':
            mfr_short_name = 'MAR'
        elif mfr_short_name == 'IC':
            mfr_short_name = 'ING'
        self.customer_number = None
        self.manufacturer_code = mfr_short_name
        self.customer_internal_sku = inventory_object.sku
        self.part_number = inventory_object.sku.split('~')[1]
        self.quantity = '10'
        return self.as_xml_item_element()


class InventoryReply(object):

    def __init__(self):
        self.additional_charge1 = None
        self.additional_charge1_description = None
        self.additional_charge2 = None
        self.additional_charge2_description = None
        self.additional_charge3 = None
        self.additional_charge3_description = None
        self.customer_internal_sku = None
        self.estimated_date_available = None
        self.factory_back_ordered = None
        self.inquiry_sequence_number = None
        self.location_where_available = None
        self.manufacturer_code_inquired = None
        self.manufacturer_code_responded = None
        self.part_description = None
        self.part_number_inquired = None
        self.part_number_responded = None
        self.quantity_available = None
        # self.mn_quantity_available = None
        # self.wi_quantity_available = None
        self.quantity_break_list = None
        self.quantity_inquired = None
        self.reason_for_alternate_part = None
        self.retail_price = None
        self.status = None
        self.unit_price = None
        self.upc_code = None

    def as_dict(self):
        return{'AdditionalCharge1': self.additional_charge1,
               'AdditionalCharge1Description': self.additional_charge1_description,
               'AdditionalCharge2': self.additional_charge2,
               'AdditionalCharge2Description': self.additional_charge2_description,
               'AdditionalCharge3': self.additional_charge3,
               'AdditionalCharge3Description': self.additional_charge3_description,
               'CustomerInternalSKU': self.customer_internal_sku,
               'SKU': self.customer_internal_sku,
               'EstimatedDateAvailable': self.estimated_date_available,
               'FactoryBackordered': self.factory_back_ordered,
               'InquirySequence_number': self.inquiry_sequence_number,
               'LocationWhereAvailable': self.location_where_available,
               'ManufacturerCodeInquired': self.manufacturer_code_inquired,
               'ManufacturerCodeResponded': self.manufacturer_code_responded,
               'PartDescription': self.part_description,
               'PartNumberInquired': self.part_number_inquired,
               'PartNumberResponded': self.part_number_responded,
               'QuantityAvailable': self.quantity_available,
               # 'MNQuantityAvailable': self.mn_quantity_available,
               # 'WIQuantityAvailable': self.wi_quantity_available,
               'QuantityBreakList': self.quantity_break_list,
               'QuantityInquired': self.quantity_inquired,
               'ReasonForAlternatePart': self.reason_for_alternate_part,
               'RetailPrice': self.retail_price,
               'Status': self.status,
               'UnitPrice': self.unit_price,
               'UpcCode': self.upc_code}
               
    def from_part_element(self, part):
        self.additional_charge1 = part.find('AdditionalCharge1').text
        self.additional_charge1_description = part.find('AdditionalCharge1Description').text
        self.additional_charge2 = part.find('AdditionalCharge2').text
        self.additional_charge2_description = part.find('AdditionalCharge2Description').text
        self.additional_charge3 = part.find('AdditionalCharge3').text
        self.additional_charge3_description = part.find('AdditionalCharge3Description').text
        self.customer_internal_sku = part.find('CustomerInternalSKU').text
        self.estimated_date_available = part.find('EstimatedDateAvailable').text
        self.factory_back_ordered = part.find('FactoryBackordered').text
        self.inquiry_sequence_number = part.find('InquirySequenceNumber').text
        self.location_where_available = part.find('LocationWhereAvailable').text
        self.manufacturer_code_inquired = part.find('ManufacturerCodeInquired').text
        self.manufacturer_code_responded = part.find('ManufacturerCodeResponded').text
        self.part_description = part.find('PartDescription').text
        self.part_number_inquired = part.find('PartNumberInquired').text
        self.part_number_responded = part.find('PartNumberResponded').text
        self.quantity_available = part.find('QuantityAvailable').text
        # self.mn_quantity_available = part.find('MNQuantityAvailable').text
        # self.wi_quantity_available = part.find('WIQuantityAvailable').text
        self.quantity_break_list = part.find('QuantityBreakList').text
        self.quantity_inquired = part.find('QuantityInquired').text
        self.reason_for_alternate_part = part.find('ReasonForAlternatePart').text
        self.retail_price = part.find('RetailPrice').text
        self.status = part.find('Status').text
        self.unit_price = part.find('UnitPrice').text
        self.upc_code = part.find('UpcCode').text

    def as_xml_item_element(self):
        item_element = et.Element('Part')
        properties_dict = self.as_dict()
        dicts_to_xml(item_element, properties_dict)
        return item_element
