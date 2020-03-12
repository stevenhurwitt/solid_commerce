from SolidCommerce import API as SolidAPI
from SolidCommerce import Product as SolidProduct
from Dialogue_Input import CustomDialog
import cv2
from PIL import Image
import requests
from io import BytesIO
import PIL
import ftplib


def run_save_image_url_to_ftp():
    while True:
        url = input('Image URL: ')
        folder = input('ImageLib Folder Name: ')
        filename = input('File Name: ')
        new_url = save_image_url_to_ftp(url, folder, filename)
        is_continue = input(new_url + '\nAnother? (y/n): ')
        if is_continue == 'n':
            break


def save_image_url_to_ftp(img_url, save_folder, file_name):
    session = get_image_server_session()
    ftp_path = 'ImageLib/' + save_folder + '/'
    try:
        file = resize_url_for_ebay(img_url)
        temp_picture = BytesIO()
        file.save(temp_picture, 'jpeg')
        temp_picture.seek(0)
        session.storbinary("STOR " + ftp_path + file_name, temp_picture)
        file.close()
        session.quit()
        return 'content.powerequipdeals.com/ImageLib/' + save_folder + '/' + file_name
    except:
        session.quit()
        return ''


def resize_url_for_ebay(img_url):
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content)).convert('RGB')
    return resize_image(image)


def resize_image_for_ebay(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image)
    return resize_image(image_pil)


def resize_image(image_obj):
    ebay_minimum = 500
    width, height = image_obj.size
    # print('width: ' + str(width) + ' height: ' + str(height))
    if width > 499 or height > 499:
        return image_obj
    else:
        bool_width_longer = is_width_longest_side(width, height)
        if bool_width_longer is True:
            resize_percent = ebay_minimum / width
        else:
            resize_percent = ebay_minimum / height
        # print(resize_percent)
        return resize_by_percent(image_obj, resize_percent)


def is_width_longest_side(width, height):
    if width > height:
        return True
    else:
        return False


def resize_by_percent(image_obj, percent):
    width, height = image_obj.size
    new_width = width * percent
    new_height = height * percent
    return image_obj.resize((int(new_width), int(new_height)), PIL.Image.ANTIALIAS)


def get_image_server_session():
    return ftplib.FTP('ftp.PowerEquipDeals.com', 'PEDAdmin', 'YardNeedsRaking10')


def dialogue_get_sku():
    string = CustomDialog("Enter SKU:").show()
    return string



def solid_update_images(sku, image_urls):
    solid_api = SolidAPI()
    solid_product = SolidProduct()
    solid_product.custom_sku = sku
    solid_product.main_image = image_urls[0]
    solid_product.alternate_images = image_urls[1:]
    print(solid_product.as_update_dict())
    solid_api.update_insert_product(solid_product.as_update_product_xml_string())


def run_save_image_object_to_ftp(images):
    sku = dialogue_get_sku()
    ftp_image_links = []
    i = 1
    for image in images:
        print('Saving Image...')
        sku_dict = {
            'KAW': 'Kawasaki',
            'ARN': 'Ariens',
            'AIP': 'AIP',
            'ECH': 'Echo',
            'HYD': 'HydroGear',
            'KOH': 'Kohler',
            'MTD': 'MTD',
            'TEC': 'Tecumseh',
            'BIL': 'BillyGoat'

        }
        session = get_image_server_session()
        ftp_path = 'ImageLib/' + sku_dict[sku.split('~')[0]] + '/'
        full_file_path = ftp_path + sku + '(' + str(i) + ')' + '.jpeg'
        # try:
        file = resize_image_for_ebay(image)
        temp_picture = BytesIO()
        file.save(temp_picture, 'jpeg')
        temp_picture.seek(0)
        session.storbinary("STOR " + full_file_path, temp_picture)
        file.close()
        session.quit()
        ftp_image_links.append('http://content.powerequipdeals.com/' + full_file_path)
        # except:
        #     session.quit()
        i += 1
    print(ftp_image_links)
    solid_update_images(sku, ftp_image_links)
