from classes import Distributor
from classes import SolidCommerce
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import InvalidArgumentException
from multiprocessing.pool import ThreadPool
import selenium.webdriver as webdriver
import json
import time
import requests
from bs4 import BeautifulSoup
from functools import partial


# noinspection SpellCheckingInspection,SpellCheckingInspection
class AIP(Distributor.Distributor):

    def __init__(self, manufacturer_short_name, manufacturer_long_name):
        super(AIP, self).__init__('AIP', "A&I Products")
        self.manufacturer_short_name = manufacturer_short_name
        self.manufacturer_long_name = manufacturer_long_name
        self.manufacturer_file_path_root = r'T:/ebay/' + self.manufacturer_short_name
        self.user_id = None
        self.dealer_id = None
        self.password = None
        self.set_ids()
        self.updated_products = []

    def update_images_and_description_from_file(self):
        solid_api = SolidCommerce.API()
        products, primary_key, filepath = self.open_selected_csv_with_primary_key()
        for product in products:
            try:
                product_update = self.get_product_info(product[primary_key])
                product_update.custom_sku = product['SKU']
                solid_api.update_insert_product(product_update.as_product_xml_string())
            except:
                print(product[primary_key])

    def get_product_info(self, item_number):
        aip_api = API()
        aip_api.item_number = item_number
        product_info_html_dict = aip_api.get_all_html()
        product_info_html = self.get_product_html_for_ebay(product_info_html_dict)
        picture_links = product_info_html_dict['PictureLinks']
        product_object = SolidCommerce.Product()
        product_object.ebay_description = product_info_html
        product_object.mystore_description = product_info_html
        product_object.description = product_info_html
        if len(picture_links) > 0:
            product_object.main_image = picture_links.pop(0)
        if len(picture_links) > 0:
            product_object.alternate_images = picture_links
        return product_object

    def get_product_html_for_ebay(self, product_info_html_dict):
        model_dict = self.model_tables_list_as_dict(product_info_html_dict['Models'])
        mega_cross_dict = self.mega_cross_tables_list_as_dict(product_info_html_dict['MegaCrosses'])
        attributes = product_info_html_dict['Attributes'].prettify().replace(
            'Kevlar Cord Kevlar Cord', 'Kevlar Cord').replace('Kevlar', 'with Kevlar')
        self.replace_a_tags(product_info_html_dict['KitMaster'])
        [self.replace_a_tags(model_info) for model_info in product_info_html_dict['Models']]
        [self.replace_a_tags(cross_info) for cross_info in product_info_html_dict['MegaCrosses']]
        kit_info = product_info_html_dict['KitMaster']
        html = (
            str(attributes) +
            '<h3>Kit Details:</h3><br />' + str(kit_info) +
            self.model_dict_as_html(model_dict) +
            self.mega_crosses_dict_as_html(mega_cross_dict)
        )
        return html

    def replace_a_tags(self, soup_element):
        try:
            for link_element in soup_element.select('a'):
                soup = BeautifulSoup(str(soup_element), features='lxml')
                new_element = soup.new_tag('td')
                new_element.string = link_element.text
                link_element.parent.replace_with(new_element)
        except AttributeError:
            pass

    def model_dict_as_html(self, models_dict):
        model_html = '<h3>Fits Models:</h3>'
        for model_name, model_specifics in models_dict.items():
            model_html += (
                    '<h4>' + model_name.title() + "'s</h4><br />" +
                    '<span>' + ', '.join(model_specifics) + '</span>'
            )
        return model_html

    def mega_crosses_dict_as_html(self, mega_crosses_dict):
        try:
            crosses_html = '<h3>Replaces:</h3>'
            replaces_dicts = mega_crosses_dict['Replaces:']
            for replacement in replaces_dicts:
                crosses_html += ('<b>' + replacement['Brand'].title() + '</b> Part Number: ' +
                                 replacement['PartNumber'] + ', ')
            return crosses_html.strip(', ')
        except KeyError:
            return ''


    def model_tables_list_as_dict(self, model_tables):
        model_lists = {}
        for table in model_tables:
            for model_link in table.select('a')[3:]:
                model_info = model_link.text.split(':')
                if model_info[0] not in model_lists:
                    try:
                        model_lists[model_info[0]] = [model_info[1]]
                    except IndexError:
                        pass
                else:
                    model_lists[model_info[0]].append(model_info[1])
        return model_lists

    def mega_cross_tables_list_as_dict(self, cross_tables):
        cross_lists = {}
        cross_key = None
        for table in cross_tables:
            for row in table.select('tr'):
                row_list = [cell.text for cell in row.select('td')]
                if row_list[0] != '':
                    cross_key = row_list[0]
                if cross_key not in cross_lists:
                    cross_lists[cross_key] = [{
                        'PartNumber': row_list[1],
                        'Brand': row_list[2]
                    }]
                else:
                    cross_lists[cross_key].append({
                        'PartNumber': row_list[1],
                        'Brand': row_list[2]
                    })
        return cross_lists

    def inventory_from_api(self, products):
        browser = webdriver.Firefox()
        self.dealer_site_login(browser)
        cookies = browser.get_cookies()
        browser.quit()
        func = partial(self.inventory, cookies)
        with ThreadPool(20) as inventory_pool:
            inventory_pool.map(func, products)
        return self.updated_products

    def shipping_from_api(self):
        solid_api = SolidCommerce.API()
        order_search_filter = SolidCommerce.OrderSearchFilter()
        order_search_filter.page = '1'
        order_search_filter.records_per_page_count = '1000'
        order_search_filter.filter_by_order_status = 'true'
        order_search_filter.order_status = 'PAID'
        order_search_filter.filter_by_warehouse = 'true'
        order_search_filter.order_search_format = 'ByOrderItems'
        aip_company_lists = [
            company_list for company_list in solid_api.get_all_company_lists() if
            company_list.list_name.split('-')[0] == 'A&I'
        ]
        aip_orders = {order.po_number: order for order in list(self.get_orders())}
        for warehouse in aip_company_lists:
            order_search_filter.warehouse_list = warehouse.list_id
            open_orders = [
                open_order for open_order in solid_api.search_orders_v6(order_search_filter.as_element())
            ]
            for open_order in open_orders:
                try:
                    order_page = aip_orders[open_order.sale_id]
                    self.update_shipping(order_page)
                    open_order.status = 'Drop Shipped AIP'
                    solid_api.update_order_status(open_order)
                except KeyError:
                    print('Order number ' + open_order.sale_id + ' not found')
                except TypeError:
                    pass
                except AttributeError:
                    print('Attribute Error: ' + str(open_order))

    def shipping_from_orders_page(self):
        order_dicts = {
            order.po_number: order for order in list(self.get_orders()) if order.ship_date == time.strftime("%m/%d/%Y")
        }
        for order_number, order_object in order_dicts.items():
            solid_api = SolidCommerce.API()
            order_search_filter = SolidCommerce.OrderSearchFilter()
            order_search_filter.page = '1'
            order_search_filter.records_per_page_count = '1000'
            order_search_filter.order_search_format = 'ByOrderItems'
            order_search_filter.search_type = 'BySCOrderID'
            try:
                self.update_shipping(order_object)
                order_search_filter.search_value = order_number
                open_order = solid_api.search_orders_v6(order_search_filter.as_element())[0]
                open_order.status = 'Drop Shipped AIP'
                solid_api.update_order_status(open_order)
            except TypeError:
                pass

    @staticmethod
    def update_shipping(order_page):
        shipping_type_cases = {'UPS': 'UPSGround',
                               'SpeeDee': 'SpeeDeeDelivery'}
        shipping_package_type_cases = {'UPS': '0', 'SpeeDee': '0'}
        shipment_api_update = SolidCommerce.Shipment()
        shipment_api_update.sc_sale_id = order_page.po_number
        shipment_api_update.ship_date = order_page.ship_date
        shipment_api_update.ship_cost = order_page.freight
        shipment_api_update.tracking_number = order_page.order_shipments[0]['Track / PRO Number']
        shipment_api_update.marketplace = '3'
        shipment_api_update.shipping_type_code = shipping_type_cases[order_page.order_shipments[0]['Shipper']]
        shipment_api_update.package_type = shipping_package_type_cases[order_page.order_shipments[0]['Shipper']]
        solid_api_shipping_update_call = SolidCommerce.API()
        solid_api_shipping_update_call.update_ebay_shipment(shipment_api_update.as_shipment_element())

    def get_cookies(self):
        browser = webdriver.Firefox()
        self.dealer_site_login(browser)
        cookies = browser.get_cookies()
        browser.quit()
        return cookies

    def get_orders(self):
        session = self.get_session()
        orders_html = self.get_orders_html(session)
        soup = BeautifulSoup(orders_html, features="lxml")
        order_rows = soup.select('tr.RowSpacing')
        for row in order_rows[7:-1]:
            order_object = SeleniumOrdersRow()
            order_object.set_from_soup(row)
            order_page_object = self.parse_order_page(self.get_order_html(
                session, order_object.order, order_object.invoice_number
            ))
            yield order_page_object

    def get_order_html(self, session, order_number, invoice_number):
        url = ('https://www.aiproducts.com/dealer/OrderDetl.htm?OrderNumber=' +
               order_number +
               '&InvoiceNumber=' +
               invoice_number)
        response = session.get(url)
        return response.text

    def get_orders_html(self, session):
        url = 'https://www.aiproducts.com/dealer/orders.htm'
        response = session.get(url)
        return response.text

    def get_session(self):
        cookies = self.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        return session

    def inventory(self, cookies, product):
        mfr = product.sku.split('~')[0]
        product_id = product.sku.split('~')[1]
        if mfr == 'BRS':
            product_id = 'B1' + product_id
        html_string = self.get_product_html(cookies, product_id, '100')
        aip_inventory_obj = InventoryPage()
        try:
            aip_inventory_obj.product_id = product_id
            aip_inventory_obj.from_html(html_string)
            product.warehouse_with_inventory_dicts = aip_inventory_obj.as_dict_warehouses()
            product.cost = aip_inventory_obj.cost
            self.updated_products.append(product)
        except KeyError:
            self.log_distributor_event(
                self.get_log_dict(
                    product.sku,
                    'Error - No Inventory',
                    'Catalogue Product not available at distributor'
                )
            )

    def inventory_from_default(self, products):
        return self.inventory_from_api(products)

    @staticmethod
    def get_product_html(cookies, product_id, qty):
        url = 'https://www.aiproducts.com/catalog/Available.htm?ItemNumber=' + product_id + '&CheckQuantity=' + qty
        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])
        response = s.get(url)
        return response.content

    def set_ids(self):
        ids_filepath = 'T://MchenryPowerEquipment/data/aip_ids.txt'
        with open(ids_filepath, 'r') as text_file:
            kaw_ids = json.load(text_file)
            self.dealer_id = kaw_ids['DealerID']
            self.user_id = kaw_ids['UserID']
            self.password = kaw_ids['Password']

    def dealer_site_login(self, browser):
        login_url = r'https://' + self.user_id + ':' + self.password + '@www.aiproducts.com/dealer/customer.htm'
        browser.get(login_url)

    @staticmethod
    def nav_menu(browser, menu_string):
        frame_xpath = '/html/frameset/frameset/frame[1]'
        frame = browser.find_element_by_xpath(frame_xpath)
        browser.switch_to.frame(frame)
        browser.find_element_by_xpath("(//*[contains(text(), '" + menu_string + "')])").click()

    @staticmethod
    def nav_sub_menu(browser, sub_menu_string):
        browser.find_element_by_xpath("(//*[contains(text(), '" + sub_menu_string + "')])").click()

    def get_orders_page(self, browser):
        self.dealer_site_login(browser)
        self.nav_menu(browser, "Ordering & Information")
        self.nav_sub_menu(browser, "View Orders")

    @staticmethod
    def parse_order_page(html_string):
        try:
            order_page_object = OrderPage()
            order_page_object.set_from_tree(html_string)
            return order_page_object
        except InvalidArgumentException:
            pass

    def get_tracking(self):
        return self.get_tracking_of_date(time.strftime("%m/%d/%Y"))

    def get_tracking_input_date(self):
        date = input('Enter Date (MM/DD/YYYY): ')
        return self.get_tracking_of_date(date)

    def get_tracking_of_date(self, date):
        today_date_string = date
        orders_frame_xpath = r'/html/frameset/frameset/frame[2]'
        orders_xpath = '/html/body/table/tbody/tr[2]/td/table/tbody/tr'
        browser = webdriver.Firefox()
        self.get_orders_page(browser)
        browser.switch_to.default_content()
        frame = browser.find_element_by_xpath(orders_frame_xpath)
        browser.switch_to.frame(frame)
        time.sleep(5)
        orders_rows = browser.find_elements_by_xpath(orders_xpath)
        row_objects = []
        for selenium_row in orders_rows[2:-1]:
            selenium_object = SeleniumOrdersRow()
            try:
                selenium_object.set_from_selenium(selenium_row)
                row_objects.append(selenium_object)
            except NoSuchElementException:
                pass
        row_dicts = [row_object.as_dict() for row_object in row_objects]
        shipped_orders_rows = [row_dict for row_dict in row_dicts if row_dict['ShipDate'] is not '' and row_dict['ShipDate'] == today_date_string]
        order_page_objects = []
        for shipped_order_row in shipped_orders_rows:
            browser.get(shipped_order_row['Order'])
            parsed_order_page = self.parse_order_page(browser.page_source)
            order_page_objects.append(parsed_order_page)
        browser.quit()
        for order_page_object in order_page_objects:
            print(order_page_object.as_dict())
        return order_page_objects

    def write_tracking_to_drop_folder(self):
        pass


