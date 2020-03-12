import requests
from bs4 import BeautifulSoup
import pandas as pd

import re

page = requests.get('https://www.jackssmallengines.com/jacks-parts-lookup/part')
#page = requests.get('https://www.jackssmallengines.com/jacks-parts-lookup/')
Page = BeautifulSoup(page.content, 'html.parser')


