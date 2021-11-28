import abc
import copy
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from re import finditer
import argparse
import requests
import sys
from argparse import RawTextHelpFormatter

import yaml
from html2text import html2text
from mechanicalsoup import StatefulBrowser
from time import sleep
from tqdm import tqdm
import os
from plugins import load_and_register_factory_classes, list_navigators, list_outputs, get_navigator, get_output
from cmp_version import VersionString

CACHE_DATA = 'cache_data'

session = None

UNKNOWN_VERSION = '0.0.0'
COUNT = 'count'
STORE_TRUE = 'store_true'

TYPE = 'type'
MAIN_FILE = 'main_file'
EXTRA_FILE = 'extra_file'
UNUSED_FILE = 'unused_file'
FORMAT = 'format'
VERSION = 'version'
NAME = 'name'
INFO = 'info'
WEBSITE = 'website'
DEPENDENCIES = 'dependencies'
DIGESTS = 'digests'
EXPAND = 'expand'
PLATFORM = 'platform'
DARWIN = 'darwin'
LINUX = 'linux'
ANY = 'any'  # can be used for ARCH as well
TARGET = 'target'
X86_64 = 'x86_64'
X86 = 'x86'
MX = 'mx'
OS = 'os'

# https://gist.github.com/michelbl/efda48b19d3e587685e3441a74457024
# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import sys
    import termios
    import atexit
    from select import select


def keyboard_hit():
    """ Returns True if keyboard character was hit, False otherwise.
    """
    if os.name == 'nt':
        return msvcrt.keyboard_hit()

    else:
        dr, dw, de = select([sys.stdin], [], [], 0)
        return dr != []


def get_char():
    """ Returns a keyboard character after keyboard_hit() has been called.
        Should not be called in the same program as get_arrow().
    """

    if os.name == 'nt':
        return msvcrt.get_char().decode('utf-8')

    else:
        return sys.stdin.read(1)


class KBHit:

    def __init__(self):
        """Creates a KBHit object that you can call to do various keyboard things.
        """

        if os.name == 'nt':
            pass

        else:

            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)

    def set_normal_term(self):
        """ Resets to normal terminal.  On Windows this is a no-op.
        """

        if os.name == 'nt':
            pass

        else:
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


def test_hash_length(digester_factory):
    m = digester_factory()
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


class DownloadFailedException(Exception):
    def __init__(self, msg):
        super(DownloadFailedException, self).__init__(msg)


def display_text(text, header):

    max_line_length = 0
    for line in text.split('\n'):
        line_length = len(line)
        if line_length > max_line_length:
            max_line_length = line_length

    under_length = max_line_length - len(header)
    if under_length <= 6:
        under_length = 6

    if under_length % 2:
        under_length += 1

    under_length //= 2

    print('-' * under_length + header + '-' * under_length)
    print()
    print(text)
    print()
    print('-' * (under_length * 2 + len(header)))


def display_response(response, header='response'):
    text = html2text(response.text)
    display_text(text, header)


suffixes = ['B ', 'KB', 'MB', 'GB', 'TB', 'PB']


def human_size(number_bytes):
    index = 0
    while number_bytes >= 1024 and index < len(suffixes) - 1:
        number_bytes /= 1024.
        index += 1
    f = ('%6.2f' % number_bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[index])


def transfer_page(target_session, target_url, username_password=(None, None)):
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


def get_hash_from_url(target_url, target_session, verbose, count, digest='sha256',
                      username_password=(None, None), debug=False):

    show_progress = verbose > 0

    digester_factory = getattr(hashlib, digest)
    digester = digester_factory()

    if not debug:
        response = transfer_page(target_session, target_url, username_password)

        total_data_length = response.headers.get('content-length')

        bar_length = 80 - 56

        t = None
        if response.status_code != 200:
            raise DownloadFailedException(f"download failed [response was {response.status_code}]")
        elif total_data_length is None:
            digester.update(response.content)
        else:
            try:
                total_data_length = int(total_data_length)

                human = human_size(total_data_length)
                if show_progress:
                    bar_format = f'Reading {count} {human} {{l_bar}}{{bar:{bar_length}}} [remaining time: {{remaining}}]'
                    t = tqdm(total=total_data_length, bar_format=bar_format, file=sys.stderr, leave=False)

                for data in response.iter_content(chunk_size=4096):
                    if show_progress:
                        t.update(len(data))
                    digester.update(data)

                if show_progress:
                    t.close()
                    print(f'Reading {count} {human} done!', file=sys.stderr, end='')

            except Exception as exception:
                raise DownloadFailedException(get_failure_message(target_url, exception_to_message(exception)))
    else:
        digester.update(url.encode('utf8'))

    return digester.hexdigest(), digester.name



