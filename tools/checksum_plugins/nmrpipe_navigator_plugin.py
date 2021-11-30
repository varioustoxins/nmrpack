import re

from bs4 import BeautifulSoup
from cmp_version import VersionString
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page, UNKNOWN_VERSION
# noinspection PyUnresolvedReferences
from plugins import register_navigator
from .url_navigator_plugin import UrlNavigator
# noinspection PyUnresolvedReferences
from checksum_url import TYPE, MAIN_FILE, EXTRA_FILE, FORMAT, VERSION, NAME, INFO, WEBSITE, DEPENDENCIES, DIGESTS


@register_navigator()
class NmrPipeNavigator(UrlNavigator):

    NAME = 'nmrpipe'

    def __init__(self, browser, target_args):
        super(NmrPipeNavigator, self).__init__(browser, target_args)
        self._version = UNKNOWN_VERSION
        self._extra_item_info = {}

    def login_with_form(self, target_url, username_password, form=None, verbose=0):

        response = super(NmrPipeNavigator, self).login_with_form(target_url, username_password)

        if response.status_code == 200:
            install_page_url = target_url
            install_page_response = transfer_page(self._target_session, install_page_url, username_password)
            self._root = install_page_response.content
            if install_page_response.status_code == 200:
                content_soup = BeautifulSoup(self._root, 'html.parser')

                # note there is only one version here as the nmrpipe release page only ever contains one version...
                self._version = self._parse_page(content_soup)
            else:
                print(f'WARNING: response from {install_page_url} was {install_page_response.status_code}')

    @staticmethod
    def _parse_page(content_soup):
        version_regex = re.compile(r'\(NMRPipe Version ([0-9\.]+) Rev ([0-9\.]+).*\)')

        versions = set()
        for i in content_soup.body():
            match = version_regex.search(str(i))
            if match:
                versions.add('-'.join(match.group(1, 2)))

        if not versions:
            print('WARNING: nop version string found setting version to 0.0.0')
            versions.append('0.0.0')
        elif versions and len(versions) > 1:
            print(f'WARNING: more than one version string found ({", ".join(versions)}), taking highest!')

        versions = [VersionString(version) for version in versions]
        versions.sort()

        result = versions[-1]

        return str(result)

    def get_urls(self, sorted_by_version=True):

        result = super(NmrPipeNavigator, self).get_urls()

        for url in result:
            url_extension = url.split('.')[-1]
            if 'NMRPipeX' in url:
                self._extra_item_info[url] = {
                    TYPE: MAIN_FILE,
                    FORMAT: url_extension,
                    VERSION: self._version,
                }
            else:
                self._extra_item_info[url] = {
                    TYPE: EXTRA_FILE,
                    FORMAT: url_extension,
                    VERSION: self._version,
                }

        return result

    def get_version(self, url):
        return self._version

    def get_extra_info(self, url):
        return self._extra_item_info[url]

    def get_package_info(self):
        return {
            NAME: 'NMRPipe',
            INFO: 'NMRPipe is an extensive software system for processing, analyzing, and exploiting '
                  'multidimensional NMR spectroscopic data. ',
            WEBSITE: 'https://www.ibbr.umd.edu/nmrpipe/index.html'
        }

    def have_cache(self):
        return True

