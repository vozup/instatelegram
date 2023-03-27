import os
from pathlib import Path


def get_site_name(http_link: str):
    """
    Parsing http string
    :param http_link: http string like http://somesite.com/adsaf/assssd
    :return: None if string not http like; tuple(full_site_name, short_site_name)
    """
    if http_link.startswith('http'):
        full_site_name = http_link.split('/')[2]
        short_site_name = full_site_name.split('.')[1]
        return full_site_name.lower(), short_site_name.lower()
    else:
        return None


def get_file_size(file_path, return_size_in='mb'):
    """
    Get file size
    :param file_path: path to file
    :param return_size_in: output format:
    'mb' - mbytes
    'kb - kbytes
    'b' - bytes
    :return: None if error; result in float
    """

    if not os.path.isfile(file_path):
        print(f"{file_path} is not a file")
        return None
    try:
        file_size = os.path.getsize(file_path)
        if return_size_in == 'mb':
            file_size = file_size / (1024 * 1024)
            return file_size
        if return_size_in == 'kb':
            return file_size / 1024
        return file_size
    except FileNotFoundError:
        print(f"File {Path(file_path).name} not found")
        return None


def get_dir_size(directory, return_size_in='mb'):
    if not os.path.isdir(directory):
        print(f"{directory} is not directory")
        return None
    files_in_dir = os.listdir(Path(directory))
    sum_size = 0
    for file in files_in_dir:
        if Path(directory, file).is_file():
            sum_size += get_file_size(Path(directory, file), return_size_in)

    return sum_size


def make_dirs(path):
    if Path(path).suffix:
        print(f"Wrong path {path}")
        return None
    if not os.path.exists(path):
        print(f"Path dont exist, creating directory: {path}")
        os.makedirs(path)
