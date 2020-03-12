import os
from lxml import etree
from lxml import objectify


class Interface:

    def __init__(self):
        self.root = '\\'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[0:-1])
        self.schema_file = os.path.join(self.root, 'data', 'ShipWorksSchema.xsd')
        self.schema_xml = self.parse_schema_to_xml()
        print(self.schema_xml)

    def parse_schema_to_xml(self):
        with open(self.schema_file, 'rb') as file:
            xslt_content = file.read()
            xslt_root = etree.XML(xslt_content)
            schema = etree.XMLSchema(xslt_root)
            parser = etree.XMLParser(schema=schema)
            root = etree.fromstring('<Order>test</Order>', parser)
            return root


Interface()
