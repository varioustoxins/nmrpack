import argparse
import json
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm


def download(target_url):

    response = requests.get(target_url)
    if response.status_code != 200:
        raise Exception(f'failed to down load {target_url} ')

    return response.content


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculate hashes from web links.')
    parser.add_argument('names', nargs='*')

    args = parser.parse_args()

    for name in args.names:
        json_text = download(f'https://pypi.org/pypi/{name}/json')
        print(json_text)
        print(json.dumps(json.loads(json_text), indent=4, sort_keys=True))

