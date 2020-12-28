
import hashlib
import inspect
import re
from collections import OrderedDict
from pathlib import Path
from re import finditer
import argparse
import requests
import sys
from argparse import RawTextHelpFormatter
from html2text import html2text
from mechanicalsoup import StatefulBrowser
from time import sleep
from tqdm import tqdm
import os
import pluggy
import importlib
from operator import itemgetter
from cmp_version import VersionString



CHECK_SUM_PROJECT = "check_sum_url"
CHECK_SUM_SPEC = pluggy.HookspecMarker(CHECK_SUM_PROJECT)
CHECK_SUM_IMPL = pluggy.HookimplMarker(CHECK_SUM_PROJECT)


class ChecksumHookspecs:

    @CHECK_SUM_SPEC
    def create_navigator(self, name, target_browser, target_args):
        """create a new navigator
        """

    @CHECK_SUM_SPEC
    def get_plugin_name(self):
        """get the name of the navigator
        """

    @CHECK_SUM_SPEC
    def create_output(self, name, additional_args=None):
        """create an output
        """

    @CHECK_SUM_SPEC
    def get_output_name(self):
        """get the name of an output
        """


pm = pluggy.PluginManager(CHECK_SUM_PROJECT)
pm.add_hookspecs(ChecksumHookspecs)

session = None

COUNT = 'count'
STORE_TRUE = 'store_true'

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

    print('-'*under_length + header + '-'*under_length)
    print()
    print(text)
    print()
    print('-' * (under_length*2 + len(header)))


def display_response(response, header='response'):
    text = html2text(response.text)
    display_text(text, header)


suffixes = ['B ', 'KB', 'MB', 'GB', 'TB', 'PB']


def human_size(number_bytes):
    index = 0
    while number_bytes >= 1024 and index < len(suffixes)-1:
        number_bytes /= 1024.
        index += 1
    f = ('%6.2f' % number_bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[index])


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


def get_hash_from_url(target_url, target_session, verbose, count, digest='sha256',
                      username_password=(None, None)):

    show_progress = verbose > 0

    response = transfer_page(target_session, target_url, username_password)

    total_data_length = response.headers.get('content-length')

    digester_factory = getattr(hashlib, digest)
    digester = digester_factory()

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
                t = tqdm(total=total_data_length, bar_format=bar_format, file=sys.stdout, leave=False)

            for data in response.iter_content(chunk_size=4096):
                if show_progress:
                    t.update(len(data))
                digester.update(data)

            if show_progress:
                t.close()

        except Exception as exception:
            raise DownloadFailedException(get_failure_message(target_url, exception_to_message(exception)))
    return digester.hexdigest()



def report_error(target_url, error, url_length, index):
    msg = " ".join(error.args)
    target_url = target_url.ljust(url_length)
    index_string = f'[{index}]'.ljust(5)
    sys.stdout.write(f"\rsum {index_string} {target_url} {msg}")


def exit_if_asked():

    print()
    print('exiting...')
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
        print('argument --template requires matching root_argument')
        print('exiting...')
        sys.exit()


class Navigator:

    DEFAULT_VERSION_REGEX = r'([0-9]+\.(?:[0-9][A-Za-z0-9_-]*)(?:\.[0-9][A-Za-z0-9_-]*)*)'

    def __init__(self, target_session, target_args):
        self._target_session = target_session
        self._browser = StatefulBrowser(session=target_session)
        self._args = target_args
        self._target_url = None
        self._username_password = None
        self._form = None

    @classmethod
    def _sort_url_versions(cls, url_versions):
        result = cls._sort_by_version(url_versions)
        return result

    @staticmethod
    def _do_login(browser, target_url, username_password, form, verbose=0):
        username, password = username_password
        form_selector, user_field, pass_field, selector = form

        response = browser.open(target_url)

        if verbose > 1:
            display_response(response, 'login-form')

        if response.status_code != 200:
            raise DownloadFailedException(f"couldn't open the password page\n\n{response.text}")

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
    def _urls_to_url_version(cls, target_urls, version_regex=None):

        results = {}
        for target_url in target_urls:
            default_template = cls.DEFAULT_VERSION_REGEX
            if not version_regex:
                version_regex = default_template
            regex = re.compile(version_regex)
            match = regex.search(target_url)

            if match:
                results[target_url] = match.group(1)
            else:
                print(f"WARNING: couldn't match version for url: {target_url}")
                results[target_url] = '0.0.0'

        return results



