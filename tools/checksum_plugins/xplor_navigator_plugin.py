from fnmatch import fnmatch
from functools import partial
from pathlib import Path
from urllib.parse import urlunparse, urlparse
import sys
from html2text import html2text

# noinspection PyUnresolvedReferences
from checksum_url import Navigator, VERSION, FORMAT, TYPE, EXTRA_FILE, MAIN_FILE, NAME, INFO, WEBSITE, UNUSED_FILE, \
    PLATFORM, OS, TARGET, URL_TYPE
from plugins import register_navigator


PLATFORMS = ['darwin', 'linux', 'Irix', 'Ppc', 'SunOs', 'OSF1', ]
DARWIN_VERSIONS = darwin_versions = {
            "Darwin_12":  "Mountain Lion",
            "Darwin_10":  "Snow Leopard",
            "Dawin_8":    "Tiger",
            "Darwin_7":   "Panther",
            "Darwin_6":   "Jaguar",
            "Darwin_5":   "Puma"
}

IGNORED_PLATFORMS = [
    'Irix',
    'Ppc',
    'SunOs',
    'OSF1',
]
IGNORED_PLATFORMS_LOWER = [platform.lower() for platform in IGNORED_PLATFORMS]

class LicenseNotAcceptedException(Exception):
    ...

class TooManyUrlsException(Exception):
    ...

def show_license(page):
    print(file=sys.stderr)
    print(html2text(str(page)),file=sys.stderr)
    agree = [input_elem for input_elem in page.find_all('input') if input_elem['name'] == 'AgreeToLicense'][0]
    print(file=sys.stderr)
    print(agree['value'], file=sys.stderr)
    print(file=sys.stderr)


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


def get_interpolated_url(root_url, button_value):
    path = Path(root_url.path)
    path = path.parent
    path = path / button_value
    return urlunparse(root_url._replace(path=str(path)))



BUTTONS = 'buttons'
EXTRA = 'extra'

@register_navigator()
class XplorNavigator(Navigator):

    NAME = 'xplor'

    VERSION_REGEX_GZ = Navigator.DEFAULT_VERSION_REGEX + '[-]'



    def __init__(self, browser, target_args):
        super(XplorNavigator, self).__init__(browser, target_args)
        # TODO: move to input args?
        # if optimise is set to true read the url for the firdt button and extract the complete path and
        # extrapolate the rest
        self._optimise=True
        self._cache_data = {BUTTONS: {}, EXTRA: {}}
        self._urls = None
        self._target_url = None
        self._license_shown = False


    def login_with_form(self, target_url, username_password, form=None, verbose=0):
        self._target_url = target_url
        if not form:
            form = (0, 'UserName', 'Password', None)
        return super(XplorNavigator, self).login_with_form(target_url, username_password, form, verbose=verbose)

    def get_version(self, url):

        if url.endswith('.gz'):
            result = self._urls_to_url_version([url,], self.VERSION_REGEX_GZ)[url]
        else:
            result = self._urls_to_url_version([url,], self.DEFAULT_VERSION_REGEX)[url]

        return result

    def have_cache(self):
        return True

    def set_cache_data(self, url, data):
        pass

    def get_cache_data(self, url):
        return {}

    def get_urls(self):

        if self._urls == None:
            result = []
            prototype_browser = self._browser

            all_buttons = prototype_browser.get_current_page().find_all('input')
            all_button_names = [button['value'] for button in all_buttons]

            raw_target_names = set()
            for template in self._args.urls:
                match = partial(fnmatch, pat=template)
                raw_target_names.update(filter(match, all_button_names))


            root_url = None
            for target_index, button_value in enumerate(raw_target_names):

                if root_url:
                    single_result = get_interpolated_url(root_url,button_value)
                else:
                    single_result = self._get_single_url(button_value)

                if not root_url:
                    root_url = urlparse(single_result)

                platform = self.get_platform(single_result)
                if platform.lower() in IGNORED_PLATFORMS_LOWER:
                    print(f'NOTE: {platform} currently not supported ignoring filename {single_result}', file=sys.stderr)
                    continue
                result.append(single_result)

        return result

    @staticmethod
    def get_platform(url):
        result = 'any'
        for name in PLATFORMS:
            if name in url.lower():
                result = name

        return result

    @staticmethod
    def get_os(url):

        url = url.lower()
        result = 'any'
        if 'darwin' in url:
            for version, os in darwin_versions.items():
                if version in url:
                    result = os
        return result

    @staticmethod
    def get_target(url):

        url = url.lower()
        result = 'x86_64'
        for target in 'x86_64','x86':
            if target in url:
                result = target
        return result

    def login_and_get_url(self, url):
        return url

    def _get_single_url(self, button_value):

        results = []

        browser = self._re_login_with_form()
        form = browser.select_form(selector='form[method="POST"]', nr=3)
        button = browser.get_current_page().find('input', value=button_value)
        form.choose_submit(button)
        browser.submit_selected()
        page = browser.get_current_page()
        if 'LICENSE FOR NON-PROFIT INSTITUTIONS TO USE XPLOR-NIH' not in page.get_text():
            print(f"WARNING: ignored the selection {button_value} as it wasn't found in the page", file=sys.stderr)
        else:
            if not self._license_shown:
                show_license(page)
                self._license_shown=True
                if not self._args.yes:
                    if not query_yes_no('Do you accept the license?'):
                        msg = 'License not accepted!'
                        raise LicenseNotAcceptedException(msg)
                    else:
                        print()
            browser.select_form()
            browser.submit_selected()

            for link in browser.get_current_page().find_all('a'):
                results.append(browser.absolute_url(link.get('href')))

        newline = '\n'
        if len(results) == 0:
            result = None
        elif len(results) > 1:
            msg = f'''Error: there should be one download link per link per url I got {len(results)}...
                      {newline.join(results)}
            '''
            raise TooManyUrlsException(msg)
        else:
            result = results[0]

        return result


    def get_package_info(self):
            return {
                NAME: 'Xplor-NIH',
                INFO: '''XPLOR-NIH a structure determination program which builds on the X-PLOR program, 
                         including additional tools developed at the NIH''',
                WEBSITE: 'https://nmr.cit.nih.gov/xplor-nih/'
            }

    def get_extra_info(self, url):

        file_name = self._file_name_form_url(url)

        if file_name.endswith('.sh'):
            type = UNUSED_FILE
        elif 'old' in file_name:
            type=UNUSED_FILE
        elif '-db' in file_name:
            type = MAIN_FILE
        else:
            type = EXTRA_FILE

        version = self.get_version(file_name)
        url_extension = file_name.split('.')[-1]
        target = self.get_target(file_name)
        platform = self.get_platform(file_name)
        os = self.get_os(file_name)

        result = {
            VERSION: version,
            FORMAT: url_extension,
            TYPE: type,
            PLATFORM: platform,
            OS: os,
            TARGET: target,
            URL_TYPE: 'xplor_url'
        }

        return result

    def _file_name_form_url(self, url):
        return Path(urlparse(url).path).parts[-1]
