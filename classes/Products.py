import csv


class Products(object):

    def __init__(self, file_path):
        self.file_path_product_ids = file_path

    def products_as_list_of_dicts(self):
        with open(self.file_path_product_ids, encoding="utf-8", errors="ignore") as file:
            products = csv.DictReader(file)
            for product in products:
                yield(product)
