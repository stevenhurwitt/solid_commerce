from classes.eBay import API as EBayAPI
from abc import ABC
from abc import abstractmethod
import time
import csv
import requests
from bs4 import BeautifulSoup


class Competitor(ABC):

    def __init__(self, store_name):
        self.store_name = store_name
        self.base_store_url = 'http://www.ebaystores.com'

    @abstractmethod
    def get_categories(self):
        raise NotImplemented

    @abstractmethod
    def get_listing_ids_from_category(self, category_link):
        raise NotImplemented

    @staticmethod
    def get_item_with_shipping_to_mpe(item_id):
        ebay_api = EBayAPI()
        return ebay_api.get_single_item_with_shipping(item_id, '60050')

    def get_all_products(self):
        category_links = self.get_categories()
        item_ids_by_category = [self.get_listing_ids_from_category(category_link) for category_link in category_links]
        print('Category Links Collected...')
        item_ids = []
        for category_item_ids in item_ids_by_category:
            item_ids = item_ids+category_item_ids
        print('Item IDs Collected...')
        item_dicts = []
        for item_id in item_ids:
            try:
                item_dict = self.get_item_with_shipping_to_mpe(item_id)
                if item_dict is not None:
                    item_dicts.append(item_dict)
            except:
                pass
        save_to_filepath = (
            'U:/Marketplaces/eBay/Data/CompetitorScrapes/' + self.store_name +
            '/StoreScrape.' + time.strftime('%m%d%Y') + '.csv'
        )
        self.save_dicts_to_csv(item_dicts, save_to_filepath)


    @staticmethod
    def save_dicts_to_csv(list_of_dicts, save_file_path):
        keys = list_of_dicts[0].keys()
        with open(save_file_path, 'a', newline='', encoding='utf-8', errors='ignore') as csv_file:
            dict_writer = csv.DictWriter(csv_file, keys)
            dict_writer.writeheader()
            data = [{k: v for k, v in record.items() if k in keys} for record in list_of_dicts]
            dict_writer.writerows(data)


class PoweredByMoyer(Competitor):

    def __init__(self):
        super(PoweredByMoyer, self).__init__('poweredbymoyer')

    def get_categories(self):
        store_url = self.base_store_url + '/' + self.store_name
        response = requests.get(store_url)
        soup = BeautifulSoup(response.text, features='lxml')
        category_links = [self.base_store_url + link['href'] for link in soup.select('div.boxlinks a')]
        return category_links

    def get_listing_ids_from_category(self, category_link):
        response = requests.get(category_link)
        soup = BeautifulSoup(response.text, features='lxml')
        item_ids = [item['id'].strip('src') for item in soup.select('td.details a')]
        next_page_link = self.get_next_page_link(soup)
        if next_page_link is not None:
            return item_ids + self.get_listing_ids_from_category(next_page_link)
        else:
            return item_ids

    def get_next_page_link(self, soup):
        try:
            return self.base_store_url + soup.select('td.next a')[0]['href']
        except KeyError:
            return None
        except IndexError:
            return None


test_scrape = PoweredByMoyer()
test_result = test_scrape.get_all_products()