def report_error(target_url, error, url_length, index):
    msg = " ".join(error.args)
    target_url = target_url.ljust(url_length)
    index_string = f'[{index}]'.ljust(5)
    sys.stdout.write(f"\rsum {index_string} {target_url} {msg}")


def exit_if_asked():

    print()
    print('exiting...', file=sys.stder)
    sys.exit(1)


def display_hash(target_url, _hash, url_field_length, index):
    target_url = target_url.ljust(url_field_length)
    index_string = f'[{index}]'.ljust(5)
    sys.stdout.write(f"\rsum {index_string} {target_url} {_hash}")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for index in range(0, len(lst), n):
        yield lst[index:index + n]


NEW_LINE = '\n'


def digests_formatted():
    digests = list(chunks(list(hashlib.algorithms_available), 5))
    digests = [', '.join(group) for group in digests]
    digests = '\n'.join(digests)
    return digests


def check_root_set_or_exit(target_args):
    if not target_args.root:
        print('argument --template requires matching root_argument', file=sys.stderr)
        print('exiting...', file=sys.stderr)
        sys.exit()


def check_for_bad_navigators_and_exit(navigators, navigator_name, possible_navigators):

    if len(navigators) == 0:
        print(f'navigator {navigator_name} not found expected one of {possible_navigators}', file=sys.stderr)
        print('exiting...', file=sys.stderr)
        sys.exit(1)

    if len(navigators) > 1:
        print(f'Error: multiple navigators selected for {navigator_name}...', file=sys.stderr)
        print('exiting...', file=sys.stderr)
        sys.exit(1)

class NavigatorABC(abc.ABC):

    @abc.abstractmethod
    def get_urls(self):
        pass

    @abc.abstractmethod
    def login_with_form(self, target_url, username_password, form, verbose=0):
        pass

    @abc.abstractmethod
    def get_extra_info(self, url):
        pass

    @abc.abstractmethod
    def get_package_info(self):
        pass

    def have_cache(self):
        return False

    def get_cache_data(self, type, url):
        return {}

    def set_cache_data(self, url, data):
        ...

    def camel_case_to_spaced(self, name):
        name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
        return name

    def name(self):
        raw_name = self.__class__.__name__
        raw_name = raw_name.strip('<>')
        raw_name = raw_name.split()[0]
        name = raw_name.split('.')[-1]

        return self.camel_case_to_spaced(name)




class Navigator(NavigatorABC):
    DEFAULT_VERSION_REGEX = r'([0-9]+\.(?:[0-9][A-Za-z0-9_-]*)(?:\.[0-9][A-Za-z0-9_-]*)*)'

    def __init__(self, target_session, target_args):
        self._target_session = target_session
        self._browser = StatefulBrowser(session=target_session)
        self._args = target_args
        self._target_url = None
        self._username_password = None
        self._form = None

    def get_urls(self, sorted_by_version=True):
        raise Exception('Error: please implement get_urls')

    @classmethod
    def _sort_url_versions(cls, url_versions):
        return cls._sort_by_version(url_versions)

    @staticmethod
    def _do_login(browser, target_url, username_password, form, verbose=0):
        username, password = username_password
        if form:
            form_selector, user_field, pass_field, selector = form

        response = browser.open(target_url)

        if verbose > 1:
            display_response(response, 'login-form')

        if response.status_code != 200:
            raise DownloadFailedException(f"couldn't open the password page\n\n{response.text}")
        if form:
            if not form_selector:
                form_selector = 'form'
                browser.select_form(form_selector)
            else:
                browser.select_form(form_selector, 0)

            browser[user_field] = username
            browser[pass_field] = password
            response = browser.submit_selected()

        if verbose > 1:
            display_response(response, 'login-response')

        if response.status_code != 200:
            raise DownloadFailedException(f"bad response from password page\n\n{response.text}")

        return browser

    def login_with_form(self, target_url, username_password, form, verbose=0):

        browser = self._browser

        self._target_url = target_url
        self._username_password = username_password
        self._form = form

        self._do_login(browser, target_url, username_password, form, verbose)

    def _re_login_with_form(self):

        browser = StatefulBrowser(session=self._target_session)

        self._do_login(browser, self._target_url, self._username_password, self._form)

        return browser

    @classmethod
    def inverted_sort_dict(cls, dict_to_sort, reverse_sorted=True):

        inverted = [(value, key) for key, value in dict_to_sort.items()]
        inverted.sort(key=lambda x: VersionString(x[0]), reverse=reverse_sorted)

        result = OrderedDict()

        for value, key in inverted:
            result[key] = value

        return result

    @classmethod
    def _sort_by_version(cls, url_versions):
        return cls.inverted_sort_dict(url_versions)

    @classmethod
    def _urls_to_url_version(cls, target_urls, version_matcher=None):

        results = {}
        for target_url in target_urls:
            default_template = cls.DEFAULT_VERSION_REGEX
            if not version_matcher:
                version_matcher = default_template

            result = None
            if isinstance(version_matcher, str):
                regex = re.compile(version_matcher)
                match = regex.search(target_url)
                if match:
                    result = match.group(1)
            elif callable(version_matcher):
                result = version_matcher(target_url)

            if not result:
                print(f"WARNING: couldn't match version for url: {target_url}", file=sys.stderr)
                result = '0.0.0'

            results[target_url] = result

        return results


