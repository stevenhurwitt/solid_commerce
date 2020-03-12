import pyodbc
from classes.SolidCommerce import API as SolidAPI
import csv
import time


class Database:

    def __init__(self):
        self.connection = pyodbc.connect("DSN=Ideal ODBC")
        self.cursor = self.connection.cursor()

    def write_tables_and_columns(self):
        database = self.cursor
        csv_string = ''
        table_names = [table.table_name for table in database.tables()]
        for table_name in table_names:
            csv_string += table_name + ',' + ','.join([column.column_name for column in database.columns(table=table_name)]) + '\n'
        save_filepath = 't:/McHenryPowerEquipment/data/tables_and_columns.csv'
        with open(save_filepath, 'w', newline='') as csv_file:
            csv_file.writelines(csv_string)
        # for row in cursor.tables():
        #     print(row.table_name)
        # for row in cursor.columns(table='PRODUCTLOCATION'):
        #     print(row.column_name)
        # print('--------------')
        # for row in cursor.columns(table='PRODUCT'):
        #     print(row.column_name)

    def print_table_names(self):
        for row in self.cursor.tables():
            print(row.table_name)

    def print_column_names(self, table_name):
        for row in self.cursor.columns(table=table_name):
            print(row.column_name)

    def get_oldest_sales_order_reference_and_range(self):
        orders = self.get_sales_orders()
        order_reference_numbers = [int(order['REFERENCE']) for order in orders if order['REFERENCE'] is not None and len(order['REFERENCE']) < 7]
        oldest_order_number = min(order_reference_numbers)
        newest_order_number = max(order_reference_numbers)
        return [str(oldest_order_number), str(newest_order_number - oldest_order_number)]

    def get_sales_orders(self):
        orders = self.table_as_dicts('SALESORDER')
        return orders

    def table_as_dicts(self, table_name):
        database = self.cursor
        columns = [column.column_name for column in database.columns(table=table_name)]
        rows = list(self.cursor.execute("SELECT * FROM " + table_name + " WHERE CUSTOMERID=1099").fetchall())
        data_frames = []
        i = 0
        for row in rows:
            row_dict = {}
            for cell in row:
                row_dict[columns[i]] = cell
                i += 1
            data_frames.append(row_dict)
            i = 0
        return data_frames

    def get_table_by_name_as_dict(self, table_name):
        database = self.cursor
        columns = [column.column_name for column in database.columns(table=table_name)]
        rows = list(self.cursor.execute("SELECT * FROM " + table_name).fetchall())
        data_frames = []
        i = 0
        for row in rows:
            row_dict = {}
            for cell in row:
                row_dict[columns[i]] = cell
                i += 1
            data_frames.append(row_dict)
            i = 0
        return data_frames

    def get_table_columns_by_names_as_dict(self, table_name, column_names):
        columns_string = ', '.join(column_names)
        database = self.cursor
        columns = [column.column_name for column in database.columns(table=table_name)]
        rows = list(self.cursor.execute("SELECT " + columns_string + " FROM " + table_name).fetchall())
        data_frames = []
        i = 0
        for row in rows:
            row_dict = {}
            for cell in row:
                row_dict[columns[i]] = cell
                i += 1
            data_frames.append(row_dict)
            i = 0
        return data_frames

    def save_table_as_csv(self, table_name):
        table_as_dicts = self.get_table_by_name_as_dict(table_name)
        filepath = 'U:/McHenry Power/Data/2019/' + table_name + time.strftime('_%m%d%Y%I%M.csv')
        self.write_dicts_to_csv(table_as_dicts, filepath)

    def write_dicts_to_csv(self, list_of_dicts, save_file_path):
        keys = list_of_dicts[0].keys()
        with open(save_file_path, 'a', newline='', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(list_of_dicts)

    def get_table_by_sql_as_dict(self, sql_string):
        table = self.cursor.execute(sql_string)
        columns = [column[0] for column in table.description]
        rows = list(table.fetchall())
        data_frames = []
        i = 0
        for row in rows:
            row_dict = {}
            for cell in row:
                row_dict[columns[i]] = cell
                i += 1
            data_frames.append(row_dict)
            i = 0
        return data_frames

    def get_inventory_for_solid(self):
        ideal_products_dict = {}
        ideal_products = self.get_table_columns_by_names_as_dict('PRODUCT', ['MFRID', 'PARTNUMBER', 'CURRENTCOST'])
        for ideal_product in ideal_products:
            try:
                ideal_products_dict[ideal_product['MFRID'] + '~' + ideal_product['PARTNUMBER']] = (
                    ideal_product['DESCRIPTION']
                )
            except KeyError:
                print()
        ideal_inventory = self.get_table_by_name_as_dict('PRODUCTLOCATION')
        ideal_stocking = self.get_table_by_name_as_dict('PRODUCTSTOCK')
        inventory_dict = {}
        solid = SolidAPI()
        products = [
            product_dict for product_dict in solid.get_products_from_file()
            if '~DL' not in product_dict['SKU'] and '~MP' not in product_dict['SKU']
        ]
        for item in ideal_inventory:
            composite_key = item['COMPOSITEKEY'].split('$')
            inventory_dict[composite_key[0] + '~' + composite_key[1]] = {'Quantity': item['ONHANDAVAILABLEQUANTITY']}
        for stock in ideal_stocking:
            try:
                sku = stock['MFRID'] + '~' + stock['PARTNUMBER']
                inventory_dict[sku]['StorageLocation'] = stock['BINLOCATION']
            except KeyError:
                pass
        for product in products:
            if product['SKU'].split('~')[0] == 'STE':
                product_sku = product['SKU'].replace('-', '')
            else:
                product_sku = product['SKU']
            try:
                product['Cost'] = ideal_products_dict[product_sku]
            except KeyError:
                product['Cost'] = '0'
            if product_sku in inventory_dict:
                product['WH_McHenry Power'] = str(int(inventory_dict[product_sku]['Quantity']))
                try:
                    product['StorageLocation'] = inventory_dict[product_sku]['StorageLocation']
                except KeyError:
                    pass
            elif product_sku == 'MAG~LOT#1':
                try:
                    mag1000_qty = inventory_dict['MAG~MAG1000']['Quantity']
                    mag9000_qty = inventory_dict['MAG~MAG9000']['Quantity']
                    lowest_qty = self.get_lowest_of_list([int(mag1000_qty), int(mag9000_qty)])
                    product['WH_McHenry Power'] = lowest_qty
                    product['StorageLocation'] = ''
                except KeyError:
                    pass
            elif product_sku == 'MAG~LOT#2':
                try:
                    mag1000_qty = inventory_dict['MAG~MAG1000']['Quantity']
                    mag8000_qty = inventory_dict['MAG~MAG8000']['Quantity']
                    lowest_qty = self.get_lowest_of_list([int(mag1000_qty), int(mag8000_qty)])
                    product['WH_McHenry Power'] = lowest_qty
                    product['StorageLocation'] = ''
                except KeyError:
                    pass
            elif product_sku == 'MAG~LOT#3':
                try:
                    mag1000_qty = inventory_dict['MAG~MAG1000']['Quantity']
                    mag9000_qty = inventory_dict['MAG~MAG9000']['Quantity']
                    mag10400_qty = inventory_dict['MAG~MAG10400']['Quantity']
                    lowest_qty = self.get_lowest_of_list([int(mag1000_qty), int(mag9000_qty), int(mag10400_qty)])
                    product['WH_McHenry Power'] = lowest_qty
                    product['StorageLocation'] = ''
                except KeyError:
                    pass
            elif product_sku == 'MAG~LOT#4':
                try:
                    mag1000_qty = inventory_dict['MAG~MAG1000']['Quantity']
                    mag8000_qty = inventory_dict['MAG~MAG8000']['Quantity']
                    mag10400_qty = inventory_dict['MAG~MAG10400']['Quantity']
                    lowest_qty = self.get_lowest_of_list([int(mag1000_qty), int(mag8000_qty, int(mag10400_qty))])
                    product['WH_McHenry Power'] = lowest_qty
                    product['StorageLocation'] = ''
                except KeyError:
                    pass
            else:
                # print(product_sku + ' Not in stock')
                product['WH_McHenry Power'] = '0'
        return products

    @staticmethod
    def get_lowest_of_list(numbers):
        lowest = None
        for number in numbers:
            if lowest is None:
                lowest = number
            else:
                if number < lowest:
                    lowest = number
        return lowest

    def inventory_from_database_to_solid(self):
        products = self.get_inventory_for_solid()
        solid = SolidAPI()
        solid.upload_list_items(products)

    def write_all_inventory_csv(self):
        ideal_inventory = self.get_table_by_name_as_dict('PRODUCTLOCATION')
        keys = ideal_inventory[0].keys()
        save_file_path = 'T:/ebay/All/Data/All_Inventory_Ideal.csv'
        with open(save_file_path, 'w', newline='', encoding='utf-8', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(ideal_inventory)

    def write_all_ap_trans(self):
        ideal_inventory = self.get_table_by_name_as_dict('APTRANS')
        keys = ideal_inventory[0].keys()
        save_file_path = 'T:/ebay/All/Data/AP_Trans.csv'
        with open(save_file_path, 'w', newline='', encoding='utf-8', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(ideal_inventory)
