import os
from urllib.parse import urlparse


def get_file_name(file_path):
    parsed_url = urlparse(file_path)
    path = parsed_url.path

    file_name = os.path.basename(path)

    return file_name

