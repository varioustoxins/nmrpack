
import hashlib
from re import finditer
import argparse
import requests
import sys
from urllib.parse import urlparse
from os.path import split
from argparse import RawTextHelpFormatter
# noinspection PyProtectedMember
from bs4 import BeautifulSoup, SoupStrainer
from fnmatch import fnmatch
from html2text import html2text
from mechanicalsoup import StatefulBrowser
from time import sleep
from tqdm import tqdm
import os

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


def get_arrow():
    """ Returns an arrow-key code after keyboard_hit() has been called. Codes are
    0 : up
    1 : right
    2 : down
    3 : left
    Should not be called in the same program as get_char().
    """

    if os.name == 'nt':
        msvcrt.get_char()  # skip 0xE0
        c = msvcrt.get_char()
        values = [72, 77, 80, 75]

    else:
        c = sys.stdin.read(3)[2]
        values = [65, 67, 66, 68]

    return values.index(ord(c.decode('utf-8')))


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


# https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = input(question + prompt).lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


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


def get_hash_from_url(target_url, target_session, verbose, digest='sha256', username_password=(None, None)):

    show_progress = verbose > 0

    response = transfer_page(target_session, target_url, username_password)

    if verbose > 1:
        display_response(response)

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


def report_error(target_url, error):
    msg = " ".join(error.args)
    sys.stdout.write(f"\r{target_url} {msg}")


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


def check_root_set_or_exit(target_args):
    if not target_args.root:
        print('argument --template requires matching root_argument')
        print('exiting...')
        sys.exit()


def get_urls_for_templates(target_page, templates):

    target_urls = []
    result = []
    for link in BeautifulSoup(target_page, parse_only=SoupStrainer('a'), features="html.parser"):

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
        target_urls = [f'{root}/{target_url}' for target_url in target_urls]
    
    return target_urls


def check_root_exists_or_exit(root, target_session, username_password=(None, None)):

    response = transfer_page(target_session, root, username_password)

    if response.status_code != 200:
        print(f"the web site {root} isn't accessible")
        print('exiting...')
        sys.exit()


class Navigator:
    def __init__(self, target_session, target_args):
        self._target_session = target_session
        self._browser = StatefulBrowser(session=target_session)
        self._args = target_args
        self._target_url = None
        self._username_password = None
        self._form = None

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


def show_license(page):
    print()
    print(html2text(str(page)))
    agree = [input_elem for input_elem in page.find_all('input') if input_elem['name'] == 'AgreeToLicense'][0]
    print()
    print(agree['value'])
    print()


class XplorNavigator(Navigator):

    def __init__(self, browser, target_args):
        super(XplorNavigator, self).__init__(browser, target_args)

    def login_with_form(self, target_url, username_password, form=None, verbose=0):
        if not form:
            form = (0, 'UserName', 'Password', None)
        super(XplorNavigator, self).login_with_form(target_url, username_password, form, verbose=verbose)

    def get_urls(self):
        prototype_browser = self._browser

        all_buttons = prototype_browser.get_current_page().find_all('input')
        targets = set()
        for template in args.urls:
            for button in all_buttons:
                if fnmatch(button['value'], template):
                    targets.add(button['value'])

        for i, button_value in enumerate(targets):
            browser = self._re_login_with_form()
            form = browser.select_form(selector='form[method="POST"]', nr=3)
            button = browser.get_current_page().find('input', value=button_value)

            form.choose_submit(button)
            browser.submit_selected()

            page = browser.get_current_page()

            if 'LICENSE FOR NON-PROFIT INSTITUTIONS TO USE XPLOR-NIH' not in page.get_text():
                print(f"WARNING: ignored the selection {button_value} as it wasn't found in the page")
                continue

            if i == 0:
                show_license(page)
                if not self._args.yes:
                    if not query_yes_no('Do you accept the license?'):
                        print('License not accepted!')
                        print('exiting...')
                        sys.exit(1)

            browser.select_form()
            browser.submit_selected()

            for link in browser.get_current_page().find_all('a'):
                yield browser.absolute_url(link.get('href'))


class UrlNavigator(Navigator):
    def __init__(self, browser, target_args):
        super(UrlNavigator, self).__init__(browser, target_args)
    
    def get_urls(self):
        target_args = self._args

        if target_args.form and target_args.root and not target_args.use_templates:
            for target_url in target_args.urls:
                yield target_url
        elif target_args.root and not target_args.use_templates:
            for target_url in get_urls_from_args(target_args.root, target_args.urls):
                yield target_url
        elif target_args.use_templates:
            page = transfer_page(target_args.root, session, target_args.password)

            for target_url in get_urls_for_templates(page, target_args.urls):
                yield target_url
        else:
            print(f'Bad combination of template {target_args.use_templates} and root {target_args.root}')


navigators = {'url': UrlNavigator, 'xplor': XplorNavigator}


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
    for i in range(100):
        sleep(0.1)
        progress_bar.update(0.1)
        progress_bar.set_description(f'{int((100-i)/10)}s remaining ')

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


if __name__ == '__main__':

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
                        help='method to navigate to download url, currently (supported: url [default], xplor)')
    parser.add_argument('-y', '--yes', default=False, dest='yes', action=STORE_TRUE,
                        help='answer yes to all questions, including accepting licenses')
    parser.add_argument('urls', nargs='*')

    args = parser.parse_args()
    args.password = tuple(args.password)

    if args.yes:
        show_yes_message_cancel_or_wait()

    session = requests.session()

    if args.navigator not in navigators:
        print(f'bad navigator {args.navigator} expected one of {", ".join(navigators.keys())}')
        print('exiting...')
        sys.exit(1)

    navigator_class = navigators[args.navigator]
    navigator = navigator_class(session, args)

    if args.form or navigator_class != UrlNavigator:
        navigator.login_with_form(args.root, args.password, args.form)
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

            report_error(url, e)

            if args.fail_early:
                exit_if_asked()
        print()
