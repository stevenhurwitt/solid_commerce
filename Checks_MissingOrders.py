from classes import Database_Ideal
from lxml import etree as element_tree
from collections import defaultdict
import time
import os


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


ideal = Database_Ideal.Database()
start_and_range = ideal.get_oldest_sales_order_reference_and_range()
oldest_order_request_string = '<SixBitAPICalls><Order_List externalorderid="' + start_and_range[0] + '"/></SixBitAPICalls>'
with open('T:/ProgramData/SixBit/Automation/XmlDrop/Input/' + start_and_range[0] + '.xml', 'w')as file:
    file.writelines(oldest_order_request_string)
output_filepath = 'T:/ProgramData/SixBit/Automation/XmlDrop/Output/'
while not any(fname.startswith(start_and_range[0]) for fname in os.listdir(output_filepath)):
    time.sleep(1)
xml_file_name = [i for i in os.listdir(output_filepath) if os.path.isfile(os.path.join(output_filepath, i)) and start_and_range[0] in i][0]
xml_filepath_full = output_filepath + '/' + xml_file_name
with open(xml_filepath_full, 'r', encoding='utf8') as xml_file:
    xml_string = xml_file.read()
parser = element_tree.XMLParser(recover=True)
tree = element_tree.fromstring(xml_string, parser=parser)
for shipment in tree:
    shipment_dict = etree_to_dict(shipment)
    print(shipment_dict['OrderID'])
    order_list_string = '<SixBitAPICalls><Order_List startid="' + start_and_range[0] + '" count="' + start_and_range[1] + '" /></SixBitAPICalls>'
    time_id = time.strftime("%m%d%Y%I%M")
    orders_filepath = 'T:/ProgramData/SixBit/Automation/XmlDrop/Input/' + time_id + '.xml'
    with open(orders_filepath, 'w')as file:
        file.writelines(order_list_string)
    while not any(fname.startswith(time_id) for fname in os.listdir(output_filepath)):
        time.sleep(1)
    orders_xml_file_name = [i for i in os.listdir(output_filepath) if os.path.isfile(os.path.join(output_filepath, i)) and time_id in i][0]
    orders_xml_filepath_full = output_filepath + '/' + orders_xml_file_name
    with open(orders_xml_filepath_full, 'r', encoding='utf8') as orders_xml_file:
        orders_xml_string = orders_xml_file.read()
    parser = element_tree.XMLParser(recover=True)
    tree = element_tree.fromstring(xml_string, parser=parser)
    for orders in tree:
        orders_dict = etree_to_dict(orders)
        print(orders_dict)
