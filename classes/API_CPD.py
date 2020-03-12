from lxml import etree as element_tree
from tools import Dictionary_To_ETree
from xml.etree import ElementTree
item_element = element_tree.Element('inventory_request')
import requests


class API(object):

    def __init__(self):
        self.dealer_number = ''
        self.order_endpoint = 'http://2cpdonline.com/BMSTEST/order.asp'

    def place_dropship_order(self):
        order = OrderRequest()
        order.customer_number = '40855'
        order.order_date = '12/19/2009 12:45:16 PM'
        order.requested_ship_date = '12/19/2009 12:45:16 PM'
        order.ship_to_name = 'Joel Ohman'
        order.ship_to_phone_number = '262-422-8595'
        order.ship_to_address1 = '333 my house'
        order.ship_to_city = 'Sussex'
        order.ship_to_state_code = 'WI'
        order.ship_to_postal_code = '53089'
        part = OrderPart()
        part.manufacturer_code = 'MTD'
        part.quantity = '1'
        part.part_number = '9540280a'
        part.client_internal_sku = 'MTD~954-0280A'
        order.parts.append(part)
        data = ElementTree.tostring(order.as_element()).decode('utf8')
        response = requests.post(self.order_endpoint, data=data)
        print(response.content)


class InventoryInquiry(object):

    def __init__(self):
        self.endpoint = 'www.2cpdonline.com/BMSTEST/inquiry.asp '


class InventoryResponse(object):

    def __init__(self):
        self.place_holder = None


class OrderRequest(object):

    def __init__(self):
        self.record_type = None
        self.customer_number = None
        self.supplier_id = None
        self.purchase_order_number = None
        self.order_code = None
        self.order_date = None
        self.requested_ship_date = None
        self.shipping_method = None
        self.special_order_type = None
        self.client_order_reference_data = None
        self.override_salesperson_code_for_ticket = None
        self.client_vendor_number = None
        self.client_store_number = None
        self.client_department_number = None
        self.ship_to_name = None
        self.ship_to_phone_number = None
        self.ship_to_address1 = None
        self.ship_to_address2 = None
        self.ship_to_city = None
        self.ship_to_state_code = None
        self.ship_to_postal_code = None
        self.parts = []

    def as_dict(self):
        return{
            'RecordType': self.record_type,
            'CustomerNumber': self.customer_number,
            'SupplierID': self.supplier_id,
            'PONumber': self.purchase_order_number,
            'OrderCode': self.order_code,
            'OrderDate': self.order_date,
            'RequestedShipDate': self.requested_ship_date,
            'ShippingMethod': self.shipping_method,
            'SpecialOrderType': self.special_order_type,
            'ClientOrderReferenceData': self.client_order_reference_data,
            'OverrideSalespersonCodeForTicket': self.override_salesperson_code_for_ticket,
            'ClientVendorNumber': self.client_vendor_number,
            'ClientStoreNumber': self.client_store_number,
            'ClientDeptNumber': self.client_department_number,
            'ShipToName': self.ship_to_name,
            'ShipToPhoneNo': self.ship_to_phone_number,
            'ShipToAddress1': self.ship_to_address1,
            'ShipToAddress2': self.ship_to_address2,
            'ShipToCity': self.ship_to_city,
            'ShipToStateCode': self.ship_to_state_code,
            'ShipToPostalCode': self.ship_to_postal_code,
        }

    def as_element(self):
        order_element = element_tree.Element('order_request')
        Dictionary_To_ETree.dicts_to_xml(order_element, self.as_dict())
        for part in self.parts:
            order_element.append(part.as_element())
        return order_element


class OrderResponse(object):

    def __init__(self):
        self.place_holder = None


class OrderPart(object):

    def __init__(self):
        self.manufacturer_code = None
        self.part_number = None
        self.quantity = None
        self.unit_price_pre_discount = None
        self.discount_percentage = None
        self.client_sku_prefix = None
        self.client_internal_sku = None
        self.client_item_reference_data = None
        self.client_override_price_code = None
        self.client_purchase_order_line_number = None
        self.upc_code = None
        self.client_unit_of_measure = None

    def as_dict(self):
        return{
            'ManufacturerCode': self.manufacturer_code,
            'PartNumber': self.part_number,
            'Quantity': self.quantity,
            'UnitPricePreDisc': self.unit_price_pre_discount,
            'DiscountPercentage': self.discount_percentage,
            'ClientSKUPrefix': self.client_sku_prefix,
            'ClientInternalSKU': self.client_internal_sku,
            'ClientItemReferenceData': self.client_item_reference_data,
            'ClientOverridePriceCode': self.client_override_price_code,
            'ClientPOLineNumber': self.client_purchase_order_line_number,
            'UPCCode': self.upc_code,
            'ClientUOM': self.client_unit_of_measure,
        }

    def as_element(self):
        order_part_element = element_tree.Element('Part')
        Dictionary_To_ETree.dicts_to_xml(order_part_element, self.as_dict())
        return order_part_element


api = API()
api.place_dropship_order()
