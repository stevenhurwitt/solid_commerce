import Distributor
import xlrd


class GE(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(GE, self).__init__('GE', "Golden Eagle")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name

    def inventory_from_default(self, products):
        inventory = self.inventory_from_file(products)
        return inventory

    def inventory_from_file(self, products):
        vendor_products = {}
        distributor_inventory_filepath = 'T:/ebay/Golden Eagle/Inventory/Mchenry.xlsx'
        workbook = xlrd.open_workbook(distributor_inventory_filepath, on_demand=True)
        worksheet = workbook.sheet_by_index(0)
        first_row = []  # The row where we stock the name of the column
        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        data = []
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)
            data.append(elm)
        try:
            for row in data:
                len_pid = len(row['Item Code'])
                item_code = row['Item Code']
                product_id = item_code[5:len_pid]
                sku = item_code[:3] + '~' + product_id
                vendor_product = {
                    'Inventory': {'WH_GE-IL': str(int(row['Qty on Hand'])),
                                  'WH_McHenry Inbound': str(int(row['Qty on Hand']))},
                    'Cost': '0.00',
                    'MSRP': row['Retail']
                }
                vendor_products[sku] = vendor_product
        except:
            pass
        for product in products:
            try:
                product.warehouse_with_inventory_dicts = vendor_products[product.sku]['Inventory']
                product.cost = vendor_products[product.sku]['Cost']
                product.msrp = vendor_products[product.sku]['MSRP']
            except KeyError:
                self.log_distributor_event(
                    self.get_log_dict(
                        product.sku,
                        'Error - No Inventory',
                        'Catalogue Product not available at distributor'
                    )
                )
                product.warehouse_with_inventory_dicts['WH_GE-IL'] = None
        inventory = [product for product in products if product.warehouse_with_inventory_dicts['WH_GE-IL']]
        return inventory
