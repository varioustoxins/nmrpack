from fnmatch import fnmatch
from functools import partial
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pluggy
import sys
from html2text import html2text
from tqdm import tqdm
# noinspection PyUnresolvedReferences
from checksum_url import Navigator, VERSION, FORMAT, TYPE, EXTRA_FILE, MAIN_FILE, NAME, INFO, WEBSITE
from plugins import register_navigator
# pm = pluggy.PluginManager(CHECK_SUM_PROJECT)

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
        self._cached_urls = None
        self._url_extra_info = {}


    def login_with_form(self, target_url, username_password, form=None, verbose=0):
        if not form:
            form = (0, 'UserName', 'Password', None)
        return super(XplorNavigator, self).login_with_form(target_url, username_password, form, verbose=verbose)

    def get_version(self, url):

        if url.endswith('.gz'):
            result = self._urls_to_url_version([url,], self.VERSION_REGEX_GZ)[url]
        else:
            result = self._urls_to_url_version([url,], self.DEFAULT_VERSION_REGEX)[url]

        return result

    def get_urls(self, sorted_by_version=True):

        if self._cached_urls == None:
            result = []
            prototype_browser = self._browser

            all_buttons = prototype_browser.get_current_page().find_all('input')
            all_button_names = [button['value'] for button in all_buttons]

            target_names = set()
            for template in self._args.urls:
                # noinspection PyTypeChecker
                match = partial(fnmatch, pat=template)
                target_names.update(filter(match, all_button_names))

            show_progress = self._args.verbose >= 1

            t = None
            should_show_license = True
            root_url = None
            for target_index, button_value in enumerate(target_names):

                if root_url:
                    single_result = get_interpolated_url(root_url,button_value)
                else:
                    single_result = self.get_single_url(button_value, should_show_license)

                if show_progress:
                    if target_index == 0:
                        if show_progress:
                            bar_format = f'Reading urls {{l_bar}}{{bar: 92}} [remaining time: {{remaining}}]'
                            t = tqdm(total=len(target_names) - 1, bar_format=bar_format, file=sys.stdout, leave=False)
                    else:
                        t.update()

                ignored_names = [
                    'Linux',
                    'Irix',
                    'Ppc',
                    'SunOs',
                    'OSF1',
                    'Darwin_7.3.0',
                    'Darwin_6.3'
                ]
                ignore_url = False
                for ignored_name in ignored_names:
                    if ignored_name.upper() in single_result.upper():
                        print(f'NOTE: {ignored_name} currently not supported ignoring url {single_result}', file=sys.stderr)
                        ignore_url = True
                if ignore_url:
                    continue

                if single_result:
                    should_show_license = False
                    result.append(single_result)
                    if self._optimise:
                        root_url = urlparse(single_result)



            if show_progress:
                t.close()


            url_versions = [arg.split('#')[0] for arg in result]
            url_versions = self._urls_to_url_version(url_versions, self.get_version)
            url_versions = self._sort_url_versions(url_versions)

            if sorted_by_version:
                result = list(url_versions.keys())

            self.process_extra_info(url_versions)

            self._cached_urls = tuple(result)
        else:
            result = self._cached_urls
        return result

    def process_extra_info(self, url_versions):

        version_url = {}
        for url, version in url_versions.items():
            url_extension = url.split('.')[-1]

            if url.endswith('.sh'):
                type = MAIN_FILE
            else:
                type = EXTRA_FILE

            self._url_extra_info[url] = {
                VERSION: version,
                FORMAT: url_extension,
                TYPE: type
            }

            version_url.setdefault(version,[]).append(url)


    def get_single_url(self, button_value, should_show_license):

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
            if should_show_license:
                show_license(page)
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
        return self._url_extra_info[url]
