
import hashlib
from re import finditer
import argparse
import requests
import sys
from urllib.parse import urlparse
from os.path import split
from argparse import RawTextHelpFormatter
from bs4 import BeautifulSoup,SoupStrainer
from fnmatch import fnmatch

def test_hash_length():
    m = hashlib.md5()
    m.update(b'wibble')
    return len(m.hexdigest())

def exception_to_message(exception):
    identifier =  exception.__class__.__name__
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    camels = [match.group(0).lower() for match in matches]
    return ' '.join(camels)

def write_digest(url, digest):
    sys.stdout.write(f"\r{url} {digest}")


def get_failure_message(url, message):
    return f"\r{url} download failed [{message}]"


def get_bar(display_length, data_length, total_data_length):
    done = int(display_length * data_length / total_data_length)
    return '[%s%s]' % ('=' * done, ' ' * (display_length - done))


def write_progress(url, display_length, data_length, total_data_length):

    bar = get_bar(display_length, data_length, total_data_length)
    url_components = urlparse(url)
    file = split(url_components.path)[-1]
    sys.stdout.write(f"\r{file} {bar}")
    sys.stdout.flush()


class DownloadFailedException(Exception):
    def __init__(self, msg):
        super(DownloadFailedException, self).__init__(msg)


def get_hash_from_url(url, show_progress=False,  digest='sha256'):


    response = requests.get(url, allow_redirects=True, timeout=10, stream=True)
    total_data_length = response.headers.get('content-length')

    digester = getattr(hashlib, digest)()

    display_length = test_hash_length()

    if response.status_code != 200:
        raise DownloadFailedException(f"download failed [response was {response.status_code}]")
    elif total_data_length is None:
        digester.update(response.content)
    else:
        try:
            data_length = 0
            total_data_length = int(total_data_length)
            for data in response.iter_content(chunk_size=4096):
                data_length += len(data)
                digester.update(data)

                if show_progress:
                    write_progress(url, display_length, data_length, total_data_length)

        except Exception as e:
            raise DownloadFailedException(get_failure_message(exception_to_message(e)))
    return digester.hexdigest()


def report_error(e):
    msg = " ".join(e.args)
    sys.stdout.write(f"\r{url} {msg}")


def exit_if_asked():

    print()
    print('exiting...')
    sys.exit(1)


def display_hash(url, hash):
    sys.stdout.write(f"\r{url} {hash}")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

NEW_LINE='\n'

def digests_formatted():
    digests = list(chunks(list(hashlib.algorithms_available),5))
    digests = [', '.join(group) for group in digests]
    digests = '\n'.join(digests)
    return digests


def check_root_set_or_exit(args):
    if not args.root:
        print('argument --template requires matching root_argument')
        print('exiting...')
        sys.exit()


def get_urls_for_templates(root, templates):
    urls = []

    response = requests.get(root)

    for link in BeautifulSoup(response.content, parse_only=SoupStrainer('a'), features="html.parser"):
        if link.has_attr('href'):
            urls.append(link['href'])

    result = set()
    for url in urls:
        for template in templates:
            if fnmatch(url.rsplit('/', 1)[-1], template):
                result.add(url)
                
    return list(result)


def get_urls_from_args(args):

    if args.use_templates:
        urls = get_urls_for_templates(args.root, args.urls)
    elif args.root:
        urls = [f'{args.root}/{url}' for url in args.urls]
    else:
        urls = args.urls
    
    return urls


def check_root_exists_or_exit(root):

    request = requests.get(root)
    if request.status_code != 200:
        print(f"the web site {root} isn't acessible")
        print('exiting...')
        sys.exit()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='calculate hashes from web links.', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v','--verbose', dest='verbose', default=False, action='store_true', help='verbose output with origress bars')
    parser.add_argument('-e','--fail-early', dest='fail_early', default=False, action='store_true', help='exit on first error')
    parser.add_argument('-r', '--root', dest='root', default=None, help='root url to add command line arguments to')
    parser.add_argument('-d', '--digest', dest ='digest', default='sha256', help=f'which digest algorithm to use: \n\n{digests_formatted()}\n')
    parser.add_argument('-t', '--template', dest='use_templates', default=False, action='store_true',
                        help='if set all filenames are treated as templates in the root page, --root must also be set...')
    parser.add_argument('urls', nargs='+')
    args = parser.parse_args()

    if args.root:
        check_root_exists_or_exit(args.root)

    urls = get_urls_from_args(args)

    for url in urls:
        try:
            hash = get_hash_from_url(url, args.verbose, digest=args.digest)
            display_hash(url, hash)
        except DownloadFailedException as e:

            report_error(e)

            if args.fail_early:
                exit_if_asked()
        print()

