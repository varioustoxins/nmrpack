
import hashlib
from re import finditer
import argparse
import requests
import sys
from urllib.parse import urlparse
from os.path import split
from argparse import RawTextHelpFormatter
from bs4 import BeautifulSoup, SoupStrainer
from fnmatch import fnmatch

session = None


def test_hash_length():
    m = hashlib.md5()
    m.update(b'flibbertigibbet')
    return len(m.hexdigest())


def exception_to_message(exception):
    identifier = exception.__class__.__name__
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    camels = [match.group(0).lower() for match in matches]
    return ' '.join(camels)


def write_digest(target_url, digest):
    sys.stdout.write(f"\r{target_url} {digest}")


def get_failure_message(target_url, message):
    return f"\r{target_url} download failed [{message}]"


def get_bar(display_length, data_length, total_data_length):
    done = int(display_length * data_length / total_data_length)
    return '[%s%s]' % ('=' * done, ' ' * (display_length - done))


def write_progress(target_url, display_length, data_length, total_data_length):

    bar = get_bar(display_length, data_length, total_data_length)
    url_components = urlparse(target_url)
    file = split(url_components.path)[-1]
    sys.stdout.write(f"\r{file} {bar}")
    sys.stdout.flush()


class DownloadFailedException(Exception):
    def __init__(self, msg):
        super(DownloadFailedException, self).__init__(msg)


def get_hash_from_url(target_url, target_session, show_progress=False, digest='sha256', username_password=(None, None)):

    response = transfer_page(target_session, url, username_password)

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
                    write_progress(target_url, display_length, data_length, total_data_length)

        except Exception as exception:
            raise DownloadFailedException(get_failure_message(target_url, exception_to_message(exception)))
    return digester.hexdigest()


def transfer_page(target_session, target_url, username_password):
    if username_password != (None, None):
        username, password = username_password

        auth = requests.auth.HTTPBasicAuth(username, password)
        response = target_session.get(target_url, allow_redirects=True, timeout=10, stream=True, auth=auth)

        if response.status_code != 200:
            auth = requests.auth.HTTPDigestAuth(username, password)
            response = target_session.get(target_url, allow_redirects=True, timeout=10, stream=True, auth=auth)

    else:
        response = target_session.get(target_url, allow_redirects=True, timeout=10, stream=True)
    return response


def report_error(error):
    msg = " ".join(error.args)
    sys.stdout.write(f"\r{url} {msg}")


def exit_if_asked():

    print()
    print('exiting...')
    sys.exit(1)


def display_hash(target_url, _hash):
    sys.stdout.write(f"\r{target_url} {_hash}")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


NEW_LINE = '\n'


def digests_formatted():
    digests = list(chunks(list(hashlib.algorithms_available), 5))
    digests = [', '.join(group) for group in digests]
    digests = '\n'.join(digests)
    return digests


def check_root_set_or_exit(in_args):
    if not in_args.root:
        print('argument --template requires matching root_argument')
        print('exiting...')
        sys.exit()


def get_urls_for_templates(in_page, templates):

    target_urls = []
    result = []
    for link in BeautifulSoup(in_page, parse_only=SoupStrainer('a'), features="html.parser"):

        if link.has_attr('href'):
            target_urls.append(link['href'])

        result = set()
        for target_url in target_urls:
            for template in templates:
                if fnmatch(target_url.rsplit('/', 1)[-1], template):
                    result.add(target_url)

    return list(result)


def get_urls_from_args(root, target_urls):

    if root:
        target_urls = [f'{args.root}/{target_url}' for target_url in target_urls]
    
    return target_urls


def check_root_exists_or_exit(root, target_session, username_password=(None, None)):

    response = transfer_page(target_session, root, username_password)

    if response.status_code != 200:
        print(f"the web site {root} isn't accessible")
        print('exiting...')
        sys.exit()


def login_with_form(target_session, username_password, form):
    username, password = username_password
    user_field, pass_field, submit_field = form

    # for xplor these are 'UserName, Password, .submit'
    data = {user_field: username, pass_field: password, submit_field: 'y'}

    response = target_session.post(args.root, data=data)
    if response.status_code != 200:
        raise DownloadFailedException(f"couldn't open the password page\n\n{response.text}")

    return response.content


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='calculate hashes from web links.',
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true',
                        help='verbose output with progress bars')
    parser.add_argument('-e', '--fail-early', dest='fail_early', default=False, action='store_true',
                        help='exit on first error')
    parser.add_argument('-r', '--root', dest='root', default=None, help='root url to add command line arguments to')
    parser.add_argument('-d', '--digest', dest='digest', default='sha256',
                        help=f'which digest algorithm to use: \n\n{digests_formatted()}\n')
    parser.add_argument('-t', '--template', dest='use_templates', default=False, action='store_true',
                        help='use urls as unix filename templates and scan the root page, --root must also be set...')
    parser.add_argument('-p', '--password', dest='password', nargs=2,  default=(None, None),
                        help='provide a username and password', metavar=('USERNAME', 'PASSWORD'))
    parser.add_argument('-f', '--form', default=None, dest='form', nargs=3,
                        help='use a form for login use root for the url of the form',
                        metavar=('USERNAME_FIELD', 'PASSWORD_FIELD', 'SUBMIT_FIELD'))
    parser.add_argument('urls', nargs='*')
    args = parser.parse_args()

    args.password = tuple(args.password)

    session = requests.session()

    page = None
    urls = []
    if args.form:
        page = login_with_form(session, args.password, args.form)
    else:
        check_root_exists_or_exit(args.root, session, username_password=args.password)

    if args.form and args.root and not args.use_templates:
        urls = args.urls
    elif args.root and not args.use_templates:
        urls = get_urls_from_args(args.root, args.urls)
    elif args.use_templates:
        if not page:
            page = transfer_page(args.root, session, args.password)
        urls = get_urls_for_templates(page,  args.urls)
    else:
        print(f'Bad combination of template {args.use_templates} and root {args.root}')

    for url in urls:
        try:
            _hash = get_hash_from_url(url, session, args.verbose, digest=args.digest, username_password=args.password)
            display_hash(url, _hash)
        except DownloadFailedException as e:

            report_error(e)

            if args.fail_early:
                exit_if_asked()
        print()
