class Inventory(object):

    def __init__(self):
        self.ebay_product_id = None
        self.sixbit_item_id = None
        self.manufacturer_product_id = None
        self.distributor_product_id = None
        self.sku = None
        self.comparable_sku = None
        self.distributor_short_name = None
        self.total_quantity = None
        self.cost = None
        self.weight = '0.0'
        self.length = None
        self.width = None
        self.depth = None
        self.unit_type = None
        self.list_price = None
        self.minimum_order_qty = None
        self.default_warehouse_quantity = None
        self.selective_quantity = None
        self.current_quantity = None
        self.upc = None
        self.fulfillment_source = None
        self.warehouse_with_inventory_dicts = {}

    def set_only_ebay_id_and_sku(self, product_id, sku):
        self.ebay_product_id = product_id
        self.sku = sku
        self.comparable_sku = sku

    def as_dict(self):
        return{'ProductID': self.ebay_product_id,
               'ItemID': self.sixbit_item_id,
               'Cost': self.cost,
               'TotalAvailability': self.total_quantity,
               'Quantity': self.selective_quantity}

    def as_dict_for_solid(self):
        as_dict = self.warehouse_with_inventory_dicts
        as_dict['SKU'] = self.sku
        as_dict['Cost'] = self.cost
        return as_dict

    def as_dict_for_sixbit(self):
        return {'ProductID': self.ebay_product_id,
                'SKU': self.sku,
                'ItemID': self.sixbit_item_id,
                'MPN': self.manufacturer_product_id,
                'CF_DistributorProductID': self.distributor_product_id,
                'Cost': self.cost,
                'Quantity': self.selective_quantity,
                'FulfillmentSource': self.fulfillment_source}

    def as_dict_for_listing_generation(self):
        return{'ProductID': self.ebay_product_id,
               'SKU': self.sku,
               'BaseSKU': self.comparable_sku,
               'DistributorAbbreviation': self.distributor_short_name,
               'Cost': self.cost,
               'Quantity': self.total_quantity,
               'PriceFileWeight': self.weight,
               'DimensionLength': self.length,
               'DimensionWidth': self.width,
               'DimensionDepth': self.depth,
               'UnitType': self.unit_type,
               'MSRP': self.list_price,
               'UPC': self.upc,
               'MinimumOrderQuantity': self.minimum_order_qty}

    def set_properties_from_productids_csv_dict(self, product_ids):
        self.ebay_product_id = product_ids['ProductID']
        self.sixbit_item_id = product_ids['ItemID']
        self.sku = product_ids['SKU']
        self.current_quantity = product_ids['Quantity']

    def from_solid_csv_dict(self, solid_dict):
        self.sku = solid_dict['SKU']
        self.manufacturer_product_id = solid_dict['Model Number']
