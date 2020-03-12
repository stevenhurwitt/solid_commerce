import requests
from lxml import html
import tkinter as tk
from tkinter import filedialog
import csv


class ProductPage(object):

    def __init__(self, brand_long_name, part_number):
        self.base_url = 'https://www.partstree.com/parts'
        self.brand_long_name = brand_long_name
        self.product_line = None
        self.part_number = part_number
        self.full_url = self.base_url + '/' + self.brand_long_name + '/parts/' + self.part_number.lower() + '/'
        self.partstree_part_number = None
        self.replaces = None
        self.alternative = None
        self.description = None
        self.comments = None
        self.details = None
        self.price = None
        self.parts = None
        self.pictures = None
        self.where_used = None

    def parse_page(self):
        page = requests.get(self.full_url)
        tree = html.fromstring(page.content)
        try:
            self.product_line = tree.xpath('.//p[@class="partId"]/span[@class="line"]/text()')[0]
        except IndexError:
            pass
        try:
            self.partstree_part_number = tree.xpath('.//p[@class="partId"]/span[@class="number"]/text()')[0]
        except IndexError:
            pass
        try:
            self.replaces = tree.xpath('.//p[@class="partId"]/span[@class="replaces"]/text()')
        except IndexError:
            pass
        try:
            self.alternative = tree.xpath('.//p[@class="alternative"]/text()')
        except IndexError:
            pass
        try:
            self.description = tree.xpath('.//p[@class="description"]/text()')[0]
        except IndexError:
            pass
        try:
            self.comments = tree.xpath('.//p[@class="comments"]/text()')
        except IndexError:
            pass
        try:
            self.details = tree.xpath('.//p[@class="details"]/text()')
        except IndexError:
            pass
        try:
            self.price = tree.xpath('.//p[@class="pricing"]/span[@class="your"]/text()')[0]
        except IndexError:
            pass
        try:
            self.parts = tree.xpath('.//table[@class="parts"]/text()')
        except IndexError:
            pass
        try:
            self.where_used = tree.xpath('.//div[@class="whereUsed"]/ul/li/a[1]/text()')
        except IndexError:
            pass
        try:
            self.pictures = tree.xpath('.//div[@class="carousel"]/a/img/@src')
        except IndexError:
            pass

    def as_dict(self):
        return{'ProductLine': self.product_line,
               'URL': self.full_url,
               'PartNumber': self.part_number,
               'PartsTreePartNumber': self.partstree_part_number,
               'Replaces': self.replaces,
               'AlternativePartNumber': self.alternative,
               'Description': self.description,
               'Comments': self.comments,
               'Details': self.details,
               'Price': self.price,
               'Parts': self.parts,
               'Pictures': self.pictures,
               'WhereUsed': self.where_used}


class ScrapePartsTree:

    @staticmethod
    def scrape_multiple_from_file():
        root = tk.Tk()
        root.withdraw()
        product_ids_filepath = filedialog.askopenfilename()
        with open(product_ids_filepath, encoding="utf8") as file:
            brand_long_name = input("what is the long brand name from the Parts Tree URL? ")
            reader = csv.DictReader(file)
            field_names = reader.fieldnames
            field_names_as_menu_string = ''
            i = 1
            for field_name in field_names:
                field_names_as_menu_string = field_names_as_menu_string + '\n[' + str(i) + '] ' + field_name
                i += 1
            field_names_as_menu_string = field_names_as_menu_string + '\nSelection: '
            column_selection = field_names[int(input('Which Column Contains The Product Ids? ' +
                                                     field_names_as_menu_string))-1]
            for row in reader:
                parts_tree_product = ProductPage(brand_long_name, row[column_selection])
                parts_tree_product.parse_page()
                yield parts_tree_product


parts_tree = ScrapePartsTree()
parts_tree.scrape_multiple_from_file()
