import base64
import os
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image


# future placeholder: upsizer / quality


# tests
# GCS: 'https://storage.googleapis.com/ice1337/ocr_test/a9482534-0dcc-44da-9189-4370ad8230f3.jpeg'
# Telegram: "https://web.telegram.org/e0abaf13-088d-4eec-9e16-df61da13948d"
# S3:
def get_image_obj(image_url, input_type='filepath', mode='binary'):
    image = None
    if input_type == 'blob' and mode == 'binary':
        with open(image_url, 'rb') as image_file:
            image_binary = image_file.read()
            return image_binary

    if type(image_url) is float:
        return image_url
    elif 'http' in image_url:
        response = requests.get(image_url)

        # print("saw",response)
        image_bytes = BytesIO(response.content)
        if mode == 'binary' and input_type == 'filepath':
            # Now, before encoding, you need to read the bytes from the BytesIO object
            bytes_content = image_bytes.getvalue()

            # can apply encoding to other later e.g. base64
            return bytes_content
        else:
            image = Image.open(image_bytes)
            return image
    else:

        image = Image.open(image_url)
    return image


def get_extension(file_url) -> str:
    if has_extension(file_url):
        parsed_url = urlparse(file_url)
        file_path = parsed_url.path
        _, file_extension = os.path.splitext(file_path)
        return file_extension

    return ".jpeg"


def get_image_for_s3(image_url):
    image_data = None
    response = requests.get(image_url)
    if response.status_code == 200:
        image_data = response.content

    return image_data


def has_extension(image_url: str) -> bool:
    if image_url.endswith('.jpeg') or image_url.endswith('.jpg') or image_url.endswith('.png'):
        return True
    return False
