from lxml import etree as et
from xml.etree import ElementTree


def get_dict(element):
    element_dict = {}
    for child in list(element):
        if len(list(child)) > 0:
            element_dict.update(get_dict(child))
        else:
            element_dict.update({child.tag: child.text})
    return {element.tag: element_dict}
