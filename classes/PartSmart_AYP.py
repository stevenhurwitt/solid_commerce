from classes import Distributor_OW


class GardnerAPI(Distributor_OW):

    # https://www.gardnerinc.com
    def __init__(self):
        super(GardnerAPI, self).__init__('AYP', 'AYP')
        self.login = 'dealer1'
        self.password = '1015566202'
        self.app = 'grdn'


class JonseredAPI:

    def __init__(self, login, password, app):

        self.login = login
        self.password = password
        self.app = app
        self.search_db = 138
        self.cat = 152


class HusqAPI:

    def __init__(self, login, password, app):

        self.login = login
        self.password = password
        self.app = app
        self.search_db = 1020
        self.cat = 1029


class AYPHusqAPI:

    def __init__(self, login, password, app):

        self.login = login
        self.password = password
        self.app = app
        self.search_db = 1020
        self.cat = 1030


class McCollAPI:

    def __init__(self, login, password, app):

        self.login = login
        self.password = password
        self.app = app
        self.search_db = 1021
        self.cat = 1050


class PoulanWEEAPI:

    def __init__(self, login, password, app):

        self.login = login
        self.password = password
        self.app = app
        self.search_db = 1042
        self.cat = 1051
