import time
import csv
import requests
from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection as Finding
from ebaysdk.trading import Connection as Trading
from ebaysdk.shopping import Connection as Shopping


class API:

    def __init__(self):
        self.app_id = 'JoelOhma-MPE-PRD-a392af54d-2faf7f08'

    def get_orders(self):
        # page = 10
        # orders = []
        # while True:
        #     trading = Trading(appid=self.app_id, config_file='ebay.yaml')
        #     response = trading.execute('GetOrders', {
        #         "NumberOfDays": "7",
        #         "DetailLevel": "ReturnAll",
        #         "OrderRole": "Seller",
        #         "OrderStatus": "Completed",
        #         "Pagination": {
        #             "PageNumber": page,
        #             "EntriesPerPage": "100"
        #         }
        #     })
        #     response_dict = response.dict()
        #     pages = response_dict['PaginationResult']['TotalNumberOfPages']
        #     if response_dict['OrderArray'] is not None:
        #         pending_orders = [
        #             order for order in response_dict['OrderArray']['Order'] if order['OrderStatus'] != 'Completed'
        #         ]
        #         orders += pending_orders
        #     del response_dict['OrderArray']
        #     print(response_dict)
        #     if str(page) == pages:
        #         break
        #     page += 1
        # for order in orders:
        #     print(order)
        url = 'https://api.ebay.com/sell/fulfillment/v1/order?'
        header = {
            'Authorization': self.app_id,
            # 'X-EBAY-C-ENDUSERCTX': 'AgAAAA**AQAAAA**aAAAAA**jhY7XQ**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wJk4qlCJCGpgSdj6x9nY+seQ**7McFAA**AAMAAA**PIXtp0dhJE8pP71BVEUJrOoDcS58nf1lWCP26fpcrgMdOASpAEdnyixixYCEZQtuwM2PZnSUeuUJedJQbOKu8At6gXXSQo5+0jdMMiUZwzENG+huVzQt7Zsi5LVtl42SJDWzRnZXmCnRnT6OcUEv4ebqDxazTSmUuMRzxVxWaxFnb+7cE9pZMovTvNFmDUIlOi0NTIYbOUfPTKNqE4kPcDuHoHeYEwDFoISZEiFapAK0x0B+rBVesSCbHRsVwE66L3FypDUgvsJpga4KyWN2ES3hDBW6ppeBgAZvpXfRYvIMnG6fi5CbTPC+z6qUSkrafk2fYiCDy2w7ZV2xjCLBi92TSC4d/I6sZUAxIQ0/AglLEkeP/4fhrJE1FX9ZIzdb3QeDJ05qkYF8+xVUKXaZi79t41KxE03mqQWByfkMbSEl9wqvCzJUSjeteTHEmGl+y9ygCWTiX6vaeW9qa4C3COFtZvHr1SQEzQo5iEVrsHYyiXpGnmbHp7Kz3/6snWh9u1QSe111gdHiexiWjz+xKUsVrGLwvqtEpMKJ3UeZ7Jmiq4GFEQoDpIN8FvGiW7NKrHHMT7gFSrm1EF8BuNRaTDo/gOuDC0DIANfZxXR+Rzb53NB5pElCo+EDdBeRqH8aE/5Bd+4AWg5f64tor9AG+0+x1TCahivmdb46nDV397f1aKe+1Mnw9ogBYXlqKP5qFnKXCkh4rcuGLH4qT1BsCzQkZTeVjcM/ixxzjeIn1XxxPo5TNk7UMPtrtjFoNpTn'
        }
        paramaters = {
            'filter': 'orderfulfillmentstatus:{NOT_STARTED|IN_PROGRESS}'
        }
        response = requests.get(url, headers=header, params=paramaters)
        print(response)
        print(response.text)

    def get_feedback(self):
        trading = Trading(appid=self.app_id, config_file='ebay.yaml')
        response = trading.execute('GetFeedback', {
            'UserID': 'powerequipmentdeals',
            'CommentType': 'Positive',
            'Pagination': {
                'EntriesPerPage': '200',
                'PageNumber': '1'
            },
            'FeedbackType': 'FeedbackReceivedAsSeller',
            'DetailLevel': 'ReturnAll'
        })
        feedback = response.dict()['FeedbackDetailArray']['FeedbackDetail']
        # print(feedback)
        # for review in feedback:
        #     print(review)
        file_path = 'U:/Marketplaces/eBay/Data/Reviews/Last_200_Positive_Reviews' + time.strftime('%m%d%Y') + '.csv'
        with open(file_path, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=feedback[0].keys())
            writer.writeheader()
            for data in feedback:
                writer.writerow(data)

    def search_item(self, search_string, shipping_to_zip):
        try:
            finding_api = Finding()
            finding_response = finding_api.execute('findItemsAdvanced', {
                'keywords': search_string,
                'buyerPostalCode': shipping_to_zip,
                'sortOrder': 'PricePlusShippingLowest',
                'itemFilter': [
                    {'name': 'Condition',
                     'value': 'New'}
                ],
            })
            assert (finding_response.reply.ack == 'Success')
            try:
                item = finding_response.reply.searchResult.item[0]
            except AttributeError:
                return None
            single_item = self.get_single_item_with_shipping(item.itemId, shipping_to_zip)
            return single_item
        except ConnectionError as error:
            print(error)
            print(error.response.dict)

    def get_single_item_with_shipping(self, item_id, ship_to_zip):
        single_item = self.get_single_item(item_id)
        shipping_costs = self.get_shipping_cost(item_id, ship_to_zip)
        single_item['Item']['Shipping'] = shipping_costs
        return single_item

    def get_single_item(self, item_id):
        shopping_api = Shopping(appid=self.app_id, config_file=None)
        shopping_response = shopping_api.execute("GetSingleItem", {
            "ItemID": item_id,
            'IncludeSelector': ['Details,ItemSpecifics']
        })
        return shopping_response.dict()

    def get_shipping_cost(self, item_id, zip_code):
        try:
            api = Shopping(appid=self.app_id, config_file=None)
            response = api.execute('GetShippingCosts', {
                'DestinationCountryCode': 'US',
                'DestinationPostalCode': zip_code,
                'IncludeDetails': 'true',
                'ItemID': item_id,
                'QuantitySold': '1'
            })
            return response.dict()
        except ConnectionError as e:
            print(e)
            print(e.response.dict())


