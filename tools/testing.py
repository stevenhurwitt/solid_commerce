'''import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
page = requests.get('https://www.jackssmallengines.com/jacks-parts-lookup/part/briggs-stratton/491588s')
soup = BeautifulSoup(page.content, 'html.parser')
Productpage = soup.find(class_='content-wrapper')
Item_image = Productpage.find('img', {'src': re.compile('.jpg')})
Item_name = Productpage.find(itemprop='name').get_text()
print(Item_image['src'] + '\n')'''

import csv
with open('JacksProductOne.txt', 'r') as in_file:
    stripped = (line.strip() for line in in_file)
    lines = (line.split(",") for line in stripped if line)
    with open('sample.csv', 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(('link': Item_src, 'Name': ItemName, 'Partnumber': Item_part_number, 'Price': ItemPrice, 'Description': Item_Desc))
        writer.writerows(lines)
