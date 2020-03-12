import requests
from bs4 import BeautifulSoup
import re


class API:

    def __init__(self, store_name, app, login_id, login_password, catalog, database_id):
        self.store_name = store_name
        self.login_id = login_id
        self.login_password = login_password
        self.catalog = catalog
        self.database_id = database_id
        self.base_url = 'https://' + self.store_name + '.partsmartweb.com/scripts/EmpartISAPI.dll?'
        self.mf_url = self.base_url + 'MF'
        self.ajax_url = self.base_url + 'AJAX'
        self.fx_url = self.base_url + 'XF'
        self.s_user_rand = ''
        self.session_id = ''
        self.app = app
    # Additional Notes at EOF

    def get_session(self):
        data = {'app': self.app,
                'TF': 'EmpartWeb',
                'lang': 'EN',
                'loginID': self.login_id,
                'loginPWD': self.login_password}
        response = requests.post(self.mf_url, data=data)
        pattern = re.compile(r'var (\S* = \S*);')
        soup = BeautifulSoup(response.text, 'lxml')
        soup_vars = soup.find_all("script", text=pattern)
        soup_vars_dict = {text.split('=')[0].strip().strip("'"): re.split(' = ', text)[1].strip().strip("'") for
                          text in re.findall(pattern, soup_vars[1].text)}
        url_parameters_dict = {parameter.split('=')[0]: parameter.split('=')[1] for
                               parameter in soup_vars_dict['sMainURL'].split('&')[1:]}
        self.s_user_rand = soup_vars_dict['sUserRand']
        self.session_id = url_parameters_dict['session']

    def get_product_line(self):
        catalog_data = {'app': self.app,
                        'session': self.session_id,
                        'cat': self.catalog,
                        'mode': '11'}
        catalog_url = (self.mf_url +
                       '&app=' + catalog_data['app'] +
                       '&session=' + catalog_data['session'] +
                       '&cat=' + catalog_data['cat'] +
                       '&mode=' + catalog_data['mode'])
        catalogue_response = requests.get(catalog_url)
        soup = BeautifulSoup(catalogue_response.text, 'lxml')
        level_1 = [tag.get('data-assembly-id') for tag in soup.select('.assemblyTree-item')]
        level_2_data = {'app': self.app,
                        'session': self.session_id,
                        'catalogId': self.catalog,
                        'assemblyId': '1',
                        'level': '1',
                        'mode': 'assemblyChildren'}
        level_2 = requests.post(self.ajax_url, data=level_2_data)
        level_3_data = {'app': self.app,
                        'session': self.session_id,
                        'catalogId': self.catalog,
                        'assemblyId': '2',
                        'level': '2',
                        'mode': 'assemblyChildren'}
        level_3 = requests.post(self.ajax_url, data=level_3_data)
        level_4_data = {'app': self.app,
                        'session': self.session_id,
                        'catalogId': self.catalog,
                        'assemblyId': '3',
                        'level': '3',
                        'mode': 'assemblyChildren'}
        level_4 = requests.post(self.ajax_url, data=level_4_data)
        print(level_4.text)

    def part_search(self, product_id):
        search_data = {'searchType': '2',
                       'partName': product_id,
                       'app': self.app,
                       'session': self.session_id,
                       'mode': 'PartSearch',
                       'TF': 'Search\\searchResultsPT',
                       'searchDB': self.database_id,
                       'modelSearchMask': '1',
                       'hidePriorIcon': 'FALSE',
                       'hideSuperIcon': 'FALSE',
                       'showPriceIcon': 'TRUE'}
        search_response = requests.post(self.fx_url, data=search_data)
        soup = BeautifulSoup(search_response.content, 'lxml')
        # print(product_id)
        # print(soup.prettify())
        # input('press enter')
        rows = soup.select('tr.SearchRow')
        if len(rows) > 0:
            cells = [cell.text.strip() for cell in rows[0].select('td')]
            part = {'PartName': cells[0],
                    'PartDescription': cells[1]}
            if part['PartName'] == product_id:
                return part
            else:
                return None
        else:
            return None

    def part_where_used(self, part):
        part_data = {'session': self.session_id,
                     'app': self.app,
                     'TF': 'emHeirarchy',
                     'mode': '10',
                     'DBID': self.database_id,
                     'PartName': part['PartName'],
                     'PartDesc': part['PartDescription'],
                     'searchType': '2'}
        part_response = requests.post(self.mf_url, data=part_data)
        soup = BeautifulSoup(part_response.text, 'lxml')
        # print(soup.prettify())
        # input('press enter')
        where_used_strings = [re.split('-->', used.text)[0] for used in soup.select('span.Tree')]
        return where_used_strings

    def get_part_where_used(self, product_id):
        search_result = self.part_search(product_id)
        if search_result is not None:
            where_used = self.part_where_used(search_result)
            if len(where_used) > 0:
                return where_used
            else:
                return ['No Where Used Information Available']
        else:
            return ['No Matching Part']

    def get_part_where_used_from_list(self, product_dicts):
        dicts = []
        for product_dict in product_dicts:
            where_used = self.get_part_where_used(product_dict['ProductID'].strip('[').strip(']'))
            product_dict.update({'WhereUsed': where_used})
            dicts.append(product_dict)
        return dicts
        # return [product_dict.update({'WhereUsed': self.get_part_where_used(product_dict['ProductID'])}) for
        #         product_dict in product_dicts]

# Known but not limited to the following:
# for endpoint ?XF
# TF (template) can equal:
    # imgToolbar
    # iplHeader
    # jsLanguage
    # Search\\...
        # \\tabModel
        # \\tabParts
        # \\tabLit
        # \\tabAttr
        # \\searchResultsFrame
        # \\tabModelCompare

# for endpoint ?MF
# TF (template) can equal:
    # EmpartWeb
    # modelInfo
    # modelDetails
    # modelLiterature
    # iplLoader
    # iplImage
    # IPLFrame
    # iplImageFrame
    # emImage
    # imgLoader
    # emIPL
    # ewMain
    # jsCfgBase
    # partnerRedirect
    # emAboutEN
    # mngPickList
    # epcFrame
    # userNotesFrame
    # attFileFrame (attachments?)
    # some if not all Search\\... from above