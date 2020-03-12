from classes import Database_Ideal
import csv


class TableViewer:

    def __init__(self):
        self.database = Database_Ideal.Database()

    def print_table_names(self):
        self.database.print_table_names()

    def print_column_names(self, table_name):
        self.database.print_column_names(table_name)

    def print_table(self):
        table_name = input('Enter Table Name: ')
        table = self.database.get_table_by_name_as_dict(table_name)
        print([row for row in table][0])

    def print_table_where(self):
        table_name = input('Enter Table Name: ')
        where_string = input('Where: ')
        table = self.database.get_table_by_name_where_as_dict(table_name, where_string)
        print([row for row in table][0])

    def save_table_where(self):
        table_name = input('Enter Table Name: ')
        where_string = input('Where: ')
        file_name = input('Output File Name: ')
        table = self.database.get_table_by_name_where_as_dict(table_name, where_string)
        print('Writing File....')
        keys = table[0].keys()
        save_filepath = 'T:/ebay/Ideal/Reports/' + file_name + '.csv'
        with open(save_filepath, 'w', newline='') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(table)

    def save_table(self):
        table_name = input('Enter Table Name: ')
        file_name = input('Output File Name: ')
        table = self.database.get_table_by_name_as_dict(table_name)
        print('Writing File....')
        keys = table[0].keys()
        save_filepath = 'T:/ebay/Ideal/Reports/' + file_name + '.csv'
        with open(save_filepath, 'w', newline='') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(table)

    def save_table_custom_sql(self):
        sql_string = input('Enter SQL String: ')
        file_name = input('Output File Name: ')
        table = self.database.get_table_by_sql_as_dict(sql_string)
        print('Writing File....')
        keys = table[0].keys()
        save_table_filepath = 'T:/ebay/Ideal/Reports/' + file_name + '.csv'
        with open(save_table_filepath, 'w', newline='') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(table)


table_viewer = TableViewer()
table_viewer.save_table_custom_sql()
