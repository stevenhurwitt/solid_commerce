from classes import Distributor_PED
from classes import Distributor_CPD
import os
import json


def main():
    script_dir = os.path.dirname(__file__)
    rel_path = "data/DistributorsAndBrands.txt"
    abs_file_path = os.path.join(script_dir, rel_path)
    distributor_selection_menu_string = 'Distributors\n' \
                                        '-----------------------------\n' \
                                        '[1] Power Equipment Distributors\n' \
                                        '[2] Central Power Distributors\n' \
                                        '[3] Oscar Wilson\n' \
                                        '[4] Golden Eagle\n' \
                                        '[5] Self Distributing Manufacturers'
    print(distributor_selection_menu_string)
    distributor_selection = input('Select a Distributor: ')
    distributors_dict = {'1': 'PED',
                         '2': 'CPD',
                         '3': 'OW',
                         '4': 'GE',
                         '5': 'Single'}
    with open(abs_file_path, 'r') as text_file:
        brands = json.load(text_file)[distributors_dict[distributor_selection]]
        menu_dict = {}
        brands_menu_string = 'Manufacturer Selection Menu' \
                             '\n-----------------------------\n'
        i = 1
        for k, v in brands.items():
            brands_menu_string += '[' + str(i) + '] ' + v + '\n'
            menu_dict[str(i)] = k
            i += 1
        cls()
        print(brands_menu_string)
        selected_brand = menu_dict[input('Which Brand: ')]
    distributor = None
    if distributor_selection == '1':
        distributor = Distributor_PED.PED(selected_brand, brands[selected_brand])
    elif distributor_selection == '2':
        distributor = Distributor_CPD.CPD(selected_brand, brands[selected_brand])
    xml_action_dict = {'1': distributor.inventory_from_file_to_xml,
                       '2': distributor.inventory_from_web_to_xml,
                       '3': distributor.inventory_from_api_to_xml}
    csv_action_dict = {'1': distributor.inventory_from_file_to_csv,
                       '2': distributor.inventory_from_web_to_csv,
                       '3': distributor.inventory_from_api_to_csv}
    actions_dicts = {'1': xml_action_dict, '2': csv_action_dict}
    distributor_menu_string = distributor.distributor_long_name + '\n-----------------------------\n' \
                                                                  '[1] Inventory From File\n' \
                                                                  '[2] Inventory From Website\n' \
                                                                  '[3] Inventory From API'
    output_selection_menu_string = distributor.distributor_long_name + '\n-----------------------------\n' \
                                                                       '[1] XML\n' \
                                                                       '[2] CSV'
    cls()
    print(distributor_menu_string)
    selected_action = input('What Would You Like To Do?: ')
    cls()
    print(output_selection_menu_string)
    selected_output = input('Select Output Format: ')
    try:
        actions_dicts[selected_output][selected_action]()
    except NotImplementedError:
        cls()
        print('That Source has not been implemented yet. Please make another selection')
        input('Press Enter to Continue')
        cls()
        main()
    cls()
    main()


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


main()