class ProductPage(object):

    def __init__(self):
        self.ebay_item_number = None
        self.pictures = None
        self.price = None
        self.shipping = None
        self.seller = None
        self.item_specifics = None
        self.upc = None
        self.mpn = None
        self.brand = None
        self.condition = None

    def as_dict(self):
        return{
            'ItemNumber': self.ebay_item_number,
            'Pictures': self.pictures,
            'Price': self.price,
            'Shipping': self.shipping,
            'Seller': self.seller,
            'ItemSpecifics': self.item_specifics,
            'UPC': self.upc,
            'MPN': self.mpn,
            'Brand': self.brand,
            'Condition': self.condition
        }

    def set_properties_from_soup(self, soup):
        try:
            self.price = soup.find("span", {"id": "prcIsum"}).text.strip()
        except AttributeError:
            self.price = 'None'
        try:
            self.shipping = soup.find("span", {"id": "fshippingCost"}).text.strip()
        except AttributeError:
            self.shipping = 'Calculated'
        self.seller = soup.find("a", {"id": "mbgLink"}).text.strip()
        self.ebay_item_number = soup.find("div", {"id": "descItemNumber"}).text.strip()
        item_specifics_element = soup.find("div", {"id": "viTabs_0_is"})
        cells = item_specifics_element.select('td')
        labels = [label.text.strip().strip(':').lower() for label in cells[0::2]]
        info = [info_text.text.strip().replace('\n', '').replace('\t', '') for info_text in cells[1::2]]
        item_specifics_dict = dict(zip(labels, info))
        self.item_specifics = item_specifics_dict
        try:
            self.upc = item_specifics_dict['upc']
        except KeyError:
            self.upc = 'None'
        try:
            self.mpn = item_specifics_dict['mpn']
        except KeyError:
            self.mpn = 'None'
        try:
            self.brand = item_specifics_dict['brand']
        except KeyError:
            self.brand = 'None'
        try:
            self.condition = item_specifics_dict['condition'].split(' ')[0].strip(':')
        except KeyError:
            self.condition = 'None'