class API(object):

    def __init__(self):
        self.base_url = 'https://www.allpartsstore.com/'
        self.item_number = None

    def get_all_html(self):
        return{
            'Models': self.get_model_html(),
            'MegaCrosses': self.get_mega_cross_html(),
            'PictureLinks': self.get_picture_links(),
            'Attributes': self.get_attribute_area_html(),
            'KitMaster': self.get_kit_area_html()
        }

    def get_model_html(self):
        model_area = ModelArea()
        model_area.item_number = self.item_number
        return model_area.get_all_html()

    def get_mega_cross_html(self):
        mega_cross = MegaCrossArea()
        mega_cross.item_number = self.item_number
        return mega_cross.get_all_html()

    def get_picture_links(self):
        graphic_area = GraphicArea()
        graphic_area.item_number = self.item_number
        return graphic_area.get_picture_links()

    def get_attribute_area_html(self):
        attribute_area = AttributeArea()
        attribute_area.item_number = self.item_number
        return attribute_area.get_html()

    def get_kit_area_html(self):
        kit_area = KitMaster()
        kit_area.item_number = self.item_number
        return kit_area.get_html()


# noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
class ItemDetails(API):

    def __init__(self):
        super(ItemDetails, self).__init__()
        self.end_point = self.base_url + 'ItemDetl.htm'
        self.session_id = None
        self.category_seq = None
        self.selc_brand = None
        self.selc_machn = None
        self.selc_model = None
        self.selc_sectn = None
        self.selc_sub_sc = None
        self.search_item = None
        self.text_search = None

    def as_dict(self):
        return{
            'SessionID': self.session_id,
            'CategorySeq': self.category_seq,
            'SelcBrand': self.selc_brand,
            'SelcMachn': self.selc_machn,
            'SelcModel': self.selc_model,
            'SelcSectn': self.selc_sectn,
            'SelcSubsc': self.selc_sub_sc,
            'SearchItem':  self.search_item,
            'TextSearch': self.text_search,
            'ItemNumber': self.item_number,
        }


