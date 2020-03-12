from lxml import etree as et


def key_value_pair_as_etree_element(key, value):
    try:
        element = et.Element(key)
        if key is 'ItemID':
            element.text = et.CDATA(value)
        else:
            element.text = value
    except TypeError:
        element = et.Element(key)
        element.text = ''

    return element


def dicts_to_xml(parent_element, dictionary):
    for key, value in dictionary.items():
        element = et.Element(key)
        if isinstance(value, dict):
            dicts_to_xml(element, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    dicts_to_xml(element, item)
        elif value is None or value == '' or value == 'None':
            continue
        else:
            try:
                element.text = et.CDATA(value)
            except TypeError:
                element.text = ''
        parent_element.append(element)
    return parent_element
