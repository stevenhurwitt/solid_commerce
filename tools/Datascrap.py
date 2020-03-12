import csv
'''with open('employee_file.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    employee_writer.writerow(['John Smith', 'Accounting', 'November'])
  employee_writer.writerow(['Erica Meyers', 'IT', 'March'])'''

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
page = requests.get('https://www.jackssmallengines.com/jacks-parts-lookup/part/oregon/20021')
soup = BeautifulSoup(page.content, 'html.parser')
Productpage = soup.find(class_='content-wrapper')
Item_image = Productpage.find('img', {'src': re.compile('.jpg')})
Item_name = Productpage.find(itemprop='name').get_text()
Item_part_number = Productpage.find(class_='itemPartNum').get_text()
Item_Price = Productpage.find(class_='item-price').get_text()
Item_Desc = Productpage.find(class_='tab').get_text()
Item_src = Item_image['src'] + '\n'

ItemName =(Item_name.lstrip())
#print(Item_part_number)
ItemPrice =(Item_Price.lstrip())
#print(Item_Desc)
Product_details = (ItemName + Item_part_number + ItemPrice + Item_src + Item_Desc)
print(Product_details)
file = open('Data1.txt', 'w')
file.write(Product_details)
file.close()





