class ItemNotes(API):

    def __init__(self):
        super(ItemNotes, self).__init__()
        self.end_point = self.base_url + 'Notes.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }


class AddList(API):

    def __init__(self):
        super(AddList, self).__init__()
        self.end_point = self.base_url + 'AddList.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }


class ListNext(API):

    def __init__(self):
        super(ListNext, self).__init__()
        self.end_point = self.base_url + 'ListNext.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }


class GraphicArea(API):

    def __init__(self):
        super(GraphicArea, self).__init__()
        self.end_point = self.base_url + 'Graphic.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        return BeautifulSoup(response.text, features='lxml')

    def get_picture_links(self):
        picture_html = self.get_html()
        return [picture['src'] for picture in picture_html.findAll('img')]


class AttributeArea(API):

    def __init__(self):
        super(AttributeArea, self).__init__()
        self.end_point = self.base_url + 'Attribute.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        response_soup = BeautifulSoup(response.text, features='lxml')
        if response_soup.prettify() == '':
            return ''
        else:
            return response_soup.select('div')[0]


class KitMaster(API):

    def __init__(self):
        super(KitMaster, self).__init__()
        self.end_point = self.base_url + 'KitMaster.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        response_soup = BeautifulSoup(response.text, features='lxml')
        if response_soup.prettify() == '':
            return ''
        else:
            return response_soup.select('table')[0]