def show_yes_message_cancel_or_wait():
    print('''
        --------------------------**NOTE**--------------------------

            You have used the --yes facility all licenses will 
            now be displayed and then accepted **automatically**

            press y or space bar to continue

            press any other key to exit...

        ------------------------------------------------------------
    ''', file=sys.stderr)

    progress_bar = tqdm(total=10, bar_format='        {desc}{bar:45}', file=sys.stderr, leave=False)

    # in a pycharm terminal this doesn't work skip it
    try:
        kb = KBHit()
        wait_time = 100
    except:
        kb = None
        wait_time = 0

    doit = True
    for index in range(wait_time):
        sleep(0.1)
        progress_bar.update(0.1)
        progress_bar.set_description(f'{int((100 - index) / 10)}s remaining ')

        if keyboard_hit():
            c = get_char()
            if ord(c) in (ord(' '), ord('y'), ord('Y')):
                doit = True
                progress_bar.close()
                break
            else:
                doit = False
                progress_bar.close()
                break

    if kb:
        kb.set_normal_term()

    if not doit:
        print(file=sys.stderr)
        print('canceled, exiting...', file=sys.stderr)
        sys.exit(0)


def get_max_string_length(in_urls):
    num_urls = len(in_urls)
    if num_urls > 1:
        result = max([len(in_url) for in_url in in_urls])
    elif num_urls > 0:
        result = len(in_urls[0])
    else:
        result = 0
    return result


class OutputBase:

    def __init__(self, target_args):
        self._target_args = target_args
        self.digest = 'unknown'

    def output(self, url, hash, max_length_url, i):
        """output a url and its hash"""


def cache_file_exists(file_name):
    return Path(file_name).is_file()


def load_cache_file(file_name):
    try:
        with open(file_name) as file_h:
            result = yaml.safe_load(file_h)
    except IOError as err:
        print(f'WARNING: cache file {file_name} can be opened {err} ignored!', file=sys.stderr)
        result = None
    return result


def get_cache(cache_file_name, notes):
    if args.cache_file:
        if cache_file_exists(cache_file_name):
            result = load_cache_file(cache_file_name)
            if verbose:
                notes.append(f"NOTE: using cache file {cache_file_name}")

        else:
            notes.append(f"NOTE: cache file {cache_file_name} doesn't exists creating a new one...")
            result = {}
    else:
        result = None

    return result

def get_package_from_cache(cache, navigator):

    if cache != None and 'package' in cache:
        package_info = cache['package']
    elif cache != None:
        package_info = navigator.get_package_info()
        cache['package'] = package_info
    else:
        package_info = None
    return package_info


