from classes.Distributor_OW import OW


short = input('Enter Manufacturer Abbreviation: ')
long = input('Enter Manufacturer Full Name: ')
zip_code = input('Enter Zip Code for Calculated Shipping(63101 is zone 5): ')
ow = OW(short, long)
ow.ebay_api_competitor_inquiry_for_brand_for_zip(zip_code)