class ModelArea(API):

    def __init__(self):
        super(ModelArea, self).__init__()
        self.end_point = self.base_url + 'Model.hsm'
        self.start_index = 1

    def as_dict(self):
        return{
            'ItemNumber': self.item_number,
            'StartIndex': str(self.start_index)
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        return BeautifulSoup(response.text, features='lxml')

    def get_all_html(self):
        all_html = []
        while True:
            html = self.get_html()
            if html.prettify() == '':
                break
            all_html.append(html.select('table')[0])
            self.start_index += 20
        return all_html


class Manual(API):

    def __init__(self):
        super(Manual, self).__init__()
        self.end_point = self.base_url + 'Manual.hsm'

    def as_dict(self):
        return{
            'ItemNumber': self.item_number
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        return BeautifulSoup(response.text, features='lxml')


class MegaCrossArea(API):

    def __init__(self):
        super(MegaCrossArea, self).__init__()
        self.end_point = self.base_url + 'MegaCross.hsm'
        self.start_index = 1

    def as_dict(self):
        return{
            'ItemNumber': self.item_number,
            'StartIndex': str(self.start_index)
        }

    def get_html(self):
        response = requests.get(self.end_point, self.as_dict())
        return BeautifulSoup(response.text, features='lxml')

    def get_all_html(self):
        all_html = []
        while True:
            html = self.get_html()
            if html.prettify() == '':
                break
            all_html.append(html.select('table')[0])
            self.start_index += 20
        return all_html


class SeleniumOrdersRow(object):

    def __init__(self):
        self.order_date = None
        self.order = None
        self.invoice_number = ''
        self.ship_date = None
        self.po_number = None
        self.method = None
        self.freight = None
        self.carrier = None

    def set_from_selenium(self, row_selenium_element):
        cells = row_selenium_element.find_elements_by_xpath('td')
        try:
            self.order_date = cells[1].text
        except IndexError:
            pass
        try:
            self.order = cells[2].find_element_by_xpath('a').get_attribute("href")
        except IndexError:
            pass
        try:
            self.invoice_number = cells[3].text
        except IndexError:
            pass
        try:
            self.ship_date = cells[4].text
        except IndexError:
            pass
        try:
            self.po_number = cells[5].text
        except IndexError:
            pass
        try:
            self.method = cells[6].text
        except IndexError:
            pass
        try:
            self.freight = cells[6].text
        except IndexError:
            pass

    def set_from_soup(self, product_soup):
        cells = [cell.text.strip() for cell in product_soup.select('td')]
        self.order_date = cells[1]
        self.order = cells[2]
        try:
            self.invoice_number = cells[3]
        except:
            pass
        self.ship_date = cells[4]
        self.po_number = cells[5]
        self.method = cells[6]
        self.freight = cells[7]

    def as_dict(self):
        return{'OrderDate': self.order_date,
               'Order': self.order,
               'InvoiceNumber': self.invoice_number,
               'ShipDate': self.ship_date,
               'PONumber': self.po_number,
               'Method': self.method,
               'Freight': self.freight,
               'Carrier': self.carrier}


# noinspection SpellCheckingInspection,SpellCheckingInspection
class OrderPage(object):

    def __init__(self):
        self.order_number = None
        self.invoice_number = ''
        self.customer_name = None
        self.customer_address_line1 = None
        self.customer_address_line2 = None
        self.ship_to_name = None
        self.ship_to_address_line1 = None
        self.ship_to_address_line2 = None
        self.ship_to_phone = None
        self.order_date = None
        self.ship_date = None
        self.entered_by = None
        self.po_number = None
        self.parts_total = None
        self.freight = None
        self.handling = None
        self.invoice_total = ''
        self.order_items = None
        self.order_shipments = None
        self.shipment_inquiry_xml = None

    def set_from_tree(self, html_string):
        soup = BeautifulSoup(html_string, features='lxml')
        cells = [cell.text.strip() for cell in soup.select('td td')]
        self.order_number = cells[1]
        try:
            self.invoice_number = cells[4]
        except:
            pass
        self.customer_name = cells[20]
        self.customer_address_line1 = cells[34]
        self.customer_address_line2 = cells[41]
        self.ship_to_name = cells[23]
        self.ship_to_address_line1 = cells[37]
        self.ship_to_address_line2 = cells[44]
        self.ship_to_phone = cells[51]
        self.order_date = cells[61]
        self.ship_date = cells[63]
        self.entered_by = cells[65]
        self.po_number = cells[67]
        self.parts_total = cells[72]
        self.freight = cells[74]
        self.handling = cells[76]
        try:
            self.invoice_total = cells[78]
        except:
            pass
        self.order_items = []
        shipments = soup.select('table.Text')[6].select('tr')
        try:
            shipments_dicts = []
            for shipment in shipments[1:]:
                shipment_dict = {
                    shipments[0].select('td')[0].text: shipment.select('td')[0].text,
                    shipments[0].select('td')[1].text: shipment.select('td')[1].text,
                    shipments[0].select('td')[2].text: shipment.select('td')[2].text,
                    shipments[0].select('td')[3].text: shipment.select('td')[3].text,
                    shipments[0].select('td')[4].text: (shipment.select('td')[4].select('img')[0]
                                                        ['src'].strip('Images/').strip('.gif')),
                    shipments[0].select('td')[5].text: shipment.select('td')[5].text
                }
                shipments_dicts.append(shipment_dict)
            self.order_shipments = shipments_dicts
        except IndexError:
            pass
        self.shipment_inquiry_xml = '<SixBitAPICalls>' \
                                    '<Shipment_List externalorderid="' + self.po_number + '"/>' \
                                    '</SixBitAPICalls>'
    
    def as_dict(self):
        return {
            'OrderNumber': self.order_number,
            'InvoiceNumber': self.invoice_number,
            'CustomerName': self.customer_name,
            'BillToAddress1': self.customer_address_line1,
            'BillToAddress2': self.customer_address_line2,
            'ShipToName': self.ship_to_name,
            'ShipToAddress1': self.ship_to_address_line1,
            'ShipToAddress2': self.ship_to_address_line2,
            'ShipToPhone': self.ship_to_phone,
            'Orderdate': self.order_date,
            'ShipDate': self.ship_date,
            'EnteredBy': self.entered_by,
            'PONumber': self.po_number,
            'Parts_Total': self.parts_total,
            'ShippingCost': self.freight,
            'Handling': self.handling,
            'InvoiceTotal': self.invoice_total,
            'OrderItems': self.order_items,
            'OrderShipments': self.order_shipments
        }


class OrderItem(object):

    def __init__(self, tree_row):
        self.order_qty = None
        self.ship_qty = None
        self.part_number = None
        self.description = None
        self.price_each = None
        self.core_charge = None
        self.line_total = None
        self.set_from_tree_row(tree_row)

    def set_from_tree_row(self, tree_row):
        cells = [cell for cell in iter(tree_row)]
        try:
            self.order_qty = cells[0].text
            self.ship_qty = cells[1].text
            self.part_number = cells[2].text
            self.description = cells[3].text
            self.price_each = cells[4].text
            self.core_charge = cells[5].text
            self.line_total = cells[6].text
        except IndexError:
            pass


class OrderShipment(object):

    def __init__(self, tree_row):
        self.weight = None
        self.tracking = None
        self.shipped_from = None
        self.shipper = None
        self.set_from_tree_row(tree_row)

    def set_from_tree_row(self, tree_row):
        cells = [cell for cell in iter(tree_row)]
        self.weight = cells[1].text
        self.tracking = cells[2].text
        self.shipped_from = cells[3].text
        try:
            self.shipper = cells[4].find('a').find('img').get("src").split('/')[1].split('.')[0]
        except AttributeError:
            self.shipper = cells[4].text.strip()


# noinspection SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection,SpellCheckingInspection
class InventoryPage(object):

    def __init__(self):
        self.product_id = None
        self.cost = None
        self.list_price = None
        self.wh_ia = '0'
        self.wh_il = '0'
        self.wh_nc = '0'
        self.wh_tx = '0'
        self.wh_pa = '0'
        self.wh_mo = '0'
        self.wh_in = '0'
        self.wh_ca = '0'
        self.wh_wa = '0'
        self.wh_ga = '0'
        self.wh_fl = '0'
        self.wh_sb_nc = '0'
        self.wh_sb_ga = '0'
        self.wh_sb_pa = '0'
        self.briggs = '0'
        
    def as_dict(self):
        return{
            'Cost': self.cost,
            'ListPrice': self.list_price,
            'WH_A&I-IA': self.wh_ia,
            'WH_A&I-IL': self.wh_il,
            'WH_A&I-NC': self.wh_nc,
            'WH_A&I-TX': self.wh_tx,
            'WH_A&I-PA': self.wh_pa,
            'WH_A&I-MO': self.wh_mo,
            'WH_A&I-IN': self.wh_in,
            'WH_A&I-CA': self.wh_ca,
            'WH_A&I-WA': self.wh_wa,
            'WH_A&I-GA': self.wh_ga,
            'WH_A&I-FL': self.wh_fl,
            'WH_A&I-SB-NC': self.wh_sb_nc,
            'WH_A&I-SB-GA': self.wh_sb_ga,
            'WH_A&I-SB-PA': self.wh_sb_pa,
            'WH_Briggs': self.briggs
        }

    def as_dict_warehouses(self):
        return{
            'WH_A&I-IA': self.wh_ia,
            'WH_A&I-IL': self.wh_il,
            'WH_A&I-NC': self.wh_nc,
            'WH_A&I-TX': self.wh_tx,
            'WH_A&I-PA': self.wh_pa,
            'WH_A&I-MO': self.wh_mo,
            'WH_A&I-IN': self.wh_in,
            'WH_A&I-CA': self.wh_ca,
            'WH_A&I-WA': self.wh_wa,
            'WH_A&I-GA': self.wh_ga,
            'WH_A&I-FL': self.wh_fl,
            'WH_A&I-SB-NC': self.wh_sb_nc,
            'WH_A&I-SB-GA': self.wh_sb_ga,
            'WH_A&I-SB-PA': self.wh_sb_pa,
            'WH_Briggs': self.briggs,
            'WH_McHenry Inbound': str(int(self.wh_ia) + int(self.wh_il) + int(self.wh_pa) + int(self.wh_mo) +
                                      int(self.wh_in) + int(self.wh_ga) + int(self.wh_sb_ga) + int(self.wh_sb_pa) +
                                      int(self.wh_nc) + int(self.wh_tx) + int(self.wh_sb_nc) + int(self.wh_fl))
        }

    def from_html(self, html_string):
        soup = BeautifulSoup(html_string, features='lxml')
        rows = [row for row in soup. select('tr.RowSpacing') if len(row.select('td')) > 2]
        item = {row.select('td')[0].text.strip(): row.select('td')[2].text.split(' ')[0].strip() for row in rows}
        item['Product ID'] = self.product_id
        self.cost = rows[2].select('td')[2].text.strip().strip('$')
        self.list_price = rows[4].select('td')[2].text.strip().strip('$')
        try:
            self.wh_ia = item['Rock Valley, IA:']
        except:
            pass
        try:
            self.wh_il = item['Rock Island, IL:']
        except:
            pass
        try:
            self.wh_nc = item['Charlotte, NC:']
        except:
            pass
        try:
            self.wh_tx = item['Dallas, TX:']
        except:
            pass
        try:
            self.wh_pa = item['Williamsport, PA:']
        except:
            pass
        try:
            self.wh_mo = item['Seymour, MO:']
        except:
            pass
        try:
            self.wh_in = item['Indianapolis, IN:']
        except:
            pass
        try:
            self.wh_ca = item['Lathrop, CA:']
        except:
            pass
        try:
            self.wh_wa = item['Prosser, WA:']
        except:
            pass
        try:
            self.wh_ga = item['McDonough, GA:']
        except:
            pass
        try:
            self.wh_fl = item['Jacksonville, FL:']
        except:
            pass
        try:
            self.wh_sb_nc = item['~Sunbelt Charlotte, NC:']
        except:
            pass
        try:
            self.wh_sb_ga = item['~Sunbelt McDonough, GA:']
        except:
            pass
        try:
            self.wh_sb_pa = item['~Sunbelt Williamsport, PA:']
        except:
            pass
        try:
            self.briggs = item['~Briggs:']
        except:
            pass
