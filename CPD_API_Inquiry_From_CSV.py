from classes import Distributor_CPD
import os
import json


script_dir = os.path.dirname(__file__)
rel_path = "data/DistributorsAndBrands.txt"
abs_file_path = os.path.join(script_dir, rel_path)
with open(abs_file_path, 'r') as text_file:
    brands = json.load(text_file)['CPD']
    mfr_code = input('Enter CPD MFR Code: ').upper()
    print(brands[mfr_code])
    kaw = Distributor_CPD.CPD(mfr_code, brands[mfr_code])
    kaw.inventory_file_from_api()
