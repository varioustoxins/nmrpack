from fnmatch import fnmatch
from functools import partial

import pluggy
import sys
from html2text import html2text
from tqdm import tqdm
# noinspection PyUnresolvedReferences
from checksum_url import Navigator
from plugins import register_navigator
# pm = pluggy.PluginManager(CHECK_SUM_PROJECT)


def show_license(page):
    print()
    print(html2text(str(page)))
    agree = [input_elem for input_elem in page.find_all('input') if input_elem['name'] == 'AgreeToLicense'][0]
    print()
    print(agree['value'])
    print()


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

@register_navigator()
class XplorNavigator(Navigator):

    NAME = 'xplor'

    VERSION_REGEX_GZ = Navigator.DEFAULT_VERSION_REGEX + '[-]'

    def __init__(self, browser, target_args):
        super(XplorNavigator, self).__init__(browser, target_args)

    def login_with_form(self, target_url, username_password, form=None, verbose=0):
        if not form:
            form = (0, 'UserName', 'Password', None)
        return super(XplorNavigator, self).login_with_form(target_url, username_password, form, verbose=verbose)


    def version_matcher(self, url):

        result = None
        if url.endswith('.gz'):
            result = self._urls_to_url_version([url,], self.VERSION_REGEX_GZ)[url]
        else:
            result = self._urls_to_url_version([url,], self.DEFAULT_VERSION_REGEX)[url]

        return result

    def get_urls(self, sorted_by_version=True):

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
        for target_index, button_value in enumerate(target_names):
            browser = self._re_login_with_form()
            form = browser.select_form(selector='form[method="POST"]', nr=3)
            button = browser.get_current_page().find('input', value=button_value)

            form.choose_submit(button)
            browser.submit_selected()

            page = browser.get_current_page()

            if 'LICENSE FOR NON-PROFIT INSTITUTIONS TO USE XPLOR-NIH' not in page.get_text():
                print(f"WARNING: ignored the selection {button_value} as it wasn't found in the page", file=sys.stderr)
                continue

            if target_index == 0:
                show_license(page)
                if not self._args.yes:
                    if not query_yes_no('Do you accept the license?'):
                        print('License not accepted!')
                        print('exiting...')
                        sys.exit(1)
                    else:
                        print()

            browser.select_form()
            browser.submit_selected()

            for link in browser.get_current_page().find_all('a'):
                result.append(browser.absolute_url(link.get('href')))

            if show_progress:
                if target_index == 0:
                    if show_progress:
                        bar_format = f'Reading urls {{l_bar}}{{bar: 92}} [remaining time: {{remaining}}]'
                        t = tqdm(total=len(target_names) - 1, bar_format=bar_format, file=sys.stdout, leave=False)
                else:
                    t.update()

        if show_progress:
            t.close()

        if sorted_by_version:
            url_versions = [arg.split('#')[0] for arg in result]
            url_versions = self._urls_to_url_version(url_versions, self.version_matcher)
            url_versions = self._sort_url_versions(url_versions)
            result = list(url_versions.keys())

        return result



