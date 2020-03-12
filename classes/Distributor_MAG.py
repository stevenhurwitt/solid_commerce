from classes import Distributor
from multiprocessing.pool import ThreadPool
import selenium.webdriver as webdriver
from selenium.common.exceptions import NoSuchElementException
from threading import Thread
import queue
import requests
from bs4 import BeautifulSoup


class MAG(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(MAG, self).__init__('MAG', "Magna-matic")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.updated_products = []

    def inventory_from_default(self, products):
        updated_product_objects = self.inventory_from_web(products)
        return updated_product_objects

    def inventory_from_api(self, product_objects):
        with ThreadPool(1) as inventory_pool:
            inventory_pool.map(self.inventory, product_objects)
        return self.updated_products

    def inventory(self, product_object):
        inventory_object = MagProductPage()
        inventory_object.set_from_api(product_object.sku)
        product_object.warehouse_with_inventory_dicts = {'WH_MAG-WI': inventory_object.qty}
        self.updated_products.append(product_object)

    def inventory_from_web(self, products):
        browser = webdriver.Firefox()
        for product in products:
            self.browser_load_product(browser, product)
            quantity = self.parse_inventory(browser)
            product.total_quantity = quantity
            product.default_warehouse_quantity = quantity
            product.selective_quantity = quantity
            product.warehouse_with_inventory_dicts = {'WH_MAG-WI': quantity}
        return products

    def parse_inventory(self, browser):
        availability_xpath = r'//*[@id="v65-product-parent"]/tbody/tr[2]/td[2]/table/tbody/tr/td/table/tbody/' \
                             r'tr[2]/td[2]/table/tbody/tr[1]/td[1]/div/meta[2]'
        backorder = ''
        try:
            backorder = browser.find_element_by_xpath(
                r'//*[@id="v65-product-parent"]/tbody/tr[2]/td[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/'
                r'tbody/tr[1]/td[1]/div').text.split('\n')[2]
        except:
            pass
        try:
            availability = browser.find_element_by_xpath(availability_xpath).get_attribute("content")
            if backorder.strip(' ') == 'Availability:: Back Order':
                return '0'
            elif availability == 'InStock':
                return '10'
            else:
                return '0'
        except NoSuchElementException:
            return 'NoSuchElementException'

    def browser_load_product(self, browser, product):
        browser.get(
            'http://www.magna-matic-direct.com/MAG-9000-Lawn-Mower-Blade-Sharpener-p/' +
            product.sku.split('~')[1] + '.htm')


class MagProductPage:

    def __init__(self):
        self.qty = None

    def set_from_api(self, sku):
        edited_sku = '-'.join(sku.split('~'))
        url = 'https://www.magna-matic-direct.com/-p/' + edited_sku + '.htm'
        session = requests.session()
        session.headers.update({
            'authority': 'www.magna-matic-direct.com',
            'method': 'GET',
            'path': '/-p/mag-9000.htm',
            'scheme': 'https'
        })
        response = session.get(url)
        print(response.content)
        input()


mag = MAG('MAG', 'Magna-matic')
mag.inventory_from_default_to_solid()