if __name__ == '__main__':

    load_and_register_factory_classes()

    navigator_names = list_navigators()
    output_names = list_outputs()

    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description='calculate hashes from web links.',
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('-v', '--verbose', dest='verbose', default=0, action=COUNT,
                        help='verbose output (>0  with progress bars, >1 with html responses)')
    parser.add_argument('-e', '--fail-early', dest='fail_early', default=False, action=STORE_TRUE,
                        help='exit on first error')
    parser.add_argument('-r', '--root', dest='root', default=None, help='root url to add command line arguments to')
    parser.add_argument('-d', '--digest', dest='digest', default='sha256',
                        help=f'which digest algorithm to use: \n\n{digests_formatted()}\n')
    parser.add_argument('-t', '--template', dest='use_templates', default=False, action=STORE_TRUE,
                        help='use urls as unix filename templates and scan the root page, --root must also be set...')
    parser.add_argument('-p', '--password', dest='password', nargs=2, default=(None, None),
                        help='provide a username and password', metavar=('USERNAME', 'PASSWORD'))
    parser.add_argument('-f', '--form', default=None, dest='form', nargs=4,
                        help='use a form for login use root for the url of the form',
                        metavar=('FORM_SELECTOR', 'USERNAME_FIELD', 'PASSWORD_FIELD', 'SUBMIT_FIELD'))
    parser.add_argument('-n', '--navigator', default='url', dest='navigator',
                        help=f'method to navigate to download url, currently (supported: {navigator_names})')
    parser.add_argument('-y', '--yes', default=False, dest='yes', action=STORE_TRUE,
                        help='answer yes to all questions, including accepting licenses')
    parser.add_argument('-o', '--output', dest='output_format', default='simple',
                        help=f'define the output methods (supported: {output_names})')
    parser.add_argument('-m', '--main', dest='main_file_template', default=None,
                        help='template for the the main file [default = plugin chooses]')
    parser.add_argument('--version-format', dest='version_regex', default=None,
                        help=f'define a regex to select the version of the software typically from its url, '
                             f'it should create a single match for each url, all others are discarded'
                             r'default: ([0-9]+\.(?:[0-9]+[A-Za-z0-9_-]*\.[0-9]+[A-Za-z0-9_-]*))+')
    parser.add_argument('-c', '--cache', dest='cache_file', type=str, metavar='CACHE-FILE', default=None,
                        help='use a cached values from a  file if available to limit bandwidth used')
    parser.add_argument('--debug', dest='debug', default=False, action='store_true',
                        help=f'debug mode: use hashes of filenames rather than hashes of downloaded files for speed when debugging')

    parser.add_argument('urls', nargs='*')

    notes = []

    args = parser.parse_args()
    args.password = tuple(args.password)

    verbose = args.verbose

    if args.yes:
        show_yes_message_cancel_or_wait()

    cache = get_cache(args.cache_file, notes)

    if cache != None:
        original_cache = copy.deepcopy(cache)

    session = requests.session()

    navigators = get_navigator(name=args.navigator, target_browser=session, target_args=args)

    check_for_bad_navigators_and_exit(navigators, args.navigator, navigator_names)

    navigator = navigators[0](session, args)

    navigator.login_with_form(args.root, args.password, args.form, verbose=args.verbose)

    out = get_output(name=args.output_format, target_args=args)
    out.digest = args.digest

    urls = navigator.get_urls()
    max_length_url = get_max_string_length(urls)
    num_urls = len(urls)

    package_info = get_package_from_cache(cache, navigator)

    version_info = OrderedDict()
    hashes = {}
    for i, url in enumerate(urls):
        x_of_y = '%3i/%-3i' % (i + 1, len(urls))

        version = navigator.get_version(url)

        hash_type = args.digest


        if not navigator.have_cache():
            if verbose >=1:
                print(f"NOTE: cache requested but the navigator {navigator.name()} doesn't support caching", file=sys.stderr)
            have_cache = False
        elif cache != None and url in cache:
            have_cache = url in cache and args.digest in cache[url][DIGESTS]
        else:
            have_cache = False

        try:
            _hash = None
            if have_cache:
                if hash_type in cache[url][DIGESTS] and navigator.have_cache():
                    _hash = cache[url][DIGESTS][hash_type]
                    hashes[url] = _hash
                    navigator.set_cache_data(url, cache[url][CACHE_DATA])

                    if verbose >=1:
                        notes.append(f"NOTE: using cached data for {url} [version: {version}]")

            if _hash is None:
                specific_url = navigator.login_and_get_url(url)
                _hash, hash_type = get_hash_from_url(specific_url, session, verbose, x_of_y, digest=args.digest,
                                                     username_password=args.password, debug=args.debug)
                hashes[url] = _hash

                if cache != None  and navigator.have_cache():
                    if verbose>=1:
                        notes.append(f"NOTE: creating cached data for {url} [version: {version}]")
                    cache_digests = cache.setdefault(url, {}).setdefault(DIGESTS, {})
                    cache[url][DIGESTS][hash_type] = _hash
                    cache[url][CACHE_DATA] = navigator.get_cache_data(url)

            if args.debug:
                _hash = f'!DEBUG!-{_hash}-!FAKE!'

        except DownloadFailedException as e:

            report_error(url, e, max_length_url, i + 1)

            if args.fail_early:
                exit_if_asked()

    for note in notes:
        print(note, file=sys.stderr)
        sys.stderr.flush()

    if cache != None and original_cache != cache:
        if verbose:
            notes.append('NOTE: cache changed, updating...')
        try:
            with open(args.cache_file, 'w') as cache_file:
                cache_file.write(json.dumps(cache, indent=4))
        except IOError as err:
            notes.append(f'NOTE: failed to write cache to {args.cache_file} because {err}')

    if len(notes):
        print(file=sys.stderr)

    for i, url in enumerate(urls):
        out.display_hash(url, hashes[url], max_length_url, i + 1, num_urls, hash_type=hash_type)
        version_info[url] = navigator.get_extra_info(url)

    out.finish(package_info, version_info)