def show_yes_message_cancel_or_wait():
    print('''
        --------------------------**NOTE**--------------------------
        
            You have used the --yes facility all licenses will 
            now be displayed and then accepted **automatically**
            
            press y or space bar to continue
            
            press any other key to exit...
            
        ------------------------------------------------------------
    ''')

    progress_bar = tqdm(total=10, bar_format='        {desc}{bar:45}', file=sys.stdout, leave=False)

    kb = KBHit()

    doit = True
    for index in range(100):
        sleep(0.1)
        progress_bar.update(0.1)
        progress_bar.set_description(f'{int((100-index)/10)}s remaining ')

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

    kb.set_normal_term()

    if not doit:
        print()
        print('canceled, exiting...')
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


def get_script_directory():
    return os.path.dirname(os.path.realpath(__file__))


def load_plugins():

    result = []

    plugins_dir = Path(get_script_directory()) / Path('checksum_plugins')

    importlib.import_module('checksum_plugins')
    for file_name in plugins_dir.iterdir():

        if file_name.suffix == '.py' and file_name.name.endswith('_plugin.py'):
            module_name = 'checksum_plugins.' + file_name.name[0:-len('.py')]
            result.append(importlib.import_module(module_name))

    return result

def load_factory_classes(modules):

    result = []
    for module in modules:
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Factory'):
                result.append(cls)
    return result


def load_and_register_factory_classes(pm):
    modules = load_plugins()
    factories = load_factory_classes(modules)

    for factory in factories:
        instance = factory()
        pm.register(instance)


class OutputBase:
    def output(self, url, hash, max_length_url, i):
        """output a url and its hash"""


if __name__ == '__main__':

    load_and_register_factory_classes(pm)

    navigator_names = ', '.join(pm.hook.get_plugin_name())
    output_names = ', '.join(pm.hook.get_output_name())

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
    parser.add_argument('-p', '--password', dest='password', nargs=2,  default=(None, None),
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
    parser.add_argument('--version-format', dest='version_regex', default=None,
                        help=f'define a regex to select the version of the software typically from its url, '
                             f'it should create a single match for each url, all others are discarded'
                             r'default: ([0-9]+\.(?:[0-9]+[A-Za-z0-9_-]*\.[0-9]+[A-Za-z0-9_-]*))+')
    parser.add_argument('urls', nargs='*')

    args = parser.parse_args()
    args.password = tuple(args.password)

    if args.yes:
        show_yes_message_cancel_or_wait()

    session = requests.session()

    navigators = pm.hook.create_navigator(name=args.navigator, target_browser=session, target_args=args)

    if len(navigators) == 0:
        print(f'navigator {args.navigator} not found expected one of {", ".join(navigators.keys())}')
        print('exiting...')
        sys.exit(1)

    if len(navigators) > 1:
        print(f'WARNING multiple navigators select for  {args.navigator} selecting the first one')

    navigator = navigators[0](session, args)

    navigator.login_with_form(args.root, args.password, args.form)

    out = pm.hook.create_output(name=args.output_format)[0]

    urls = navigator.get_urls()
    max_length_url = get_max_string_length(urls)
    num_urls = len(urls)

    for i, url in enumerate(urls):
        x_of_y = '%3i/%-3i' % (i + 1, len(urls))

        try:
            _hash = get_hash_from_url(url, session, args.verbose, x_of_y, digest=args.digest,
                                      username_password=args.password)
            out.display_hash(url, _hash, max_length_url, i+1, num_urls)

        except DownloadFailedException as e:

            report_error(url, e, max_length_url, i+1)

            if args.fail_early:
                exit_if_asked()

        out.finish()

        print()
