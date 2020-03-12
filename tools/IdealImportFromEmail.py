import os
import re
import codecs


def check_for_file_in_directory(file_name, directory_path):
    directory_file_names = os.listdir(directory_path)
    if file_name in directory_file_names:
        return True
    else:
        return False


def write_ideal_import_file():
    with codecs.open('S:/ideal for windows/ShipWorks/IdealImport.csv', 'w', 'utf-8') as import_file:
        import_file.writelines([',"FAIL!\n\nNOW!",'])

# '\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks'
pending_orders_directory = 'S:/ideal for windows/ShipWorks/Orders For Import/'
processed_orders_directory = 'S:/ideal for windows/ShipWorks/Processed Emails/'
# pending_orders_directory = '\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks/Orders For Import/'
# processed_orders_directory = '\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks/Processed Emails/'
pending_orders_file_names = os.listdir(pending_orders_directory)
if not check_for_file_in_directory('IdealImport.csv', 'S:/ideal for windows/ShipWorks/'):
# if not check_for_file_in_directory('IdealImport.csv', '\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks/'):
    write_ideal_import_file()
# Only needed if orders from email and IdealImport.csv are in the same folder
# else:
#     pending_orders_file_names.remove('IdealImport.csv')
new_file = []
with codecs.open('S:/ideal for windows/ShipWorks/IdealImport.csv', 'r', 'utf-8') as ideal_import_file:
# with codecs.open('\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks\\IdealImport.csv', 'r', 'utf-8') as ideal_import_file:
    old_file = ideal_import_file.readlines()
    for pending_orders_file_name in pending_orders_file_names:
        with codecs.open(pending_orders_directory + pending_orders_file_name, 'r', 'utf-8') as pending_orders_file:
            pending_orders = pending_orders_file.readlines()
            regex = re.compile(r'\s+ext\.:\s+\w+')
            phone_regex = re.compile(r'\D\d{3}\D+\d{3}\D\d{4}')
            phone_digits_regex = re.compile(r'\d')
            formatted_lines = []
            for line in pending_orders:
                try:
                    try:
                        extension = regex.findall(line)[0]
                        line = line.replace(extension, '')
                    except IndexError:
                        pass
                    phone_number = str(phone_regex.findall(line)[0])
                    formatted_phone = ''.join(phone_digits_regex.findall(phone_number))
                    line = line.replace(phone_number, formatted_phone)
                    formatted_lines.append(line)
                except IndexError:
                    formatted_lines.append(line)
            new_file.append(formatted_lines)
            with codecs.open(processed_orders_directory + pending_orders_file_name, 'w', 'utf-8') as new_pending_orders_file:
                new_pending_orders_file.writelines(pending_orders)
        os.remove(pending_orders_directory + pending_orders_file_name)
open('S:/ideal for windows/ShipWorks/IdealImport.csv', 'w').close()
with codecs.open('S:/ideal for windows/ShipWorks/IdealImport.csv', 'a', 'utf-8') as ideal_import_file:
# open('\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks\\IdealImport.csv', 'w').close()
# with codecs.open('\\\\Server1\\Netapp\\IdealShare\\Ideal for Windows\\ShipWorks\\IdealImport.csv', 'a', 'utf-8') as ideal_import_file:
    for file in new_file:
        ideal_import_file.writelines(file)
    ideal_import_file.writelines(old_file)
