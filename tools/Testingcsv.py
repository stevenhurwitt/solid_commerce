
import requests
from bs4 import BeautifulSoup
import pandas as pd

import re
page = requests.get('https://www.jackssmallengines.com/jacks-parts-lookup/part/briggs-stratton/491588s')
soup = BeautifulSoup(page.content, 'html.parser')
Productpage = soup.find(class_='content-wrapper')
Item_image = Productpage.find('img', {'src': re.compile('.jpg')})
Item_name = Productpage.find(itemprop='name').get_text()
Item_part_number = Productpage.find(class_='itemPartNum').get_text()
Item_Price = Productpage.find(class_='item-price').get_text()
Item_src = Item_image['src'] + '\n'

ItemName = (Item_name.lstrip())
ItemPrice = (Item_Price.lstrip())
Products = {'Name': ItemName, 'PartNumber': Item_part_number, 'Price': ItemPrice}
df = pd.DataFrame(Products)
print(df)
df.to_csv('sample.csv', index=False, header=False)




























