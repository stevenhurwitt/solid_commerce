
import csv
import json


with open('U:/Marketplaces/eBay/Data/CompetitorScrapes/poweredbymoyer/StoreScrape.07222019.csv') as file:
    list_of_dicts = []
    for line in file:
        new_line = (
            line.strip('\n').strip('"').replace('""', '"').replace('"', '\\"').replace(" '", ' "').replace("{'", '{"')
                .replace("',", '",').replace("':", '":').replace("['", '["').replace("']", '"]').replace("'}", '"}')
                .replace('\\",', '",').replace(': \\"', ': "').replace("\\'", "'").replace('Tap "N', "Tap 'N")
                .replace(': None', ': "None"').replace('\\"}', '"}')
        )
        new_dict = dict(json.loads(new_line))
        if new_dict['Shipping'] != 'None':
            try:
                new_dict_shipping = new_dict['Shipping']['ShippingDetails']['ShippingServiceOption'][0]
                del new_dict['Shipping']
                if new_dict_shipping != 'None':
                    combined_dict = {**new_dict, **new_dict_shipping}
                    print(combined_dict)
                    list_of_dicts.append(combined_dict)
            except:
                del new_dict['Shipping']
                list_of_dicts.append(new_dict)
    keys = list_of_dicts[0].keys()
    save_file_path = 'U:/Marketplaces/eBay/Data/CompetitorScrapes/poweredbymoyer/StoreScrape.07222019.fixed.csv'
    with open(save_file_path, 'w', newline='', encoding='utf-8', errors='ignore') as csv_file:
        dict_writer = csv.DictWriter(csv_file, keys)
        dict_writer.writeheader()
        data = [{k: v for k, v in record.items() if k in keys} for record in list_of_dicts]
        dict_writer.writerows(data)
