import csv


import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

page = requests.get('https://www.jackssmallengines.com/Products/ARIENS/Air-Filters')
soup = BeautifulSoup(page.content, 'html.parser')
Product_details = soup.find(class_='product')
for Partnumber in Product_details.findAll('td'):
    Part_Number = (Partnumber.get("class"))
    print(Part_Number)





#file = open('linksfile.txt', 'w')
'''for link in Product_image.findAll("a"):
    All_links = (link.get("src"))
    print(All_links)
    file.write(All_links)
file.close()'''


#path = ('T:\McHenryPowerEquipment\data\\linksofARIairfilter.txt')
