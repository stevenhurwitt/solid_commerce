import csv
'''with open('employee_file.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    employee_writer.writerow(['John Smith', 'Accounting', 'November'])
  employee_writer.writerow(['Erica Meyers', 'IT', 'March'])'''

import requests
from bs4 import BeautifulSoup
import pandas as pd
page = requests.get('https://forecast.weather.gov/MapClick.php?lat=42.026170000000036&lon=-88.06541999999996#.XajOpehKiUk')
soup = BeautifulSoup(page.content, 'html.parser')
week = soup.find(id='seven-day-forecast-body')
#print(week)
items = week.find_all(class_='tombstone-container')
#print(items[0])
items[0].find(class_='period-name').get_text()
items[0].find(class_='short-desc').get_text()
items[0].find(class_='temp').get_text()

period_names = [item.find(class_='period-name').get_text() for item in items]
short_description = [item.find(class_='short-desc').get_text() for item in items]
temperature = [item.find(class_='temp').get_text() for item in items]
#print(period_names)
#print(short_description)
#print(temperature)
BOLD = '\033[1m'
weather_stuff = pd.DataFrame(
    {

      'Period': period_names,
      'Short_description' : short_description,
      'Temperature' : temperature
    })
print(weather_stuff)
path = 'T:\McHenryPowerEquipment\data\\Testing.csv'
weather_stuff.to_csv(path)

