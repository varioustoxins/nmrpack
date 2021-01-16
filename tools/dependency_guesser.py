import argparse
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

STORE_TRUE = 'store_true'

suffixes = ['B ', 'KB', 'MB', 'GB', 'TB', 'PB']


def human_size(number_bytes):
    index = 0
    while number_bytes >= 1024 and index < len(suffixes)-1:
        number_bytes /= 1024.
        index += 1
    f = ('%6.2f' % number_bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[index])


def download(directory, target_url):
    response = requests.get(target_url, allow_redirects=True, timeout=10, stream=True)

    file_name = target_url.split('/')[-1]
    target_file = Path(directory) / file_name

    response = requests.get(target_url, allow_redirects=True, timeout=10, stream=True)
    if response.status_code == 200:
        total_data_length = int(response.headers.get('content-length'))
        human = human_size(total_data_length)

        bar_format = f'Reading {human} {{l_bar}}{{bar:150}} [remaining time: {{remaining}}]'
        progress_bar = tqdm(total=total_data_length, bar_format=bar_format, file=sys.stdout, leave=False)

        with open(target_file, 'wb') as file_handle:
            for chunk in response.iter_content(chunk_size=512 * 1024):
                if chunk:  # filter out keep-alive new chunks
                    file_handle.write(chunk)
                    progress_bar.update(len(chunk))
    else:
        raise Exception(f'failed to down load {file_name} to {directory}')

    return file_name


def extract(directory, file_name):
    file_name = Path(file_name)
    directory = Path(directory)
    handled = False
    for extension in 'tar.gz', 'zip', 'whl':
        if extension in ''.join(file_name.suffixes):
            full_file_name = directory / file_name
            if extension == 'tar.gz':
                handled = True
                full_file_name = directory / file_name
                with tarfile.open(full_file_name, 'r:gz') as tar_file:
                    tar_file.extractall(directory)
            elif extension in ('zip', 'whl'):
                handled = True
                with zipfile.ZipFile(full_file_name, 'r') as zip_file:
                    zip_file.extractall(directory)

    if not handled:
        raise Exception(f"couldn't extract file {file_name}")



def guess_dependencies(directory, target_url):
    result = []
    for sub_directory in list_sub_directories(directory):
        try:
            result.extend(find_requirements(sub_directory))
        except RequirementsNotFound:
            pass

    for elem in result:
        print('elem', elem)
        # dependency_to_spack(elem)
    return result


def download_and_extract(directory, target_url):
    file_name = download(directory, target_url)
    extract(directory, file_name)
    guess_dependencies(directory, target_url)


def work_with_directory(directory, target_url):
    print(f'work with file://{directory} {target_url}')

    download_and_extract(directory, target_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculate hashes from web links.')
    parser.add_argument('-n', '--no-cleanup', default=False, dest='no_cleanup', action=STORE_TRUE,
                        help='prevent cleanup of temporary files')
    parser.add_argument('urls', nargs='*')

    args = parser.parse_args()

    for url in args.urls:
        if args.no_cleanup:
            temp_directory = tempfile.mkdtemp()
            work_with_directory(temp_directory, url)
            print(f'WARNING: directory {temp_directory} will not be deleted on program termination')
        else:
            with tempfile.TemporaryDirectory() as temp_directory:
                work_with_directory(temp_directory, url)
