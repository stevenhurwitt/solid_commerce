import requests
from io import open as iopen
import csv


def requests_image(file_url, save_directory):
    file_name = file_url.split('/')[-1]
    print(file_name)
    response = requests.get(file_url)
    with iopen(save_directory + file_name, 'wb') as file:
        file.write(response.content)


def save_images_from_csv():
    with open('T:/ebay/All/Data/2019/PictureLinksNoDuplicates.csv', encoding='utf-8', errors='ignore') as picture_file:
        picture_links = csv.DictReader(picture_file)
        save_directory = 'T:/ebay/All/Data/2019/Temp Pictures/'
        for link in picture_links:
            print(link)
            requests_image(link['MainImage'], save_directory)


save_images_from_csv()
